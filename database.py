import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Obter credenciais
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Para evitar que o URL e KEY sejam invertidos
if SUPABASE_URL and not SUPABASE_URL.startswith("https://"):
    # Se URL não começa com https://, provavelmente está trocado
    temp = SUPABASE_URL
    SUPABASE_URL = SUPABASE_KEY
    SUPABASE_KEY = temp

def init_connection():
    """Inicializa conexão com Supabase"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Credenciais do Supabase não configuradas. Configure SUPABASE_URL e SUPABASE_KEY como variáveis de ambiente.")
        return None
    
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Erro ao conectar ao Supabase: {e}")
        return None

def get_connection():
    """Retorna conexão ativa"""
    return init_connection()

# [O restante das funções permanece igual]
