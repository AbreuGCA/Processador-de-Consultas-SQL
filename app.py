import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

from src.parser.parse import parse_sql, extrair_condicoes, extrair_coluna_de_condicao
from src.data.dic_dados import SCHEMA_VENDAS
from src.algebra.otimizador import Optimizer
from src.graph.grafo import QueryGraph
from src.data.val_schema import ValidarSchema

# ── Configuração da Página ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Processador de Consultas SQL",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Fonte monoespaçada na área SQL */
    .stTextArea textarea {
        font-family: 'Courier New', monospace;
        font-size: 15px;
    }
    /* Destaque para erros */
    .erro-box {
        background: #fff0f0;
        border-left: 4px solid #e74c3c;
        padding: 10px 14px;
        border-radius: 4px;
        font-family: monospace;
    }
    /* Plano de execução */
        .passo {
            background: transparent;
            border-left: 4px solid #2980b9;
            padding: 8px 14px;
            margin-bottom: 6px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 14px;
        }
    </style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  VALIDAÇÃO SEMÂNTICA
# ══════════════════════════════════════════════════════════════════════════════

def validar_consulta_completa(result: dict, validador: ValidarSchema) -> list:
    tabela_from = result['from'].lower()
    tabelas_envolvidas = [tabela_from]
    validador.validar_tabela(tabela_from)

    if result.get('join_table'):
        tabela_join = result['join_table'].lower()
        validador.validar_tabela(tabela_join)
        tabelas_envolvidas.append(tabela_join)
        if result.get('join_cond'):
            for cond in extrair_condicoes(result['join_cond']):
                col = extrair_coluna_de_condicao(cond)
                if col:
                    validador.validar_coluna_condicao(col, tabelas_envolvidas, contexto="JOIN ON")

    validador.validar_colunas_select(result['select'], tabelas_envolvidas)

    if result.get('where'):
        for cond in extrair_condicoes(result['where']):
            col = extrair_coluna_de_condicao(cond)
            if col:
                validador.validar_coluna_condicao(col, tabelas_envolvidas, contexto="WHERE")

    return tabelas_envolvidas


# ══════════════════════════════════════════════════════════════════════════════
#  CONSTRUÇÃO DO GRAFO NETWORKX
# ══════════════════════════════════════════════════════════════════════════════

def construir_grafo_networkx(G: nx.DiGraph, node, x=0.5, y=0.9, dx=0.25,
                              parent_id=None, counter=0) -> int:
    current_id = f"node_{counter}"
    counter += 1

    if node.name == "Scan":
        label = f"SCAN\n({getattr(node, 'table_name', '')})"
        color = "#50E3C2"
    elif node.name == "Selection":
        cond = getattr(node, 'condition', '')
        label = f"σ SELEÇÃO\n{cond[:22]}"
        color = "#F5A623"
    elif node.name == "Projection":
        cols = ", ".join(getattr(node, 'columns', []))
        label = f"π PROJEÇÃO\n{cols[:22]}"
        color = "#4A90E2"
    elif node.name == "Join":
        cond = getattr(node, 'condition', '')
        label = f"⨝ JUNÇÃO\n{cond[:22]}"
        color = "#FF6B6B"
    else:
        label = node.name
        color = "#BDC3C7"

    G.add_node(current_id, label=label, pos=(x, y), color=color)
    if parent_id:
        G.add_edge(current_id, parent_id)

    if node.name == "Join":
        counter = construir_grafo_networkx(G, node.left_child,  x - dx, y - 0.22, dx / 1.8, current_id, counter)
        counter = construir_grafo_networkx(G, node.right_child, x + dx, y - 0.22, dx / 1.8, current_id, counter)
    elif hasattr(node, 'child') and node.child:
        counter = construir_grafo_networkx(G, node.child, x, y - 0.22, dx, current_id, counter)

    return counter


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR — SCHEMA
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.header("📋 Schema do Banco")
    st.caption("Tabelas e colunas disponíveis:")
    for tabela, colunas in SCHEMA_VENDAS.items():
        with st.expander(tabela.capitalize()):
            for coluna in colunas:
                st.markdown(f"- `{coluna}`")
    st.divider()
    st.caption("**Operadores permitidos:**")
    st.code("=   >   <   >=   <=   <>   AND   ( )")
    st.caption("**Cláusulas suportadas:**")
    st.code("SELECT  FROM  WHERE  INNER JOIN")


# ══════════════════════════════════════════════════════════════════════════════
#  ÁREA PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

st.title("🔍 Processador de Consultas SQL")
st.caption("Digite uma consulta SQL, processe e visualize o grafo de operadores e o plano de execução.")

st.divider()

