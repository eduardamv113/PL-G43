"""
optimizer.py - Otimizações de Código VM

Implementa otimizações básicas:
1. Constant folding - Avaliar constantes em compile-time
2. Dead code elimination - Remover código não executável
3. Unused label removal - Remover labels sem referências
"""

import re


class VMOptimizer:
    """Otimizador para código VM."""
    
    def __init__(self, code_lines):
        """
        Inicializa o otimizador.
        code_lines: lista de strings (instruções VM)
        """
        self.code_lines = code_lines[:]
        self.optimizations_applied = []
    
    def optimize(self):
        """Aplica todas as otimizações."""
        self.dead_code_elimination()
        # self.unused_label_removal()  # Desativado: pode remover labels válidos
        self.redundant_push_elimination()
        return self.code_lines
    
    def dead_code_elimination(self):
        """Remove código não executável após RETURN, GOTO, JMPZ, etc."""
        optimized = []
        i = 0
        while i < len(self.code_lines):
            line = self.code_lines[i].strip()
            optimized.append(self.code_lines[i])
            
            # Se encontrou jump incondicional, pula tudo até próximo label
            if line.startswith(('RETURN', 'STOP')) or \
               (line.startswith('JMP ') and not line.startswith('JMPZ')):
                # Procura próximo label
                i += 1
                while i < len(self.code_lines):
                    next_line = self.code_lines[i].strip()
                    if next_line.endswith(':'):  # é um label
                        # Não avança, para adicionar o label
                        break
                    self.optimizations_applied.append(
                        f"Removido código inacessível: {next_line}"
                    )
                    i += 1
                continue
            
            i += 1
        
        if len(optimized) < len(self.code_lines):
            self.code_lines = optimized
    
    def unused_label_removal(self):
        """Remove labels que não são referenciados."""
        # Recolher todos os labels usados (destinos de jumps)
        used_labels = set()
        for line in self.code_lines:
            line = line.strip()
            # Procura por: JMP label, JMPZ label, etc.
            match = re.search(r'(JMP|JMPZ|CALL)\s+(\w+)', line)
            if match:
                used_labels.add(match.group(2))
        
        # Recolher todos os labels definidos
        defined_labels = set()
        label_indices = {}
        for i, line in enumerate(self.code_lines):
            line = self.code_lines[i].strip()
            if line.endswith(':'):
                label = line[:-1]
                defined_labels.add(label)
                label_indices[label] = i
        
        # Remover labels não usados
        unused = defined_labels - used_labels
        optimized = []
        for i, line in enumerate(self.code_lines):
            stripped = line.strip()
            if stripped.endswith(':'):
                label = stripped[:-1]
                if label in unused:
                    self.optimizations_applied.append(
                        f"Removido label não usado: {label}"
                    )
                    continue
            optimized.append(line)
        
        self.code_lines = optimized
    
    def redundant_push_elimination(self):
        """Remove PUSHes redundantes (ex: PUSH X seguido de POP)."""
        optimized = []
        i = 0
        while i < len(self.code_lines):
            line = self.code_lines[i].strip()
            
            # Procura sequência: PUSH* seguida de POP
            if i + 1 < len(self.code_lines):
                next_line = self.code_lines[i + 1].strip()
                if (line.startswith(('PUSHG', 'PUSHL', 'PUSHS', 'PUSHI', 'PUSHF')) and
                    next_line == 'POP'):
                    self.optimizations_applied.append(
                        f"Removido PUSH/POP redundante: {line}"
                    )
                    i += 2
                    continue
            
            optimized.append(self.code_lines[i])
            i += 1
        
        if len(optimized) < len(self.code_lines):
            self.code_lines = optimized
    
    def get_optimizations_report(self):
        """Retorna relatório das otimizações aplicadas."""
        if not self.optimizations_applied:
            return "Nenhuma otimização aplicada."
        
        report = f"{len(self.optimizations_applied)} otimizações aplicadas:\n"
        for opt in self.optimizations_applied[:5]:  # Max 5 primeiras
            report += f"  - {opt}\n"
        if len(self.optimizations_applied) > 5:
            report += f"  ... e {len(self.optimizations_applied) - 5} mais\n"
        return report


# ============================================================================
# Constant Folding para AST
# ============================================================================

def fold_constants(node):
    """
    Fold constantes em expressões durante parsing/semantic.
    
    Exemplos:
    - 2 + 3 → 5
    - 10 / 2 → 5
    - 1 .LT. 2 → .TRUE.
    """
    if node is None:
        return node
    
    # Expressão binária
    if isinstance(node, tuple) and len(node) == 3:
        op, left, right = node
        
        # Recursivamente fold subexpressões
        left = fold_constants(left)
        right = fold_constants(right)
        
        # Se ambos são constantes, evaluar
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            try:
                if op == '+':
                    return left + right
                elif op == '-':
                    return left - right
                elif op == '*':
                    return left * right
                elif op == '/':
                    if right != 0:
                        return left / right
                elif op == '**':
                    return left ** right
                elif op == 'MOD':
                    return left % right
                elif op == '.LT.':
                    return 1 if left < right else 0
                elif op == '.LE.':
                    return 1 if left <= right else 0
                elif op == '.GT.':
                    return 1 if left > right else 0
                elif op == '.GE.':
                    return 1 if left >= right else 0
                elif op == '.EQ.':
                    return 1 if left == right else 0
                elif op == '.NE.':
                    return 1 if left != right else 0
            except:
                pass
        
        return (op, left, right)
    
    # Expressão unária
    elif isinstance(node, tuple) and len(node) == 2:
        op, operand = node
        operand = fold_constants(operand)
        
        if isinstance(operand, (int, float)):
            try:
                if op == '-':  # negação
                    return -operand
                elif op == '.NOT.':
                    return 0 if operand else 1
            except:
                pass
        
        return (op, operand)
    
    # Recursão em listas
    elif isinstance(node, list):
        return [fold_constants(item) for item in node]
    
    # Outros tipos: retornar como estão
    return node
