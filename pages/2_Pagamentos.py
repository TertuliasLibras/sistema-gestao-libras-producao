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
            load_payments_data,
            save_payments_data,
            format_currency
        )
    except ImportError as e:
        st.error(f"Erro ao importar módulos: {e}")
        st.info("Esta funcionalidade requer conexão com o banco de dados.")
        st.stop()
    
    st.title("Gerenciamento de Pagamentos")
    
    # Carregar dados
    students_df = load_students_data()
    payments_df = load_payments_data()
    
    # Verificar se há dados
    if students_df.empty:
        st.warning("Não há alunos cadastrados.")
        st.stop()
    
    # Criar abas
    tab_list, tab_new, tab_manage = st.tabs(["Lista de Pagamentos", "Novo Pagamento", "Gerenciar Pagamento"])
    
    # Aba Lista de Pagamentos
    with tab_list:
        st.subheader("Lista de Pagamentos")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtro de status
            status_filter = st.selectbox(
                "Status:",
                ["Todos", "Pendente", "Pago", "Atrasado"],
                index=0
            )
        
        with col2:
            # Filtro de mês
            current_month = datetime.now().month
            month_filter = st.selectbox(
                "Mês:",
                list(range(1, 13)),
                index=current_month - 1,
                format_func=lambda x: calendar.month_name[x]
            )
        
        with col3:
            # Filtro de ano
            current_year = datetime.now().year
            year_filter = st.selectbox(
                "Ano:",
                list(range(current_year - 2, current_year + 3)),
                index=2
            )
        
        # Filtro de aluno
        student_filter = st.selectbox(
            "Aluno:",
            ["Todos"] + students_df['name'].tolist() if 'name' in students_df.columns else ["Todos"]
        )
        
        # Filtrar pagamentos
        if not payments_df.empty:
            # Copiar para não modificar o original
            filtered_df = payments_df.copy()
            
            # Aplicar filtros
            # Filtro de status
            if status_filter != "Todos" and 'status' in filtered_df.columns:
                status_map = {
                    "Pendente": "pending",
                    "Pago": "paid",
                    "Atrasado": "overdue"
                }
                if status_filter in status_map:
                    # Para o status "Atrasado", verificar data de vencimento e status pendente
                    if status_filter == "Atrasado":
                        today = datetime.now().date()
                        mask = (
                            (filtered_df['status'] == "pending") &
                            (pd.to_datetime(filtered_df['due_date']).dt.date < today)
                        )
                        filtered_df = filtered_df[mask]
                    else:
                        filtered_df = filtered_df[filtered_df['status'] == status_map[status_filter]]
            
            # Filtro de mês e ano
            if 'month' in filtered_df.columns and 'year' in filtered_df.columns:
                filtered_df = filtered_df[
                    (filtered_df['month'] == month_filter) &
                    (filtered_df['year'] == year_filter)
                ]
            
            # Filtro de aluno
            if student_filter != "Todos" and 'phone' in filtered_df.columns:
                # Obter telefone do aluno selecionado
                if 'name' in students_df.columns and 'phone' in students_df.columns:
                    student_phone = students_df[students_df['name'] == student_filter]['phone'].iloc[0]
                    filtered_df = filtered_df[filtered_df['phone'] == student_phone]
            
            # Juntar com dados dos alunos para exibir nome
            if not filtered_df.empty and not students_df.empty:
                if 'phone' in filtered_df.columns and 'phone' in students_df.columns and 'name' in students_df.columns:
                    display_df = pd.merge(
                        filtered_df,
                        students_df[['phone', 'name']],
                        on='phone',
                        how='left'
                    )
                else:
                    display_df = filtered_df.copy()
                    if 'phone' in filtered_df.columns and 'phone' not in students_df.columns:
                        st.warning("Não foi possível juntar dados de alunos (coluna 'phone' não encontrada nos dados de alunos).")
                    elif 'phone' not in filtered_df.columns:
                        st.warning("Não foi possível juntar dados de alunos (coluna 'phone' não encontrada nos dados de pagamentos).")
                    elif 'name' not in students_df.columns:
                        st.warning("Não foi possível juntar dados de alunos (coluna 'name' não encontrada nos dados de alunos).")
            else:
                display_df = filtered_df.copy()
            
            # Ordenar por data de vencimento
            if not display_df.empty and 'due_date' in display_df.columns:
                display_df = display_df.sort_values('due_date')
            
            # Mostrar dados
            if not display_df.empty:
                # Colunas a exibir
                if 'name' in display_df.columns:
                    display_cols = ['name', 'due_date', 'amount', 'status', 'payment_date', 'payment_method']
                else:
                    display_cols = ['phone', 'due_date', 'amount', 'status', 'payment_date', 'payment_method']
                
                # Verificar se todas as colunas existem
                display_cols = [col for col in display_cols if col in display_df.columns]
                
                # Preparar dados para exibição
                display_view = display_df[display_cols].copy()
                
                # Formatar valores
                if 'amount' in display_view.columns:
                    display_view['amount'] = display_view['amount'].apply(format_currency)
                if 'status' in display_view.columns:
                    # Verificar pagamentos atrasados
                    today = datetime.now().date()
                    
                    def format_status(row):
                        status = row.get('status', '')
                        due_date = row.get('due_date', None)
                        
                        if status == 'pending' and due_date:
                            due_date = pd.to_datetime(due_date).date()
                            if due_date < today:
                                return "Atrasado"
                        
                        status_map = {
                            'pending': 'Pendente',
                            'paid': 'Pago',
                            'overdue': 'Atrasado'
                        }
                        
                        return status_map.get(status, status)
                    
                    display_view['status'] = display_view.apply(format_status, axis=1)
                
                st.dataframe(display_view, use_container_width=True)
                st.info(f"Total de pagamentos: {len(display_df)}")
                
                # Calcular total
                if 'amount' in filtered_df.columns:
                    total_amount = filtered_df['amount'].sum()
                    st.success(f"Valor total: {format_currency(total_amount)}")
                    
                    # Calcular por status
                    if 'status' in filtered_df.columns:
                        # Total pendente
                        pending_amount = filtered_df[filtered_df['status'] == 'pending']['amount'].sum()
                        st.info(f"Total pendente: {format_currency(pending_amount)}")
                        
                        # Total pago
                        paid_amount = filtered_df[filtered_df['status'] == 'paid']['amount'].sum()
                        st.success(f"Total pago: {format_currency(paid_amount)}")
                        
                        # Total atrasado
                        today = datetime.now().date()
                        overdue_mask = (
                            (filtered_df['status'] == 'pending') &
                            (pd.to_datetime(filtered_df['due_date']).dt.date < today)
                        )
                        overdue_amount = filtered_df[overdue_mask]['amount'].sum()
                        if overdue_amount > 0:
                            st.error(f"Total atrasado: {format_currency(overdue_amount)}")
            else:
                st.info("Nenhum pagamento encontrado com os filtros selecionados.")
        else:
            st.info("Nenhum pagamento registrado.")
    
    # Aba Novo Pagamento
    with tab_new:
        st.subheader("Registrar Novo Pagamento")
        
        with st.form("new_payment_form"):
            # Selecionar aluno
            student_name = st.selectbox(
                "Aluno:",
                students_df['name'].tolist() if 'name' in students_df.columns else [],
                key="new_payment_student"
            )
            
            # Obter telefone do aluno selecionado
            if 'name' in students_df.columns and 'phone' in students_df.columns:
                student_phone = students_df[students_df['name'] == student_name]['phone'].iloc[0]
            else:
                student_phone = ""
                st.warning("Não foi possível obter o telefone do aluno.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Data de vencimento
                due_date = st.date_input(
                    "Data de vencimento",
                    datetime.now().date(),
                    key="new_payment_due_date"
                )
                
                # Valor
                amount = st.number_input(
                    "Valor (R$)",
                    min_value=0.0,
                    format="%.2f",
                    key="new_payment_amount"
                )
                
                # Mês e ano de referência
                payment_month = st.selectbox(
                    "Mês de referência",
                    list(range(1, 13)),
                    index=datetime.now().month - 1,
                    format_func=lambda x: calendar.month_name[x],
                    key="new_payment_month"
                )
                
                payment_year = st.number_input(
                    "Ano de referência",
                    min_value=2020,
                    max_value=2030,
                    value=datetime.now().year,
                    key="new_payment_year"
                )
            
            with col2:
                # Status
                status = st.selectbox(
                    "Status",
                    ["pending", "paid"],
                    format_func=lambda x: "Pendente" if x == "pending" else "Pago",
                    key="new_payment_status"
                )
                
                # Data de pagamento
                payment_date = st.date_input(
                    "Data de pagamento",
                    datetime.now().date() if status == "paid" else None,
                    disabled=status != "paid",
                    key="new_payment_date"
                )
                
                # Método de pagamento
                payment_method = st.selectbox(
                    "Método de pagamento",
                    ["", "Dinheiro", "PIX", "Cartão de Crédito", "Cartão de Débito", "Transferência", "Boleto"],
                    disabled=status != "paid",
                    key="new_payment_method"
                )
                
                # Número da parcela
                installment = st.number_input(
                    "Número da parcela",
                    min_value=1,
                    value=1,
                    key="new_payment_installment"
                )
                
                total_installments = st.number_input(
                    "Total de parcelas",
                    min_value=1,
                    value=12,
                    key="new_payment_total_installments"
                )
            
            # Comentários
            comments = st.text_area("Observações", key="new_payment_comments")
            
            submitted = st.form_submit_button("Registrar")
            
            if submitted:
                # Validação de dados
                if not student_phone:
                    st.error("Selecione um aluno válido.")
                elif amount <= 0:
                    st.error("O valor deve ser maior que zero.")
                elif status == "paid" and not payment_method:
                    st.error("Informe o método de pagamento.")
                else:
                    # Preparar dados
                    new_payment = {
                        "phone": student_phone,
                        "amount": amount,
                        "due_date": due_date.strftime("%Y-%m-%d"),
                        "status": status,
                        "payment_date": payment_date.strftime("%Y-%m-%d") if status == "paid" and payment_date else None,
                        "payment_method": payment_method if status == "paid" else "",
                        "month": payment_month,
                        "year": payment_year,
                        "comments": comments,
                        "installment": installment,
                        "total_installments": total_installments
                    }
                    
                    # Adicionar ao DataFrame
                    new_row = pd.DataFrame([new_payment])
                    
                    # Se o DataFrame estiver vazio, criar um novo
                    if payments_df.empty:
                        payments_df = new_row
                    else:
                        payments_df = pd.concat([payments_df, new_row], ignore_index=True)
                    
                    # Salvar dados
                    try:
                        save_payments_data(payments_df)
                        st.success(f"Pagamento registrado com sucesso para o aluno {student_name}!")
                    except Exception as e:
                        st.error(f"Erro ao salvar dados: {e}")
    
    # Aba Gerenciar Pagamento
    with tab_manage:
        st.subheader("Gerenciar Pagamento")
        
        if not payments_df.empty:
            # Selecionar aluno primeiro
            student_filter = st.selectbox(
                "Selecione o aluno:",
                students_df['name'].tolist() if 'name' in students_df.columns else [],
                key="manage_payment_student"
            )
            
            # Obter telefone do aluno selecionado
            if 'name' in students_df.columns and 'phone' in students_df.columns:
                student_phone = students_df[students_df['name'] == student_filter]['phone'].iloc[0]
            else:
                student_phone = ""
                st.warning("Não foi possível obter o telefone do aluno.")
            
            # Filtrar pagamentos do aluno
            student_payments = payments_df[payments_df['phone'] == student_phone].copy() if student_phone else pd.DataFrame()
            
            if not student_payments.empty:
                # Ordenar por data de vencimento
                if 'due_date' in student_payments.columns:
                    student_payments = student_payments.sort_values('due_date')
                
                # Preparar lista de pagamentos para seleção
                payment_list = []
                for _, row in student_payments.iterrows():
                    payment_id = row.get('id', None)
                    due_date = row.get('due_date', '')
                    amount = row.get('amount', 0)
                    status = row.get('status', '')
                    
                    # Formatar o status
                    status_format = {
                        'pending': '🔸 Pendente',
                        'paid': '✅ Pago'
                    }
                    status_text = status_format.get(status, status)
                    
                    # Verificar se está atrasado
                    if status == 'pending' and due_date:
                        due_date_obj = pd.to_datetime(due_date).date()
                        if due_date_obj < datetime.now().date():
                            status_text = '❌ Atrasado'
                    
                    # Formatar texto para seleção
                    payment_text = f"{due_date} - {format_currency(amount)} - {status_text}"
                    
                    payment_list.append((payment_text, payment_id or _))
                
                # Selecionar pagamento
                selected_payment = st.selectbox(
                    "Selecione o pagamento:",
                    [text for text, _ in payment_list],
                    key="manage_payment_select"
                )
                
                # Obter ID do pagamento selecionado
                selected_idx = [text for text, _ in payment_list].index(selected_payment)
                payment_id = payment_list[selected_idx][1]
                
                # Obter dados do pagamento selecionado
                if isinstance(payment_id, int):
                    payment_data = student_payments.iloc[payment_id]
                else:
                    payment_data = student_payments[student_payments['id'] == payment_id].iloc[0]
                
                # Exibir formulário de edição
                with st.form("edit_payment_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Data de vencimento
                        due_date = st.date_input(
                            "Data de vencimento",
                            datetime.strptime(payment_data.get('due_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date(),
                            key="edit_payment_due_date"
                        )
                        
                        # Valor
                        amount = st.number_input(
                            "Valor (R$)",
                            min_value=0.0,
                            value=float(payment_data.get('amount', 0)),
                            format="%.2f",
                            key="edit_payment_amount"
                        )
                        
                        # Mês e ano de referência
                        payment_month = st.selectbox(
                            "Mês de referência",
                            list(range(1, 13)),
                            index=int(payment_data.get('month', datetime.now().month)) - 1,
                            format_func=lambda x: calendar.month_name[x],
                            key="edit_payment_month"
                        )
                        
                        payment_year = st.number_input(
                            "Ano de referência",
                            min_value=2020,
                            max_value=2030,
                            value=int(payment_data.get('year', datetime.now().year)),
                            key="edit_payment_year"
                        )
                    
                    with col2:
                        # Status
                        status = st.selectbox(
                            "Status",
                            ["pending", "paid"],
                            index=0 if payment_data.get('status', '') == "pending" else 1,
                            format_func=lambda x: "Pendente" if x == "pending" else "Pago",
                            key="edit_payment_status"
                        )
                        
                        # Data de pagamento
                        payment_date_value = None
                        if payment_data.get('payment_date'):
                            try:
                                payment_date_value = datetime.strptime(payment_data.get('payment_date'), '%Y-%m-%d').date()
                            except:
                                payment_date_value = datetime.now().date()
                        else:
                            payment_date_value = datetime.now().date()
                        
                        payment_date = st.date_input(
                            "Data de pagamento",
                            payment_date_value,
                            disabled=status != "paid",
                            key="edit_payment_date"
                        )
                        
                        # Método de pagamento
                        payment_method = st.selectbox(
                            "Método de pagamento",
                            ["", "Dinheiro", "PIX", "Cartão de Crédito", "Cartão de Débito", "Transferência", "Boleto"],
                            index=["", "Dinheiro", "PIX", "Cartão de Crédito", "Cartão de Débito", "Transferência", "Boleto"].index(payment_data.get('payment_method', '')) if payment_data.get('payment_method', '') in ["", "Dinheiro", "PIX", "Cartão de Crédito", "Cartão de Débito", "Transferência", "Boleto"] else 0,
                            disabled=status != "paid",
                            key="edit_payment_method"
                        )
                        
                        # Número da parcela
                        installment = st.number_input(
                            "Número da parcela",
                            min_value=1,
                            value=int(payment_data.get('installment', 1)),
                            key="edit_payment_installment"
                        )
                        
                        total_installments = st.number_input(
                            "Total de parcelas",
                            min_value=1,
                            value=int(payment_data.get('total_installments', 12)),
                            key="edit_payment_total_installments"
                        )
                    
                    # Comentários
                    comments = st.text_area("Observações", value=payment_data.get('comments', ''), key="edit_payment_comments")
                    
                    submitted = st.form_submit_button("Atualizar")
                    
                    if submitted:
                        # Validação de dados
                        if amount <= 0:
                            st.error("O valor deve ser maior que zero.")
                        elif status == "paid" and not payment_method:
                            st.error("Informe o método de pagamento.")
                        else:
                            # Preparar dados
                            updated_payment = payment_data.copy()
                            updated_payment.update({
                                "amount": amount,
                                "due_date": due_date.strftime("%Y-%m-%d"),
                                "status": status,
                                "payment_date": payment_date.strftime("%Y-%m-%d") if status == "paid" else None,
                                "payment_method": payment_method if status == "paid" else "",
                                "month": payment_month,
                                "year": payment_year,
                                "comments": comments,
                                "installment": installment,
                                "total_installments": total_installments
                            })
                            
                            # Atualizar no DataFrame
                            if 'id' in payment_data and payment_data['id']:
                                payments_df.loc[payments_df['id'] == payment_data['id']] = updated_payment
                            else:
                                payments_df.iloc[payment_id] = updated_payment
                            
                            # Salvar dados
                            try:
                                save_payments_data(payments_df)
                                st.success(f"Pagamento atualizado com sucesso!")
                            except Exception as e:
                                st.error(f"Erro ao salvar dados: {e}")
                
                # Marcar como pago (shortcut)
                if payment_data.get('status') == "pending":
                    if st.button("Marcar como Pago", key="mark_as_paid"):
                        # Preparar dados
                        updated_payment = payment_data.copy()
                        updated_payment.update({
                            "status": "paid",
                            "payment_date": datetime.now().strftime("%Y-%m-%d"),
                            "payment_method": "PIX"  # Método padrão
                        })
                        
                        # Atualizar no DataFrame
                        if 'id' in payment_data and payment_data['id']:
                            payments_df.loc[payments_df['id'] == payment_data['id']] = updated_payment
                        else:
                            payments_df.iloc[payment_id] = updated_payment
                        
                        # Salvar dados
                        try:
                            save_payments_data(payments_df)
                            st.success(f"Pagamento marcado como pago com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar dados: {e}")
                
                # Excluir pagamento
                if st.button("Excluir Pagamento", type="primary", help="Cuidado! Esta ação não pode ser desfeita.", key="delete_payment"):
                    # Excluir do DataFrame
                    if 'id' in payment_data and payment_data['id']:
                        payments_df = payments_df[payments_df['id'] != payment_data['id']]
                    else:
                        payments_df = payments_df.drop(payment_id)
                    
                    # Salvar dados
                    try:
                        save_payments_data(payments_df)
                        st.success(f"Pagamento excluído com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar dados: {e}")
            else:
                st.info(f"Não há pagamentos registrados para este aluno.")
        else:
            st.info("Nenhum pagamento registrado.")