# ── Entrada da Consulta ──────────────────────────────────────────────────────
query = st.text_area(
    "Consulta SQL:",
    value="SELECT Nome, Preco FROM produto WHERE Preco > 100",
    height=110,
    help="Use SELECT, FROM, WHERE e/ou INNER JOIN. Operadores: =, >, <, >=, <=, <>, AND, ( )"
)

processar_btn = st.button("▶ Processar Consulta", type="primary", use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PROCESSAMENTO
# ══════════════════════════════════════════════════════════════════════════════

if processar_btn:
    if not query.strip():
        st.warning("⚠️ Insira uma consulta SQL antes de processar.")
        st.stop()

    # ETAPA 1: Parse
    try:
        result = parse_sql(query)
    except ValueError as e:
        st.error(f"❌ **Erro de Sintaxe (Parser):** {e}")
        st.stop()

    # ETAPA 2: Validação Semântica
    validador = ValidarSchema(SCHEMA_VENDAS)
    try:
        tabelas_envolvidas = validar_consulta_completa(result, validador)
    except ValueError as e:
        st.error(f"❌ **Erro de Validação (Schema):** {e}")
        st.caption("Verifique os nomes de tabelas e colunas na barra lateral.")
        st.stop()

    # ETAPA 3: Otimização
    try:
        optimizer = Optimizer(result)
        arvore_otimizada = optimizer.build_optimized_tree()
    except Exception as e:
        st.error(f"❌ **Erro no Otimizador:** {e}")
        st.stop()

    # ETAPA 4: Plano de Execução
    graph_manager = QueryGraph(arvore_otimizada)
    passos = graph_manager.generate_execution_steps()

    # ── Sucesso ──────────────────────────────────────────────────────────────
    st.divider()
    st.success("✅ Consulta processada com sucesso!")

    col_esq, col_dir = st.columns([1, 1.6])

    # ── Coluna Esquerda ──────────────────────────────────────────────────────
    with col_esq:

        # Álgebra Relacional
        st.subheader("Álgebra Relacional")
        t = result['from']
        c = result['select']
        w = result.get('where', '')
        join_t = result.get('join_table', '')
        join_c = result.get('join_cond', '')

        if join_t:
            inner = f"({t} \\bowtie_{{{join_c}}} {join_t})"
        else:
            inner = t
        if w:
            inner = f"\\sigma_{{{w}}}({inner})"
        if c and c.strip() != '*':
            expr = f"\\pi_{{{c}}}({inner})"
        else:
            expr = inner
        st.latex(expr)

        st.markdown("---")

        # Plano de Execução
        st.subheader("📋 Plano de Execução")
        st.caption("Ordem lógica das operações (pós-ordem na árvore):")
        for i, passo in enumerate(passos, 1):
            st.markdown(
                f'<div class="passo"><b>Passo {i}:</b> {passo}</div>',
                unsafe_allow_html=True
            )

        st.markdown("---")

        # Heurísticas
        st.subheader("🔧 Heurísticas Aplicadas")
        heuristicas = []
        if result.get('where'):
            heuristicas.append("**H1 — Redução de Tuplas:** σ aplicada antes da π")
        if c and c.strip() != '*':
            heuristicas.append("**H2 — Redução de Atributos:** π elimina colunas desnecessárias")
        if result.get('join_table'):
            heuristicas.append("**H3 — Evitar Produto Cartesiano:** ⨝ com condição ON explícita")

        if heuristicas:
            for h in heuristicas:
                st.markdown(f"✅ {h}")
        else:
            st.info("Nenhuma heurística ativa (consulta simples sem WHERE nem JOIN).")

    # ── Coluna Direita: Grafo ─────────────────────────────────────────────────
    with col_dir:
        st.subheader("🌳 Grafo de Operadores Otimizado")

        # Legenda
        leg = st.columns(4)
        with leg[0]: st.markdown("🟩 **SCAN**")
        with leg[1]: st.markdown("🟧 **σ** Seleção")
        with leg[2]: st.markdown("🟦 **π** Projeção")
        with leg[3]: st.markdown("🟥 **⨝** Junção")

        # Grafo NetworkX
        G = nx.DiGraph()
        construir_grafo_networkx(G, arvore_otimizada)

        fig, ax = plt.subplots(figsize=(7, 5))
        fig.patch.set_alpha(0)
        ax.set_facecolor("none")

        pos = nx.get_node_attributes(G, 'pos')
        nx.draw_networkx_edges(
            G, pos, ax=ax, arrows=True,
            edge_color="#7F8C8D", width=2, arrowsize=20,
        )
        for node_id, (x, y) in pos.items():
            ax.text(
                x, y, G.nodes[node_id]['label'],
                ha='center', va='center', fontweight='bold', fontsize=9,
                bbox=dict(
                    boxstyle="round,pad=0.5",
                    fc=G.nodes[node_id]['color'],
                    ec="black", alpha=0.95
                )
            )

        ax.axis("off")
        st.pyplot(fig)