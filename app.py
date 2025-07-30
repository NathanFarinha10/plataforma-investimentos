import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Plataforma de Alocação de Ativos",
    page_icon="📊",
    layout="wide"
)

# --- DADOS E PARÂMETROS GLOBAIS ---

# 1. Dicionário de Portfólios Modelo
PORTFOLIOS = {
    "Conservador": {"Caixa": 0.40, "Renda Fixa Brasil": 0.50, "Renda Fixa Internacional": 0.05, "Ações Brasil": 0.02, "Ações Internacional": 0.03, "Fundos Imobiliários": 0.00, "Alternativos": 0.00},
    "Moderado": {"Caixa": 0.10, "Renda Fixa Brasil": 0.40, "Renda Fixa Internacional": 0.10, "Ações Brasil": 0.15, "Ações Internacional": 0.15, "Fundos Imobiliários": 0.05, "Alternativos": 0.05},
    "Balanceado": {"Caixa": 0.05, "Renda Fixa Brasil": 0.25, "Renda Fixa Internacional": 0.15, "Ações Brasil": 0.20, "Ações Internacional": 0.25, "Fundos Imobiliários": 0.05, "Alternativos": 0.05},
    "Crescimento": {"Caixa": 0.05, "Renda Fixa Brasil": 0.15, "Renda Fixa Internacional": 0.10, "Ações Brasil": 0.30, "Ações Internacional": 0.30, "Fundos Imobiliários": 0.05, "Alternativos": 0.05},
    "Agressivo": {"Caixa": 0.02, "Renda Fixa Brasil": 0.08, "Renda Fixa Internacional": 0.05, "Ações Brasil": 0.40, "Ações Internacional": 0.40, "Fundos Imobiliários": 0.02, "Alternativos": 0.03}
}

# 2. Mapeamento de Classes de Ativo para Tickers do Yahoo Finance (PROXIES)
ASSET_CLASSES_TICKERS = {
    "Caixa": "BSW.L",  # Usando um ETF de bonds de curto prazo como proxy para caixa
    "Renda Fixa Brasil": "B5P211.SA",
    "Renda Fixa Internacional": "BND",
    "Ações Brasil": "BOVA11.SA",
    "Ações Internacional": "VT",
    "Fundos Imobiliários": "IFIX.SA",
    "Alternativos": "GOLD11.SA"
}

# 3. Tese de Investimento (Exemplo)
TESES = {
    "Conservador": "Foco máximo em preservação de capital e baixa volatilidade.",
    "Moderado": "Equilíbrio entre preservação de capital e apreciação moderada.",
    "Balanceado": "Busca por uma valorização de capital consistente através de uma carteira diversificada.",
    "Crescimento": "Foco em crescimento de capital, com maior exposição a ativos de risco.",
    "Agressivo": "Prioriza o potencial máximo de crescimento no longo prazo, aceitando volatilidade significativamente maior."
}


# --- FUNÇÕES DE LÓGICA E CÁLCULO ---

# Usamos o cache do Streamlit para não baixar os mesmos dados repetidamente.
@st.cache_data
def get_market_data(tickers, period="5y"):
    """Baixa os dados históricos de preços 'Adj Close' para uma lista de tickers."""
    data = yf.download(tickers, period=period, progress=False)['Adj Close']
    return data.dropna()

@st.cache_data
def calculate_portfolio_performance(weights, returns):
    """Calcula a performance de um portfólio com base nos pesos e retornos dos ativos."""
    portfolio_return = returns.dot(weights)
    cumulative_returns = (1 + portfolio_return).cumprod()
    return cumulative_returns

def calculate_metrics(returns):
    """Calcula as principais métricas de risco e retorno."""
    total_return = (returns.iloc[-1] - 1) * 100
    annualized_return = (returns.iloc[-1])**(252/len(returns)) - 1
    annualized_volatility = returns.pct_change().std() * np.sqrt(252)
    
    # Simples, assumindo taxa livre de risco de 0 para o cálculo do Sharpe.
    sharpe_ratio = annualized_return / annualized_volatility if annualized_volatility != 0 else 0
    
    return {
        "Retorno Total (%)": f"{total_return:.2f}",
        "Volatilidade Anualizada (%)": f"{annualized_volatility * 100:.2f}",
        "Índice de Sharpe": f"{sharpe_ratio:.2f}"
    }

