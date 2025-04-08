import os
import pandas as pd
import json
import streamlit as st
from datetime import datetime
import hashlib

# Estrutura de diretórios
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Caminhos dos arquivos
STUDENTS_FILE = os.path.join(DATA_DIR, "students.csv")
PAYMENTS_FILE = os.path.join(DATA_DIR, "payments.csv")
INTERNSHIPS_FILE = os.path.join(DATA_DIR, "internships.csv")
USERS_FILE = os.path.join(DATA_DIR, "users.csv")

# Funções auxiliares
def ensure_files_exist():
    """Garantir que os arquivos de dados existam"""
    # Estudantes
    if not os.path.exists(STUDENTS_FILE):
        pd.DataFrame(columns=[
            'phone', 'name', 'cpf', 'email', 'address', 'enrollment_date', 
            'monthly_fee', 'course_type', 'status', 'comments', 'registration_origin',
            'payment_day', 'payment_plan'
        ]).to_csv(STUDENTS_FILE, index=False)
    
    # Pagamentos
    if not os.path.exists(PAYMENTS_FILE):
        pd.DataFrame(columns=[
            'id', 'phone', 'amount', 'due_date', 'status', 'payment_date', 
            'payment_method', 'month', 'year', 'comments', 
            'installment', 'total_installments'
        ]).to_csv(PAYMENTS_FILE, index=False)
    
    # Estágios
    if not os.path.exists(INTERNSHIPS_FILE):
        pd.DataFrame(columns=[
            'id', 'phone', 'date', 'topic', 'hours', 'location',
            'supervisor', 'description', 'students'
        ]).to_csv(INTERNSHIPS_FILE, index=False)
    
    # Usuários
    if not os.path.exists(USERS_FILE):
        # Criar usuário admin padrão
        admin_user = {
            "username": "admin",
            "name": "Administrador",
            "password_hash": "0192023a7bbd73250516f069df18b500",  # hash de admin123
            "level": "admin",
            "created_at": datetime.now().strftime("%Y-%m-%d")
        }
        pd.DataFrame([admin_user]).to_csv(USERS_FILE, index=False)

# Garantir que os arquivos existam
ensure_files_exist()

# Funções de acesso a dados
def load_students():
    """Carrega todos os estudantes do arquivo CSV"""
    try:
        if os.path.exists(STUDENTS_FILE):
            df = pd.read_csv(STUDENTS_FILE)
            return df.to_dict('records')
        return []
    except Exception as e:
        st.error(f"Erro ao carregar estudantes: {e}")
        return []

