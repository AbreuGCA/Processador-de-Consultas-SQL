from src.algebra.algebra_relacional import ScanNode, SelectionNode, ProjectionNode, JoinNode
from src.data.dic_dados import SCHEMA_VENDAS

class Optimizer:
    def __init__(self, parsed_query):
        self.query = parsed_query

    def identificar_tabela_da_condicao(self, condicao):
        """
        Heurística: Identifica qual tabela possui a coluna mencionada no WHERE.
        """
        if not condicao:
            return None
        
        condicao_lower = condicao.lower()
    # Use "or ''" para garantir que, se for None, vire uma string vazia
        tabela_principal = (self.query.get('from') or "").lower()
        tabela_join = (self.query.get('join_table') or "").lower()
        
        # Verifica se a condição explicitamente cita a tabela (ex: produto.Preco)
        if tabela_join and f"{tabela_join}." in condicao_lower:
            return "join"
        if f"{tabela_principal}." in condicao_lower:
            return "principal"

        # Se não cita explicitamente, busca a coluna no dicionário de dados
        for tabela, colunas in SCHEMA_VENDAS.items():
            for col in colunas:
                if col.lower() in condicao_lower:
                    if tabela.lower() == tabela_principal:
                        return "principal"
                    if tabela.lower() == tabela_join:
                        return "join"
        return "principal" # Default

    def build_optimized_tree(self):
        # 1. Criação dos ramos folha (Scans)
        nome_tabela_principal = self.query.get('from') or ""
        left_branch = ScanNode(nome_tabela_principal)
    
        right_branch = None
        if self.query.get('join_table'):
            right_branch = ScanNode(self.query['join_table'])

        # 2. HEURÍSTICA: Push-down de Seleção (Redução de Tuplas)
        # Aplicamos o filtro ANTES do Join se possível
        where_cond = self.query.get('where')
        tabela_alvo = self.identificar_tabela_da_condicao(where_cond)

        if where_cond:
            if tabela_alvo == "join" and right_branch:
                right_branch = SelectionNode(where_cond, right_branch)
                where_cond = None # Filtro já aplicado
            elif tabela_alvo == "principal":
                left_branch = SelectionNode(where_cond, left_branch)
                where_cond = None # Filtro já aplicado

        # 3. Integração (Join)
        if right_branch:
            root = JoinNode(self.query['join_cond'], left_branch, right_branch)
        else:
            root = left_branch

        # Se o WHERE envolver ambas as tabelas (e não foi aplicado antes), aplica agora
        if where_cond:
            root = SelectionNode(where_cond, root)

        # 4. HEURÍSTICA: Redução de Atributos (Projeção)
        if self.query.get('select') and self.query['select'].strip() != '*':
            columns = [c.strip() for c in self.query['select'].split(',')]
            root = ProjectionNode(columns, root)
            
        return root