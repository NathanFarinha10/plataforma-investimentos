# utils/db_functions.py
import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st

DB_PATH = 'gestora.db'

def initialize_database():
    """Verifica e cria o banco de dados e as tabelas se não existirem."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabela de Alocações
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

    # Tabela para as Análises de Mercado
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            summary TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    # Popula a tabela 'allocations' se estiver vazia
    cursor.execute("SELECT COUNT(*) FROM allocations")
    if cursor.fetchone()[0] == 0:
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

@st.cache_data(ttl=300)
def get_latest_allocations(portfolio_name):
    """Busca a alocação mais recente para um determinado portfólio."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(batch_id) FROM allocations WHERE portfolio_name = ?", (portfolio_name,))
        latest_batch_id = cursor.fetchone()[0]
        if latest_batch_id is None:
            return pd.DataFrame()
        query = "SELECT asset_class, allocation_pct FROM allocations WHERE portfolio_name = ? AND batch_id = ?"
        df = pd.read_sql_query(query, conn, params=(portfolio_name, latest_batch_id))
        return df
    finally:
        conn.close()

def save_allocations(portfolio_name, allocations_dict):
    """Salva um novo conjunto de alocações no banco de dados."""
    conn = get_db_connection()
    try:
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
    finally:
        conn.close()
    st.cache_data.clear()

def save_analysis(title, source, summary, author):
    """Salva uma nova análise de mercado no banco de dados."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO analyses (title, source, summary, author, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, source, summary, author, current_time))
        conn.commit()
    finally:
        conn.close()
    st.cache_data.clear()

@st.cache_data(ttl=300)
def get_all_analyses():
    """Busca todas as análises salvas, da mais recente para a mais antiga."""
    conn = get_db_connection()
    try:
        query = "SELECT title, source, summary, author, created_at FROM analyses ORDER BY created_at DESC"
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()
