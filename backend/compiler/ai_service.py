import os
import difflib
import re
import json
import logging
import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import httpx

try:
    from ..models import (
        DiagnosisAndFixResponse, DiagnosticItem, DiffLine,
        ConceptExplanationResponse, CompilerError
    )
    from .lexer import LexicalAnalyzer
    from .parser import CParser
except (ImportError, ValueError):
    from models import (
        DiagnosisAndFixResponse, DiagnosticItem, DiffLine,
        ConceptExplanationResponse, CompilerError
    )
    from compiler.lexer import LexicalAnalyzer
    from compiler.parser import CParser

logger = logging.getLogger("compilerlab.ai_service")

EDUCATIONAL_CONCEPTS: Dict[str, Dict[str, Any]] = {
    "lexical_analysis": {
        "title": "Lexical Analysis (Scanning)",
        "phase": "Front-End: Phase 1",
        "summary": "Transforms raw source character streams into a linear sequence of meaningful tokens.",
        "detailed_explanation": (
            "The Lexical Analyzer (scanner) reads source code as a stream of individual characters and groups them "
            "into meaningful units called lexemes. Each lexeme is categorized into a Token with a specific type and attribute value. "
            "Scanning is formally defined using Regular Expressions and implemented via Deterministic Finite Automata (DFAs). "
            "Comments and whitespace are generally discarded here, while line/column coordinates are tracked for error reporting."
        ),
        "key_principles": [
            "Lexeme: The actual sequence of characters in the source code.",
            "Token: An abstract category paired with an optional attribute value (e.g. <KEYWORD, 'int'>).",
            "Maximal Munch Rule: The scanner always matches the longest valid prefix of input characters.",
            "DFA Transition Table: State machines execute in O(n) linear time with respect to source length."
        ],
        "code_example": (
            "// Lexer input: int total = 100 + count;\n"
            "// Tokens emitted:\n"
            "<KEYWORD, 'int'>, <IDENTIFIER, 'total'>, <DELIMITER, '='>,\n"
            "<INT_LITERAL, '100'>, <OPERATOR, '+'>, <IDENTIFIER, 'count'>, <DELIMITER, ';'>"
        ),
        "common_pitfalls": [
            "Confusing token types with token values.",
            "Failing to handle string escapes or multi-line comments that cross file boundaries.",
            "Off-by-one errors in line and column tracking."
        ]
    },
    "syntax_analysis": {
        "title": "Syntax Analysis (Parsing & Shared AST)",
        "phase": "Front-End: Phase 2",
        "summary": "Constructs the shared Abstract Syntax Tree (AST) that serves as the single source of truth for semantic analysis and code generation.",
        "detailed_explanation": (
            "The Parser verifies that the sequence of tokens satisfies the formal grammar of the programming language, "
            "typically specified as a Context-Free Grammar (CFG) in Backus-Naur Form (BNF). "
            "It generates a hierarchical Abstract Syntax Tree (AST) where non-terminals represent structural language constructs "
            "(like declarations, statements, and expressions) and terminals represent leaves. "
            "In a production compiler, the shared AST is the single source of truth: downstream passes (type checkers, symbol tables, "
            "optimizer, and intermediate code generators) traverse this tree rather than independently re-parsing source text."
        ),
        "key_principles": [
            "Shared AST Architecture: Lexer and Parser define the canonical AST used by all downstream passes.",
            "Source Coordinates: Every AST node preserves line and column metadata for diagnostics and source attribution.",
            "Grammar Disambiguation: Explicit precedence rules eliminate ambiguity (e.g. operator precedence, dangling-else).",
            "Error Synchronization: Panic-mode recovery prevents cascading false-positive syntax diagnostics."
        ],
        "code_example": (
            "// Grammar rule for binary addition:\n"
            "AdditiveExpr -> MultiplicativeExpr ( ('+' | '-') MultiplicativeExpr )*\n\n"
            "// Produces shared AST node:\n"
            "BinaryExpression(op='+', left=Literal(100), right=Identifier('count'))"
        ),
        "common_pitfalls": [
            "Modules bypassing the AST and duplicating parsing through ad-hoc regular expressions.",
            "Allowing downstream passes to synthesize code when the parser encountered fatal syntax errors.",
            "Labeling repair suggestions as validated without re-running the full compiler pipeline."
        ]
    },
    "symbol_table": {
        "title": "Symbol Table & Semantic Analysis",
        "phase": "Front-End: Phase 3",
        "summary": "Manages identifiers, type declarations, lexical scopes, and enforces static semantic constraints by traversing the AST.",
        "detailed_explanation": (
            "The Symbol Table is built by traversing the shared AST. It stores information about every identifier declared in the program: "
            "its type, category (variable, parameter, function), memory size, and lexical scope. "
            "Scopes are organized hierarchically (global -> function -> block). "
            "Semantic analysis uses this table to resolve identifier references, verify that variables are declared before use, "
            "detect identifier shadowing, and calculate memory offsets for intermediate code generation."
        ),
        "key_principles": [
            "AST-Driven Analysis: Symbol declarations and identifier references are extracted exclusively from AST nodes.",
            "Lexical Scoping: Inner scopes inherit definitions from outer scopes but can shadow them.",
            "Static Type Checking: Validates type compatibility in assignments, expressions, and function calls.",
            "Offset Calculation: Computes relative memory offsets within stack frames or global data segments."
        ],
        "code_example": (
            "// Nested Scopes in C:\n"
            "int x = 10;           // Global scope [x: int, offset 0]\n"
            "void foo() {\n"
            "    float x = 3.14;  // Shadows global x [x: float, offset 0 in foo stack frame]\n"
            "}"
        ),
        "common_pitfalls": [
            "Scanning raw tokens instead of traversing the AST to resolve references in their actual scope context.",
            "Using a flat dictionary instead of a hierarchical chained scope environment.",
            "Failing to clean up local symbols when exiting a block scope."
        ]
    },
    "intermediate_code": {
        "title": "Intermediate Code Generation (Three-Address Code)",
        "phase": "Middle-End: Phase 4",
        "summary": "Translates ASTs into a machine-independent, linear representation with explicit temporaries and control flow.",
        "detailed_explanation": (
            "Intermediate Representation (IR) decouples the compiler front-end (source language) from the back-end (target CPU). "
            "Three-Address Code (TAC) is a standard linear IR where every instruction has at most one operator and at most three address operands. "
            "Complex nested expressions in the AST are flattened into sequential temporary variables (t0, t1, t2), and high-level control structures "
            "(if, while, for) are decomposed into primitive conditional jumps and labels. "
            "Basic blocks partition the TAC into straight-line sequences with single entry and exit points for Control Flow Graph (CFG) analysis."
        ),
        "key_principles": [
            "Quadruple Representation: Tuples of (operator, argument1, argument2, result).",
            "Basic Block: A straight-line sequence of instructions with one entry point and one exit point.",
            "Control Flow Graph (CFG): Directed graph where nodes are Basic Blocks and edges are jump transitions.",
            "Linearization: Flattening hierarchical AST trees into sequential execution streams."
        ],
        "code_example": (
            "// High-level C expression:\n"
            "result = (a + b) * (c - d);\n\n"
            "// Three-Address Code (TAC):\n"
            "t0 = a + b\n"
            "t1 = c - d\n"
            "t2 = t0 * t1\n"
            "result = t2"
        ),
        "common_pitfalls": [
            "Generating redundant temporary variables without register reuse analysis.",
            "Generating unreachable basic blocks after unconditional jump statements.",
            "Prematurely coupling intermediate instructions to specific CPU register architectures."
        ]
    }
}

