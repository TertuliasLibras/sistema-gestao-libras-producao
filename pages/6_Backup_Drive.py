import streamlit as st
import os
from auth_wrapper import verify_authentication
import auto_backup

# Verificar autenticação
verify_authentication()

# Header com logo
st.title("Backup Automático com Google Drive")

# Exibir informações do usuário autenticado
if 'usuario_autenticado' in st.session_state:
    user_data = st.session_state['usuario_autenticado']
    st.sidebar.write(f"Usuário: {user_data.get('name', user_data.get('username', 'Desconhecido'))}")
    
    # Somente administradores podem acessar esta página
    if user_data.get('level', '').lower() != 'admin':
        st.warning("Somente administradores podem acessar esta página.")
        st.stop()

# Configuração de backup
auto_backup.setup_auto_backup()

# Informações adicionais
with st.expander("Sobre o Backup Automático"):
    st.markdown("""
    ## Como funciona o Backup Automático
    
    Este sistema realiza backup automático dos seus dados para o Google Drive sempre que alterações importantes são feitas.
    
    ### Funcionalidades:
    
    - **Backup Automático**: Cada alteração nos dados é automaticamente salva no Google Drive
    - **Sincronização ao Iniciar**: Ao reiniciar o sistema, os dados mais recentes são carregados do Google Drive
    - **Restauração Manual**: Você pode escolher qualquer versão de backup para restaurar
    
    ### Benefícios:
    
    - Seus dados ficam seguros no Google Drive mesmo se o servidor Render reiniciar
    - Você pode restaurar versões anteriores caso ocorra alguma perda de dados
    - O sistema sempre carrega os dados mais atualizados automaticamente
    
    ### Configuração:
    
    Para utilizar esta funcionalidade, você precisou:
    
    1. Criar um projeto no Google Cloud Platform 
    2. Ativar a API do Google Drive para seu projeto
    3. Criar credenciais OAuth 2.0
    4. Fazer upload do arquivo de credenciais nesta página
    
    Seus dados estão protegidos e o backup é automático!
    """)

# Adicionar link para voltar ao dashboard
if st.button("Voltar ao Dashboard"):
    st.switch_page("app.py")
