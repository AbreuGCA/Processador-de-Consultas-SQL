import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from src.parser.parse import parse_sql
from src.data.dic_dados import SCHEMA_VENDAS

st.set_page_config(
    page_title="Processador de Consultas SQL", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização
st.markdown("""
    <style>
    .stTextArea textarea { font-family: monospace; font-size: 16px; }
    [data-testid="stMetricValue"] { font-size: 1.2rem; }
    </style>
""", unsafe_allow_html=True)

# --- Barra Lateral ---
with st.sidebar:
    st.header("Schema do Banco")
    for tabela, colunas in SCHEMA_VENDAS.items():
        with st.expander(tabela.capitalize()):
            for coluna in colunas:
                st.markdown(f"- `{coluna}`")

# --- Área Principal ---
st.title("Processador de Consultas SQL")

modo = st.radio(
    "Escolha o modo de construção da consulta:", 
    ["Tradicional (Editor SQL)", "Low-Code (Construtor Visual)"], 
    horizontal=True
)

st.divider()

query = ""

if modo == "Tradicional (Editor SQL)":
    query = st.text_area(
        "Consulta SQL:", 
        value="SELECT Nome, Preco FROM produto WHERE Preco > 100",
        height=120
    )
else:
    st.subheader("Construtor Visual (Low-Code)")
    
    # 1. FROM
    tabela_principal = st.selectbox("1. Selecione a Tabela Principal (FROM)", list(SCHEMA_VENDAS.keys()))
    
    # 2. INNER JOIN
    st.write("**2. Junção (Opcional)**")
    com_join = st.checkbox("Adicionar INNER JOIN")
    join_clause = ""
    
    if com_join:
        j_col1, j_col2, j_col3 = st.columns(3)
        with j_col1:
            tabela_join = st.selectbox("Tabela para Junção", [t for t in SCHEMA_VENDAS.keys() if t != tabela_principal])
        with j_col2:
            col_principal = st.selectbox(f"Coluna de {tabela_principal}", SCHEMA_VENDAS[tabela_principal])
        with j_col3:
            col_join = st.selectbox(f"Coluna de {tabela_join}", SCHEMA_VENDAS[tabela_join])
        
        join_clause = f" INNER JOIN {tabela_join} ON {tabela_principal}.{col_principal} = {tabela_join}.{col_join}"
        
        # Atualiza colunas disponíveis para o SELECT (mescla as duas tabelas)
        cols_disp = [f"{tabela_principal}.{c}" for c in SCHEMA_VENDAS[tabela_principal]] + \
                    [f"{tabela_join}.{c}" for c in SCHEMA_VENDAS[tabela_join]]
    else:
        cols_disp = SCHEMA_VENDAS[tabela_principal]

    # 3. SELECT
    st.write("**3. Projeção**")
    colunas_selecionadas = st.multiselect("Selecione as Colunas (SELECT)", cols_disp)
    str_cols = ", ".join(colunas_selecionadas) if colunas_selecionadas else "*"

    # 4. WHERE
    st.write("**4. Filtro (Opcional)**")
    com_where = st.checkbox("Adicionar condição (WHERE)")
    where_clause = ""
    if com_where:
        w_col1, w_col2, w_col3 = st.columns(3)
        with w_col1:
            where_col = st.selectbox("Coluna do Filtro", cols_disp)
        with w_col2:
            where_op = st.selectbox("Operador", ["=", ">", "<", ">=", "<=", "!="])
        with w_col3:
            where_val = st.text_input("Valor (ex: 100 ou 'Texto')")
        if where_val:
            where_clause = f" WHERE {where_col} {where_op} {where_val}"

    # Montagem final
    query = f"SELECT {str_cols} FROM {tabela_principal}{join_clause}{where_clause}"
    st.info("SQL Gerado:")
    st.code(query, language="sql")

processar_btn = st.button("Processar Consulta", type="primary", use_container_width=True)

if processar_btn:
    if not query.strip():
        st.warning("Insira uma consulta.")
    else:
        try:
            result = parse_sql(query)
            st.divider()
            col_res1, col_res2 = st.columns([1, 1.5])

            with col_res1:
                st.subheader("Análise Estrutural")
                t = result['from']
                c = result['select']
                w = result['where']
                j = result['join_table']
                
                txt_algebra = f"\\pi_{{{c}}} "
                if w: txt_algebra += f"(\\sigma_{{{w}}} "
                if j: txt_algebra += f"({t} \\bowtie_{{{result['join_cond']}}} {j})"
                else: txt_algebra += f"({t})"
                if w: txt_algebra += ")"
                
                st.latex(txt_algebra)
                st.json(result)

            with col_res2:
                st.subheader("Plano de Execução")
                G = nx.DiGraph()
                
                # Nó FROM
                G.add_node("FROM", label=f"Tabela:\n{result['from']}", pos=(0.4, 0.1), color="#50E3C2")
                
                ultima_camada = "FROM"

                # Nó JOIN
                if result['join_table']:
                    G.add_node("JOIN", label=f"JOIN:\n{result['join_table']}\nON {result['join_cond']}", pos=(0.7, 0.1), color="#FF6B6B")
                    G.add_edge("JOIN", "FROM") # Join "alimenta" a origem de dados
                
                # Nó WHERE
                if result['where']:
                    w_label = f"Filtro:\n{result['where'][:20]}..." if len(result['where']) > 20 else f"Filtro:\n{result['where']}"
                    G.add_node("WHERE", label=w_label, pos=(0.5, 0.5), color="#F5A623")
                    G.add_edge("FROM", "WHERE")
                    ultima_camada = "WHERE"
                
                # Nó SELECT
                G.add_node("SELECT", label=f"Projeção:\n{result['select'][:30]}", pos=(0.5, 0.9), color="#4A90E2")
                G.add_edge(ultima_camada, "SELECT")

                # Plotagem
                fig, ax = plt.subplots(figsize=(7, 5))
                pos = nx.get_node_attributes(G, 'pos')
                
                nx.draw_networkx_edges(G, pos, ax=ax, arrows=True, edge_color="#BDC3C7", width=2)
                
                for node, (x, y) in pos.items():
                    ax.text(x, y, G.nodes[node]['label'], 
                            ha='center', va='center', fontweight='bold',
                            bbox=dict(boxstyle="round,pad=0.5", fc=G.nodes[node]['color'], ec="black", alpha=0.9))

                ax.axis("off")
                st.pyplot(fig)

        except Exception as e:
            st.error(f"Erro: {str(e)}")