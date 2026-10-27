import re
from typing import List, Tuple
try:
    from ..models import Token, CompilerError
except (ImportError, ValueError):
    from models import Token, CompilerError

KEYWORDS = {
    "auto", "break", "case", "char", "const", "continue", "default", "do",
    "double", "else", "enum", "extern", "float", "for", "goto", "if",
    "int", "long", "register", "return", "short", "signed", "sizeof", "static",
    "struct", "switch", "typedef", "union", "unsigned", "void", "volatile", "while",
    "bool", "true", "false", "NULL",
    "_Atomic", "_Alignas", "_Alignof", "_Bool", "_Static_assert", "_Generic", "_Noreturn", "_Thread_local",
    "inline", "restrict",
    "size_t", "uint64_t", "uint32_t", "uint16_t", "uint8_t",
    "int64_t", "int32_t", "int16_t", "int8_t", "uintptr_t", "intptr_t"
}

TYPES = {
    "int", "float", "double", "char", "void", "long", "short", "bool",
    "_Bool", "_Atomic",
    "size_t", "uint64_t", "uint32_t", "uint16_t", "uint8_t",
    "int64_t", "int32_t", "int16_t", "int8_t", "uintptr_t", "intptr_t"
}

TOKEN_SPECS = [
    # (Type, Regex, Category, Description)
    ("PREPROCESSOR", r'#[a-zA-Z_]\w*(?:[^\n\\]|\\.)*', "preprocessor", "C preprocessor directive processed before lexical translation"),
    ("COMMENT_MULTI", r'/\*[\s\S]*?\*/', "comment", "Multi-line C comment block (discarded during semantic translation)"),
    ("COMMENT_SINGLE", r'//[^\n]*', "comment", "Single-line comment to end of line"),
    ("STRING_LITERAL", r'"(?:\\.|[^"\\])*"', "literal", "Sequence of characters enclosed in double quotes (string literal, null-terminated array)"),
    ("CHAR_LITERAL", r"'(?:\\.|[^'\\])'", "literal", "Single character constant enclosed in single quotes"),
    ("FLOAT_LITERAL", r'\b\d+\.\d+(?:[eE][+-]?\d+)?\b|\b\d+[eE][+-]?\d+\b', "literal", "Floating-point numeric constant (IEEE 754 representation)"),
    ("HEX_LITERAL", r'\b0[xX][0-9a-fA-F]+\b', "literal", "Hexadecimal base-16 integer constant"),
    ("INT_LITERAL", r'\b\d+\b', "literal", "Decimal base-10 integer constant"),
    ("OP_ARROW", r'->', "operator", "Structure/union pointer member access operator"),
    ("OP_REL", r'==|!=|<=|>=', "operator", "Relational comparison operator (yields boolean condition 0 or 1)"),
    ("OP_LOGIC", r'&&|\|\|', "operator", "Short-circuit logical operator (AND / OR)"),
    ("OP_INC_DEC", r'\+\+|--', "operator", "Unary increment or decrement operator"),
    ("OP_ASSIGN_COMPOUND", r'\+=|-=|\*=|/=|%=', "operator", "Compound arithmetic assignment operator"),
    ("IDENTIFIER", r'[a-zA-Z_][a-zA-Z0-9_]*', "identifier", "User-defined identifier or keyword (resolved via symbol table lookup)"),
    ("OPERATOR", r'[+\-*/%=<>!&|^~]', "operator", "Arithmetic, relational, or bitwise operator"),
    ("DELIMITER", r'[(){}\[\];,.]', "delimiter", "Syntactic delimiter or punctuator structuring expression and statement boundaries"),
    ("NEWLINE", r'\n', "whitespace", "Newline character"),
    ("WHITESPACE", r'[ \t\r]+', "whitespace", "Horizontal whitespace (skipped by lexer)"),
    ("MISMATCH", r'.', "error", "Unrecognized character violating C lexical grammar"),
]

COMPILED_SPECS = [(tok_type, re.compile(regex), regex, cat, desc) for tok_type, regex, cat, desc in TOKEN_SPECS]

class LexicalAnalyzer:
    def __init__(self, source_code: str):
        self.source_code = source_code
        self.tokens: List[Token] = []
        self.errors: List[CompilerError] = []

    def tokenize(self) -> Tuple[List[Token], List[CompilerError]]:
        self.tokens = []
        self.errors = []
        pos = 0
        line = 1
        col = 1
        length = len(self.source_code)

        while pos < length:
            matched = False
            for tok_type, regex_obj, raw_pattern, category, description in COMPILED_SPECS:
                match = regex_obj.match(self.source_code, pos)
                if match:
                    val = match.group(0)
                    tok_len = len(val)

                    if tok_type == "WHITESPACE":
                        col += tok_len
                    elif tok_type == "NEWLINE":
                        line += 1
                        col = 1
                    elif tok_type in ("COMMENT_SINGLE", "COMMENT_MULTI"):
                        # Count newlines inside comment
                        newlines = val.count('\n')
                        if newlines > 0:
                            last_nl = val.rfind('\n')
                            col = len(val) - last_nl
                            line += newlines
                        else:
                            col += tok_len
                        # Also record comment token for educational completeness
                        self.tokens.append(Token(
                            type="COMMENT",
                            value=val,
                            line=line - (newlines if newlines > 0 else 0),
                            column=col - tok_len if newlines == 0 else 1,
                            length=tok_len,
                            category="comment",
                            regex_pattern=raw_pattern,
                            description=description
                        ))
                    elif tok_type == "IDENTIFIER":
                        if val in KEYWORDS:
                            self.tokens.append(Token(
                                type="KEYWORD",
                                value=val,
                                line=line,
                                column=col,
                                length=tok_len,
                                category="keyword",
                                regex_pattern=f"\\b{val}\\b",
                                description=f"Reserved C keyword '{val}' with fixed semantic role"
                            ))
                        else:
                            self.tokens.append(Token(
                                type="IDENTIFIER",
                                value=val,
                                line=line,
                                column=col,
                                length=tok_len,
                                category="identifier",
                                regex_pattern=r'[a-zA-Z_][a-zA-Z0-9_]*',
                                description=f"User identifier '{val}' representing a variable, function, or type name"
                            ))
                        col += tok_len
                    elif tok_type == "MISMATCH":
                        self.errors.append(CompilerError(
                            stage="lexical",
                            message=f"Illegal or unrecognized character '{val}' (ASCII {ord(val)})",
                            line=line,
                            column=col,
                            snippet=val,
                            suggestion="Remove or replace this invalid character with valid C syntax."
                        ))
                        col += tok_len
                    else:
                        # Preprocessor, literals, operators, delimiters
                        self.tokens.append(Token(
                            type=tok_type,
                            value=val,
                            line=line,
                            column=col,
                            length=tok_len,
                            category=category,
                            regex_pattern=raw_pattern,
                            description=description
                        ))
                        col += tok_len

                    pos += tok_len
                    matched = True
                    break

            if not matched:
                # Fallback for unexpected unicode or non-ascii
                char = self.source_code[pos]
                self.errors.append(CompilerError(
                    stage="lexical",
                    message=f"Lexer encountered unhandled character: {repr(char)}",
                    line=line,
                    column=col,
                    snippet=char,
                    suggestion="Verify that source file uses ASCII or standard UTF-8 characters."
                ))
                pos += 1
                col += 1

        return self.tokens, self.errors
