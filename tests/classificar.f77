C Testa IF-THEN-ELSE aninhados e operadores relacionais
      PROGRAM CLASSIFICAR
      INTEGER NOTA
      PRINT *, 'Introduza uma nota (0-20):'
      READ *, NOTA
      IF (NOTA .GE. 18) THEN
          PRINT *, 'Muito Bom'
      ELSE
          IF (NOTA .GE. 14) THEN
              PRINT *, 'Bom'
          ELSE
              IF (NOTA .GE. 10) THEN
                  PRINT *, 'Suficiente'
              ELSE
                  PRINT *, 'Reprovado'
              ENDIF
          ENDIF
      ENDIF
      END
