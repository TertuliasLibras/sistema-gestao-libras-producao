import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from utils import (
    load_students_data, 
    load_payments_data,
    save_payments_data,
    format_phone,
    format_currency,
    get_active_students
)
from login import verificar_autenticacao, mostrar_pagina_login

# Importar verificação de autenticação universal
from auth_wrapper import verify_authentication

# Verificar autenticação
verify_authentication()

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

# Header with logo
col1, col2 = st.columns([1, 3])
with col1:
    try:
        # Usar função para obter o caminho da logo
        from config import get_logo_path
        logo_path = get_logo_path()
        st.image(logo_path, width=120)
    except Exception as e:
        st.warning(f"Erro ao carregar a logo: {e}")
        st.image('assets/images/logo.svg', width=120)
with col2:
    st.title("Gerenciamento de Pagamentos")

# Load data
students_df = load_students_data()
payments_df = load_payments_data()

# Create tabs for different operations
tab1, tab2, tab3 = st.tabs(["Registrar Pagamento", "Listar Pagamentos", "Gerar Pagamentos Mensais"])

with tab1:
    st.subheader("Registrar Novo Pagamento")
    
    # Botão para recarregar dados
    if st.button("🔄 Recarregar Dados", use_container_width=True):
        st.cache_data.clear()
        students_df = load_students_data()
        payments_df = load_payments_data()
        st.success("Dados recarregados com sucesso!")
    
    if students_df is not None and not students_df.empty:
        # Get active students
        active_students = get_active_students(students_df)
        
        if not active_students.empty:
            with st.form("payment_form"):
                # Student selection
                selected_phone = st.selectbox(
                    "Selecione o aluno:",
                    options=active_students['phone'].tolist(),
                    format_func=lambda x: f"{format_phone(x)} - {active_students[active_students['phone'] == x]['name'].values[0]}"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Get monthly fee
                    student_fee = active_students[active_students['phone'] == selected_phone]['monthly_fee'].values[0]
                    
                    payment_date = st.date_input("Data do Pagamento", datetime.now())
                    
                    # Get current month and year
                    today = datetime.now()
                    current_month = today.month
                    current_year = today.year
                    
                    # Month and year selection
                    month_options = list(range(1, 13))
                    month_reference = st.selectbox(
                        "Mês de Referência",
                        options=month_options,
                        format_func=lambda x: calendar.month_name[x],
                        index=current_month - 1
                    )
                    
                    year_reference = st.number_input(
                        "Ano de Referência",
                        min_value=2020,
                        max_value=2050,
                        value=current_year
                    )
                
                with col2:
                    amount = st.number_input(
                        "Valor (R$)",
                        min_value=0.0,
                        value=float(student_fee),
                        step=10.0
                    )
                    
                    status = st.selectbox(
                        "Status",
                        options=['paid', 'pending', 'overdue', 'canceled'],
                        format_func=lambda x: {
                            'paid': 'Pago',
                            'pending': 'Pendente',
                            'overdue': 'Atrasado',
                            'canceled': 'Cancelado'
                        }[x],
                        index=0
                    )
                    
                    # Calculate due date (10th of the reference month)
                    due_date = datetime(year_reference, month_reference, 10)
                    due_date_display = due_date.strftime('%d/%m/%Y')
                    st.info(f"Data de vencimento: {due_date_display}")
                
                notes = st.text_area("Observações", height=80, value=f"Mensalidade {calendar.month_name[month_reference]}/{year_reference}")
                
                # Opção para forçar substituição de um pagamento existente
                force_overwrite = st.checkbox("⚠️ Substituir pagamento existente (se houver)")
                
                submitted = st.form_submit_button("Registrar Pagamento")
                
                if submitted:
                    # Check if payment already exists
                    existing_payment = None
                    existing_payment_idx = None
                    
                    if not payments_df.empty:
                        # Verificar primeiro se temos as colunas month_reference e year_reference
                        if 'month_reference' in payments_df.columns and 'year_reference' in payments_df.columns:
                            existing_mask = (
                                (payments_df['phone'] == selected_phone) & 
                                (payments_df['month_reference'] == month_reference) & 
                                (payments_df['year_reference'] == year_reference)
                            )
                            existing_payment = payments_df[existing_mask]
                            if not existing_payment.empty:
                                existing_payment_idx = existing_payment.index
                        # Verificar se temos month e year
                        elif 'month' in payments_df.columns and 'year' in payments_df.columns:
                            existing_mask = (
                                (payments_df['phone'] == selected_phone) & 
                                (payments_df['month'] == month_reference) & 
                                (payments_df['year'] == year_reference)
                            )
                            existing_payment = payments_df[existing_mask]
                            if not existing_payment.empty:
                                existing_payment_idx = existing_payment.index
                    
                    if existing_payment is not None and not existing_payment.empty and not force_overwrite:
                        # Mostrar mensagem sobre pagamento existente
                        st.warning(f"Já existe um pagamento registrado para este aluno no mês {calendar.month_name[month_reference]}/{year_reference}.")
                        st.info("Marque a opção 'Substituir pagamento existente' se deseja sobrescrever.")
                    else:
                        # Create new payment record
                        new_payment = {
                            'phone': selected_phone,
                            'payment_date': payment_date.strftime('%Y-%m-%d') if status == 'paid' else None,
                            'due_date': due_date.strftime('%Y-%m-%d'),
                            'amount': amount,
                            'month_reference': month_reference,
                            'year_reference': year_reference,
                            'status': status,
                            'notes': notes
                        }
                        
                        # Se estamos substituindo um pagamento existente
                        if existing_payment is not None and not existing_payment.empty and force_overwrite:
                            # Remover o pagamento existente
                            payments_df = payments_df.drop(existing_payment_idx)
                        
                        # Add to dataframe
                        if payments_df is None or payments_df.empty:
                            payments_df = pd.DataFrame([new_payment])
                        else:
                            payments_df = pd.concat([payments_df, pd.DataFrame([new_payment])], ignore_index=True)
                        
                        # Save data
                        success = save_payments_data(payments_df)
                        
                        if success:
                            st.success("✅ Pagamento registrado com sucesso!")
                            st.info("Vá para a aba 'Listar Pagamentos' para ver todos os pagamentos.")
                            
                            # Limpar o cache para garantir que os dados sejam recarregados
                            st.cache_data.clear()
                        else:
                            st.error("❌ Erro ao registrar pagamento. Verifique os logs para mais detalhes.")
        else:
            st.warning("Não há alunos ativos cadastrados para registrar pagamentos.")
    else:
        st.info("Não há alunos cadastrados ainda.")

with tab2:
    st.subheader("Lista de Pagamentos")
    
    # Adicionar botão para recarregar dados
    if st.button("🔄 Recarregar Dados de Pagamentos", type="primary", use_container_width=True):
        # Recarregar dados
        st.cache_data.clear()
        payments_df = load_payments_data()
        st.success("Dados de pagamentos recarregados!")
        
    # Botões para filtros rápidos
    st.write("Filtros rápidos:")
    quick_filter_cols = st.columns(4)
    with quick_filter_cols[0]:
        if st.button("🔄 Todos os pagamentos", use_container_width=True):
            st.session_state['quick_status_filter'] = ["Todos"]
            st.rerun()
    with quick_filter_cols[1]:
        if st.button("✅ Apenas pagos", use_container_width=True):
            st.session_state['quick_status_filter'] = ["Pago"]
            st.rerun()
    with quick_filter_cols[2]:
        if st.button("⏳ Apenas pendentes", use_container_width=True):
            st.session_state['quick_status_filter'] = ["Pendente"]
            st.rerun()
    with quick_filter_cols[3]:
        if st.button("⚠️ Apenas atrasados", use_container_width=True):
            st.session_state['quick_status_filter'] = ["Atrasado"]
            st.rerun()
            
    # Inicializar filtro rápido se não existir
    if 'quick_status_filter' not in st.session_state:
        st.session_state['quick_status_filter'] = ["Todos"]
            
    # Filter options
    st.write("Filtros detalhados:")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.multiselect(
            "Status", 
            options=["Todos", "Pago", "Pendente", "Atrasado", "Cancelado"],
            default=st.session_state['quick_status_filter']
        )
    
    with col2:
        # Create month range
        months = list(range(1, 13))
        month_filter = st.multiselect(
            "Mês",
            options=["Todos"] + months,
            default=["Todos"],
            format_func=lambda x: x if x == "Todos" else calendar.month_name[x]
        )
    
    with col3:
        current_year = datetime.now().year
        year_options = list(range(current_year - 2, current_year + 2))
        year_filter = st.multiselect(
            "Ano",
            options=["Todos"] + year_options,
            default=["Todos"]
        )
    
    search_term = st.text_input("Buscar por nome ou telefone")
    
    if payments_df is not None and not payments_df.empty and students_df is not None and not students_df.empty:
        # Merge payments with student data
        merged_df = pd.merge(
            payments_df,
            students_df[['phone', 'name']],
            on='phone',
            how='left'
        )
        
        # Apply filters
        filtered_df = merged_df.copy()
        
        # Status filter
        status_map = {
            "Pago": "paid",
            "Pendente": "pending",
            "Atrasado": "overdue",
            "Cancelado": "canceled"
        }
        
        if "Todos" not in status_filter:
            status_values = [status_map[s] for s in status_filter]
            filtered_df = filtered_df[filtered_df['status'].isin(status_values)]
        
        # Month filter
        if "Todos" not in month_filter:
            if 'month_reference' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['month_reference'].isin(month_filter)]
            elif 'month' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['month'].isin(month_filter)]
        
        # Year filter
        if "Todos" not in year_filter:
            if 'year_reference' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['year_reference'].isin(year_filter)]
            elif 'year' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['year'].isin(year_filter)]
        
        # Search filter
        if search_term:
            search_term = search_term.lower()
            filtered_df = filtered_df[
                filtered_df['name'].str.lower().str.contains(search_term, na=False) |
                filtered_df['phone'].str.lower().str.contains(search_term, na=False)
            ]
        
        # Display dataframe
        if not filtered_df.empty:
            # Create a copy with formatted data for display
            display_df = filtered_df.copy()
            
            # Format phone numbers
            display_df['phone'] = display_df['phone'].apply(format_phone)
            
            # Format month reference
            if 'month_reference' in display_df.columns:
                display_df['month_name'] = display_df['month_reference'].apply(lambda x: calendar.month_name[x])
            elif 'month' in display_df.columns:
                display_df['month_name'] = display_df['month'].apply(lambda x: calendar.month_name[x])
            
            # Format status
            display_df['status'] = display_df['status'].map({
                'paid': 'Pago',
                'pending': 'Pendente',
                'overdue': 'Atrasado',
                'canceled': 'Cancelado'
            })
            
            # Format amount
            display_df['amount'] = display_df['amount'].apply(format_currency)
            
            # Format dates
            display_df['payment_date'] = pd.to_datetime(display_df['payment_date']).dt.strftime('%d/%m/%Y').fillna('-')
            display_df['due_date'] = pd.to_datetime(display_df['due_date']).dt.strftime('%d/%m/%Y')
            
            # Calculate if payment is late
            current_date = datetime.now().date()
            display_df['is_late'] = (
                (pd.to_datetime(filtered_df['due_date']).dt.date < current_date) & 
                (filtered_df['status'] != 'paid')
            )
            
            # Definir as colunas disponíveis para exibição
            display_columns = ['name', 'phone', 'month_name', 'amount', 'due_date', 'payment_date', 'status', 'is_late']
            column_labels = {
                'name': 'Nome',
                'phone': 'Telefone',
                'month_name': 'Mês',
                'amount': 'Valor',
                'due_date': 'Vencimento',
                'payment_date': 'Data Pagamento',
                'status': 'Status',
                'is_late': 'Atrasado'
            }
            column_order = ['name', 'phone', 'month_name', 'amount', 'due_date', 'payment_date', 'status', 'is_late']
            
            # Adicionar ano se disponível
            if 'year_reference' in display_df.columns:
                display_columns.append('year_reference')
                column_labels['year_reference'] = 'Ano'
                column_order.insert(3, 'year_reference')
            elif 'year' in display_df.columns:
                display_df['year_reference'] = display_df['year']  # Criar coluna temporária com nome padronizado
                display_columns.append('year_reference')
                column_labels['year_reference'] = 'Ano'
                column_order.insert(3, 'year_reference')
                
            # Use DataFrame com formatação personalizada
            st.dataframe(
                display_df[display_columns],
                use_container_width=True,
                column_config=column_labels,
                column_order=column_order,
                height=400
            )
            
            st.info(f"Total de pagamentos: {len(filtered_df)}")
            
            # Summary
            paid_total = filtered_df[filtered_df['status'] == 'paid']['amount'].sum()
            pending_total = filtered_df[filtered_df['status'] == 'pending']['amount'].sum()
            overdue_total = filtered_df[filtered_df['status'] == 'overdue']['amount'].sum()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Pago", format_currency(paid_total))
            
            with col2:
                st.metric("Total Pendente", format_currency(pending_total))
            
            with col3:
                st.metric("Total Atrasado", format_currency(overdue_total))
            
            # Export option
            if st.button("Exportar Lista (CSV)"):
                export_df = filtered_df.copy()
                # Format month name for export
                if 'month_reference' in export_df.columns:
                    export_df['month_name'] = export_df['month_reference'].apply(lambda x: calendar.month_name[x])
                elif 'month' in export_df.columns:
                    export_df['month_name'] = export_df['month'].apply(lambda x: calendar.month_name[x])
                # Convert to CSV
                csv = export_df.to_csv(index=False).encode('utf-8')
                
                # Create download button
                st.download_button(
                    "Baixar CSV",
                    csv,
                    "pagamentos.csv",
                    "text/csv",
                    key='download-csv'
                )
        else:
            st.warning("Nenhum pagamento encontrado com os filtros selecionados.")
    else:
        st.info("Não há pagamentos registrados ainda.")

