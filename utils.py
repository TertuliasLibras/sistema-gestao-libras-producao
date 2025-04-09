import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar
import streamlit as st
import os

# Função para converter lista de dicionários para DataFrame
def list_to_df(data_list):
    if not data_list:
        return pd.DataFrame()
    return pd.DataFrame(data_list)

def load_students_data():
    """Load student data from CSV file"""
    try:
        from database import load_students
        students = load_students()
        return list_to_df(students)
    except Exception as e:
        st.error(f"Erro ao carregar dados dos alunos: {e}")
        return pd.DataFrame()

def load_payments_data():
    """Load payment data from CSV file"""
    try:
        from database import load_payments
        payments = load_payments()
        return list_to_df(payments)
    except Exception as e:
        st.error(f"Erro ao carregar dados de pagamentos: {e}")
        return pd.DataFrame()

def load_internships_data():
    """Load internship data from CSV file"""
    try:
        from database import load_internships
        internships = load_internships()
        return list_to_df(internships)
    except Exception as e:
        st.error(f"Erro ao carregar dados de estágios: {e}")
        return pd.DataFrame()

def save_students_data(df):
    """Save student data to CSV file"""
    try:
        if df is None or df.empty:
            return
        
        from database import save_student
        # Para cada estudante, salvar os dados
        for _, row in df.iterrows():
            student_data = row.to_dict()
            save_student(student_data)
    except Exception as e:
        st.error(f"Erro ao salvar dados dos alunos: {e}")

def save_payments_data(df):
    """Save payment data to CSV file"""
    try:
        if df is None or df.empty:
            return
        
        from database import save_payment
        # Para cada pagamento, salvar os dados
        for _, row in df.iterrows():
            payment_data = row.to_dict()
            save_payment(payment_data)
    except Exception as e:
        st.error(f"Erro ao salvar dados de pagamentos: {e}")
        
def save_internships_data(df):
    """Save internship data to CSV file"""
    try:
        if df is None or df.empty:
            return
        
        from database import save_internship
        # Para cada estágio, salvar os dados
        for _, row in df.iterrows():
            internship_data = row.to_dict()
            save_internship(internship_data)
    except Exception as e:
        st.error(f"Erro ao salvar dados de estágios: {e}")

def get_active_students(students_df):
    """Get active students"""
    if students_df.empty:
        return pd.DataFrame()
    
    if 'status' in students_df.columns:
        return students_df[students_df['status'] == 'active']
    
    # Se não houver coluna status, assumir que todos estão ativos
    return students_df

def get_canceled_students(students_df):
    """Get canceled students"""
    if students_df.empty:
        return pd.DataFrame()
    
    if 'status' in students_df.columns:
        return students_df[students_df['status'] == 'canceled']
    
    # Se não houver coluna status, retornar DataFrame vazio
    return pd.DataFrame()

def format_currency(value):
    """Format value as BRL currency"""
    if pd.isna(value) or value is None:
        return "R$ 0,00"
    
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_phone(phone):
    """Format phone number to standard format"""
    if not phone:
        return ""
        
    # Remover tudo que não for dígito
    digits = ''.join(filter(str.isdigit, str(phone)))
    
    if len(digits) == 11:
        return f"({digits[0:2]}) {digits[2:7]}-{digits[7:11]}"
    elif len(digits) == 10:
        return f"({digits[0:2]}) {digits[2:6]}-{digits[6:10]}"
    else:
        return phone

def get_overdue_payments(students_df, payments_df):
    """Get students with overdue payments"""
    if students_df.empty or payments_df.empty:
        return pd.DataFrame()
    
    # Verificar se as colunas necessárias existem
    required_cols_students = ['phone', 'name', 'monthly_fee']
    required_cols_payments = ['phone', 'due_date', 'status']
    
    if not all(col in students_df.columns for col in required_cols_students) or \
       not all(col in payments_df.columns for col in required_cols_payments):
        return pd.DataFrame()
    
    # Obter apenas estudantes ativos
    active_students = get_active_students(students_df)
    if active_students.empty:
        return pd.DataFrame()
    
    # Obter pagamentos em aberto e atrasados
    today = datetime.now().date()
    overdue_payments = payments_df[
        (payments_df['status'] == 'pending') & 
        (pd.to_datetime(payments_df['due_date']).dt.date < today)
    ]
    
    if overdue_payments.empty:
        return pd.DataFrame()
    
    # Juntar com dados dos estudantes
    result = pd.merge(
        overdue_payments,
        active_students[['phone', 'name', 'monthly_fee']],
        on='phone',
        how='inner'
    )
    
    # Calcular dias de atraso
    result['days_overdue'] = (today - pd.to_datetime(result['due_date']).dt.date).dt.days
    
    return result

def calculate_monthly_revenue(students_df, payments_df, month, year):
    """Calculate projected monthly revenue"""
    if students_df.empty:
        return 0
    
    # Verificar se existe a coluna monthly_fee
    if 'monthly_fee' not in students_df.columns:
        return 0
    
    # Obter apenas estudantes ativos
    active_students = get_active_students(students_df)
    if active_students.empty:
        return 0
    
    # Calcular receita mensal baseada nas mensalidades dos alunos ativos
    total = active_students['monthly_fee'].sum()
    
    return total

def get_student_internship_hours(internships_df, phone):
    """Calculate total internship hours for a student"""
    if internships_df.empty:
        return 0
    
    # Verificar se as colunas necessárias existem
    if not all(col in internships_df.columns for col in ['phone', 'hours']):
        return 0
    
    # Filtrar estágios do estudante
    student_internships = internships_df[internships_df['phone'] == phone]
    
    if student_internships.empty:
        return 0
    
    # Calcular total de horas
    return student_internships['hours'].sum()

def get_student_internship_topics(internships_df, phone):
    """Get all internship topics for a student"""
    if internships_df.empty:
        return []
    
    # Verificar se as colunas necessárias existem
    if not all(col in internships_df.columns for col in ['phone', 'topic']):
        return []
    
    # Filtrar estágios do estudante
    student_internships = internships_df[internships_df['phone'] == phone]
    
    if student_internships.empty:
        return []
    
    # Obter tópicos únicos
    topics = student_internships['topic'].unique().tolist()
    
    return topics

def validate_phone(phone):
    """Validate if phone number is in correct format"""
    if not phone:
        return False
        
    # Remover tudo que não for dígito
    digits = ''.join(filter(str.isdigit, str(phone)))
    
    # Verificar se tem 10 ou 11 dígitos (com ou sem o 9)
    return len(digits) in [10, 11]

def get_months_between_dates(start_date, end_date):
    """Get list of months between two dates"""
    # Garantir que ambos são datetime.datetime
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    
    if isinstance(end_date, str):
        end_date
