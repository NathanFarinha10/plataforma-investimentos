import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st

# --- MAPEAMENTO DE TICKERS (COM CORREÇÃO) ---
TICKER_MAP = {
    "Caixa": "^IRX",
    "Renda Fixa Brasil": "B5P211.SA",
    "Renda Fixa Internacional": "BND",
    "Ações Brasil": "^BVSP",
    "Ações Internacional": "IVV",
    "Fundos Imobiliários": "IFIX.SA",
    "Alternativos": "GLD"  # <<< CORRIGIDO DE "GOLD" PARA "GLD" (ETF de Ouro)
}

RISK_FREE_RATE = 0.105

# --- FUNÇÃO get_market_data (MAIS ROBUSTA) ---
@st.cache_data(ttl=3600)
def get_market_data(tickers):
    """
    Baixa os dados históricos dos últimos 3 anos.
    Esta versão é robusta para lidar com 1 ou múltiplos tickers.
    """
    data = yf.download(tickers, period="3y")
    
    if data.empty:
        return pd.DataFrame()

    # Acessa os preços de fechamento ajustado.
    adj_close = data.get('Adj Close')

    # Se 'Adj Close' não existir (pode acontecer em erros), retorne DF vazio.
    if adj_close is None:
        return pd.DataFrame()

    # Se apenas um ticker for baixado, yfinance retorna uma Série.
    # Precisamos garantir que o resultado seja sempre um DataFrame.
    if isinstance(adj_close, pd.Series):
        adj_close = adj_close.to_frame(name=tickers[0])
        
    return adj_close

def calculate_portfolio_risk(allocations_df: pd.DataFrame):
    """
    Calcula as métricas de risco para um portfólio com base na sua alocação.
    """
    if allocations_df.empty:
        return None, None

    active_allocations = allocations_df[allocations_df['allocation_pct'] > 0]
    tickers_to_download = {TICKER_MAP[asset]: pct for asset, pct in active_allocations.set_index('asset_class')['allocation_pct'].to_dict().items()}
    
    if not tickers_to_download:
        return None, None

    market_data = get_market_data(list(tickers_to_download.keys()))

    # Se não houver dados de mercado após a tentativa de download, encerre.
    if market_data.empty:
        st.error(f"Não foi possível obter dados de mercado para os tickers: {list(tickers_to_download.keys())}. Verifique se os tickers no TICKER_MAP são válidos.")
        return None, None
        
    market_data.ffill(inplace=True)
    daily_returns = market_data.pct_change().dropna()
    
    # Alinha os pesos com as colunas de retorno, caso algum ticker tenha falhado
    valid_tickers = daily_returns.columns
    weights = np.array([tickers_to_download[ticker] / 100.0 for ticker in valid_tickers])
    # Recalcula a soma dos pesos para normalizar, caso um ticker tenha falhado
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
