import streamlit as st
from utils.db_functions import save_analysis, get_all_analyses
import pandas as pd

# --- Verificação de Login ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("Por favor, faça o login na página principal para acessar este conteúdo.")
    st.stop()

# --- Configuração da Página ---
st.set_page_config(page_title="Hub de Inteligência", layout="wide")
st.title("🧠 Hub de Inteligência de Mercado")
st.markdown("---")

# --- Fontes de Análise ---
SOURCES = ["BlackRock", "JP Morgan", "XP", "BTG Pactual", "Opinião da Casa"]

# --- Seção de Submissão para Editores ---
if st.session_state["role"] == "Editor":
    with st.expander("📝 Submeter nova análise (Acesso de Editor)", expanded=False):
        with st.form("analysis_form", clear_on_submit=True):
            title = st.text_input("Título da Análise", placeholder="Ex: Perspectivas para Renda Fixa Global")
            source = st.selectbox("Fonte da Análise", SOURCES)
            summary = st.text_area("Resumo da Análise", height=200, placeholder="Insira os pontos principais da análise aqui...")
            
            submitted = st.form_submit_button("Salvar Análise")
            
            if submitted:
                if not title or not summary:
                    st.warning("Por favor, preencha o Título e o Resumo.")
                else:
                    author = st.session_state["username"]
                    try:
                        save_analysis(title, source, summary, author)
                        st.success("Análise salva com sucesso!")
                    except Exception as e:
                        st.error(f"Ocorreu um erro ao salvar a análise: {e}")

# --- Seção de Visualização de Análises ---
st.subheader("Análises Recentes")

analyses_df = get_all_analyses()

if analyses_df.empty:
    st.info("Nenhuma análise de mercado foi cadastrada ainda. Editores podem adicionar uma análise na seção acima.")
else:
    # Itera sobre cada linha do DataFrame para exibir as análises
    for index, row in analyses_df.iterrows():
        with st.container(border=True):
            st.markdown(f"#### {row['title']}")
            st.caption(f"Fonte: **{row['source']}** | Adicionado por: **{row['author']}** em {pd.to_datetime(row['created_at']).strftime('%d/%m/%Y às %H:%M')}")
            st.markdown(row['summary'])
