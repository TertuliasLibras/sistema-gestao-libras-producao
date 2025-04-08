import os
import pandas as pd
from datetime import datetime
import streamlit as st
import json
import shutil

# Estrutura de diretórios
DATA_DIR = "data"
BACKUP_DIR = "backup"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# Funções de backup
def create_backup():
    """Cria um backup completo dos dados"""
    try:
        # Timestamp para o nome do backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = os.path.join(BACKUP_DIR, f"backup_{timestamp}")
        os.makedirs(backup_folder, exist_ok=True)
        
        # Copiar arquivos de dados
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('.csv'):
                src_file = os.path.join(DATA_DIR, filename)
                dst_file = os.path.join(backup_folder, filename)
                shutil.copy2(src_file, dst_file)
        
        # Criar arquivo de metadados
        metadata = {
            "timestamp": timestamp,
            "backup_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "files_included": os.listdir(DATA_DIR)
        }
        
        with open(os.path.join(backup_folder, "metadata.json"), 'w') as f:
            json.dump(metadata, f, indent=4)
        
        st.success(f"Backup criado com sucesso em {backup_folder}")
        return backup_folder
    except Exception as e:
        st.error(f"Erro ao criar backup: {e}")
        return None

def restore_backup(backup_folder):
    """Restaura dados a partir de um backup"""
    try:
        # Verificar se o diretório existe
        if not os.path.exists(backup_folder):
            st.error(f"Diretório de backup {backup_folder} não encontrado")
            return False
        
        # Copiar arquivos de backup para o diretório de dados
        for filename in os.listdir(backup_folder):
            if filename.endswith('.csv'):
                src_file = os.path.join(backup_folder, filename)
                dst_file = os.path.join(DATA_DIR, filename)
                shutil.copy2(src_file, dst_file)
        
        st.success(f"Backup restaurado com sucesso de {backup_folder}")
        return True
    except Exception as e:
        st.error(f"Erro ao restaurar backup: {e}")
        return False

def list_backups():
    """Lista todos os backups disponíveis"""
    try:
        backups = []
        for item in os.listdir(BACKUP_DIR):
            backup_dir = os.path.join(BACKUP_DIR, item)
            if os.path.isdir(backup_dir) and item.startswith("backup_"):
                # Tentar ler metadata
                metadata_file = os.path.join(backup_dir, "metadata.json")
                if os.path.exists(metadata_file):
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        backups.append({
                            "folder": backup_dir,
                            "name": item,
                            "timestamp": metadata.get("backup_date", "Desconhecido")
                        })
                else:
                    # Sem metadata, usar informações básicas
                    backups.append({
                        "folder": backup_dir,
                        "name": item,
                        "timestamp": "Desconhecido"
                    })
        
        # Ordenar por nome (que contém timestamp)
        backups.sort(key=lambda x: x["name"], reverse=True)
        return backups
    except Exception as e:
        st.error(f"Erro ao listar backups: {e}")
        return []

def download_backup(backup_folder):
    """Prepara um backup para download pelo usuário"""
    try:
        # Cria arquivo zip do backup
        import zipfile
        
        zip_path = f"{backup_folder}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(backup_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, backup_folder)
                    zipf.write(file_path, arcname)
        
        # Ler conteúdo do zip para retornar
        with open(zip_path, 'rb') as f:
            data = f.read()
        
        # Remover arquivo temporário
        os.remove(zip_path)
        
        return data
    except Exception as e:
        st.error(f"Erro ao preparar backup para download: {e}")
        return None

def upload_backup_to_gdrive():
    """
    Implementação futura: Fazer upload do backup para o Google Drive
    Isso requer implementação de OAuth2 com o Google, o que é um pouco mais complexo
    """
    st.info("Função de upload para Google Drive será implementada em versão futura")
    pass
