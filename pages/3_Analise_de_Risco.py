import streamlit as st
from utils.db_functions import get_latest_allocations
from utils.risk_functions import calculate_portfolio_risk

# --- Verificação de Login ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("Por favor, faça o login na página principal para acessar este conteúdo.")
    st.stop()

# --- Configuração da Página ---
st.set_page_config(page_title="Análise de Risco", layout="wide")
st.title("🔎 Análise de Risco dos Portfólios")
st.markdown("---")

# --- Variáveis ---
PORTFOLIO_NAMES = ["Conservador", "Moderado", "Balanceado", "Crescimento", "Agressivo"]

# --- Corpo da Página ---
selected_portfolio = st.selectbox(
    "Selecione um portfólio para analisar:",
    PORTFOLIO_NAMES
)

if selected_portfolio:
    # Mostra um spinner enquanto os cálculos estão sendo feitos
    with st.spinner(f"Calculando métricas de risco para o portfólio '{selected_portfolio}'..."):
        # 1. Pega a alocação do banco de dados
        allocations_df = get_latest_allocations(selected_portfolio)

        if allocations_df.empty:
            st.warning(f"Não há dados de alocação para o portfólio '{selected_portfolio}'.")
        else:
            # 2. Calcula as métricas de risco
            risk_metrics, cumulative_returns = calculate_portfolio_risk(allocations_df)

            if risk_metrics:
                st.subheader(f"Métricas de Risco - {selected_portfolio}")
                
                # Exibe as métricas em colunas
                col1, col2, col3 = st.columns(3)
                col1.metric(
                    label="Volatilidade Anualizada",
                    value=f"{risk_metrics['Volatilidade Anualizada']:.2%}"
                )
                col2.metric(
                    label="Sharpe Ratio",
                    value=f"{risk_metrics['Sharpe Ratio']:.2f}"
                )
                col3.metric(
                    label="VaR 95% (1 dia)",
                    value=f"{risk_metrics['VaR 95% (1 dia)']:.2%}",
                    help="Representa a perda máxima esperada em 1 dia, com 95% de confiança, baseada em dados históricos."
                )

                # Exibe o gráfico de retorno acumulado
                st.subheader("Retorno Acumulado Histórico (3 anos)")
                st.line_chart(cumulative_returns)
            else:
                st.error("Não foi possível calcular as métricas de risco. Verifique as alocações e o mapeamento de tickers.")
