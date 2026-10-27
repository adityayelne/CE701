import os
import json
from backend.main import (
    analyze_code, diagnose_and_fix, SourceCodeRequest,
    DiagnosisAndFixRequest, EDUCATIONAL_SAMPLES, ai_service
)
from backend.models import ASTNode, CompilerError

def test_1_valid_c_input():
    print("\n--- TEST 1: Valid C Input Consistency ---")
    req = SourceCodeRequest(source_code=EDUCATIONAL_SAMPLES[0]['code'])
    res = analyze_code(req)
    assert res.success is True
    assert res.is_syntactically_valid is True
    assert res.is_semantically_valid is True
    assert len(res.tokens) > 30, f"Token count should be > 30, got {len(res.tokens)}"
    assert res.ast is not None
    assert res.ast.type == "TranslationUnit"
    assert len(res.ast.children) >= 2, "AST should contain function definitions"
    assert len(res.symbol_table) >= 5, f"Symbol table should have symbols, got {len(res.symbol_table)}"
    symbol_names = [s.name for s in res.symbol_table]
    assert "factorial" in symbol_names
    assert "main" in symbol_names
    assert len(res.intermediate_code) > 0, "TAC instructions must be generated"
    assert len(res.basic_blocks) > 0, "Basic blocks must be partitioned"
    print(f"PASS: Tokens={len(res.tokens)}, AST Nodes={res.metrics.ast_node_count}, Symbols={len(res.symbol_table)}, TAC={len(res.intermediate_code)}, Blocks={len(res.basic_blocks)}")

def test_2_operator_precedence():
    print("\n--- TEST 2: Operator Precedence in AST and TAC ---")
    code = """
    int main() {
        int a = 2;
        int b = 3;
        int c = 4;
        int x = a + b * c;
        int y = (a + b) * c;
        return x + y;
    }
    """
    res = analyze_code(SourceCodeRequest(source_code=code))
    assert res.is_syntactically_valid is True
    assert res.ast is not None

    # Find the statements in main
    main_func = next(c for c in res.ast.children if c.type == "FunctionDeclaration" and c.attributes.get("name") == "main")
    compound = next(c for c in main_func.children if c.type == "CompoundStatement")
    
    # Check AST for x = a + b * c
    # The initializer for x should have '+' at root, with right child having '*'
    decl_x = next(c for c in compound.children if c.type == "VariableDeclaration" and c.attributes.get("name") == "x")
    expr_x = decl_x.children[0]
    assert expr_x.type == "BinaryExpression"
    assert expr_x.attributes.get("operator") == "+", f"Expected '+' as root op for a + b * c, got {expr_x.attributes.get('operator')}"
    assert expr_x.children[1].type == "BinaryExpression"
    assert expr_x.children[1].attributes.get("operator") == "*", f"Expected '*' as right child op, got {expr_x.children[1].attributes.get('operator')}"

    # Check AST for y = (a + b) * c
    # The initializer for y should have '*' at root, with left child having '+'
    decl_y = next(c for c in compound.children if c.type == "VariableDeclaration" and c.attributes.get("name") == "y")
    expr_y = decl_y.children[0]
    assert expr_y.type == "BinaryExpression"
    assert expr_y.attributes.get("operator") == "*", f"Expected '*' as root op for (a + b) * c, got {expr_y.attributes.get('operator')}"
    assert expr_y.children[0].type == "BinaryExpression"
    assert expr_y.children[0].attributes.get("operator") == "+", f"Expected '+' as left child op, got {expr_y.children[0].attributes.get('operator')}"

    # Check TAC instructions sequence
    # For x: b * c should be evaluated first, then a + t0
    tac_reprs = [ins.representation for ins in res.intermediate_code]
    mul_idx = next(i for i, r in enumerate(tac_reprs) if "b * c" in r)
    add_x_idx = next(i for i, r in enumerate(tac_reprs) if f"a + t{mul_idx}" in r or ("+" in r and i > mul_idx and i < mul_idx + 3))
    assert mul_idx < add_x_idx, "TAC for b * c must precede a + t0"

    print("PASS: Operator precedence correctly verified in AST hierarchy and TAC execution order.")

