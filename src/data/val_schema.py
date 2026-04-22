class ValidarSchema:

    # Normaliza tudo para minúsculas para facilitar comparações
    def __init__(self, schema: dict):
        self.schema = {
            k.lower(): [c.lower() for c in v]
            for k, v in schema.items()
        }

    # ------------------------------------------------------------------ #
    #  Validações Primitivas                                               #
    # ------------------------------------------------------------------ #

    # Valida se a tabela existe no schema
    def validar_tabela(self, tabela: str) -> bool:
        if tabela.lower() not in self.schema:
            tabelas_disponiveis = ', '.join(sorted(self.schema.keys()))
            raise ValueError(
                f"Tabela '{tabela}' não existe no banco de dados.\n"
                f"Tabelas disponíveis: {tabelas_disponiveis}"
            )
        return True

    # Valida se a coluna existe na tabela especificada
    def validar(self, tabela: str, coluna: str) -> bool:
        t, c = tabela.lower(), coluna.lower()
        self.validar_tabela(t)
        if c not in self.schema[t]:
            colunas_disponiveis = ', '.join(self.schema[t])
            raise ValueError(
                f"Coluna '{coluna}' não existe na tabela '{tabela}'.\n"
                f"Colunas disponíveis em '{tabela}': {colunas_disponiveis}"
            )
        return True

    # ------------------------------------------------------------------ #
    #  Validação do SELECT                                                 #
    # ------------------------------------------------------------------ #

    # Valida as colunas do SELECT, considerando '*' e colunas qualificadas
    def validar_colunas_select(self, select_str: str, tabelas: list) -> bool:
        if select_str.strip() == '*':
            return True

        tabelas_lower = [t.lower() for t in tabelas]
        colunas = [c.strip() for c in select_str.split(',')]

        for col in colunas:
            if col:
                self._resolver_coluna(col.strip(), tabelas_lower, contexto="SELECT")

        return True

    # ------------------------------------------------------------------ #
    #  Validação de WHERE e JOIN ON                                        #
    # ------------------------------------------------------------------ #

    # Valida as colunas usadas em condições, considerando colunas qualificadas
    def validar_coluna_condicao(self, coluna_str: str, tabelas: list, contexto: str = "WHERE") -> bool:
        tabelas_lower = [t.lower() for t in tabelas]
        self._resolver_coluna(coluna_str.strip(), tabelas_lower, contexto=contexto)
        return True

    # ------------------------------------------------------------------ #
    #  Núcleo de Resolução (uso interno)                                   #
    # ------------------------------------------------------------------ #

    # Resolve uma coluna, verificando se ela existe no contexto das tabelas envolvidas
    def _resolver_coluna(self, col: str, tabelas_lower: list, contexto: str):
        col_lower = col.lower()

        if '.' in col_lower:
            partes = col_lower.split('.', 1)
            tab, nome_col = partes[0].strip(), partes[1].strip()

            if tab not in self.schema:
                raise ValueError(
                    f"[{contexto}] Tabela '{tab}' referenciada em '{col}' não existe no schema."
                )
            if nome_col not in self.schema[tab]:
                colunas_disponiveis = ', '.join(self.schema[tab])
                raise ValueError(
                    f"[{contexto}] Coluna '{nome_col}' não existe na tabela '{tab}'.\n"
                    f"Colunas disponíveis em '{tab}': {colunas_disponiveis}"
                )
        else:
            encontrada = any(
                col_lower in self.schema.get(t, [])
                for t in tabelas_lower
            )
            if not encontrada:
                tabelas_str = ', '.join(tabelas_lower)
                raise ValueError(
                    f"[{contexto}] Coluna '{col}' não foi encontrada em nenhuma "
                    f"das tabelas envolvidas: {tabelas_str}."
                )
