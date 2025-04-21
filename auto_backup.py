"""
Módulo para backup automático com Google Drive.
Este módulo gerencia o backup automático dos arquivos CSV para o Google Drive
e a sincronização ao iniciar o sistema.
"""
import os
import io
import json
import time
import zipfile
import shutil
import logging
import streamlit as st
from datetime import datetime
from pathlib import Path

# Verificar se as bibliotecas do Google estão disponíveis
GOOGLE_DRIVE_AVAILABLE = False
try:
    import google.oauth2.credentials
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    # As bibliotecas não estão disponíveis
    pass

# Configuração de logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('auto_backup')

# Diretórios e arquivos
DATA_DIR = "data"
BACKUP_DIR = "backups"
CREDENTIALS_DIR = "credentials"
TOKEN_PATH = os.path.join(CREDENTIALS_DIR, "token.json")
CREDENTIALS_PATH = os.path.join(CREDENTIALS_DIR, "credentials.json")

# Configuração do Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']
BACKUP_FOLDER_NAME = "Libras_Sistema_Backup"  # Nome da pasta no Google Drive

# Arquivos para backup
FILES_TO_BACKUP = [
    os.path.join(DATA_DIR, "students.csv"),
    os.path.join(DATA_DIR, "payments.csv"),
    os.path.join(DATA_DIR, "internships.csv"),
    os.path.join(DATA_DIR, "users.csv"),
    os.path.join(DATA_DIR, "config.json")
]

def ensure_directories():
    """Garantir que os diretórios necessários existam"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(CREDENTIALS_DIR, exist_ok=True)

def get_credentials():
    """Obter credenciais para a API do Google Drive"""
    creds = None
    
    # Verificar se existe token de acesso
    try:
        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_info(json.load(open(TOKEN_PATH, 'r')))
    except Exception as e:
        logger.error(f"Erro ao carregar token: {e}")
    
    # Se não houver credenciais válidas, solicitar ao usuário
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Erro ao atualizar token: {e}")
                creds = None
        
        if not creds:
            if not os.path.exists(CREDENTIALS_PATH):
                logger.error("Arquivo de credenciais não encontrado.")
                raise FileNotFoundError("Arquivo de credenciais não encontrado. Por favor, configure as credenciais do Google Drive.")
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=8080)
            except Exception as e:
                logger.error(f"Erro na autenticação: {e}")
                raise
            
            # Salvar as credenciais para a próxima execução
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
    
    return creds

def get_drive_service():
    """Inicializar o serviço do Google Drive"""
    try:
        creds = get_credentials()
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Erro ao inicializar serviço do Drive: {e}")
        return None

def find_or_create_backup_folder(service):
    """Encontrar ou criar a pasta de backup no Google Drive"""
    try:
        # Verificar se a pasta já existe
        query = f"name='{BACKUP_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        items = results.get('files', [])
        
        if items:
            # Pasta encontrada
            folder_id = items[0]['id']
            logger.info(f"Pasta de backup encontrada: {folder_id}")
            return folder_id
        else:
            # Criar nova pasta
            file_metadata = {
                'name': BACKUP_FOLDER_NAME,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = service.files().create(body=file_metadata, fields='id').execute()
            folder_id = folder.get('id')
            logger.info(f"Pasta de backup criada: {folder_id}")
            return folder_id
    except Exception as e:
        logger.error(f"Erro ao buscar/criar pasta de backup: {e}")
        return None

def create_zip_backup():
    """Criar um arquivo ZIP com todos os dados para backup"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = os.path.join(BACKUP_DIR, f"backup_{timestamp}.zip")
    
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in FILES_TO_BACKUP:
                if os.path.exists(file_path):
                    arcname = os.path.basename(file_path)
                    zipf.write(file_path, arcname)
                    logger.info(f"Arquivo adicionado ao backup: {file_path}")
                else:
                    logger.warning(f"Arquivo não encontrado para backup: {file_path}")
        
        logger.info(f"Backup ZIP criado: {zip_filename}")
        return zip_filename
    except Exception as e:
        logger.error(f"Erro ao criar backup ZIP: {e}")
        return None

