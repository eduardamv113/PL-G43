C Testa operadores logicos .AND. .OR. .NOT. e variaveis LOGICAL
      PROGRAM LOGICA
      LOGICAL A, B, C
      A = .TRUE.
      B = .FALSE.
      C = A .AND. B
      PRINT *, 'TRUE AND FALSE = ', C
      C = A .OR. B
      PRINT *, 'TRUE OR  FALSE = ', C
      C = .NOT. A
      PRINT *, 'NOT TRUE       = ', C
      C = .NOT. B
      PRINT *, 'NOT FALSE      = ', C
      END
