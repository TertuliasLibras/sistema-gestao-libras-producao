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
        if df is None:
            return
        
        # Salvar o DataFrame diretamente no CSV, substituindo o arquivo existente
        from database import STUDENTS_FILE
        df.to_csv(STUDENTS_FILE, index=False)
        
        # Log para facilitar a depuração
        st.debug(f"Arquivo de alunos salvo com {len(df)} registros")
    except Exception as e:
        st.error(f"Erro ao salvar dados dos alunos: {e}")

def save_payments_data(df):
    """Save payment data to CSV file"""
    try:
        if df is None:
            return
        
        # Salvar o DataFrame diretamente no CSV, substituindo o arquivo existente
        from database import PAYMENTS_FILE
        df.to_csv(PAYMENTS_FILE, index=False)
        
        # Log para facilitar a depuração
        st.debug(f"Arquivo de pagamentos salvo com {len(df)} registros")
    except Exception as e:
        st.error(f"Erro ao salvar dados de pagamentos: {e}")
        
def save_internships_data(df):
    """Save internship data to CSV file"""
    try:
        if df is None:
            return
        
        # Salvar o DataFrame diretamente no CSV, substituindo o arquivo existente
        from database import INTERNSHIPS_FILE
        df.to_csv(INTERNSHIPS_FILE, index=False)
        
        # Log para facilitar a depuração
        st.debug(f"Arquivo de estágios salvo com {len(df)} registros")
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
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Converter para datetime.date para comparação
    start_date_for_compare = start_date
    if hasattr(start_date, 'date'):
        start_date_for_compare = start_date.date()
    
    end_date_for_compare = end_date
    if hasattr(end_date, 'date'):
        end_date_for_compare = end_date.date()
    
    months = []
    current_date = datetime(start_date.year, start_date.month, 1)
    
    # Use string comparison para evitar problemas de tipo
    current_str = current_date.strftime('%Y-%m')
    end_str = end_date.strftime('%Y-%m')
    
    while current_str <= end_str:
        months.append(current_date)
        
        # Avançar para o próximo mês
        if current_date.month == 12:
            current_date = datetime(current_date.year + 1, 1, 1)
        else:
            current_date = datetime(current_date.year, current_date.month + 1, 1)
        
        current_str = current_date.strftime('%Y-%m')
    
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
    
    # Garantir que enrollment_date é datetime
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
    else:
        # Garantir que end_date é datetime
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
        today = datetime.now().date()
        
        # Obter a data de vencimento como date
        due_date_as_date = due_date
        if hasattr(due_date, 'date'):
            due_date_as_date = due_date.date()
        elif type(due_date) == str:
            try:
                due_date_as_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            except:
                due_date_as_date = due_date
        
        # Comparação de datas usando string para evitar problemas de tipo
        try:
            # Converter para string YYYY-MM-DD para comparação de datas
            if hasattr(due_date_as_date, 'strftime'):
                due_date_str = due_date_as_date.strftime('%Y-%m-%d')
            elif type(due_date_as_date) == str:
                due_date_str = due_date_as_date
            else:
                due_date_str = str(due_date_as_date)
                
            today_str = today.strftime('%Y-%m-%d')
            
            if due_date_str < today_str:
                payment_status = "pending"  # Começar como pendente mesmo se atrasado
        except Exception as e:
            # Em caso de erro, manter como pendente
            payment_status = "pending"
        
        # Formatar a data de vencimento com tratamento de erro
        try:
            if hasattr(due_date, 'strftime'):
                due_date_formatted = due_date.strftime('%Y-%m-%d')
            else:
                due_date_formatted = str(due_date)
        except Exception:
            # Em caso de erro, usar a data atual formatada
            due_date_formatted = datetime.now().strftime('%Y-%m-%d')
            
        payment = {
            "phone": student_phone,
            "amount": monthly_fee,
            "due_date": due_date_formatted,
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