def upload_backup_to_drive(drive_service=None):
    """Upload do arquivo de backup para o Google Drive"""
    if not drive_service:
        drive_service = get_drive_service()
        if not drive_service:
            logger.error("Não foi possível inicializar o serviço do Drive.")
            return False
    
    try:
        # Criar backup ZIP
        zip_file = create_zip_backup()
        if not zip_file:
            logger.error("Falha ao criar arquivo ZIP para backup.")
            return False
        
        # Encontrar ou criar pasta de backup
        folder_id = find_or_create_backup_folder(drive_service)
        if not folder_id:
            logger.error("Falha ao encontrar/criar pasta de backup no Drive.")
            return False
        
        # Configurar metadados para upload
        file_metadata = {
            'name': os.path.basename(zip_file),
            'parents': [folder_id]
        }
        
        # Preparar mídia para upload
        media = MediaFileUpload(
            zip_file,
            mimetype='application/zip',
            resumable=True
        )
        
        # Realizar upload
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        logger.info(f"Backup enviado para o Drive com sucesso. ID: {file.get('id')}")
        
        # Limpar backups antigos (manter apenas os 3 mais recentes)
        cleanup_old_backups()
        
        return True
    except Exception as e:
        logger.error(f"Erro ao fazer upload do backup: {e}")
        return False

def list_backups_on_drive(drive_service=None):
    """Listar todos os backups disponíveis no Google Drive"""
    if not drive_service:
        drive_service = get_drive_service()
        if not drive_service:
            logger.error("Não foi possível inicializar o serviço do Drive.")
            return []
    
    try:
        # Encontrar pasta de backup
        folder_id = find_or_create_backup_folder(drive_service)
        if not folder_id:
            logger.error("Falha ao encontrar/criar pasta de backup no Drive.")
            return []
        
        # Buscar arquivos na pasta de backup
        query = f"'{folder_id}' in parents and mimeType='application/zip' and trashed=false"
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, createdTime)',
            orderBy='createdTime desc'
        ).execute()
        
        files = results.get('files', [])
        logger.info(f"Encontrados {len(files)} backups no Drive.")
        return files
    except Exception as e:
        logger.error(f"Erro ao listar backups no Drive: {e}")
        return []

def download_backup_from_drive(file_id, drive_service=None):
    """Download de um backup específico do Google Drive"""
    if not drive_service:
        drive_service = get_drive_service()
        if not drive_service:
            logger.error("Não foi possível inicializar o serviço do Drive.")
            return None
    
    try:
        # Obter informações do arquivo
        file = drive_service.files().get(fileId=file_id, fields='name').execute()
        file_name = file.get('name')
        
        # Preparar download
        request = drive_service.files().get_media(fileId=file_id)
        
        # Realizar download para memória
        file_content = io.BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            logger.info(f"Download {int(status.progress() * 100)}% concluído")
        
        # Salvar arquivo
        download_path = os.path.join(BACKUP_DIR, file_name)
        with open(download_path, 'wb') as f:
            f.write(file_content.getvalue())
        
        logger.info(f"Backup baixado para: {download_path}")
        return download_path
    except Exception as e:
        logger.error(f"Erro ao baixar backup do Drive: {e}")
        return None

def restore_backup_from_zip(zip_file):
    """Restaurar dados a partir de um arquivo ZIP de backup"""
    try:
        # Criar diretório temporário para extração
        temp_dir = os.path.join(BACKUP_DIR, "temp_extract")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        # Extrair ZIP para o diretório temporário
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Copiar arquivos extraídos para o diretório de dados
        for file_name in os.listdir(temp_dir):
            source = os.path.join(temp_dir, file_name)
            destination = os.path.join(DATA_DIR, file_name)
            shutil.copy2(source, destination)
            logger.info(f"Arquivo restaurado: {destination}")
        
        # Limpar diretório temporário
        shutil.rmtree(temp_dir)
        
        logger.info("Backup restaurado com sucesso.")
        return True
    except Exception as e:
        logger.error(f"Erro ao restaurar backup: {e}")
        return False

