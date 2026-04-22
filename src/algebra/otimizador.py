from src.algebra.algebra_relacional import ScanNode, SelectionNode, ProjectionNode, JoinNode


class Optimizer:

    def __init__(self, parsed_query: dict):
        self.query = parsed_query

    def build_optimized_tree(self):
        # ── Base: Scan da tabela principal (nó folha esquerdo) ────────
        root = ScanNode(self.query['from'])

        # ── H1: Seleção logo após a origem (antes da projeção) ────────
        # Push-down da seleção → reduz tuplas o mais cedo possível
        if self.query.get('where'):
            root = SelectionNode(
                condition=self.query['where'],
                child=root
            )

        # ── H2: Projeção no topo (após filtrar tuplas) ─────────────────
        # Push-down da projeção → elimina atributos desnecessários no final
        if self.query.get('select'):
            if self.query['select'].strip() != '*':
                columns = [c.strip() for c in self.query['select'].split(',')]
                root = ProjectionNode(columns=columns, child=root)

        # ── H3: INNER JOIN → evita Produto Cartesiano ─────────────────
        # Se houver JOIN, cria um nó de junção com a tabela principal à esquerda
        if self.query.get('join_table'):
            right_branch = ScanNode(self.query['join_table'])
            root = JoinNode(
                condition=self.query['join_cond'],
                left_child=root,
                right_child=right_branch
            )

        return root

