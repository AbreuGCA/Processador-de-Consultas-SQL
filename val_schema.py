class ValidarSchema:
    def __init__(self, schema):
        self.schema = {k.lower():[c.lower() for c in v] for k, v in schema.items()}
    
    def validar(self, tabela, coluna):
        tabela = tabela.lower()
        coluna = coluna.lower()
        if tabela not in self.schema:
            raise ValueError(f"Tabela '{tabela}' não está definida no schema.")
        if coluna not in self.schema[tabela]:
            raise ValueError(f"Coluna '{coluna}' não está definida na tabela '{tabela}' do schema.")
        return True