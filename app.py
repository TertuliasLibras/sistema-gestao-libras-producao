import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import calendar
from utils import (
    load_students_data,
    load_payments_data,
    load_internships_data,
    format_currency,
    calculate_monthly_revenue,
    get_overdue_payments,
    get_active_students
)
from login import verificar_autenticacao, mostrar_pagina_login, logout

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
    # Dashboard
    st.title("Dashboard")
    
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
    
    # Botão de logout
    if st.sidebar.button("Sair"):
        logout()
        st.rerun()
