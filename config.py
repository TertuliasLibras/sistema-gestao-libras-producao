import os
import streamlit as st
import json
import shutil
from datetime import datetime

# Diretórios
CONFIG_DIR = "config"
os.makedirs(CONFIG_DIR, exist_ok=True)

# Arquivos
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DEFAULT_LOGO_PATH = os.path.join("assets", "images", "logo.png")
os.makedirs(os.path.dirname(DEFAULT_LOGO_PATH), exist_ok=True)

# Configuração padrão
DEFAULT_CONFIG = {
    "logo_path": DEFAULT_LOGO_PATH,
    "system_name": "Tertúlia Libras - Sistema de Gestão",
    "default_payment_day": 10,
    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

def load_config():
    """Carregar configurações do sistema"""
    # Verificar se o arquivo existe
    if not os.path.exists(CONFIG_FILE):
        # Criar configuração padrão
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        # Carregar do arquivo
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        # Verificar se todas as chaves necessárias existem
        for key in DEFAULT_CONFIG:
            if key not in config:
                config[key] = DEFAULT_CONFIG[key]
        
        return config
    except Exception as e:
        st.error(f"Erro ao carregar configurações: {e}")
        return DEFAULT_CONFIG

def save_config(config_data):
    """Salvar configurações do sistema"""
    try:
        # Atualizar timestamp
        config_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Salvar no arquivo
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=4)
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar configurações: {e}")
        return False

def get_logo_path():
    """Obter o caminho da logo atual"""
    config = load_config()
    logo_path = config.get("logo_path", DEFAULT_LOGO_PATH)
    
    # Verificar se o arquivo existe
    if not os.path.exists(logo_path):
        return DEFAULT_LOGO_PATH
    
    return logo_path

def save_uploaded_logo(uploaded_file):
    """Salvar logo enviada pelo usuário"""
    try:
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(DEFAULT_LOGO_PATH), exist_ok=True)
        
        # Salvar o arquivo
        with open(DEFAULT_LOGO_PATH, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        # Atualizar configuração
        config = load_config()
        config["logo_path"] = DEFAULT_LOGO_PATH
        save_config(config)
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar logo: {e}")
        return False