class AIService:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "groq").lower()
        self.groq_api_key = os.getenv("GROQ_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
        self.groq_model = os.getenv("GROQ_MODEL", "") or os.getenv("LLM_MODEL", "") or "qwen/qwen3.8-27b"
        # Groq enforces strict output token limits (e.g. 1000 OTPM on free tier Qwen 3.8 27B)
        self.max_tokens = min(int(os.getenv("GROQ_MAX_TOKENS", "900")), 900)
        self._recent_requests: Dict[str, Tuple[float, DiagnosisAndFixResponse]] = {}

    def has_groq_key(self) -> bool:
        return bool(self.groq_api_key and "your_" not in self.groq_api_key.lower())

    def diagnose_and_fix(self, source_code: str, parser_errors: List[CompilerError]) -> DiagnosisAndFixResponse:
        """
        AI Diagnostic & Repair Service.
        Integrates with Groq API (Qwen 3.8 27B) when configured.
        Falls back safely to local heuristic compiler engine when offline, rate-limited, or no API key.
        Strictly re-parses all proposed repairs through LexicalAnalyzer & CParser before
        marking as parser-validated.
        """
        # Debounce: prevent duplicate execution for identical code within 2.5 seconds
        cache_key = hashlib.sha256(source_code.encode("utf-8")).hexdigest()
        now = time.time()
        if cache_key in self._recent_requests:
            cached_time, cached_resp = self._recent_requests[cache_key]
            if now - cached_time < 2.5:
                logger.info("Returning debounced in-flight/recent repair response.")
                return cached_resp

        error_category = "unavailable"
        error_detail: Optional[str] = None
        recovery_guidance: Optional[str] = None

        if self.provider in ("groq", "qwen"):
            if self.has_groq_key():
                groq_resp, err_cat, err_det, rec_guid = self._call_groq_qwen(source_code, parser_errors)
                if groq_resp:
                    self._recent_requests[cache_key] = (now, groq_resp)
                    return groq_resp
                error_category = err_cat or "provider_error"
                error_detail = err_det
                recovery_guidance = rec_guid
            else:
                error_category = "invalid_credentials"
                error_detail = "Groq API key not configured in backend/.env."
                recovery_guidance = "Set GROQ_API_KEY in backend/.env to enable Qwen-powered repairs."
        else:
            error_category = "unavailable"
            error_detail = f"Configured LLM provider '{self.provider}' is not active."
            recovery_guidance = "Set LLM_PROVIDER=groq in backend/.env."

        # Heuristic fallback: explicitly labelled as heuristic
        heuristic_resp = self._heuristic_diagnose_and_repair(
            source_code=source_code,
            parser_errors=parser_errors,
            error_category=error_category,
            error_detail=error_detail,
            recovery_guidance=recovery_guidance
        )
        self._recent_requests[cache_key] = (now, heuristic_resp)
        return heuristic_resp

    def _parse_raw_llm_response(
        self,
        raw_content: str,
        finish_reason: Optional[str]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str], Optional[str]]:
        """
        Narrowly scoped, robust parser for LLM responses.
        Handles valid JSON, markdown fences, extracts outermost JSON objects,
        detects truncated and empty responses, and refuses ambiguous non-JSON text.
        Returns: (parsed_json_dict, error_category, error_detail, recovery_guidance)
        """
        # 1. Truncated output detection via finish_reason
        if finish_reason == "length":
            logger.warning("Groq completion stopped due to token limit (finish_reason=length).")
            return (
                None,
                "truncated_response",
                "AI provider response was truncated because the token completion limit was reached.",
                "The code or explanation exceeded token bounds. Local heuristic repair provided below."
            )

        # 2. Empty output detection
        if not raw_content or not raw_content.strip():
            logger.warning("Groq completion returned empty content.")
            return (
                None,
                "empty_response",
                "AI provider returned an empty response.",
                "The model did not generate output. Local heuristic repair provided below."
            )

        # 3. Strip reasoning / chain-of-thought tags (e.g. <think>...</think>) if present
        clean = re.sub(r"<think>[\s\S]*?</think>", "", raw_content).strip()

        # 4. Strip outer markdown code blocks if the response was wrapped in ```json or ```
        if clean.startswith("```"):
            clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.IGNORECASE)
            clean = re.sub(r"\s*```$", "", clean)
            clean = clean.strip()

        parsed: Optional[Dict[str, Any]] = None

        # 5. Attempt direct JSON deserialization
        try:
            candidate = json.loads(clean)
            if isinstance(candidate, dict):
                parsed = candidate
        except (json.JSONDecodeError, ValueError):
            pass

        # 6. If direct parse failed, attempt to isolate outermost JSON object {...}
        if parsed is None:
            first_brace = clean.find("{")
            last_brace = clean.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                slice_candidate = clean[first_brace:last_brace + 1]
                try:
                    candidate = json.loads(slice_candidate)
                    if isinstance(candidate, dict):
                        parsed = candidate
                except (json.JSONDecodeError, ValueError):
                    pass

        # 7. If still unparsed, fail safely without fabricating arbitrary code
        if parsed is None:
            logger.warning("Failed to parse AI response as valid JSON.")
            return (
                None,
                "malformed_response",
                "AI provider response could not be parsed as JSON.",
                "The model produced an unstructured response. Local heuristic repair provided below."
            )

        # 8. Structural validation: must contain 'corrected_code' string
        corrected_code = parsed.get("corrected_code")
        if not isinstance(corrected_code, str) or not corrected_code.strip():
            logger.warning("AI response JSON missing non-empty 'corrected_code' string.")
            return (
                None,
                "malformed_response",
                "AI response JSON was missing the required 'corrected_code' field.",
                "Model produced incomplete structure. Local heuristic repair provided below."
            )

        return parsed, None, None, None

    def _call_groq_qwen(
        self, source_code: str, parser_errors: List[CompilerError]
    ) -> Tuple[Optional[DiagnosisAndFixResponse], Optional[str], Optional[str], Optional[str]]:
        """
        Calls Groq Chat Completions API with configured model using JSON mode.
        Returns: (response, error_category, error_detail, recovery_guidance)
        """
        error_context = "\n".join([
            f"- Line {e.line}, Col {e.column} [{e.stage}]: {e.message}"
            for e in parser_errors
        ]) or "No static parse errors reported."

        system_prompt = (
            "You are a C compiler assistant. Repair syntax errors in student C code to produce clean C99 code. "
            "Respond ONLY with a JSON object with keys: 'corrected_code', 'summary', 'diagnostics', 'explanation'. "
            "Do not include any text before or after the JSON."
        )

        user_content = (
            f"Broken C code:\n```c\n{source_code}\n```\n\n"
            f"Parser diagnostics:\n{error_context}\n\n"
            "Respond with JSON."
        )

        payload: Dict[str, Any] = {
            "model": self.groq_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.1,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"}
        }

        # Bounded retry: attempt up to 2 times only if HTTP 429 provides a short retry delay
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                with httpx.Client(timeout=25.0) as client:
                    res = client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.groq_api_key}",
                            "Content-Type": "application/json"
                        },
                        json=payload
                    )

                # If response_format is unsupported by this specific model (HTTP 400), retry without it
                if res.status_code == 400 and "response_format" in res.text:
                    payload.pop("response_format", None)
                    with httpx.Client(timeout=25.0) as client:
                        res = client.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {self.groq_api_key}",
                                "Content-Type": "application/json"
                            },
                            json=payload
                        )

                # HTTP 401 Unauthorized / Invalid Credentials
                if res.status_code == 401:
                    return (
                        None,
                        "invalid_credentials",
                        "Groq authentication failed (HTTP 401). Invalid API key.",
                        "Verify and update GROQ_API_KEY in backend/.env."
                    )

                # HTTP 429 Rate Limit
                if res.status_code == 429:
                    retry_after = res.headers.get("retry-after")
                    reset_tokens = res.headers.get("x-ratelimit-reset-tokens", "")
                    
                    delay = 0.0
                    if retry_after:
                        try:
                            delay = float(retry_after)
                        except ValueError:
                            delay = 0.0
                    elif "ms" in reset_tokens:
                        try:
                            delay = float(reset_tokens.replace("ms", "").strip()) / 1000.0
                        except ValueError:
                            delay = 0.0

                    if attempt == 0 and 0.0 < delay <= 2.0:
                        logger.info(f"Groq 429 rate limit reset in {delay:.2f}s. Sleeping and retrying once.")
                        time.sleep(delay)
                        continue

                    reset_info = f" (Reset in {reset_tokens or retry_after})" if (reset_tokens or retry_after) else ""
                    return (
                        None,
                        "rate_limited",
                        f"Groq token rate limit exceeded (HTTP 429). Account limit: 1,000 tokens/min{reset_info}.",
                        "Wait 15-60 seconds for token replenishment. The local heuristic repair below is available immediately."
                    )

                # Non-200 Server / Provider error
                if res.status_code != 200:
                    logger.error(f"Groq API error ({res.status_code}): {res.text[:200]}")
                    return (
                        None,
                        "provider_error",
                        f"Groq API returned HTTP {res.status_code}.",
                        "Check Groq platform status or verify model availability."
                    )

                data = res.json()
                choice = data.get("choices", [{}])[0]
                content_str = choice.get("message", {}).get("content", "")
                finish_reason = choice.get("finish_reason")

                parsed, err_cat, err_det, rec_guid = self._parse_raw_llm_response(content_str, finish_reason)
                if not parsed:
                    return None, err_cat, err_det, rec_guid

                corrected_code = parsed.get("corrected_code", source_code)
                summary = parsed.get("summary", "AI repair generated via Groq Qwen.")
                explanation = parsed.get("explanation", "Repairs generated using Qwen on Groq.")
                educational_notes = parsed.get("educational_notes", [])

                diagnostics_raw = parsed.get("diagnostics", [])
                diagnostics: List[DiagnosticItem] = []
                if isinstance(diagnostics_raw, str):
                    diagnostics.append(DiagnosticItem(
                        stage="syntax",
                        line=1,
                        column=1,
                        message=diagnostics_raw,
                        fix_suggestion="Apply suggested fix."
                    ))
                elif isinstance(diagnostics_raw, list):
                    for d in diagnostics_raw:
                        if isinstance(d, dict):
                            diagnostics.append(DiagnosticItem(
                                stage=str(d.get("stage", "syntax")),
                                line=int(d.get("line", 1)),
                                column=int(d.get("column", 1)),
                                message=str(d.get("message", "Syntax correction")),
                                code_context=d.get("code_context"),
                                fix_suggestion=str(d.get("fix_suggestion", "Apply suggested change."))
                            ))
                        elif isinstance(d, str):
                            diagnostics.append(DiagnosticItem(
                                stage="syntax",
                                line=1,
                                column=1,
                                message=d,
                                fix_suggestion="Apply suggested change."
                            ))

                # =========================================================================
                # CRITICAL ARCHITECTURE RULE: Re-parse Groq proposed code with CParser
                # =========================================================================
                re_lexer = LexicalAnalyzer(corrected_code)
                re_tokens, re_lex_errors = re_lexer.tokenize()
                re_parser = CParser(re_tokens, corrected_code)
                _, re_syn_errors = re_parser.parse()

                re_errors = re_lex_errors + re_syn_errors
                is_parser_validated = (len(re_errors) == 0)
                validation_status = "PARSER_VALIDATED" if is_parser_validated else "SYNTAX_ERRORS_REMAIN"

                diff_lines = self._compute_diff(source_code, corrected_code)

                if is_parser_validated:
                    validation_disclaimer = (
                        "Parser validation confirms 0 syntax errors under standard C rules; "
                        "it does not guarantee runtime semantic or algorithmic correctness."
                    )
                else:
                    validation_disclaimer = (
                        f"Validation Failed: Proposed AI repair contains {len(re_errors)} residual syntax error(s). "
                        "It is NOT parser-validated."
                    )

                return (
                    DiagnosisAndFixResponse(
                        original_code=source_code,
                        corrected_code=corrected_code,
                        has_errors=len(diagnostics) > 0 or len(parser_errors) > 0,
                        is_parser_validated=is_parser_validated,
                        validation_status=validation_status,
                        summary=summary,
                        diagnostics=diagnostics,
                        diff_lines=diff_lines,
                        explanation=explanation,
                        educational_notes=educational_notes,
                        provider_used=f"Groq ({self.groq_model})",
                        repair_origin="ai",
                        provider_status="success",
                        error_detail=None,
                        recovery_guidance=None,
                        residual_error_count=len(re_errors),
                        residual_errors=re_errors,
                        validation_disclaimer=validation_disclaimer
                    ),
                    None, None, None
                )

            except httpx.RequestError as e:
                logger.error(f"Groq connection error: {e}")
                return (
                    None,
                    "unavailable",
                    f"Network error communicating with Groq API: {str(e)}",
                    "Verify internet connectivity and firewall rules."
                )
            except Exception as e:
                logger.error(f"Unexpected Groq error: {e}")
                return (
                    None,
                    "provider_error",
                    f"Unexpected error: {str(e)}",
                    "Review server logs for details."
                )

        return (
            None,
            "rate_limited",
            "Groq rate limit exceeded after retry.",
            "Wait 30-60 seconds for quota replenishment."
        )

    def _heuristic_diagnose_and_repair(
        self,
        source_code: str,
        parser_errors: List[CompilerError],
        error_category: str = "unavailable",
        error_detail: Optional[str] = None,
        recovery_guidance: Optional[str] = None
    ) -> DiagnosisAndFixResponse:
        """
        Deterministic local heuristic compiler repair engine.
        Strictly labeled as heuristic — never marked as AI-generated.
        Re-parses all candidate repairs and only assigns PARSER_VALIDATED if 0 syntax errors remain.
        """
        lines = source_code.splitlines()
        repaired_lines = list(lines)
        diagnostics: List[DiagnosticItem] = []
        educational_notes: List[str] = []

        has_stdio = any("#include <stdio.h>" in line or '#include "stdio.h"' in line for line in lines)
        uses_printf = any("printf(" in line or "puts(" in line or "scanf(" in line for line in lines)

        # 1. Missing stdio.h include
        if uses_printf and not has_stdio:
            repaired_lines.insert(0, "#include <stdio.h>")
            diagnostics.append(DiagnosticItem(
                stage="preprocessor",
                line=1,
                column=1,
                message="Implicit declaration of standard I/O function without <stdio.h>",
                code_context="printf / scanf usage",
                fix_suggestion="Include '#include <stdio.h>' at top of file."
            ))
            educational_notes.append("Standard I/O functions require prototypes declared in <stdio.h>.")

        # 2. Heuristic line-by-line repairs
        for idx, line in enumerate(repaired_lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("#"):
                continue

            # 2a. Misplaced semicolon in argument list or parenthesized expression (e.g. `printf("...",; id)`)
            if ",;" in line or re.search(r',\s*;', line):
                new_line = re.sub(r',\s*;\s*', ', ', line)
                if new_line != line:
                    repaired_lines[idx] = new_line
                    diagnostics.append(DiagnosticItem(
                        stage="syntax",
                        line=idx + 1,
                        column=line.find(";") + 1,
                        message="Misplaced semicolon ';' in argument list after comma",
                        code_context=stripped,
                        fix_suggestion="Remove misplaced semicolon from argument list."
                    ))
                    line = new_line
                    stripped = line.strip()

            if re.search(r'\(\s*;', line):
                new_line = re.sub(r'\(\s*;\s*', '(', line)
                if new_line != line:
                    repaired_lines[idx] = new_line
                    diagnostics.append(DiagnosticItem(
                        stage="syntax",
                        line=idx + 1,
                        column=line.find(";") + 1,
                        message="Misplaced semicolon ';' after opening parenthesis",
                        code_context=stripped,
                        fix_suggestion="Remove misplaced semicolon after parenthesis."
                    ))
                    line = new_line
                    stripped = line.strip()

            if re.search(r';\s*\)', line):
                new_line = re.sub(r';\s*\)', ')', line)
                if new_line != line:
                    repaired_lines[idx] = new_line
                    diagnostics.append(DiagnosticItem(
                        stage="syntax",
                        line=idx + 1,
                        column=line.rfind(";") + 1,
                        message="Misplaced semicolon ';' before closing parenthesis",
                        code_context=stripped,
                        fix_suggestion="Remove misplaced semicolon before parenthesis."
                    ))
                    line = new_line
                    stripped = line.strip()

            # 2b. Accidental assignment in if guard: if (sum = 30)
            if re.search(r'if\s*\(\s*[a-zA-Z_]\w*\s*=\s*[^=]', stripped):
                new_line = re.sub(r'(if\s*\(\s*[a-zA-Z_]\w*)\s*=\s*([^=])', r'\1 == \2', line)
                if new_line != line:
                    repaired_lines[idx] = new_line
                    diagnostics.append(DiagnosticItem(
                        stage="semantic",
                        line=idx + 1,
                        column=line.find("=") + 1,
                        message="Potential accidental assignment '=' inside condition guard",
                        code_context=stripped,
                        fix_suggestion="Replace assignment '=' with equality operator '=='."
                    ))
                    line = new_line
                    stripped = line.strip()

            # 2c. Check for missing statement terminators
            ends_with_block = stripped.endswith("{") or stripped.endswith("}")
            is_control = (stripped.startswith("if (") or stripped.startswith("if(") or
                          stripped.startswith("while (") or stripped.startswith("while(") or
                          stripped.startswith("for (") or stripped.startswith("for(") or
                          stripped.startswith("else"))
            is_func_def = re.match(r'^(int|void|float|double|char)\s+[a-zA-Z_]\w*\s*\([^;)]*\)\s*$', stripped)

            if not ends_with_block and not is_control and not is_func_def:
                if not stripped.endswith(";"):
                    repaired_lines[idx] = line + ";"
                    diagnostics.append(DiagnosticItem(
                        stage="syntax",
                        line=idx + 1,
                        column=len(line) + 1,
                        message="Missing statement terminator semicolon ';'",
                        code_context=stripped,
                        fix_suggestion="Append semicolon ';' to complete the statement."
                    ))

        # 3. Balance unmatched curly braces
        full_text = "\n".join(repaired_lines)
        open_braces = full_text.count("{")
        close_braces = full_text.count("}")

        if open_braces > close_braces:
            diff_count = open_braces - close_braces
            for _ in range(diff_count):
                repaired_lines.append("}")
            diagnostics.append(DiagnosticItem(
                stage="syntax",
                line=len(repaired_lines),
                column=1,
                message=f"Unmatched opening brace: Missing {diff_count} closing brace '}}'",
                code_context="End of file",
                fix_suggestion="Add closing brace '}' to enclose scope."
            ))

        # 4. Check main return 0
        has_main = any("main(" in l for l in repaired_lines)
        has_return = any("return" in l for l in repaired_lines)
        if has_main and not has_return:
            for i in range(len(repaired_lines) - 1, -1, -1):
                if "}" in repaired_lines[i]:
                    indent = "    "
                    repaired_lines.insert(i, f"{indent}return 0;")
                    diagnostics.append(DiagnosticItem(
                        stage="semantic",
                        line=i + 1,
                        column=len(indent) + 1,
                        message="Function 'main' missing explicit exit code",
                        code_context="int main()",
                        fix_suggestion="Add 'return 0;' to indicate successful termination."
                    ))
                    break

        corrected_code = "\n".join(repaired_lines)
        diff_lines = self._compute_diff(source_code, corrected_code)

        # Re-parse candidate repair through compiler pipeline
        re_lexer = LexicalAnalyzer(corrected_code)
        re_tokens, re_lex_errors = re_lexer.tokenize()
        re_parser = CParser(re_tokens, corrected_code)
        _, re_syn_errors = re_parser.parse()

        re_errors = re_lex_errors + re_syn_errors
        is_parser_validated = (len(re_errors) == 0)
        validation_status = "PARSER_VALIDATED" if is_parser_validated else "SYNTAX_ERRORS_REMAIN"

        if is_parser_validated:
            validation_disclaimer = (
                "Parser validation confirms 0 syntax errors under standard C rules; "
                "it does not guarantee runtime semantic or algorithmic correctness."
            )
            if error_category in ("unavailable", "invalid_credentials"):
                summary = "Repaired using local heuristic rules. 0 syntax errors remain."
            else:
                summary = f"Repaired using local heuristic rules ({error_category}). 0 syntax errors remain."
        else:
            validation_disclaimer = (
                f"Validation Failed: Local heuristic fallback could not resolve all syntax errors ({len(re_errors)} remaining). "
                "It is NOT parser-validated."
            )
            summary = f"Local heuristic fallback attempted repair, but {len(re_errors)} syntax error(s) remain ({error_category})."

        if error_category == "rate_limited":
            provider_used = "Local Heuristic Engine (Fallback: Groq Rate-Limited)"
        elif error_category == "malformed_response":
            provider_used = "Local Heuristic Engine (Fallback: Malformed AI Response)"
        elif error_category == "truncated_response":
            provider_used = "Local Heuristic Engine (Fallback: Truncated AI Response)"
        elif error_category == "empty_response":
            provider_used = "Local Heuristic Engine (Fallback: Empty AI Response)"
        elif error_category == "invalid_credentials":
            provider_used = "Local Heuristic Engine (Fallback: API Key Missing)"
        else:
            provider_used = f"Local Heuristic Engine (Fallback: {error_category})"

        explanation = (
            "Rule-based educational compiler repair evaluated statement delimiters, "
            "header dependencies, scope balancing, and function termination."
        )

        return DiagnosisAndFixResponse(
            original_code=source_code,
            corrected_code=corrected_code,
            has_errors=len(diagnostics) > 0 or len(parser_errors) > 0,
            is_parser_validated=is_parser_validated,
            validation_status=validation_status,
            summary=summary,
            diagnostics=diagnostics,
            diff_lines=diff_lines,
            explanation=explanation,
            educational_notes=educational_notes,
            provider_used=provider_used,
            repair_origin="heuristic",
            provider_status=error_category,
            error_detail=error_detail,
            recovery_guidance=recovery_guidance,
            residual_error_count=len(re_errors),
            residual_errors=re_errors,
            validation_disclaimer=validation_disclaimer
        )

    def explain_concept(self, concept_id: str, context_code: Optional[str] = None) -> ConceptExplanationResponse:
        key = concept_id.lower().replace("-", "_").strip()
        data = EDUCATIONAL_CONCEPTS.get(key)
        if not data:
            data = EDUCATIONAL_CONCEPTS["syntax_analysis"]
            key = "syntax_analysis"

        return ConceptExplanationResponse(
            concept_id=key,
            title=data["title"],
            phase=data["phase"],
            summary=data["summary"],
            detailed_explanation=data["detailed_explanation"],
            key_principles=data["key_principles"],
            code_example=data.get("code_example"),
            common_pitfalls=data.get("common_pitfalls", [])
        )

    def _compute_diff(self, original: str, corrected: str) -> List[DiffLine]:
        orig_lines = original.splitlines()
        corr_lines = corrected.splitlines()

        matcher = difflib.SequenceMatcher(None, orig_lines, corr_lines)
        diff_lines: List[DiffLine] = []

        old_idx = 1
        new_idx = 1

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for k in range(i1, i2):
                    diff_lines.append(DiffLine(
                        type="same",
                        content=orig_lines[k],
                        old_line_number=old_idx,
                        new_line_number=new_idx
                    ))
                    old_idx += 1
                    new_idx += 1
            elif tag == "delete":
                for k in range(i1, i2):
                    diff_lines.append(DiffLine(
                        type="remove",
                        content=orig_lines[k],
                        old_line_number=old_idx,
                        new_line_number=None
                    ))
                    old_idx += 1
            elif tag == "insert":
                for k in range(j1, j2):
                    diff_lines.append(DiffLine(
                        type="add",
                        content=corr_lines[k],
                        old_line_number=None,
                        new_line_number=new_idx
                    ))
                    new_idx += 1
            elif tag == "replace":
                for k in range(i1, i2):
                    diff_lines.append(DiffLine(
                        type="remove",
                        content=orig_lines[k],
                        old_line_number=old_idx,
                        new_line_number=None
                    ))
                    old_idx += 1
                for k in range(j1, j2):
                    diff_lines.append(DiffLine(
                        type="add",
                        content=corr_lines[k],
                        old_line_number=None,
                        new_line_number=new_idx
                    ))
                    new_idx += 1

        return diff_lines
