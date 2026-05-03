# semantic.py - Analisador Semântico para Fortran 77
# Projeto PL2026 - Grupo G43

# ===========================================================================
# Tabela de Símbolos
# ===========================================================================

class Symbol:
    """Representa uma entrada na tabela de símbolos."""
    def __init__(self, name, kind, dtype, dims=None, params=None, return_type=None):
        self.name       = name         # nome da variável/função
        self.kind       = kind         # 'var', 'array', 'function', 'subroutine', 'parameter'
        self.dtype      = dtype        # 'INTEGER', 'REAL', 'LOGICAL', 'CHARACTER', None
        self.dims       = dims or []   # dimensões (para arrays)
        self.params     = params or [] # lista de tipos dos parâmetros (para funções/subrotinas)
        self.return_type = return_type # tipo de retorno (para funções)

    def __repr__(self):
        return f"Symbol({self.name}, {self.kind}, {self.dtype})"


class SymbolTable:
    """Tabela de símbolos com suporte a âmbitos (scopes) encadeados."""

    def __init__(self, name='global', parent=None):
        self.name    = name
        self.parent  = parent
        self.symbols = {}

    def declare(self, symbol: Symbol):
        if symbol.name in self.symbols:
            return False  # já declarado neste âmbito
        self.symbols[symbol.name] = symbol
        return True

    def lookup(self, name: str):
        """Procura o símbolo no âmbito atual e nos âmbitos pai."""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def lookup_local(self, name: str):
        """Procura apenas no âmbito atual."""
        return self.symbols.get(name)


# ===========================================================================
# Regras de tipo implícito do Fortran 77
# (variáveis I-N são INTEGER por omissão, restantes são REAL)
# ===========================================================================

def implicit_type(name: str) -> str:
    first = name[0].upper()
    return 'INTEGER' if 'I' <= first <= 'N' else 'REAL'


# ===========================================================================
# Analisador Semântico
# ===========================================================================

