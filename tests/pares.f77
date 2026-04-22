C Testa ciclo DO com passo (step) diferente de 1
      PROGRAM PARES
      INTEGER I
      PRINT *, 'Numeros pares de 2 a 20:'
      DO 10 I = 2, 20, 2
          PRINT *, I
10    CONTINUE
      PRINT *, 'Contagem decrescente de 10 a 1:'
      DO 20 I = 10, 1, -1
          PRINT *, I
20    CONTINUE
      END
