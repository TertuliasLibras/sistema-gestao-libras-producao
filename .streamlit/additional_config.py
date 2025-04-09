import streamlit as st
import os

# Configurar secrets
if 'RENDER' in os.environ:
    # Estamos no Render, usar compartilhamento de sessão
    st.session_state.share_session = True
    
    # Configurar cookies compartilhados
    if not hasattr(st.session_state, '_session_id'):
        import uuid
        st.session_state._session_id = str(uuid.uuid4())

# Função para verificar autenticação de forma consistente
def check_authentication():
    if 'usuario_autenticado' not in st.session_state:
        return False
    return True
