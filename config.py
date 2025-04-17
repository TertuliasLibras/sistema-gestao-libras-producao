import os
import json
import streamlit as st

# Caminho para o arquivo de configurações
CONFIG_FILE = "data/system_config.json"

# Configurações padrão
DEFAULT_CONFIG = {
    "logo_path": "assets/images/logo.svg",
    "system_name": "Sistema de Gestão - Pós-Graduação Libras",
    "theme_color": "#1E88E5"
}

def load_config():
    """Carregar configurações do sistema"""
    try:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    # Verificar se todas as chaves necessárias existem
                    for key in DEFAULT_CONFIG:
                        if key not in config:
                            config[key] = DEFAULT_CONFIG[key]
                    
                    return config
            except Exception as e:
                print(f"Erro ao carregar configurações: {e}")
                # Se houver erro, recriar o arquivo de configurações
                save_config(DEFAULT_CONFIG)
                return DEFAULT_CONFIG
        else:
            # Se o arquivo não existir, criar com configurações padrão
            save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
    except Exception as e:
        print(f"Erro crítico ao carregar configurações: {e}")
        # Em caso de erro crítico, retornar configurações padrão sem salvar
        return DEFAULT_CONFIG.copy()

def save_config(config_data):
    """Salvar configurações do sistema"""
    try:
        # Garantir que config_data é um dicionário
        if not isinstance(config_data, dict):
            print(f"Tentativa de salvar configuração inválida: {type(config_data)}")
            config_data = DEFAULT_CONFIG.copy()
            
        # Garantir que o diretório de configuração existe
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        # Salvar as configurações
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
            
        return True
    except Exception as e:
        # Usar print em vez de st.error para garantir funcionamento fora de contexto Streamlit
        print(f"Erro ao salvar configurações: {e}")
        return False

def get_logo_path():
    """Obter o caminho da logo atual"""
    try:
        config = load_config()
        # Garantir que config é um dicionário
        if not isinstance(config, dict):
            print(f"Configuração inválida: {config}, usando padrão")
            return DEFAULT_CONFIG["logo_path"]
            
        # Garantir que a chave existe
        if "logo_path" not in config:
            print("Chave 'logo_path' não encontrada, usando padrão")
            return DEFAULT_CONFIG["logo_path"]
            
        return config.get("logo_path", DEFAULT_CONFIG["logo_path"])
    except Exception as e:
        print(f"Erro ao obter logo_path: {e}")
        return DEFAULT_CONFIG["logo_path"]

def save_uploaded_logo(uploaded_file):
    """Salvar logo enviada pelo usuário"""
    try:
        # Criar diretório se não existir
        logo_dir = "assets/images"
        os.makedirs(logo_dir, exist_ok=True)
        
        # Definir caminho do arquivo
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        file_path = f"{logo_dir}/custom_logo{file_extension}"
        
        # Salvar arquivo
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Atualizar configuração - com verificação de tipo
        try:
            config = load_config()
            
            # Garantir que config é um dicionário
            if not isinstance(config, dict):
                print(f"Configuração inválida: {config}, criando novo")
                config = DEFAULT_CONFIG.copy()
                
            config["logo_path"] = file_path
            save_config(config)
        except Exception as e:
            print(f"Erro ao atualizar configuração: {e}")
            # Mesmo com erro, retornamos o caminho do arquivo salvo
        
        return file_path
    except Exception as e:
        # Usar print em vez de st.error para evitar erros de contexto Streamlit
        print(f"Erro ao salvar logo: {e}")
        return None
