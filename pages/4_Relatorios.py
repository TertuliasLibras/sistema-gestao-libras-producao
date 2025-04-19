import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import calendar
from utils import (
    load_students_data, 
    load_payments_data,
    load_internships_data,
    format_phone,
    format_currency,
    get_active_students,
    get_canceled_students,
    get_student_internship_hours,
    get_student_internship_topics
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
    st.title("Relatórios")

# Load data
students_df = load_students_data()
payments_df = load_payments_data()
internships_df = load_internships_data()

# Create tabs for different reports
tab1, tab2, tab3, tab4 = st.tabs(["Financeiro", "Alunos", "Estágios", "Exportar Dados"])

with tab1:
    st.subheader("Relatório Financeiro")
    
    if payments_df is not None and not payments_df.empty:
        # Date range filter
        col1, col2 = st.columns(2)
        
        with col1:
            period = st.radio(
                "Período",
                options=["Mensal", "Trimestral", "Anual", "Personalizado"],
                horizontal=True
            )
        
        with col2:
            current_date = datetime.now()
            
            if period == "Mensal":
                start_date = datetime(current_date.year, current_date.month, 1)
                end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            elif period == "Trimestral":
                current_quarter = (current_date.month - 1) // 3 + 1
                start_date = datetime(current_date.year, 3 * current_quarter - 2, 1)
                end_date = datetime(current_date.year if current_quarter < 4 else current_date.year + 1, 
                                   1 if current_quarter == 4 else 3 * current_quarter + 1, 1) - timedelta(days=1)
            elif period == "Anual":
                start_date = datetime(current_date.year, 1, 1)
                end_date = datetime(current_date.year, 12, 31)
            else:  # Personalizado
                date_range = st.date_input(
                    "Selecione o período",
                    value=(
                        datetime(current_date.year, current_date.month, 1),
                        current_date
                    )
                )
                
                if len(date_range) == 2:
                    start_date, end_date = date_range
                else:
                    start_date = datetime(current_date.year, current_date.month, 1)
                    end_date = current_date
        
        # Convert dates to string for comparison
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Filter payments by date
        payments_df['payment_date'] = pd.to_datetime(payments_df['payment_date'])
        filtered_payments = payments_df.dropna(subset=['payment_date'])  # Only include payments with dates
        
        filtered_payments = filtered_payments[
            (filtered_payments['payment_date'] >= start_date_str) &
            (filtered_payments['payment_date'] <= end_date_str)
        ]
        
        if not filtered_payments.empty:
            # Usar a função get_payment_status_column para obter o nome correto da coluna
            from utils import get_payment_status_column
            status_column = get_payment_status_column(filtered_payments)
            
            # Calculate metrics
            total_received = filtered_payments[filtered_payments[status_column] == 'paid']['amount'].sum()
            count_payments = len(filtered_payments[filtered_payments[status_column] == 'paid'])
            
            # Daily payments
            payments_by_day = filtered_payments.groupby(filtered_payments['payment_date'].dt.strftime('%Y-%m-%d')).agg({
                'amount': 'sum',
                'phone': 'count'
            }).reset_index()
            payments_by_day.columns = ['data', 'valor', 'quantidade']
            
            # Payment totals by month
            payments_by_month = filtered_payments.groupby([
                filtered_payments['payment_date'].dt.year,
                filtered_payments['payment_date'].dt.month
            ]).agg({
                'amount': 'sum',
                'phone': 'count'
            }).reset_index()
            payments_by_month.columns = ['ano', 'mes', 'valor', 'quantidade']
            payments_by_month['mes_nome'] = payments_by_month['mes'].apply(lambda x: calendar.month_abbr[x])
            payments_by_month['periodo'] = payments_by_month.apply(lambda x: f"{x['mes_nome']}/{x['ano']}", axis=1)
            
            # Display metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Recebido", format_currency(total_received))
            
            with col2:
                st.metric("Quantidade de Pagamentos", count_payments)
            
            # Show charts
            if len(payments_by_day) > 1:
                fig = px.line(
                    payments_by_day, 
                    x='data', 
                    y='valor',
                    markers=True,
                    title='Pagamentos por Dia'
                )
                fig.update_layout(xaxis_title='Data', yaxis_title='Valor (R$)')
                st.plotly_chart(fig, use_container_width=True)
            
            if len(payments_by_month) > 1:
                fig = px.bar(
                    payments_by_month, 
                    x='periodo', 
                    y='valor',
                    title='Pagamentos por Mês'
                )
                fig.update_layout(xaxis_title='Mês', yaxis_title='Valor (R$)')
                st.plotly_chart(fig, use_container_width=True)
            
            # Payment status distribution
            st.subheader("Distribuição de Status de Pagamento")
            
            # Filter by due date in the period
            payments_df['due_date'] = pd.to_datetime(payments_df['due_date'])
            status_payments = payments_df[
                (payments_df['due_date'] >= start_date_str) &
                (payments_df['due_date'] <= end_date_str)
            ]
            
            if not status_payments.empty:
                # Usar a função get_payment_status_column para obter o nome correto da coluna
                from utils import get_payment_status_column
                status_column = get_payment_status_column(status_payments)
                
                status_counts = status_payments[status_column].value_counts().reset_index()
                status_counts.columns = ['status', 'quantidade']
                
                # Map status names
                status_map = {
                    'paid': 'Pago',
                    'pending': 'Pendente',
                    'overdue': 'Atrasado',
                    'canceled': 'Cancelado'
                }
                status_counts['status'] = status_counts['status'].map(status_map)
                
                # Create pie chart
                fig = px.pie(
                    status_counts, 
                    names='status', 
                    values='quantidade',
                    color='status',
                    color_discrete_map={
                        'Pago': 'green',
                        'Pendente': 'orange',
                        'Atrasado': 'red',
                        'Cancelado': 'gray'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Não há pagamentos com vencimento no período selecionado.")
        else:
            st.info(f"Não há pagamentos registrados entre {start_date.strftime('%d/%m/%Y')} e {end_date.strftime('%d/%m/%Y')}.")
    else:
        st.info("Não há dados de pagamento para gerar o relatório financeiro.")

with tab2:
    st.subheader("Relatório de Alunos")
    
    if students_df is not None and not students_df.empty:
        active_students = get_active_students(students_df)
        canceled_students = get_canceled_students(students_df)
        
        # Metrics
        active_count = len(active_students)
        canceled_count = len(canceled_students)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Alunos Ativos", active_count)
        
        with col2:
            st.metric("Alunos Cancelados", canceled_count)
        
        with col3:
            cancellation_rate = (canceled_count / (active_count + canceled_count)) * 100 if (active_count + canceled_count) > 0 else 0
            st.metric("Taxa de Cancelamento", f"{cancellation_rate:.1f}%")
        
        # Enrollment trend
        if not students_df.empty:
            # Convert enrollment dates to datetime
            students_df['enrollment_date'] = pd.to_datetime(students_df['enrollment_date'])
            
            # Group by month and count enrollments
            enrollments_by_month = students_df.groupby(
                students_df['enrollment_date'].dt.strftime('%Y-%m')
            ).size().reset_index(name='count')
            enrollments_by_month.columns = ['Mês', 'Matrículas']
            
            # Create bar chart for enrollments
            if not enrollments_by_month.empty:
                fig = px.bar(
                    enrollments_by_month, 
                    x='Mês', 
                    y='Matrículas',
                    title='Matrículas por Mês'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Cancellation trend
        if not canceled_students.empty:
            # Convert cancellation dates to datetime
            canceled_students['cancellation_date'] = pd.to_datetime(canceled_students['cancellation_date'])
            
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
        
        # Average monthly fee
        if not active_students.empty:
            avg_fee = active_students['monthly_fee'].mean()
            st.metric("Mensalidade Média (Alunos Ativos)", format_currency(avg_fee))
    else:
        st.info("Não há dados de alunos para gerar o relatório.")

with tab3:
    st.subheader("Relatório de Estágios")
    
    if internships_df is not None and not internships_df.empty:
        # Convert dates to datetime
        internships_df['date'] = pd.to_datetime(internships_df['date'])
        
        # Filter by date range
        date_range = st.date_input(
            "Período",
            value=(
                datetime.now() - timedelta(days=180),
                datetime.now()
            )
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            
            filtered_internships = internships_df[
                (internships_df['date'].dt.date >= start_date) &
                (internships_df['date'].dt.date <= end_date)
            ]
            
            if not filtered_internships.empty:
                # Calculate metrics
                total_internships = len(filtered_internships)
                total_hours = filtered_internships['duration_hours'].sum()
                
                # Count unique students
                all_student_phones = []
                for students_str in filtered_internships['students'].dropna():
                    student_phones = students_str.split(',')
                    all_student_phones.extend([phone.strip() for phone in student_phones if phone.strip()])
                
                unique_students = len(set(all_student_phones))
                
                # Display metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total de Estágios", total_internships)
                
                with col2:
                    st.metric("Total de Horas", f"{total_hours:.1f}h")
                
                with col3:
                    st.metric("Alunos Participantes", unique_students)
                
                # Internships by month
                internships_by_month = filtered_internships.groupby(
                    filtered_internships['date'].dt.strftime('%Y-%m')
                ).agg({
                    'duration_hours': 'sum',
                    'topic': 'count'
                }).reset_index()
                internships_by_month.columns = ['Mês', 'Horas', 'Quantidade']
                
                # Create line chart for internship hours
                if not internships_by_month.empty:
                    fig = px.line(
                        internships_by_month, 
                        x='Mês', 
                        y='Horas',
                        markers=True,
                        title='Horas de Estágio por Mês'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Popular topics
                topic_counts = filtered_internships['topic'].value_counts().reset_index()
                topic_counts.columns = ['Tema', 'Quantidade']
                
                # Display top 10 topics
                st.subheader("Temas Mais Frequentes")
                
                if len(topic_counts) > 0:
                    fig = px.bar(
                        topic_counts.head(10), 
                        x='Tema', 
                        y='Quantidade',
                        title='Top 10 Temas de Estágio'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Student participation
                if students_df is not None and not students_df.empty:
                    st.subheader("Participação dos Alunos")
                    
                    student_participation = []
                    
                    for _, student in students_df.iterrows():
                        hours = get_student_internship_hours(filtered_internships, student['phone'])
                        
                        if hours > 0:
                            student_participation.append({
                                'name': student['name'],
                                'phone': student['phone'],
                                'hours': hours
                            })
                    
                    if student_participation:
                        participation_df = pd.DataFrame(student_participation)
                        participation_df = participation_df.sort_values('hours', ascending=False)
                        
                        # Display top 10 students
                        top_students = participation_df.head(10)
                        
                        fig = px.bar(
                            top_students, 
                            x='name', 
                            y='hours',
                            title='Top 10 Alunos com Mais Horas de Estágio'
                        )
                        fig.update_layout(xaxis_title='Aluno', yaxis_title='Horas')
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"Não há estágios registrados entre {start_date.strftime('%d/%m/%Y')} e {end_date.strftime('%d/%m/%Y')}.")
    else:
        st.info("Não há dados de estágio para gerar o relatório.")

with tab4:
    st.subheader("Exportar Dados")
    
    st.write("""
    Aqui você pode exportar todos os dados do sistema em formato CSV para backup ou análise externa.
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if students_df is not None and not students_df.empty:
            # Convert to CSV
            csv = students_df.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                "Exportar Alunos (CSV)",
                csv,
                "alunos_completo.csv",
                "text/csv",
                key='download-students-csv'
            )
        else:
            st.info("Não há dados de alunos para exportar.")
    
    with col2:
        if payments_df is not None and not payments_df.empty:
            # Convert to CSV
            csv = payments_df.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                "Exportar Pagamentos (CSV)",
                csv,
                "pagamentos_completo.csv",
                "text/csv",
                key='download-payments-csv'
            )
        else:
            st.info("Não há dados de pagamentos para exportar.")
    
    with col3:
        if internships_df is not None and not internships_df.empty:
            # Convert to CSV
            csv = internships_df.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                "Exportar Estágios (CSV)",
                csv,
                "estagios_completo.csv",
                "text/csv",
                key='download-internships-csv'
            )
        else:
            st.info("Não há dados de estágios para exportar.")
    
    st.subheader("Relatório Completo de Alunos")
    
    if students_df is not None and not students_df.empty and payments_df is not None and internships_df is not None:
        if st.button("Gerar Relatório Completo de Alunos"):
            # Create a comprehensive report
            complete_report = []
            
            for _, student in students_df.iterrows():
                phone = student['phone']
                
                # Get payment info
                total_paid = 0
                payments_pending = 0
                last_payment_date = None
                
                if not payments_df.empty:
                    student_payments = payments_df[payments_df['phone'] == phone]
                    
                    if not student_payments.empty:
                        # Usar a função get_payment_status_column para obter o nome correto da coluna
                        from utils import get_payment_status_column
                        status_column = get_payment_status_column(student_payments)
                        
                        # Calculate total paid
                        paid_payments = student_payments[student_payments[status_column] == 'paid']
                        total_paid = paid_payments['amount'].sum() if not paid_payments.empty else 0
                        
                        # Count pending payments
                        payments_pending = len(student_payments[student_payments[status_column] == 'pending'])
                        
                        # Get last payment date
                        if not paid_payments.empty:
                            paid_payments['payment_date'] = pd.to_datetime(paid_payments['payment_date'])
                            last_payment = paid_payments.sort_values('payment_date', ascending=False).iloc[0]
                            last_payment_date = last_payment['payment_date'].strftime('%d/%m/%Y') if pd.notna(last_payment['payment_date']) else None
                
                # Get internship info
                internship_hours = get_student_internship_hours(internships_df, phone)
                internship_topics = get_student_internship_topics(internships_df, phone)
                
                # Create report entry
                report_entry = {
                    'name': student['name'],
                    'phone': format_phone(phone),
                    'email': student['email'],
                    'status': 'Ativo' if student['status'] == 'active' else 'Cancelado',
                    'enrollment_date': pd.to_datetime(student['enrollment_date']).strftime('%d/%m/%Y') if pd.notna(student['enrollment_date']) else None,
                    'monthly_fee': format_currency(student['monthly_fee']),
                    'total_paid': format_currency(total_paid),
                    'payments_pending': payments_pending,
                    'last_payment_date': last_payment_date,
                    'internship_hours': f"{internship_hours:.1f}h",
                    'internship_topics_count': len(internship_topics),
                    'notes': student['notes']
                }
                
                complete_report.append(report_entry)
            
            # Create dataframe
            report_df = pd.DataFrame(complete_report)
            
            # Display report
            st.dataframe(report_df, use_container_width=True)
            
            # Export option
            csv = report_df.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                "Exportar Relatório Completo (CSV)",
                csv,
                "relatorio_completo_alunos.csv",
                "text/csv",
                key='download-report-csv'
            )
    else:
        st.info("Não há dados suficientes para gerar o relatório completo.")
