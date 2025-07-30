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
#    *** VERSÃO CORRIGIDA COM TICKERS MAIS ROBUSTOS ***
ASSET_CLASSES_TICKERS = {
    # SUBSTITUÍDO: BSW.L (Londres) por SELB11.SA (Brasil) -> Proxy para SELIC
    "Caixa": "SELB11.SA",
    "Renda Fixa Brasil": "B5P211.SA",
    "Renda Fixa Internacional": "BND",
    "Ações Brasil": "BOVA11.SA",
    "Ações Internacional": "VT",
    # SUBSTITUÍDO: IFIX.SA (índice) por XFIX11.SA (ETF) -> Mais confiável
    "Fundos Imobiliários": "XFIX11.SA",
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

@st.cache_data
def get_market_data(tickers, period="5y"):
    """Baixa os dados históricos de preços 'Adj Close' para uma lista de tickers."""
    data = yf.download(tickers, period=period, progress=False)
    
    if isinstance(data.columns, pd.MultiIndex):
        data = data['Adj Close']
    
    if isinstance(data, pd.Series):
        data = data.to_frame(name=tickers[0])
        
    # Usamos ffill() para preencher feriados com o valor do dia anterior, e depois bfill() para o início da série
    data = data.ffill().bfill()
    
    return data

@st.cache_data
def calculate_portfolio_performance(weights, returns):
    """Calcula a performance de um portfólio com base nos pesos e retornos dos ativos."""
    common_assets = returns.columns.intersection(weights.index)
    
    if len(common_assets) == 0:
        return pd.Series(1.0, index=returns.index)

    filtered_returns = returns[common_assets]
    filtered_weights = weights[common_assets]

    portfolio_return = filtered_returns.dot(filtered_weights)
    cumulative_returns = (1 + portfolio_return).cumprod()
    return cumulative_returns

def calculate_metrics(returns):
    """Calcula as principais métricas de risco e retorno."""
    if len(returns) < 2:
        return {"Retorno Total (%)": "N/A", "Volatilidade Anualizada (%)": "N/A", "Índice de Sharpe": "N/A"}

    total_return = (returns.iloc[-1] - 1)
    annualized_return = (returns.iloc[-1])**(252/len(returns)) - 1
    annualized_volatility = returns.pct_change().std() * np.sqrt(252)
    
    sharpe_ratio = annualized_return / annualized_volatility if annualized_volatility > 0 else 0
    
    return {
        "Retorno Total (%)": f"{total_return * 100:.2f}",
        "Volatilidade Anualizada (%)": f"{annualized_volatility * 100:.2f}",
        "Índice de Sharpe": f"{sharpe_ratio:.2f}"
    }

# --- INTERFACE DA APLICAÇÃO (UI) ---
st.title("📊 Plataforma de Portfólios Modelo")
st.markdown("Análise de performance e simulação interativa de portfólios.")

# --- SIDEBAR ---
st.sidebar.header("Configurações")
selected_portfolio_name = st.sidebar.selectbox("Selecione um perfil para análise:", list(PORTFOLIOS.keys()))
st.sidebar.info(TESES.get(selected_portfolio_name, "Tese de investimento não disponível."))
st.sidebar.markdown("---")
st.sidebar.markdown("Os dados são obtidos via `yfinance` e os ETFs são usados como *proxies* para as classes de ativos.")

# --- LÓGICA PRINCIPAL ---
model_allocation = PORTFOLIOS[selected_portfolio_name]
asset_classes = list(model_allocation.keys())
tickers_to_download = [ASSET_CLASSES_TICKERS[asset] for asset in asset_classes]

try:
    market_data = get_market_data(tickers_to_download)
    
    if market_data.empty:
        st.warning("Não foi possível obter dados para os tickers selecionados. A análise não pode ser exibida.")
    else:
        available_tickers = market_data.columns.tolist()
        ticker_to_asset_map = {v: k for k, v in ASSET_CLASSES_TICKERS.items()}
        available_assets = [ticker_to_asset_map[ticker] for ticker in available_tickers]

        daily_returns = market_data.pct_change().dropna()
        daily_returns.columns = available_assets

        st.header(f"Análise do Perfil: {selected_portfolio_name}")

        # --- SIMULADOR ---
        st.subheader("🧪 Simulador Interativo")
        st.markdown("Ajuste os pesos para simular uma carteira personalizada (desvio de até 5% do modelo).")
        
        filtered_model_allocation = {asset: model_allocation[asset] for asset in available_assets}
        
        # Garante que os sliders só apareçam se houver ativos
        if available_assets:
            cols = st.columns(len(available_assets))
            custom_weights_dict = {}

            for i, asset in enumerate(available_assets):
                with cols[i]:
                    original_weight = filtered_model_allocation.get(asset, 0)
                    min_val, max_val = max(0.0, original_weight - 0.05), min(1.0, original_weight + 0.05)
                    custom_weight = st.slider(f"{asset}", min_val, max_val, original_weight, 0.01, "%.0f%%", key=f"slider_{asset}")
                    custom_weights_dict[asset] = custom_weight
            
            total_custom_weight = sum(custom_weights_dict.values())
            if total_custom_weight > 0:
                custom_weights_series = pd.Series({asset: weight / total_custom_weight for asset, weight in custom_weights_dict.items()})
            else:
                custom_weights_series = pd.Series(custom_weights_dict)

            # --- CÁLCULO E EXIBIÇÃO ---
            model_weights_series = pd.Series(filtered_model_allocation)
            
            model_performance = calculate_portfolio_performance(model_weights_series, daily_returns)
            custom_performance = calculate_portfolio_performance(custom_weights_series, daily_returns)
            
            performance_df = pd.DataFrame({"Modelo": model_performance, "Personalizado": custom_performance})
            
            st.subheader("Performance Histórica")
            st.line_chart(performance_df)
            
            st.subheader("Métricas de Risco e Retorno (Carteira Personalizada)")
            metrics = calculate_metrics(custom_performance)
            
            metric_cols = st.columns(3)
            metric_cols[0].metric(label="Retorno Total", value=f"{metrics['Retorno Total (%)']}%")
            metric_cols[1].metric(label="Volatilidade Anualizada", value=f"{metrics['Volatilidade Anualizada (%)']}%")
            metric_cols[2].metric(label="Índice de Sharpe", value=metrics['Índice de Sharpe'])
        else:
            st.warning("Nenhum ativo com dados válidos foi encontrado para a simulação.")


except Exception as e:
    st.error(f"Ocorreu um erro inesperado ao processar os dados.")
    st.error(f"Detalhe do erro: {e}")
