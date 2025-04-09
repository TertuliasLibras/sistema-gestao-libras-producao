import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from utils import (
    load_students_data, 
    load_payments_data,
    save_payments_data,
    format_currency,
    format_phone
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
tab1, tab2, tab3 = st.tabs(["Registrar Pagamentos", "Listar Pagamentos", "Editar Pagamentos"])

with tab1:
    st.subheader("Registrar Novo Pagamento")
    
    if students_df is not None and not students_df.empty:
        with st.form("payment_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Select student
                student_phone = st.selectbox(
                    "Selecione o aluno:",
                    options=students_df['phone'].tolist(),
                    format_func=lambda x: f"{format_phone(x)} - {students_df[students_df['phone'] == x]['name'].values[0]}"
                )
                
                # Get pending payments for this student
                if payments_df is not None and not payments_df.empty and student_phone:
                    pending_payments = payments_df[
                        (payments_df['student_phone'] == student_phone) & 
                        (payments_df['payment_status'] == 'pending')
                    ]
                    
                    if not pending_payments.empty:
                        # Format the due date for display
                        pending_payments['formatted_due_date'] = pd.to_datetime(pending_payments['due_date']).dt.strftime('%d/%m/%Y')
                        
                        # Create a readable description for each pending payment
                        payment_options = [
                            f"Parcela {row['installment_number']} - Vencimento: {row['formatted_due_date']} - Valor: R$ {row['amount']:.2f}" 
                            for _, row in pending_payments.iterrows()
                        ]
                        
                        # Map the display text back to the payment_id
                        payment_id_map = {
                            f"Parcela {row['installment_number']} - Vencimento: {row['formatted_due_date']} - Valor: R$ {row['amount']:.2f}": row['payment_id']
                            for _, row in pending_payments.iterrows()
                        }
                        
                        payment_description = st.selectbox(
                            "Selecione a parcela:",
                            options=payment_options
                        )
                        
                        payment_id = payment_id_map[payment_description]
                        
                        # Get the amount from the selected payment
                        selected_amount = pending_payments[pending_payments['payment_id'] == payment_id]['amount'].values[0]
                    else:
                        st.info("Este aluno não possui parcelas pendentes.")
                        payment_id = None
                        selected_amount = 0
                else:
                    st.info("Não há dados de pagamento disponíveis.")
                    payment_id = None
                    selected_amount = 0
            
            with col2:
                payment_date = st.date_input("Data do Pagamento", datetime.now())
                
                amount = st.number_input(
                    "Valor Pago (R$)", 
                    min_value=0.0, 
                    value=float(selected_amount) if selected_amount else 0.0, 
                    step=10.0
                )
                
                payment_method = st.selectbox(
                    "Forma de Pagamento",
                    options=["PIX", "Cartão de Crédito", "Boleto", "Transferência", "Dinheiro"]
                )
                
                notes = st.text_area("Observações", height=100)
            
            submitted = st.form_submit_button("Registrar Pagamento")
            
            if submitted:
                if not payment_id:
                    st.error("Por favor, selecione uma parcela para pagamento.")
                elif amount <= 0:
                    st.error("O valor do pagamento deve ser maior que zero.")
                else:
                    # Update payment status
                    payments_df.loc[payments_df['payment_id'] == payment_id, 'payment_status'] = 'paid'
                    payments_df.loc[payments_df['payment_id'] == payment_id, 'payment_date'] = payment_date.strftime('%Y-%m-%d')
                    payments_df.loc[payments_df['payment_id'] == payment_id, 'payment_method'] = payment_method
                    payments_df.loc[payments_df['payment_id'] == payment_id, 'paid_amount'] = amount
                    payments_df.loc[payments_df['payment_id'] == payment_id, 'notes'] = notes
                    
                    # Save updated data
                    save_payments_data(payments_df)
                    
                    st.success("Pagamento registrado com sucesso!")
    else:
        st.info("Não há alunos cadastrados ainda.")

with tab2:
    st.subheader("Lista de Pagamentos")
    
    # Filter options
    st.write("Filtros:")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.multiselect(
            "Status", 
            options=["Todos", "Pagos", "Pendentes", "Atrasados"],
            default=["Todos"]
        )
    
    with col2:
        date_filter = st.date_input(
            "Data de Referência",
            datetime.now()
        )
    
    with col3:
        student_filter = None
        if students_df is not None and not students_df.empty:
            student_options = ["Todos"] + students_df['phone'].tolist()
            
            student_filter = st.selectbox(
                "Filtrar por Aluno",
                options=student_options,
                format_func=lambda x: "Todos" if x == "Todos" else f"{format_phone(x)} - {students_df[students_df['phone'] == x]['name'].values[0]}"
            )
    
    if payments_df is not None and not payments_df.empty:
        # Apply filters
        filtered_df = payments_df.copy()
        
        # Student filter
        if student_filter and student_filter != "Todos":
            filtered_df = filtered_df[filtered_df['student_phone'] == student_filter]
        
        # Status filter
        if "Todos" not in status_filter:
            temp_df = pd.DataFrame()
            
            if "Pagos" in status_filter:
                temp_df = pd.concat([temp_df, filtered_df[filtered_df['payment_status'] == 'paid']])
            
            if "Pendentes" in status_filter:
                # Pendentes são os que ainda não foram pagos e não estão atrasados
                pending_df = filtered_df[
                    (filtered_df['payment_status'] == 'pending') & 
                    (pd.to_datetime(filtered_df['due_date']) >= pd.to_datetime(date_filter))
                ]
                temp_df = pd.concat([temp_df, pending_df])
            
            if "Atrasados" in status_filter:
                # Atrasados são os pendentes com data de vencimento anterior à data de referência
                overdue_df = filtered_df[
                    (filtered_df['payment_status'] == 'pending') & 
                    (pd.to_datetime(filtered_df['due_date']) < pd.to_datetime(date_filter))
                ]
                temp_df = pd.concat([temp_df, overdue_df])
            
            filtered_df = temp_df
        
        # Display dataframe if not empty
        if not filtered_df.empty:
            # Create a copy with formatted data for display
            display_df = filtered_df.copy()
            
            # Add student name column from students_df
            if students_df is not None and not students_df.empty:
                # Create a map of phone to name
                phone_to_name = dict(zip(students_df['phone'], students_df['name']))
                
                # Add a column with student name
                display_df['student_name'] = display_df['student_phone'].map(phone_to_name)
            
            # Format phone numbers
            display_df['student_phone'] = display_df['student_phone'].apply(format_phone)
            
            # Format payment status with colors
            def format_status(status, due_date):
                due_date = pd.to_datetime(due_date)
                if status == 'paid':
                    return 'Pago'
                elif status == 'pending':
                    if due_date < pd.to_datetime(date_filter):
                        return 'Atrasado'
                    else:
                        return 'Pendente'
                return status
            
            display_df['payment_status'] = display_df.apply(
                lambda row: format_status(row['payment_status'], row['due_date']), 
                axis=1
            )
            
            # Format dates to Brazilian format (dd/mm/yyyy)
            display_df['due_date'] = pd.to_datetime(display_df['due_date']).dt.strftime('%d/%m/%Y')
            display_df['payment_date'] = pd.to_datetime(display_df['payment_date'], errors='coerce').dt.strftime('%d/%m/%Y')
            
            # Format amounts as currency
            display_df['amount'] = display_df['amount'].apply(format_currency)
            display_df['paid_amount'] = display_df['paid_amount'].apply(
                lambda x: format_currency(x) if pd.notna(x) and x > 0 else ""
            )
            
            # Reorder and select columns for display
            columns_to_display = [
                'payment_id', 'student_name', 'student_phone', 'installment_number',
                'due_date', 'amount', 'payment_status', 'payment_date', 'paid_amount', 'payment_method'
            ]
            
            # Ensure all columns exist (older data might not have all columns)
            for col in columns_to_display:
                if col not in display_df.columns:
                    display_df[col] = ""
            
            # Custom column labels
            column_labels = {
                'payment_id': 'ID',
                'student_name': 'Nome do Aluno',
                'student_phone': 'Telefone',
                'installment_number': 'Parcela',
                'due_date': 'Vencimento',
                'amount': 'Valor',
                'payment_status': 'Status',
                'payment_date': 'Data Pagamento',
                'paid_amount': 'Valor Pago',
                'payment_method': 'Forma Pagamento'
            }
            
            # Display the dataframe
            st.dataframe(
                display_df[columns_to_display], 
                use_container_width=True,
                column_config={col: column_labels[col] for col in columns_to_display}
            )
            
            total_payments = len(filtered_df)
            total_paid = len(filtered_df[filtered_df['payment_status'] == 'paid'])
            total_pending = total_payments - total_paid
            
            # Calculate total amounts
            total_amount = filtered_df['amount'].sum()
            total_paid_amount = filtered_df[filtered_df['payment_status'] == 'paid']['amount'].sum()
            
            # Display summary
            st.info(f"""
            **Resumo:** {total_payments} pagamentos no total
            * Pagos: {total_paid} ({format_currency(total_paid_amount)})
            * Pendentes/Atrasados: {total_pending} ({format_currency(total_amount - total_paid_amount)})
            """)
            
            # Export option
            if st.button("Exportar Lista (CSV)"):
                export_df = filtered_df.copy()
                # Convert to CSV
                csv = export_df.to_csv(index=False).encode('utf-8')
                
                # Create download button
                st.download_button(
                    "Baixar CSV",
                    csv,
                    "pagamentos.csv",
                    "text/csv",
                    key='download-csv-payments'
                )
        else:
            st.warning("Nenhum pagamento encontrado com os filtros selecionados.")
    else:
        st.info("Não há pagamentos registrados ainda.")

with tab3:
    st.subheader("Editar Pagamentos")
    
    if payments_df is not None and not payments_df.empty and students_df is not None and not students_df.empty:
        # Create phone to name mapping
        phone_to_name = dict(zip(students_df['phone'], students_df['name']))
        
        # Allow selecting a student first
        student_options = students_df['phone'].tolist()
        
        selected_student = st.selectbox(
            "Selecione o aluno:",
            options=student_options,
            format_func=lambda x: f"{format_phone(x)} - {phone_to_name.get(x, 'Unknown')}"
        )
        
        if selected_student:
            # Get payments for this student
            student_payments = payments_df[payments_df['student_phone'] == selected_student]
            
            if not student_payments.empty:
                # Format for selection
                student_payments['formatted_due_date'] = pd.to_datetime(student_payments['due_date']).dt.strftime('%d/%m/%Y')
                
                payment_options = [
                    f"Parcela {row['installment_number']} - Vencimento: {row['formatted_due_date']} - Status: {'Pago' if row['payment_status'] == 'paid' else 'Pendente'}"
                    for _, row in student_payments.iterrows()
                ]
                
                payment_id_map = {
                    f"Parcela {row['installment_number']} - Vencimento: {row['formatted_due_date']} - Status: {'Pago' if row['payment_status'] == 'paid' else 'Pendente'}": row['payment_id']
                    for _, row in student_payments.iterrows()
                }
                
                # Select payment to edit
                payment_description = st.selectbox(
                    "Selecione a parcela para editar:",
                    options=payment_options
                )
                
                payment_id = payment_id_map[payment_description]
                
                # Get payment data
                payment = payments_df[payments_df['payment_id'] == payment_id].iloc[0]
                
                # Create edit form
                with st.form("edit_payment_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        status = st.selectbox(
                            "Status",
                            options=['pending', 'paid'],
                            format_func=lambda x: 'Pago' if x == 'paid' else 'Pendente',
                            index=1 if payment['payment_status'] == 'paid' else 0
                        )
                        
                        due_date = st.date_input(
                            "Data de Vencimento",
                            pd.to_datetime(payment['due_date']).date() if pd.notna(payment['due_date']) else datetime.now()
                        )
                        
                        amount = st.number_input(
                            "Valor da Parcela (R$)",
                            min_value=0.0,
                            value=float(payment['amount']),
                            step=10.0
                        )
                    
                    with col2:
                        payment_date = None
                        payment_method = None
                        paid_amount = None
                        
                        if status == 'paid':
                            payment_date = st.date_input(
                                "Data do Pagamento",
                                pd.to_datetime(payment['payment_date']).date() if pd.notna(payment['payment_date']) else datetime.now()
                            )
                            
                            payment_method = st.selectbox(
                                "Forma de Pagamento",
                                options=["PIX", "Cartão de Crédito", "Boleto", "Transferência", "Dinheiro"],
                                index=0 if 'payment_method' not in payment or pd.isna(payment['payment_method']) 
                                       else ["PIX", "Cartão de Crédito", "Boleto", "Transferência", "Dinheiro"].index(payment['payment_method'])
                            )
                            
                            paid_amount = st.number_input(
                                "Valor Pago (R$)",
                                min_value=0.0,
                                value=float(payment['paid_amount']) if 'paid_amount' in payment and pd.notna(payment['paid_amount']) else float(payment['amount']),
                                step=10.0
                            )
                    
                    notes = st.text_area(
                        "Observações",
                        value=payment['notes'] if 'notes' in payment and pd.notna(payment['notes']) else "",
                        height=100
                    )
                    
                    submitted = st.form_submit_button("Atualizar Pagamento")
                    
                    if submitted:
                        # Update payment data
                        payments_df.loc[payments_df['payment_id'] == payment_id, 'payment_status'] = status
                        payments_df.loc[payments_df['payment_id'] == payment_id, 'due_date'] = due_date.strftime('%Y-%m-%d')
                        payments_df.loc[payments_df['payment_id'] == payment_id, 'amount'] = amount
                        payments_df.loc[payments_df['payment_id'] == payment_id, 'notes'] = notes
                        
                        if status == 'paid':
                            payments_df.loc[payments_df['payment_id'] == payment_id, 'payment_date'] = payment_date.strftime('%Y-%m-%d')
                            payments_df.loc[payments_df['payment_id'] == payment_id, 'payment_method'] = payment_method
                            payments_df.loc[payments_df['payment_id'] == payment_id, 'paid_amount'] = paid_amount
                        else:
                            # Clear payment data if status is pending
                            payments_df.loc[payments_df['payment_id'] == payment_id, 'payment_date'] = None
                            payments_df.loc[payments_df['payment_id'] == payment_id, 'payment_method'] = None
                            payments_df.loc[payments_df['payment_id'] == payment_id, 'paid_amount'] = None
                        
                        # Save updated data
                        save_payments_data(payments_df)
                        
                        st.success("Pagamento atualizado com sucesso!")
            else:
                st.info("Este aluno não possui pagamentos registrados.")
    else:
        st.info("Não há pagamentos ou alunos registrados ainda.")
