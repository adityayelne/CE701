export interface Token {
  type: string;
  value: string;
  line: number;
  column: number;
  length: number;
  category: 'keyword' | 'identifier' | 'literal' | 'operator' | 'delimiter' | 'comment' | 'preprocessor' | 'error';
  regex_pattern: string;
  description: string;
}

export interface ASTNode {
  id: string;
  type: string;
  label: string;
  line?: number;
  column?: number;
  attributes: Record<string, any>;
  children: ASTNode[];
}

export interface SymbolEntry {
  name: string;
  type: string;
  kind: 'variable' | 'function' | 'parameter' | 'constant';
  scope: string;
  scope_level: number;
  line_declared: number;
  memory_size: number;
  offset: number;
  is_initialized: boolean;
  references: number;
}

export interface TACInstruction {
  id: number;
  op: string;
  arg1?: string | null;
  arg2?: string | null;
  result?: string | null;
  representation: string;
  basic_block: string;
  line_reference?: number | null;
  explanation: string;
}

export interface BasicBlock {
  id: string;
  label: string;
  instruction_ids: number[];
  predecessors: string[];
  successors: string[];
}

export interface CompilerError {
  stage: 'lexical' | 'syntax' | 'semantic';
  message: string;
  line: number;
  column: number;
  snippet?: string | null;
  suggestion?: string | null;
}

export interface CompilerMetrics {
  token_count: number;
  ast_node_count: number;
  ast_max_depth: number;
  symbol_count: number;
  tac_count: number;
  basic_block_count: number;
  error_count: number;
  analysis_time_ms: number;
}

export interface AnalysisResult {
  success: boolean;
  is_syntactically_valid?: boolean;
  is_semantically_valid?: boolean;
  has_partial_ast?: boolean;
  tokens: Token[];
  ast?: ASTNode | null;
  symbol_table: SymbolEntry[];
  intermediate_code: TACInstruction[];
  basic_blocks: BasicBlock[];
  errors: CompilerError[];
  metrics: CompilerMetrics;
}

export interface DiffLine {
  type: 'same' | 'add' | 'remove';
  content: string;
  old_line_number?: number | null;
  new_line_number?: number | null;
}

export interface DiagnosticItem {
  stage: string;
  line: number;
  column: number;
  message: string;
  code_context?: string | null;
  fix_suggestion: string;
}

export interface DiagnosisAndFixResponse {
  original_code: string;
  corrected_code: string;
  has_errors: boolean;
  is_parser_validated: boolean;
  validation_status: 'PARSER_VALIDATED' | 'SYNTAX_ERRORS_REMAIN' | 'UNVALIDATED';
  summary: string;
  diagnostics: DiagnosticItem[];
  diff_lines: DiffLine[];
  explanation: string;
  educational_notes: string[];
  provider_used: string;
  repair_origin: 'ai' | 'heuristic';
  provider_status: 'success' | 'rate_limited' | 'invalid_credentials' | 'provider_error' | 'malformed_response' | 'truncated_response' | 'empty_response' | 'unavailable';
  error_detail?: string | null;
  recovery_guidance?: string | null;
  residual_error_count?: number;
  residual_errors?: CompilerError[];
  validation_disclaimer: string;
}

export type RepairState = 
  | 'IDLE'
  | 'AI_REQUESTING'
  | 'AI_RESPONSE_INVALID'
  | 'LOCAL_FALLBACK'
  | 'PARSER_VALIDATED'
  | 'SYNTAX_ERRORS_REMAIN'
  | 'REPAIR_REJECTED'
  | 'REPAIR_APPLIED';

export interface ConceptExplanation {
  concept_id: string;
  title: string;
  phase: string;
  summary: string;
  detailed_explanation: string;
  key_principles: string[];
  code_example?: string | null;
  common_pitfalls: string[];
}

export interface SampleProgram {
  id: string;
  title: string;
  description: string;
  category: 'valid' | 'broken';
  code: string;
}
