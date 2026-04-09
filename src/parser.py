# parser.py - Analisador Sintático para Fortran 77
# Projeto PL2026 - Grupo G43
# Usa ply.yacc; compatível com o lexer.py do grupo

import ply.yacc as yacc
from lexer import tokens, lexer  # noqa: F401

# ---------------------------------------------------------------------------
# Precedências (menor → maior prioridade)
# ---------------------------------------------------------------------------
precedence = (
    ('left',  'OR'),
    ('left',  'AND'),
    ('right', 'NOT'),
    ('left',  'EQ', 'NE', 'LT', 'LE', 'GT', 'GE',
               'EQEQ', 'NEQ', 'LTLT', 'GTGT', 'LEQ', 'GEQ'),
    ('left',  'CONCAT'),
    ('left',  'PLUS', 'MINUS'),
    ('left',  'TIMES', 'DIVIDE'),
    ('right', 'UMINUS', 'UPLUS'),
    ('right', 'POWER'),
)

# ===========================================================================
# Programa
# ===========================================================================

def p_program(p):
    """program : program_unit_list"""
    p[0] = ('program', p[1])

def p_program_unit_list_multi(p):
    """program_unit_list : program_unit_list program_unit"""
    p[0] = p[1] + [p[2]]

def p_program_unit_list_single(p):
    """program_unit_list : program_unit"""
    p[0] = [p[1]]

def p_program_unit(p):
    """program_unit : main_program
                    | function_subprogram
                    | subroutine_subprogram"""
    p[0] = p[1]

# ===========================================================================
# Programa principal
# ===========================================================================

def p_main_program(p):
    """main_program : PROGRAM ID statement_list END"""
    p[0] = ('main_program', p[2], p[3])

# ===========================================================================
# Subprogramas
# ===========================================================================

def p_function_subprogram(p):
    """function_subprogram : type_spec FUNCTION ID LPAREN param_list RPAREN statement_list END"""
    p[0] = ('function', p[3], p[1], p[5], p[7])

def p_function_subprogram_notype(p):
    """function_subprogram : FUNCTION ID LPAREN param_list RPAREN statement_list END"""
    p[0] = ('function', p[2], None, p[4], p[6])

def p_subroutine_subprogram(p):
    """subroutine_subprogram : SUBROUTINE ID LPAREN param_list RPAREN statement_list END"""
    p[0] = ('subroutine', p[2], p[4], p[6])

def p_subroutine_subprogram_noparams(p):
    """subroutine_subprogram : SUBROUTINE ID statement_list END"""
    p[0] = ('subroutine', p[2], [], p[3])

# Parâmetros formais
def p_param_list_multi(p):
    """param_list : param_list COMMA ID"""
    p[0] = p[1] + [p[3]]

def p_param_list_single(p):
    """param_list : ID"""
    p[0] = [p[1]]

def p_param_list_empty(p):
    """param_list :"""
    p[0] = []

# ===========================================================================
# Lista de statements
# ===========================================================================

def p_statement_list_multi(p):
    """statement_list : statement_list statement"""
    if p[2] is not None:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = p[1]

def p_statement_list_single(p):
    """statement_list : statement"""
    if p[1] is not None:
        p[0] = [p[1]]
    else:
        p[0] = []

# ===========================================================================
# Statement (com ou sem label numérico)
# ===========================================================================

def p_statement_labeled(p):
    """statement : INTEGER_LIT unlabeled_statement"""
    p[0] = ('labeled', p[1], p[2])

def p_statement_unlabeled(p):
    """statement : unlabeled_statement"""
    p[0] = p[1]

# ===========================================================================
# Statements sem label
# ===========================================================================

def p_unlabeled_statement(p):
    """unlabeled_statement : declaration_stmt
                           | assignment_stmt
                           | if_stmt
                           | if_then_stmt
                           | do_stmt
                           | goto_stmt
                           | continue_stmt
                           | print_stmt
                           | write_stmt
                           | read_stmt
                           | call_stmt
                           | return_stmt
                           | stop_stmt
                           | format_stmt
                           | common_stmt
                           | parameter_stmt
                           | dimension_stmt"""
    p[0] = p[1]

# ===========================================================================
# Declarações de tipos e variáveis
# ===========================================================================

