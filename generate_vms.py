#!/usr/bin/env python
"""
Gerar ficheiros .vm de referência para todos os testes
"""

import os
import subprocess
import sys

test_files = [
    'hello.f77',
    'fatorial.f77',
    'primo.f77',
    'somar.f77',
    'aritmetica.f77',
    'classificar.f77',
    'pares.f77',
    'logica.f77',
    'matriz.f77',
    'contagem.f77',
    'conversor.f77',
    'subroutine.f77',
]

os.chdir('tests')

print("Gerando ficheiros .vm de referência...")
print("=" * 60)

for test_file in test_files:
    output_file = test_file.replace('.f77', '.vm')
    cmd = [sys.executable, '../src/main.py', test_file, '-o', output_file]
    
    print(f"\nCompilando {test_file}...", end=' ')
    sys.stdout.flush()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ OK")
    else:
        print(f"✗ ERRO")
        print(result.stderr)

print("\n" + "=" * 60)
print("Ficheiros .vm gerados em tests/")