# --- INTERFACE DA APLICAÇÃO (UI) ---

st.title("📊 Plataforma de Portfólios Modelo")
st.markdown("Análise de performance e simulação interativa de portfólios.")

# --- SIDEBAR ---
st.sidebar.header("Configurações")
selected_portfolio_name = st.sidebar.selectbox(
    "Selecione um perfil para análise:",
    list(PORTFOLIOS.keys())
)
st.sidebar.info(TESES.get(selected_portfolio_name, "Tese de investimento não disponível."))
st.sidebar.markdown("---")
st.sidebar.markdown("Os dados são obtidos via `yfinance` e os ETFs são usados como *proxies* para as classes de ativos.")


# --- LÓGICA PRINCIPAL ---

# 1. Pega a alocação do portfólio modelo selecionado
model_allocation = PORTFOLIOS[selected_portfolio_name]
asset_classes = list(model_allocation.keys())
model_weights = np.array(list(model_allocation.values()))

# 2. Filtra os tickers necessários e baixa os dados de mercado
tickers_to_download = [ASSET_CLASSES_TICKERS[asset] for asset in asset_classes]
try:
    market_data = get_market_data(tickers_to_download)
    daily_returns = market_data.pct_change().dropna()
    
    # Renomeia colunas para nomes amigáveis
    daily_returns.columns = asset_classes
    
    st.header(f"Análise do Perfil: {selected_portfolio_name}")
    
    # 3. Seção do Simulador Interativo
    st.subheader("🧪 Simulador Interativo")
    st.markdown("Ajuste os pesos abaixo para simular uma carteira personalizada (desvio de até 5% do modelo).")
    
    cols = st.columns(len(asset_classes))
    custom_weights = []
    
    for i, asset in enumerate(asset_classes):
        with cols[i]:
            original_weight = model_allocation[asset]
            # Usando a regra de +/- 5%
            min_val = max(0.0, original_weight - 0.05)
            max_val = min(1.0, original_weight + 0.05)
            
            custom_weight = st.slider(
                f"{asset}",
                min_value=min_val,
                max_value=max_val,
                value=original_weight,
                step=0.01,
                format="%.0f%%",  # Mostra o valor como porcentagem
                key=f"slider_{asset}" # Chave única para cada slider
            )
            custom_weights.append(custom_weight)

    # Normaliza os pesos para que a soma seja sempre 100%
    custom_weights = np.array(custom_weights)
    custom_weights /= custom_weights.sum()
    
    # 4. Cálculo e Exibição dos Resultados
    
    # Calcula performance para o portfólio modelo E o customizado
    model_performance = calculate_portfolio_performance(model_weights, daily_returns)
    custom_performance = calculate_portfolio_performance(custom_weights, daily_returns)
    
    # Combina os resultados em um DataFrame para o gráfico
    performance_df = pd.DataFrame({
        "Modelo": model_performance,
        "Personalizado": custom_performance
    })
    
    st.subheader("Performance Histórica (Últimos 5 anos)")
    st.line_chart(performance_df)
    
    st.subheader("Métricas de Risco e Retorno (Carteira Personalizada)")
    metrics = calculate_metrics(custom_performance)
    
    metric_cols = st.columns(3)
    metric_cols[0].metric(label="Retorno Total", value=f"{metrics['Retorno Total (%)']}%")
    metric_cols[1].metric(label="Volatilidade Anualizada", value=f"{metrics['Volatilidade Anualizada (%)']}%")
    metric_cols[2].metric(label="Índice de Sharpe", value=metrics['Índice de Sharpe'])

except Exception as e:
    st.error(f"Não foi possível carregar os dados de mercado. Verifique os tickers ou tente novamente mais tarde. Erro: {e}")
