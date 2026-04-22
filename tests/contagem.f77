C Testa GOTO e labels - simula um loop while
      PROGRAM CONTAGEM
      INTEGER N, SOMA
      SOMA = 0
      N = 1
10    IF (N .LE. 100) THEN
          SOMA = SOMA + N
          N = N + 1
          GOTO 10
      ENDIF
      PRINT *, 'Soma de 1 a 100: ', SOMA
      END
