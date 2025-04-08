import os
import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime, timedelta
from config import get_logo_path
from database import authenticate_user, load_users, save_user, update_user, delete_user

# Nome da variável de sessão para login
LOGIN_SESSION_VAR = "usuario_autenticado"

def hash_senha(senha):
    """Gera um hash MD5 da senha"""
    return hashlib.md5(senha.encode()).hexdigest()

def verificar_login(usuario, senha):
    """Verifica se o login e senha estão corretos"""
    senha_hash = hash_senha(senha)
    user = authenticate_user(usuario, senha_hash)
    
    if user:
        st.session_state[LOGIN_SESSION_VAR] = {
            "username": usuario,
            "name": user.get("name", "Usuário"),
            "level": user.get("level", "user"),
            "last_activity": datetime.now()
        }
        return True
    return False

# [O restante das funções permanece igual]
