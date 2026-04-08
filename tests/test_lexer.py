# test_lexer.py - Testes do Analisador Léxico
# Corre todos os ficheiros .f77 da pasta tests/ e mostra os tokens gerados

import sys
import os

# Adiciona o diretório src ao path para importar o lexer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from lexer import tokenize

# ---------------------------------------------------------------------------
# Ficheiros de teste
# ---------------------------------------------------------------------------
TEST_DIR = os.path.dirname(__file__)

test_files = [
    'hello.f77',
    'fatorial.f77',
    'primo.f77',
    'somar.f77',
    'conversor.f77',
]

# ---------------------------------------------------------------------------
# Correr testes
# ---------------------------------------------------------------------------
def run_test(filepath):
    with open(filepath, 'r') as f:
        code = f.read()

    print(f"\n{'='*60}")
    print(f"FICHEIRO: {os.path.basename(filepath)}")
    print('='*60)

    try:
        tokens = tokenize(code)
        for tok in tokens:
            print(f"  {tok.type:<15} | {str(tok.value):<25} | linha {tok.lineno}")
        print(f"\n  ✓ Total: {len(tokens)} tokens sem erros")
        return True
    except Exception as e:
        print(f"  ✗ ERRO: {e}")
        return False


def main():
    passed = 0
    failed = 0

    for filename in test_files:
        filepath = os.path.join(TEST_DIR, filename)
        if not os.path.exists(filepath):
            print(f"\n  [AVISO] Ficheiro não encontrado: {filepath}")
            continue

        success = run_test(filepath)
        if success:
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"RESULTADOS: {passed} passaram  |  {failed} falharam")
    print('='*60)


if __name__ == '__main__':
    main()
