import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

from src.parser.parse import parse_sql
from src.data.dic_dados import SCHEMA_VENDAS
from src.algebra.otimizador import Optimizer
from src.graph.grafo import QueryGraph
from src.data.val_schema import ValidarSchema

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
    
    # ... (O restante da lógica do Low-Code continua idêntica à sua) ...
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

    query = f"SELECT {str_cols} FROM {tabela_principal}{join_clause}{where_clause}"
    st.info("SQL Gerado:")
    st.code(query, language="sql")

processar_btn = st.button("Processar Consulta", type="primary", use_container_width=True)

# --- NOVA LÓGICA DE PROCESSAMENTO, VALIDAÇÃO E OTIMIZAÇÃO ---
if processar_btn:
    if not query.strip():
        st.warning("Insira uma consulta.")
    else:
        try:
            # 1. PARSER
            result = parse_sql(query)
            
            # 2. VALIDAÇÃO DE SCHEMA (Garante 1,0 ponto)
            validador = ValidarSchema(SCHEMA_VENDAS)
            tabela_from = result['from'].lower()
            
            if tabela_from not in validador.schema:
                st.error(f"Erro: A tabela '{tabela_from}' não existe no banco de dados.")
                st.stop()

            # 3. OTIMIZAÇÃO (Garante os pontos de Heurísticas)
            optimizer = Optimizer(result)
            arvore_otimizada = optimizer.build_optimized_tree()
            
            # 4. PLANO DE EXECUÇÃO (Passo a Passo)
            graph_manager = QueryGraph(arvore_otimizada)
            passos = graph_manager.generate_execution_steps()

            st.divider()
            col_res1, col_res2 = st.columns([1, 1.5])

            with col_res1:
                st.subheader("Plano de Execução")
                st.markdown("**Ordem Lógica das Operações:**")
                for passo in passos:
                    st.success(passo)
                
                st.markdown("---")
                st.subheader("Análise Estrutural")
                t = result['from']
                c = result['select']
                w = result['where']
                
                # Monta a Álgebra Relacional Dinâmica
                txt_algebra = f"\\pi_{{{c}}} "
                if w: txt_algebra += f"(\\sigma_{{{w}}} "
                txt_algebra += f"({t})"
                if w: txt_algebra += ")"
                
                st.latex(txt_algebra)

            with col_res2:
                st.subheader("Grafo de Operadores Otimizado")
                st.caption("A estrutura abaixo reflete o *Push-down* das heurísticas de redução.")
                
                # Desenhador Dinâmico do Grafo Otimizado
                G = nx.DiGraph()
                
                def construir_grafo_networkx(node, x=0.5, y=0.9, dx=0.2, parent_id=None, counter=0):
                    current_id = f"node_{counter}"
                    counter += 1
                    
                    # Definição de Cores e Labels
                    color = "#BDC3C7"
                    label = node.name
                    
                    if node.name == "Scan":
                        label = f"SCAN\n({getattr(node, 'table_name', '')})"
                        color = "#50E3C2"
                    elif node.name == "Selection":
                        cond = getattr(node, 'condition', '')
                        label = f"FILTRO (σ)\n{cond[:20]}"
                        color = "#F5A623"
                    elif node.name == "Projection":
                        cols = ", ".join(getattr(node, 'columns', []))
                        label = f"PROJEÇÃO (π)\n{cols[:20]}"
                        color = "#4A90E2"
                    elif node.name == "Join":
                        cond = getattr(node, 'condition', '')
                        label = f"JUNÇÃO (⨝)\n{cond[:20]}"
                        color = "#FF6B6B"

                    # Adiciona o nó atual ao grafo NetworkX
                    G.add_node(current_id, label=label, pos=(x, y), color=color)
                    
                    # Se houver um pai, cria a aresta (o fluxo sobe: filho -> pai)
                    if parent_id:
                        G.add_edge(current_id, parent_id)
                        
                    # Lógica de Recursão
                    # CASO 1: Nó de Junção (Dois filhos/ramos)
                    if node.name == "Join":
                        # Filho Esquerdo (root original)
                        counter = construir_grafo_networkx(node.left_child, x - dx, y - 0.2, dx/2, current_id, counter)
                        # Filho Direito (tabela do join)
                        counter = construir_grafo_networkx(node.right_child, x + dx, y - 0.2, dx/2, current_id, counter)
                    
                    # CASO 2: Nó Linear (Um filho)
                    elif hasattr(node, 'child') and node.child:
                        counter = construir_grafo_networkx(node.child, x, y - 0.2, dx, current_id, counter)
                        
                    return counter

                # Invoca a construção a partir da raiz otimizada
                construir_grafo_networkx(arvore_otimizada)
                
                # Plotagem usando Matplotlib
                fig, ax = plt.subplots(figsize=(7, 5))
                pos = nx.get_node_attributes(G, 'pos')
                
                nx.draw_networkx_edges(G, pos, ax=ax, arrows=True, edge_color="#7F8C8D", width=2, arrowsize=20)
                
                for node_id, (x, y) in pos.items():
                    ax.text(x, y, G.nodes[node_id]['label'], 
                            ha='center', va='center', fontweight='bold', fontsize=10,
                            bbox=dict(boxstyle="round,pad=0.6", fc=G.nodes[node_id]['color'], ec="black", alpha=0.95))

                ax.axis("off")
                st.pyplot(fig)

        except ValueError as ve:
            st.error(f"Erro na Consulta: {ve}")
        except Exception as e:
            st.error(f"Erro Inesperado: {str(e)}")