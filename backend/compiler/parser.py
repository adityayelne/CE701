import re
from typing import List, Optional, Tuple, Dict, Any, Set
try:
    from ..models import Token, ASTNode, CompilerError
except (ImportError, ValueError):
    from models import Token, ASTNode, CompilerError

STANDARD_TYPES = {
    "int", "float", "double", "char", "void", "long", "short", "bool", "_Bool",
    "size_t", "uint64_t", "uint32_t", "uint16_t", "uint8_t",
    "int64_t", "int32_t", "int16_t", "int8_t", "uintptr_t", "intptr_t"
}

TYPE_QUALIFIERS = {
    "const", "volatile", "static", "extern", "register", "inline", "restrict",
    "_Atomic", "_Alignas"
}

class CParser:
    def __init__(self, tokens: List[Token], source_code: str):
        # Filter out comments and whitespace tokens for parsing
        self.tokens = [t for t in tokens if t.category not in ("comment", "whitespace")]
        self.source_code = source_code
        self.pos = 0
        self.errors: List[CompilerError] = []
        self._node_counter = 0
        # Track typedef aliases and standard type names
        self.typedef_names: Set[str] = set(STANDARD_TYPES)
        # Track preprocessor definitions like #define BUFFER_SIZE 64
        self.defined_constants: Dict[str, str] = {}

    def _next_id(self, prefix: str = "node") -> str:
        self._node_counter += 1
        return f"{prefix}_{self._node_counter}"

    def peek(self, offset: int = 0) -> Optional[Token]:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return None

    def match_type(self, *types: str) -> bool:
        t = self.peek()
        return t is not None and t.type in types

    def match_val(self, *values: str) -> bool:
        t = self.peek()
        return t is not None and t.value in values

    def consume(self) -> Optional[Token]:
        if self.pos < len(self.tokens):
            t = self.tokens[self.pos]
            self.pos += 1
            return t
        return None

    def expect(self, val: str, suggestion: Optional[str] = None) -> Optional[Token]:
        t = self.peek()
        if t and t.value == val:
            return self.consume()
        prev = self.tokens[self.pos - 1] if self.pos > 0 else None
        line = prev.line if prev else 1
        col = (prev.column + prev.length) if prev else 1
        found = f"'{t.value}'" if t else "end of input"
        self._add_error(
            stage="syntax",
            message=f"Syntax error: Expected '{val}', but encountered {found}",
            line=line,
            column=col,
            suggestion=suggestion or f"Insert '{val}' at line {line}, column {col} to satisfy grammar rule."
        )
        return None

    def expect_identifier(self, context_description: str = "identifier") -> Optional[Token]:
        t = self.peek()
        if t and (t.type == "IDENTIFIER" or (t.type == "KEYWORD" and t.value in self.typedef_names)):
            return self.consume()
        line = t.line if t else 1
        col = t.column if t else 1
        found = f"'{t.value}'" if t else "end of input"
        self._add_error(
            stage="syntax",
            message=f"Syntax error: Expected {context_description}, but found {found}",
            line=line,
            column=col,
            suggestion=f"Provide a valid C identifier for {context_description}."
        )
        return None

    def _add_error(self, stage: str, message: str, line: int, column: int, suggestion: Optional[str] = None):
        # Prevent emitting duplicate diagnostics for the exact same location and message
        for existing in self.errors:
            if existing.line == line and existing.column == column and existing.message == message:
                return
        self.errors.append(CompilerError(
            stage=stage,
            message=message,
            line=line,
            column=column,
            snippet=self._get_line_snippet(line),
            suggestion=suggestion or "Inspect source line and adjust to conform with standard C grammar."
        ))

    def _get_line_snippet(self, line_num: int) -> str:
        lines = self.source_code.splitlines()
        if 1 <= line_num <= len(lines):
            return lines[line_num - 1].strip()
        return ""

    def _synchronize_to(self, *sync_tokens: str):
        """Skip tokens until one of the synchronization boundary tokens is reached."""
        while self.pos < len(self.tokens):
            tok = self.peek()
            if not tok:
                break
            if tok.value in sync_tokens:
                break
            self.consume()

    # =========================================================================
    # Program Root & Declarations
    # =========================================================================

    def parse(self) -> Tuple[ASTNode, List[CompilerError]]:
        root = ASTNode(
            id="root_prog",
            type="TranslationUnit",
            label="TranslationUnit (Source File)",
            line=1,
            column=1,
            attributes={"kind": "ProgramRoot"},
            children=[]
        )

        while self.pos < len(self.tokens):
            tok = self.peek()
            if not tok:
                break

            if tok.type == "PREPROCESSOR":
                prep_tok = self.consume()
                # Parse macros like #define BUFFER_SIZE 64
                self._handle_preprocessor_directive(prep_tok.value)
                root.children.append(ASTNode(
                    id=self._next_id("include"),
                    type="PreprocessorDirective",
                    label=prep_tok.value,
                    line=prep_tok.line,
                    column=prep_tok.column,
                    attributes={"directive": prep_tok.value}
                ))
            elif tok.value == "typedef":
                td = self.parse_typedef_declaration()
                if td:
                    root.children.append(td)
            elif self._is_declaration_start():
                decl = self.parse_declaration_or_function()
                if decl:
                    root.children.append(decl)
            elif tok.value == ";":
                self.consume()
            else:
                # Unexpected top-level token
                tok = self.consume()
                self._add_error(
                    stage="syntax",
                    message=f"Syntax error: Unexpected top-level token '{tok.value}'",
                    line=tok.line,
                    column=tok.column,
                    suggestion="Top-level constructs must be function definitions, typedefs, struct definitions, global variable declarations, or preprocessor directives."
                )
                self._synchronize_to(";", "}")
                if self.match_val(";"):
                    self.consume()

        return root, self.errors

    def _handle_preprocessor_directive(self, text: str):
        m = re.match(r'#define\s+([a-zA-Z_]\w*)\s+(.*)', text.strip())
        if m:
            name, val = m.group(1), m.group(2).strip()
            self.defined_constants[name] = val

    def _is_declaration_start(self) -> bool:
        tok = self.peek()
        if not tok:
            return False
        val = tok.value
        if val in ("typedef", "struct", "union", "enum"):
            return True
        if val in ("signed", "unsigned"):
            return True
        if val in TYPE_QUALIFIERS:
            return True
        if val in STANDARD_TYPES:
            return True
        if val in self.typedef_names:
            return True
        return False

    def parse_typedef_declaration(self) -> Optional[ASTNode]:
        td_tok = self.consume() # 'typedef'
        start_line = td_tok.line
        start_col = td_tok.column

        # Check if typedef struct { ... } Alias;
        if self.match_val("struct", "union"):
            struct_node = self.parse_struct_definition(is_typedef=True)
            # The alias name comes after the struct definition
            is_ptr = False
            if self.match_val("*"):
                self.consume()
                is_ptr = True

            alias_tok = self.expect_identifier("typedef alias name after struct definition")
            alias_name = alias_tok.value if alias_tok else "AnonymousAlias"
            if alias_tok:
                self.typedef_names.add(alias_name)

            self.expect(";", "Terminate typedef declaration with a semicolon ';'")

            full_alias = f"{alias_name}*" if is_ptr else alias_name
            return ASTNode(
                id=self._next_id("typedef"),
                type="TypedefDeclaration",
                label=f"typedef struct -> {full_alias}",
                line=start_line,
                column=start_col,
                attributes={"alias": alias_name, "is_pointer": is_ptr, "target_type": "struct"},
                children=[struct_node] if struct_node else []
            )
        else:
            # Standard typedef: typedef int MyInt; or typedef uint64_t Word;
            type_str, is_ptr, _ = self.parse_type_specifier()
            alias_tok = self.expect_identifier("typedef alias name")
            alias_name = alias_tok.value if alias_tok else "AnonymousAlias"
            if alias_tok:
                self.typedef_names.add(alias_name)

            self.expect(";", "Terminate typedef declaration with a semicolon ';'")
            full_type = f"{type_str}*" if is_ptr else type_str
            return ASTNode(
                id=self._next_id("typedef"),
                type="TypedefDeclaration",
                label=f"typedef {full_type} -> {alias_name}",
                line=start_line,
                column=start_col,
                attributes={"alias": alias_name, "is_pointer": is_ptr, "target_type": full_type},
                children=[]
            )

    def parse_struct_definition(self, is_typedef: bool = False) -> ASTNode:
        struct_tok = self.consume() # 'struct'
        name = ""
        if self.match_type("IDENTIFIER") or (self.peek() and self.peek().value not in ("{", ";", "*")):
            name_tok = self.consume()
            name = name_tok.value if name_tok else ""

        members: List[ASTNode] = []
        if self.match_val("{"):
            self.consume()
            while self.pos < len(self.tokens) and not self.match_val("}"):
                member = self.parse_struct_member()
                if member:
                    members.append(member)
                else:
                    self._synchronize_to(";", "}")
                    if self.match_val(";"):
                        self.consume()
            self.expect("}", "Close struct body with matching '}'")

        struct_node = ASTNode(
            id=self._next_id("struct"),
            type="StructDeclaration",
            label=f"struct {name}".strip() if name else "struct (anonymous)",
            line=struct_tok.line,
            column=struct_tok.column,
            attributes={
                "name": name,
                "is_anonymous": not bool(name),
                "member_count": len(members)
            },
            children=members
        )

        # Standalone struct definition (not part of typedef): struct Foo { ... };
        if not is_typedef and self.match_val(";"):
            self.consume()

        return struct_node

    def parse_struct_member(self) -> Optional[ASTNode]:
        if not self._is_declaration_start():
            tok = self.consume()
            if tok:
                self._add_error(
                    stage="syntax",
                    message=f"Syntax error: Unexpected token '{tok.value}' in struct body",
                    line=tok.line,
                    column=tok.column,
                    suggestion="Struct members must be valid type declarations (e.g. 'int id;' or 'uint64_t data;')."
                )
            return None

        type_str, is_ptr, meta = self.parse_type_specifier()
        name_tok = self.expect_identifier("struct member name")
        if not name_tok:
            self._synchronize_to(";", "}")
            if self.match_val(";"):
                self.consume()
            return None

        member_name = name_tok.value
        is_array = False
        array_size = ""
        if self.match_val("["):
            self.consume()
            is_array = True
            size_tok = self.peek()
            if size_tok and not self.match_val("]"):
                array_size = size_tok.value
                self.consume()
            self.expect("]", "Close array dimension with ']'")

        self.expect(";", "Terminate struct member declaration with a semicolon ';'")

        full_type = f"{type_str}*" if is_ptr else type_str
        if is_array:
            full_type = f"{full_type}[{array_size}]"

        return ASTNode(
            id=self._next_id("member"),
            type="StructMember",
            label=f"{full_type} {member_name}",
            line=name_tok.line,
            column=name_tok.column,
            attributes={
                "name": member_name,
                "type": full_type,
                "is_pointer": is_ptr,
                "is_array": is_array,
                "array_size": array_size,
                "is_atomic": meta.get("is_atomic", False),
                "alignas": meta.get("alignas", "")
            }
        )

    def parse_type_specifier(self) -> Tuple[str, bool, Dict[str, Any]]:
        """
        Parses type specifiers and qualifiers:
        e.g. const int*, _Alignas(64) _Atomic uint64_t, struct Point*, BufferItem
        """
        meta: Dict[str, Any] = {}
        qualifiers = []

        # Consume leading qualifiers: const, static, volatile, _Atomic, _Alignas(...)
        while self.pos < len(self.tokens):
            tok = self.peek()
            if not tok:
                break
            if tok.value == "_Alignas":
                self.consume()
                self.expect("(")
                align_val = ""
                if self.pos < len(self.tokens) and not self.match_val(")"):
                    align_val = self.consume().value
                self.expect(")")
                meta["alignas"] = align_val
            elif tok.value == "_Atomic":
                self.consume()
                meta["is_atomic"] = True
                # Could be _Atomic(type)
                if self.match_val("("):
                    self.consume()
                    inner_type, inner_ptr, _ = self.parse_type_specifier()
                    self.expect(")")
                    return f"_Atomic({inner_type})", inner_ptr, meta
            elif tok.value in TYPE_QUALIFIERS:
                qualifiers.append(self.consume().value)
            elif tok.value in ("signed", "unsigned"):
                qualifiers.append(self.consume().value)
            else:
                break

        # Base type
        base_tok = self.peek()
        type_str = "int"
        if base_tok:
            if base_tok.value in ("struct", "union"):
                struct_node = self.parse_struct_definition()
                type_str = struct_node.attributes.get("name", "struct")
                if not type_str:
                    type_str = "struct (anonymous)"
            elif base_tok.value in STANDARD_TYPES or base_tok.value in self.typedef_names:
                type_str = self.consume().value
            elif base_tok.type in ("IDENTIFIER", "KEYWORD"):
                type_str = self.consume().value

        # Optional pointer asterisks
        is_pointer = False
        while self.match_val("*"):
            self.consume()
            is_pointer = True

        return type_str, is_pointer, meta

    def parse_declaration_or_function(self) -> Optional[ASTNode]:
        # Check if standalone struct definition: struct Name { ... };
        if self.match_val("struct", "union"):
            peek2 = self.peek(1)
            peek3 = self.peek(2)
            # struct Name { ... };
            if (peek2 and peek2.value == "{") or (peek3 and peek3.value == "{"):
                return self.parse_struct_definition()

        type_str, is_pointer, meta = self.parse_type_specifier()

        # Identifier name
        name_tok = self.peek()
        if not name_tok or (name_tok.type != "IDENTIFIER" and name_tok.value not in self.typedef_names):
            self._add_error(
                stage="syntax",
                message=f"Syntax error: Expected identifier after type '{type_str}'",
                line=name_tok.line if name_tok else 1,
                column=name_tok.column if name_tok else 1,
                suggestion="Specify a variable or function name after the type specifier."
            )
            return None
        self.consume()
        name = name_tok.value

        # Check if function definition/prototype: next token is '('
        if self.match_val("("):
            return self.parse_function_definition(type_str, name, name_tok.line, name_tok.column, is_pointer)
        else:
            return self.parse_variable_declaration(type_str, name, name_tok.line, name_tok.column, is_pointer)

    def parse_function_definition(self, ret_type: str, name: str, line: int, col: int, is_pointer: bool) -> ASTNode:
        self.expect("(")
        params = []
        if not self.match_val(")"):
            params = self.parse_parameter_list()
        self.expect(")")

        full_ret = f"{ret_type}*" if is_pointer else ret_type
        func_node = ASTNode(
            id=self._next_id("func"),
            type="FunctionDeclaration",
            label=f"{full_ret} {name}(...)",
            line=line,
            column=col,
            attributes={
                "name": name,
                "return_type": full_ret,
                "parameter_count": len(params)
            },
            children=[]
        )

        for p in params:
            func_node.children.append(p)

        if self.match_val("{"):
            body = self.parse_compound_statement()
            func_node.children.append(body)
        elif self.match_val(";"):
            self.consume()
            func_node.attributes["is_prototype"] = True
        else:
            self._add_error(
                stage="syntax",
                message=f"Syntax error: Expected '{{' for function body or ';' for prototype of '{name}'",
                line=line,
                column=col,
                suggestion="Add '{' to open the function body block or ';' for forward declaration."
            )

        return func_node

    def parse_parameter_list(self) -> List[ASTNode]:
        params = []
        while self.pos < len(self.tokens):
            if not self._is_declaration_start():
                break
            type_str, is_ptr, _ = self.parse_type_specifier()

            name_tok = self.peek()
            p_name = ""
            if name_tok and (name_tok.type == "IDENTIFIER" or name_tok.value not in (",", ")")):
                self.consume()
                p_name = name_tok.value

            full_type = f"{type_str}*" if is_ptr else type_str
            params.append(ASTNode(
                id=self._next_id("param"),
                type="Parameter",
                label=f"Param: {full_type} {p_name}".strip(),
                line=name_tok.line if name_tok else 1,
                column=name_tok.column if name_tok else 1,
                attributes={"name": p_name, "type": full_type}
            ))

            if self.match_val(","):
                self.consume()
            else:
                break
        return params

    def parse_variable_declaration(self, var_type: str, var_name: str, line: int, col: int, is_pointer: bool) -> ASTNode:
        full_type = f"{var_type}*" if is_pointer else var_type
        is_array = False
        array_size = ""

        # Optional array dimension: var[BUFFER_SIZE]
        if self.match_val("["):
            self.consume()
            is_array = True
            dim_tok = self.peek()
            if dim_tok and not self.match_val("]"):
                array_size = dim_tok.value
                self.consume()
            self.expect("]")
            full_type = f"{full_type}[{array_size}]"

        decl_node = ASTNode(
            id=self._next_id("vardecl"),
            type="VariableDeclaration",
            label=f"VarDecl: {full_type} {var_name}",
            line=line,
            column=col,
            attributes={
                "name": var_name,
                "type": full_type,
                "is_array": is_array,
                "array_size": array_size
            },
            children=[]
        )

        # Optional initializer: = expr or = { ... }
        if self.match_val("="):
            self.consume()
            init_expr = self.parse_initializer()
            if init_expr:
                decl_node.children.append(init_expr)
                decl_node.attributes["has_initializer"] = True

        self.expect(";", "Terminate variable declaration with a semicolon ';'")
        return decl_node

    # =========================================================================
    # Initializers (Compound & Designated)
    # =========================================================================

    def parse_initializer(self) -> Optional[ASTNode]:
        if self.match_val("{"):
            open_brace = self.consume()
            elements: List[ASTNode] = []

            while self.pos < len(self.tokens) and not self.match_val("}"):
                if self.match_val("."):
                    # Designated member initializer: .id = 42
                    dot_tok = self.consume()
                    field_tok = self.expect_identifier("designator field name after '.'")
                    self.expect("=", "Designated initializer requires '=' after designator field name")
                    val_node = self.parse_initializer()
                    elem = ASTNode(
                        id=self._next_id("desig_init"),
                        type="DesignatedInitializer",
                        label=f".{field_tok.value if field_tok else 'field'} = ...",
                        line=dot_tok.line,
                        column=dot_tok.column,
                        attributes={"designator": field_tok.value if field_tok else "", "kind": "field"},
                        children=[val_node] if val_node else []
                    )
                    elements.append(elem)
                elif self.match_val("["):
                    # Designated array initializer: [0] = 42
                    bracket_tok = self.consume()
                    idx_expr = self.parse_expression()
                    self.expect("]")
                    self.expect("=")
                    val_node = self.parse_initializer()
                    elem = ASTNode(
                        id=self._next_id("desig_init"),
                        type="DesignatedInitializer",
                        label="[...] = ...",
                        line=bracket_tok.line,
                        column=bracket_tok.column,
                        attributes={"kind": "index"},
                        children=[c for c in (idx_expr, val_node) if c is not None]
                    )
                    elements.append(elem)
                elif self.match_val("{"):
                    nested = self.parse_initializer()
                    if nested:
                        elements.append(nested)
                else:
                    expr = self.parse_expression()
                    if expr:
                        elements.append(expr)

                if self.match_val(","):
                    self.consume()
                else:
                    break

            self.expect("}", "Close initializer list with '}'")
            return ASTNode(
                id=self._next_id("init_list"),
                type="InitializerList",
                label="InitializerList { ... }",
                line=open_brace.line,
                column=open_brace.column,
                attributes={"element_count": len(elements)},
                children=elements
            )
        else:
            return self.parse_expression()

    # =========================================================================
    # Statements
    # =========================================================================

    def parse_compound_statement(self) -> ASTNode:
        brace_tok = self.expect("{")
        line = brace_tok.line if brace_tok else 1
        col = brace_tok.column if brace_tok else 1

        block_node = ASTNode(
            id=self._next_id("block"),
            type="CompoundStatement",
            label="CompoundStatement { ... }",
            line=line,
            column=col,
            attributes={"scope": "block"},
            children=[]
        )

        while self.pos < len(self.tokens) and not self.match_val("}"):
            stmt = self.parse_statement()
            if stmt:
                block_node.children.append(stmt)
            else:
                # Synchronize to prevent infinite loop
                self.consume()

        self.expect("}", "Close code block with matching right brace '}'")
        return block_node

    def parse_statement(self) -> Optional[ASTNode]:
        tok = self.peek()
        if not tok:
            return None

        if tok.value == "{":
            return self.parse_compound_statement()
        elif tok.value == "if":
            return self.parse_if_statement()
        elif tok.value == "while":
            return self.parse_while_statement()
        elif tok.value == "for":
            return self.parse_for_statement()
        elif tok.value == "return":
            return self.parse_return_statement()
        elif self._is_declaration_start():
            return self.parse_declaration_or_function()
        elif tok.value == ";":
            self.consume()
            return ASTNode(
                id=self._next_id("empty_stmt"),
                type="EmptyStatement",
                label=";",
                line=tok.line,
                column=tok.column
            )
        else:
            expr = self.parse_expression()
            self.expect(";", "Statement must terminate with a semicolon ';'")
            return expr

    def parse_if_statement(self) -> ASTNode:
        if_tok = self.consume()
        self.expect("(")
        cond = self.parse_expression()
        self.expect(")")
        then_stmt = self.parse_statement()

        node = ASTNode(
            id=self._next_id("if"),
            type="IfStatement",
            label="if (...) statement",
            line=if_tok.line,
            column=if_tok.column,
            children=[c for c in (cond, then_stmt) if c is not None]
        )

        if self.match_val("else"):
            self.consume()
            else_stmt = self.parse_statement()
            if else_stmt:
                node.children.append(else_stmt)
                node.attributes["has_else"] = True

        return node

    def parse_while_statement(self) -> ASTNode:
        while_tok = self.consume()
        self.expect("(")
        cond = self.parse_expression()
        self.expect(")")
        body = self.parse_statement()

        return ASTNode(
            id=self._next_id("while"),
            type="WhileStatement",
            label="while (...) loop",
            line=while_tok.line,
            column=while_tok.column,
            children=[c for c in (cond, body) if c is not None]
        )

    def parse_for_statement(self) -> ASTNode:
        for_tok = self.consume()
        self.expect("(")

        init = None
        if not self.match_val(";"):
            if self._is_declaration_start():
                init = self.parse_declaration_or_function()
            else:
                init = self.parse_expression()
                self.expect(";")
        else:
            self.consume()

        cond = None
        if not self.match_val(";"):
            cond = self.parse_expression()
        self.expect(";")

        step = None
        if not self.match_val(")"):
            step = self.parse_expression()
        self.expect(")")

        body = self.parse_statement()

        children = [c for c in [init, cond, step, body] if c is not None]
        return ASTNode(
            id=self._next_id("for"),
            type="ForStatement",
            label="for (...) loop",
            line=for_tok.line,
            column=for_tok.column,
            children=children
        )

    def parse_return_statement(self) -> ASTNode:
        ret_tok = self.consume()
        expr = None
        if not self.match_val(";"):
            expr = self.parse_expression()
        self.expect(";", "Return statements must terminate with a semicolon ';'")

        return ASTNode(
            id=self._next_id("return"),
            type="ReturnStatement",
            label="return" + (f" {expr.label}" if expr else ""),
            line=ret_tok.line,
            column=ret_tok.column,
            children=[expr] if expr else []
        )

    # =========================================================================
    # Expressions & Precedence Hierarchy
    # =========================================================================

    def parse_expression(self) -> Optional[ASTNode]:
        return self.parse_assignment()

    def parse_assignment(self) -> Optional[ASTNode]:
        left = self.parse_logical_or()
        if not left:
            return None

        if self.match_val("=", "+=", "-=", "*=", "/=", "%="):
            op_tok = self.consume()
            right = self.parse_assignment()
            if right:
                return ASTNode(
                    id=self._next_id("assign"),
                    type="AssignmentExpression",
                    label=f"Assign: {op_tok.value}",
                    line=op_tok.line,
                    column=op_tok.column,
                    attributes={"operator": op_tok.value},
                    children=[left, right]
                )
        return left

    def parse_logical_or(self) -> Optional[ASTNode]:
        left = self.parse_logical_and()
        while self.match_val("||"):
            op = self.consume()
            right = self.parse_logical_and()
            if left and right:
                left = ASTNode(
                    id=self._next_id("logic_or"),
                    type="BinaryExpression",
                    label="LogicOr (||)",
                    line=op.line,
                    column=op.column,
                    attributes={"operator": "||"},
                    children=[left, right]
                )
        return left

    def parse_logical_and(self) -> Optional[ASTNode]:
        left = self.parse_equality()
        while self.match_val("&&"):
            op = self.consume()
            right = self.parse_equality()
            if left and right:
                left = ASTNode(
                    id=self._next_id("logic_and"),
                    type="BinaryExpression",
                    label="LogicAnd (&&)",
                    line=op.line,
                    column=op.column,
                    attributes={"operator": "&&"},
                    children=[left, right]
                )
        return left

    def parse_equality(self) -> Optional[ASTNode]:
        left = self.parse_relational()
        while self.match_val("==", "!="):
            op = self.consume()
            right = self.parse_relational()
            if left and right:
                left = ASTNode(
                    id=self._next_id("rel_eq"),
                    type="BinaryExpression",
                    label=f"Compare ({op.value})",
                    line=op.line,
                    column=op.column,
                    attributes={"operator": op.value},
                    children=[left, right]
                )
        return left

    def parse_relational(self) -> Optional[ASTNode]:
        left = self.parse_additive()
        while self.match_val("<", ">", "<=", ">="):
            op = self.consume()
            right = self.parse_additive()
            if left and right:
                left = ASTNode(
                    id=self._next_id("rel"),
                    type="BinaryExpression",
                    label=f"RelOp ({op.value})",
                    line=op.line,
                    column=op.column,
                    attributes={"operator": op.value},
                    children=[left, right]
                )
        return left

    def parse_additive(self) -> Optional[ASTNode]:
        left = self.parse_multiplicative()
        while self.match_val("+", "-"):
            op = self.consume()
            right = self.parse_multiplicative()
            if left and right:
                left = ASTNode(
                    id=self._next_id("binop"),
                    type="BinaryExpression",
                    label=f"AddSub ({op.value})",
                    line=op.line,
                    column=op.column,
                    attributes={"operator": op.value},
                    children=[left, right]
                )
        return left

    def parse_multiplicative(self) -> Optional[ASTNode]:
        left = self.parse_unary()
        while self.match_val("*", "/", "%"):
            op = self.consume()
            right = self.parse_unary()
            if left and right:
                left = ASTNode(
                    id=self._next_id("binop_mul"),
                    type="BinaryExpression",
                    label=f"MulDiv ({op.value})",
                    line=op.line,
                    column=op.column,
                    attributes={"operator": op.value},
                    children=[left, right]
                )
        return left

    def parse_unary(self) -> Optional[ASTNode]:
        if self.match_val("-", "!", "~", "++", "--", "*", "&"):
            op = self.consume()
            operand = self.parse_unary()
            if operand:
                return ASTNode(
                    id=self._next_id("unary"),
                    type="UnaryExpression",
                    label=f"UnaryOp ({op.value})",
                    line=op.line,
                    column=op.column,
                    attributes={"operator": op.value},
                    children=[operand]
                )
        return self.parse_postfix()

    def parse_postfix(self) -> Optional[ASTNode]:
        expr = self.parse_primary()
        if not expr:
            return None

        while True:
            if self.match_val("("):
                # Function call: expr(...)
                self.consume()
                args = []
                if not self.match_val(")"):
                    while self.pos < len(self.tokens) and not self.match_val(")"):
                        # Diagnostic recovery: Check for invalid ';' in argument list
                        if self.match_val(";"):
                            semi_tok = self.consume()
                            self._add_error(
                                stage="syntax",
                                message="Syntax error: Unexpected ';' in function argument list. Did you mean to use ','?",
                                line=semi_tok.line,
                                column=semi_tok.column,
                                suggestion="Replace ';' with ',' to separate function arguments."
                            )
                            continue

                        arg = self.parse_expression()
                        if arg:
                            args.append(arg)
                        else:
                            # Avoid infinite loop
                            if self.match_val(";"):
                                semi_tok = self.consume()
                                self._add_error(
                                    stage="syntax",
                                    message="Syntax error: Unexpected ';' in function argument list. Did you mean to use ','?",
                                    line=semi_tok.line,
                                    column=semi_tok.column,
                                    suggestion="Replace ';' with ',' to separate function arguments."
                                )
                            elif not self.match_val(")", ","):
                                self.consume()

                        if self.match_val(","):
                            self.consume()
                            # Check for immediate trailing/misplaced ';' after comma: ",;"
                            if self.match_val(";"):
                                semi_tok = self.consume()
                                self._add_error(
                                    stage="syntax",
                                    message="Syntax error: Unexpected ';' in function argument list immediately following ','.",
                                    line=semi_tok.line,
                                    column=semi_tok.column,
                                    suggestion="Remove invalid semicolon ';' from function call argument list."
                                )
                        else:
                            break
                self.expect(")")
                expr = ASTNode(
                    id=self._next_id("call"),
                    type="FunctionCall",
                    label=f"Call: {expr.label}(...)",
                    line=expr.line,
                    column=expr.column,
                    attributes={"function_name": expr.label, "argument_count": len(args)},
                    children=[expr] + args
                )
            elif self.match_val("."):
                dot_tok = self.consume()
                member_tok = self.expect_identifier("struct member name after '.'")
                member_name = member_tok.value if member_tok else "field"
                expr = ASTNode(
                    id=self._next_id("member_access"),
                    type="MemberAccess",
                    label=f"{expr.label}.{member_name}",
                    line=dot_tok.line,
                    column=dot_tok.column,
                    attributes={"operator": ".", "member": member_name},
                    children=[expr]
                )
            elif self.match_val("->"):
                arrow_tok = self.consume()
                member_tok = self.expect_identifier("struct pointer member name after '->'")
                member_name = member_tok.value if member_tok else "field"
                expr = ASTNode(
                    id=self._next_id("arrow_access"),
                    type="PointerMemberAccess",
                    label=f"{expr.label}->{member_name}",
                    line=arrow_tok.line,
                    column=arrow_tok.column,
                    attributes={"operator": "->", "member": member_name},
                    children=[expr]
                )
            elif self.match_val("["):
                bracket_tok = self.consume()
                idx_expr = self.parse_expression()
                self.expect("]")
                expr = ASTNode(
                    id=self._next_id("subscript"),
                    type="ArraySubscript",
                    label=f"{expr.label}[...]",
                    line=bracket_tok.line,
                    column=bracket_tok.column,
                    attributes={"operator": "[]"},
                    children=[expr, idx_expr] if idx_expr else [expr]
                )
            elif self.match_val("++", "--"):
                op = self.consume()
                expr = ASTNode(
                    id=self._next_id("postfix"),
                    type="PostfixExpression",
                    label=f"Postfix: {op.value}",
                    line=op.line,
                    column=op.column,
                    attributes={"operator": op.value},
                    children=[expr]
                )
            else:
                break
        return expr

    def parse_primary(self) -> Optional[ASTNode]:
        tok = self.peek()
        if not tok:
            return None

        if tok.type in ("INT_LITERAL", "FLOAT_LITERAL", "HEX_LITERAL", "STRING_LITERAL", "CHAR_LITERAL"):
            self.consume()
            return ASTNode(
                id=self._next_id("lit"),
                type="Literal",
                label=f"{tok.value}",
                line=tok.line,
                column=tok.column,
                attributes={"literal_type": tok.type, "value": tok.value}
            )
        elif tok.type in ("IDENTIFIER", "KEYWORD") and (tok.value in ("true", "false", "NULL") or tok.type == "IDENTIFIER"):
            self.consume()
            return ASTNode(
                id=self._next_id("id"),
                type="Identifier",
                label=f"{tok.value}",
                line=tok.line,
                column=tok.column,
                attributes={"name": tok.value}
            )
        elif tok.value == "(":
            self.consume()
            expr = self.parse_expression()
            self.expect(")")
            return expr
        else:
            self._add_error(
                stage="syntax",
                message=f"Syntax error: Unexpected token in expression: '{tok.value}'",
                line=tok.line,
                column=tok.column,
                suggestion="Check for missing operands, unmatched parentheses, or typos."
            )
            return None