def p_declaration_stmt(p):
    """declaration_stmt : type_spec var_decl_list"""
    p[0] = ('declaration', p[1], p[2])

def p_type_spec_simple(p):
    """type_spec : INTEGER
                 | REAL
                 | LOGICAL
                 | CHARACTER"""
    p[0] = p[1]

def p_type_spec_char_len(p):
    """type_spec : CHARACTER TIMES INTEGER_LIT"""
    p[0] = ('CHARACTER', p[3])

def p_var_decl_list_multi(p):
    """var_decl_list : var_decl_list COMMA var_decl"""
    p[0] = p[1] + [p[3]]

def p_var_decl_list_single(p):
    """var_decl_list : var_decl"""
    p[0] = [p[1]]

def p_var_decl_simple(p):
    """var_decl : ID"""
    p[0] = ('var', p[1], None)

def p_var_decl_array(p):
    """var_decl : ID LPAREN dim_list RPAREN"""
    p[0] = ('array', p[1], p[3])

# Especificações de dimensão
def p_dim_list_multi(p):
    """dim_list : dim_list COMMA dim_spec"""
    p[0] = p[1] + [p[3]]

def p_dim_list_single(p):
    """dim_list : dim_spec"""
    p[0] = [p[1]]

def p_dim_spec_range(p):
    """dim_spec : expr COLON expr"""
    p[0] = ('range', p[1], p[3])

def p_dim_spec_size(p):
    """dim_spec : expr"""
    p[0] = p[1]

# ===========================================================================
# Atribuição
# ===========================================================================

def p_assignment_stmt(p):
    """assignment_stmt : lvalue ASSIGN expr"""
    p[0] = ('assign', p[1], p[3])

def p_lvalue_id(p):
    """lvalue : ID"""
    p[0] = ('var', p[1])

def p_lvalue_array_elem(p):
    """lvalue : ID LPAREN expr_list RPAREN"""
    p[0] = ('array_elem', p[1], p[3])

# ===========================================================================
# IF simples (uma linha, sem THEN)
# ===========================================================================

def p_if_stmt(p):
    """if_stmt : IF LPAREN expr RPAREN unlabeled_statement"""
    p[0] = ('if_simple', p[3], p[5])

# ===========================================================================
# IF-THEN / IF-THEN-ELSE / ENDIF
# ===========================================================================

def p_if_then_stmt_full(p):
    """if_then_stmt : IF LPAREN expr RPAREN THEN statement_list ELSE statement_list ENDIF"""
    p[0] = ('if_then_else', p[3], p[6], p[8])

def p_if_then_stmt_no_else(p):
    """if_then_stmt : IF LPAREN expr RPAREN THEN statement_list ENDIF"""
    p[0] = ('if_then', p[3], p[6])

# ===========================================================================
# DO loop com label
# ===========================================================================

def p_do_stmt(p):
    """do_stmt : DO INTEGER_LIT ID ASSIGN expr COMMA expr"""
    p[0] = ('do', p[2], p[3], p[5], p[7], None)

def p_do_stmt_step(p):
    """do_stmt : DO INTEGER_LIT ID ASSIGN expr COMMA expr COMMA expr"""
    p[0] = ('do', p[2], p[3], p[5], p[7], p[9])

# ===========================================================================
# GOTO
# ===========================================================================

def p_goto_stmt(p):
    """goto_stmt : GOTO INTEGER_LIT"""
    p[0] = ('goto', p[2])

# ===========================================================================
# CONTINUE
# ===========================================================================

def p_continue_stmt(p):
    """continue_stmt : CONTINUE"""
    p[0] = ('continue',)

# ===========================================================================
# STOP / RETURN
# ===========================================================================

def p_stop_stmt(p):
    """stop_stmt : STOP"""
    p[0] = ('stop',)

def p_return_stmt(p):
    """return_stmt : RETURN"""
    p[0] = ('return',)

# ===========================================================================
# PRINT
# ===========================================================================

def p_print_stmt_star(p):
    """print_stmt : PRINT TIMES COMMA print_item_list"""
    p[0] = ('print', '*', p[4])

def p_print_stmt_fmt(p):
    """print_stmt : PRINT INTEGER_LIT COMMA print_item_list"""
    p[0] = ('print', p[2], p[4])

