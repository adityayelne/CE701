import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models import DiagnosisAndFixResponse, CompilerError
from compiler.lexer import LexicalAnalyzer
from compiler.parser import CParser
from compiler.ai_service import AIService

class TestAIRepairPipelineRegression(unittest.TestCase):
    def setUp(self):
        self.ai = AIService()

    # 1. Valid structured AI response
    def test_01_valid_structured_ai_response(self):
        raw_json = '{"corrected_code": "int main() { return 0; }", "summary": "Fixed main return", "explanation": "Valid C99"}'
        parsed, err_cat, err_det, rec = self.ai._parse_raw_llm_response(raw_json, "stop")
        self.assertIsNotNone(parsed)
        self.assertIsNone(err_cat)
        self.assertEqual(parsed["corrected_code"], "int main() { return 0; }")

    # 2. Valid code wrapped in supported response formatting (Markdown code fences)
    def test_02_valid_code_wrapped_in_markdown_fences(self):
        wrapped = """```json
{
    "corrected_code": "int main() { int x = 10; return x; }",
    "summary": "Added semicolon",
    "explanation": "Markdown fenced JSON parsed properly"
}
```"""
        parsed, err_cat, err_det, rec = self.ai._parse_raw_llm_response(wrapped, "stop")
        self.assertIsNotNone(parsed)
        self.assertIsNone(err_cat)
        self.assertIn("int x = 10;", parsed["corrected_code"])

    # 3. Malformed or truncated response (finish_reason="length")
    def test_03_malformed_or_truncated_response(self):
        # 3a. Truncated
        parsed, err_cat, err_det, rec = self.ai._parse_raw_llm_response('{"corrected_code": "int', "length")
        self.assertIsNone(parsed)
        self.assertEqual(err_cat, "truncated_response")
        self.assertIn("truncated", err_det)

        # 3b. Malformed JSON
        parsed, err_cat, err_det, rec = self.ai._parse_raw_llm_response("Here is the code: int main() { return 0; }", "stop")
        self.assertIsNone(parsed)
        self.assertEqual(err_cat, "malformed_response")

    # 4. Empty response
    def test_04_empty_response(self):
        parsed, err_cat, err_det, rec = self.ai._parse_raw_llm_response("   \n  ", "stop")
        self.assertIsNone(parsed)
        self.assertEqual(err_cat, "empty_response")

    # 5. Rate limit and provider errors
    @patch("httpx.Client.post")
    def test_05_rate_limit_and_provider_errors(self, mock_post):
        # HTTP 429
        mock_resp_429 = MagicMock()
        mock_resp_429.status_code = 429
        mock_resp_429.headers = {"retry-after": "25", "x-ratelimit-reset-tokens": "25s"}
        mock_post.return_value = mock_resp_429

        orig_key = self.ai.groq_api_key
        try:
            self.ai.groq_api_key = "gsk_test_key_mock"
            resp, err_cat, err_det, rec = self.ai._call_groq_qwen("int main() {", [])
            self.assertIsNone(resp)
            self.assertEqual(err_cat, "rate_limited")
            self.assertIn("429", err_det)

            # HTTP 401
            mock_resp_401 = MagicMock()
            mock_resp_401.status_code = 401
            mock_post.return_value = mock_resp_401
            resp, err_cat, err_det, rec = self.ai._call_groq_qwen("int main() {", [])
            self.assertIsNone(resp)
            self.assertEqual(err_cat, "invalid_credentials")

            # HTTP 500
            mock_resp_500 = MagicMock()
            mock_resp_500.status_code = 500
            mock_resp_500.text = "Internal Server Error"
            mock_post.return_value = mock_resp_500
            resp, err_cat, err_det, rec = self.ai._call_groq_qwen("int main() {", [])
            self.assertIsNone(resp)
            self.assertEqual(err_cat, "provider_error")
        finally:
            self.ai.groq_api_key = orig_key

    # 6. Valid local fallback (e.g. misplaced semicolon in argument list `,;`)
    def test_06_valid_local_fallback(self):
        code_with_misplaced_semicolon = (
            "#include <stdio.h>\n"
            "int main() {\n"
            '    printf("Result: %d\\n",; 42);\n'
            "    return 0;\n"
            "}\n"
        )
        res = self.ai._heuristic_diagnose_and_repair(
            source_code=code_with_misplaced_semicolon,
            parser_errors=[],
            error_category="malformed_response"
        )
        self.assertTrue(res.is_parser_validated)
        self.assertEqual(res.validation_status, "PARSER_VALIDATED")
        self.assertEqual(res.residual_error_count, 0)
        self.assertEqual(len(res.residual_errors), 0)
        self.assertNotIn(",;", res.corrected_code)
        self.assertIn("Parser validation confirms 0 syntax errors", res.validation_disclaimer)

    # 7. Invalid local fallback (arbitrary unfixable syntax)
    def test_07_invalid_local_fallback(self):
        unfixable_code = (
            "typedef unknown_type ??? ;\n"
            "int main() { %%% $$$ ; }\n"
        )
        res = self.ai._heuristic_diagnose_and_repair(
            source_code=unfixable_code,
            parser_errors=[CompilerError(stage="syntax", line=1, column=1, message="Syntax error")],
            error_category="malformed_response"
        )
        self.assertFalse(res.is_parser_validated)
        self.assertEqual(res.validation_status, "SYNTAX_ERRORS_REMAIN")
        self.assertGreater(res.residual_error_count, 0)
        self.assertGreater(len(res.residual_errors), 0)
        self.assertIn("Validation Failed", res.validation_disclaimer)
        self.assertIn("syntax error(s) remain", res.summary)

    # 8. Parser errors remaining after an AI proposal
    @patch("httpx.Client.post")
    def test_08_parser_errors_remaining_after_ai_proposal(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        # AI returned invalid C code with syntax error
        mock_resp.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"corrected_code": "int main() { int x = ; return 0; }", "summary": "Attempted fix"}'
                },
                "finish_reason": "stop"
            }]
        }
        mock_post.return_value = mock_resp

        orig_key = self.ai.groq_api_key
        try:
            self.ai.groq_api_key = "gsk_test_key_mock"
            resp, err_cat, err_det, rec = self.ai._call_groq_qwen("int main() {", [])
            self.assertIsNotNone(resp)
            self.assertFalse(resp.is_parser_validated)
            self.assertEqual(resp.validation_status, "SYNTAX_ERRORS_REMAIN")
            self.assertGreater(resp.residual_error_count, 0)
            self.assertIn("Validation Failed", resp.validation_disclaimer)
        finally:
            self.ai.groq_api_key = orig_key

    # 9. Consistent status across header, summary, footer, and buttons
    def test_09_consistent_validation_disclaimer_and_status(self):
        # Case A: Valid
        valid_res = self.ai._heuristic_diagnose_and_repair(
            source_code="int main() { int x = 10\n return 0; }\n",
            parser_errors=[]
        )
        self.assertTrue(valid_res.is_parser_validated)
        self.assertEqual(valid_res.validation_status, "PARSER_VALIDATED")
        self.assertIn("Parser validation confirms 0 syntax errors", valid_res.validation_disclaimer)

        # Case B: Invalid
        invalid_res = self.ai._heuristic_diagnose_and_repair(
            source_code="int main() { @@@ invalid syntax @@@ }\n",
            parser_errors=[]
        )
        self.assertFalse(invalid_res.is_parser_validated)
        self.assertEqual(invalid_res.validation_status, "SYNTAX_ERRORS_REMAIN")
        self.assertIn("Validation Failed", invalid_res.validation_disclaimer)
        self.assertNotIn("confirms 0 syntax errors", invalid_res.validation_disclaimer)

    # 10. Apply and Reject preserving the original source correctly
    def test_10_apply_and_reject_source_preservation(self):
        original = "int main() { int x = 10\n return 0; }"
        res = self.ai._heuristic_diagnose_and_repair(original, [])
        # Diff lines capture additions/modifications
        self.assertGreater(len(res.diff_lines), 0)
        # Original code is preserved in response
        self.assertEqual(res.original_code, original)
        # Corrected code has the fix
        self.assertNotEqual(res.corrected_code, original)
        self.assertIn("int x = 10;", res.corrected_code)

if __name__ == "__main__":
    unittest.main()
