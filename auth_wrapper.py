import streamlit as st
import os
import sys

# Função global para verificar autenticação
def verify_authentication():
    """Verifica se o usuário está autenticado de forma consistente em todas as páginas."""
    # Primeiro, verificar se o usuário está autenticado
    if 'usuario_autenticado' not in st.session_state:
        st.warning('Você precisa fazer login para acessar esta página.')
        
        # Adicionar um botão para retornar à página de login
        if st.button("Ir para página de login"):
            # Redirecionar para a página principal usando javascript
            st.markdown("""
            <script>
                window.parent.location.href = "/";
            </script>
            """, unsafe_allow_html=True)
        
        # Parar a execução da página
        st.stop()
    
    return True

# Função para registrar a autenticação
def set_authentication(user_data, expiry=None):
    """Define os dados de autenticação na sessão."""
    st.session_state['usuario_autenticado'] = user_data
    if expiry:
        st.session_state['login_expiracao'] = expiry

# Função para fazer logout
def do_logout():
    """Remove os dados de autenticação da sessão."""
    if 'usuario_autenticado' in st.session_state:
        del st.session_state['usuario_autenticado']
    
    if 'login_expiracao' in st.session_state:
        del st.session_state['login_expiracao']
