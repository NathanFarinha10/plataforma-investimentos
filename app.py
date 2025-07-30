import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Plataforma de Alocação de Ativos",
    page_icon="📊",
    layout="wide"
)

# --- DADOS DOS PORTFÓLIOS (Hardcoded por enquanto) ---
# No futuro, isso virá de um banco de dados
PORTFOLIOS = {
    "Conservador": {
        "Caixa": 0.40,
        "Renda Fixa Brasil": 0.50,
        "Renda Fixa Internacional": 0.05,
        "Ações Brasil": 0.02,
        "Ações Internacional": 0.03,
        "Fundos Imobiliários": 0.00,
        "Alternativos": 0.00,
    },
    "Moderado": {
        "Caixa": 0.10,
        "Renda Fixa Brasil": 0.40,
        "Renda Fixa Internacional": 0.10,
        "Ações Brasil": 0.15,
        "Ações Internacional": 0.15,
        "Fundos Imobiliários": 0.05,
        "Alternativos": 0.05,
    },
    "Balanceado": {
        "Caixa": 0.05,
        "Renda Fixa Brasil": 0.25,
        "Renda Fixa Internacional": 0.15,
        "Ações Brasil": 0.20,
        "Ações Internacional": 0.25,
        "Fundos Imobiliários": 0.05,
        "Alternativos": 0.05,
    },
    "Crescimento": {
        "Caixa": 0.05,
        "Renda Fixa Brasil": 0.15,
        "Renda Fixa Internacional": 0.10,
        "Ações Brasil": 0.30,
        "Ações Internacional": 0.30,
        "Fundos Imobiliários": 0.05,
        "Alternativos": 0.05,
    },
    "Agressivo": {
        "Caixa": 0.02,
        "Renda Fixa Brasil": 0.08,
        "Renda Fixa Internacional": 0.05,
        "Ações Brasil": 0.40,
        "Ações Internacional": 0.40,
        "Fundos Imobiliários": 0.02,
        "Alternativos": 0.03,
    }
}

# Tese de Investimento (Exemplo)
TESES = {
    "Conservador": "Foco máximo em preservação de capital e baixa volatilidade, com exposição mínima a ativos de risco.",
    "Moderado": "Busca um equilíbrio entre preservação de capital e apreciação moderada, com uma alocação diversificada em diferentes classes de ativos.",
    "Agressivo": "Prioriza o potencial máximo de crescimento do capital no longo prazo, aceitando uma volatilidade significativamente maior."
    # Adicionar as outras teses...
}


# --- INTERFACE DA APLICAÇÃO ---

st.title("📊 Plataforma de Portfólios Modelo")
st.markdown("Bem-vindo à plataforma de inteligência e visualização de portfólios da gestora.")

# --- SELEÇÃO E VISUALIZAÇÃO DO PORTFÓLIO ---
st.header("Análise dos Portfólios Modelo")

# Seleção do portfólio em uma coluna lateral para melhor organização
selected_portfolio = st.sidebar.selectbox(
    "Selecione um perfil para análise:",
    list(PORTFOLIOS.keys())
)

st.sidebar.info(TESES.get(selected_portfolio, "Tese de investimento não disponível."))

# Obter os dados do portfólio selecionado
allocation = PORTFOLIOS[selected_portfolio]

# Remover classes com 0% de alocação para um gráfico mais limpo
filtered_allocation = {key: value for key, value in allocation.items() if value > 0}

# Criar um DataFrame para melhor visualização
df_allocation = pd.DataFrame(filtered_allocation.items(), columns=["Classe de Ativo", "Alocação"])
df_allocation["Alocação"] = df_allocation["Alocação"] * 100 # Mostrar em percentual

# Dividir a tela em duas colunas
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"Alocação do Perfil: {selected_portfolio}")
    st.dataframe(
        df_allocation.style.format({"Alocação": "{:.2f}%"}),
        hide_index=True,
        use_container_width=True
    )

with col2:
    st.subheader("Distribuição Visual")
    fig = px.pie(
        df_allocation,
        values="Alocação",
        names="Classe de Ativo",
        title=f"Gráfico de Alocação - {selected_portfolio}",
        hole=0.3 # Cria um gráfico de "rosca" (donut chart)
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
