from src.algebra.algebra_relacional import ScanNode, SelectionNode, ProjectionNode, JoinNode

class Optimizer:
    def __init__(self, parsed_query):
        self.query = parsed_query

    def build_optimized_tree(self):
        # 1. Base: Scan da tabela principal
        root = ScanNode(self.query['from'])
        
        # 2. Heurística: Integração de Junção (União de ramos)
        if self.query.get('join_table'):
            right_branch = ScanNode(self.query['join_table'])
            # Cria o nó de Join unindo a tabela principal e a tabela do Join
            root = JoinNode(self.query['join_cond'], root, right_branch)
        
        # 3. Heurística: Redução de Tuplas (Seleção logo após a origem/junção)
        if self.query.get('where'):
            root = SelectionNode(self.query['where'], root)
        
        # 4. Heurística: Redução de Atributos (Projeção final)
        if self.query.get('select'):
            if self.query['select'].strip() != '*':
                columns = [c.strip() for c in self.query['select'].split(',')]
                root = ProjectionNode(columns, root)
            
        return root