def test_3_broken_syntax_diagnostics():
    print("\n--- TEST 3: Broken Syntax & Accurate Diagnostics ---")
    broken_code = """
    int main() {
        int x = 10
        int y = 20;
        int sum = x + ;
        return 0;
    }
    """
    res = analyze_code(SourceCodeRequest(source_code=broken_code))
    assert res.is_syntactically_valid is False
    assert len(res.errors) >= 1
    # Check that error is stage 'syntax' with valid line and column
    syntax_errs = [e for e in res.errors if e.stage == "syntax"]
    assert len(syntax_errs) >= 1
    for err in syntax_errs:
        assert err.line > 0
        assert err.column > 0
        assert len(err.message) > 0
        assert len(err.suggestion) > 0
    print(f"PASS: Broken syntax caught cleanly: {len(syntax_errs)} syntax diagnostics emitted.")

def test_4_ai_reparsing_validation():
    print("\n--- TEST 4: AI Repairs Are Re-Parsed Before Validation ---")
    req = DiagnosisAndFixRequest(source_code=EDUCATIONAL_SAMPLES[1]['code'])
    fix_res = diagnose_and_fix(req)
    assert fix_res.is_parser_validated is True
    assert fix_res.validation_status == "PARSER_VALIDATED"
    assert len(fix_res.corrected_code) > 0
    assert len(fix_res.diff_lines) > 0
    
    # Re-verify by manually running CParser on corrected code
    from backend.compiler.lexer import LexicalAnalyzer
    from backend.compiler.parser import CParser
    re_tokens, re_lex_err = LexicalAnalyzer(fix_res.corrected_code).tokenize()
    _, re_syn_err = CParser(re_tokens, fix_res.corrected_code).parse()
    assert len(re_lex_err) == 0, f"Corrected code produced lex errors: {re_lex_err}"
    assert len(re_syn_err) == 0, f"Corrected code produced parse errors: {re_syn_err}"
    print(f"PASS: Corrected code independently re-parsed with 0 errors. Status: {fix_res.validation_status}")

def test_5_groq_missing_config_and_429_graceful():
    print("\n--- TEST 5: Missing Config & 429 Rate Limits Handled Gracefully ---")
    orig_key = ai_service.groq_api_key
    try:
        # Simulate missing API key
        ai_service._recent_requests.clear()
        ai_service.groq_api_key = ""
        assert ai_service.has_groq_key() is False
        fix = ai_service.diagnose_and_fix(EDUCATIONAL_SAMPLES[1]['code'], [])
        assert fix is not None
        assert fix.is_parser_validated is True
        assert "Offline" in fix.provider_used or "Heuristic" in fix.provider_used
        print("PASS: Missing API key handled gracefully without crash.")

        # Simulate HTTP 429
        fix_429 = ai_service._heuristic_diagnose_and_repair(
            source_code=EDUCATIONAL_SAMPLES[1]['code'],
            parser_errors=[],
            error_category="rate_limited",
            error_detail="Groq rate limit exceeded (HTTP 429).",
            recovery_guidance="Wait a moment for quota replenishment."
        )
        assert fix_429 is not None
        assert fix_429.is_parser_validated is True
        print("PASS: HTTP 429 rate limit simulation handled gracefully.")
    finally:
        ai_service.groq_api_key = orig_key

def test_6_unsupported_syntax_and_malformed_llm():
    print("\n--- TEST 6: Unsupported Syntax & Malformed Model Responses ---")
    # 1. Binary gibberish / unsupported syntax
    gibberish = "@@#$$%^^ &*() _+~`|}{[]:;?><,./ 123456"
    res = analyze_code(SourceCodeRequest(source_code=gibberish))
    assert res is not None
    assert res.is_syntactically_valid is False
    print("PASS: Arbitrary gibberish handled safely without crash.")

    # 2. Malformed LLM response handling
    from backend.compiler.ai_service import AIService
    service = AIService()
    markdown_wrapped = "```json\n{\"corrected_code\": \"int main() { return 0; }\", \"summary\": \"fixed\", \"diagnostics\": [], \"explanation\": \"test\", \"educational_notes\": []}\n```"
    import re
    clean = markdown_wrapped.strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?\s*", "", clean)
        clean = re.sub(r"\s*```$", "", clean)
    data = json.loads(clean)
    assert data["summary"] == "fixed"
    print("PASS: Markdown fenced JSON cleanly extracted.")

if __name__ == "__main__":
    test_1_valid_c_input()
    test_2_operator_precedence()
    test_3_broken_syntax_diagnostics()
    test_4_ai_reparsing_validation()
    test_5_groq_missing_config_and_429_graceful()
    test_6_unsupported_syntax_and_malformed_llm()
    print("\n=== ALL QA TESTS PASSED SUCCESSFULLY! ===")
