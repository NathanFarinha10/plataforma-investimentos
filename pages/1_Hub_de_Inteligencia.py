import streamlit as st

# Verifica se o usuário está logado, buscando a informação do st.session_state
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("Por favor, faça o login na página principal para acessar este conteúdo.")
    st.stop() # Interrompe a execução da página se não estiver logado

# --- Conteúdo da Página ---

st.set_page_config(page_title="Hub de Inteligência", layout="wide")

st.title("🧠 Hub de Inteligência de Mercado")
st.markdown("---")

st.markdown("Aqui serão exibidas as visões consolidadas das principais gestoras globais e locais.")

# Conteúdo exclusivo para o perfil "Editor"
if st.session_state["role"] == "Editor":
    with st.expander("📝 Submeter nova análise (Acesso de Editor)"):
        st.info("Esta área será usada para que os analistas possam inserir os resumos e fazer upload de relatórios.")
        
        st.text_input("Título da Análise")
        st.text_area("Resumo da Análise")
        st.file_uploader("Fazer upload do relatório em PDF")
        if st.button("Salvar Análise"):
            st.success("Análise salva com sucesso! (Funcionalidade a ser implementada)")

# Conteúdo para todos (depois que a lógica for implementada)
st.subheader("Análises Recentes")
st.info("Em breve: Lista das últimas análises de mercado cadastradas.")
