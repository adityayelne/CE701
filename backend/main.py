import time
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

try:
    from .models import (
        SourceCodeRequest, AnalysisResult, DiagnosisAndFixRequest,
        DiagnosisAndFixResponse, ConceptExplanationRequest, ConceptExplanationResponse,
        CompilerMetrics, ASTNode
    )
    from .compiler.lexer import LexicalAnalyzer
    from .compiler.parser import CParser
    from .compiler.symbol_table import SymbolTableAnalyzer
    from .compiler.ir_generator import IRGenerator
    from .compiler.ai_service import AIService
except (ImportError, ValueError):
    from models import (
        SourceCodeRequest, AnalysisResult, DiagnosisAndFixRequest,
        DiagnosisAndFixResponse, ConceptExplanationRequest, ConceptExplanationResponse,
        CompilerMetrics, ASTNode
    )
    from compiler.lexer import LexicalAnalyzer
    from compiler.parser import CParser
    from compiler.symbol_table import SymbolTableAnalyzer
    from compiler.ir_generator import IRGenerator
    from compiler.ai_service import AIService

load_dotenv()

app = FastAPI(
    title="CompilerLab API",
    description="Educational C Compiler Construction Learning Lab Backend",
    version="1.0.0"
)

# Enable CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai_service = AIService()

EDUCATIONAL_SAMPLES = [
    {
        "id": "factorial",
        "title": "Factorial with Loops & Scopes (Valid C)",
        "description": "Demonstrates function definition, nested variable declarations, while loop, and I/O call.",
        "category": "valid",
        "code": """#include <stdio.h>

int factorial(int n) {
    int result = 1;
    int i = 1;
    while (i <= n) {
        result = result * i;
        i = i + 1;
    }
    return result;
}

int main() {
    int num = 5;
    int answer = factorial(num);
    printf("Factorial of %d is %d\\n", num, answer);
    return 0;
}"""
    },
    {
        "id": "syntax_errors",
        "title": "Broken Syntax & Missing Delimiters (Broken C)",
        "description": "Common student bugs: missing header, missing semicolons, accidental assignment in if guard, unclosed brace.",
        "category": "broken",
        "code": """int main() {
    int x = 10
    int y = 20;
    int sum = x + y

    if (sum = 30) {
        printf("Sum is thirty\\n");
    
    return 0;
"""
    },
    {
        "id": "expressions",
        "title": "Expression Precedence & AST Tree (Valid C)",
        "description": "Tests operator precedence hierarchy: additive, multiplicative, relational, and logical operators.",
        "category": "valid",
        "code": """int evaluate(int a, int b, int c) {
    int step1 = a + b * c;
    int step2 = (a + b) * c;
    int is_valid = (step1 > 50) && (step2 <= 200);
    return is_valid;
}

int main() {
    int res = evaluate(5, 10, 4);
    return res;
}"""
    },
    {
        "id": "control_flow",
        "title": "Control Flow & Basic Blocks (Valid C)",
        "description": "Branching if/else structure demonstrating Basic Block leaders and Control Flow Graph transitions.",
        "category": "valid",
        "code": """int classify(int score) {
    int grade = 0;
    if (score >= 90) {
        grade = 4;
    } else {
        if (score >= 75) {
            grade = 3;
        } else {
            grade = 2;
        }
    }
    return grade;
}

int main() {
    int mark = 85;
    int g = classify(mark);
    return g;
}"""
    },
    {
        "id": "lock_free_ring_buffer",
        "title": "C11 Lock-Free Ring Buffer (Typedefs, Structs, Atomics)",
        "description": "Demonstrates C11 atomics, typedef struct aliases, designated initializers, aligned storage, and pointer member access.",
        "category": "valid",
        "code": """#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdatomic.h>

#define BUFFER_SIZE 64

typedef struct {
    int id;
    uint64_t data;
} BufferItem;

typedef struct {
    _Alignas(64) _Atomic uint64_t head;
    _Alignas(64) _Atomic uint64_t tail;
    BufferItem items[BUFFER_SIZE];
} LockFreeRingBuffer;

void ring_buffer_init(LockFreeRingBuffer *rb) {
    atomic_init(&rb->head, 0);
    atomic_init(&rb->tail, 0);
}

bool ring_buffer_push(LockFreeRingBuffer *rb, BufferItem item) {
    uint64_t current_tail = atomic_load(&rb->tail);
    uint64_t current_head = atomic_load(&rb->head);
    if ((current_tail + 1) % BUFFER_SIZE == current_head) {
        return false;
    }
    rb->items[current_tail] = item;
    atomic_store(&rb->tail, (current_tail + 1) % BUFFER_SIZE);
    return true;
}

int main() {
    LockFreeRingBuffer rb;
    ring_buffer_init(&rb);

    BufferItem item = { .id = 42, .data = 100 };
    ring_buffer_push(&rb, item);

    printf("Pushed item with id: %d, data: %lu\\n", item.id);
    return 0;
}"""
    }
]