def p_print_item_list_multi(p):
    """print_item_list : print_item_list COMMA print_item"""
    p[0] = p[1] + [p[3]]

def p_print_item_list_single(p):
    """print_item_list : print_item"""
    p[0] = [p[1]]

def p_print_item(p):
    """print_item : expr"""
    p[0] = p[1]

# ===========================================================================
# WRITE
# ===========================================================================

def p_write_stmt(p):
    """write_stmt : WRITE LPAREN write_ctrl RPAREN print_item_list"""
    p[0] = ('write', p[3], p[5])

def p_write_stmt_nolist(p):
    """write_stmt : WRITE LPAREN write_ctrl RPAREN"""
    p[0] = ('write', p[3], [])

def p_write_ctrl_star_star(p):
    """write_ctrl : TIMES COMMA TIMES"""
    p[0] = ('*', '*')

def p_write_ctrl_unit_fmt(p):
    """write_ctrl : expr COMMA INTEGER_LIT"""
    p[0] = (p[1], p[3])

def p_write_ctrl_unit_star(p):
    """write_ctrl : expr COMMA TIMES"""
    p[0] = (p[1], '*')

# ===========================================================================
# READ
# ===========================================================================

def p_read_stmt_star(p):
    """read_stmt : READ TIMES COMMA expr_list"""
    p[0] = ('read', '*', p[4])

def p_read_stmt_fmt(p):
    """read_stmt : READ INTEGER_LIT COMMA expr_list"""
    p[0] = ('read', p[2], p[4])

# ===========================================================================
# CALL
# ===========================================================================

def p_call_stmt(p):
    """call_stmt : CALL ID LPAREN expr_list RPAREN"""
    p[0] = ('call', p[2], p[4])

def p_call_stmt_noargs(p):
    """call_stmt : CALL ID"""
    p[0] = ('call', p[2], [])

# ===========================================================================
# FORMAT
# ===========================================================================

def p_format_stmt(p):
    """format_stmt : FORMAT LPAREN format_spec_list RPAREN"""
    p[0] = ('format', p[3])

def p_format_spec_list_multi(p):
    """format_spec_list : format_spec_list COMMA format_spec"""
    p[0] = p[1] + [p[3]]

def p_format_spec_list_single(p):
    """format_spec_list : format_spec"""
    p[0] = [p[1]]

def p_format_spec_str(p):
    """format_spec : STRING"""
    p[0] = ('str', p[1])

def p_format_spec_id(p):
    """format_spec : ID"""
    p[0] = ('spec', p[1])

def p_format_spec_rep_id(p):
    """format_spec : INTEGER_LIT ID"""
    p[0] = ('rep_spec', p[1], p[2])

def p_format_spec_int(p):
    """format_spec : INTEGER_LIT"""
    p[0] = ('int', p[1])

# ===========================================================================
# COMMON
# ===========================================================================

def p_common_stmt(p):
    """common_stmt : COMMON id_list"""
    p[0] = ('common', None, p[2])

def p_common_stmt_named(p):
    """common_stmt : COMMON DIVIDE ID DIVIDE id_list"""
    p[0] = ('common', p[3], p[5])

def p_id_list_multi(p):
    """id_list : id_list COMMA ID"""
    p[0] = p[1] + [p[3]]

def p_id_list_single(p):
    """id_list : ID"""
    p[0] = [p[1]]

# ===========================================================================
# PARAMETER
# ===========================================================================

def p_parameter_stmt(p):
    """parameter_stmt : PARAMETER LPAREN param_assign_list RPAREN"""
    p[0] = ('parameter', p[3])

def p_param_assign_list_multi(p):
    """param_assign_list : param_assign_list COMMA param_assign"""
    p[0] = p[1] + [p[3]]

def p_param_assign_list_single(p):
    """param_assign_list : param_assign"""
    p[0] = [p[1]]

def p_param_assign(p):
    """param_assign : ID ASSIGN expr"""
    p[0] = (p[1], p[3])

# ===========================================================================
# DIMENSION
# ===========================================================================

def p_dimension_stmt(p):
    """dimension_stmt : DIMENSION var_decl_list"""
    p[0] = ('dimension', p[2])