class SemanticAnalyzer:

    def __init__(self, implicit_typing=True):
        self.implicit_typing = implicit_typing  # regra I-N do Fortran 77
        self.errors   = []
        self.warnings = []
        self.global_scope = SymbolTable('global')
        self.current_scope = self.global_scope
        self.current_unit  = None  # nome do programa/função atual
        # Mapa label → statement, para validar DO/CONTINUE
        self.do_labels   = {}   # label → ('do', var, ...)
        self.cont_labels = set()  # labels vistos em CONTINUE

    # -----------------------------------------------------------------------
    # Helpers de erro / aviso
    # -----------------------------------------------------------------------

    def error(self, msg):
        self.errors.append(f"[SEMÂNTICO] Erro: {msg}")

    def warning(self, msg):
        self.warnings.append(f"[SEMÂNTICO] Aviso: {msg}")

    def report(self):
        for w in self.warnings:
            print(w)
        for e in self.errors:
            print(e)
        if not self.errors and not self.warnings:
            print("[SEMÂNTICO] Nenhum erro encontrado.")
        return len(self.errors) == 0

    # -----------------------------------------------------------------------
    # Entrada principal
    # -----------------------------------------------------------------------

    def analyze(self, ast):
        """Recebe a AST do parser e analisa-a semanticamente."""
        if ast is None:
            self.error("AST vazia — o parser falhou.")
            return False
        # ast = ('program', [unit, ...])
        node_type = ast[0]
        if node_type == 'program':
            for unit in ast[1]:
                self.visit_program_unit(unit)
        else:
            self.error(f"Nó raiz desconhecido: {node_type}")
        return self.report()

    # -----------------------------------------------------------------------
    # Unidades de programa
    # -----------------------------------------------------------------------

    def visit_program_unit(self, node):
        kind = node[0]
        if kind == 'main_program':
            _, name, stmts = node
            self.current_unit = name or 'MAIN'
            scope = SymbolTable(self.current_unit, parent=self.global_scope)
            self.current_scope = scope
            self.do_labels.clear()
            self.cont_labels.clear()
            self._visit_stmts(stmts)
            self._check_do_labels()
            self.current_scope = self.global_scope

        elif kind == 'function':
            _, name, rtype, params, stmts = node
            rtype = rtype or implicit_type(name)
            sym = Symbol(name, 'function', rtype, return_type=rtype)
            if not self.global_scope.declare(sym):
                self.warning(f"Função '{name}' já declarada.")
            scope = SymbolTable(name, parent=self.global_scope)
            # Declarar parâmetros formais com tipo implícito
            for p in params:
                psym = Symbol(p, 'var', implicit_type(p))
                scope.declare(psym)
            # Declarar variável de retorno com o mesmo nome da função
            scope.declare(Symbol(name, 'var', rtype))
            self.current_unit = name
            self.current_scope = scope
            self.do_labels.clear()
            self.cont_labels.clear()
            self._visit_stmts(stmts)
            self._check_do_labels()
            self.current_scope = self.global_scope

        elif kind == 'subroutine':
            _, name, params, stmts = node
            sym = Symbol(name, 'subroutine', None)
            if not self.global_scope.declare(sym):
                self.warning(f"Subrotina '{name}' já declarada.")
            scope = SymbolTable(name, parent=self.global_scope)
            for p in params:
                psym = Symbol(p, 'var', implicit_type(p))
                scope.declare(psym)
            self.current_unit = name
            self.current_scope = scope
            self.do_labels.clear()
            self.cont_labels.clear()
            self._visit_stmts(stmts)
            self._check_do_labels()
            self.current_scope = self.global_scope

        else:
            self.error(f"Unidade de programa desconhecida: {kind}")

    # -----------------------------------------------------------------------
    # Lista de statements
    # -----------------------------------------------------------------------

    def _visit_stmts(self, stmts):
        if stmts is None:
            return
        for stmt in stmts:
            self.visit_stmt(stmt)

    # -----------------------------------------------------------------------
    # Statement
    # -----------------------------------------------------------------------

    def visit_stmt(self, node):
        if node is None:
            return
        kind = node[0]

        if kind == 'labeled':
            _, label, inner = node
            self._register_label(label, inner)
            self.visit_stmt(inner)

        elif kind == 'declaration':
            self._visit_declaration(node)

        elif kind == 'assign':
            self._visit_assign(node)

        elif kind == 'if_simple':
            _, cond, body = node
            self._check_logical(cond)
            self.visit_stmt(body)

        elif kind == 'if_then':
            _, cond, then_stmts = node
            self._check_logical(cond)
            self._visit_stmts(then_stmts)

        elif kind == 'if_then_else':
            _, cond, then_stmts, else_stmts = node
            self._check_logical(cond)
            self._visit_stmts(then_stmts)
            self._visit_stmts(else_stmts)

        elif kind == 'do':
            _, label, var, start, end, step = node
            self.do_labels[label] = node
            self._ensure_declared(var)
            vtype = self._typeof(('var', var))
            if vtype not in ('INTEGER', 'REAL', None):
                self.error(f"Variável de controlo do DO '{var}' deve ser numérica.")
            self._typeof(start)
            self._typeof(end)
            if step is not None:
                self._typeof(step)

        elif kind == 'goto':
            pass  # validação de label feita no final

        elif kind == 'continue':
            pass  # label já registado acima

        elif kind == 'print':
            _, fmt, items = node
            for item in items:
                self._typeof(item)

        elif kind == 'write':
            _, ctrl, items = node
            for item in items:
                self._typeof(item)

        elif kind == 'read':
            _, fmt, targets = node
            for t in targets:
                if isinstance(t, tuple) and t[0] in ('var', 'array_elem'):
                    self._ensure_declared(t[1])
                else:
                    self._typeof(t)

        elif kind == 'call':
            _, name, args = node
            sym = self.current_scope.lookup(name)
            if sym is None:
                # subrotinas podem ser declaradas depois — apenas aviso
                self.warning(f"Subrotina '{name}' chamada mas não declarada.")
            elif sym.kind not in ('subroutine', 'function'):
                self.error(f"'{name}' não é uma subrotina.")
            for a in args:
                self._typeof(a)

        elif kind == 'return':
            if self.current_unit == 'MAIN':
                self.warning("RETURN dentro do programa principal.")

        elif kind in ('stop', 'continue', 'format', 'common',
                      'parameter', 'dimension'):
            pass  # sem verificações adicionais relevantes

        else:
            self.warning(f"Statement não tratado pelo semântico: {kind}")

    # -----------------------------------------------------------------------
    # Declarações
    # -----------------------------------------------------------------------

    def _visit_declaration(self, node):
        _, dtype, decls = node
        # dtype pode ser string ('INTEGER') ou tuplo ('CHARACTER', n)
        if isinstance(dtype, tuple):
            base_type = dtype[0]
        else:
            base_type = dtype

        for decl in decls:
            dkind = decl[0]
            if dkind == 'var':
                _, name, _ = decl
                
                # Permitir redeclaração de parâmetros em funções/subrotinas
                existing = self.current_scope.lookup_local(name)
                if existing and existing.kind == 'var':
                    # Redeclaração de parâmetro: atualizar tipo
                    # (a redeclaração explícita sobrepõe o tipo implícito)
                    existing.dtype = base_type
                else:
                    # Declaração nova
                    if existing:
                        self.error(f"Variável '{name}' declarada mais do que uma vez em '{self.current_unit}'.")
                    else:
                        sym = Symbol(name, 'var', base_type)
                        self.current_scope.declare(sym)

            elif dkind == 'array':
                _, name, dims = decl
                
                # Permitir redeclaração de parâmetros em funções/subrotinas
                existing = self.current_scope.lookup_local(name)
                if existing and existing.kind == 'array':
                    # Redeclaração: apenas ignorar (assumir que é a mesma)
                    pass
                else:
                    if existing:
                        self.error(f"Array '{name}' declarado mais do que uma vez em '{self.current_unit}'.")
                    else:
                        sym = Symbol(name, 'array', base_type, dims=dims)
                        self.current_scope.declare(sym)

    # -----------------------------------------------------------------------
    # Atribuição
    # -----------------------------------------------------------------------

    def _visit_assign(self, node):
        _, lval, rval = node
        ltype = self._typeof_lval(lval)
        rtype = self._typeof(rval)
        if ltype and rtype and not self._types_compatible(ltype, rtype):
            self.warning(
                f"Atribuição com tipos incompatíveis: {ltype} <- {rtype} "
                f"('{self._lval_name(lval)}')."
            )

    def _typeof_lval(self, lval):
        kind = lval[0]
        if kind == 'var':
            return self._ensure_declared(lval[1])
        elif kind == 'array_elem':
            name, indices = lval[1], lval[2]
            sym = self._ensure_declared(name)
            if sym and sym.kind != 'array':
                self.error(f"'{name}' não é um array.")
            for idx in indices:
                t = self._typeof(idx)
                if t and t != 'INTEGER':
                    self.error(f"Índice de array '{name}' deve ser INTEGER, é {t}.")
            return sym.dtype if sym else None
        return None

    def _lval_name(self, lval):
        return lval[1] if len(lval) > 1 else '?'

    # -----------------------------------------------------------------------
    # Tipo de uma expressão (retorna string ou None)
    # -----------------------------------------------------------------------

    def _typeof(self, node):
        if node is None:
            return None
        if not isinstance(node, tuple):
            return None

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
            sym = self._ensure_declared(node[1])
            return sym.dtype if sym else None

        if kind == 'array_elem':
            name, indices = node[1], node[2]
            sym = self._ensure_declared(name)
            for idx in indices:
                t = self._typeof(idx)
                if t and t != 'INTEGER':
                    self.error(f"Índice de '{name}' deve ser INTEGER, é {t}.")
            return sym.dtype if sym else None

        if kind == 'call_or_array':
            name, args = node[1], node[2]
            # intrínsecos conhecidos
            intrinsic = self._intrinsic_type(name, args)
            if intrinsic is not None:
                return intrinsic
            sym = self.current_scope.lookup(name)
            if sym is None:
                self.warning(f"Função/array '{name}' usada mas não declarada.")
                return None
            if sym.kind == 'array':
                return sym.dtype
            if sym.kind == 'function':
                return sym.return_type
            return sym.dtype

        if kind == 'binop':
            _, op, left, right = node
            lt = self._typeof(left)
            rt = self._typeof(right)
            return self._numeric_result_type(lt, rt, op)

        if kind == 'uminus':
            return self._typeof(node[1])

        if kind == 'relop':
            _, op, left, right = node
            lt = self._typeof(left)
            rt = self._typeof(right)
            if lt and rt and not self._types_compatible(lt, rt):
                self.warning(f"Comparação entre tipos {lt} e {rt}.")
            return 'LOGICAL'

        if kind == 'logop':
            _, op, left, right = node
            self._check_logical(left)
            self._check_logical(right)
            return 'LOGICAL'

        if kind == 'not':
            self._check_logical(node[1])
            return 'LOGICAL'

        if kind == 'concat':
            lt = self._typeof(node[1])
            rt = self._typeof(node[2])
            if lt != 'CHARACTER':
                self.error("Operador // requer CHARACTER no lado esquerdo.")
            if rt != 'CHARACTER':
                self.error("Operador // requer CHARACTER no lado direito.")
            return 'CHARACTER'

        return None

    # -----------------------------------------------------------------------
    # Intrínsecos do Fortran 77
    # -----------------------------------------------------------------------

    INTRINSICS = {
        'MOD':   'INTEGER',
        'ABS':   None,       # mesmo tipo do argumento
        'IABS':  'INTEGER',
        'SQRT':  'REAL',
        'EXP':   'REAL',
        'LOG':   'REAL',
        'LOG10': 'REAL',
        'SIN':   'REAL',
        'COS':   'REAL',
        'TAN':   'REAL',
        'ATAN':  'REAL',
        'ATAN2': 'REAL',
        'INT':   'INTEGER',
        'REAL':  'REAL',
        'FLOAT': 'REAL',
        'IFIX':  'INTEGER',
        'MAX':   None,
        'MIN':   None,
        'MAX0':  'INTEGER',
        'MIN0':  'INTEGER',
        'AMAX1': 'REAL',
        'AMIN1': 'REAL',
        'LEN':   'INTEGER',
        'INDEX': 'INTEGER',
        'CHAR':  'CHARACTER',
        'ICHAR': 'INTEGER',
    }

    def _intrinsic_type(self, name, args):
        if name not in self.INTRINSICS:
            return None
        rtype = self.INTRINSICS[name]
        if rtype is None and args:
            rtype = self._typeof(args[0])
        for a in args:
            self._typeof(a)
        return rtype

    # -----------------------------------------------------------------------
    # Auxiliares de tipo
    # -----------------------------------------------------------------------

    def _numeric_result_type(self, lt, rt, op):
        if lt is None or rt is None:
            return lt or rt
        if lt == 'REAL' or rt == 'REAL':
            return 'REAL'
        if lt == 'INTEGER' and rt == 'INTEGER':
            return 'INTEGER'
        self.warning(f"Operação '{op}' entre tipos {lt} e {rt}.")
        return None

    def _types_compatible(self, t1, t2):
        numeric = {'INTEGER', 'REAL'}
        if t1 in numeric and t2 in numeric:
            return True
        return t1 == t2

    def _check_logical(self, node):
        t = self._typeof(node)
        if t and t != 'LOGICAL':
            self.warning(f"Condição com tipo {t} em vez de LOGICAL.")

    # -----------------------------------------------------------------------
    # Garantir que uma variável está declarada (com tipo implícito se necessário)
    # -----------------------------------------------------------------------

    def _ensure_declared(self, name: str):
        sym = self.current_scope.lookup(name)
        if sym is None:
            if self.implicit_typing:
                itype = implicit_type(name)
                sym = Symbol(name, 'var', itype)
                self.current_scope.declare(sym)
                # Não emitimos aviso por cada variável — o Fortran 77 standard permite
            else:
                self.error(f"Variável '{name}' usada sem ser declarada.")
        return sym

    # -----------------------------------------------------------------------
    # Validação de labels DO/CONTINUE
    # -----------------------------------------------------------------------

    def _register_label(self, label, stmt):
        if stmt and stmt[0] == 'continue':
            self.cont_labels.add(label)

    def _check_do_labels(self):
        for label, do_node in self.do_labels.items():
            if label not in self.cont_labels:
                var = do_node[2]
                self.error(
                    f"Ciclo DO com label {label} (variável '{var}') "
                    f"não tem CONTINUE correspondente."
                )


