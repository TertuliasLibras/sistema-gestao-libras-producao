import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import os
import re

# Verificação de autenticação
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning('Você precisa fazer login para acessar esta página.')
    st.stop()

# Importação de funções auxiliares
from utils import (
    load_students_data, 
    save_students_data,
    load_payments_data,
    save_payments_data,
    format_currency,
    format_phone,
    generate_monthly_payments
)

# Título da página
st.title('Gestão de Alunos')

# Carregar dados
students_df = load_students_data()
payments_df = load_payments_data()

# Seções via tabs
tab1, tab2 = st.tabs(["Cadastrar Aluno", "Editar/Excluir Aluno"])

with tab1:
    st.header("Cadastro de Novo Aluno")
    
    # Criar formulário de cadastro
    with st.form("student_form"):
        # Dados pessoais
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nome", help="Campo opcional")
            course_type = st.selectbox(
                "Tipo de Curso", 
                options=["Aperfeiçoamento", "Pós-Graduação"], 
                help="Selecione o tipo de curso"
            )
            payment_plan = st.number_input(
                "Plano de Pagamento (meses)", 
                min_value=1, 
                max_value=36, 
                value=12, 
                help="Número de parcelas"
            )
            due_day = st.number_input(
                "Dia de Vencimento", 
                min_value=1, 
                max_value=28, 
                value=10, 
                help="Dia do mês para vencimento das parcelas"
            )
        
        with col2:
            phone = st.text_input(
                "Telefone (WhatsApp)", 
                help="Use apenas números: Ex: 21984567890"
            )
            cpf = st.text_input(
                "CPF", 
                help="Campo obrigatório. Use apenas números, sem pontos ou traços."
            )
            monthly_fee = st.number_input(
                "Mensalidade (R$)", 
                min_value=0.0, 
                value=0.0, 
                step=50.0,
                help="Valor da mensalidade"
            )
            source = st.selectbox(
                "Origem do Cadastro", 
                options=["Venda direta", "Evento Online", "Indicação"],
                help="Como o aluno conheceu o curso"
            )
        
        enrollment_date = st.date_input(
            "Data de Matrícula", 
            datetime.now().date(),
            help="Data em que o aluno se matriculou"
        )
        
        notes = st.text_area(
            "Observações", 
            "",
            help="Informações adicionais sobre o aluno"
        )
        
        # Botão de submissão
        submit_button = st.form_submit_button("Cadastrar")
        
        if submit_button:
            # Validar campos obrigatórios
            if not cpf:
                st.error("O campo CPF é obrigatório para o cadastro.")
            elif not phone:
                st.error("O campo Telefone é obrigatório para o cadastro.")
            else:
                # Verificar se já existe um aluno com o mesmo telefone
                if not students_df.empty and 'phone' in students_df.columns and phone in students_df['phone'].values:
                    st.warning(f"Já existe um aluno cadastrado com o telefone {phone}.")
                else:
                    # Criar objeto de dados
                    student_data = {
                        'phone': phone,
                        'name': name,
                        'cpf': cpf,
                        'course_type': course_type,
                        'enrollment_date': enrollment_date.strftime('%Y-%m-%d'),
                        'monthly_fee': monthly_fee,
                        'status': 'active',
                        'notes': notes,
                        'source': source,
                        'due_day': due_day,
                        'payment_plan': payment_plan
                    }
                    
                    # Adicionar ao dataframe se o dataframe já existir
                    if students_df is None or students_df.empty:
                        students_df = pd.DataFrame([student_data])
                    else:
                        students_df = pd.concat([students_df, pd.DataFrame([student_data])], ignore_index=True)
                    
                    # Salvar dados
                    save_students_data(students_df)
                    
                    # Gerar pagamentos mensais
                    payment_records = generate_monthly_payments(
                        student_phone=phone,
                        monthly_fee=monthly_fee,
                        enrollment_date=enrollment_date,
                        payment_plan=payment_plan,
                        due_day=due_day
                    )
                    
                    # Adicionar pagamentos ao dataframe
                    if payments_df is None or payments_df.empty:
                        # Criar dataframe do zero com a estrutura correta
                        payments_df = pd.DataFrame(payment_records)
                    else:
                        # Adicionar novos pagamentos
                        payments_df = pd.concat([payments_df, pd.DataFrame(payment_records)], ignore_index=True)
                    
                    # Salvar pagamentos
                    save_payments_data(payments_df)
                    
                    st.success(f"Aluno cadastrado com sucesso! {len(payment_records)} pagamentos gerados.")
                    st.rerun()