# ===========================================================================
# Expressões
# ===========================================================================

def p_expr_binop(p):
    """expr : expr PLUS   expr
            | expr MINUS  expr
            | expr TIMES  expr
            | expr DIVIDE expr
            | expr POWER  expr"""
    p[0] = ('binop', p[2], p[1], p[3])

def p_expr_concat(p):
    """expr : expr CONCAT expr"""
    p[0] = ('concat', p[1], p[3])

def p_expr_relop_fortran(p):
    """expr : expr EQ expr
            | expr NE expr
            | expr LT expr
            | expr LE expr
            | expr GT expr
            | expr GE expr"""
    p[0] = ('relop', p[2], p[1], p[3])

def p_expr_relop_cstyle(p):
    """expr : expr EQEQ expr
            | expr NEQ  expr
            | expr LTLT expr
            | expr GTGT expr
            | expr LEQ  expr
            | expr GEQ  expr"""
    p[0] = ('relop', p[2], p[1], p[3])

def p_expr_logop(p):
    """expr : expr AND expr
            | expr OR  expr"""
    p[0] = ('logop', p[2], p[1], p[3])

def p_expr_not(p):
    """expr : NOT expr"""
    p[0] = ('not', p[2])

def p_expr_uminus(p):
    """expr : MINUS expr %prec UMINUS"""
    p[0] = ('uminus', p[2])

def p_expr_uplus(p):
    """expr : PLUS expr %prec UPLUS"""
    p[0] = p[2]

def p_expr_group(p):
    """expr : LPAREN expr RPAREN"""
    p[0] = p[2]

def p_expr_integer(p):
    """expr : INTEGER_LIT"""
    p[0] = ('int', p[1])

def p_expr_real(p):
    """expr : REAL_LIT"""
    p[0] = ('real', p[1])

def p_expr_string(p):
    """expr : STRING"""
    p[0] = ('string', p[1])

def p_expr_true(p):
    """expr : TRUE"""
    p[0] = ('bool', True)

def p_expr_false(p):
    """expr : FALSE"""
    p[0] = ('bool', False)

def p_expr_id(p):
    """expr : ID"""
    p[0] = ('var', p[1])

# Acesso a array ou chamada de função/intrínseco
def p_expr_array_or_call(p):
    """expr : ID LPAREN expr_list RPAREN"""
    p[0] = ('call_or_array', p[1], p[3])

# MOD intrínseco reconhecido explicitamente pelo lexer como keyword
def p_expr_mod(p):
    """expr : MOD LPAREN expr COMMA expr RPAREN"""
    p[0] = ('call_or_array', 'MOD', [p[3], p[5]])

# Lista de expressões
def p_expr_list_multi(p):
    """expr_list : expr_list COMMA expr"""
    p[0] = p[1] + [p[3]]

def p_expr_list_single(p):
    """expr_list : expr"""
    p[0] = [p[1]]

def p_expr_list_empty(p):
    """expr_list :"""
    p[0] = []

# ===========================================================================
# Tratamento de erros
# ===========================================================================

def p_error(p):
    if p:
        print(f"[PARSER] Erro sintático no token '{p.value}' "
              f"(tipo: {p.type}) na linha {p.lineno}")
    else:
        print("[PARSER] Erro sintático: fim de ficheiro inesperado")

# ===========================================================================
# Construção do parser
# ===========================================================================

parser = yacc.yacc(debug=False, outputdir='.')

# ===========================================================================
# API pública
# ===========================================================================

def parse(code: str):
    """
    Recebe código Fortran 77 como string e devolve a AST (tuplos aninhados).
    Retorna None em caso de erro irrecuperável.
    """
    from lexer import lexer as _lexer
    _lexer.lineno = 1
    return parser.parse(code, lexer=_lexer, tracking=True)


# ===========================================================================
# Execução direta: python parser.py <ficheiro.f77>
# ===========================================================================

if __name__ == '__main__':
    import sys
    import pprint

    if len(sys.argv) < 2:
        print("Uso: python parser.py <ficheiro.f77>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        source = f.read()

    ast = parse(source)
    if ast:
        pprint.pprint(ast)
    else:
        print("[PARSER] Falha no parsing.")