import os
import streamlit as st
import shutil
from datetime import datetime

# Pasta padrão para configurações
CONFIG_DIR = os.path.join(os.getcwd(), 'config')
LOGO_DIR = os.path.join(os.getcwd(), 'assets', 'images')

# Garantir que as pastas existam
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(LOGO_DIR, exist_ok=True)

# Arquivo para armazenar o caminho da logo
LOGO_CONFIG_FILE = os.path.join(CONFIG_DIR, 'logo_path.txt')

# Logo padrão (incluída no repositório)
DEFAULT_LOGO = os.path.join(LOGO_DIR, 'logo.png')

def load_config():
    """Carregar configurações do sistema"""
    # Implementação futura: carregar outras configurações
    return {}

def save_config(config_data):
    """Salvar configurações do sistema"""
    # Implementação futura: salvar outras configurações
    return True

def get_logo_path():
    """Obter o caminho da logo atual"""
    # Verificar se o arquivo de configuração existe
    if os.path.exists(LOGO_CONFIG_FILE):
        with open(LOGO_CONFIG_FILE, 'r') as f:
            logo_path = f.read().strip()
            if os.path.exists(logo_path):
                return logo_path
    
    # Se logo personalizada não existe, criar uma no diretório de assets
    # Fazer uma cópia da logo default para uma pasta segura
    # Isso garante que, mesmo se a pasta assets/images não existir, teremos uma logo
    os.makedirs('data/assets', exist_ok=True)
    internal_logo_path = 'data/assets/logo.png'
    
    # Se já existe uma logo na pasta data/assets, usá-la
    if os.path.exists(internal_logo_path):
        return internal_logo_path
    
    # Criar um arquivo de logo simples com texto se não tivermos nenhuma logo
    try:
        # Tenta criar um arquivo SVG básico com texto
        with open(internal_logo_path, 'w') as f:
            f.write('SGL')  # Arquivo de texto simples como fallback
        return internal_logo_path
    except:
        # Se falhar, apenas retornar o caminho (mesmo que o arquivo não exista)
        return internal_logo_path

def save_uploaded_logo(uploaded_file):
    """Salvar logo enviada pelo usuário"""
    try:
        # Garantir que a pasta de destino existe
        os.makedirs(LOGO_DIR, exist_ok=True)
        
        # Caminho para a nova logo
        file_extension = os.path.splitext(uploaded_file.name)[1]
        new_logo_path = os.path.join(LOGO_DIR, f'custom_logo{file_extension}')
        
        # Salvar o arquivo
        with open(new_logo_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        # Salvar uma cópia na pasta data/assets para garantir que esteja acessível
        os.makedirs('data/assets', exist_ok=True)
        backup_logo_path = os.path.join('data/assets', f'logo{file_extension}')
        shutil.copy2(new_logo_path, backup_logo_path)
        
        # Atualizar o arquivo de configuração com o caminho da logo de backup
        # Usar a cópia de backup como a principal para maior segurança
        with open(LOGO_CONFIG_FILE, 'w') as f:
            f.write(backup_logo_path)
        
        return True, backup_logo_path
    except Exception as e:
        return False, str(e)
