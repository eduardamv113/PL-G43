# Compilador Fortran 77 → VM EWVM

**Projeto de Processamento de Linguagens 2026 - Grupo G43**

Compilador funcional para Fortran 77 que traduz código fonte para código máquina da VM EWVM.

## Quick Start

### Passos

```bash
# 1. Clonar e configurar
git clone <url>
cd PL-G43

# 2. Instalar Python (se necessário)
python --version  # Deve ser 3.11+

# 3. Criar ambiente virtual
python -m venv .venv

# 4. Ativar (escolhe conforme teu SO)
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 5. Instalar dependência
pip install ply

# 6. Compilar um programa
python src/main.py tests/hello.f77 -o hello.vm

# 7. Ver o código gerado
type hello.vm
```

## Exemplos de Uso

### Exemplo 1: Olá Mundo

```bash
python src/main.py tests/hello.f77 -o hello.vm
```

**Código Fortran (tests/hello.f77):**
```fortran
PROGRAM HELLO
  PRINT *, 'Ola, Mundo!'
END
```

**Saída VM (hello.vm):**
```
START
PUSHS "Ola, Mundo!"
WRITES
WRITELN
STOP
```

### Exemplo 2: Ciclo DO (Fatorial)

```bash
python src/main.py tests/fatorial.f77 -o fatorial.vm
```

### Exemplo 3: Operações Lógicas e IF

```bash
python src/main.py tests/primo.f77 -o primo.vm
```

## Opções do Compilador

```bash
# Mostrar apenas tokens
python src/main.py tests/hello.f77 --tokens

# Mostrar AST (árvore sintática)
python src/main.py tests/hello.f77 --ast

# Compilar sem análise semântica (não recomendado)
python src/main.py tests/hello.f77 --no-semantic

# Especificar ficheiro de saída
python src/main.py tests/hello.f77 -o output.vm
```

## Testes

```bash
# Validar todos os programas
cd tests
python test_codegen.py

# Testar análise léxica
python test_lexer.py
```

## Estrutura

```
src/
  main.py         — Ponto de entrada
  lexer.py        — Análise léxica (tokens)
  parser.py       — Análise sintática (AST)
  semantic.py     — Semântica e símbolos
  codegen.py      — Geração de código VM

tests/
  *.f77           — Programas de teste
  *.vm            — Código gerado (referência)
  test_*.py       — Testes
```

## Features Suportadas

✅ Tipos: INTEGER, REAL, LOGICAL, CHARACTER
✅ Arrays com DIMENSION
✅ Funções e Subrotinas
✅ IF-THEN-ELSE, DO loops, GOTO
✅ READ/PRINT para I/O
✅ Expressões aritméticas e lógicas
✅ Operadores: +, -, *, /, **, .AND., .OR., .NOT.

## Próximos Passos

1. Compilar `tests/hello.f77` 
2. Ver output em `.vm`
3. Copiar código para https://ewvm.epl.di.uminho.pt/
4. Clicar "Run" para executar na VM
