class QueryGraph:
    def __init__(self, root_node):
        self.root = root_node
        self.execution_steps = []
        
    def generate_execution_steps(self, node=None):
        if node is None:
            node = self.root
            self.execution_steps = []
        
        if hasattr(node, 'child') and node.child is not None:
            self.generate_execution_steps(node.child)
        elif hasattr(node, 'left_child') and node.left_child is not None:
            self.generate_execution_steps(node.left_child)
            self.generate_execution_steps(node.right_child)
        
        step = len(self.execution_steps) + 1
        
        if node.name == "Scan":
            desc = f"Passo {step}: Scan table: '{node.table_name}'"
        elif node.name == "Selection":
            desc = f"Passo {step}: Aplicar filtro (σ) com a condição: '{node.condition}'"
        elif node.name == "Projection":
            desc = f"Passo {step}: Projetar colunas (π): {', '.join(node.columns)}"
        elif node.name == "Join":
            desc = f"Passo {step}: Realizar junção (⨝) entre '{node.left_child.name}' e '{node.right_child.name}' com a condição: '{node.condition}'"
            
        self.execution_steps.append(desc)
        return self.execution_steps
            