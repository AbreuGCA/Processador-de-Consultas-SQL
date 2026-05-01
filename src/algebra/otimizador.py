from src.algebra.algebra_relacional import ScanNode, SelectionNode, ProjectionNode, JoinNode
from src.parser.parse import extrair_condicoes, extrair_coluna_de_condicao

class Optimizer:

    def __init__(self, parsed_query: dict):
        self.query = parsed_query

    def build_optimized_tree(self):        
        # 1. Separar e agrupar as condições do WHERE por tabela
        condicoes_por_tabela = {}
        todas_condicoes = extrair_condicoes(self.query.get('where', ''))
        tabela_from = self.query['from'].lower()
        
        for cond in todas_condicoes:
            coluna = extrair_coluna_de_condicao(cond)
            if not coluna: 
                continue
            
            # Se a coluna for qualificada (tabela.coluna), pegamos o nome da tabela
            if '.' in coluna:
                tabela_alvo = coluna.split('.')[0].lower()
            else:
                # Se não for qualificada, assumimos que pertence à tabela FROM (tabela principal)
                tabela_alvo = tabela_from 
                
            if tabela_alvo not in condicoes_por_tabela:
                condicoes_por_tabela[tabela_alvo] = []
            condicoes_por_tabela[tabela_alvo].append(cond)

        # 2. Criar ScanNode da tabela principal e aplicar a seleção DELA logo em seguida
        root = ScanNode(self.query['from'])
        if tabela_from in condicoes_por_tabela:
            cond_from = " AND ".join(condicoes_por_tabela[tabela_from])
            root = SelectionNode(condition=cond_from, child=root)

        # 3. Aplicar JOINs com as tabelas da direita (também aplicando seleções antes de juntar)
        for join in self.query.get('joins', []):
            tabela_join = join['table']
            right_branch = ScanNode(tabela_join)
            tabela_join_lower = tabela_join.lower()
            
            # Se houver um WHERE filtrando dados dessa tabela do JOIN, aplica o filtro NELA primeiro
            if tabela_join_lower in condicoes_por_tabela:
                cond_join = " AND ".join(condicoes_por_tabela[tabela_join_lower])
                right_branch = SelectionNode(condition=cond_join, child=right_branch)

            root = JoinNode(
                condition=join['cond'],
                left_child=root,
                right_child=right_branch
            )

        # 4. Projeção (permanece no topo, após os dados já estarem reduzidos)
        if self.query.get('select'):
            if self.query['select'].strip() != '*':
                columns = [c.strip() for c in self.query['select'].split(',')]
                root = ProjectionNode(columns=columns, child=root)

        return root

    def build_unoptimized_tree(self):
        root = ScanNode(self.query['from'])

        for join in self.query.get('joins', []):
            right_branch = ScanNode(join['table'])
            root = JoinNode(
                condition=join['cond'],
                left_child=root,
                right_child=right_branch
            )

        if self.query.get('where'):
            root = SelectionNode(
                condition=self.query['where'],
                child=root
            )

        if self.query.get('select') and self.query['select'].strip() != '*':
            columns = [c.strip() for c in self.query['select'].split(',')]
            root = ProjectionNode(columns=columns, child=root)

        return root