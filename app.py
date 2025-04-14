import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import calendar
from utils import (
    load_students_data, 
    load_payments_data, 
    load_internships_data,
    get_active_students,
    get_canceled_students,
    get_overdue_payments,
    calculate_monthly_revenue,
    format_currency
)
from login import verificar_autenticacao, mostrar_pagina_login, pagina_gerenciar_usuarios, pagina_trocar_senha, logout
from config import get_logo_path, load_config, save_config, save_uploaded_logo

# Set page configuration
st.set_page_config(
    page_title="Sistema de Gestão - Pós-Graduação Libras",
    page_icon="📊",
    layout="wide"
)

# Create the data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# Create empty data files if they don't exist
if not os.path.exists("data/students.csv"):
    pd.DataFrame({
        "phone": [],
        "name": [],
        "email": [],
        "enrollment_date": [],
        "status": [],
        "cancellation_date": [],
        "cancellation_fee_paid": [],
        "monthly_fee": [],
        "notes": []
    }).to_csv("data/students.csv", index=False)

if not os.path.exists("data/payments.csv"):
    pd.DataFrame({
        "phone": [],
        "payment_date": [],
        "due_date": [],
        "amount": [],
        "month_reference": [],
        "year_reference": [],
        "status": [],
        "notes": []
    }).to_csv("data/payments.csv", index=False)

if not os.path.exists("data/internships.csv"):
    pd.DataFrame({
        "date": [],
        "topic": [],
        "duration_hours": [],
        "students": []
    }).to_csv("data/internships.csv", index=False)