def cleanup_old_backups():
    """Limpar backups antigos, mantendo apenas os 3 mais recentes localmente"""
    try:
        backup_files = [f for f in os.listdir(BACKUP_DIR) if f.startswith("backup_") and f.endswith(".zip")]
        backup_files.sort(reverse=True)  # Do mais recente para o mais antigo
        
        # Manter apenas os 3 mais recentes
        for file_to_delete in backup_files[3:]:
            file_path = os.path.join(BACKUP_DIR, file_to_delete)
            os.remove(file_path)
            logger.info(f"Backup antigo removido: {file_path}")
    except Exception as e:
        logger.error(f"Erro ao limpar backups antigos: {e}")

def auto_backup_after_change():
    """Realizar backup automático após alterações no banco de dados"""
    # Verificar se o Google Drive está disponível
    if not GOOGLE_DRIVE_AVAILABLE:
        # Se as bibliotecas não estão disponíveis, apenas criar backup local
        zip_file = create_zip_backup()
        if zip_file:
            logger.info(f"Backup local criado: {zip_file}")
            cleanup_old_backups()
            return True
        return False
    
    # Verificar última vez que o backup foi realizado (para evitar muitos backups em sequência)
    last_backup_time = st.session_state.get('last_backup_time', 0)
    current_time = time.time()
    
    # Só fazer backup se passaram pelo menos 5 minutos desde o último
    if current_time - last_backup_time >= 300:  # 300 segundos = 5 minutos
        try:
            result = upload_backup_to_drive()
            if result:
                st.session_state['last_backup_time'] = current_time
                logger.info("Backup automático realizado com sucesso")
                return True
            else:
                # Tentar pelo menos criar um backup local
                zip_file = create_zip_backup()
                if zip_file:
                    logger.info(f"Backup local criado como alternativa: {zip_file}")
                    cleanup_old_backups()
                    return True
                logger.warning("Falha no backup automático")
                return False
        except Exception as e:
            logger.error(f"Erro no backup automático: {e}")
            # Tentar pelo menos criar um backup local
            zip_file = create_zip_backup()
            if zip_file:
                logger.info(f"Backup local criado como alternativa após erro: {zip_file}")
                cleanup_old_backups()
                return True
            return False
    else:
        logger.info("Backup automático ignorado (muito cedo desde o último backup)")
        return True  # Retorna True para não interferir no fluxo do programa

def sync_from_drive_on_startup():
    """Sincronizar dados do Google Drive ao iniciar o sistema"""
    # Verificar se o Google Drive está disponível
    if not GOOGLE_DRIVE_AVAILABLE:
        logger.warning("Google Drive API não está disponível. Sincronização ignorada.")
        return False
    
    # Verificar se já existem arquivos de backup locais que podemos usar
    try:
        backup_files = [f for f in os.listdir(BACKUP_DIR) if f.startswith("backup_") and f.endswith(".zip")]
        if backup_files:
            # Ordenar por data de criação (mais recente primeiro)
            backup_files.sort(reverse=True)
            # Usar o backup local mais recente
            backup_path = os.path.join(BACKUP_DIR, backup_files[0])
            logger.info(f"Usando backup local mais recente: {backup_path}")
            
            # Restaurar dados do backup local
            result = restore_backup_from_zip(backup_path)
            if result:
                logger.info("Sistema sincronizado com sucesso a partir do backup local mais recente.")
                return True
    except Exception as e:
        logger.warning(f"Erro ao verificar backups locais: {e}")
    
    # Se não houver backups locais ou falhar, tentar o Google Drive
    try:
        drive_service = get_drive_service()
        if not drive_service:
            logger.error("Não foi possível inicializar o serviço do Drive.")
            return False
        
        # Listar backups disponíveis
        backups = list_backups_on_drive(drive_service)
        if not backups:
            logger.warning("Nenhum backup encontrado no Drive para sincronização.")
            return False
        
        # Baixar o backup mais recente
        latest_backup = backups[0]  # O primeiro da lista (ordenada por data)
        backup_path = download_backup_from_drive(latest_backup['id'], drive_service)
        
        if not backup_path:
            logger.error("Falha ao baixar backup do Drive.")
            return False
        
        # Restaurar dados do backup
        result = restore_backup_from_zip(backup_path)
        if result:
            logger.info("Sistema sincronizado com sucesso a partir do backup mais recente do Drive.")
            return True
        else:
            logger.error("Falha ao restaurar dados do backup.")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao sincronizar dados do Drive: {e}")
        return False

