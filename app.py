import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Plataforma Gestora",
    page_icon="📊",
    layout="wide"
)

# --- LÓGICA DE AUTENTICAÇÃO ---

def check_password():
    """Retorna `True` se o usuário estiver logado, `False` caso contrário."""

    # Dicionário de usuários e senhas (APENAS PARA DESENVOLVIMENTO)
    # Em um ambiente real, use um banco de dados e senhas com hash.
    VALID_CREDENTIALS = {
        "editor": {"password": "gestora123", "role": "Editor"},
        "advisor": {"password": "advisor123", "role": "Visualizador"}
    }

    def login_form():
        """Exibe o formulário de login."""
        with st.form("login_form"):
            st.header("Login")
            username = st.text_input("Usuário", key="login_username").lower()
            password = st.text_input("Senha", type="password", key="login_password")
            submitted = st.form_submit_button("Entrar")

            if submitted:
                user_info = VALID_CREDENTIALS.get(username)
                if user_info and user_info["password"] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.session_state["role"] = user_info["role"]
                    st.rerun() # Recarrega a página após o login bem-sucedido
                else:
                    st.error("Usuário ou senha inválidos.")
    
    # Se o usuário não estiver logado, exibe o formulário.
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        login_form()
        return False
    # Se já estiver logado, permite o acesso.
    else:
        return True

# --- INÍCIO DA APLICAÇÃO ---

# Verifica se o login foi feito com sucesso
if check_password():
    # --- CABEÇALHO COM LOGOUT ---
    col1, col2 = st.columns([0.85, 0.15])
    with col1:
        st.title("Plataforma de Inteligência da Gestora")
    with col2:
        if st.button("Logout"):
            st.session_state["logged_in"] = False
            st.session_state.pop("username", None)
            st.session_state.pop("role", None)
            st.rerun()

    st.markdown(f"Bem-vindo, **{st.session_state['username']}**! (Perfil: *{st.session_state['role']}*)")
    st.markdown("---")
    
    st.info(
        """
        ### Bem-vindo à sua plataforma centralizada!
        - Use o menu na barra lateral à esquerda para navegar entre as seções.
        - **Hub de Inteligência:** Acesse as visões de mercado compiladas.
        - **Portfólios Modelo:** Visualize as alocações estratégicas da casa.
        """,
        icon="👈"
    )
