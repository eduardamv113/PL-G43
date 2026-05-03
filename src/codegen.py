# codegen.py - Geração de Código para a VM
# Projeto PL2026 - Grupo G43
#
# A VM usa uma pilha com:
#   gp  — base das variáveis globais (programa principal)
#   fp  — base das variáveis locais (dentro de funções/subrotinas)
#   sp  — topo da pilha
#
# Convenções adotadas:
#   - Variáveis do programa principal → PUSHG/STOREG (índice no gp)
#   - Variáveis locais de funções     → PUSHL/STOREL (índice no fp)
#   - Arrays → alocados no heap com ALLOC, endereço guardado como variável
#   - Strings literais → PUSHS
#   - Funções → label com o nome da função, terminam em RETURN
#   - Labels DO/GOTO → labels numéricos prefixados com "L"

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from semantic import SemanticAnalyzer, SymbolTable, Symbol, implicit_type


# ===========================================================================
# Gerador de Código
# ===========================================================================

class CodeGenerator:

    def __init__(self, analyzer: SemanticAnalyzer = None):
        self.analyzer     = analyzer          # analisador semântico (tabela de símbolos)
        self.code         = []                # lista de linhas de código VM
        self.label_count  = 0                 # contador de labels internos
        self.current_scope_name = None        # nome da unidade atual
        self.var_index    = {}                # nome → índice gp/fp
        self.next_index   = 0                 # próximo índice disponível
        self.is_global    = True              # True = programa principal, False = função
        self.array_sizes  = {}               # nome → tamanho total do array
        self.functions    = []                # unidades a gerar depois do main
        self.current_do_end_labels = []       # stack de labels de fim de DO

    # -----------------------------------------------------------------------
    # Helpers de emissão
    # -----------------------------------------------------------------------

    def emit(self, instr):
        self.code.append(instr)

    def emit_label(self, label):
        self.code.append(f"{label}:")

    def new_label(self, prefix='_L'):
        self.label_count += 1
        return f"{prefix}{self.label_count}"

    def fortran_label(self, n):
        """Converte um label numérico Fortran (ex: 10) para label VM (ex: L10)."""
        return f"L{n}"

    # -----------------------------------------------------------------------
    # Entrada principal
    # -----------------------------------------------------------------------

    def generate(self, ast) -> str:
        """Recebe a AST e devolve o código VM como string."""
        if ast is None or ast[0] != 'program':
            raise ValueError("AST inválida")

        units = ast[1]

        # Separar programa principal de subprogramas
        main_unit = None
        sub_units = []
        for unit in units:
            if unit[0] == 'main_program':
                main_unit = unit
            else:
                sub_units.append(unit)

        # Gerar programa principal
        self.emit('START')
        if main_unit:
            self._gen_main(main_unit)
        self.emit('STOP')

        # Gerar subprogramas depois do STOP
        for unit in sub_units:
            self._gen_subprogram(unit)

        return '\n'.join(self.code) + '\n'

    # -----------------------------------------------------------------------
    # Programa principal
    # -----------------------------------------------------------------------

    def _gen_main(self, node):
        _, name, stmts = node
        self.current_scope_name = name or 'MAIN'
        self.is_global  = True
        self.var_index  = {}
        self.next_index = 0

        # Primeira passagem: recolher declarações e alocar variáveis
        self._collect_declarations(stmts)

        # Reservar espaço na pilha para todas as variáveis globais
        if self.next_index > 0:
            self.emit(f'PUSHN {self.next_index}')

        # Gerar statements
        self._gen_stmts(stmts)

    # -----------------------------------------------------------------------
    # Subprogramas (FUNCTION / SUBROUTINE)
    # -----------------------------------------------------------------------

    def _gen_subprogram(self, node):
        kind = node[0]

        if kind == 'function':
            _, name, rtype, params, stmts = node
            self.emit_label(name)
            self.is_global  = False
            self.current_scope_name = name
            self.var_index  = {}
            self.next_index = 0

            # Parâmetros chegam na pilha: fp[0], fp[1], ...
            for i, p in enumerate(params):
                self.var_index[p] = i
            self.next_index = len(params)

            # Variável de retorno tem o mesmo nome da função
            if name not in self.var_index:
                self.var_index[name] = self.next_index
                self.next_index += 1

            # Recolher restantes declarações locais
            self._collect_declarations(stmts, offset=self.next_index)

            # Reservar espaço para variáveis locais (excluindo parâmetros)
            local_count = self.next_index - len(params)
            if local_count > 0:
                self.emit(f'PUSHN {local_count}')

            self._gen_stmts(stmts)

            # Se não houver RETURN explícito, garantir retorno
            # O valor de retorno está em fp[var_index[name]]
            ret_idx = self.var_index.get(name, 0)
            self.emit(f'PUSHL {ret_idx}')
            self.emit('RETURN')

        elif kind == 'subroutine':
            _, name, params, stmts = node
            self.emit_label(name)
            self.is_global  = False
            self.current_scope_name = name
            self.var_index  = {}
            self.next_index = 0

            for i, p in enumerate(params):
                self.var_index[p] = i
            self.next_index = len(params)

            self._collect_declarations(stmts, offset=self.next_index)

            local_count = self.next_index - len(params)
            if local_count > 0:
                self.emit(f'PUSHN {local_count}')

            self._gen_stmts(stmts)
            self.emit('RETURN')

    # -----------------------------------------------------------------------
    # Recolha de declarações (primeira passagem)
    # Atribui índices gp/fp a todas as variáveis declaradas
    # -----------------------------------------------------------------------

    def _collect_declarations(self, stmts, offset=0):
        if offset > 0:
            self.next_index = offset
        if stmts is None:
            return
        for stmt in stmts:
            self._collect_stmt_decls(stmt)

    def _collect_stmt_decls(self, stmt):
        if stmt is None:
            return
        kind = stmt[0]

        if kind == 'labeled':
            self._collect_stmt_decls(stmt[2])

        elif kind == 'declaration':
            _, dtype, decls = stmt
            if isinstance(dtype, tuple):
                base_type = dtype[0]
            else:
                base_type = dtype
            for decl in decls:
                dkind = decl[0]
                if dkind == 'var':
                    name = decl[1]
                    if name not in self.var_index:
                        self.var_index[name] = self.next_index
                        self.next_index += 1
                elif dkind == 'array':
                    name = decl[1]
                    dims = decl[2]
                    size = self._array_size(dims)
                    self.array_sizes[name] = size
                    if name not in self.var_index:
                        # Guardamos o endereço do array como uma variável escalar
                        self.var_index[name] = self.next_index
                        self.next_index += 1

        elif kind == 'if_then':
            self._collect_declarations(stmt[2])
        elif kind == 'if_then_else':
            self._collect_declarations(stmt[2])
            self._collect_declarations(stmt[3])
        elif kind == 'if_simple':
            self._collect_stmt_decls(stmt[2])

    def _array_size(self, dims):
        """Calcula o tamanho total de um array a partir das suas dimensões."""
        total = 1
        for dim in dims:
            if isinstance(dim, tuple) and dim[0] == 'range':
                lo = self._const_eval(dim[1])
                hi = self._const_eval(dim[2])
                if lo is not None and hi is not None:
                    total *= (hi - lo + 1)
                else:
                    total *= 100  # tamanho desconhecido — usar valor conservador
            else:
                v = self._const_eval(dim)
                if v is not None:
                    total *= v
                else:
                    total *= 100
        return total

    def _const_eval(self, node):
        """Avalia uma expressão constante simples."""
        if node is None:
            return None
        if isinstance(node, tuple):
            if node[0] == 'int':
                return node[1]
            if node[0] == 'uminus':
                v = self._const_eval(node[1])
                return -v if v is not None else None
        return None

    # -----------------------------------------------------------------------
    # Geração de statements
    # -----------------------------------------------------------------------

    def _gen_stmts(self, stmts):
        if stmts is None:
            return
        for stmt in stmts:
            self._gen_stmt(stmt)

    def _gen_stmt(self, node):
        if node is None:
            return
        kind = node[0]

        if kind == 'labeled':
            _, label, inner = node
            self.emit_label(self.fortran_label(label))
            self._gen_stmt(inner)

        elif kind == 'declaration':
            self._gen_declaration(node)

        elif kind == 'assign':
            self._gen_assign(node)

        elif kind == 'if_simple':
            self._gen_if_simple(node)

        elif kind == 'if_then':
            self._gen_if_then(node)

        elif kind == 'if_then_else':
            self._gen_if_then_else(node)

        elif kind == 'do':
            self._gen_do(node)

        elif kind == 'goto':
            _, label = node
            self.emit(f'JUMP {self.fortran_label(label)}')

        elif kind == 'continue':
            self.emit('NOP')

        elif kind == 'print':
            self._gen_print(node)

        elif kind == 'write':
            self._gen_write(node)

        elif kind == 'read':
            self._gen_read(node)

        elif kind == 'call':
            self._gen_call_stmt(node)

        elif kind == 'return':
            self._gen_return()

        elif kind == 'stop':
            self.emit('STOP')

        elif kind in ('format', 'common', 'parameter', 'dimension'):
            pass  # ignorados na geração de código

        else:
            self.emit(f'NOP  ; statement não gerado: {kind}')

    # -----------------------------------------------------------------------
    # Declaração — alocar arrays no heap
    # -----------------------------------------------------------------------

    def _gen_declaration(self, node):
        _, dtype, decls = node
        for decl in decls:
            if decl[0] == 'array':
                name = decl[1]
                size = self.array_sizes.get(name, 1)
                self.emit(f'ALLOC {size}')
                self._store_var(name)

    # -----------------------------------------------------------------------
    # Atribuição
    # -----------------------------------------------------------------------

    def _gen_assign(self, node):
        _, lval, rval = node
        lkind = lval[0]

        if lkind == 'var':
            name = lval[1]
            # Atribuição à variável de retorno de função?
            self._gen_expr(rval)
            self._store_var(name)

        elif lkind == 'array_elem':
            name, indices = lval[1], lval[2]
            # Empilhar endereço base do array
            self._push_var(name)
            # Calcular offset (por agora só suporta 1 dimensão)
            if len(indices) == 1:
                self._gen_expr(indices[0])
                self.emit('PUSHI 1')
                self.emit('SUB')        # Fortran arrays são 1-based
            else:
                # Multi-dimensional: simplificado
                self._gen_expr(indices[0])
                self.emit('PUSHI 1')
                self.emit('SUB')
            self.emit('PADD')
            # Valor a armazenar
            self._gen_expr(rval)
            self.emit('STOREN')

    # -----------------------------------------------------------------------
    # IF simples (sem THEN)
    # -----------------------------------------------------------------------

    def _gen_if_simple(self, node):
        _, cond, body = node
        end_label = self.new_label('_IF_END')
        self._gen_expr(cond)
        self.emit('NOT')
        self.emit(f'JZ {end_label}')
        self._gen_stmt(body)
        self.emit_label(end_label)

    # -----------------------------------------------------------------------
    # IF-THEN
    # -----------------------------------------------------------------------

    def _gen_if_then(self, node):
        _, cond, then_stmts = node
        end_label = self.new_label('_IF_END')
        self._gen_expr(cond)
        self.emit('NOT')
        self.emit(f'JZ {end_label}')
        self._gen_stmts(then_stmts)
        self.emit_label(end_label)

    # -----------------------------------------------------------------------
    # IF-THEN-ELSE
    # -----------------------------------------------------------------------

    def _gen_if_then_else(self, node):
        _, cond, then_stmts, else_stmts = node
        else_label = self.new_label('_ELSE')
        end_label  = self.new_label('_IF_END')
        self._gen_expr(cond)
        self.emit('NOT')
        self.emit(f'JZ {else_label}')
        self._gen_stmts(then_stmts)
        self.emit(f'JUMP {end_label}')
        self.emit_label(else_label)
        self._gen_stmts(else_stmts)
        self.emit_label(end_label)

    # -----------------------------------------------------------------------
    # DO loop
    # -----------------------------------------------------------------------

    def _gen_do(self, node):
        _, label, var, start, end_expr, step = node
        loop_label = self.fortran_label(label)
        test_label = self.new_label('_DO_TEST')
        end_label  = self.new_label('_DO_END')

        # Inicializar variável de controlo
        self._gen_expr(start)
        self._store_var(var)

        # Guardar valor final na pilha (fica lá durante o loop)
        self._gen_expr(end_expr)

        self.emit_label(test_label)

        # Testar: var <= end (valor final está no topo - 1, var no topo)
        self._push_var(var)
        # Stack: [end_val, var_val] — comparar var <= end
        # Duplicar end_val para comparação
        self.emit('DUP 1')       # duplica o end_val que está abaixo
        self._push_var(var)
        self.emit('SUPEQ')       # var >= end_val → end_val no topo depois de SUP
        self.emit('NOT')
        self.emit(f'JZ {end_label}')

        # Emitir label Fortran (para GOTO e CONTINUE)
        self.emit_label(loop_label)

        # O corpo do DO é gerado pelo _gen_stmts dos statements seguintes
        # (até ao CONTINUE com o mesmo label) — guardamos o end_label
        self.current_do_end_labels.append((label, end_label, test_label, var, step))

    def _finish_do(self, label):
        """Chamado quando encontramos o CONTINUE do DO — incrementa e fecha o loop."""
        if not self.current_do_end_labels:
            return
        do_label, end_label, test_label, var, step = self.current_do_end_labels[-1]
        if do_label != label:
            return
        self.current_do_end_labels.pop()

        # Incrementar variável de controlo
        self._push_var(var)
        if step is not None:
            self._gen_expr(step)
        else:
            self.emit('PUSHI 1')
        self.emit('ADD')
        self._store_var(var)

        self.emit(f'JUMP {test_label}')
        self.emit_label(end_label)
        # Retirar o end_val da pilha
        self.emit('POP 1')

    # -----------------------------------------------------------------------
    # PRINT
    # -----------------------------------------------------------------------

    def _gen_print(self, node):
        _, fmt, items = node
        for item in items:
            self._gen_print_item(item)
        self.emit('WRITELN')

    def _gen_print_item(self, item):
        if item is None:
            return
        kind = item[0]
        itype = self._typeof_expr(item)

        self._gen_expr(item)

        if itype == 'REAL':
            self.emit('WRITEF')
        elif itype == 'CHARACTER':
            self.emit('WRITES')
        elif itype == 'LOGICAL':
            # Imprimir .TRUE. ou .FALSE.
            true_label = self.new_label('_TRUE')
            end_label  = self.new_label('_BOOL_END')
            self.emit(f'JZ {true_label}')
            self.emit('PUSHS ".FALSE."')
            self.emit('WRITES')
            self.emit(f'JUMP {end_label}')
            self.emit_label(true_label)
            self.emit('PUSHS ".TRUE."')
            self.emit('WRITES')
            self.emit_label(end_label)
        else:
            self.emit('WRITEI')

    # -----------------------------------------------------------------------
    # WRITE (igual ao PRINT por agora)
    # -----------------------------------------------------------------------

    def _gen_write(self, node):
        _, ctrl, items = node
        for item in items:
            self._gen_print_item(item)
        self.emit('WRITELN')

    # -----------------------------------------------------------------------
    # READ
    # -----------------------------------------------------------------------

    def _gen_read(self, node):
        _, fmt, targets = node
        for target in targets:
            self.emit('READ')
            tkind = target[0] if isinstance(target, tuple) else None
            itype = self._typeof_expr(target)

            if itype == 'REAL':
                self.emit('ATOF')
            elif itype == 'CHARACTER':
                pass  # já é string
            else:
                self.emit('ATOI')

            if tkind == 'var':
                self._store_var(target[1])
            elif tkind == 'array_elem':
                name, indices = target[1], target[2]
                # Guardar o valor lido temporariamente
                temp = self.new_label('_READ_TMP')
                # Empilhar endereço
                self._push_var(name)
                self._gen_expr(indices[0])
                self.emit('PUSHI 1')
                self.emit('SUB')
                self.emit('PADD')
                # Stack: [addr, val] — precisamos [addr, val] → STOREN
                self.emit('SWAP')
                self.emit('STOREN')

    # -----------------------------------------------------------------------
    # CALL (subrotina)
    # -----------------------------------------------------------------------

    def _gen_call_stmt(self, node):
        _, name, args = node
        for arg in args:
            self._gen_expr(arg)
        self.emit(f'PUSHA {name}')
        self.emit('CALL')
        # Subrotinas não deixam valor na pilha — descartar args
        # (na nossa convenção os args ficam como variáveis locais)

    # -----------------------------------------------------------------------
    # RETURN
    # -----------------------------------------------------------------------

    def _gen_return(self):
        if not self.is_global:
            # Empilhar valor de retorno (variável com nome da função)
            ret_var = self.current_scope_name
            if ret_var in self.var_index:
                self._push_var(ret_var)
        self.emit('RETURN')

    # -----------------------------------------------------------------------
    # Geração de expressões
    # -----------------------------------------------------------------------

    def _gen_expr(self, node):
        if node is None:
            return
        if not isinstance(node, tuple):
            return
        kind = node[0]

        if kind == 'int':
            self.emit(f'PUSHI {node[1]}')

        elif kind == 'real':
            self.emit(f'PUSHF {node[1]}')

        elif kind == 'string':
            # Escapar aspas duplas internas
            s = node[1].replace('"', '\\"')
            self.emit(f'PUSHS "{s}"')

        elif kind == 'bool':
            self.emit(f'PUSHI {1 if node[1] else 0}')

        elif kind == 'var':
            self._push_var(node[1])

        elif kind == 'array_elem':
            name, indices = node[1], node[2]
            self._push_var(name)
            if len(indices) >= 1:
                self._gen_expr(indices[0])
                self.emit('PUSHI 1')
                self.emit('SUB')   # Fortran é 1-based
            self.emit('LOADN')

        elif kind == 'uminus':
            self._gen_expr(node[1])
            self.emit('PUSHI -1')
            self.emit('MUL')

        elif kind == 'binop':
            _, op, left, right = node
            lt = self._typeof_expr(left)
            rt = self._typeof_expr(right)
            use_float = (lt == 'REAL' or rt == 'REAL')

            self._gen_expr(left)
            if use_float and lt != 'REAL':
                self.emit('ITOF')
            self._gen_expr(right)
            if use_float and rt != 'REAL':
                self.emit('ITOF')

            ops_int   = {'+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV'}
            ops_float = {'+': 'FADD', '-': 'FSUB', '*': 'FMUL', '/': 'FDIV'}
            if op == '**':
                # Potência: implementar como loop ou chamar intrínseco
                # Simplificação: só potências inteiras positivas
                self._gen_power(use_float)
            elif use_float:
                self.emit(ops_float.get(op, f'NOP  ; op {op}'))
            else:
                self.emit(ops_int.get(op, f'NOP  ; op {op}'))

        elif kind == 'relop':
            _, op, left, right = node
            lt = self._typeof_expr(left)
            rt = self._typeof_expr(right)
            use_float = (lt == 'REAL' or rt == 'REAL')

            self._gen_expr(left)
            if use_float and lt != 'REAL':
                self.emit('ITOF')
            self._gen_expr(right)
            if use_float and rt != 'REAL':
                self.emit('ITOF')

            rel_map = {
                '.EQ.': 'EQUAL', '==':  'EQUAL',
                '.NE.': ('EQUAL', 'NOT'),
                '/=':   ('EQUAL', 'NOT'),
                '.LT.': 'INF',   '<':   'INF',
                '.LE.': 'INFEQ', '<=':  'INFEQ',
                '.GT.': 'SUP',   '>':   'SUP',
                '.GE.': 'SUPEQ', '>=':  'SUPEQ',
            }
            if use_float:
                rel_map = {
                    '.EQ.': 'EQUAL', '==':  'EQUAL',
                    '.NE.': ('EQUAL', 'NOT'), '/=': ('EQUAL', 'NOT'),
                    '.LT.': 'FINF',  '<':   'FINF',
                    '.LE.': 'FINFEQ','<=':  'FINFEQ',
                    '.GT.': 'FSUP',  '>':   'FSUP',
                    '.GE.': 'FSUPEQ','>=':  'FSUPEQ',
                }
            instr = rel_map.get(op)
            if isinstance(instr, tuple):
                for i in instr:
                    self.emit(i)
            elif instr:
                self.emit(instr)

        elif kind == 'logop':
            _, op, left, right = node
            self._gen_expr(left)
            self._gen_expr(right)
            if op == '.AND.':
                self.emit('AND')
            elif op == '.OR.':
                self.emit('OR')

        elif kind == 'not':
            self._gen_expr(node[1])
            self.emit('NOT')

        elif kind == 'concat':
            self._gen_expr(node[1])
            self._gen_expr(node[2])
            self.emit('CONCAT')

        elif kind == 'call_or_array':
            self._gen_call_or_array(node)

    def _gen_power(self, use_float):
        """Gera código para ** usando um loop simples (expoente inteiro)."""
        # Stack: [base, exp]
        # Implementação: resultado = 1; while exp > 0: resultado *= base; exp -= 1
        result_tmp = self.new_label('_POW_RES')
        exp_tmp    = self.new_label('_POW_EXP')
        loop_label = self.new_label('_POW_LOOP')
        end_label  = self.new_label('_POW_END')

        # exp está no topo, base abaixo
        # Guardar exp e base em variáveis temporárias da pilha
        # Stack antes: [base, exp]
        self.emit('PUSHI 1')   # resultado = 1  → stack: [base, exp, 1]
        # Loop
        self.emit_label(loop_label)
        # Verificar se exp > 0: stack [base, exp, res]
        self.emit('DUP 1')     # duplicar exp   → [base, exp, res, exp]
        self.emit('PUSHI 0')
        self.emit('SUP')       # exp > 0?
        self.emit(f'JZ {end_label}')
        # res = res * base: stack [base, exp, res]
        self.emit('COPY 1')    # copiar res     → [base, exp, res, res]
        self.emit('DUP 3')     # copiar base    → [base, exp, res, res, base]
        if use_float:
            self.emit('FMUL')
        else:
            self.emit('MUL')
        # Stack agora: [base, exp, res, new_res]
        self.emit('SWAP')      # [base, exp, new_res, res]
        self.emit('POP 1')     # [base, exp, new_res]
        # exp -= 1
        self.emit('SWAP')      # [base, new_res, exp]
        self.emit('PUSHI 1')
        self.emit('SUB')       # [base, new_res, exp-1]
        self.emit('SWAP')      # [base, exp-1, new_res]
        self.emit(f'JUMP {loop_label}')
        self.emit_label(end_label)
        # Stack: [base, exp, res] — limpar base e exp
        self.emit('SWAP')      # [base, res, exp]
        self.emit('POP 1')     # [base, res]
        self.emit('SWAP')      # [res, base]
        self.emit('POP 1')     # [res]

    # -----------------------------------------------------------------------
    # Chamada de função ou acesso a array
    # -----------------------------------------------------------------------

    def _gen_call_or_array(self, node):
        _, name, args = node

        # Intrínsecos
        if name == 'MOD':
            self._gen_expr(args[0])
            self._gen_expr(args[1])
            self.emit('MOD')
            return
        if name in ('INT', 'IFIX'):
            self._gen_expr(args[0])
            self.emit('FTOI')
            return
        if name in ('REAL', 'FLOAT'):
            self._gen_expr(args[0])
            self.emit('ITOF')
            return
        if name == 'ABS':
            self._gen_expr(args[0])
            t = self._typeof_expr(args[0])
            end = self.new_label('_ABS_END')
            self.emit('DUP 1')
            self.emit('PUSHI 0')
            self.emit('INFEQ')
            self.emit(f'JZ {end}')
            self.emit('PUSHI -1')
            self.emit('MUL' if t != 'REAL' else 'FMUL')
            self.emit_label(end)
            return
        if name == 'IABS':
            self._gen_expr(args[0])
            end = self.new_label('_ABS_END')
            self.emit('DUP 1')
            self.emit('PUSHI 0')
            self.emit('INFEQ')
            self.emit(f'JZ {end}')
            self.emit('PUSHI -1')
            self.emit('MUL')
            self.emit_label(end)
            return
        if name in ('SQRT', 'SIN', 'COS'):
            self._gen_expr(args[0])
            t = self._typeof_expr(args[0])
            if t != 'REAL':
                self.emit('ITOF')
            if name == 'SQRT':
                self.emit('PUSHF 0.5')
                self.emit('FMUL')   # sqrt via x^0.5 não existe na VM
                # A VM não tem SQRT — usar aproximação ou ERR
                self.emit(f'ERR "SQRT nao suportado diretamente pela VM"')
            elif name == 'SIN':
                self.emit('FSIN')
            elif name == 'COS':
                self.emit('FCOS')
            return
        if name == 'LEN':
            self._gen_expr(args[0])
            self.emit('STRLEN')
            return
        if name == 'CHAR':
            self._gen_expr(args[0])
            self.emit('WRITECHR')   # não existe CHAR intrínseco na VM — limitação
            return
        if name == 'ICHAR':
            self._gen_expr(args[0])
            self.emit('CHRCODE')
            return
        if name in ('MAX', 'MAX0', 'AMAX1'):
            self._gen_max_min(args, is_max=True)
            return
        if name in ('MIN', 'MIN0', 'AMIN1'):
            self._gen_max_min(args, is_max=False)
            return

        # Verificar se é array
        if name in self.array_sizes:
            self._push_var(name)
            if args:
                self._gen_expr(args[0])
                self.emit('PUSHI 1')
                self.emit('SUB')
            self.emit('LOADN')
            return

        # Chamada de função definida pelo utilizador
        for arg in args:
            self._gen_expr(arg)
        self.emit(f'PUSHA {name}')
        self.emit('CALL')

    def _gen_max_min(self, args, is_max):
        """Gera código para MAX/MIN com N argumentos."""
        if not args:
            return
        self._gen_expr(args[0])
        for arg in args[1:]:
            self._gen_expr(arg)
            cmp_label = self.new_label('_MAXMIN_KEEP')
            end_label = self.new_label('_MAXMIN_END')
            # Stack: [current_best, new_val]
            self.emit('DUP 1')   # [best, new, best]
            self.emit('DUP 1')   # [best, new, best, new]  — errado, usar COPY
            # Recalcular: comparar new vs best
            # Stack: [best, new]
            self.emit('DUP 2')   # copiar ambos
            if is_max:
                self.emit('SUP')  # new > best?
            else:
                self.emit('INF')  # new < best?
            self.emit(f'JZ {cmp_label}')
            # new é melhor: descartar best, manter new
            self.emit('SWAP')
            self.emit('POP 1')
            self.emit(f'JUMP {end_label}')
            self.emit_label(cmp_label)
            # best é melhor: descartar new
            self.emit('POP 1')
            self.emit_label(end_label)

    # -----------------------------------------------------------------------
    # Push/Store de variáveis (global vs local)
    # -----------------------------------------------------------------------

    def _push_var(self, name):
        if name not in self.var_index:
            # Tipo implícito — criar entrada
            self.var_index[name] = self.next_index
            self.next_index += 1
        idx = self.var_index[name]
        if self.is_global:
            self.emit(f'PUSHG {idx}')
        else:
            self.emit(f'PUSHL {idx}')

    def _store_var(self, name):
        if name not in self.var_index:
            self.var_index[name] = self.next_index
            self.next_index += 1
        idx = self.var_index[name]
        if self.is_global:
            self.emit(f'STOREG {idx}')
        else:
            self.emit(f'STOREL {idx}')

    # -----------------------------------------------------------------------
    # Tipo de uma expressão (consulta o analisador semântico ou infere)
    # -----------------------------------------------------------------------

    def _typeof_expr(self, node):
        if node is None:
            return 'INTEGER'
        if not isinstance(node, tuple):
            return 'INTEGER'
        kind = node[0]
        if kind == 'int':
            return 'INTEGER'
        if kind == 'real':
            return 'REAL'
        if kind == 'string':
            return 'CHARACTER'
        if kind == 'bool':
            return 'LOGICAL'
        if kind == 'var':
            name = node[1]
            if self.analyzer:
                sym = self.analyzer.current_scope.lookup(name)
                if sym:
                    return sym.dtype
            return implicit_type(name)
        if kind in ('binop', 'uminus'):
            lt = self._typeof_expr(node[2] if kind == 'binop' else node[1])
            rt = self._typeof_expr(node[3]) if kind == 'binop' else lt
            if lt == 'REAL' or rt == 'REAL':
                return 'REAL'
            return 'INTEGER'
        if kind in ('relop', 'logop', 'not'):
            return 'LOGICAL'
        if kind == 'concat':
            return 'CHARACTER'
        if kind == 'call_or_array':
            name = node[1]
            if name in self.array_sizes:
                # tipo do array — procurar no analisador
                if self.analyzer:
                    sym = self.analyzer.current_scope.lookup(name)
                    if sym:
                        return sym.dtype
            return implicit_type(name)
        return 'INTEGER'


# ===========================================================================
# Execução direta: python codegen.py <ficheiro.f77>
# ===========================================================================

if __name__ == '__main__':
    import pprint
    from parser import parse
    from semantic import analyze_full

    if len(sys.argv) < 2:
        print("Uso: python codegen.py <ficheiro.f77>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        source = f.read()

    ast = parse(source)
    if ast is None:
        print("[CODEGEN] Parser falhou.")
        sys.exit(1)

    analyzer, ok = analyze_full(ast)
    if not ok:
        print("[CODEGEN] Análise semântica falhou.")
        sys.exit(1)

    gen = CodeGenerator(analyzer)
    vm_code = gen.generate(ast)

    # Escrever ficheiro .vm
    out = sys.argv[1].replace('.f77', '.vm')
    with open(out, 'w') as f:
        f.write(vm_code)

    print(vm_code)
    print(f"\n[CODEGEN] Código VM escrito em '{out}'.")