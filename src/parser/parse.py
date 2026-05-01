import re

# Operadores de comparação permitidos pelo enunciado do projeto
OPERADORES_PERMITIDOS = {'=', '>', '<', '<=', '>=', '<>'}


def parse_sql(query: str) -> dict:
    # para garantir que ele pare apenas na palavra WHERE inteira.
    pattern = re.compile(
        r"SELECT\s+(?P<select>.*?)\s+FROM\s+(?P<from>\w+)(?P<joins>(?:\s+INNER\s+JOIN\s+\w+\s+ON\s+(?:(?!\bWHERE\b).)*?)*)\s*(?:WHERE\s+(?P<where>.*?))?\s*$",
        re.IGNORECASE | re.DOTALL
    )

    match = pattern.match(query.strip())
    if not match:
        raise ValueError(
            "Formato SQL inválido.\n"
            "Sintaxe esperada:\n"
            "  SELECT colunas FROM tabela\n"
            "  [INNER JOIN tabela2 ON condição] ...\n"
            "  [WHERE condição]"
        )

    result = match.groupdict()

    joins = []
    joins_str = result.get('joins') or ''
    # Ajustando o sub-regex do JOIN também para não usar [^I]+? (que quebra com a letra 'I')
    join_pattern = re.compile(r"INNER\s+JOIN\s+(\w+)\s+ON\s+((?:(?!\bINNER\s+JOIN\b).)+)", re.IGNORECASE | re.DOTALL)
    for m in join_pattern.finditer(joins_str):
        join_table = m.group(1)
        join_cond = m.group(2).strip()
        joins.append({'table': join_table, 'cond': join_cond})
        _validar_operadores(join_cond, clausula="ON")

    if result.get('where'):
        _validar_operadores(result['where'], clausula="WHERE")

    return {
        'select': result['select'],
        'from': result['from'],
        'joins': joins,
        'where': result.get('where')
    }

# Valida operadores em uma condição composta, rejeitando palavras-chave e operadores não permitidos
def _validar_operadores(condicao: str, clausula: str):
    # Rejeita palavras-chave não suportadas
    palavras_proibidas = re.findall(r'\b(OR|NOT|LIKE|IN|BETWEEN|IS)\b', condicao, re.IGNORECASE)
    if palavras_proibidas:
        raise ValueError(
            f"[{clausula}] Palavra-chave '{palavras_proibidas[0].upper()}' não é suportada.\n"
            f"Conectivos permitidos: AND. Operadores: {', '.join(sorted(OPERADORES_PERMITIDOS))}"
        )

    # Remove parênteses e divide por AND para analisar sub-condições
    condicao_limpa = condicao.replace('(', ' ').replace(')', ' ')
    sub_condicoes = re.split(r'\bAND\b', condicao_limpa, flags=re.IGNORECASE)

    for sub in sub_condicoes:
        sub = sub.strip()
        if not sub:
            continue

        # Detecta uso de '!=' (operador proibido — o correto é '<>')
        if '!=' in sub:
            raise ValueError(
                f"[{clausula}] Operador '!=' não é permitido. Use '<>' para 'diferente de'."
            )

        # Verifica que a sub-condição contém exatamente um operador válido
        op_match = re.search(r'(<=|>=|<>|<|>|=)', sub)
        if not op_match:
            raise ValueError(
                f"[{clausula}] A condição '{sub.strip()}' não contém um operador de comparação válido.\n"
                f"Operadores permitidos: {', '.join(sorted(OPERADORES_PERMITIDOS))}"
            )

# Extrai as condições individuais de uma cláusula WHERE composta por AND
def extrair_condicoes(where_str: str) -> list:
    if not where_str:
        return []
    limpo = where_str.replace('(', ' ').replace(')', ' ')
    partes = re.split(r'\bAND\b', limpo, flags=re.IGNORECASE)
    return [p.strip() for p in partes if p.strip()]

# Extrai a coluna de uma condição simples
def extrair_coluna_de_condicao(condicao: str):
    partes = re.split(r'<=|>=|<>|<|>|=', condicao)
    
    if len(partes) != 2:
        return None
        
    esq = partes[0].strip()
    dir = partes[1].strip()
    
    if esq.startswith("'") or esq.startswith('"') or esq.replace('.', '', 1).isdigit():
        return dir
        
    # Caso contrário, assumimos que a coluna está à esquerda (Ex: Preco > 100).
    return esq
