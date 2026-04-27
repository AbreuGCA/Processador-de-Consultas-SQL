from src.algebra.algebra_relacional import ScanNode, SelectionNode, ProjectionNode, JoinNode

class Optimizer:

    def __init__(self, parsed_query: dict):
        self.query = parsed_query

    def build_optimized_tree(self):
        # [Seu código existente permanece inalterado aqui]
        root = ScanNode(self.query['from'])

        if self.query.get('where'):
            root = SelectionNode(condition=self.query['where'], child=root)

        if self.query.get('select'):
            if self.query['select'].strip() != '*':
                columns = [c.strip() for c in self.query['select'].split(',')]
                root = ProjectionNode(columns=columns, child=root)

        if self.query.get('join_table'):
            right_branch = ScanNode(self.query['join_table'])
            root = JoinNode(
                condition=self.query['join_cond'],
                left_child=root,
                right_child=right_branch
            )

        return root

    # ── NOVO MÉTODO ──────────────────────────────────────────────────────────
    def build_unoptimized_tree(self):
        """
        Constrói a árvore canônica (não otimizada) seguindo a ordem lógica:
        1. Produto Cartesiano/Junção (FROM e JOIN)
        2. Seleção (WHERE)
        3. Projeção (SELECT)
        """
        # 1. Base: Lemos a tabela primária
        root = ScanNode(self.query['from'])

        # 2. Junção com a segunda tabela, se existir
        if self.query.get('join_table'):
            right_branch = ScanNode(self.query['join_table'])
            root = JoinNode(
                condition=self.query['join_cond'],
                left_child=root,
                right_child=right_branch
            )

        # 3. Aplica o filtro de linhas (Seleção) após ter todas as tabelas juntas
        if self.query.get('where'):
            root = SelectionNode(
                condition=self.query['where'],
                child=root
            )

        # 4. Aplica o filtro de colunas (Projeção) no topo de tudo
        if self.query.get('select') and self.query['select'].strip() != '*':
            columns = [c.strip() for c in self.query['select'].split(',')]
            root = ProjectionNode(columns=columns, child=root)

        return root