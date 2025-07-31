import streamlit as st

# Verifica se o usuário está logado
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("Por favor, faça o login na página principal para acessar este conteúdo.")
    st.stop()

# --- Conteúdo da Página ---

st.set_page_config(page_title="Portfólios Modelo", layout="wide")

st.title("💼 Portfólios Modelo da Gestora")
st.markdown("---")

# Seletor de Portfólio
portfolio_selecionado = st.selectbox(
    "Selecione um portfólio para visualizar a alocação:",
    ("Conservador", "Moderado", "Balanceado", "Crescimento", "Agressivo")
)

st.write(f"### Alocação Estratégica - Portfólio {portfolio_selecionado}")

st.info("Em breve: Gráficos e tabelas com as alocações por classe de ativo.")

# Conteúdo exclusivo para o perfil "Editor"
if st.session_state["role"] == "Editor":
    with st.expander("✏️ Editar Alocações (Acesso de Editor)"):
        st.warning("A funcionalidade de edição será implementada aqui, permitindo que gestores atualizem os percentuais.")
        st.slider("Ações Brasil", 0, 100, 20)
        st.slider("Ações Internacional", 0, 100, 20)
        st.slider("Renda Fixa Brasil", 0, 100, 40)
        # ... adicionar outros sliders
        if st.button("Salvar Nova Alocação"):
            st.success("Alocação salva! (Funcionalidade a ser implementada)")
