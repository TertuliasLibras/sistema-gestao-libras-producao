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

def load_students():
    """Carrega todos os estudantes do banco de dados"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        response = conn.table('students').select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao carregar estudantes: {e}")
        return []

def save_student(student_data):
    """Salva um novo estudante no banco de dados"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        # Verificar se o aluno já existe
        existing = conn.table('students').select("*").eq('phone', student_data['phone']).execute()
        
        if existing.data and len(existing.data) > 0:
            # Atualizar
            response = conn.table('students').update(student_data).eq('phone', student_data['phone']).execute()
        else:
            # Inserir
            response = conn.table('students').insert(student_data).execute()
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar estudante: {e}")
        return False

def update_student(phone, student_data):
    """Atualiza os dados de um estudante existente"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        response = conn.table('students').update(student_data).eq('phone', phone).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar estudante: {e}")
        return False

def delete_student(phone):
    """Exclui um estudante do banco de dados"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        response = conn.table('students').delete().eq('phone', phone).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir estudante: {e}")
        return False

def load_payments():
    """Carrega todos os pagamentos do banco de dados"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        response = conn.table('payments').select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao carregar pagamentos: {e}")
        return []

def save_payment(payment_data):
    """Salva um novo pagamento no banco de dados"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        # Se tiver ID, atualiza, senão insere
        if 'id' in payment_data and payment_data['id']:
            response = conn.table('payments').update(payment_data).eq('id', payment_data['id']).execute()
        else:
            response = conn.table('payments').insert(payment_data).execute()
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar pagamento: {e}")
        return False

def update_payment(payment_id, payment_data):
    """Atualiza os dados de um pagamento existente"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        response = conn.table('payments').update(payment_data).eq('id', payment_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar pagamento: {e}")
        return False

def delete_payment(payment_id):
    """Exclui um pagamento do banco de dados"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        response = conn.table('payments').delete().eq('id', payment_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir pagamento: {e}")
        return False

def delete_student_payments(phone):
    """Exclui todos os pagamentos associados a um estudante"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        response = conn.table('payments').delete().eq('phone', phone).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir pagamentos do estudante: {e}")
        return False

def load_internships():
    """Carrega todos os estágios do banco de dados"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        response = conn.table('internships').select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao carregar estágios: {e}")
        return []

def save_internship(internship_data):
    """Salva um novo estágio no banco de dados"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        # Se tiver ID, atualiza, senão insere
        if 'id' in internship_data and internship_data['id']:
            response = conn.table('internships').update(internship_data).eq('id', internship_data['id']).execute()
        else:
            response = conn.table('internships').insert(internship_data).execute()
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar estágio: {e}")
        return False

def update_internship(internship_id, internship_data):
    """Atualiza os dados de um estágio existente"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        response = conn.table('internships').update(internship_data).eq('id', internship_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar estágio: {e}")
        return False

def delete_internship(internship_id):
    """Exclui um estágio do banco de dados"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        response = conn.table('internships').delete().eq('id', internship_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir estágio: {e}")
        return False

def authenticate_user(username, password_hash):
    """Autentica um usuário com base no nome de usuário e senha hasheada"""
    conn = get_connection()
    if not conn:
        # Autenticação de emergência para admin
        if username == "admin" and password_hash == "0192023a7bbd73250516f069df18b500":  # hash de admin123
            return {"username": "admin", "name": "Administrador", "level": "admin"}
        return None
    
    try:
        response = conn.table('users').select("*").eq('username', username).eq('password_hash', password_hash).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        
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
    """Carrega todos os usuários do banco de dados"""
    conn = get_connection()
    if not conn:
        # Retornar usuário admin padrão
        return [{"username": "admin", "name": "Administrador", "level": "admin", "password_hash": "0192023a7bbd73250516f069df18b500"}]
    
    try:
        response = conn.table('users').select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Erro ao carregar usuários: {e}")
        # Retornar usuário admin padrão
        return [{"username": "admin", "name": "Administrador", "level": "admin", "password_hash": "0192023a7bbd73250516f069df18b500"}]

def save_user(user_data):
    """Salva um novo usuário no banco de dados"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        # Verificar se o usuário já existe
        existing = conn.table('users').select("*").eq('username', user_data['username']).execute()
        
        if existing.data and len(existing.data) > 0:
            # Atualizar
            response = conn.table('users').update(user_data).eq('username', user_data['username']).execute()
        else:
            # Inserir
            response = conn.table('users').insert(user_data).execute()
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar usuário: {e}")
        return False

def update_user(user_id, user_data):
    """Atualiza os dados de um usuário existente"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        response = conn.table('users').update(user_data).eq('id', user_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar usuário: {e}")
        return False

def delete_user(user_id):
    """Exclui um usuário do banco de dados"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        response = conn.table('users').delete().eq('id', user_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir usuário: {e}")
        return False
