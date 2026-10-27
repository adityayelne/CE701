import re
from typing import List, Dict, Tuple, Optional
try:
    from ..models import ASTNode, SymbolEntry, CompilerError
except (ImportError, ValueError):
    from models import ASTNode, SymbolEntry, CompilerError

TYPE_SIZES = {
    "char": 1,
    "bool": 1,
    "_Bool": 1,
    "short": 2,
    "int": 4,
    "float": 4,
    "long": 8,
    "double": 8,
    "pointer": 8,
    "void": 0,
    "uint64_t": 8,
    "int64_t": 8,
    "uint32_t": 4,
    "int32_t": 4,
    "uint16_t": 2,
    "int16_t": 2,
    "uint8_t": 1,
    "int8_t": 1,
    "size_t": 8,
    "uintptr_t": 8,
    "intptr_t": 8
}

STANDARD_BUILTINS = {
    "printf", "scanf", "malloc", "free", "exit", "strlen", 
    "strcmp", "strcpy", "puts", "getchar", "putchar", "sqrt", "pow",
    "true", "false", "NULL",
    # C11 Atomics
    "atomic_init", "atomic_load", "atomic_store", "atomic_exchange",
    "atomic_compare_exchange_strong", "atomic_compare_exchange_weak",
    "atomic_fetch_add", "atomic_fetch_sub", "atomic_fetch_or",
    "atomic_fetch_xor", "atomic_fetch_and", "atomic_thread_fence",
    "atomic_signal_fence", "atomic_is_lock_free",
    "memory_order_relaxed", "memory_order_consume", "memory_order_acquire",
    "memory_order_release", "memory_order_acq_rel", "memory_order_seq_cst"
}

def estimate_size(type_str: str) -> int:
    if not type_str:
        return 4
    if "*" in type_str:
        return TYPE_SIZES["pointer"]
    base = type_str.replace("unsigned", "").replace("signed", "").replace("_Atomic", "").strip()
    # Check if array: type[N]
    if "[" in base and "]" in base:
        m = re.match(r'^(.*?)\[(\d+)\]$', base)
        if m:
            elem_t, count = m.group(1), int(m.group(2))
            return estimate_size(elem_t) * count
    return TYPE_SIZES.get(base, 4)

