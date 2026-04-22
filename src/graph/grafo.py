class QueryGraph:

    def __init__(self, root_node):
        self.root = root_node
        self.execution_steps = []

    # Pecorre a árvore de operadores para gerar uma descrição passo a passo da execução otimizada
    def generate_execution_steps(self, node=None):
        if node is None:
            node = self.root
            self.execution_steps = []

        # ── Recursão em Pós-Ordem ───────────────────────────────────────
        if node.name == "Join":
            if node.left_child:
                self.generate_execution_steps(node.left_child)
            if node.right_child:
                self.generate_execution_steps(node.right_child)
        elif hasattr(node, 'child') and node.child is not None:
            self.generate_execution_steps(node.child)

        # ── Geração da Descrição do Passo ──────────────────────────────
        if node.name == "Scan":
            table = getattr(node, 'table_name', None)
            if not table:
                table = getattr(node, 'name', 'TABELA_DESCONHECIDA')
            desc = f"SCAN — Leitura completa da tabela '{table}'"

        elif node.name == "Selection":
            desc = (
                f"\n SELEÇÃO (σ) — Aplicar filtro: '{node.condition}' \n"
                f"\n Heurística: Redução de Tuplas (push-down antes da projeção)"
            )

        elif node.name == "Projection":
            cols = ', '.join(node.columns)
            desc = (
                f"\n PROJEÇÃO (π) — Manter apenas as colunas: {cols} \n"
                f"\n Heurística: Redução de Atributos (elimina colunas desnecessárias)"
            )

        elif node.name == "Join":
            left_name = getattr(node.left_child, 'table_name', node.left_child.name)
            right_name = getattr(node.right_child, 'table_name', node.right_child.name)
            desc = (
                f"\n JUNÇÃO (⨝) — '{left_name}' ⨝ '{right_name}' \n"
                f"\n Condição: '{node.condition}' \n"
                f"\n Heurística: Junção preferida ao Produto Cartesiano"
            )

        else:
            desc = node.name

        self.execution_steps.append(desc)
        return self.execution_steps