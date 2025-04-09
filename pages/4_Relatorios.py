import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
import os
from utils import (
    load_students_data, 
    load_payments_data,
    load_internships_data,
    format_currency,
    format_phone,
    get_months_between_dates,
    get_overdue_payments,
    calculate_monthly_revenue
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
    .metric-card {
        border-radius: 5px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 1rem;
        color: #555;
    }
    .metric-green {
        background-color: #d4edda;
        color: #155724;
    }
    .metric-blue {
        background-color: #d1ecf1;
        color: #0c5460;
    }
    .metric-yellow {
        background-color: #fff3cd;
        color: #856404;
    }
    .metric-red {
        background-color: #f8d7da;
        color: #721c24;
    }
    .report-section {
        margin-top: 1.5rem;
        margin-bottom: 2.5rem;
    }
    .chart-container {
        margin-top: 1rem;
        margin-bottom: 2rem;
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
        # Tentar diretamente o caminho relativo
        try:
            st.image('./assets/images/logo.svg', width=120)
        except:
            # Se falhar, não mostrar logo
            st.warning(f"Logo não pôde ser carregada. App continuará funcionando normalmente.")
with col2:
    st.title("Relatórios e Análises")

# Load data
students_df = load_students_data()
payments_df = load_payments_data()
internships_df = load_internships_data()

# Create tabs for different reports
tab1, tab2, tab3, tab4 = st.tabs(["Visão Geral", "Financeiro", "Alunos", "Estágios"])

with tab1:
    st.subheader("Visão Geral do Sistema")
    
    # Calculate key metrics
    if students_df is not None and not students_df.empty:
        total_students = len(students_df)
        active_students = len(students_df[students_df['status'] == 'active'])
        cancelled_students = len(students_df[students_df['status'] == 'canceled'])
    else:
        total_students = 0
        active_students = 0
        cancelled_students = 0
    
    if payments_df is not None and not payments_df.empty:
        today = datetime.now().date()
        
        # Paid payments
        paid_payments = payments_df[payments_df['payment_status'] == 'paid']
        total_paid = paid_payments['amount'].sum() if not paid_payments.empty else 0
        
        # Pending payments
        pending_payments = payments_df[payments_df['payment_status'] == 'pending']
        total_pending = pending_payments['amount'].sum() if not pending_payments.empty else 0
        
        # Overdue payments
        overdue_payments = pending_payments[pd.to_datetime(pending_payments['due_date']).dt.date < today]
        total_overdue = overdue_payments['amount'].sum() if not overdue_payments.empty else 0
    else:
        total_paid = 0
        total_pending = 0
        total_overdue = 0
    
    if internships_df is not None and not internships_df.empty:
        total_internships = len(internships_df)
        total_internship_hours = internships_df['hours'].sum()
    else:
        total_internships = 0
        total_internship_hours = 0
    
    # Display key metrics
    st.markdown("### Métricas Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card metric-blue">
            <div class="metric-label">Alunos Ativos</div>
            <div class="metric-value">{active_students}</div>
            <div class="metric-label">de {total_students} total</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card metric-green">
            <div class="metric-label">Recebido</div>
            <div class="metric-value">{format_currency(total_paid)}</div>
            <div class="metric-label">em pagamentos</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card metric-yellow">
            <div class="metric-label">A Receber</div>
            <div class="metric-value">{format_currency(total_pending)}</div>
            <div class="metric-label">pendente</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card metric-red">
            <div class="metric-label">Vencido</div>
            <div class="metric-value">{format_currency(total_overdue)}</div>
            <div class="metric-label">em atraso</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent activity / Timeline
    st.markdown("### Atividade Recente")
    
    # Combine recent payments and internships
    recent_activities = []
    
    if payments_df is not None and not payments_df.empty:
        recent_payments = payments_df[payments_df['payment_status'] == 'paid'].copy()
        if not recent_payments.empty:
            recent_payments['date'] = pd.to_datetime(recent_payments['payment_date'])
            recent_payments['type'] = 'payment'
            recent_payments['description'] = recent_payments.apply(
                lambda row: f"Pagamento de {format_currency(row['amount'])} recebido", 
                axis=1
            )
            
            recent_activities.append(
                recent_payments[['date', 'type', 'description', 'student_phone']]
            )
    
    if internships_df is not None and not internships_df.empty:
        recent_internships = internships_df.copy()
        recent_internships['date'] = pd.to_datetime(recent_internships['date'])
        recent_internships['type'] = 'internship'
        recent_internships['description'] = recent_internships.apply(
            lambda row: f"Estágio de {row['hours']} horas - {row['topic']}", 
            axis=1
        )
        
        # Need to handle multiple students per internship
        expanded_internships = []
        for _, row in recent_internships.iterrows():
            if pd.notna(row['students']):
                students = row['students'].split(',')
                for student in students:
                    new_row = row.copy()
                    new_row['student_phone'] = student
                    expanded_internships.append(new_row)
        
        if expanded_internships:
            expanded_df = pd.DataFrame(expanded_internships)
            recent_activities.append(
                expanded_df[['date', 'type', 'description', 'student_phone']]
            )
    
    if recent_activities:
        # Combine all activities
        all_activities = pd.concat(recent_activities, ignore_index=True)
        
        # Sort by date (most recent first)
        all_activities = all_activities.sort_values('date', ascending=False)
        
        # Take only the most recent 10 activities
        recent = all_activities.head(10)
        
        # Add student names
        if students_df is not None and not students_df.empty:
            # Create a map of phone to name
            phone_to_name = dict(zip(students_df['phone'], students_df['name']))
            
            # Add a column with student name
            recent['student_name'] = recent['student_phone'].map(phone_to_name)
        
        # Format for display
        recent['date_formatted'] = recent['date'].dt.strftime('%d/%m/%Y')
        
        # Display in a clean format
        for _, row in recent.iterrows():
            activity_type = "🟢 Pagamento" if row['type'] == 'payment' else "🔵 Estágio"
            student_name = row['student_name'] if 'student_name' in row and pd.notna(row['student_name']) else format_phone(row['student_phone'])
            
            st.markdown(f"""
            <div style="margin-bottom: 10px; padding: 10px; border-radius: 5px; background-color: #f9f9f9;">
                <div style="display: flex; justify-content: space-between;">
                    <div><strong>{activity_type}</strong> - {row['date_formatted']}</div>
                    <div>{student_name}</div>
                </div>
                <div>{row['description']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Não há atividades recentes para exibir.")

with tab2:
    st.subheader("Relatórios Financeiros")
    
    # Financial metrics
    if payments_df is not None and not payments_df.empty and students_df is not None and not students_df.empty:
        # Date range for analysis
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Data Inicial",
                value=datetime.now().replace(day=1, month=1),  # January 1st of current year
                key="financial_start_date"
            )
        
        with col2:
            end_date = st.date_input(
                "Data Final",
                value=datetime.now(),
                key="financial_end_date"
            )
        
        if start_date and end_date:
            # Create a list of months in the date range
            months_between = get_months_between_dates(start_date, end_date)
            
            # Calculate projected and actual revenue for each month
            monthly_data = []
            
            for year, month in months_between:
                month_str = f"{year}-{month:02d}"
                month_name = f"{calendar.month_name[month]}/{year}"
                
                # Calculate projected revenue for this month
                projected = calculate_monthly_revenue(students_df, payments_df, month, year)
                
                # Calculate actual revenue for this month
                actual_payments = payments_df[
                    (payments_df['payment_status'] == 'paid') &
                    (pd.to_datetime(payments_df['payment_date']).dt.year == year) &
                    (pd.to_datetime(payments_df['payment_date']).dt.month == month)
                ]
                
                actual = actual_payments['amount'].sum() if not actual_payments.empty else 0
                
                monthly_data.append({
                    'month': month_str,
                    'month_name': month_name,
                    'projected': projected,
                    'actual': actual,
                    'diff': actual - projected
                })
            
            monthly_df = pd.DataFrame(monthly_data)
            
            # 1. Create a bar chart for projected vs actual revenue
            st.markdown("### Receita Projetada vs. Realizada")
            
            fig_revenue = go.Figure()
            
            # Projected revenue
            fig_revenue.add_trace(go.Bar(
                x=monthly_df['month_name'],
                y=monthly_df['projected'],
                name='Projetado',
                marker_color='lightskyblue'
            ))
            
            # Actual revenue
            fig_revenue.add_trace(go.Bar(
                x=monthly_df['month_name'],
                y=monthly_df['actual'],
                name='Realizado',
                marker_color='lightgreen'
            ))
            
            # Format layout
            fig_revenue.update_layout(
                title='Receita Mensal',
                xaxis_title='Mês',
                yaxis_title='Valor (R$)',
                legend_title='Tipo',
                barmode='group',
                height=400,
                xaxis={'categoryorder':'total descending'}
            )
            
            # Display chart
            st.plotly_chart(fig_revenue, use_container_width=True)
            
            # Calculate total expected revenue
            total_projected = monthly_df['projected'].sum()
            total_actual = monthly_df['actual'].sum()
            total_diff = total_actual - total_projected
            
            # Display totals
            st.markdown("### Receita no Período")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="Receita Projetada", 
                    value=format_currency(total_projected)
                )
            
            with col2:
                st.metric(
                    label="Receita Realizada", 
                    value=format_currency(total_actual)
                )
            
            with col3:
                st.metric(
                    label="Diferença", 
                    value=format_currency(total_diff),
                    delta=f"{(total_diff/total_projected*100):.1f}%" if total_projected > 0 else "0%"
                )
            
            # 2. Overdue payments analysis
            st.markdown("### Análise de Pagamentos em Atraso")
            
            # Get overdue payments
            overdue_df = get_overdue_payments(students_df, payments_df)
            
            if not overdue_df.empty:
                # Add student name and format phone
                if students_df is not None and not students_df.empty:
                    # Create a map of phone to name
                    phone_to_name = dict(zip(students_df['phone'], students_df['name']))
                    
                    # Add student name
                    overdue_df['student_name'] = overdue_df['student_phone'].map(phone_to_name)
                
                # Format for display
                display_overdue = overdue_df.copy()
                display_overdue['due_date'] = pd.to_datetime(display_overdue['due_date']).dt.strftime('%d/%m/%Y')
                display_overdue['days_overdue'] = (datetime.now().date() - pd.to_datetime(display_overdue['due_date']).dt.date).dt.days
                display_overdue['amount'] = display_overdue['amount'].apply(format_currency)
                
                # Select columns for display
                columns_to_display = [
                    'student_name', 'student_phone', 'due_date', 'amount', 'days_overdue', 'installment_number'
                ]
                
                # Ensure all columns exist
                for col in columns_to_display:
                    if col not in display_overdue.columns:
                        display_overdue[col] = ""
                
                # Custom column labels
                column_labels = {
                    'student_name': 'Nome do Aluno',
                    'student_phone': 'Telefone',
                    'due_date': 'Vencimento',
                    'amount': 'Valor',
                    'days_overdue': 'Dias em Atraso',
                    'installment_number': 'Parcela'
                }
                
                # Display the dataframe
                st.dataframe(
                    display_overdue[columns_to_display], 
                    use_container_width=True,
                    column_config={col: column_labels.get(col, col) for col in columns_to_display}
                )
                
                # Summary of overdue payments
                total_overdue = overdue_df['amount'].sum()
                avg_days_overdue = display_overdue['days_overdue'].mean()
                
                st.warning(f"""
                **Resumo de Atrasos:**
                * Total em atraso: {format_currency(total_overdue)}
                * Média de dias em atraso: {avg_days_overdue:.1f} dias
                * Número de parcelas em atraso: {len(overdue_df)}
                """)
            else:
                st.success("Não há pagamentos em atraso! 🎉")
            
            # 3. Payment status breakdown
            st.markdown("### Distribuição de Status de Pagamentos")
            
            # Get counts by status
            if payments_df is not None and not payments_df.empty:
                # Filter by date range
                filtered_payments = payments_df[
                    (pd.to_datetime(payments_df['due_date']) >= pd.to_datetime(start_date)) &
                    (pd.to_datetime(payments_df['due_date']) <= pd.to_datetime(end_date))
                ]
                
                if not filtered_payments.empty:
                    # Count by status
                    status_counts = []
                    
                    # Paid
                    paid_count = len(filtered_payments[filtered_payments['payment_status'] == 'paid'])
                    paid_amount = filtered_payments[filtered_payments['payment_status'] == 'paid']['amount'].sum()
                    
                    # Pending (not overdue)
                    pending_df = filtered_payments[
                        (filtered_payments['payment_status'] == 'pending') &
                        (pd.to_datetime(filtered_payments['due_date']) >= datetime.now())
                    ]
                    pending_count = len(pending_df)
                    pending_amount = pending_df['amount'].sum() if not pending_df.empty else 0
                    
                    # Overdue
                    overdue_df = filtered_payments[
                        (filtered_payments['payment_status'] == 'pending') &
                        (pd.to_datetime(filtered_payments['due_date']) < datetime.now())
                    ]
                    overdue_count = len(overdue_df)
                    overdue_amount = overdue_df['amount'].sum() if not overdue_df.empty else 0
                    
                    # Create data for pie chart
                    labels = ['Pagos', 'Pendentes', 'Atrasados']
                    counts = [paid_count, pending_count, overdue_count]
                    amounts = [paid_amount, pending_amount, overdue_amount]
                    colors = ['lightgreen', 'lightskyblue', 'salmon']
                    
                    # Create a column structure for the pie charts
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Pie chart by count
                        fig_count = px.pie(
                            values=counts,
                            names=labels,
                            title="Por Quantidade de Parcelas",
                            color_discrete_sequence=colors
                        )
                        fig_count.update_traces(textinfo='percent+value')
                        st.plotly_chart(fig_count, use_container_width=True)
                    
                    with col2:
                        # Pie chart by amount
                        fig_amount = px.pie(
                            values=amounts,
                            names=labels,
                            title="Por Valor (R$)",
                            color_discrete_sequence=colors
                        )
                        fig_amount.update_traces(textinfo='percent+value')
                        st.plotly_chart(fig_amount, use_container_width=True)
                    
                    # Summary statistics
                    total_parcels = sum(counts)
                    total_value = sum(amounts)
                    
                    st.markdown(f"""
                    **Resumo do Período:**
                    * Total de parcelas: {total_parcels}
                    * Valor total: {format_currency(total_value)}
                    * Taxa de recebimento: {(paid_count/total_parcels*100):.1f}% das parcelas ({format_currency(paid_amount)} de {format_currency(total_value)})
                    """)
                else:
                    st.info("Não há pagamentos no período selecionado.")
    else:
        st.info("Dados insuficientes para gerar relatórios financeiros.")

with tab3:
    st.subheader("Relatórios de Alunos")
    
    if students_df is not None and not students_df.empty:
        # 1. Student status breakdown
        st.markdown("### Distribuição de Status dos Alunos")
        
        # Count by status
        active_count = len(students_df[students_df['status'] == 'active'])
        canceled_count = len(students_df[students_df['status'] == 'canceled'])
        
        # Create data for pie chart
        labels = ['Ativos', 'Cancelados']
        counts = [active_count, canceled_count]
        colors = ['lightgreen', 'salmon']
        
        # Pie chart
        fig_status = px.pie(
            values=counts,
            names=labels,
            title="Status dos Alunos",
            color_discrete_sequence=colors
        )
        fig_status.update_traces(textinfo='percent+value')
        st.plotly_chart(fig_status, use_container_width=True)
        
        # 2. Registration source analysis
        if 'source' in students_df.columns:
            st.markdown("### Origem dos Cadastros")
            
            # Count by source
            source_counts = students_df['source'].value_counts().reset_index()
            source_counts.columns = ['source', 'count']
            
            # Bar chart
            fig_source = px.bar(
                source_counts,
                x='source',
                y='count',
                color='source',
                title="Alunos por Origem de Cadastro"
            )
            fig_source.update_layout(xaxis_title="Origem", yaxis_title="Quantidade de Alunos")
            st.plotly_chart(fig_source, use_container_width=True)
        
        # 3. Course type distribution
        if 'course_type' in students_df.columns:
            st.markdown("### Tipos de Curso")
            
            # Count by course type
            course_counts = students_df['course_type'].value_counts().reset_index()
            course_counts.columns = ['course_type', 'count']
            
            # Create data for pie chart
            fig_course = px.pie(
                course_counts,
                values='count',
                names='course_type',
                title="Alunos por Tipo de Curso"
            )
            fig_course.update_traces(textinfo='percent+value')
            st.plotly_chart(fig_course, use_container_width=True)
        
        # 4. Enrollment trends over time
        st.markdown("### Tendência de Matrículas ao Longo do Tempo")
        
        # Ensure enrollment_date is in datetime format
        students_df['enrollment_date'] = pd.to_datetime(students_df['enrollment_date'])
        
        # Extract month and year from enrollment_date
        students_df['enrollment_month'] = students_df['enrollment_date'].dt.to_period('M')
        
        # Count enrollments by month
        enrollments_by_month = students_df.groupby('enrollment_month').size().reset_index()
        enrollments_by_month.columns = ['month', 'count']
        
        # Convert period to string for better display
        enrollments_by_month['month_str'] = enrollments_by_month['month'].astype(str)
        
        # Line chart
        fig_trend = px.line(
            enrollments_by_month,
            x='month_str',
            y='count',
            markers=True,
            title="Matrículas por Mês"
        )
        fig_trend.update_layout(xaxis_title="Mês", yaxis_title="Número de Matrículas")
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # 5. Student list with key metrics
        st.markdown("### Lista de Alunos com Métricas")
        
        # Create a copy for display
        display_students = students_df.copy()
        
        # Format phone numbers
        display_students['phone'] = display_students['phone'].apply(format_phone)
        
        # Calculate metrics for each student
        if payments_df is not None and not payments_df.empty:
            # Calculate payment metrics
            student_payment_stats = []
            
            for phone in students_df['phone']:
                # Get payments for this student
                student_payments = payments_df[payments_df['student_phone'] == phone]
                
                # Calculate payment stats
                total_payments = len(student_payments) if not student_payments.empty else 0
                paid_payments = len(student_payments[student_payments['payment_status'] == 'paid']) if not student_payments.empty else 0
                total_amount = student_payments['amount'].sum() if not student_payments.empty else 0
                paid_amount = student_payments[student_payments['payment_status'] == 'paid']['amount'].sum() if not student_payments.empty else 0
                
                student_payment_stats.append({
                    'phone': phone,
                    'total_payments': total_payments,
                    'paid_payments': paid_payments,
                    'payment_rate': paid_payments / total_payments if total_payments > 0 else 0,
                    'total_amount': total_amount,
                    'paid_amount': paid_amount,
                    'amount_rate': paid_amount / total_amount if total_amount > 0 else 0
                })
            
            # Convert to DataFrame
            payment_stats_df = pd.DataFrame(student_payment_stats)
            
            # Merge with student data
            display_students = display_students.merge(payment_stats_df, on='phone', how='left')
            
            # Format rates as percentages
            display_students['payment_rate'] = display_students['payment_rate'].apply(lambda x: f"{x*100:.1f}%")
            display_students['amount_rate'] = display_students['amount_rate'].apply(lambda x: f"{x*100:.1f}%")
            
            # Format amounts as currency
            display_students['total_amount'] = display_students['total_amount'].apply(format_currency)
            display_students['paid_amount'] = display_students['paid_amount'].apply(format_currency)
        
        # Calculate internship metrics for each student
        if internships_df is not None and not internships_df.empty:
            # Calculate internship hours
            student_internship_stats = []
            
            for phone in students_df['phone']:
                # Get internships for this student
                total_hours = 0
                internship_count = 0
                
                for _, row in internships_df.iterrows():
                    if pd.notna(row['students']) and phone in row['students'].split(','):
                        total_hours += row['hours']
                        internship_count += 1
                
                student_internship_stats.append({
                    'phone': phone,
                    'internship_count': internship_count,
                    'total_hours': total_hours
                })
            
            # Convert to DataFrame
            internship_stats_df = pd.DataFrame(student_internship_stats)
            
            # Merge with student data
            display_students = display_students.merge(internship_stats_df, on='phone', how='left')
        
        # Format status
        display_students['status'] = display_students['status'].map({
            'active': 'Ativo',
            'canceled': 'Cancelado'
        })
        
        # Format enrollment date
        display_students['enrollment_date'] = display_students['enrollment_date'].dt.strftime('%d/%m/%Y')
        
        # Select columns for display
        columns_to_display = [
            'name', 'phone', 'status', 'enrollment_date', 'course_type'
        ]
        
        # Add payment columns if available
        if 'payment_rate' in display_students.columns:
            columns_to_display.extend(['paid_payments', 'total_payments', 'payment_rate', 'paid_amount', 'total_amount'])
        
        # Add internship columns if available
        if 'total_hours' in display_students.columns:
            columns_to_display.extend(['internship_count', 'total_hours'])
        
        # Ensure all columns exist
        for col in columns_to_display:
            if col not in display_students.columns:
                display_students[col] = ""
        
        # Custom column labels
        column_labels = {
            'name': 'Nome',
            'phone': 'Telefone',
            'status': 'Status',
            'enrollment_date': 'Data de Matrícula',
            'course_type': 'Tipo de Curso',
            'paid_payments': 'Parcelas Pagas',
            'total_payments': 'Total de Parcelas',
            'payment_rate': 'Taxa de Pagamento',
            'paid_amount': 'Valor Pago',
            'total_amount': 'Valor Total',
            'internship_count': 'Número de Estágios',
            'total_hours': 'Horas de Estágio'
        }
        
        # Display the dataframe
        st.dataframe(
            display_students[columns_to_display], 
            use_container_width=True,
            column_config={col: column_labels.get(col, col) for col in columns_to_display}
        )
        
        # Export option
        if st.button("Exportar Lista Completa (CSV)"):
            export_df = display_students.copy()
            # Convert to CSV
            csv = export_df.to_csv(index=False).encode('utf-8')
            
            # Create download button
            st.download_button(
                "Baixar CSV",
                csv,
                "alunos_metricas.csv",
                "text/csv",
                key='download-csv-students-metrics'
            )
    else:
        st.info("Dados insuficientes para gerar relatórios de alunos.")

with tab4:
    st.subheader("Relatórios de Estágios")
    
    if internships_df is not None and not internships_df.empty:
        # 1. Internship activity over time
        st.markdown("### Atividade de Estágios ao Longo do Tempo")
        
        # Ensure date is in datetime format
        internships_df['date'] = pd.to_datetime(internships_df['date'])
        
        # Extract month and year from date
        internships_df['month'] = internships_df['date'].dt.to_period('M')
        
        # Count internships and sum hours by month
        internships_by_month = internships_df.groupby('month').agg({
            'internship_id': 'count',
            'hours': 'sum'
        }).reset_index()
        
        internships_by_month.columns = ['month', 'count', 'hours']
        
        # Convert period to string for better display
        internships_by_month['month_str'] = internships_by_month['month'].astype(str)
        
        # Create a column layout
        col1, col2 = st.columns(2)
        
        with col1:
            # Line chart - Count
            fig_count = px.line(
                internships_by_month,
                x='month_str',
                y='count',
                markers=True,
                title="Número de Estágios por Mês"
            )
            fig_count.update_layout(xaxis_title="Mês", yaxis_title="Número de Estágios")
            st.plotly_chart(fig_count, use_container_width=True)
        
        with col2:
            # Line chart - Hours
            fig_hours = px.line(
                internships_by_month,
                x='month_str',
                y='hours',
                markers=True,
                title="Horas de Estágio por Mês"
            )
            fig_hours.update_layout(xaxis_title="Mês", yaxis_title="Horas")
            st.plotly_chart(fig_hours, use_container_width=True)
        
        # 2. Topic analysis
        if 'topic' in internships_df.columns:
            st.markdown("### Análise de Temas de Estágio")
            
            # Count by topic
            topic_counts = internships_df['topic'].value_counts().reset_index()
            topic_counts.columns = ['topic', 'count']
            
            # Take only the top 10 topics
            top_topics = topic_counts.head(10)
            
            # Bar chart
            fig_topics = px.bar(
                top_topics,
                x='count',
                y='topic',
                orientation='h',
                title="Temas Mais Frequentes de Estágio"
            )
            fig_topics.update_layout(xaxis_title="Número de Estágios", yaxis_title="Tema")
            st.plotly_chart(fig_topics, use_container_width=True)
        
        # 3. Location analysis
        if 'location' in internships_df.columns:
            st.markdown("### Análise de Locais de Estágio")
            
            # Count by location
            location_counts = internships_df['location'].value_counts().reset_index()
            location_counts.columns = ['location', 'count']
            
            # Take only the top 10 locations
            top_locations = location_counts.head(10)
            
            # Bar chart
            fig_locations = px.bar(
                top_locations,
                x='count',
                y='location',
                orientation='h',
                title="Locais Mais Frequentes de Estágio"
            )
            fig_locations.update_layout(xaxis_title="Número de Estágios", yaxis_title="Local")
            st.plotly_chart(fig_locations, use_container_width=True)
        
        # 4. Student participation analysis
        st.markdown("### Participação dos Alunos em Estágios")
        
        # Expand the internships to have one row per student
        expanded_internships = []
        
        for _, row in internships_df.iterrows():
            if pd.notna(row['students']):
                students = row['students'].split(',')
                for student in students:
                    expanded_internships.append({
                        'student_phone': student,
                        'hours': row['hours'],
                        'date': row['date']
                    })
        
        if expanded_internships:
            expanded_df = pd.DataFrame(expanded_internships)
            
            # Group by student and calculate metrics
            student_stats = expanded_df.groupby('student_phone').agg({
                'hours': 'sum',
                'date': 'count'
            }).reset_index()
            
            student_stats.columns = ['student_phone', 'total_hours', 'internship_count']
            
            # Merge with student names if available
            if students_df is not None and not students_df.empty:
                student_stats = student_stats.merge(
                    students_df[['phone', 'name']],
                    left_on='student_phone',
                    right_on='phone',
                    how='left'
                )
            
            # Format phone numbers
            student_stats['student_phone'] = student_stats['student_phone'].apply(format_phone)
            
            # Sort by total hours descending
            student_stats = student_stats.sort_values('total_hours', ascending=False)
            
            # Select columns for display
            columns_to_display = ['name', 'student_phone', 'total_hours', 'internship_count']
            
            # Filter out columns that don't exist
            columns_to_display = [col for col in columns_to_display if col in student_stats.columns]
            
            # Custom column labels
            column_labels = {
                'name': 'Nome',
                'student_phone': 'Telefone',
                'total_hours': 'Total de Horas',
                'internship_count': 'Número de Estágios'
            }
            
            # Display the dataframe
            st.dataframe(
                student_stats[columns_to_display], 
                use_container_width=True,
                column_config={col: column_labels.get(col, col) for col in columns_to_display}
            )
            
            # Calculate summary statistics
            avg_hours = student_stats['total_hours'].mean()
            max_hours = student_stats['total_hours'].max()
            min_hours = student_stats['total_hours'].min()
            
            st.markdown(f"""
            **Resumo de Horas de Estágio:**
            * Média de horas por aluno: {avg_hours:.1f} horas
            * Máximo de horas por aluno: {max_hours} horas
            * Mínimo de horas por aluno: {min_hours} horas
            * Total de alunos com estágios: {len(student_stats)}
            """)
            
            # Export option
            if st.button("Exportar Dados de Estágio (CSV)"):
                export_df = student_stats.copy()
                # Convert to CSV
                csv = export_df.to_csv(index=False).encode('utf-8')
                
                # Create download button
                st.download_button(
                    "Baixar CSV",
                    csv,
                    "horas_estagio.csv",
                    "text/csv",
                    key='download-csv-internship-hours'
                )
        else:
            st.info("Não foi possível analisar a participação dos alunos nos estágios.")
    else:
        st.info("Dados insuficientes para gerar relatórios de estágios.")
