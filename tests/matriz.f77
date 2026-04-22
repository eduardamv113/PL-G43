C Testa array 2D e ciclos DO aninhados
      PROGRAM MATRIZ
      INTEGER MAT(3, 3)
      INTEGER I, J, VAL
      VAL = 1
      DO 10 I = 1, 3
          DO 20 J = 1, 3
              MAT(I) = VAL
              VAL = VAL + 1
20        CONTINUE
10    CONTINUE
      PRINT *, 'Valores da matriz (linha a linha):'
      DO 30 I = 1, 9
          PRINT *, MAT(I)
30    CONTINUE
      END
