from typing import List, Tuple, Optional, Dict
try:
    from ..models import ASTNode, TACInstruction, BasicBlock
except (ImportError, ValueError):
    from models import ASTNode, TACInstruction, BasicBlock

class IRGenerator:
    def __init__(self, ast: ASTNode):
        self.ast = ast
        self.instructions: List[TACInstruction] = []
        self._temp_count = 0
        self._label_count = 0
        self._curr_block = "B0"
        self._blocks: Dict[str, BasicBlock] = {}

    def _new_temp(self) -> str:
        t = f"t{self._temp_count}"
        self._temp_count += 1
        return t

    def _new_label(self) -> str:
        l = f"L{self._label_count}"
        self._label_count += 1
        return l

    def _emit(self, op: str, arg1: Optional[str] = None, arg2: Optional[str] = None, result: Optional[str] = None,
              repr_str: str = "", line: Optional[int] = None, explanation: str = "") -> str:
        idx = len(self.instructions)
        ins = TACInstruction(
            id=idx,
            op=op,
            arg1=arg1,
            arg2=arg2,
            result=result,
            representation=repr_str,
            basic_block=self._curr_block,
            line_reference=line,
            explanation=explanation
        )
        self.instructions.append(ins)
        return result or ""

    def generate(self) -> Tuple[List[TACInstruction], List[BasicBlock]]:
        self.instructions = []
        self._temp_count = 0
        self._label_count = 0
        self._curr_block = "B0"

        self._gen_node(self.ast)

        # Partition instructions into Basic Blocks
        basic_blocks = self._partition_basic_blocks()
        return self.instructions, basic_blocks

    def _get_lvalue_repr(self, node: ASTNode) -> str:
        if not node:
            return "var"
        if node.type == "Identifier":
            return node.attributes.get("name", node.label)
        elif node.type in ("MemberAccess", "PointerMemberAccess"):
            base = self._get_lvalue_repr(node.children[0]) if node.children else "obj"
            op = node.attributes.get("operator", ".")
            mem = node.attributes.get("member", "field")
            return f"{base}{op}{mem}"
        elif node.type == "ArraySubscript":
            arr = self._get_lvalue_repr(node.children[0]) if node.children else "arr"
            idx = self._gen_node(node.children[1]) if len(node.children) > 1 else "0"
            return f"{arr}[{idx}]"
        return node.attributes.get("name", node.label)

    def _gen_node(self, node: ASTNode) -> Optional[str]:
        if not node:
            return None

        ntype = node.type

        if ntype == "TranslationUnit":
            for child in node.children:
                self._gen_node(child)
            return None

        elif ntype == "FunctionDeclaration":
            name = node.attributes.get("name", "func")
            self._emit("LABEL", result=f"{name}:", repr_str=f"--- FUNCTION {name} ---", line=node.line,
                       explanation=f"Function prologue: Entry point for procedure '{name}'")
            for child in node.children:
                self._gen_node(child)
            # Implicit return 0 if main
            if name == "main":
                self._emit("RETURN", arg1="0", repr_str="return 0", line=node.line,
                           explanation="Default function epilogue for main returning code 0")
            return None

        elif ntype in ("TypedefDeclaration", "StructDeclaration", "PreprocessorDirective"):
            return None

        elif ntype == "VariableDeclaration":
            name = node.attributes.get("name", "var")
            if node.children:
                # Initializer expression
                init_val = self._gen_node(node.children[0])
                if init_val:
                    self._emit("ASSIGN", arg1=init_val, result=name, repr_str=f"{name} = {init_val}",
                               line=node.line, explanation=f"Assign initial expression value to variable '{name}'")
            return name

        elif ntype == "CompoundStatement":
            for child in node.children:
                self._gen_node(child)
            return None

        elif ntype == "AssignmentExpression":
            op = node.attributes.get("operator", "=")
            left_node = node.children[0]
            right_node = node.children[1]
            var_name = self._get_lvalue_repr(left_node)
            r_val = self._gen_node(right_node)

            if op == "=":
                self._emit("ASSIGN", arg1=r_val, result=var_name, repr_str=f"{var_name} = {r_val}",
                           line=node.line, explanation=f"Store result of right-hand expression into l-value '{var_name}'")
            else:
                # Compound like +=, -=
                pure_op = op.replace("=", "")
                t = self._new_temp()
                self._emit(pure_op, arg1=var_name, arg2=r_val, result=t, repr_str=f"{t} = {var_name} {pure_op} {r_val}",
                           line=node.line, explanation=f"Compute compound arithmetic {var_name} {pure_op} {r_val}")
                self._emit("ASSIGN", arg1=t, result=var_name, repr_str=f"{var_name} = {t}",
                           line=node.line, explanation=f"Write back compound result to '{var_name}'")
            return var_name

        elif ntype in ("MemberAccess", "PointerMemberAccess"):
            op = node.attributes.get("operator", ".")
            member = node.attributes.get("member", "field")
            base_val = self._gen_node(node.children[0]) if node.children else "obj"
            temp = self._new_temp()
            self._emit(op, arg1=base_val, arg2=member, result=temp,
                       repr_str=f"{temp} = {base_val}{op}{member}",
                       line=node.line, explanation=f"Access struct member '{member}' via {op}")
            return temp

        elif ntype == "ArraySubscript":
            arr_val = self._gen_node(node.children[0]) if node.children else "arr"
            idx_val = self._gen_node(node.children[1]) if len(node.children) > 1 else "0"
            temp = self._new_temp()
            self._emit("INDEX", arg1=arr_val, arg2=idx_val, result=temp,
                       repr_str=f"{temp} = {arr_val}[{idx_val}]",
                       line=node.line, explanation="Array element indexing")
            return temp

        elif ntype in ("InitializerList", "DesignatedInitializer"):
            return "{...}"

        elif ntype == "BinaryExpression":
            op = node.attributes.get("operator", "+")
            left_val = self._gen_node(node.children[0])
            right_val = self._gen_node(node.children[1])
            temp = self._new_temp()
            self._emit(op, arg1=left_val, arg2=right_val, result=temp,
                       repr_str=f"{temp} = {left_val} {op} {right_val}",
                       line=node.line,
                       explanation=f"Evaluate binary operation '{op}' into temporary register {temp}")
            return temp

        elif ntype == "UnaryExpression":
            op = node.attributes.get("operator", "-")
            operand_val = self._gen_node(node.children[0])
            temp = self._new_temp()
            self._emit(op, arg1=operand_val, result=temp,
                       repr_str=f"{temp} = {op}{operand_val}",
                       line=node.line,
                       explanation=f"Compute unary operation '{op}'")
            return temp

        elif ntype == "PostfixExpression":
            op = node.attributes.get("operator", "++")
            operand_node = node.children[0]
            var_name = operand_node.attributes.get("name", operand_node.label)
            delta = "1"
            sub_op = "+" if op == "++" else "-"
            temp = self._new_temp()
            self._emit("ASSIGN", arg1=var_name, result=temp, repr_str=f"{temp} = {var_name}",
                       line=node.line, explanation=f"Capture pre-modification value of '{var_name}'")
            t_inc = self._new_temp()
            self._emit(sub_op, arg1=var_name, arg2=delta, result=t_inc, repr_str=f"{t_inc} = {var_name} {sub_op} {delta}",
                       line=node.line, explanation=f"Increment/decrement {var_name}")
            self._emit("ASSIGN", arg1=t_inc, result=var_name, repr_str=f"{var_name} = {t_inc}",
                       line=node.line, explanation=f"Store updated value into '{var_name}'")
            return temp

        elif ntype == "FunctionCall":
            fn_name = node.attributes.get("function_name", "func")
            arg_vals = []
            for arg_child in node.children[1:]:
                arg_vals.append(self._gen_node(arg_child))

            for a in arg_vals:
                self._emit("PARAM", arg1=a, repr_str=f"param {a}", line=node.line,
                           explanation=f"Push parameter {a} onto call stack frame")

            ret_temp = self._new_temp()
            self._emit("CALL", arg1=fn_name, arg2=str(len(arg_vals)), result=ret_temp,
                       repr_str=f"{ret_temp} = call {fn_name}, {len(arg_vals)}",
                       line=node.line,
                       explanation=f"Transfer execution to '{fn_name}' with {len(arg_vals)} arguments and capture return")
            return ret_temp

        elif ntype == "Literal":
            return node.attributes.get("value", node.label)

        elif ntype == "Identifier":
            return node.attributes.get("name", node.label)

        elif ntype == "ReturnStatement":
            ret_val = None
            if node.children:
                ret_val = self._gen_node(node.children[0])
            self._emit("RETURN", arg1=ret_val, repr_str=f"return {ret_val or ''}".strip(),
                       line=node.line, explanation="Return control and value to calling procedure frame")
            return None

        elif ntype == "IfStatement":
            cond_node = node.children[0]
            then_node = node.children[1]
            has_else = len(node.children) > 2
            else_node = node.children[2] if has_else else None

            cond_val = self._gen_node(cond_node)
            lbl_else = self._new_label()
            lbl_end = self._new_label()

            target_false = lbl_else if has_else else lbl_end
            self._emit("IF_FALSE", arg1=cond_val, result=target_false,
                       repr_str=f"if_false {cond_val} goto {target_false}",
                       line=node.line, explanation=f"Conditional branch: Jump to {target_false} if condition evaluates to false (0)")

            self._gen_node(then_node)

            if has_else:
                self._emit("GOTO", result=lbl_end, repr_str=f"goto {lbl_end}",
                           line=node.line, explanation=f"Unconditional jump skipping else branch to {lbl_end}")
                self._emit("LABEL", result=f"{lbl_else}:", repr_str=f"{lbl_else}:",
                           line=node.line, explanation="Target label for else block execution")
                self._gen_node(else_node)

            self._emit("LABEL", result=f"{lbl_end}:", repr_str=f"{lbl_end}:",
                       line=node.line, explanation="Target label joining control flow after if/else")
            return None

        elif ntype == "WhileStatement":
            cond_node = node.children[0]
            body_node = node.children[1]

            lbl_start = self._new_label()
            lbl_end = self._new_label()

            self._emit("LABEL", result=f"{lbl_start}:", repr_str=f"{lbl_start}:",
                       line=node.line, explanation=f"Loop header label {lbl_start} for repetition entry")

            cond_val = self._gen_node(cond_node)
            self._emit("IF_FALSE", arg1=cond_val, result=lbl_end,
                       repr_str=f"if_false {cond_val} goto {lbl_end}",
                       line=node.line, explanation=f"Loop guard: Exit loop to {lbl_end} when condition is false")

            self._gen_node(body_node)

            self._emit("GOTO", result=lbl_start, repr_str=f"goto {lbl_start}",
                       line=node.line, explanation=f"Loop back-edge: Jump back to {lbl_start} for next iteration")
            self._emit("LABEL", result=f"{lbl_end}:", repr_str=f"{lbl_end}:",
                       line=node.line, explanation=f"Exit label {lbl_end} reached once loop terminates")
            return None

        elif ntype == "ForStatement":
            # [init, cond, step, body]
            idx = 0
            if len(node.children) >= 1:
                self._gen_node(node.children[0]) # init
            
            lbl_cond = self._new_label()
            lbl_end = self._new_label()

            self._emit("LABEL", result=f"{lbl_cond}:", repr_str=f"{lbl_cond}:",
                       line=node.line, explanation="For loop condition evaluation header")

            if len(node.children) >= 2:
                cond_val = self._gen_node(node.children[1])
                self._emit("IF_FALSE", arg1=cond_val, result=lbl_end,
                           repr_str=f"if_false {cond_val} goto {lbl_end}",
                           line=node.line, explanation="For loop guard condition check")

            # body
            if len(node.children) >= 4:
                self._gen_node(node.children[3])
            elif len(node.children) == 3:
                self._gen_node(node.children[2])

            # step
            if len(node.children) >= 3:
                self._gen_node(node.children[2] if len(node.children) >= 4 else node.children[1])

            self._emit("GOTO", result=lbl_cond, repr_str=f"goto {lbl_cond}",
                       line=node.line, explanation="Cycle back to for loop condition test")
            self._emit("LABEL", result=f"{lbl_end}:", repr_str=f"{lbl_end}:",
                       line=node.line, explanation="Exit label terminating for loop")
            return None

        return None

    def _partition_basic_blocks(self) -> List[BasicBlock]:
        if not self.instructions:
            return []

        # Find leaders
        leaders = set()
        leaders.add(0)

        for i, ins in enumerate(self.instructions):
            if ins.op in ("IF_FALSE", "GOTO", "RETURN"):
                if i + 1 < len(self.instructions):
                    leaders.add(i + 1)
            elif ins.op == "LABEL":
                leaders.add(i)

        leader_list = sorted(list(leaders))
        blocks: List[BasicBlock] = []

        for b_idx, start_idx in enumerate(leader_list):
            end_idx = leader_list[b_idx + 1] if (b_idx + 1 < len(leader_list)) else len(self.instructions)
            b_id = f"B{b_idx}"
            inst_ids = list(range(start_idx, end_idx))
            
            # Label
            first_ins = self.instructions[start_idx]
            b_label = first_ins.result if first_ins.op == "LABEL" else f"Block {b_id}"

            block = BasicBlock(
                id=b_id,
                label=b_label or f"Block {b_id}",
                instruction_ids=inst_ids,
                predecessors=[],
                successors=[]
            )
            # Tag instructions with block ID
            for ins_id in inst_ids:
                self.instructions[ins_id].basic_block = b_id

            blocks.append(block)

        # Build CFG edges (predecessors and successors)
        for i, b in enumerate(blocks):
            if not b.instruction_ids:
                continue
            last_id = b.instruction_ids[-1]
            last_ins = self.instructions[last_id]

            if last_ins.op == "GOTO":
                target_label = last_ins.result
                target_b = self._find_block_by_label(blocks, target_label)
                if target_b and target_b.id not in b.successors:
                    b.successors.append(target_b.id)
                    target_b.predecessors.append(b.id)
            elif last_ins.op == "IF_FALSE":
                target_label = last_ins.result
                target_b = self._find_block_by_label(blocks, target_label)
                if target_b and target_b.id not in b.successors:
                    b.successors.append(target_b.id)
                    target_b.predecessors.append(b.id)
                # Also fallthrough to next block
                if i + 1 < len(blocks):
                    next_b = blocks[i + 1]
                    if next_b.id not in b.successors:
                        b.successors.append(next_b.id)
                        next_b.predecessors.append(b.id)
            elif last_ins.op == "RETURN":
                # End of procedure, no successor
                pass
            else:
                # Normal fallthrough to next block
                if i + 1 < len(blocks):
                    next_b = blocks[i + 1]
                    if next_b.id not in b.successors:
                        b.successors.append(next_b.id)
                        next_b.predecessors.append(b.id)

        return blocks

    def _find_block_by_label(self, blocks: List[BasicBlock], label: Optional[str]) -> Optional[BasicBlock]:
        if not label:
            return None
        clean_lbl = label.rstrip(":")
        for b in blocks:
            for i_id in b.instruction_ids:
                ins = self.instructions[i_id]
                if ins.op == "LABEL" and (ins.result or "").rstrip(":") == clean_lbl:
                    return b
        return None
