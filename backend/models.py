from __future__ import annotations
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

class Token(BaseModel):
    type: str = Field(..., description="Token class, e.g. KEYWORD, IDENTIFIER, INT_LITERAL, OPERATOR")
    value: str = Field(..., description="Lexeme value")
    line: int = Field(..., description="1-indexed line number")
    column: int = Field(..., description="1-indexed column number")
    length: int = Field(..., description="Character length of lexeme")
    category: str = Field(..., description="Display category: keyword, identifier, literal, operator, delimiter, comment")
    regex_pattern: str = Field(..., description="Formal language / regex specification pattern")
    description: str = Field(..., description="Educational explanation of this token")

class ASTNode(BaseModel):
    id: str = Field(..., description="Unique node identifier")
    type: str = Field(..., description="Grammar construct / AST node class")
    label: str = Field(..., description="Human-readable node summary")
    line: Optional[int] = Field(None, description="Source line number")
    column: Optional[int] = Field(None, description="Source column number")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Semantic metadata and node properties")
    children: List[ASTNode] = Field(default_factory=list, description="Child nodes in tree hierarchy")

class SymbolEntry(BaseModel):
    name: str = Field(..., description="Identifier name")
    type: str = Field(..., description="C data or return type, e.g. int, float, void")
    kind: str = Field(..., description="Category: variable, function, parameter, constant")
    scope: str = Field(..., description="Scope descriptor, e.g. global, main, block:L12")
    scope_level: int = Field(..., description="Nesting level of scope (0 for global, 1 for function, etc.)")
    line_declared: int = Field(..., description="Source line where identifier was declared")
    memory_size: int = Field(..., description="Estimated memory size in bytes")
    offset: int = Field(..., description="Stack frame or global segment offset")
    is_initialized: bool = Field(default=False, description="Whether symbol had initial value")
    references: int = Field(default=0, description="Count of occurrences/references in AST")

class TACInstruction(BaseModel):
    id: int = Field(..., description="Instruction index")
    op: str = Field(..., description="Operator or opcode (ADD, SUB, ASSIGN, JUMP, IF_FALSE, etc.)")
    arg1: Optional[str] = Field(None, description="First operand or source")
    arg2: Optional[str] = Field(None, description="Second operand")
    result: Optional[str] = Field(None, description="Target destination or label")
    representation: str = Field(..., description="Three-Address Code string, e.g. 't0 = a + b'")
    basic_block: str = Field(..., description="Enclosing basic block ID, e.g. B0, B1")
    line_reference: Optional[int] = Field(None, description="Original source line that yielded this instruction")
    explanation: str = Field(..., description="Educational note explaining this step of TAC generation")

class BasicBlock(BaseModel):
    id: str = Field(..., description="Block ID, e.g. B0, B1, B2")
    label: str = Field(..., description="Block header label if any")
    instruction_ids: List[int] = Field(default_factory=list, description="IDs of TAC instructions in this block")
    predecessors: List[str] = Field(default_factory=list, description="Predecessor block IDs in Control Flow")
    successors: List[str] = Field(default_factory=list, description="Successor block IDs in Control Flow")

class CompilerError(BaseModel):
    stage: Literal["lexical", "syntax", "semantic"] = Field(..., description="Compiler phase that encountered the error")
    message: str = Field(..., description="Descriptive diagnostic message")
    line: int = Field(..., description="Line number of error")
    column: int = Field(..., description="Column number of error")
    snippet: Optional[str] = Field(None, description="Code snippet where error occurred")
    suggestion: Optional[str] = Field(None, description="Educational suggestion to fix error")

class CompilerMetrics(BaseModel):
    token_count: int = 0
    ast_node_count: int = 0
    ast_max_depth: int = 0
    symbol_count: int = 0
    tac_count: int = 0
    basic_block_count: int = 0
    error_count: int = 0
    analysis_time_ms: float = 0.0

class SourceCodeRequest(BaseModel):
    source_code: str = Field(..., min_length=1, max_length=20000, description="C source code string")

class AnalysisResult(BaseModel):
    success: bool
    is_syntactically_valid: bool = True
    is_semantically_valid: bool = True
    has_partial_ast: bool = False
    tokens: List[Token] = Field(default_factory=list)
    ast: Optional[ASTNode] = None
    symbol_table: List[SymbolEntry] = Field(default_factory=list)
    intermediate_code: List[TACInstruction] = Field(default_factory=list)
    basic_blocks: List[BasicBlock] = Field(default_factory=list)
    errors: List[CompilerError] = Field(default_factory=list)
    metrics: CompilerMetrics = Field(default_factory=CompilerMetrics)

class DiffLine(BaseModel):
    type: Literal["same", "add", "remove"]
    content: str
    old_line_number: Optional[int] = None
    new_line_number: Optional[int] = None

class DiagnosticItem(BaseModel):
    stage: str
    line: int
    column: int
    message: str
    code_context: Optional[str] = None
    fix_suggestion: str

class DiagnosisAndFixRequest(BaseModel):
    source_code: str = Field(..., min_length=1, max_length=20000)

class DiagnosisAndFixResponse(BaseModel):
    original_code: str
    corrected_code: str
    has_errors: bool
    is_parser_validated: bool = Field(False, description="Whether corrected code was re-parsed and validated by CParser")
    validation_status: Literal["PARSER_VALIDATED", "SYNTAX_ERRORS_REMAIN", "UNVALIDATED"] = Field(..., description="Parser verification status of suggested fix")
    summary: str
    diagnostics: List[DiagnosticItem] = Field(default_factory=list)
    diff_lines: List[DiffLine] = Field(default_factory=list)
    explanation: str
    educational_notes: List[str] = Field(default_factory=list)
    provider_used: str
    repair_origin: Literal["ai", "heuristic"] = Field("heuristic", description="Whether fix was generated by AI model or local rule heuristic")
    provider_status: Literal[
        "success", "rate_limited", "invalid_credentials",
        "provider_error", "malformed_response", "truncated_response",
        "empty_response", "unavailable"
    ] = Field("success", description="Status code category of AI provider call")
    error_detail: Optional[str] = Field(None, description="Actual provider error message if AI generation was unavailable")
    recovery_guidance: Optional[str] = Field(None, description="Actionable recovery steps for the user")
    residual_error_count: int = Field(0, description="Count of syntax errors remaining in candidate repair")
    residual_errors: List[CompilerError] = Field(default_factory=list, description="List of syntax diagnostics if candidate code failed validation")
    validation_disclaimer: str = Field(
        "Parser validation verifies 0 grammar and syntax errors under C standard rules; it does not prove runtime algorithmic correctness.",
        description="Formal compiler verification disclaimer"
    )

class ConceptExplanationRequest(BaseModel):
    concept_id: str
    context_code: Optional[str] = None

class ConceptExplanationResponse(BaseModel):
    concept_id: str
    title: str
    phase: str
    summary: str
    detailed_explanation: str
    key_principles: List[str]
    code_example: Optional[str] = None
    common_pitfalls: List[str] = Field(default_factory=list)
