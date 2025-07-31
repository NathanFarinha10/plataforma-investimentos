import streamlit as st
import pandas as pd
import plotly.express as px
from utils.db_functions import get_latest_allocations, save_allocations

# --- Verificação de Login ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("Por favor, faça o login na página principal para acessar este conteúdo.")
    st.stop()

# --- Configuração da Página ---
st.set_page_config(page_title="Portfólios Modelo", layout="wide")
st.title("💼 Portfólios Modelo da Gestora")
st.markdown("---")

# --- Variáveis e Constantes ---
PORTFOLIO_NAMES = ["Conservador", "Moderado", "Balanceado", "Crescimento", "Agressivo"]
ASSET_CLASSES = ["Caixa", "Renda Fixa Brasil", "Renda Fixa Internacional", 
                 "Ações Brasil", "Ações Internacional", "Fundos Imobiliários", "Alternativos"]

# --- Corpo Principal da Página ---
selected_portfolio = st.selectbox(
    "Selecione um portfólio para visualizar a alocação:",
    PORTFOLIO_NAMES
)

if selected_portfolio:
    df_alloc = get_latest_allocations(selected_portfolio)

    if df_alloc.empty:
        st.warning(f"Ainda não há dados de alocação para o portfólio '{selected_portfolio}'. Editores podem adicionar abaixo.")
    else:
        st.write(f"### Alocação Estratégica - Portfólio {selected_portfolio}")
        
        col1, col2 = st.columns([0.5, 0.5])
        with col1:
            fig = px.pie(df_alloc, names='asset_class', values='allocation_pct', 
                         title='Distribuição por Classe de Ativo', hole=0.3)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.dataframe(
                df_alloc.style.format({'allocation_pct': '{:.2f}%'}),
                use_container_width=True,
                hide_index=True
            )
        
# --- Seção de Edição para o Perfil "Editor" ---
if st.session_state["role"] == "Editor":
    with st.expander("✏️ Editar/Adicionar Alocações (Acesso de Editor)", expanded=df_alloc.empty):
        with st.form("edit_allocation_form"):
            st.write(f"**Definindo alocação para o portfólio:** `{selected_portfolio}`")
            
            new_allocations = {}
            for asset in ASSET_CLASSES:
                new_allocations[asset] = st.slider(
                    f"% {asset}", min_value=0.0, max_value=100.0, value=0.0, step=0.5, format="%.1f%%"
                )

            total_pct = sum(new_allocations.values())
            st.metric("Total Alocado", f"{total_pct:.1f}%")

            submitted = st.form_submit_button("Salvar Nova Alocação")

            if submitted:
                if abs(total_pct - 100.0) > 0.1:
                    st.error("A soma das alocações deve ser exatamente 100%.")
                else:
                    try:
                        save_allocations(selected_portfolio, new_allocations)
                        st.success(f"Alocação para o portfólio '{selected_portfolio}' salva com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ocorreu um erro ao salvar: {e}")
