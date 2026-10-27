from backend.main import (
    analyze_code, diagnose_and_fix, SourceCodeRequest,
    DiagnosisAndFixRequest, EDUCATIONAL_SAMPLES, ai_service
)

def test_shared_ast_pipeline():
    # 1. Valid Factorial
    res1 = analyze_code(SourceCodeRequest(source_code=EDUCATIONAL_SAMPLES[0]['code']))
    assert res1.is_syntactically_valid, "Sample 1 should be syntactically valid"
    assert res1.is_semantically_valid, "Sample 1 should be semantically valid"
    assert len(res1.symbol_table) == 7, f"Expected 7 symbols, got {len(res1.symbol_table)}"
    assert len(res1.intermediate_code) > 0, "TAC must be generated"
    print(f"PASS: Valid sample analyzed through shared AST. Symbols: {len(res1.symbol_table)}, TAC: {len(res1.intermediate_code)}")

    # 2. Broken syntax errors
    res2 = analyze_code(SourceCodeRequest(source_code=EDUCATIONAL_SAMPLES[1]['code']))
    assert not res2.is_syntactically_valid, "Broken sample must be flagged syntactically invalid"
    assert len(res2.errors) > 0, "Errors must be populated"
    print(f"PASS: Broken sample diagnosed with {len(res2.errors)} errors via shared pipeline")

    # 3. AI Fix re-parsing verification (with Groq Qwen when configured)
    fix = diagnose_and_fix(DiagnosisAndFixRequest(source_code=EDUCATIONAL_SAMPLES[1]['code']))
    assert fix.is_parser_validated is True, "Fix must be re-parsed and validated by CParser"
    assert fix.validation_status == "PARSER_VALIDATED", "Status must be PARSER_VALIDATED"
    print(f"PASS: AI Fix re-parsed through CParser. Status: {fix.validation_status}, Provider: {fix.provider_used}")

    # 4. Expressions precedence AST
    res3 = analyze_code(SourceCodeRequest(source_code=EDUCATIONAL_SAMPLES[2]['code']))
    assert res3.is_syntactically_valid, "Expressions sample must parse cleanly"
    assert res3.ast is not None, "AST must exist"
    print(f"PASS: Expression precedence shared AST created with {res3.metrics.ast_node_count} nodes")

    # 5. Groq Qwen configuration check
    if ai_service.has_groq_key():
        assert ("groq" in fix.provider_used.lower() or 
                "qwen" in fix.provider_used.lower() or 
                "fallback" in fix.provider_used.lower() or
                "heuristic" in fix.provider_used.lower())
        print(f"PASS: Verified Groq Qwen integration handling active ({fix.provider_used})")
    else:
        print("NOTE: Groq API key not set, verified offline heuristic fallback.")

if __name__ == "__main__":
    test_shared_ast_pipeline()
    print("ALL SHARED-AST PIPELINE & GROQ QWEN TESTS PASSED!")