# ===========================================================================
# API pública
# ===========================================================================

def analyze(ast) -> bool:
    """
    Recebe a AST do parser e faz a análise semântica.
    Devolve True se não houver erros, False caso contrário.
    """
    sa = SemanticAnalyzer(implicit_typing=True)
    return sa.analyze(ast)


def analyze_full(ast):
    """
    Como analyze(), mas devolve o próprio SemanticAnalyzer para
    que o codegen possa consultar a tabela de símbolos.
    """
    sa = SemanticAnalyzer(implicit_typing=True)
    ok = sa.analyze(ast)
    return sa, ok


# ===========================================================================
# Execução direta: python semantic.py <ficheiro.f77>
# ===========================================================================

if __name__ == '__main__':
    from pathlib import Path
    import sys
    from parser import parse

    if len(sys.argv) < 2:
        print("Uso: python semantic.py <ficheiro.f77>")
        sys.exit(1)

    # Aceitar caminhos relativos ao cwd e, por conveniência, ao diretório tests do projeto.
    arg_path = Path(sys.argv[1])
    candidates = [arg_path]
    if not arg_path.is_absolute() and len(arg_path.parts) == 1:
        project_root = Path(__file__).resolve().parent.parent
        candidates.append(project_root / 'tests' / arg_path)

    source_path = next((p for p in candidates if p.exists()), None)
    if source_path is None:
        print(f"[SEMÂNTICO] Ficheiro não encontrado: '{sys.argv[1]}'")
        print("[SEMÂNTICO] Dica: usa um caminho válido (ex.: ../tests/hello.f77)")
        sys.exit(1)

    with open(source_path, 'r') as f:
        source = f.read()

    ast = parse(source)
    if ast is None:
        print("[SEMÂNTICO] Parser falhou — análise semântica abortada.")
        sys.exit(1)

    ok = analyze(ast)
    sys.exit(0 if ok else 1)