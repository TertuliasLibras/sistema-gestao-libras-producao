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
    st.title("Gerenciamento de Alunos")
    
    try:
        from utils import (
            load_students_data, 
            save_students_data,
            format_currency, 
            validate_phone,
            generate_monthly_payments
        )
        
        # Carregar dados
        students_df = load_students_data()
        
        # Resto do código da página
        st.write("Carregando dados dos alunos...")
        
    except Exception as e:
        st.error(f"Erro ao carregar módulos: {e}")
        st.info("Esta funcionalidade requer conexão com o banco de dados.")
