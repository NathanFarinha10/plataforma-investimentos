import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st

# --- MAPEAMENTO DE TICKERS ---
TICKER_MAP = {
    "Caixa": "SHV",
    "Renda Fixa Brasil": "B5P211.SA",
    "Renda Fixa Internacional": "BND",
    "Ações Brasil": "^BVSP",
    "Ações Internacional": "IVV",
    "Fundos Imobiliários": "IFIX.SA",
    "Alternativos": "GLD"
}

RISK_FREE_RATE = 0.105

# --- FUNÇÃO get_market_data (VERSÃO FINAL COM FALLBACK) ---
@st.cache_data(ttl=3600)
def get_market_data(tickers):
    """
    Baixa dados ticker por ticker e os une de forma segura.
    """
    all_series = {}  # Usaremos um dicionário para armazenar as séries de preços
    for ticker in tickers:
        try:
            data = yf.download(ticker, period="3y", progress=False)
            if data.empty:
                raise ValueError("DataFrame vazio.")
            
            price_series = None
            # Tenta usar 'Adj Close', se falhar, usa 'Close'
            if 'Adj Close' in data.columns:
                price_series = data['Adj Close']
            elif 'Close' in data.columns:
                st.info(f"Usando 'Close' como fallback para o ticker '{ticker}'.")
                price_series = data['Close']
            else:
                raise ValueError(f"Não foi possível encontrar 'Adj Close' ou 'Close'.")

            # Adiciona a série ao dicionário, com o ticker como a chave
            all_series[ticker] = price_series

        except Exception as e:
            st.warning(f"Não foi possível processar dados para o ticker '{ticker}'. Erro: {e}")

    if not all_series:
        return pd.DataFrame()

    # O pd.concat irá usar as chaves do dicionário como nomes das colunas
    return pd.concat(all_series, axis=1)


def calculate_portfolio_risk(allocations_df: pd.DataFrame):
    """
    Calcula as métricas de risco para um portfólio com base na sua alocação.
    """
    if allocations_df.empty:
        return None, None

    active_allocations = allocations_df[allocations_df['allocation_pct'] > 0]
    tickers_to_download = {TICKER_MAP.get(asset): pct for asset, pct in active_allocations.set_index('asset_class')['allocation_pct'].to_dict().items() if TICKER_MAP.get(asset)}
    
    if not tickers_to_download:
        return None, None

    market_data = get_market_data(list(tickers_to_download.keys()))
    
    if market_data.empty:
        st.error("Não foi possível obter dados de mercado para nenhum dos ativos do portfólio.")
        return None, None
        
    market_data.ffill(inplace=True)
    daily_returns = market_data.pct_change().dropna()
    
    valid_tickers = daily_returns.columns
    if len(valid_tickers) == 0:
        st.error("Não há dados de retorno válidos para calcular o risco.")
        return None, None
        
    # --- LINHA CORRIGIDA ---
    # Usando colchetes [ticker] para acessar o dicionário corretamente.
    weights = np.array([tickers_to_download[ticker] / 100.0 for ticker in valid_tickers])
    
    if weights.sum() > 0:
      weights /= weights.sum()

    portfolio_daily_returns = daily_returns.dot(weights)
    
    volatility = portfolio_daily_returns.std() * np.sqrt(252)
    avg_annual_return = portfolio_daily_returns.mean() * 252
    sharpe_ratio = (avg_annual_return - RISK_FREE_RATE) / volatility if volatility != 0 else 0
    var_95 = np.percentile(portfolio_daily_returns, 5)

    risk_metrics = {
        "Volatilidade Anualizada": volatility,
        "Sharpe Ratio": sharpe_ratio,
        "VaR 95% (1 dia)": var_95
    }

    cumulative_returns = (1 + portfolio_daily_returns).cumprod() - 1
    
    return risk_metrics, cumulative_returns
