import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st # Importamos streamlit para usar o cache

DB_PATH = 'gestora.db'

def initialize_database():
    """
    Verifica e cria o banco de dados e a tabela se não existirem.
    Popula com dados iniciais se a tabela estiver vazia.
    Esta função é segura para ser executada toda vez que o app inicia.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # A cláusula "IF NOT EXISTS" garante que não teremos erro se a tabela já existir.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_name TEXT NOT NULL,
            asset_class TEXT NOT NULL,
            allocation_pct REAL NOT NULL,
            updated_at TEXT NOT NULL,
            batch_id INTEGER NOT NULL 
        )
    ''')

    # Verifica se a tabela está vazia antes de inserir dados iniciais.
    cursor.execute("SELECT COUNT(*) FROM allocations")
    count = cursor.fetchone()[0]

    if count == 0:
        # Se a tabela está vazia, insere os dados do portfólio Conservador.
        initial_allocations = {
            "Conservador": {
                "Caixa": 50.0, "Renda Fixa Brasil": 30.0, "Renda Fixa Internacional": 10.0,
                "Ações Brasil": 5.0, "Ações Internacional": 3.0, "Fundos Imobiliários": 2.0, "Alternativos": 0.0
            }
        }
        portfolio_name = "Conservador"
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        batch_id = 1

        for asset, pct in initial_allocations[portfolio_name].items():
            cursor.execute('''
                INSERT INTO allocations (portfolio_name, asset_class, allocation_pct, updated_at, batch_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (portfolio_name, asset, pct, current_time, batch_id))
        
        conn.commit()

    conn.close()

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@st.cache_data(ttl=300) # Cache de 5 minutos
def get_latest_allocations(portfolio_name):
    """Busca a alocação mais recente para um determinado portfólio."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT MAX(batch_id) FROM allocations WHERE portfolio_name = ?", (portfolio_name,))
    latest_batch_id = cursor.fetchone()[0]
    
    if latest_batch_id is None:
        conn.close()
        return pd.DataFrame()

    query = "SELECT asset_class, allocation_pct FROM allocations WHERE portfolio_name = ? AND batch_id = ?"
    df = pd.read_sql_query(query, conn, params=(portfolio_name, latest_batch_id))
    
    conn.close()
    return df

def save_allocations(portfolio_name, allocations_dict):
    """Salva um novo conjunto de alocações no banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(batch_id) FROM allocations")
    max_batch_id = cursor.fetchone()[0]
    new_batch_id = (max_batch_id or 0) + 1

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for asset, pct in allocations_dict.items():
        cursor.execute('''
            INSERT INTO allocations (portfolio_name, asset_class, allocation_pct, updated_at, batch_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (portfolio_name, asset, pct, current_time, new_batch_id))
    
    conn.commit()
    conn.close()
    st.cache_data.clear() # Limpa o cache após salvar novos dados
