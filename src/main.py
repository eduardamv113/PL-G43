# main.py - Ponto de entrada do compilador Fortran 77
# Projeto PL2026 - Grupo G43
#
# Uso:
#   python main.py <ficheiro.f77>             # compila e gera <ficheiro>.vm
#   python main.py <ficheiro.f77> -o out.vm  # especifica ficheiro de saída
#   python main.py <ficheiro.f77> --ast      # mostra a AST e para
#   python main.py <ficheiro.f77> --tokens   # mostra os tokens e para

import sys
import os
import argparse
import pprint


def main():
    # -----------------------------------------------------------------------
    # Argumentos da linha de comandos
    # -----------------------------------------------------------------------
    ap = argparse.ArgumentParser(
        description='Compilador Fortran 77 → VM (PL2026 G43)'
    )
    ap.add_argument('source',
                    help='Ficheiro Fortran 77 de entrada (.f77)')
    ap.add_argument('-o', '--output',
                    help='Ficheiro de saída com código VM (por omissão: <source>.vm)')
    ap.add_argument('--tokens', action='store_true',
                    help='Mostra os tokens gerados pelo lexer e termina')
    ap.add_argument('--ast', action='store_true',
                    help='Mostra a AST gerada pelo parser e termina')
    ap.add_argument('--no-semantic', action='store_true',
                    help='Salta a análise semântica (não recomendado)')
    args = ap.parse_args()

    # -----------------------------------------------------------------------
    # Leitura do ficheiro fonte
    # -----------------------------------------------------------------------
    if not os.path.isfile(args.source):
        print(f"[ERRO] Ficheiro não encontrado: {args.source}")
        sys.exit(1)

    with open(args.source, 'r') as f:
        source = f.read()

    print(f"[1/4] A analisar léxico de '{args.source}'...")

    # -----------------------------------------------------------------------
    # Fase 1 — Análise Léxica
    # -----------------------------------------------------------------------
    from lexer import tokenize

    tokens = tokenize(source)

    if args.tokens:
        print("\n=== TOKENS ===")
        for tok in tokens:
            print(f"  {tok.type:<15} {tok.value!r}")
        sys.exit(0)

    print(f"      {len(tokens)} tokens gerados.")

    # -----------------------------------------------------------------------
    # Fase 2 — Análise Sintática
    # -----------------------------------------------------------------------
    print("[2/4] A construir AST (parser)...")

    from parser import parse

    ast = parse(source)

    if ast is None:
        print("[ERRO] O parser falhou. Compilação abortada.")
        sys.exit(1)

    if args.ast:
        print("\n=== AST ===")
        pprint.pprint(ast)
        sys.exit(0)

    print("      AST construída com sucesso.")

    # -----------------------------------------------------------------------
    # Fase 3 — Análise Semântica
    # -----------------------------------------------------------------------
    if not args.no_semantic:
        print("[3/4] A fazer análise semântica...")

        from semantic import analyze_full

        analyzer, ok = analyze_full(ast)

        if not ok:
            print("[ERRO] Análise semântica falhou. Compilação abortada.")
            sys.exit(1)

        print("      Sem erros semânticos.")
    else:
        analyzer = None
        print("[3/4] Análise semântica ignorada (--no-semantic).")

    # -----------------------------------------------------------------------
    # Fase 4 — Geração de Código
    # -----------------------------------------------------------------------
    print("[4/4] A gerar código VM...")

    try:
        from codegen import CodeGenerator

        gen = CodeGenerator(analyzer)
        vm_code = gen.generate(ast)
    except NotImplementedError:
        print("      [AVISO] codegen.py ainda não implementado.")
        print("\nCompilação incompleta — fases 1, 2 e 3 concluídas com sucesso.")
        sys.exit(0)
    except Exception as e:
        print(f"[ERRO] Falha na geração de código: {e}")
        sys.exit(1)

    # -----------------------------------------------------------------------
    # Escrita do ficheiro de saída
    # -----------------------------------------------------------------------
    if args.output:
        out_path = args.output
    else:
        base = os.path.splitext(args.source)[0]
        out_path = base + '.vm'

    with open(out_path, 'w') as f:
        f.write(vm_code)

    print(f"      Código VM escrito em '{out_path}'.")
    print("\nCompilação concluída com sucesso.")


if __name__ == '__main__':
    main()