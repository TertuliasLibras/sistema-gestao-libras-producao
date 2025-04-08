import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

# Tentar importar login normalmente primeiro
try:
    from login import verificar_autenticacao, mostrar_pagina_login
except ImportError:
    # Se não conseguir, tentar o fallback
    try:
        from login_fallback import verificar_autenticacao, mostrar_pagina_login
    except ImportError:
        st.error("Não foi possível importar o módulo de login.")
        st.stop()

# Verificar autenticação
if not verificar_autenticacao():
    mostrar_pagina_login()
else:
    # Importar utils com tratamento de erro
    try:
        from utils import (
            load_students_data, 
            save_students_data,
            format_currency, 
            validate_phone,
            generate_monthly_payments
        )
    except ImportError as e:
        st.error(f"Erro ao importar módulos: {e}")
        st.info("Esta funcionalidade requer conexão com o banco de dados.")
        st.stop()
    
    st.title("Gerenciamento de Alunos")
    
    # Criar abas
    tab_list, tab_new, tab_manage = st.tabs(["Lista de Alunos", "Novo Aluno", "Gerenciar Aluno"])
    
    # Carregar dados
    students_df = load_students_data()
    
    # Aba Lista de Alunos
    with tab_list:
        st.subheader("Lista de Alunos")
        
        # Filtro de status
        status_filter = st.radio(
            "Filtrar por status:",
            ["Todos", "Ativos", "Cancelados"],
            horizontal=True,
            index=1  # Ativos como padrão
        )
        
        # Aplicar filtro de status
        if not students_df.empty:
            if 'status' in students_df.columns:
                if status_filter == "Ativos":
                    filtered_df = students_df[students_df['status'] == 'active']
                elif status_filter == "Cancelados":
                    filtered_df = students_df[students_df['status'] == 'canceled']
                else:
                    filtered_df = students_df
            else:
                filtered_df = students_df
                st.warning("Coluna 'status' não encontrada nos dados.")
            
            # Filtro de texto
            search_term = st.text_input("Buscar por nome ou telefone:")
            if search_term:
                search_term = search_term.lower()
                mask = (
                    students_df['name'].str.lower().str.contains(search_term, na=False) |
                    students_df['phone'].str.lower().str.contains(search_term, na=False)
                )
                filtered_df = filtered_df[mask]
            
            # Mostrar dados
            if not filtered_df.empty:
                # Mostrar colunas selecionadas
                display_cols = ['name', 'phone', 'enrollment_date', 'status', 'monthly_fee']
                # Verificar se todas as colunas existem
                display_cols = [col for col in display_cols if col in filtered_df.columns]
                
                # Preparar dados para exibição
                display_df = filtered_df[display_cols].copy()
                
                # Formatar valores
                if 'monthly_fee' in display_df.columns:
                    display_df['monthly_fee'] = display_df['monthly_fee'].apply(format_currency)
                if 'status' in display_df.columns:
                    display_df['status'] = display_df['status'].apply(
                        lambda x: "Ativo" if x == "active" else "Cancelado" if x == "canceled" else x
                    )
                
                st.dataframe(display_df, use_container_width=True)
                st.info(f"Total de alunos: {len(filtered_df)}")
            else:
                st.info("Nenhum aluno encontrado.")
        else:
            st.info("Nenhum aluno cadastrado.")
    
    # Aba Novo Aluno
    with tab_new:
        st.subheader("Cadastrar Novo Aluno")
        
        with st.form("new_student_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Nome completo", key="new_name")
                phone = st.text_input("Telefone (com DDD)", key="new_phone")
                cpf = st.text_input("CPF", key="new_cpf")
                address = st.text_input("Endereço", key="new_address")
                
                # Campo para origem do cadastro
                registration_origin = st.selectbox(
                    "Origem do Cadastro",
                    ["Instagram", "Facebook", "WhatsApp", "Indicação", "Google", "Outro"],
                    key="new_registration_origin"
                )
                
                if registration_origin == "Outro":
                    registration_origin_other = st.text_input("Especifique a origem:", key="new_registration_origin_other")
                    if registration_origin_other:
                        registration_origin = registration_origin_other
            
            with col2:
                # Tipo de curso
                course_type = st.selectbox(
                    "Tipo de Curso",
                    ["Aperfeiçoamento", "Pós-Graduação"],
                    key="new_course_type"
                )
                
                enrollment_date = st.date_input(
                    "Data de matrícula",
                    datetime.now().date(),
                    key="new_enrollment_date"
                )
                
                monthly_fee = st.number_input(
                    "Mensalidade (R$)",
                    min_value=0.0,
                    format="%.2f",
                    key="new_monthly_fee"
                )
                
                # Número de parcelas
                payment_plan = st.number_input(
                    "Número de parcelas",
                    min_value=1,
                    max_value=48,
                    value=12,
                    key="new_payment_plan"
                )
                
                # Dia de vencimento
                due_day = st.number_input(
                    "Dia de vencimento",
                    min_value=1,
                    max_value=28,
                    value=10,
                    key="new_due_day"
                )
                
                comments = st.text_area("Observações", key="new_comments")
            
            submitted = st.form_submit_button("Cadastrar")
            
            if submitted:
                # Validação de dados
                if not name or not phone:
                    st.error("Nome e telefone são obrigatórios.")
                elif not validate_phone(phone):
                    st.error("O telefone deve ter o formato correto (com DDD).")
                else:
                    # Verificar se telefone já existe
                    if not students_df.empty and 'phone' in students_df.columns and phone in students_df['phone'].values:
                        st.error(f"Já existe um aluno cadastrado com o telefone {phone}.")
                    else:
                        # Preparar dados
                        new_student = {
                            "name": name,
                            "phone": phone,
                            "cpf": cpf,
                            "address": address,
                            "course_type": course_type,
                            "enrollment_date": enrollment_date.strftime("%Y-%m-%d"),
                            "monthly_fee": monthly_fee,
                            "status": "active",
                            "comments": comments,
                            "registration_origin": registration_origin,
                            "payment_plan": payment_plan,
                            "due_day": due_day
                        }
                        
                        # Adicionar ao DataFrame
                        new_row = pd.DataFrame([new_student])
                        
                        # Se o DataFrame estiver vazio, criar um novo
                        if students_df.empty:
                            students_df = new_row
                        else:
                            students_df = pd.concat([students_df, new_row], ignore_index=True)
                        
                        # Salvar dados
                        try:
                            save_students_data(students_df)
                            
                            # Gerar pagamentos mensais
                            try:
                                # Calcular data final com base no número de parcelas
                                start_date = datetime.strptime(new_student["enrollment_date"], "%Y-%m-%d")
                                
                                # Gerar pagamentos
                                monthly_payments = generate_monthly_payments(
                                    student_phone=phone,
                                    monthly_fee=monthly_fee,
                                    enrollment_date=start_date,
                                    payment_plan=payment_plan,
                                    due_day=due_day
                                )
                                
                                if monthly_payments:
                                    # Importar função para salvar pagamentos
                                    from utils import save_payments_data
                                    
                                    # Adicionar pagamentos ao banco de dados
                                    payments_df = pd.DataFrame(monthly_payments)
                                    save_payments_data(payments_df)
                                    
                                    st.success(f"Aluno {name} cadastrado com sucesso! {len(monthly_payments)} mensalidades geradas.")
                                else:
                                    st.success(f"Aluno {name} cadastrado com sucesso!")
                                    st.warning("Não foi possível gerar as mensalidades.")
                            except Exception as e:
                                st.success(f"Aluno {name} cadastrado com sucesso!")
                                st.warning(f"Erro ao gerar mensalidades: {e}")
                        except Exception as e:
                            st.error(f"Erro ao salvar dados: {e}")
    
    # Aba Gerenciar Aluno
    with tab_manage:
        st.subheader("Gerenciar Aluno")
        
        # Seleção de aluno
        if not students_df.empty:
            student_list = students_df['name'].tolist() if 'name' in students_df.columns else []
            
            if student_list:
                student_name = st.selectbox("Selecione um aluno:", student_list)
                
                # Obter dados do aluno selecionado
                student_data = students_df[students_df['name'] == student_name].iloc[0]
                
                # Exibir formulário de edição
                with st.form("edit_student_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        name = st.text_input("Nome completo", value=student_data.get('name', ''), key="edit_name")
                        phone = st.text_input("Telefone (com DDD)", value=student_data.get('phone', ''), key="edit_phone", disabled=True)
                        cpf = st.text_input("CPF", value=student_data.get('cpf', ''), key="edit_cpf")
                        address = st.text_input("Endereço", value=student_data.get('address', ''), key="edit_address")
                        
                        # Campo para origem do cadastro
                        registration_origin = st.selectbox(
                            "Origem do Cadastro",
                            ["Instagram", "Facebook", "WhatsApp", "Indicação", "Google", "Outro"],
                            index=["Instagram", "Facebook", "WhatsApp", "Indicação", "Google", "Outro"].index(
                                student_data.get('registration_origin', 'Outro') if student_data.get('registration_origin', '') in ["Instagram", "Facebook", "WhatsApp", "Indicação", "Google"] else "Outro"
                            ),
                            key="edit_registration_origin"
                        )
                        
                        if registration_origin == "Outro":
                            registration_origin_other = st.text_input(
                                "Especifique a origem:",
                                value=student_data.get('registration_origin', ''),
                                key="edit_registration_origin_other"
                            )
                            if registration_origin_other:
                                registration_origin = registration_origin_other
                    
                    with col2:
                        # Tipo de curso
                        course_type = st.selectbox(
                            "Tipo de Curso",
                            ["Aperfeiçoamento", "Pós-Graduação"],
                            index=0 if student_data.get('course_type', '') == "Aperfeiçoamento" else 1,
                            key="edit_course_type"
                        )
                        
                        enrollment_date = st.date_input(
                            "Data de matrícula",
                            datetime.strptime(student_data.get('enrollment_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date(),
                            key="edit_enrollment_date"
                        )
                        
                        monthly_fee = st.number_input(
                            "Mensalidade (R$)",
                            min_value=0.0,
                            value=float(student_data.get('monthly_fee', 0)),
                            format="%.2f",
                            key="edit_monthly_fee"
                        )
                        
                        # Número de parcelas
                        payment_plan = st.number_input(
                            "Número de parcelas",
                            min_value=1,
                            max_value=48,
                            value=int(student_data.get('payment_plan', 12)),
                            key="edit_payment_plan"
                        )
                        
                        # Dia de vencimento
                        due_day = st.number_input(
                            "Dia de vencimento",
                            min_value=1,
                            max_value=28,
                            value=int(student_data.get('due_day', 10)),
                            key="edit_due_day"
                        )
                        
                        status = st.selectbox(
                            "Status",
                            ["active", "canceled"],
                            index=0 if student_data.get('status', '') == "active" else 1,
                            format_func=lambda x: "Ativo" if x == "active" else "Cancelado",
                            key="edit_status"
                        )
                        
                        comments = st.text_area("Observações", value=student_data.get('comments', ''), key="edit_comments")
                    
                    submitted = st.form_submit_button("Atualizar")
                    
                    if submitted:
                        # Validação de dados
                        if not name:
                            st.error("Nome é obrigatório.")
                        else:
                            # Preparar dados
                            updated_student = student_data.copy()
                            updated_student.update({
                                "name": name,
                                "cpf": cpf,
                                "address": address,
                                "course_type": course_type,
                                "enrollment_date": enrollment_date.strftime("%Y-%m-%d"),
                                "monthly_fee": monthly_fee,
                                "status": status,
                                "comments": comments,
                                "registration_origin": registration_origin,
                                "payment_plan": payment_plan,
                                "due_day": due_day
                            })
                            
                            # Atualizar no DataFrame
                            students_df.loc[students_df['phone'] == phone] = updated_student
                            
                            # Salvar dados
                            try:
                                save_students_data(students_df)
                                st.success(f"Dados do aluno {name} atualizados com sucesso!")
                            except Exception as e:
                                st.error(f"Erro ao salvar dados: {e}")
                
                # Opção para excluir aluno
                if st.button("Excluir Aluno", type="primary", help="Cuidado! Esta ação não pode ser desfeita."):
                    confirm = st.text_input("Digite o nome do aluno para confirmar a exclusão:")
                    
                    if confirm == student_data.get('name', ''):
                        # Excluir do DataFrame
                        students_df = students_df[students_df['phone'] != phone]
                        
                        # Excluir do banco de dados
                        try:
                            from database import delete_student, delete_student_payments
                            
                            # Excluir pagamentos associados
                            delete_student_payments(phone)
                            
                            # Excluir aluno
                            delete_student(phone)
                            
                            st.success(f"Aluno {name} excluído com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao excluir aluno: {e}")
            else:
                st.info("Nenhum aluno cadastrado.")
        else:
            st.info("Nenhum aluno cadastrado.")