with tab2:
    st.header("Editar ou Excluir Aluno")
    
    # Verificar se há alunos cadastrados
    if not students_df.empty and 'phone' in students_df.columns:
        # Formatar telefones para exibição
        display_phones = {}
        for _, student in students_df.iterrows():
            phone = student['phone']
            
            # Pegar nome se disponível, senão usar telefone formatado
            if 'name' in student and student['name']:
                display_text = f"{student['name']} - {format_phone(phone)}"
            else:
                display_text = format_phone(phone)
                
            display_phones[phone] = display_text
        
        # Dropdown para seleção do aluno
        selected_phone = st.selectbox(
            "Selecione o aluno",
            options=list(display_phones.keys()),
            format_func=lambda x: display_phones[x]
        )
        
        if selected_phone:
            # Obter dados do aluno selecionado
            student = students_df[students_df['phone'] == selected_phone].iloc[0].to_dict()
            
            # Formulário para edição dos dados
            with st.form("edit_student_form"):
                st.subheader("Dados do Aluno")
                
                # Dados pessoais
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Nome", student.get('name', ''))
                    course_type = st.selectbox(
                        "Tipo de Curso", 
                        options=["Aperfeiçoamento", "Pós-Graduação"],
                        index=0 if student.get('course_type') != "Pós-Graduação" else 1
                    )
                    payment_plan = st.number_input(
                        "Plano de Pagamento (meses)", 
                        min_value=1, 
                        max_value=36, 
                        value=int(student.get('payment_plan', 12))
                    )
                    due_day = st.number_input(
                        "Dia de Vencimento", 
                        min_value=1, 
                        max_value=28, 
                        value=int(student.get('due_day', 10))
                    )
                
                with col2:
                    st.text_input("Telefone", selected_phone, disabled=True)
                    cpf = st.text_input("CPF", student.get('cpf', ''))
                    monthly_fee = st.number_input(
                        "Mensalidade (R$)", 
                        min_value=0.0, 
                        value=float(student.get('monthly_fee', 0)),
                        step=50.0
                    )
                    source = st.selectbox(
                        "Origem do Cadastro", 
                        options=["Venda direta", "Evento Online", "Indicação"],
                        index=0 if student.get('source') not in ["Evento Online", "Indicação"] else 
                             (1 if student.get('source') == "Evento Online" else 2)
                    )
                
                # Data de inscrição
                enrollment_date_str = student.get('enrollment_date')
                if enrollment_date_str:
                    try:
                        enrollment_date = datetime.strptime(enrollment_date_str, '%Y-%m-%d').date()
                    except:
                        enrollment_date = datetime.now().date()
                else:
                    enrollment_date = datetime.now().date()
                
                enrollment_date = st.date_input("Data de Matrícula", enrollment_date)
                
                # Status
                status = st.selectbox(
                    "Status",
                    options=["active", "canceled"],
                    index=0 if student.get('status') != "canceled" else 1
                )
                
                # Campos adicionais para cancelamento
                if status == "canceled":
                    cancellation_date_str = student.get('cancellation_date')
                    if cancellation_date_str:
                        try:
                            cancellation_date = datetime.strptime(cancellation_date_str, '%Y-%m-%d').date()
                        except:
                            cancellation_date = datetime.now().date()
                    else:
                        cancellation_date = datetime.now().date()
                    
                    cancellation_date = st.date_input("Data de Cancelamento", cancellation_date)
                    cancellation_fee_paid = st.checkbox("Multa de Cancelamento Paga", student.get('cancellation_fee_paid', False))
                else:
                    cancellation_date = None
                    cancellation_fee_paid = False
                
                # Observações
                notes = st.text_area("Observações", student.get('notes', ''))
                
                # Botões para atualizar ou excluir
                col1, col2 = st.columns(2)
                
                with col1:
                    update_button = st.form_submit_button("Atualizar Dados")
                
                with col2:
                    delete_button = st.form_submit_button("Excluir Aluno", type="primary", use_container_width=True, help="Atenção: Esta ação não pode ser desfeita!")
                
                if update_button:
                    # Update student record
                    students_df.loc[students_df['phone'] == selected_phone, 'name'] = name
                    
                    # Ensure required columns exist
                    for column in ['cpf', 'course_type', 'payment_plan', 'due_day', 'source']:
                        if column not in students_df.columns:
                            students_df[column] = None
                    
                    students_df.loc[students_df['phone'] == selected_phone, 'cpf'] = cpf
                    students_df.loc[students_df['phone'] == selected_phone, 'course_type'] = course_type
                    students_df.loc[students_df['phone'] == selected_phone, 'payment_plan'] = payment_plan
                    students_df.loc[students_df['phone'] == selected_phone, 'enrollment_date'] = enrollment_date.strftime('%Y-%m-%d')
                    students_df.loc[students_df['phone'] == selected_phone, 'monthly_fee'] = monthly_fee
                    students_df.loc[students_df['phone'] == selected_phone, 'status'] = status
                    students_df.loc[students_df['phone'] == selected_phone, 'notes'] = notes
                    students_df.loc[students_df['phone'] == selected_phone, 'due_day'] = due_day
                    students_df.loc[students_df['phone'] == selected_phone, 'source'] = source
                    
                    if status == 'canceled':
                        students_df.loc[students_df['phone'] == selected_phone, 'cancellation_date'] = cancellation_date.strftime('%Y-%m-%d')
                        students_df.loc[students_df['phone'] == selected_phone, 'cancellation_fee_paid'] = cancellation_fee_paid
                    
                    # Save data
                    save_students_data(students_df)
                    
                    # Update monthly fee in pending payments if it changed
                    if monthly_fee != student['monthly_fee'] and not payments_df.empty:
                        pending_payments = payments_df[
                            (payments_df['phone'] == selected_phone) & 
                            (payments_df['status'] == 'pending')
                        ]
                        
                        if not pending_payments.empty:
                            payments_df.loc[
                                (payments_df['phone'] == selected_phone) & 
                                (payments_df['status'] == 'pending'),
                                'amount'
                            ] = monthly_fee
                            
                            save_payments_data(payments_df)
                    
                    st.success("Dados do aluno atualizados com sucesso!")
                    st.rerun()
                
                if delete_button:
                    # Usar as funções de delete diretas da database
                    from database import delete_student, delete_student_payments
                    
                    # Excluir o aluno e seus pagamentos
                    success_student = delete_student(selected_phone)
                    success_payments = delete_student_payments(selected_phone)
                    
                    if success_student and success_payments:
                        st.success("Aluno excluído com sucesso!")
                        st.rerun()
                    elif success_student:
                        st.warning("Aluno excluído, mas houve um problema ao excluir os pagamentos associados.")
                        st.rerun()
                    else:
                        st.error("Erro ao excluir o aluno. Por favor, tente novamente.")
    else:
        st.info("Não há alunos cadastrados ainda.")
