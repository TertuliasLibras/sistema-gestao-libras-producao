import streamlit as st
import pandas as pd
from datetime import datetime

# Verificar se estamos no ambiente de produção
try:
    from login import verificar_autenticacao, mostrar_pagina_login
except ImportError:
    # Fallback para demonstração
    print("Usando login de demonstração")
    from login_fallback import verificar_autenticacao, mostrar_pagina_login

# Verificar autenticação
if not verificar_autenticacao():
    mostrar_pagina_login()
else:
    st.title("Gerenciamento de Estágios")
    
    try:
        from utils import (
            load_students_data,
            load_internships_data,
            save_internships_data
        )
        
        # Carregar dados
        students_df = load_students_data()
        internships_df = load_internships_data()
        
        # Resto do código da página
        st.write("Carregando dados de estágios...")
        
    except Exception as e:
        st.error(f"Erro ao carregar módulos: {e}")
        st.info("Esta funcionalidade requer conexão com o banco de dados.")
