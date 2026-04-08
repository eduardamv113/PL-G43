# lexer.py - Analisador Léxico para Fortran 77
# Projeto PL2026 - Grupo G43
# Usa formato livre (free-form) em vez de colunas fixas

import ply.lex as lex

# ---------------------------------------------------------------------------
# Palavras-chave
# ---------------------------------------------------------------------------
reserved = {
    'PROGRAM'    : 'PROGRAM',
    'END'        : 'END',
    'INTEGER'    : 'INTEGER',
    'REAL'       : 'REAL',
    'LOGICAL'    : 'LOGICAL',
    'CHARACTER'  : 'CHARACTER',
    'IF'         : 'IF',
    'THEN'       : 'THEN',
    'ELSE'       : 'ELSE',
    'ENDIF'      : 'ENDIF',
    'DO'         : 'DO',
    'CONTINUE'   : 'CONTINUE',
    'GOTO'       : 'GOTO',
    'PRINT'      : 'PRINT',
    'READ'       : 'READ',
    'RETURN'     : 'RETURN',
    'STOP'       : 'STOP',
    'FUNCTION'   : 'FUNCTION',
    'SUBROUTINE' : 'SUBROUTINE',
    'CALL'       : 'CALL',
    'COMMON'     : 'COMMON',
    'PARAMETER'  : 'PARAMETER',
    'DIMENSION'  : 'DIMENSION',
    'WRITE'      : 'WRITE',
    'FORMAT'     : 'FORMAT',
    'MOD'        : 'MOD',
}

# ---------------------------------------------------------------------------
# Lista de tokens
# ---------------------------------------------------------------------------
tokens = list(reserved.values()) + [
    # Identificadores e literais
    'ID',
    'INTEGER_LIT',
    'REAL_LIT',
    'STRING',

    # Operadores aritméticos
    'PLUS',       # +
    'MINUS',      # -
    'TIMES',      # *
    'DIVIDE',     # /
    'POWER',      # **

    # Operadores relacionais Fortran (forma .XX.)
    'EQ',         # .EQ.
    'NE',         # .NE.
    'LT',         # .LT.
    'LE',         # .LE.
    'GT',         # .GT.
    'GE',         # .GE.

    # Operadores lógicos
    'AND',        # .AND.
    'OR',         # .OR.
    'NOT',        # .NOT.
    'TRUE',       # .TRUE.
    'FALSE',      # .FALSE.

    # Operadores de comparação alternativos (C-style, opcional)
    'EQEQ',      # ==
    'NEQ',       # /=
    'LEQ',       # <=
    'GEQ',       # >=
    'LTLT',      # <
    'GTGT',      # >

    # Atribuição e pontuação
    'ASSIGN',     # =
    'LPAREN',     # (
    'RPAREN',     # )
    'COMMA',      # ,
    'COLON',      # :
    'SEMICOLON',  # ;
    'STAR',       # * (usado em PRINT *, ...)
    'CONCAT',     # // (concatenação de strings)

    # Label (número no início de linha para DO/CONTINUE/GOTO)
    'LABEL',
]

# ---------------------------------------------------------------------------
# Regras simples (string)
# ---------------------------------------------------------------------------
t_PLUS      = r'\+'
t_MINUS     = r'-'
t_DIVIDE    = r'/'
t_ASSIGN    = r'='
t_LPAREN    = r'\('
t_RPAREN    = r'\)'
t_COMMA     = r','
t_COLON     = r':'
t_SEMICOLON = r';'
t_CONCAT    = r'//'

# Ignorar espaços e tabulações (mas NÃO newlines — tratados à parte)
t_ignore = ' \t\r'

# ---------------------------------------------------------------------------
# Regras com função (ordem importa: mais específicas primeiro)
# ---------------------------------------------------------------------------

def t_POWER(t):
    r'\*\*'
    return t

def t_TIMES(t):
    r'\*'
    return t

# Operadores relacionais e lógicos Fortran (.EQ., .AND., etc.)
def t_TRUE(t):
    r'\.TRUE\.'
    t.value = True
    return t

def t_FALSE(t):
    r'\.FALSE\.'
    t.value = False
    return t

def t_EQ(t):
    r'\.EQ\.'
    return t

def t_NE(t):
    r'\.NE\.'
    return t

def t_LE(t):
    r'\.LE\.'
    return t

def t_LT(t):
    r'\.LT\.'
    return t

def t_GE(t):
    r'\.GE\.'
    return t

def t_GT(t):
    r'\.GT\.'
    return t

def t_AND(t):
    r'\.AND\.'
    return t

def t_OR(t):
    r'\.OR\.'
    return t

def t_NOT(t):
    r'\.NOT\.'
    return t

# Operadores C-style (free-form Fortran 90+, suporte opcional)
def t_EQEQ(t):
    r'=='
    return t

def t_NEQ(t):
    r'/='
    return t

def t_LEQ(t):
    r'<='
    return t

def t_GEQ(t):
    r'>='
    return t

def t_LTLT(t):
    r'<'
    return t

def t_GTGT(t):
    r'>'
    return t

# Números reais (antes de inteiros para ter prioridade)
def t_REAL_LIT(t):
    r'\d+\.\d*([eE][+-]?\d+)?|\d+[eE][+-]?\d+'
    t.value = float(t.value)
    return t

# Números inteiros
def t_INTEGER_LIT(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Strings entre plicas
def t_STRING(t):
    r"'[^']*'"
    t.value = t.value[1:-1]  # remove as plicas
    return t

# Identificadores e palavras-chave (case-insensitive)
def t_ID(t):
    r'[A-Za-z][A-Za-z0-9_]*'
    t.value = t.value.upper()
    t.type = reserved.get(t.value, 'ID')
    return t

# Comentários Fortran 77: linha que começa com C ou ! (free-form)
def t_COMMENT(t):
    r'(^|\n)[Cc].*|!.*'
    pass  # ignorar comentários

# Newlines — rastrear número de linha
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# ---------------------------------------------------------------------------
# Erros
# ---------------------------------------------------------------------------
def t_error(t):
    print(f"[LEXER] Caracter ilegal '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)

# ---------------------------------------------------------------------------
# Construção do lexer
# ---------------------------------------------------------------------------
lexer = lex.lex()

# ---------------------------------------------------------------------------
# Função utilitária para testar
# ---------------------------------------------------------------------------
def tokenize(code):
    """Recebe código Fortran como string e devolve lista de tokens."""
    lexer.input(code)
    lexer.lineno = 1
    result = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        result.append(tok)
    return result
