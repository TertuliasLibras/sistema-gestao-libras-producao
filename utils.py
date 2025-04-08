import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar
import streamlit as st
import os

# Tentar importar funções do database
try:
    from database import (
        load_students, 
        load_payments, 
        load_internships,
        save_student, 
        update_student,
        save_payment, 
        save_internship,
        delete_student,
        delete_student_payments
    )
except ImportError as e:
    st.error(f"Erro ao importar módulo database: {e}")
    
    # Funções mock para caso de falha
    def load_students():
        return []
    
    def load_payments():
        return []
    
    def load_internships():
        return []
    
    def save_student(student_data):
        return False
    
    def update_student(phone, student_data):
        return False
    
    def save_payment(payment_data):
        return False
    
    def save_internship(internship_data):
        return False
    
    def delete_student(phone):
        return False
    
    def delete_student_payments(phone):
        return False

# Função para converter lista de dicionários para DataFrame
def list_to_df(data_list):
    if not data_list:
        return pd.DataFrame()
    return pd.DataFrame(data_list)

def load_students_data():
    """Load student data from Supabase"""
    students = load_students()
    return list_to_df(students)

def load_payments_data():
    """Load payment data from Supabase"""
    payments = load_payments()
    return list_to_df(payments)

def load_internships_data():
    """Load internship data from Supabase"""
    internships = load_internships()
    return list_to_df(internships)

def save_students_data(df):
    """Save student data to Supabase"""
    # Converter DataFrame para lista de dicionários
    if df is None or df.empty:
        return
        
    # Para cada estudante, verificar se já existe e atualizar/inserir
    for _, row in df.iterrows():
        student_data = row.to_dict()
        save_student(student_data)

def save_payments_data(df):
    """Save payment data to Supabase"""
    if df is None or df.empty:
        return
        
    # Excluir pagamentos anteriores e inserir todos novamente
    # (abordagem mais simples para garantir sincronização)
    for _, row in df.iterrows():
        payment_data = row.to_dict()
        save_payment(payment_data)
        
def save_internships_data(df):
    """Save internship data to Supabase"""
    if df is None or df.empty:
        return
        
    # Para cada estágio, verificar se já existe e atualizar/inserir
    for _, row in df.iterrows():
        internship_data = row.to_dict()
        save_internship(internship_data)

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
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    months = []
    current_date = start_date.replace(day=1)
    
    while current_date <= end_date:
        months.append(current_date)
        
        # Avançar para o próximo mês
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    return months

def generate_monthly_payments(student_phone, monthly_fee, enrollment_date, payment_plan=12, end_date=None, due_day=10):
    """Generate monthly payment records for a student based on payment plan
    
    Args:
        student_phone: Phone number of student
        monthly_fee: Monthly fee amount
        enrollment_date: Date of enrollment
        payment_plan: Number of installments (default: 12)
        end_date: Optional end date (if not provided, will calculate based on payment_plan)
        due_day: Day of the month for payment due date (default: 10)
    """
    # Validar argumentos
    if not student_phone or not monthly_fee:
        return []
    
    # Converter enrollment_date para datetime se for string
    if isinstance(enrollment_date, str):
        enrollment_date = datetime.strptime(enrollment_date, '%Y-%m-%d')
    
    # Se due_day for inválido, usar 10 como padrão
    if not due_day or due_day < 1 or due_day > 28:
        due_day = 10
    
    # Calcular end_date se não fornecido
    if not end_date:
        # Adicionar payment_plan meses à data de matrícula
        if enrollment_date.month + payment_plan <= 12:
            end_month = enrollment_date.month + payment_plan
            end_year = enrollment_date.year
        else:
            extra_years = (enrollment_date.month + payment_plan - 1) // 12
            end_month = (enrollment_date.month + payment_plan - 1) % 12 + 1
            end_year = enrollment_date.year + extra_years
        
        # Último dia do mês final
        _, last_day = calendar.monthrange(end_year, end_month)
        end_date = datetime(end_year, end_month, min(enrollment_date.day, last_day))
    
    # Converter end_date para datetime se for string
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Gerar lista de meses entre as datas
    months = get_months_between_dates(enrollment_date, end_date)
    
    # Criar registros de pagamento para cada mês
    payments = []
    
    for month_date in months:
        # Determinar data de vencimento
        # Se for o primeiro mês e o dia de vencimento já passou, usar o dia da matrícula
        if month_date.month == enrollment_date.month and month_date.year == enrollment_date.year and enrollment_date.day > due_day:
            due_date = enrollment_date
        else:
            # Verificar quantos dias tem o mês
            _, last_day = calendar.monthrange(month_date.year, month_date.month)
            due_date = datetime(month_date.year, month_date.month, min(due_day, last_day))
        
        # Verificar se o pagamento está atrasado
        payment_status = "pending"
        if due_date.date() < datetime.now().date():
            payment_status = "pending"  # Começar como pendente mesmo se atrasado
        
        payment = {
            "phone": student_phone,
            "amount": monthly_fee,
            "due_date": due_date.strftime('%Y-%m-%d'),
            "payment_date": None,
            "status": payment_status,
            "payment_method": "",
            "month": month_date.month,
            "year": month_date.year,
            "installment": months.index(month_date) + 1,
            "total_installments": len(months)
        }
        
        payments.append(payment)
    
    return payments