# Custom CSS to style the logo
st.markdown("""
<style>
    .logo-container {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }
    .logo-text {
        margin-left: 1rem;
        font-size: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Verificar se o usuário está autenticado
if not verificar_autenticacao():
    mostrar_pagina_login()
else:
    # Menu de navegação com logout
    with st.sidebar:
        st.write(f"Usuário: {st.session_state['usuario_autenticado']['nome']}")
        
        # Inicializar variáveis de navegação e estado se ainda não existirem
        if 'nav_page' not in st.session_state:
            st.session_state['nav_page'] = 'dashboard'
            
        if 'mostrar_trocar_senha' not in st.session_state:
            st.session_state['mostrar_trocar_senha'] = False
            
        if 'mostrar_gerenciamento_usuarios' not in st.session_state:
            st.session_state['mostrar_gerenciamento_usuarios'] = False
            
        if 'mostrar_configuracoes' not in st.session_state:
            st.session_state['mostrar_configuracoes'] = False
            
        if 'mostrar_backup' not in st.session_state:
            st.session_state['mostrar_backup'] = False
        
        st.markdown("### Menu de Navegação")
        
        # Botões de navegação principal que preservam o estado da sessão
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state['nav_page'] = 'dashboard'
            st.session_state['mostrar_gerenciamento_usuarios'] = False
            st.session_state['mostrar_configuracoes'] = False
            st.session_state['mostrar_backup'] = False
            st.rerun()
            
        if st.button("👨‍🎓 Alunos", use_container_width=True):
            st.session_state['nav_page'] = 'alunos'
            st.session_state['mostrar_gerenciamento_usuarios'] = False
            st.session_state['mostrar_configuracoes'] = False
            st.session_state['mostrar_backup'] = False
            st.rerun()
            
        if st.button("💰 Pagamentos", use_container_width=True):
            st.session_state['nav_page'] = 'pagamentos'
            st.session_state['mostrar_gerenciamento_usuarios'] = False
            st.session_state['mostrar_configuracoes'] = False
            st.session_state['mostrar_backup'] = False
            st.rerun()
            
        if st.button("⏱️ Estágios", use_container_width=True):
            st.session_state['nav_page'] = 'estagios'
            st.session_state['mostrar_gerenciamento_usuarios'] = False
            st.session_state['mostrar_configuracoes'] = False
            st.session_state['mostrar_backup'] = False
            st.rerun()
            
        if st.button("📈 Relatórios", use_container_width=True):
            st.session_state['nav_page'] = 'relatorios'
            st.session_state['mostrar_gerenciamento_usuarios'] = False
            st.session_state['mostrar_configuracoes'] = False
            st.session_state['mostrar_backup'] = False
            st.rerun()
        
        # Opções de usuário (para todos)
        st.markdown("### Opções de Usuário")
        
        if st.button("Trocar Senha", use_container_width=True):
            st.session_state["mostrar_trocar_senha"] = True
            st.session_state['mostrar_gerenciamento_usuarios'] = False
            st.session_state['mostrar_configuracoes'] = False
            st.session_state['mostrar_backup'] = False
            st.session_state['nav_page'] = 'dashboard'
            st.rerun()
            
        # Opções de administração (apenas admin)
        if st.session_state['usuario_autenticado']['nivel'] == "admin":
            st.markdown("### Administração")
            
            # Botões para cada opção de administração
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Gerenciar Usuários"):
                    st.session_state["mostrar_gerenciamento_usuarios"] = True
                    st.session_state["mostrar_trocar_senha"] = False
                    st.session_state['mostrar_configuracoes'] = False
                    st.session_state['mostrar_backup'] = False
                    st.session_state['nav_page'] = 'dashboard'
                    st.rerun()
                    
            with col2:
                if st.button("Configurações"):
                    st.session_state["mostrar_configuracoes"] = True
                    st.session_state["mostrar_trocar_senha"] = False
                    st.session_state['mostrar_gerenciamento_usuarios'] = False
                    st.session_state['mostrar_backup'] = False
                    st.session_state['nav_page'] = 'dashboard'
                    st.rerun()
            
            if st.button("Alterar Logo", use_container_width=True):
                st.session_state["mostrar_configuracoes"] = True
                st.session_state["mostrar_trocar_senha"] = False
                st.session_state['mostrar_gerenciamento_usuarios'] = False
                st.session_state['mostrar_backup'] = False
                st.session_state['nav_page'] = 'dashboard'
                st.rerun()
        
        st.divider()
        
        # Opção para fazer backup dos dados
        st.subheader("Backup de Dados")
        
        if st.button("Baixar Backup Completo"):
            st.session_state["mostrar_backup"] = True
            st.session_state["mostrar_trocar_senha"] = False
            st.session_state['mostrar_gerenciamento_usuarios'] = False
            st.session_state['mostrar_configuracoes'] = False
        
        st.divider()
        
        # Botão de logout
        if st.button("Sair"):
            logout()
            st.rerun()
    
    # Verificar se deve mostrar a página de gerenciamento de usuários
    if st.session_state.get("mostrar_gerenciamento_usuarios", False):
        pagina_gerenciar_usuarios()
        if st.button("Voltar ao Dashboard"):
            st.session_state["mostrar_gerenciamento_usuarios"] = False
            st.rerun()
    
    # Verificar se deve mostrar a página de configurações
    elif st.session_state.get("mostrar_configuracoes", False):
        st.subheader("Configurações do Sistema")
        
        # Carregar configurações atuais
        config = load_config()
        
        # Upload de logo
        st.write("### Logo do Sistema")
        st.write("Faça upload de uma nova imagem para usar como logo do sistema.")
        
        uploaded_file = st.file_uploader("Escolher imagem", type=['png', 'jpg', 'jpeg', 'svg'])
        if uploaded_file is not None:
            # Exibir preview da imagem
            st.image(uploaded_file, width=200, caption="Preview da nova logo")
            
            # Botão para salvar
            if st.button("Salvar Nova Logo"):
                logo_path = save_uploaded_logo(uploaded_file)
                if logo_path:
                    st.success(f"Logo atualizada com sucesso! Novo caminho: {logo_path}")
                    # Aguardar um pouco antes de recarregar
                    st.rerun()
        
        # Mostrar logo atual
        st.write("### Logo Atual")
        logo_path = get_logo_path()
        st.image(logo_path, width=150)
        
        # Opções para restaurar logo padrão
        if st.button("Restaurar Logo Padrão"):
            config["logo_path"] = "assets/images/logo.svg"
            save_config(config)
            st.success("Logo padrão restaurada com sucesso!")
            st.rerun()
        
        if st.button("Voltar ao Dashboard"):
            st.session_state["mostrar_configuracoes"] = False
            st.rerun()
    
    # Verificar se deve mostrar a página de backup
    elif st.session_state.get("mostrar_backup", False):
        st.subheader("Backup de Dados")
        
        st.write("""
        Aqui você pode baixar todos os dados do sistema em formato CSV para backup ou análise externa.
        """)
        
        col1, col2, col3 = st.columns(3)
        
        # Load data
        students_df = load_students_data()
        payments_df = load_payments_data()
        internships_df = load_internships_data()
        
        with col1:
            if students_df is not None and not students_df.empty:
                csv_students = students_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Baixar Dados de Alunos",
                    csv_students,
                    "alunos_backup.csv",
                    "text/csv",
                    key='download-students'
                )
            else:
                st.info("Não há dados de alunos para exportar.")
        
        with col2:
            if payments_df is not None and not payments_df.empty:
                csv_payments = payments_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Baixar Dados de Pagamentos",
                    csv_payments,
                    "pagamentos_backup.csv",
                    "text/csv",
                    key='download-payments'
                )
            else:
                st.info("Não há dados de pagamentos para exportar.")
        
        with col3:
            if internships_df is not None and not internships_df.empty:
                csv_internships = internships_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Baixar Dados de Estágios",
                    csv_internships,
                    "estagios_backup.csv",
                    "text/csv",
                    key='download-internships'
                )
            else:
                st.info("Não há dados de estágios para exportar.")
        
        # Opção de backup completo
        st.subheader("Backup Completo")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # TODO: Implementar zip de múltiplos arquivos quando necessário
        
        if st.button("Voltar ao Dashboard"):
            st.session_state["mostrar_backup"] = False
            st.rerun()

    else:
        # Main app title with logo
        col1, col2 = st.columns([1, 3])
        with col1:
            try:
                # Usar função para obter o caminho da logo
                logo_path = get_logo_path()
                st.image(logo_path, width=150)
            except Exception as e:
                st.write(f"Erro ao carregar logo: {e}")
                st.write("Entre em contato com suporte.")
        with col2:
            st.markdown('<div class="logo-text">Sistema de Gestão - Pós-Graduação Libras</div>', unsafe_allow_html=True)
        
        # Load data for all pages
        students_df = load_students_data()
        payments_df = load_payments_data()
        internships_df = load_internships_data()
        
        # Importações internas para páginas
        import sys
        import importlib.util
        
        # Funções para carregar páginas como módulos Python
        def load_module_from_path(module_name, file_path):
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module
            
        # Função que carrega e executa o código de uma página
        def load_page_module(page_name):
            try:
                # Primeiro verificamos se o módulo já foi carregado
                if page_name in sys.modules:
                    # Se já foi carregado, removemos para poder recarregar
                    del sys.modules[page_name]
                
                # Mapear nomes de páginas para os arquivos reais
                page_map = {
                    'alunos': '1_Alunos.py',
                    'pagamentos': 'pages/pagamentos.py',
                    'estagios': 'pages/estagios.py',
                    'relatorios': 'pages/relatorios.py'
                }
                
                # Caminho do arquivo da página
                file_path = page_map.get(page_name, f"pages/{page_name}.py")
                
                # Carrega o módulo
                module = load_module_from_path(page_name, file_path)
                
                # Módulo carregado com sucesso
                return True
            except Exception as e:
                st.error(f"Erro ao carregar a página {page_name}: {e}")
                return False
        
        # Navegação baseada na variável da sessão
        if st.session_state.get("mostrar_trocar_senha", False):
            pagina_trocar_senha()
            if st.button("Voltar ao Dashboard"):
                st.session_state["mostrar_trocar_senha"] = False
                st.session_state['nav_page'] = 'dashboard'
                st.rerun()
        
        elif st.session_state.get("mostrar_gerenciamento_usuarios", False):
            pagina_gerenciar_usuarios()
            if st.button("Voltar ao Dashboard"):
                st.session_state["mostrar_gerenciamento_usuarios"] = False
                st.session_state['nav_page'] = 'dashboard'
                st.rerun()
        
        elif st.session_state.get("mostrar_configuracoes", False):
            st.subheader("Configurações do Sistema")
            
            # Carregar configurações atuais
            config = load_config()
            
            # Upload de logo
            st.write("### Logo do Sistema")
            st.write("Faça upload de uma nova imagem para usar como logo do sistema.")
            
            uploaded_file = st.file_uploader("Escolher imagem", type=['png', 'jpg', 'jpeg', 'svg'])
            if uploaded_file is not None:
                # Exibir preview da imagem
                st.image(uploaded_file, width=200, caption="Preview da nova logo")
                
                # Botão para salvar
                if st.button("Salvar Nova Logo"):
                    logo_path = save_uploaded_logo(uploaded_file)
                    if logo_path:
                        st.success(f"Logo atualizada com sucesso! Novo caminho: {logo_path}")
                        # Aguardar um pouco antes de recarregar
                        st.rerun()
            
            # Mostrar logo atual
            st.write("### Logo Atual")
            logo_path = get_logo_path()
            st.image(logo_path, width=150)
            
            # Opções para restaurar logo padrão
            if st.button("Restaurar Logo Padrão"):
                config["logo_path"] = "assets/images/logo.svg"
                save_config(config)
                st.success("Logo padrão restaurada com sucesso!")
                st.rerun()
            
            if st.button("Voltar ao Dashboard"):
                st.session_state["mostrar_configuracoes"] = False
                st.session_state['nav_page'] = 'dashboard'
                st.rerun()
        
        elif st.session_state.get("mostrar_backup", False):
            st.subheader("Backup de Dados")
            
            st.write("""
            Aqui você pode baixar todos os dados do sistema em formato CSV para backup ou análise externa.
            """)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if students_df is not None and not students_df.empty:
                    csv_students = students_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Baixar Dados de Alunos",
                        csv_students,
                        "alunos_backup.csv",
                        "text/csv",
                        key='download-students'
                    )
                else:
                    st.info("Não há dados de alunos para exportar.")
            
            with col2:
                if payments_df is not None and not payments_df.empty:
                    csv_payments = payments_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Baixar Dados de Pagamentos",
                        csv_payments,
                        "pagamentos_backup.csv",
                        "text/csv",
                        key='download-payments'
                    )
                else:
                    st.info("Não há dados de pagamentos para exportar.")
            
            with col3:
                if internships_df is not None and not internships_df.empty:
                    csv_internships = internships_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Baixar Dados de Estágios",
                        csv_internships,
                        "estagios_backup.csv",
                        "text/csv",
                        key='download-internships'
                    )
                else:
                    st.info("Não há dados de estágios para exportar.")
            
            # Opção de backup completo
            st.subheader("Backup Completo")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # TODO: Implementar zip de múltiplos arquivos quando necessário
            
            if st.button("Voltar ao Dashboard"):
                st.session_state["mostrar_backup"] = False
                st.session_state['nav_page'] = 'dashboard'
                st.rerun()
        
        # Carregar a página com base na navegação
        elif st.session_state['nav_page'] == 'alunos':
            # Carregar página de alunos
            load_page_module('alunos')
            
        elif st.session_state['nav_page'] == 'pagamentos':
            # Carregar página de pagamentos
            load_page_module('pagamentos')
            
        elif st.session_state['nav_page'] == 'estagios':
            # Carregar página de estágios
            load_page_module('estagios')
            
        elif st.session_state['nav_page'] == 'relatorios':
            # Carregar página de relatórios
            load_page_module('relatorios')
            
        else:  # dashboard é o padrão
            # Dashboard
            st.header("Dashboard")

            # Create columns for metrics
            col1, col2, col3, col4 = st.columns(4)

            # Get active and canceled students
            active_students = get_active_students(students_df)
            canceled_students = get_canceled_students(students_df)
            overdue_payments = get_overdue_payments(students_df, payments_df)

            # Calculate metrics
            total_students = len(students_df)
            active_count = len(active_students)
            canceled_count = len(canceled_students)
            overdue_count = len(overdue_payments)

            with col1:
                st.metric("Total de Alunos", total_students)

            with col2:
                st.metric("Alunos Ativos", active_count)

            with col3:
                st.metric("Alunos Cancelados", canceled_count)

            with col4:
                st.metric("Pagamentos Atrasados", overdue_count)
            
            # Financial projection
            st.subheader("Projeção Financeira Mensal")

            current_month = datetime.now().month
            current_year = datetime.now().year

            monthly_revenue = calculate_monthly_revenue(students_df, payments_df, current_month, current_year)
            st.info(f"Receita projetada para {calendar.month_name[current_month]}/{current_year}: {format_currency(monthly_revenue)}")

            # Create two columns for the charts
            col1, col2 = st.columns(2)

            with col1:
                # Cancellation trend
                if not canceled_students.empty:
                    # Convert cancellation dates to datetime with error handling
                    canceled_students['cancellation_date'] = pd.to_datetime(canceled_students['cancellation_date'], errors='coerce')
                    
                    # Group by month and count cancellations
                    cancellations_by_month = canceled_students.groupby(
                        canceled_students['cancellation_date'].dt.strftime('%Y-%m')
                    ).size().reset_index(name='count')
                    cancellations_by_month.columns = ['Mês', 'Cancelamentos']
                    
                    # Create bar chart for cancellations
                    if not cancellations_by_month.empty:
                        fig = px.bar(
                            cancellations_by_month, 
                            x='Mês', 
                            y='Cancelamentos',
                            title='Cancelamentos por Mês'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.write("Não há dados de cancelamento para exibir.")
                else:
                    st.write("Não há dados de cancelamento para exibir.")

            with col2:
                # Payment status distribution
                if not payments_df.empty:
                    payment_status = payments_df['status'].value_counts().reset_index()
                    payment_status.columns = ['Status', 'Quantidade']
                    
                    # Map status to Portuguese
                    status_map = {
                        'paid': 'Pago',
                        'pending': 'Pendente',
                        'overdue': 'Atrasado',
                        'canceled': 'Cancelado'
                    }
                    payment_status['Status'] = payment_status['Status'].map(status_map)
                    
                    fig = px.pie(
                        payment_status, 
                        names='Status', 
                        values='Quantidade',
                        title='Distribuição de Status de Pagamento',
                        color='Status',
                        color_discrete_map={
                            'Pago': 'green',
                            'Pendente': 'orange',
                            'Atrasado': 'red',
                            'Cancelado': 'gray'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write("Não há dados de pagamento para exibir.")
            
            # Students with overdue payments
            st.subheader("Alunos com Pagamentos Atrasados")

            if not overdue_payments.empty:
                # Verificar colunas disponíveis e selecionar apenas as que existem
                available_columns = []
                column_config = {}
                
                # Definir quais colunas exibir (apenas se existirem)
                if 'name' in overdue_payments.columns:
                    available_columns.append('name')
                    column_config['name'] = 'Nome'
                
                if 'phone' in overdue_payments.columns:
                    available_columns.append('phone')
                    column_config['phone'] = 'Telefone'
                
                if 'email' in overdue_payments.columns:
                    available_columns.append('email')
                    column_config['email'] = 'Email'
                
                if 'monthly_fee' in overdue_payments.columns:
                    available_columns.append('monthly_fee')
                    column_config['monthly_fee'] = 'Mensalidade'
                
                if 'last_due_date' in overdue_payments.columns:
                    available_columns.append('last_due_date')
                    column_config['last_due_date'] = 'Último Vencimento'
                
                if 'days_overdue' in overdue_payments.columns:
                    available_columns.append('days_overdue')
                    column_config['days_overdue'] = 'Dias em Atraso'
                
                # Verificar se temos colunas para exibir
                if available_columns:
                    st.dataframe(
                        overdue_payments[available_columns], 
                        use_container_width=True,
                        column_config=column_config
                    )
                else:
                    st.warning("Não foi possível exibir dados de pagamentos atrasados: formato de dados inválido.")
            else:
                st.success("Não há pagamentos atrasados no momento.")
            
            # Internship summary
            st.subheader("Resumo de Estágios")

            if not internships_df.empty:
                # Calculate total internship hours
                total_hours = internships_df['duration_hours'].sum()
                total_internships = len(internships_df)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total de Estágios", total_internships)
                
                with col2:
                    st.metric("Total de Horas de Estágio", f"{total_hours:.1f}h")
                
                # Show recent internships
                st.write("Estágios Recentes:")
                
                # Convert date to datetime with error handling
                internships_df['date'] = pd.to_datetime(internships_df['date'], errors='coerce')
                
                # Sort by date (most recent first) and show top 5
                recent_internships = internships_df.sort_values('date', ascending=False).head(5)
                
                # Format date for display
                recent_internships['date'] = recent_internships['date'].dt.strftime('%d/%m/%Y')
                
                st.dataframe(recent_internships[['date', 'topic', 'duration_hours']], use_container_width=True)
            else:
                st.info("Não há dados de estágio registrados ainda.")

            st.markdown("""
            ---
            ### Navegação
            Utilize o menu lateral para acessar as diferentes funcionalidades do sistema:
            - **Alunos**: Cadastro e gerenciamento de alunos
            - **Pagamentos**: Registro e controle de pagamentos
            - **Estágios**: Registro e acompanhamento de estágios
            - **Relatórios**: Relatórios detalhados e exportação de dados
            """)
