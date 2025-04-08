import os
import streamlit as st
import hashlib
from datetime import datetime, timedelta
from config import get_logo_path

# Nome da variável de sessão para login
LOGIN_SESSION_VAR = "usuario_autenticado"

# Usuário admin padrão
ADMIN_USER = {
    "username": "admin",
    "password_hash": "0192023a7bbd73250516f069df18b500",  # md5 hash de "admin123"
    "name": "Administrador",
    "level": "admin",
    "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}

def hash_senha(senha):
    """Gera um hash MD5 da senha"""
    return hashlib.md5(senha.encode()).hexdigest()

def verificar_login(usuario, senha):
    """Verifica se o login e senha estão corretos"""
    senha_hash = hash_senha(senha)
    
    # No modo demonstração, só aceita o usuário admin
    if usuario == ADMIN_USER["username"] and senha_hash == ADMIN_USER["password_hash"]:
        st.session_state[LOGIN_SESSION_VAR] = {
            "username": usuario,
            "name": ADMIN_USER["name"],
            "level": ADMIN_USER["level"],
            "last_activity": datetime.now()
        }
        return True
    return False

def verificar_autenticacao():
    """Verifica se o usuário está autenticado e a sessão não expirou"""
    if LOGIN_SESSION_VAR not in st.session_state:
        return False
    
    # Verificar tempo de inatividade (30 minutos)
    last_activity = st.session_state[LOGIN_SESSION_VAR].get("last_activity")
    if last_activity and (datetime.now() - last_activity).total_seconds() > 1800:
        # Sessão expirada
        logout()
        return False
    
    # Atualizar timestamp de última atividade
    st.session_state[LOGIN_SESSION_VAR]["last_activity"] = datetime.now()
    return True

def logout():
    """Realiza o logout do usuário"""
    if LOGIN_SESSION_VAR in st.session_state:
        del st.session_state[LOGIN_SESSION_VAR]

def mostrar_pagina_login():
    """Exibe a página de login"""
    logo_path = get_logo_path()
    
    if logo_path:
        try:
            st.image(logo_path, width=200)
        except Exception as e:
            st.error(f"Erro ao carregar o logo: {e}")
    
    st.title("Sistema de Gestão - Tertúlia Libras")
    st.subheader("Login")
    
    # Formulário de login
    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
        
        if submitted:
            if verificar_login(usuario, senha):
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos!")

def pagina_gerenciar_usuarios():
    """Página para gerenciar usuários"""
    st.title("Gerenciar Usuários")
    st.text("Esta é uma versão demonstrativa. No ambiente Cloud, a funcionalidade de gerenciamento de usuários está desativada.")
