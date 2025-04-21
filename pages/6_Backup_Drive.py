import streamlit as st
import os
from datetime import datetime
import auto_backup
from auth_wrapper import verify_authentication

# Verificar autenticação
if not verify_authentication():
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# Título da página
st.title("Backup e Sincronização")

# Permitir que todos os usuários acessem a página de backup
# As funções de administração serão restritas dentro da página
admin_mode = st.session_state.get("usuario_autenticado", {}).get("nivel", "") == "admin"

# Garantir que os diretórios necessários existam
auto_backup.ensure_directories()

# Verificar se a API do Google Drive está disponível
if not auto_backup.GOOGLE_DRIVE_AVAILABLE:
    st.warning("""
    ## Backup Local Ativo
    
    As bibliotecas necessárias para o Google Drive não estão instaladas neste ambiente.
    O sistema irá continuar funcionando com backups locais automáticos.
    
    Se você deseja habilitar a integração com o Google Drive, instale as seguintes bibliotecas:
    - google-auth
    - google-auth-oauthlib
    - google-api-python-client
    """)
    
    # Mostrar backups locais disponíveis
    st.subheader("Backups Locais Disponíveis")
    
    # Criar backup local manualmente
    if st.button("Criar Backup Agora"):
        with st.spinner("Criando backup..."):
            backup_file = auto_backup.create_zip_backup()
            if backup_file:
                st.success(f"Backup criado com sucesso: {os.path.basename(backup_file)}")
                auto_backup.cleanup_old_backups()
            else:
                st.error("Falha ao criar backup.")
    
    # Listar backups locais
    try:
        backup_files = [f for f in os.listdir(auto_backup.BACKUP_DIR) if f.startswith("backup_") and f.endswith(".zip")]
        
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
                    if st.button("Restaurar", key=f"restore_{backup_file}"):
                        with st.spinner("Restaurando backup..."):
                            backup_path = os.path.join(auto_backup.BACKUP_DIR, backup_file)
                            result = auto_backup.restore_backup_from_zip(backup_path)
                            if result:
                                st.success("Backup restaurado com sucesso! Recarregue a página para ver as mudanças.")
                            else:
                                st.error("Falha ao restaurar backup.")
        else:
            st.info("Nenhum backup local encontrado.")
    except Exception as e:
        st.error(f"Erro ao listar backups: {str(e)}")
else:
    # Se a API do Google Drive estiver disponível, mostrar a interface completa
    auto_backup.setup_auto_backup(admin_mode=admin_mode)
    
    # Explicação sobre o backup automático
    st.markdown("""
    ## Como funciona o backup automático
    
    O sistema está configurado para realizar backup automático dos dados sempre que:
    - Um novo aluno é registrado
    - Os dados de um aluno são atualizados
    - Um aluno é excluído
    - Um novo pagamento é registrado
    - Um pagamento é atualizado
    - Um pagamento é excluído
    - Um novo estágio é registrado
    - Um estágio é atualizado
    - Um estágio é excluído
    - Um novo usuário é registrado
    - Um usuário é atualizado
    - Um usuário é excluído
    
    Os backups são limitados para ocorrer no máximo a cada 5 minutos para evitar sobrecarga.
    
    ### Restauração Automática
    
    Ao iniciar, o sistema verifica se há backups disponíveis no Google Drive e restaura automaticamente 
    o backup mais recente, garantindo que os dados estejam atualizados mesmo em caso de reinicialização.
    """)