def save_student(student_data):
    """Salva um novo estudante no arquivo CSV"""
    try:
        # Carregar dados existentes
        students_df = pd.read_csv(STUDENTS_FILE) if os.path.exists(STUDENTS_FILE) else pd.DataFrame()
        
        # Verificar se o estudante já existe
        if not students_df.empty and 'phone' in students_df.columns and student_data['phone'] in students_df['phone'].values:
            # Atualizar
            students_df.loc[students_df['phone'] == student_data['phone']] = pd.Series(student_data)
        else:
            # Adicionar novo
            new_row = pd.DataFrame([student_data])
            students_df = pd.concat([students_df, new_row], ignore_index=True)
        
        # Salvar
        students_df.to_csv(STUDENTS_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar estudante: {e}")
        return False

def update_student(phone, student_data):
    """Atualiza os dados de um estudante existente"""
    return save_student(student_data)

def delete_student(phone):
    """Exclui um estudante do arquivo CSV"""
    try:
        # Carregar dados existentes
        students_df = pd.read_csv(STUDENTS_FILE) if os.path.exists(STUDENTS_FILE) else pd.DataFrame()
        
        if not students_df.empty and 'phone' in students_df.columns:
            # Remover estudante
            students_df = students_df[students_df['phone'] != phone]
            
            # Salvar
            students_df.to_csv(STUDENTS_FILE, index=False)
        
        return True
    except Exception as e:
        st.error(f"Erro ao excluir estudante: {e}")
        return False

def load_payments():
    """Carrega todos os pagamentos do arquivo CSV"""
    try:
        if os.path.exists(PAYMENTS_FILE):
            df = pd.read_csv(PAYMENTS_FILE)
            return df.to_dict('records')
        return []
    except Exception as e:
        st.error(f"Erro ao carregar pagamentos: {e}")
        return []

def save_payment(payment_data):
    """Salva um novo pagamento no arquivo CSV"""
    try:
        # Carregar dados existentes
        payments_df = pd.read_csv(PAYMENTS_FILE) if os.path.exists(PAYMENTS_FILE) else pd.DataFrame()
        
        # Verificar se já tem ID
        if 'id' in payment_data and payment_data['id'] and not payments_df.empty:
            # Tem ID, então atualizar
            if 'id' in payments_df.columns and payment_data['id'] in payments_df['id'].values:
                payments_df.loc[payments_df['id'] == payment_data['id']] = pd.Series(payment_data)
            else:
                # ID não encontrado, adicionar novo
                if payments_df.empty or 'id' not in payments_df.columns:
                    new_id = 1
                else:
                    new_id = int(payments_df['id'].max()) + 1 if not payments_df.empty else 1
                payment_data['id'] = new_id
                new_row = pd.DataFrame([payment_data])
                payments_df = pd.concat([payments_df, new_row], ignore_index=True)
        else:
            # Não tem ID, criar novo
            if payments_df.empty or 'id' not in payments_df.columns:
                new_id = 1
            else:
                new_id = int(payments_df['id'].max()) + 1 if not payments_df.empty else 1
            payment_data['id'] = new_id
            new_row = pd.DataFrame([payment_data])
            payments_df = pd.concat([payments_df, new_row], ignore_index=True)
        
        # Salvar
        payments_df.to_csv(PAYMENTS_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar pagamento: {e}")
        return False

def update_payment(payment_id, payment_data):
    """Atualiza os dados de um pagamento existente"""
    payment_data['id'] = payment_id
    return save_payment(payment_data)

def delete_payment(payment_id):
    """Exclui um pagamento do arquivo CSV"""
    try:
        # Carregar dados existentes
        payments_df = pd.read_csv(PAYMENTS_FILE) if os.path.exists(PAYMENTS_FILE) else pd.DataFrame()
        
        if not payments_df.empty and 'id' in payments_df.columns:
            # Remover pagamento
            payments_df = payments_df[payments_df['id'] != payment_id]
            
            # Salvar
            payments_df.to_csv(PAYMENTS_FILE, index=False)
        
        return True
    except Exception as e:
        st.error(f"Erro ao excluir pagamento: {e}")
        return False

def delete_student_payments(phone):
    """Exclui todos os pagamentos associados a um estudante"""
    try:
        # Carregar dados existentes
        payments_df = pd.read_csv(PAYMENTS_FILE) if os.path.exists(PAYMENTS_FILE) else pd.DataFrame()
        
        if not payments_df.empty and 'phone' in payments_df.columns:
            # Remover pagamentos do estudante
            payments_df = payments_df[payments_df['phone'] != phone]
            
            # Salvar
            payments_df.to_csv(PAYMENTS_FILE, index=False)
        
        return True
    except Exception as e:
        st.error(f"Erro ao excluir pagamentos do estudante: {e}")
        return False

def load_internships():
    """Carrega todos os estágios do arquivo CSV"""
    try:
        if os.path.exists(INTERNSHIPS_FILE):
            df = pd.read_csv(INTERNSHIPS_FILE)
            return df.to_dict('records')
        return []
    except Exception as e:
        st.error(f"Erro ao carregar estágios: {e}")
        return []

def save_internship(internship_data):
    """Salva um novo estágio no arquivo CSV"""
    try:
        # Carregar dados existentes
        internships_df = pd.read_csv(INTERNSHIPS_FILE) if os.path.exists(INTERNSHIPS_FILE) else pd.DataFrame()
        
        # Verificar se já tem ID
        if 'id' in internship_data and internship_data['id'] and not internships_df.empty:
            # Tem ID, então atualizar
            if 'id' in internships_df.columns and internship_data['id'] in internships_df['id'].values:
                internships_df.loc[internships_df['id'] == internship_data['id']] = pd.Series(internship_data)
            else:
                # ID não encontrado, adicionar novo
                if internships_df.empty or 'id' not in internships_df.columns:
                    new_id = 1
                else:
                    new_id = int(internships_df['id'].max()) + 1 if not internships_df.empty else 1
                internship_data['id'] = new_id
                new_row = pd.DataFrame([internship_data])
                internships_df = pd.concat([internships_df, new_row], ignore_index=True)
        else:
            # Não tem ID, criar novo
            if internships_df.empty or 'id' not in internships_df.columns:
                new_id = 1
            else:
                new_id = int(internships_df['id'].max()) + 1 if not internships_df.empty else 1
            internship_data['id'] = new_id
            new_row = pd.DataFrame([internship_data])
            internships_df = pd.concat([internships_df, new_row], ignore_index=True)
        
        # Salvar
        internships_df.to_csv(INTERNSHIPS_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar estágio: {e}")
        return False

def update_internship(internship_id, internship_data):
    """Atualiza os dados de um estágio existente"""
    internship_data['id'] = internship_id
    return save_internship(internship_data)

def delete_internship(internship_id):
    """Exclui um estágio do arquivo CSV"""
    try:
        # Carregar dados existentes
        internships_df = pd.read_csv(INTERNSHIPS_FILE) if os.path.exists(INTERNSHIPS_FILE) else pd.DataFrame()
        
        if not internships_df.empty and 'id' in internships_df.columns:
            # Remover estágio
            internships_df = internships_df[internships_df['id'] != internship_id]
            
            # Salvar
            internships_df.to_csv(INTERNSHIPS_FILE, index=False)
        
        return True
    except Exception as e:
        st.error(f"Erro ao excluir estágio: {e}")
        return False

def authenticate_user(username, password_hash):
    """Autentica um usuário com base no nome de usuário e senha hasheada"""
    try:
        # Carregar usuários
        if os.path.exists(USERS_FILE):
            users_df = pd.read_csv(USERS_FILE)
            
            # Buscar usuário
            user = users_df[(users_df['username'] == username) & (users_df['password_hash'] == password_hash)]
            
            if not user.empty:
                return user.iloc[0].to_dict()
        
        # Verificação de emergência para admin
        if username == "admin" and password_hash == "0192023a7bbd73250516f069df18b500":  # hash de admin123
            return {"username": "admin", "name": "Administrador", "level": "admin"}
        
        return None
    except Exception as e:
        st.error(f"Erro na autenticação: {e}")
        
        # Verificação de emergência para admin
        if username == "admin" and password_hash == "0192023a7bbd73250516f069df18b500":  # hash de admin123
            return {"username": "admin", "name": "Administrador", "level": "admin"}
        
        return None

def load_users():
    """Carrega todos os usuários do arquivo CSV"""
    try:
        if os.path.exists(USERS_FILE):
            df = pd.read_csv(USERS_FILE)
            return df.to_dict('records')
        
        # Retornar usuário admin padrão
        return [{"username": "admin", "name": "Administrador", "level": "admin", "password_hash": "0192023a7bbd73250516f069df18b500"}]
    except Exception as e:
        st.error(f"Erro ao carregar usuários: {e}")
        # Retornar usuário admin padrão
        return [{"username": "admin", "name": "Administrador", "level": "admin", "password_hash": "0192023a7bbd73250516f069df18b500"}]

def save_user(user_data):
    """Salva um novo usuário no arquivo CSV"""
    try:
        # Carregar dados existentes
        users_df = pd.read_csv(USERS_FILE) if os.path.exists(USERS_FILE) else pd.DataFrame()
        
        # Verificar se o usuário já existe
        if not users_df.empty and 'username' in users_df.columns and user_data['username'] in users_df['username'].values:
            # Atualizar
            users_df.loc[users_df['username'] == user_data['username']] = pd.Series(user_data)
        else:
            # Adicionar novo
            new_row = pd.DataFrame([user_data])
            users_df = pd.concat([users_df, new_row], ignore_index=True)
        
        # Salvar
        users_df.to_csv(USERS_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar usuário: {e}")
        return False

def update_user(user_id, user_data):
    """Atualiza os dados de um usuário existente"""
    try:
        # Carregar dados existentes
        users_df = pd.read_csv(USERS_FILE) if os.path.exists(USERS_FILE) else pd.DataFrame()
        
        if not users_df.empty and 'id' in users_df.columns:
            # Atualizar usuário
            users_df.loc[users_df['id'] == user_id] = pd.Series(user_data)
            
            # Salvar
            users_df.to_csv(USERS_FILE, index=False)
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao atualizar usuário: {e}")
        return False

def delete_user(user_id):
    """Exclui um usuário do arquivo CSV"""
    try:
        # Carregar dados existentes
        users_df = pd.read_csv(USERS_FILE) if os.path.exists(USERS_FILE) else pd.DataFrame()
        
        if not users_df.empty and 'id' in users_df.columns:
            # Remover usuário
            users_df = users_df[users_df['id'] != user_id]
            
            # Salvar
            users_df.to_csv(USERS_FILE, index=False)
        
        return True
    except Exception as e:
        st.error(f"Erro ao excluir usuário: {e}")
        return False