def upload_credentials_file():
    """Interface para fazer upload do arquivo de credenciais"""
    st.subheader("Configuração do Google Drive")
    
    st.write("""
    Para usar o backup automático no Google Drive, você precisa fornecer um arquivo de credenciais do Google Cloud Platform.
    
    Passos para obter as credenciais:
    1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
    2. Crie um novo projeto ou selecione um existente
    3. Habilite a API do Google Drive para o projeto
    4. Em "Credenciais", crie uma credencial do tipo "OAuth 2.0 Client ID"
    5. Baixe o arquivo JSON de credenciais
    6. Faça upload do arquivo abaixo
    """)
    
    uploaded_file = st.file_uploader("Fazer upload do arquivo de credenciais (credentials.json)", type=["json"])
    
    if uploaded_file:
        try:
            # Salvar o arquivo de credenciais
            ensure_directories()
            with open(CREDENTIALS_PATH, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success("Arquivo de credenciais salvo com sucesso!")
            
            # Verificar se o arquivo é válido tentando inicializar o serviço
            try:
                service = get_drive_service()
                if service:
                    st.success("Credenciais verificadas com sucesso! O backup automático está configurado.")
                    return True
                else:
                    st.error("As credenciais foram salvas, mas não foi possível conectar ao Google Drive.")
                    return False
            except Exception as e:
                st.error(f"Erro ao verificar credenciais: {str(e)}")
                return False
                
        except Exception as e:
            st.error(f"Erro ao salvar arquivo de credenciais: {str(e)}")
            return False
    
    return False

def setup_auto_backup():
    """Configura o backup automático e exibe opções ao usuário"""
    st.title("Configuração de Backup Automático")
    
    # Verificar se as bibliotecas do Google estão disponíveis
    if not GOOGLE_DRIVE_AVAILABLE:
        st.error("""
        As bibliotecas do Google Drive não estão disponíveis neste ambiente.
        
        Para habilitar o backup automático com Google Drive, instale as seguintes bibliotecas:
        - google-auth
        - google-auth-oauthlib
        - google-api-python-client
        
        No entanto, o sistema continua funcionando com backup local automático.
        """)
        
        # Mostrar os backups locais disponíveis
        st.subheader("Backups Locais")
        try:
            backup_files = [f for f in os.listdir(BACKUP_DIR) if f.startswith("backup_") and f.endswith(".zip")]
            
            if backup_files:
                # Ordenar por data (mais recente primeiro)
                backup_files.sort(reverse=True)
                
                for backup_file in backup_files:
                    col1, col2 = st.columns([3, 1])
                    
                    # Extrair timestamp do nome do arquivo
                    try:
                        timestamp_str = backup_file.replace("backup_", "").replace(".zip", "")
                        dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                        formatted_date = dt.strftime("%d/%m/%Y %H:%M:%S")
                    except:
                        formatted_date = "Data desconhecida"
                    
                    with col1:
                        st.write(f"{backup_file} - {formatted_date}")
                    
                    with col2:
                        if st.button("Restaurar", key=f"restore_local_{backup_file}"):
                            with st.spinner("Restaurando backup..."):
                                backup_path = os.path.join(BACKUP_DIR, backup_file)
                                result = restore_backup_from_zip(backup_path)
                                if result:
                                    st.success("Backup restaurado com sucesso!")
                                else:
                                    st.error("Falha ao restaurar backup.")
            else:
                st.info("Nenhum backup local encontrado.")
                
            # Opção para criar backup local
            if st.button("Criar Backup Local"):
                with st.spinner("Criando backup..."):
                    backup_file = create_zip_backup()
                    if backup_file:
                        st.success(f"Backup criado com sucesso: {os.path.basename(backup_file)}")
                        cleanup_old_backups()
                    else:
                        st.error("Falha ao criar backup.")
                        
        except Exception as e:
            st.error(f"Erro ao listar backups locais: {str(e)}")
        
        return
    
    # Continuar com a configuração do Google Drive se as bibliotecas estiverem disponíveis
    # Verificar se o arquivo de credenciais existe
    credentials_exist = os.path.exists(CREDENTIALS_PATH)
    
    if not credentials_exist:
        st.warning("O backup automático para o Google Drive ainda não está configurado.")
        upload_credentials_file()
    else:
        try:
            # Verificar se as credenciais são válidas
            service = get_drive_service()
            
            if service:
                st.success("O backup automático para o Google Drive está configurado.")
                
                # Opções de backup
                st.subheader("Opções de Backup")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Fazer Backup Agora"):
                        with st.spinner("Realizando backup..."):
                            result = upload_backup_to_drive(service)
                            if result:
                                st.success("Backup realizado com sucesso!")
                            else:
                                st.error("Falha ao realizar backup.")
                
                with col2:
                    if st.button("Sincronizar do Drive"):
                        with st.spinner("Sincronizando do Google Drive..."):
                            result = sync_from_drive_on_startup()
                            if result:
                                st.success("Dados sincronizados com sucesso!")
                            else:
                                st.error("Falha ao sincronizar dados.")
                
                # Listar backups disponíveis
                st.subheader("Backups Disponíveis")
                
                with st.spinner("Carregando lista de backups..."):
                    backups = list_backups_on_drive(service)
                
                if backups:
                    for backup in backups:
                        col1, col2 = st.columns([3, 1])
                        
                        # Formatar a data de criação
                        created_time = backup.get('createdTime', '')
                        if created_time:
                            # Formato ISO 8601 para datetime
                            dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                            formatted_date = dt.strftime("%d/%m/%Y %H:%M:%S")
                        else:
                            formatted_date = "Data desconhecida"
                        
                        with col1:
                            st.write(f"{backup['name']} - {formatted_date}")
                        
                        with col2:
                            if st.button("Restaurar", key=f"restore_{backup['id']}"):
                                with st.spinner("Restaurando backup..."):
                                    backup_path = download_backup_from_drive(backup['id'], service)
                                    if backup_path:
                                        result = restore_backup_from_zip(backup_path)
                                        if result:
                                            st.success("Backup restaurado com sucesso!")
                                        else:
                                            st.error("Falha ao restaurar backup.")
                                    else:
                                        st.error("Falha ao baixar backup.")
                else:
                    st.info("Nenhum backup encontrado no Google Drive.")
                
                # Também mostrar backups locais
                st.subheader("Backups Locais")
                try:
                    backup_files = [f for f in os.listdir(BACKUP_DIR) if f.startswith("backup_") and f.endswith(".zip")]
                    
                    if backup_files:
                        # Ordenar por data (mais recente primeiro)
                        backup_files.sort(reverse=True)
                        
                        for backup_file in backup_files:
                            col1, col2 = st.columns([3, 1])
                            
                            # Extrair timestamp do nome do arquivo
                            try:
                                timestamp_str = backup_file.replace("backup_", "").replace(".zip", "")
                                dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                                formatted_date = dt.strftime("%d/%m/%Y %H:%M:%S")
                            except:
                                formatted_date = "Data desconhecida"
                            
                            with col1:
                                st.write(f"{backup_file} - {formatted_date}")
                            
                            with col2:
                                if st.button("Restaurar", key=f"restore_local_{backup_file}"):
                                    with st.spinner("Restaurando backup..."):
                                        backup_path = os.path.join(BACKUP_DIR, backup_file)
                                        result = restore_backup_from_zip(backup_path)
                                        if result:
                                            st.success("Backup restaurado com sucesso!")
                                        else:
                                            st.error("Falha ao restaurar backup.")
                    else:
                        st.info("Nenhum backup local encontrado.")
                except Exception as e:
                    st.error(f"Erro ao listar backups locais: {str(e)}")
                
                # Opção para reconfigurar
                st.subheader("Reconfigurar")
                if st.button("Alterar Credenciais"):
                    upload_credentials_file()
                
            else:
                st.error("As credenciais do Google Drive são inválidas ou expiraram.")
                upload_credentials_file()
                
        except Exception as e:
            st.error(f"Erro ao verificar configuração: {str(e)}")
            upload_credentials_file()

# Funções para integração com o resto do sistema

def patch_database_functions():
    """
    Modifica as funções do database.py para incluir chamadas de backup automático
    após cada operação de escrita.
    """
    import database
    
    # Armazenar as funções originais
    original_save_student = database.save_student
    original_update_student = database.update_student
    original_delete_student = database.delete_student
    original_save_payment = database.save_payment
    original_update_payment = database.update_payment
    original_delete_payment = database.delete_payment
    original_save_internship = database.save_internship
    original_update_internship = database.update_internship
    original_delete_internship = database.delete_internship
    original_save_user = database.save_user
    original_update_user = database.update_user
    original_delete_user = database.delete_user
    
    # Substituir as funções originais com versões que chamam o backup após a operação
    
    def patched_save_student(student_data):
        result = original_save_student(student_data)
        if result:
            auto_backup_after_change()
        return result
    
    def patched_update_student(phone, student_data):
        result = original_update_student(phone, student_data)
        if result:
            auto_backup_after_change()
        return result
    
    def patched_delete_student(phone):
        result = original_delete_student(phone)
        if result:
            auto_backup_after_change()
        return result
    
    def patched_save_payment(payment_data):
        result = original_save_payment(payment_data)
        if result:
            auto_backup_after_change()
        return result
    
    def patched_update_payment(payment_id, payment_data):
        result = original_update_payment(payment_id, payment_data)
        if result:
            auto_backup_after_change()
        return result
    
    def patched_delete_payment(payment_id):
        result = original_delete_payment(payment_id)
        if result:
            auto_backup_after_change()
        return result
    
    def patched_save_internship(internship_data):
        result = original_save_internship(internship_data)
        if result:
            auto_backup_after_change()
        return result
    
    def patched_update_internship(internship_id, internship_data):
        result = original_update_internship(internship_id, internship_data)
        if result:
            auto_backup_after_change()
        return result
    
    def patched_delete_internship(internship_id):
        result = original_delete_internship(internship_id)
        if result:
            auto_backup_after_change()
        return result
    
    def patched_save_user(user_data):
        result = original_save_user(user_data)
        if result:
            auto_backup_after_change()
        return result
    
    def patched_update_user(user_id, user_data):
        result = original_update_user(user_id, user_data)
        if result:
            auto_backup_after_change()
        return result
    
    def patched_delete_user(user_id):
        result = original_delete_user(user_id)
        if result:
            auto_backup_after_change()
        return result
    
    # Substituir as funções no módulo database
    database.save_student = patched_save_student
    database.update_student = patched_update_student
    database.delete_student = patched_delete_student
    database.save_payment = patched_save_payment
    database.update_payment = patched_update_payment
    database.delete_payment = patched_delete_payment
    database.save_internship = patched_save_internship
    database.update_internship = patched_update_internship
    database.delete_internship = patched_delete_internship
    database.save_user = patched_save_user
    database.update_user = patched_update_user
    database.delete_user = patched_delete_user
    
    logger.info("Funções de banco de dados modificadas para backup automático")

# Inicialização
ensure_directories()

if __name__ == "__main__":
    # Se executado diretamente, exibir interface de configuração
    setup_auto_backup()
