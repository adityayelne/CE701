import sys
import unittest
sys.path.insert(0, 'f:/cc')

from backend.compiler.lexer import LexicalAnalyzer
from backend.compiler.parser import CParser
from backend.compiler.symbol_table import SymbolTableAnalyzer
from backend.compiler.ir_generator import IRGenerator
from backend.models import SourceCodeRequest
from backend.main import analyze_code

class TestC11GrammarRegression(unittest.TestCase):

    def _parse(self, code: str):
        lexer = LexicalAnalyzer(code)
        tokens, lex_errs = lexer.tokenize()
        parser = CParser(tokens, code)
        ast, parse_errs = parser.parse()
        return tokens, lex_errs, ast, parse_errs

    # 1. typedef struct { ... } Alias;
    def test_typedef_anonymous_struct(self):
        code = """
        typedef struct {
            int id;
            double score;
        } Student;

        int main() {
            Student s;
            return 0;
        }
        """
        _, l_err, ast, p_err = self._parse(code)
        self.assertEqual(len(l_err), 0)
        self.assertEqual(len(p_err), 0)
        td_nodes = [c for c in ast.children if c.type == "TypedefDeclaration"]
        self.assertEqual(len(td_nodes), 1)
        self.assertEqual(td_nodes[0].attributes.get("alias"), "Student")

    # 2. Named structures and structure members
    def test_named_struct_and_members(self):
        code = """
        struct Point {
            int x;
            int y;
        };

        int main() {
            struct Point p;
            p.x = 10;
            return p.x;
        }
        """
        _, l_err, ast, p_err = self._parse(code)
        self.assertEqual(len(l_err), 0)
        self.assertEqual(len(p_err), 0)
        struct_nodes = [c for c in ast.children if c.type == "StructDeclaration"]
        self.assertEqual(len(struct_nodes), 1)
        self.assertEqual(struct_nodes[0].attributes.get("name"), "Point")
        self.assertEqual(struct_nodes[0].attributes.get("member_count"), 2)

    # 3. Standard type names and _Atomic declarations
    def test_standard_types_and_atomic(self):
        code = """
        typedef struct {
            _Alignas(64) _Atomic uint64_t counter;
            size_t capacity;
            bool is_active;
        } Context;

        int main() {
            Context ctx;
            return 0;
        }
        """
        _, l_err, ast, p_err = self._parse(code)
        self.assertEqual(len(l_err), 0)
        self.assertEqual(len(p_err), 0)
        td = [c for c in ast.children if c.type == "TypedefDeclaration"][0]
        struct_def = td.children[0]
        members = struct_def.children
        self.assertEqual(len(members), 3)
        self.assertTrue(members[0].attributes.get("is_atomic"))
        self.assertEqual(members[0].attributes.get("alignas"), "64")

    # 4. Designated initializers (.id = 42, .data = 100)
    def test_designated_initializers(self):
        code = """
        typedef struct {
            int id;
            int value;
        } Item;

        int main() {
            Item item = { .id = 42, .value = 100 };
            return item.id;
        }
        """
        _, l_err, ast, p_err = self._parse(code)
        self.assertEqual(len(l_err), 0)
        self.assertEqual(len(p_err), 0)

    # 5. Preprocessor directives (#include and #define)
    def test_preprocessor_directives(self):
        code = """
        #include <stdio.h>
        #include <stdint.h>
        #define BUFFER_CAPACITY 128

        int main() {
            int cap = BUFFER_CAPACITY;
            return cap;
        }
        """
        _, l_err, ast, p_err = self._parse(code)
        self.assertEqual(len(l_err), 0)
        self.assertEqual(len(p_err), 0)
        prep_nodes = [c for c in ast.children if c.type == "PreprocessorDirective"]
        self.assertEqual(len(prep_nodes), 3)

    # 6. Valid function calls and nested expressions
    def test_function_calls_and_nested_expressions(self):
        code = """
        int compute(int a, int b) {
            return (a + 1) * (b - 2);
        }

        int main() {
            int res = compute(10, 20);
            return res;
        }
        """
        _, l_err, ast, p_err = self._parse(code)
        self.assertEqual(len(l_err), 0)
        self.assertEqual(len(p_err), 0)

    # 7. The malformed printf argument list (identifies the genuine error at the misplaced semicolon)
    def test_malformed_printf_semicolon(self):
        code = """
        int main() {
            int id = 42;
            printf("ID is %d\\n",; id);
            return 0;
        }
        """
        _, l_err, ast, p_err = self._parse(code)
        self.assertEqual(len(l_err), 0)
        # Exactly 1 error for the misplaced semicolon, not dozens of cascading errors
        self.assertEqual(len(p_err), 1)
        self.assertIn("Unexpected ';'", p_err[0].message)
        self.assertEqual(p_err[0].line, 4)

    # 8. Correct source locations and bounded error recovery
    def test_bounded_error_recovery(self):
        code = """
        int main() {
            int a = 1;
            int b = ;
            int c = 3;
            return a + c;
        }
        """
        _, _, _, p_err = self._parse(code)
        # Should record error for the empty expression at line 4, but line 5 (int c = 3) and return must parse cleanly
        self.assertTrue(len(p_err) >= 1)
        error_lines = [e.line for e in p_err]
        self.assertIn(4, error_lines)
        # It must not cascade into declaring line 5 as an unexpected top-level token
        for e in p_err:
            self.assertNotIn("Unexpected top-level token", e.message)

    # 9. Preservation of the canonical AST pipeline across all passes
    def test_canonical_pipeline_lock_free_ring_buffer(self):
        code = """#include <stdio.h>
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
}
"""
        req = SourceCodeRequest(source_code=code)
        res = analyze_code(req)
        # 0 lexical, 0 syntax, 0 semantic errors on clean code
        self.assertEqual(len(res.errors), 0, f"Unexpected errors: {[e.message for e in res.errors]}")
        # Tokens generated
        self.assertTrue(len(res.tokens) > 100)
        # Symbols recorded
        sym_names = [s.name for s in res.symbol_table]
        self.assertIn("BufferItem", sym_names)
        self.assertIn("LockFreeRingBuffer", sym_names)
        self.assertIn("ring_buffer_init", sym_names)
        self.assertIn("ring_buffer_push", sym_names)
        # TAC generated with basic blocks
        self.assertTrue(len(res.intermediate_code) > 20)
        self.assertTrue(len(res.basic_blocks) >= 4)

    # 10. Honest unsupported-feature reporting
    def test_honest_unsupported_feature_reporting(self):
        # Malformed C with unsupported tokens
        code = """
        int main() {
            int x = @invalid;
            return x;
        }
        """
        tokens, lex_errs, _, _ = self._parse(code)
        self.assertTrue(len(lex_errs) > 0)
        self.assertIn("Illegal or unrecognized character '@'", lex_errs[0].message)

if __name__ == '__main__':
    unittest.main()
