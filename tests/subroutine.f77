C Testa definicao e chamada de SUBROUTINE
      PROGRAM TESTESUB
      INTEGER A, B
      A = 8
      B = 3
      CALL IMPRIME(A, B)
      END

      SUBROUTINE IMPRIME(X, Y)
      INTEGER X, Y, S, P
      S = X + Y
      P = X * Y
      PRINT *, 'Soma:    ', S
      PRINT *, 'Produto: ', P
      RETURN
      END
