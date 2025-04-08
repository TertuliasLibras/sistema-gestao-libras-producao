import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import calendar

# Criar diretórios necessários
os.makedirs("data", exist_ok=True)
os.makedirs("backup", exist_ok=True)
os.makedirs("assets/images", exist_ok=True)

# Tentar importar login
try:
    from login import verificar_autenticacao, mostrar_pagina_login, logout
except ImportError as e:
    st.error(f"Erro ao importar módulo de login: {e}")
    st.stop()

# Tentar importar utils
try:
    from utils import (
        load_students_data,
        load_payments_data,
        load_internships_data,
        format_currency,
        calculate_monthly_revenue,
        get_overdue_payments,
        get_active_students
    )
except ImportError as e:
    st.error(f"Erro ao importar módulos: {e}")
    
    # Funções vazias para substituir
    def load_students_data():
        return pd.DataFrame()
    
    def load_payments_data():
        return pd.DataFrame()
    
    def load_internships_data():
        return pd.DataFrame()
    
    def format_currency(value):
        return f"R$ {value:.2f}"
    
    def calculate_monthly_revenue(*args):
        return 0
    
    def get_overdue_payments(*args):
        return pd.DataFrame()
    
    def get_active_students(*args):
        return pd.DataFrame()

# Importar módulo de backup
try:
    from backup import create_backup, list_backups, restore_backup, download_backup
except ImportError:
    # Funções vazias para substituir
    def create_backup():
        st.info("Módulo de backup não disponível.")
        return None
    
    def list_backups():
        return []
    
    def restore_backup(*args):
        st.info("Módulo de backup não disponível.")
        return False
    
    def download_backup(*args):
        st.info("Módulo de backup não disponível.")
        return None

# Configuração da página
st.set_page_config(
    page_title="Tertúlia Libras - Sistema de Gestão",
    page_icon="🤟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Verificar autenticação
if not verificar_autenticacao():
    mostrar_pagina_login()
else:
    # Sidebar
    with st.sidebar:
        st.write(f"Bem-vindo, {st.session_state.get('nome', 'Usuário')}!")
        
        # Menu de backup
        if st.session_state.get('nivel') == 'admin':
            st.subheader("Backup e Restauração")
            backup_action = st.radio(
                "Ações de Backup:",
                ["Nenhuma", "Criar Backup", "Restaurar Backup", "Baixar Backup"]
            )
            
            if backup_action == "Criar Backup":
                if st.button("Criar Backup Agora"):
                    backup_path = create_backup()
                    if backup_path:
                        st.success(f"Backup criado com sucesso!")
            
            elif backup_action == "Restaurar Backup":
                backups = list_backups()
                if backups:
                    backup_options = [b["name"] + " - " + b["timestamp"] for b in backups]
                    selected_backup = st.selectbox("Selecione um backup:", backup_options)
                    
                    if st.button("Restaurar Backup Selecionado"):
                        selected_idx = backup_options.index(selected_backup)
                        backup_folder = backups[selected_idx]["folder"]
                        
                        if restore_backup(backup_folder):
                            st.success("Backup restaurado com
