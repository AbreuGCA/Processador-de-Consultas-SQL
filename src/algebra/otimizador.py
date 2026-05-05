from src.algebra.algebra_relacional import ScanNode, SelectionNode, ProjectionNode, JoinNode
from src.parser.parse import extrair_condicoes, extrair_coluna_de_condicao
import re

class Optimizer:
    def __init__(self, parsed_query: dict):
        self.query = parsed_query

    def _get_required_columns_per_table(self):
        """Identifica todas as colunas necessárias de cada tabela para a consulta."""
        needed = {}
        tabela_from = self.query['from'].lower()
        
        # 1. Colunas do SELECT
        if self.query['select'].strip() != '*':
            cols_select = [c.strip() for c in self.query['select'].split(',')]
            for col in cols_select:
                self._add_to_needed(col, needed, tabela_from)

        # 2. Colunas do WHERE
        conds_where = extrair_condicoes(self.query.get('where', ''))
        for cond in conds_where:
            col = extrair_coluna_de_condicao(cond)
            if col: self._add_to_needed(col, needed, tabela_from)

        # 3. Colunas do JOIN (condições ON)
        for join in self.query.get('joins', []):
            # Extrai colunas de ambos os lados da condição de join (ex: t1.id = t2.id_ext)
            cond_join = join['cond']
            parts = re.split(r'<=|>=|<>|<|>|=', cond_join)
            for p in parts:
                potential_col = p.strip()
                if not (potential_col.startswith("'") or potential_col.isdigit()):
                    self._add_to_needed(potential_col, needed, tabela_from)
        
        return needed

    def _add_to_needed(self, col, needed, default_tab):
        """Auxiliar para mapear coluna à sua respectiva tabela."""
        if '.' in col:
            tab, c = col.split('.', 1)
            tab = tab.lower()
        else:
            tab = default_tab
        if tab not in needed: needed[tab] = set()
        needed[tab].add(c.lower())

    def build_optimized_tree(self):
        # Mapeia colunas necessárias por tabela (Heurística de Redução de Atributos antecipada)
        colunas_por_tabela = self._get_required_columns_per_table()
        
        # Agrupa condições do WHERE por tabela (Redução de Tuplas)
        condicoes_por_tabela = {}
        todas_condicoes = extrair_condicoes(self.query.get('where', ''))
        tabela_from = self.query['from'].lower()
        
        for cond in todas_condicoes:
            coluna = extrair_coluna_de_condicao(cond)
            if not coluna: continue
            tab_alvo = coluna.split('.')[0].lower() if '.' in coluna else tabela_from
            if tab_alvo not in condicoes_por_tabela: condicoes_por_tabela[tab_alvo] = []
            condicoes_por_tabela[tab_alvo].append(cond)

        # Função para criar o ramo de uma tabela com push-down de Seleção e Projeção
        def criar_ramo_tabela(nome_tabela):
            nome_tabela_lower = nome_tabela.lower()
            node = ScanNode(nome_tabela)
            
            # Heurística 1: Redução de Tuplas (Seleção antecipada)
            if nome_tabela_lower in condicoes_por_tabela:
                cond = " AND ".join(condicoes_por_tabela[nome_tabela_lower])
                node = SelectionNode(condition=cond, child=node)
            
            # Heurística 2: Redução de Atributos (Projeção antecipada em TODO Scan)
            if nome_tabela_lower in colunas_por_tabela:
                node = ProjectionNode(columns=list(colunas_por_tabela[nome_tabela_lower]), child=node)
            
            return node

        # Montagem da Árvore
        root = criar_ramo_tabela(self.query['from'])

        for join in self.query.get('joins', []):
            right_branch = criar_ramo_tabela(join['table'])
            root = JoinNode(condition=join['cond'], left_child=root, right_child=right_branch)

        # Projeção Final (apenas se não for SELECT *)
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