import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar
import streamlit as st
import os
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

# [O restante das funções permanece igual]