with tab3:
    st.subheader("Gerar Pagamentos Mensais")
    
    st.write("""
    Esta ferramenta gera automaticamente registros de pagamento para todos os alunos ativos
    para um mês específico. Útil para criar registros de pagamento em lote.
    """)
    
    # Adicionar botão para limpar pagamentos do mês
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Recarregar Lista de Alunos", use_container_width=True):
            st.cache_data.clear()
            students_df = load_students_data()
            st.success("Lista de alunos recarregada!")
    
    with col2:
        if st.button("❌ Limpar Filtros de Mês", use_container_width=True):
            # Esta opção apenas fornece uma ação visual para o usuário
            # A limpeza real acontece no código abaixo
            st.success("Filtros de mês limpos, você pode gerar novos pagamentos!")
    
    if students_df is not None and not students_df.empty:
        # Get active students
        active_students = get_active_students(students_df)
        
        if not active_students.empty:
            with st.form("generate_payments_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Get current month and year
                    today = datetime.now()
                    current_month = today.month
                    current_year = today.year
                    
                    # Month and year selection
                    month_options = list(range(1, 13))
                    month_reference = st.selectbox(
                        "Mês de Referência",
                        options=month_options,
                        format_func=lambda x: calendar.month_name[x],
                        index=current_month - 1
                    )
                    
                    year_reference = st.number_input(
                        "Ano de Referência",
                        min_value=2020,
                        max_value=2050,
                        value=current_year
                    )
                
                with col2:
                    status = st.selectbox(
                        "Status Inicial",
                        options=['pending', 'paid'],
                        format_func=lambda x: 'Pendente' if x == 'pending' else 'Pago',
                        index=0
                    )
                    
                    # Calculate due date (10th of the reference month)
                    due_date = datetime(year_reference, month_reference, 10)
                    due_date_display = due_date.strftime('%d/%m/%Y')
                    st.info(f"Data de vencimento: {due_date_display}")
                
                # Opção para forçar a criação mesmo se já existir
                force_creation = st.checkbox("⚠️ Forçar criação (mesmo se já existirem pagamentos para este mês)")
                
                submitted = st.form_submit_button("Gerar Pagamentos")
                
                if submitted:
                    # Verificar se há pagamentos existentes
                    existing_phones = []
                    existing_payments = pd.DataFrame()
                    
                    if not payments_df.empty:
                        if 'month_reference' in payments_df.columns and 'year_reference' in payments_df.columns:
                            existing_payments = payments_df[
                                (payments_df['month_reference'] == month_reference) & 
                                (payments_df['year_reference'] == year_reference)
                            ]
                        elif 'month' in payments_df.columns and 'year' in payments_df.columns:
                            existing_payments = payments_df[
                                (payments_df['month'] == month_reference) & 
                                (payments_df['year'] == year_reference)
                            ]
                        
                        if not existing_payments.empty and not force_creation:
                            existing_phones = existing_payments['phone'].unique().tolist()
                    
                    # Se forçar criação estiver marcado, excluir pagamentos existentes
                    if force_creation and not existing_payments.empty:
                        # Remover pagamentos existentes para o mês
                        if 'month_reference' in payments_df.columns and 'year_reference' in payments_df.columns:
                            payments_df = payments_df[
                                ~((payments_df['month_reference'] == month_reference) & 
                                  (payments_df['year_reference'] == year_reference))
                            ]
                        elif 'month' in payments_df.columns and 'year' in payments_df.columns:
                            payments_df = payments_df[
                                ~((payments_df['month'] == month_reference) & 
                                  (payments_df['year'] == year_reference))
                            ]
                        
                        # Limpar lista de telefones existentes
                        existing_phones = []
                        
                        st.info(f"Pagamentos existentes para {calendar.month_name[month_reference]}/{year_reference} foram removidos.")
                    
                    # Obter alunos sem pagamentos para este mês
                    if force_creation:
                        students_to_generate = active_students  # Todos os alunos, se forçar criação
                    else:
                        students_to_generate = active_students[~active_students['phone'].isin(existing_phones)]
                    
                    if students_to_generate.empty and not force_creation:
                        st.warning("Todos os alunos ativos já possuem pagamentos registrados para este mês.")
                        st.info("Marque a opção 'Forçar criação' se deseja gerar novamente.")
                    else:
                        # Generate payment records
                        new_payments = []
                        
                        for _, student in students_to_generate.iterrows():
                            payment = {
                                'phone': student['phone'],
                                'payment_date': datetime.now().strftime('%Y-%m-%d') if status == 'paid' else None,
                                'due_date': due_date.strftime('%Y-%m-%d'),
                                'amount': student['monthly_fee'],
                                'month_reference': month_reference,
                                'year_reference': year_reference,
                                'status': status,
                                'notes': f"Mensalidade {calendar.month_name[month_reference]}/{year_reference}"
                            }
                            
                            new_payments.append(payment)
                        
                        # Add to dataframe
                        if payments_df is None or payments_df.empty:
                            payments_df = pd.DataFrame(new_payments)
                        else:
                            payments_df = pd.concat([payments_df, pd.DataFrame(new_payments)], ignore_index=True)
                        
                        # Save data
                        save_payments_data(payments_df)
                        
                        st.success(f"Gerados {len(new_payments)} registros de pagamento para {calendar.month_name[month_reference]}/{year_reference}.")
                        
                        # Recarregar dados para atualizar a interface
                        st.cache_data.clear()
        else:
            st.warning("Não há alunos ativos cadastrados para gerar pagamentos.")
    else:
        st.info("Não há alunos cadastrados ainda.")
