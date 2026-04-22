import re

# Operadores de comparação permitidos pelo enunciado do projeto
OPERADORES_PERMITIDOS = {'=', '>', '<', '<=', '>=', '<>'}


def parse_sql(query: str) -> dict:
    pattern = re.compile(
        r"SELECT\s+(?P<select>.*?)\s+"
        r"FROM\s+(?P<from>\w+)"
        r"(?:\s+INNER\s+JOIN\s+(?P<join_table>\w+)\s+ON\s+(?P<join_cond>.*?))?"
        r"(?:\s+WHERE\s+(?P<where>.*?))?\s*$",
        re.IGNORECASE | re.DOTALL
    )

    match = pattern.match(query.strip())
    if not match:
        raise ValueError(
            "Formato SQL inválido.\n"
            "Sintaxe esperada:\n"
            "  SELECT colunas FROM tabela\n"
            "  [INNER JOIN tabela2 ON condição]\n"
            "  [WHERE condição]"
        )

    result = match.groupdict()

    # Valida operadores na cláusula ON (JOIN)
    if result.get('join_cond'):
        _validar_operadores(result['join_cond'], clausula="ON")

    # Valida operadores na cláusula WHERE
    if result.get('where'):
        _validar_operadores(result['where'], clausula="WHERE")

    return result

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
    match = re.match(r'\s*([\w.]+)\s*(?:<=|>=|<>|<|>|=)', condicao)
    return match.group(1).strip() if match else None
