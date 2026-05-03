# Guia de Uso do Compilador Fortran 77

## 1️⃣ Compilar um Programa

**Sintaxe:**
```bash
python src/main.py <ficheiro.f77> [-o <output.vm>]
```

**Exemplos:**

```bash
# Compilar hello.f77 e gerar hello.vm
python src/main.py tests/hello.f77 -o hello.vm

# Compilar sem especificar saída (usa nome do ficheiro)
python src/main.py tests/fatorial.f77
# Gera: tests/fatorial.vm

# Compilar com foco/debug
python src/main.py tests/primo.f77 --tokens   # Ver tokens
python src/main.py tests/primo.f77 --ast      # Ver AST
```

## 2️⃣ Programas de Teste Incluídos

| Programa | Descrição | Ficheiro |
|----------|-----------|----------|
| Hello World | PRINT básico | `tests/hello.f77` |
| Fatorial | Ciclo DO + INTEGER | `tests/fatorial.f77` |
| Primo | IF-THEN-ELSE + GOTO | `tests/primo.f77` |
| Soma de Array | Arrays + READ | `tests/somar.f77` |
| Conversor | FUNCTION + subprogramas | `tests/conversor.f77` |
| Aritmética | Operações REAL | `tests/aritmetica.f77` |
| Lógica | Operadores .AND., .OR., .NOT. | `tests/logica.f77` |
| Matriz | Arrays 2D + loops | `tests/matriz.f77` |
| Pares | DO com STEP | `tests/pares.f77` |
| Subrotina | SUBROUTINE + CALL | `tests/subroutine.f77` |
| Contagem | GOTO + labels | `tests/contagem.f77` |
| Classificar | IF aninhados | `tests/classificar.f77` |

## 3️⃣ Executar na VM EWVM

### Passo 1: Compilar
```bash
python src/main.py tests/hello.f77 -o hello.vm
```

### Passo 2: Copiar código
```bash
# Windows
type hello.vm | clip

# Linux/Mac
cat hello.vm | pbcopy
```

### Passo 3: Abrir https://ewvm.epl.di.uminho.pt/

### Passo 4: Colar código no editor

### Passo 5: Clicar "Run"

Resultado esperado:
```
Output: Ola, Mundo!
```

## 4️⃣ Validar Compilação

```bash
# Testar se todos os .f77 compilam
cd tests
python test_codegen.py
```

Resultado esperado:
```
VALIDACAO DO COMPILADOR FORTRAN 77 para VM
...
RESULTADOS: 10 OK | 2 FALHARAM | 0 AVISO
```

(2 falharam por redeclaração de parâmetros em funções — bug semântico conhecido)

## 5️⃣ Estrutura de um Programa Fortran 77

```fortran
PROGRAM MIPROGRAMA
  ! Declaracoes
  INTEGER N, I, SOMA
  REAL X, Y
  
  ! Instrucoes
  PRINT *, 'Digite um numero:'
  READ *, N
  
  ! Controlo
  IF (N .GT. 0) THEN
    SOMA = 0
    DO 10 I = 1, N
      SOMA = SOMA + I
10  CONTINUE
    PRINT *, 'Soma:', SOMA
  ENDIF
  
END PROGRAM MIPROGRAMA
```

## 6️⃣ Código VM Gerado para Hello

**Fortran:**
```fortran
PROGRAM HELLO
  PRINT *, 'Ola, Mundo!'
END
```

**VM:**
```asm
START
PUSHS "Ola, Mundo!"
WRITES
WRITELN
STOP
```

**Instrucoes:**
- `START` — Iniciar programa
- `PUSHS "..."` — Colocar string na pilha
- `WRITES` — Imprimir string
- `WRITELN` — Quebra de linha
- `STOP` — Terminar

## 7️⃣ Operadores e Expressoes

### Aritmeticos
```fortran
A + B           ! Adicao
A - B           ! Subtracao
A * B           ! Multiplicacao
A / B           ! Divisao
A ** B          ! Potencia
```

### Relacionais
```fortran
A .EQ. B        ! Igual
A .NE. B        ! Diferente
A .LT. B        ! Menor que
A .LE. B        ! Menor ou igual
A .GT. B        ! Maior que
A .GE. B        ! Maior ou igual
```

### Logicos
```fortran
A .AND. B       ! E logico
A .OR. B        ! OU logico
.NOT. A         ! NAO logico
```

## 8️⃣ Funcoes Intrinsecas

```fortran
MOD(A, B)       ! Resto da divisao
ABS(X)          ! Valor absoluto
INT(X)          ! Converter para inteiro
REAL(I)         ! Converter para real
SQRT(X)         ! Raiz quadrada
SIN(X)          ! Seno
COS(X)          ! Cosseno
MAX(A, B, ...)  ! Maximo
MIN(A, B, ...)  ! Minimo
LEN(STRING)     ! Comprimento
```

## 9️⃣ Solucao de Problemas

### Erro: `ModuleNotFoundError: No module named 'ply'`
```bash
pip install ply
```

### Erro: `Ficheiro nao encontrado`
```bash
# Usar caminhos relativos a partir da raiz do projeto
python src/main.py tests/hello.f77
```

### Compilacao com avisos
Normalmente sao apenas type mismatches — programa ainda compila.
Use `--no-semantic` para ignorar.

### Codigo VM nao executa na VM
1. Verificar syntax na VM (erro de aspas, etc.)
2. Testar programa simpler primeiro
3. Ver output do compilador para mensagem de erro

## 📝 Exemplos Completos

### Exemplo 1: Soma de Numeros
```fortran
PROGRAM SOMA
  INTEGER A, B, RESULTADO
  
  PRINT *, 'Digite primeiro numero:'
  READ *, A
  
  PRINT *, 'Digite segundo numero:'
  READ *, B
  
  RESULTADO = A + B
  PRINT *, 'Soma:', RESULTADO
  
END PROGRAM SOMA
```

### Exemplo 2: Tabuada
```fortran
PROGRAM TABUADA
  INTEGER I, N
  
  PRINT *, 'Tabuada de:'
  READ *, N
  
  DO 10 I = 1, 10
    PRINT *, N, ' x ', I, ' = ', N * I
10 CONTINUE
  
END PROGRAM TABUADA
```

### Exemplo 3: Verificar Paridade
```fortran
PROGRAM PARIDADE
  INTEGER N
  
  PRINT *, 'Digite um numero:'
  READ *, N
  
  IF (MOD(N, 2) .EQ. 0) THEN
    PRINT *, N, ' eh par'
  ELSE
    PRINT *, N, ' eh impar'
  ENDIF
  
END PROGRAM PARIDADE
```

---

**Dúvidas?** Ver README.md para mais info.
