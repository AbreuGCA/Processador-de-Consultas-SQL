import re

def parse_sql (query):
    
    pattern = re.compile(
        r"SELECT\s+(?P<select>.*?)\s+"
        r"FROM\s+(?P<from>\w+)"
        r"(?:\s+INNER\s+JOIN\s+(?P<join_table>\w+)\s+ON\s+(?P<join_cond>.*?))?"
        r"(?:\s+WHERE\s+(?P<where>.*?))?\s*$",
        re.IGNORECASE | re.DOTALL
    )
    
    match = pattern.match(query.strip())
    if not match:
        raise ValueError("Formato de consulta SQL inválido.")
    
    return match.groupdict()