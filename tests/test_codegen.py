# test_codegen.py - Testes do Gerador de Código
# Corre todos os ficheiros .f77 da pasta tests/ pelo compilador completo
# e gera os ficheiros .vm correspondentes

import sys
import os

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from lexer import tokenize
from parser import parse
from semantic import analyze_full
from codegen import CodeGenerator

TEST_DIR = os.path.dirname(__file__)

# Ficheiros de teste e descrição do que testam
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
    filepath = os.path.join(TEST_DIR, filename)
    vmpath   = filepath.replace('.f77', '.vm')

    print(f"\n{'='*60}")
    print(f"TESTE: {filename}  [{description}]")
    print('='*60)

    if not os.path.exists(filepath):
        print(f"  [AVISO] Ficheiro nao encontrado: {filepath}")
        return None

    with open(filepath, 'r') as f:
        source = f.read()

    # Fase 1 — Lexer
    try:
        tokens = tokenize(source)
        print(f"  Lexer:    OK ({len(tokens)} tokens)")
    except Exception as e:
        print(f"  Lexer:    ERRO — {e}")
        return False

    # Fase 2 — Parser
    try:
        ast = parse(source)
        if ast is None:
            print("  Parser:   ERRO — AST vazia")
            return False
        print("  Parser:   OK")
    except Exception as e:
        print(f"  Parser:   ERRO — {e}")
        return False

    # Fase 3 — Semântica
    try:
        analyzer, ok = analyze_full(ast)
        if ok:
            print("  Semantica: OK")
        else:
            print("  Semantica: AVISOS/ERROS (ver acima)")
    except Exception as e:
        print(f"  Semantica: ERRO — {e}")
        analyzer = None

    # Fase 4 — Codegen
    try:
        gen = CodeGenerator(analyzer)
        vm_code = gen.generate(ast)
        with open(vmpath, 'w') as f:
            f.write(vm_code)
        lines = vm_code.strip().split('\n')
        print(f"  Codegen:   OK ({len(lines)} linhas de VM geradas)")
        print(f"  Saida:     {vmpath}")
        return True
    except Exception as e:
        print(f"  Codegen:   ERRO — {e}")
        return False


def main():
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

    print(f"\n{'='*60}")
    print(f"RESULTADOS: {passed} OK  |  {failed} falharam  |  {skipped} em falta")
    print('='*60)


if __name__ == '__main__':
    main()