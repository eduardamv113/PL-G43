# test_codegen.py - Validacao do Gerador de Codigo
# Compila cada .f77 e valida comparando com o ficheiro .vm de referencia

import sys
import os

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from lexer import tokenize
from parser import parse
from semantic import analyze_full
from codegen import CodeGenerator

TEST_DIR = os.path.dirname(__file__)

# Ficheiros de teste e descricao do que testam
test_files = [
    ('hello.f77',        'PRINT basico'),
    ('fatorial.f77',     'DO loop + INTEGER + aritmetica'),
    ('primo.f77',        'IF-THEN-ELSE + GOTO + operadores logicos'),
    ('somar.f77',        'Arrays + READ'),
    ('conversor.f77',    'FUNCTION + RETURN + chamada de subprograma'),
    ('aritmetica.f77',   'Operacoes com REAL'),
    ('classificar.f77',  'IF-THEN-ELSE aninhados'),
    ('pares.f77',        'DO loop com passo (step)'),
    ('subroutine.f77',   'SUBROUTINE + CALL'),
    ('logica.f77',       'Operadores logicos .AND. .OR. .NOT.'),
    ('contagem.f77',     'GOTO + labels'),
    ('matriz.f77',       'Array + DO loops aninhados'),
]


def run_test(filename, description):
    """Compila um .f77 e valida contra o ficheiro .vm de referencia"""
    f77path = os.path.join(TEST_DIR, filename)
    vmpath_ref = f77path.replace('.f77', '.vm')

    print("\n" + "="*60)
    print("TESTE: %-20s [%s]" % (filename, description))
    print("="*60)

    # Verificar ficheiro Fortran
    if not os.path.exists(f77path):
        print("  [X] Ficheiro .f77 nao encontrado")
        return None

    # Verificar ficheiro de referencia
    if not os.path.exists(vmpath_ref):
        print("  [W] Ficheiro .vm de referencia nao existe (sera criado)")
        ref_code = None
    else:
        with open(vmpath_ref, 'r', encoding='utf-8') as f:
            ref_code = f.read()

    # Ler codigo Fortran
    with open(f77path, 'r', encoding='utf-8') as f:
        source = f.read()

    # Fase 1 - Lexer
    try:
        tokens = tokenize(source)
        print("  [OK] Lexer:    %d tokens" % len(tokens))
    except Exception as e:
        print("  [ER] Lexer:    %s" % str(e))
        return False

    # Fase 2 - Parser
    try:
        ast = parse(source)
        if ast is None:
            print("  [ER] Parser:   AST vazia")
            return False
        print("  [OK] Parser:   OK")
    except Exception as e:
        print("  [ER] Parser:   %s" % str(e))
        return False

    # Fase 3 - Semantica
    try:
        analyzer, ok = analyze_full(ast)
        if ok:
            print("  [OK] Semantica: OK")
        else:
            print("  [WR] Semantica: Com erros (ver acima)")
            if analyzer is None:
                return False
    except Exception as e:
        print("  [ER] Semantica: %s" % str(e))
        return False

    # Fase 4 - Codegen
    try:
        gen = CodeGenerator(analyzer)
        generated_code = gen.generate(ast)
        lines = generated_code.strip().split('\n')
        print("  [OK] Codegen:  %d linhas geradas" % len(lines))
    except Exception as e:
        print("  [ER] Codegen:  %s" % str(e))
        return False

    # Validacao: comparar com referencia
    if ref_code is None:
        print("  [NEW] Nova referencia gerada (primeira vez)")
        with open(vmpath_ref, 'w', encoding='utf-8') as f:
            f.write(generated_code)
        return True
    
    if generated_code.strip() == ref_code.strip():
        print("  [OK] Validacao: PASSOU (codigo VM corresponde)")
        return True
    else:
        print("  [ER] Validacao: FALHOU (codigo gerado difere da referencia)")
        return False


def main():
    print("\n" + "="*60)
    print("VALIDACAO DO COMPILADOR FORTRAN 77 para VM")
    print("="*60)

    passed = 0
    failed = 0
    skipped = 0

    for filename, description in test_files:
        result = run_test(filename, description)
        if result is True:
            passed += 1
        elif result is False:
            failed += 1
        else:
            skipped += 1

    print("\n" + "="*60)
    print("RESULTADOS: %d OK | %d FALHARAM | %d AVISO" % (passed, failed, skipped))
    print("="*60)

    # Codigo de saida
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
