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
                            st.success("Backup restaurado com sucesso! Recarregando...")
                            st.rerun()
                else:
                    st.info("Nenhum backup disponível.")
            
            elif backup_action == "Baixar Backup":
                backups = list_backups()
                if backups:
                    backup_options = [b["name"] + " - " + b["timestamp"] for b in backups]
                    selected_backup = st.selectbox("Selecione um backup para baixar:", backup_options)
                    
                    selected_idx = backup_options.index(selected_backup)
                    backup_folder = backups[selected_idx]["folder"]
                    
                    backup_data = download_backup(backup_folder)
                    if backup_data:
                        st.download_button(
                            label="Baixar Backup",
                            data=backup_data,
                            file_name=f"{backups[selected_idx]['name']}.zip",
                            mime="application/zip"
                        )
                else:
                    st.info("Nenhum backup disponível.")
        
        # Botão de logout
        if st.button("Sair"):
            logout()
            st.rerun()
    
    # Dashboard
    st.title("Dashboard")
    
    try:
        # Carregar dados
        students_df = load_students_data()
        payments_df = load_payments_data()
        internships_df = load_internships_data()
        
        # Estatísticas principais
        total_students = len(students_df) if not students_df.empty else 0
        active_students = len(get_active_students(students_df)) if not students_df.empty else 0
        
        # Calcular receita mensal
        current_month = datetime.now().month
        current_year = datetime.now().year
        monthly_revenue = calculate_monthly_revenue(students_df, payments_df, current_month, current_year)
        
        # Mostrar estatísticas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total de Alunos", value=total_students)
        with col2:
            st.metric(label="Alunos Ativos", value=active_students)
        with col3:
            st.metric(label="Receita Mensal Esperada", value=format_currency(monthly_revenue))
        
        # Alunos com pagamentos atrasados
        st.subheader("Alunos com Pagamentos Atrasados")
        overdue_df = get_overdue_payments(students_df, payments_df)
        
        if not overdue_df.empty:
            # Limitar colunas exibidas
            display_cols = ['name', 'phone', 'days_overdue', 'monthly_fee']
            if all(col in overdue_df.columns for col in display_cols):
                overdue_display = overdue_df[display_cols].copy()
                
                # Formatar valores
                overdue_display['days_overdue'] = overdue_display['days_overdue'].apply(lambda x: f"{x} dias")
                if 'monthly_fee' in overdue_display.columns:
                    overdue_display['monthly_fee'] = overdue_display['monthly_fee'].apply(format_currency)
                
                st.dataframe(overdue_display)
            else:
                st.info("Dados de pagamentos atrasados não contêm todas as colunas necessárias.")
        else:
            st.info("Não há alunos com pagamentos atrasados.")
            
        # Mostrar algumas estatísticas adicionais
        st.subheader("Visão Geral do Sistema")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribuição de alunos por tipo de curso
            if not students_df.empty and 'course_type' in students_df.columns:
                course_counts = students_df['course_type'].value_counts().reset_index()
                course_counts.columns = ['Tipo de Curso', 'Quantidade']
                
                fig = px.pie(
                    course_counts,
                    values='Quantidade',
                    names='Tipo de Curso',
                    title='Distribuição por Tipo de Curso'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados suficientes para mostrar a distribuição por tipo de curso.")
        
        with col2:
            # Status dos pagamentos do mês atual
            if not payments_df.empty and 'status' in payments_df.columns:
                current_month_payments = payments_df[
                    (payments_df['month'] == current_month) & 
                    (payments_df['year'] == current_year)
                ]
                
                if not current_month_payments.empty:
                    status_counts = current_month_payments['status'].value_counts().reset_index()
                    status_counts.columns = ['Status', 'Quantidade']
                    
                    # Traduzir status
                    status_map = {
                        'pending': 'Pendente',
                        'paid': 'Pago',
                        'overdue': 'Atrasado'
                    }
                    
                    status_counts['Status'] = status_counts['Status'].map(status_map)
                    
                    fig = px.bar(
                        status_counts,
                        x='Status',
                        y='Quantidade',
                        title=f'Status dos Pagamentos - {calendar.month_name[current_month]}/{current_year}',
                        color='Status',
                        color_discrete_map={
                            'Pago': '#28a745',
                            'Pendente': '#007bff',
                            'Atrasado': '#dc3545'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"Sem dados de pagamentos para {calendar.month_name[current_month]}/{current_year}.")
            else:
                st.info("Sem dados suficientes para mostrar o status dos pagamentos.")
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.info("Esta é uma versão demonstrativa. Algumas funcionalidades podem não estar disponíveis.")
