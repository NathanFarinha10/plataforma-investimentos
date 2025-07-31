import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st

# --- MAPEAMENTO DE TICKERS ---
# ATENÇÃO: Este é o passo mais importante a ser customizado pela sua gestora.
# Cada classe de ativo precisa ser mapeada para um ticker do Yahoo Finance
# que a represente bem como um benchmark.
TICKER_MAP = {
    "Caixa": "^IRX",  # Proxy para Renda Fixa de curtíssimo prazo (Letra do Tesouro Americano de 13 semanas)
    "Renda Fixa Brasil": "B5P211.SA", # ETF de IMA-B 5+
    "Renda Fixa Internacional": "BND", # ETF Vanguard Total Bond Market (EUA)
    "Ações Brasil": "^BVSP", # Índice Bovespa
    "Ações Internacional": "IVV", # S&P 500 ETF
    "Fundos Imobiliários": "IFIX.SA", # Índice de Fundos Imobiliários
    "Alternativos": "GOLD" # ETF de Ouro
}

# Defina a taxa livre de risco anual para o cálculo do Sharpe Ratio.
# Exemplo: Usando a taxa Selic aproximada. Este valor deve ser atualizado periodicamente.
RISK_FREE_RATE = 0.105 # 10.5% a.a.

@st.cache_data(ttl=3600) # Cache de 1 hora para os dados do yfinance
def get_market_data(tickers):
    """Baixa os dados históricos dos últimos 3 anos para os tickers fornecidos."""
    return yf.download(tickers, period="3y")['Adj Close']

def calculate_portfolio_risk(allocations_df: pd.DataFrame):
    """
    Calcula as métricas de risco para um portfólio com base na sua alocação.
    """
    if allocations_df.empty:
        return None, None

    # Filtra alocações maiores que zero
    active_allocations = allocations_df[allocations_df['allocation_pct'] > 0]
    
    # Mapeia as classes de ativo para tickers
    tickers_to_download = {TICKER_MAP[asset]: pct for asset, pct in active_allocations.set_index('asset_class')['allocation_pct'].to_dict().items()}
    
    if not tickers_to_download:
        return None, None

    # Baixa os dados de mercado
    market_data = get_market_data(list(tickers_to_download.keys()))
    market_data.ffill(inplace=True) # Preenche dados faltantes (ex: feriados)

    # Calcula os retornos diários
    daily_returns = market_data.pct_change().dropna()
    
    # Pega os pesos na ordem correta das colunas do dataframe de retornos
    weights = np.array([tickers_to_download[ticker] / 100.0 for ticker in daily_returns.columns])

    # Calcula os retornos diários do portfólio
    portfolio_daily_returns = daily_returns.dot(weights)
    
    # Calcula as métricas
    # 1. Volatilidade Anualizada
    volatility = portfolio_daily_returns.std() * np.sqrt(252)

    # 2. Sharpe Ratio Anualizado
    avg_daily_return = portfolio_daily_returns.mean()
    avg_annual_return = avg_daily_return * 252
    sharpe_ratio = (avg_annual_return - RISK_FREE_RATE) / volatility if volatility != 0 else 0

    # 3. Value at Risk (VaR) Histórico (95% de confiança, para 1 dia)
    var_95 = np.percentile(portfolio_daily_returns, 5)

    risk_metrics = {
        "Volatilidade Anualizada": volatility,
        "Sharpe Ratio": sharpe_ratio,
        "VaR 95% (1 dia)": var_95
    }

    # Calcula o retorno acumulado para o gráfico
    cumulative_returns = (1 + portfolio_daily_returns).cumprod() - 1
    
    return risk_metrics, cumulative_returns