def calculate_ast_depth(node: ASTNode) -> int:
    if not node or not node.children:
        return 1
    return 1 + max(calculate_ast_depth(c) for c in node.children)

def count_ast_nodes(node: ASTNode) -> int:
    if not node:
        return 0
    return 1 + sum(count_ast_nodes(c) for c in node.children)

@app.get("/api/health")
def health_check():
    provider_name = f"groq ({ai_service.groq_model})" if (ai_service.provider in ("groq", "qwen") and ai_service.has_groq_key()) else "offline (local heuristic)"
    return {
        "status": "healthy",
        "service": "CompilerLab Educational Compiler Engine",
        "ai_provider": provider_name
    }

@app.get("/api/samples")
def get_samples():
    return EDUCATIONAL_SAMPLES

@app.post("/api/analyze", response_model=AnalysisResult)
def analyze_code(req: SourceCodeRequest):
    """
    Executes the shared compiler pipeline:
    1. Lexical Analysis: Tokenizes source code into Token stream with line/col.
    2. Syntax Analysis: Consumes tokens to produce canonical ASTNode hierarchy & syntax diagnostics.
    3. Symbol Table: Strictly traverses the shared ASTNode tree to construct lexical scopes and validate declarations.
    4. Intermediate Code: Strictly traverses the shared ASTNode tree to generate linear TAC and basic blocks.
    """
    start_time = time.perf_counter()
    errors = []

    # Phase 1: Lexical Analysis
    lexer = LexicalAnalyzer(req.source_code)
    tokens, lex_errors = lexer.tokenize()
    errors.extend(lex_errors)

    # Phase 2: Syntax Analysis & AST Generation (Source of Truth)
    parser = CParser(tokens, req.source_code)
    ast_root, syn_errors = parser.parse()
    errors.extend(syn_errors)

    has_partial_ast = bool(ast_root and len(ast_root.children) > 0)
    is_syntactically_valid = (len(lex_errors) == 0 and len(syn_errors) == 0)

    # Phase 3: Symbol Table & Semantic Analysis (Traverses shared AST exclusively)
    symbol_table = []
    sem_errors = []
    if ast_root:
        symbol_analyzer = SymbolTableAnalyzer(ast_root)
        symbol_table, sem_errors = symbol_analyzer.analyze()
        errors.extend(sem_errors)

    is_semantically_valid = (len(sem_errors) == 0)

    # Phase 4: Intermediate Code Generation (Traverses shared AST exclusively)
    tac_instructions = []
    basic_blocks = []
    if ast_root and (is_syntactically_valid or has_partial_ast):
        ir_gen = IRGenerator(ast_root)
        tac_instructions, basic_blocks = ir_gen.generate()

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    node_count = count_ast_nodes(ast_root) if ast_root else 0
    max_depth = calculate_ast_depth(ast_root) if ast_root else 0

    metrics = CompilerMetrics(
        token_count=len(tokens),
        ast_node_count=node_count,
        ast_max_depth=max_depth,
        symbol_count=len(symbol_table),
        tac_count=len(tac_instructions),
        basic_block_count=len(basic_blocks),
        error_count=len(errors),
        analysis_time_ms=elapsed_ms
    )

    return AnalysisResult(
        success=(len(errors) == 0),
        is_syntactically_valid=is_syntactically_valid,
        is_semantically_valid=is_semantically_valid,
        has_partial_ast=has_partial_ast,
        tokens=tokens,
        ast=ast_root,
        symbol_table=symbol_table,
        intermediate_code=tac_instructions,
        basic_blocks=basic_blocks,
        errors=errors,
        metrics=metrics
    )

@app.post("/api/ai/diagnose-and-fix", response_model=DiagnosisAndFixResponse)
def diagnose_and_fix(req: DiagnosisAndFixRequest):
    # Run analysis to harvest existing errors first
    lexer = LexicalAnalyzer(req.source_code)
    tokens, lex_errs = lexer.tokenize()
    parser = CParser(tokens, req.source_code)
    ast, syn_errs = parser.parse()
    
    sem_errs = []
    if ast:
        sym_analyzer = SymbolTableAnalyzer(ast)
        _, sem_errs = sym_analyzer.analyze()

    all_errors = lex_errs + syn_errs + sem_errs
    return ai_service.diagnose_and_fix(req.source_code, all_errors)

@app.post("/api/ai/explain-concept", response_model=ConceptExplanationResponse)
def explain_concept(req: ConceptExplanationRequest):
    return ai_service.explain_concept(req.concept_id, req.context_code)
