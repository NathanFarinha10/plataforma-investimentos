import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st

# --- MAPEAMENTO DE TICKERS (COM SUGESTÃO DE MELHORIA) ---
# O ticker ^IRX (título do tesouro americano) pode ser instável.
# SHV é um ETF de títulos de curto prazo, uma proxy mais estável para "Caixa".
TICKER_MAP = {
    "Caixa": "SHV",  # <<< TROCADO DE ^IRX PARA SHV (ETF mais estável)
    "Renda Fixa Brasil": "B5P211.SA",
    "Renda Fixa Internacional": "BND",
    "Ações Brasil": "^BVSP",
    "Ações Internacional": "IVV",
    "Fundos Imobiliários": "IFIX.SA",
    "Alternativos": "GLD"
}

RISK_FREE_RATE = 0.105

# --- FUNÇÃO get_market_data (VERSÃO FINAL, ROBUSTA) ---
@st.cache_data(ttl=3600)
def get_market_data(tickers):
    """
    Baixa os dados históricos ticker por ticker para máxima robustez.
    Se um ticker falhar, ele exibe o erro detalhado.
    """
    all_data = []
    for ticker in tickers:
        try:
            data = yf.download(ticker, period="3y", progress=False)
            if data.empty:
                raise ValueError("DataFrame vazio retornado pelo yfinance.")
            
            adj_close = data['Adj Close'].rename(ticker)
            all_data.append(adj_close)

        except Exception as e:
            # MUDANÇA IMPORTANTE: Exibe o erro real na tela
            st.error(f"Falha ao obter dados para '{ticker}': {e}")

    if not all_data:
        return pd.DataFrame()

    return pd.concat(all_data, axis=1)


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
    
    if market_data.empty:
        # Este erro só aparecerá agora se NENHUM ticker funcionar
        st.error("Não foi possível obter dados de mercado para nenhum dos ativos do portfólio.")
        return None, None
        
    market_data.ffill(inplace=True)
    daily_returns = market_data.pct_change().dropna()
    
    # Alinha os pesos com as colunas de retorno, caso algum ticker tenha falhado
    valid_tickers = daily_returns.columns
    if len(valid_tickers) == 0:
        st.error("Não há dados de retorno válidos para calcular o risco.")
        return None, None
        
    weights = np.array([tickers_to_download[ticker] / 100.0 for ticker in valid_tickers])
    # Recalcula a soma dos pesos para normalizar, caso um ticker tenha falhado
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