class SymbolTableAnalyzer:
    """
    Symbol Table and Semantic Analyzer.
    Strictly traverses the Shared AST produced by CParser.
    Does NOT inspect raw source text or tokens directly.
    """
    def __init__(self, ast: ASTNode):
        self.ast = ast
        self.entries: List[SymbolEntry] = []
        self.errors: List[CompilerError] = []
        self._current_scope = "global"
        self._scope_depth = 0
        self._offset = 0
        # Map: scope_name -> list of declared symbol names
        self._declared_in_scope: Dict[str, List[str]] = {"global": []}
        # Parent scope mapping for lexical lookup: child_scope -> parent_scope
        self._parent_scope: Dict[str, Optional[str]] = {"global": None}
        # Reference counts per symbol key (scope, name)
        self._ref_counts: Dict[str, int] = {}
        # Unresolved identifier usages discovered in AST
        self._ast_identifier_usages: List[Tuple[str, int, int, str]] = [] # (name, line, col, scope_at_usage)

    def analyze(self) -> Tuple[List[SymbolEntry], List[CompilerError]]:
        self.entries = []
        self.errors = []
        self._offset = 0
        self._declared_in_scope = {"global": []}
        self._parent_scope = {"global": None}
        self._ref_counts = {}
        self._ast_identifier_usages = []

        if not self.ast:
            return self.entries, self.errors

        # Pass 1: Traverse AST to collect declarations, scopes, and identifier usage nodes
        self._traverse_declarations_and_usages(self.ast)

        # Pass 2: Resolve identifier usages against scoped symbol hierarchy
        for name, line, col, usage_scope in self._ast_identifier_usages:
            symbol_found = self._lookup_symbol(name, usage_scope)
            if symbol_found:
                # Increment reference count for that symbol
                self._ref_counts[symbol_found] = self._ref_counts.get(symbol_found, 0) + 1
            elif name not in STANDARD_BUILTINS:
                self.errors.append(CompilerError(
                    stage="semantic",
                    message=f"Semantic error: Undeclared identifier '{name}' in scope '{usage_scope}'",
                    line=line,
                    column=col,
                    snippet=name,
                    suggestion=f"Declare '{name}' (e.g. 'int {name};') in scope before referencing it."
                ))

        # Update reference counts on entries
        for entry in self.entries:
            key = f"{entry.scope}::{entry.name}"
            entry.references = self._ref_counts.get(key, 0)

        return self.entries, self.errors

    def _traverse_declarations_and_usages(self, node: ASTNode):
        if not node:
            return

        prev_scope = self._current_scope
        prev_depth = self._scope_depth

        if node.type == "PreprocessorDirective":
            # Extract #define CONST_NAME VAL
            val = node.attributes.get("directive", node.label)
            m = re.match(r'#define\s+([a-zA-Z_]\w*)', val.strip())
            if m:
                macro_name = m.group(1)
                self._register_symbol(
                    name=macro_name,
                    type_str="macro constant",
                    kind="constant",
                    line=node.line or 1,
                    size=4,
                    is_initialized=True
                )

        elif node.type == "TypedefDeclaration":
            alias = node.attributes.get("alias", "alias")
            target = node.attributes.get("target_type", "type")
            self._register_symbol(
                name=alias,
                type_str=f"typedef -> {target}",
                kind="typedef",
                line=node.line or 1,
                size=estimate_size(target)
            )

        elif node.type == "StructDeclaration":
            name = node.attributes.get("name", "")
            if name:
                self._register_symbol(
                    name=f"struct {name}",
                    type_str="struct definition",
                    kind="struct",
                    line=node.line or 1,
                    size=0
                )

        elif node.type == "FunctionDeclaration":
            name = node.attributes.get("name", "func")
            ret_type = node.attributes.get("return_type", "void")
            
            # Register function in enclosing scope
            self._register_symbol(
                name=name,
                type_str=f"func() -> {ret_type}",
                kind="function",
                line=node.line or 1,
                size=0
            )

            # Enter function scope
            fn_scope = f"function:{name}"
            self._parent_scope[fn_scope] = self._current_scope
            self._current_scope = fn_scope
            self._scope_depth += 1
            self._declared_in_scope[fn_scope] = []

        elif node.type == "Parameter":
            name = node.attributes.get("name", "p")
            type_str = node.attributes.get("type", "int")
            self._register_symbol(
                name=name,
                type_str=type_str,
                kind="parameter",
                line=node.line or 1,
                size=estimate_size(type_str)
            )

        elif node.type == "VariableDeclaration":
            name = node.attributes.get("name", "var")
            type_str = node.attributes.get("type", "int")
            has_init = node.attributes.get("has_initializer", False)
            self._register_symbol(
                name=name,
                type_str=type_str,
                kind="variable",
                line=node.line or 1,
                size=estimate_size(type_str),
                is_initialized=has_init
            )

        elif node.type == "CompoundStatement" and not prev_scope.endswith(node.id) and prev_scope != "global":
            # Nested block scope
            block_scope = f"{prev_scope}/block@{node.line or 0}"
            self._parent_scope[block_scope] = self._current_scope
            self._current_scope = block_scope
            self._scope_depth += 1
            self._declared_in_scope[block_scope] = []

        elif node.type in ("MemberAccess", "PointerMemberAccess"):
            # Member access: e.g. rb->head or item.id
            # Only record usage of the base object (rb or item), NOT the member field name
            if node.children:
                self._traverse_declarations_and_usages(node.children[0])
            self._current_scope = prev_scope
            self._scope_depth = prev_depth
            return

        elif node.type == "Identifier":
            # Record AST identifier reference
            id_name = node.attributes.get("name", node.label)
            line = node.line or 1
            col = node.column or 1
            self._ast_identifier_usages.append((id_name, line, col, self._current_scope))

        # Recurse children
        for child in node.children:
            self._traverse_declarations_and_usages(child)

        self._current_scope = prev_scope
        self._scope_depth = prev_depth

    def _register_symbol(self, name: str, type_str: str, kind: str, line: int, size: int, is_initialized: bool = False):
        scope_list = self._declared_in_scope.setdefault(self._current_scope, [])
        if name in scope_list and kind != "function":
            self.errors.append(CompilerError(
                stage="semantic",
                message=f"Redefinition error: Symbol '{name}' is already declared in scope '{self._current_scope}'",
                line=line,
                column=1,
                snippet=f"{type_str} {name}",
                suggestion=f"Use a distinct identifier name or remove duplicate declaration of '{name}'."
            ))
        else:
            scope_list.append(name)

        entry = SymbolEntry(
            name=name,
            type=type_str,
            kind=kind,
            scope=self._current_scope,
            scope_level=self._scope_depth,
            line_declared=line,
            memory_size=size,
            offset=self._offset,
            is_initialized=is_initialized,
            references=0
        )
        self.entries.append(entry)
        self._offset += size

    def _lookup_symbol(self, name: str, scope: str) -> Optional[str]:
        """
        Hierarchical lexical scope lookup from innermost scope outward to global.
        Returns the unique key 'scope::name' if found, else None.
        """
        curr: Optional[str] = scope
        while curr is not None:
            if name in self._declared_in_scope.get(curr, []):
                return f"{curr}::{name}"
            curr = self._parent_scope.get(curr)
        return None
