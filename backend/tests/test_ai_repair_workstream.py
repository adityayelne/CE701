import os
import json
import time
from backend.main import (
    analyze_code, diagnose_and_fix, SourceCodeRequest,
    DiagnosisAndFixRequest, EDUCATIONAL_SAMPLES, ai_service
)
from backend.models import DiagnosisAndFixResponse, CompilerError

def test_valid_repair_pipeline():
    print("\n--- TEST: Valid Repair Re-parsing and PARSER_VALIDATED ---")
    broken_code = """int main() {
    int x = 10
    int y = 20;
    int sum = x + y

    if (sum = 30) {
        printf("Sum is thirty\\n");
    
    return 0;
"""
    fix = diagnose_and_fix(DiagnosisAndFixRequest(source_code=broken_code))
    assert fix.is_parser_validated is True
    assert fix.validation_status == "PARSER_VALIDATED"
    assert len(fix.diff_lines) > 0
    assert "Parser validation confirms" in fix.validation_disclaimer
    print(f"PASS: Valid repair generated. Origin: {fix.repair_origin}, Provider: {fix.provider_used}, Status: {fix.validation_status}")

def test_invalid_repair_flagging():
    print("\n--- TEST: Invalid Repair With Residual Errors ---")
    # Simulate an AI fix that leaves syntax errors
    bad_repair = "int main() { int x = ; return 0; }"
    from backend.compiler.lexer import LexicalAnalyzer
    from backend.compiler.parser import CParser
    re_tokens, re_lex_err = LexicalAnalyzer(bad_repair).tokenize()
    _, re_syn_err = CParser(re_tokens, bad_repair).parse()
    has_errs = (len(re_lex_err) + len(re_syn_err)) > 0
    assert has_errs is True, "Parser must catch residual syntax errors"
    print("PASS: Residual syntax errors cleanly detected by parser.")

def test_http_429_graceful():
    print("\n--- TEST: HTTP 429 Handling and Recovery Guidance ---")
    fix = ai_service._heuristic_diagnose_and_repair(
        source_code="int main() { int x = 10\n return 0;\n",
        parser_errors=[],
        error_category="rate_limited",
        error_detail="Groq token rate limit exceeded (HTTP 429). Account limit: 8,000 tokens/min (Reset in 2.5s).",
        recovery_guidance="Wait 15-60 seconds for quota replenishment. The local heuristic repair below is available immediately."
    )
    assert fix.repair_origin == "heuristic"
    assert fix.provider_status == "rate_limited"
    assert "Fallback: Groq Rate-Limited" in fix.provider_used
    assert fix.error_detail is not None
    assert fix.recovery_guidance is not None
    print(f"PASS: 429 rate limit handled with explicit guidance: '{fix.recovery_guidance}'")

def test_missing_api_key_handling():
    print("\n--- TEST: Missing / Invalid API Key Handling ---")
    orig_key = ai_service.groq_api_key
    try:
        ai_service.groq_api_key = ""
        fix = ai_service.diagnose_and_fix("int main() { int x = 10\n return 0;\n", [])
        assert fix.repair_origin == "heuristic"
        assert fix.provider_status == "invalid_credentials"
        assert "API Key Missing" in fix.provider_used
        assert "GROQ_API_KEY" in fix.recovery_guidance
        print(f"PASS: Missing key handled gracefully: {fix.provider_used}")
    finally:
        ai_service.groq_api_key = orig_key

def test_malformed_model_response():
    print("\n--- TEST: Malformed Model Response Handling ---")
    fix = ai_service._heuristic_diagnose_and_repair(
        source_code="int main() { int x = 10\n return 0;\n",
        parser_errors=[],
        error_category="malformed_response",
        error_detail="Groq response could not be parsed as JSON.",
        recovery_guidance="The model produced an unstructured response. Local heuristic repair provided below."
    )
    assert fix.repair_origin == "heuristic"
    assert fix.provider_status == "malformed_response"
    print("PASS: Malformed model response handled with heuristic recovery.")

def test_repeated_request_debouncing():
    print("\n--- TEST: Repeated In-Flight Requests Debouncing ---")
    code = "int main() { int count = 5\n return 0;\n"
    # Call 1
    t0 = time.time()
    res1 = ai_service.diagnose_and_fix(code, [])
    # Call 2 immediately (within 100ms)
    t1 = time.time()
    res2 = ai_service.diagnose_and_fix(code, [])
    t_diff = time.time() - t1
    assert t_diff < 0.1, "Debounced call should return instantaneously from cache"
    assert res1.corrected_code == res2.corrected_code
    print(f"PASS: Duplicate request debounced instantaneously ({t_diff*1000:.1f}ms).")

if __name__ == "__main__":
    test_valid_repair_pipeline()
    test_invalid_repair_flagging()
    test_http_429_graceful()
    test_missing_api_key_handling()
    test_malformed_model_response()
    test_repeated_request_debouncing()
    print("\n=== ALL AI REPAIR RELIABILITY TESTS PASSED ===")
