import re

def parse_sql(query):
    # 1. Limpeza inicial: remove espaços inúteis e pontos e vírgulas
    query = query.strip().replace(';', '')
    
    # 2. Regex melhorada:
    # - \s+ aceita um ou mais espaços/tabs/quebras de linha
    # - [\s\S]*? aceita qualquer caractere (incluindo quebras de linha) de forma não-gulosa
    pattern = re.compile(
        r"SELECT\s+(?P<select>[\s\S]*?)\s+"
        r"FROM\s+(?P<from>\w+)"
        r"(?:\s+INNER\s+JOIN\s+(?P<join_table>\w+)\s+ON\s+(?P<join_cond>[\s\S]*?))?"
        r"(?:\s+WHERE\s+(?P<where>[\s\S]*?))?\s*$",
        re.IGNORECASE
    )
    
    match = pattern.match(query)
    
    if not match:
        raise ValueError(
            "Formato SQL não reconhecido. Certifique-se de usar: "
            "SELECT ... FROM ... [INNER JOIN ... ON ...] [WHERE ...]"
        )
    
    # Extrai os grupos e limpa espaços internos
    result = {k: (v.strip() if v else None) for k, v in match.groupdict().items()}
    
    return result