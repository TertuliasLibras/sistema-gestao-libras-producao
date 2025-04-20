import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
from utils import (
    load_students_data, 
    load_payments_data,
    load_internships_data,
    format_currency,
    get_active_students,
    get_canceled_students,
    get_payment_status_column
)
from auth_wrapper import verify_authentication

# Verificar autenticação
verify_authentication()

# Custom CSS para estilizar a página
st.markdown("""
<style>
    .dashboard-title {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #1E88E5;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .metric-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
    }
    .trend-up {
        color: #4CAF50;
    }
    .trend-down {
        color: #F44336;
    }
    .trend-neutral {
        color: #9E9E9E;
    }
</style>
""", unsafe_allow_html=True)

# Header com logo
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
    st.markdown('<div class="dashboard-title">Visualizações Avançadas</div>', unsafe_allow_html=True)

# Carregar dados
students_df = load_students_data()
payments_df = load_payments_data()
internships_df = load_internships_data()

# Verificar se há dados para analisar
if students_df.empty or payments_df.empty:
    st.warning("Não há dados suficientes para gerar visualizações avançadas. Certifique-se de que existem alunos e pagamentos cadastrados.")
else:
    # Criar tabs para diferentes visualizações
    tab1, tab2, tab3, tab4 = st.tabs([
        "KPIs Financeiros", 
        "Análise de Alunos", 
        "Projeções Financeiras",
        "Análise de Desempenho"
    ])

    # KPIs Financeiros
    with tab1:
        st.subheader("Indicadores Financeiros")

        # Configuração de período
        col1, col2 = st.columns(2)
        
        with col1:
            periodo = st.selectbox(
                "Período de Análise",
                ["Último Mês", "Últimos 3 Meses", "Últimos 6 Meses", "Último Ano", "Todo o Histórico"],
                index=2  # Padrão: Últimos 6 Meses
            )
        
        # Determinar datas de início e fim com base no período selecionado
        now = datetime.now()
        
        if periodo == "Último Mês":
            start_date = datetime(now.year, now.month, 1) - timedelta(days=1)
            start_date = datetime(start_date.year, start_date.month, 1)
            end_date = datetime(now.year, now.month, 1) - timedelta(days=1)
            _, last_day = calendar.monthrange(end_date.year, end_date.month)
            end_date = datetime(end_date.year, end_date.month, last_day)
        elif periodo == "Últimos 3 Meses":
            if now.month > 3:
                start_date = datetime(now.year, now.month - 3, 1)
            else:
                months_to_subtract = 3 - now.month
                start_year = now.year - 1
                start_month = 12 - months_to_subtract
                start_date = datetime(start_year, start_month, 1)
            end_date = datetime(now.year, now.month, 1) - timedelta(days=1)
            _, last_day = calendar.monthrange(end_date.year, end_date.month)
            end_date = datetime(end_date.year, end_date.month, last_day)
        elif periodo == "Últimos 6 Meses":
            if now.month > 6:
                start_date = datetime(now.year, now.month - 6, 1)
            else:
                months_to_subtract = 6 - now.month
                start_year = now.year - 1
                start_month = 12 - months_to_subtract
                start_date = datetime(start_year, start_month, 1)
            end_date = datetime(now.year, now.month, 1) - timedelta(days=1)
            _, last_day = calendar.monthrange(end_date.year, end_date.month)
            end_date = datetime(end_date.year, end_date.month, last_day)
        elif periodo == "Último Ano":
            start_date = datetime(now.year - 1, now.month, 1)
            end_date = datetime(now.year, now.month, 1) - timedelta(days=1)
            _, last_day = calendar.monthrange(end_date.year, end_date.month)
            end_date = datetime(end_date.year, end_date.month, last_day)
        else:  # Todo o Histórico
            # Encontrar a data mais antiga nos dados
            if not payments_df.empty and 'payment_date' in payments_df.columns:
                payment_dates = pd.to_datetime(payments_df['payment_date'].dropna())
                if not payment_dates.empty:
                    start_date = payment_dates.min()
                else:
                    start_date = datetime(now.year - 1, 1, 1)
            else:
                start_date = datetime(now.year - 1, 1, 1)
            
            end_date = now

        with col2:
            st.write(f"Período analisado: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")
        
        # Converter datas para datetime
        payments_df['payment_date'] = pd.to_datetime(payments_df['payment_date'])
        payments_df['due_date'] = pd.to_datetime(payments_df['due_date'])
        
        # Filtrar pagamentos pelo período
        filtered_payments = payments_df[
            (payments_df['payment_date'] >= start_date) & 
            (payments_df['payment_date'] <= end_date)
        ]
        
        # Usar a função get_payment_status_column para obter o nome correto da coluna
        status_column = get_payment_status_column(filtered_payments)
        
        # Métricas Financeiras
        if not filtered_payments.empty:
            # Receita Total
            paid_payments = filtered_payments[filtered_payments[status_column] == 'paid']
            total_revenue = paid_payments['amount'].sum()
            
            # Ticket Médio
            avg_payment = 0
            if len(paid_payments) > 0:
                avg_payment = total_revenue / len(paid_payments)
            
            # Inadimplência
            overdue_payments = payments_df[
                (payments_df[status_column] == 'pending') & 
                (payments_df['due_date'] < now) &
                (payments_df['due_date'] >= start_date) &
                (payments_df['due_date'] <= end_date)
            ]
            total_overdue = overdue_payments['amount'].sum()
            
            # Taxa de inadimplência
            total_expected = filtered_payments['amount'].sum()
            overdue_rate = 0
            if total_expected > 0:
                overdue_rate = (total_overdue / total_expected) * 100
            
            # Mostrar KPIs
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown('<div class="metric-title">Receita Total</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-value">{format_currency(total_revenue)}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown('<div class="metric-title">Ticket Médio</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-value">{format_currency(avg_payment)}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown('<div class="metric-title">Taxa de Inadimplência</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-value">{overdue_rate:.1f}%</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Receita Mensal
            st.subheader("Receita Mensal")
            
            # Agrupar por mês
            monthly_revenue = filtered_payments[filtered_payments[status_column] == 'paid'].copy()
            monthly_revenue['month_year'] = monthly_revenue['payment_date'].dt.strftime('%Y-%m')
            
            revenue_by_month = monthly_revenue.groupby('month_year')['amount'].sum().reset_index()
            revenue_by_month.columns = ['Mês', 'Receita']
            
            # Formatar mês para exibição
            revenue_by_month['Mês/Ano'] = revenue_by_month['Mês'].apply(
                lambda x: f"{x.split('-')[1]}/{x.split('-')[0]}"
            )
            
            # Gráfico de receita mensal
            if len(revenue_by_month) > 1:
                fig = px.line(
                    revenue_by_month, 
                    x='Mês/Ano', 
                    y='Receita',
                    markers=True,
                    title="Evolução da Receita Mensal"
                )
                fig.update_layout(xaxis_title="Mês", yaxis_title="Receita (R$)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Não há dados suficientes para mostrar a evolução da receita mensal.")
            
            # Distribuição de Status de Pagamento
            st.subheader("Distribuição de Status de Pagamento")
            
            # Contar pagamentos por status
            status = filtered_payments[status_column].value_counts().reset_index()
            status.columns = ['Status', 'Quantidade']
            
            # Mapear nomes de status
            status_map = {
                'paid': 'Pago',
                'pending': 'Pendente',
                'overdue': 'Atrasado',
                'canceled': 'Cancelado'
            }
            payment_status['Status'] = payment_status['Status'].map(lambda x: status_map.get(x, x))
            
            # Gráfico de pizza de status
            if not payment_status.empty:
                fig = px.pie(
                    payment_status, 
                    names='Status', 
                    values='Quantidade',
                    title="Distribuição de Status de Pagamento",
                    color='Status',
                    color_discrete_map={
                        'Pago': '#4CAF50',
                        'Pendente': '#FFC107',
                        'Atrasado': '#F44336',
                        'Cancelado': '#9E9E9E'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Não há dados suficientes para mostrar a distribuição de status de pagamento.")
        else:
            st.info(f"Não há pagamentos registrados no período de {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}.")

    # Análise de Alunos
    with tab2:
        st.subheader("Análise de Alunos")
        
        # Métricas gerais
        total_students = len(students_df)
        active_students_count = len(get_active_students(students_df))
        canceled_students_count = len(get_canceled_students(students_df))
        
        # Taxa de retenção
        retention_rate = 0
        if total_students > 0:
            retention_rate = (active_students_count / total_students) * 100
        
        # Mostrar métricas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-title">Total de Alunos</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{total_students}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-title">Alunos Ativos</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{active_students_count}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-title">Taxa de Retenção</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{retention_rate:.1f}%</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Evolução da base de alunos
        if not students_df.empty and 'enrollment_date' in students_df.columns:
            st.subheader("Evolução da Base de Alunos")
            
            # Converter datas para datetime
            students_df['enrollment_date'] = pd.to_datetime(students_df['enrollment_date'])
            
            if 'cancellation_date' in students_df.columns:
                students_df['cancellation_date'] = pd.to_datetime(students_df['cancellation_date'])
            
            # Agrupar matrículas por mês
            enrollments_monthly = students_df.groupby(
                students_df['enrollment_date'].dt.strftime('%Y-%m')
            ).size().reset_index(name='Novas_Matrículas')
            
            enrollments_monthly.columns = ['Mês', 'Novas_Matrículas']
            
            # Calcular cancelamentos por mês (se houver dados)
            if 'cancellation_date' in students_df.columns:
                canceled_df = students_df.dropna(subset=['cancellation_date'])
                
                if not canceled_df.empty:
                    cancellations_monthly = canceled_df.groupby(
                        canceled_df['cancellation_date'].dt.strftime('%Y-%m')
                    ).size().reset_index(name='Cancelamentos')
                    
                    cancellations_monthly.columns = ['Mês', 'Cancelamentos']
                    
                    # Mesclando datasets
                    monthly_data = pd.merge(
                        enrollments_monthly, 
                        cancellations_monthly, 
                        on='Mês', 
                        how='outer'
                    ).fillna(0)
                else:
                    monthly_data = enrollments_monthly.copy()
                    monthly_data['Cancelamentos'] = 0
            else:
                monthly_data = enrollments_monthly.copy()
                monthly_data['Cancelamentos'] = 0
            
            # Calcular crescimento líquido
            monthly_data['Crescimento_Líquido'] = monthly_data['Novas_Matrículas'] - monthly_data['Cancelamentos']
            
            # Calcular base acumulada
            monthly_data = monthly_data.sort_values('Mês')
            monthly_data['Base_Acumulada'] = monthly_data['Crescimento_Líquido'].cumsum()
            
            # Formatar mês para exibição
            monthly_data['Mês/Ano'] = monthly_data['Mês'].apply(
                lambda x: f"{x.split('-')[1]}/{x.split('-')[0]}"
            )
            
            # Gráfico de evolução
            if len(monthly_data) > 1:
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=monthly_data['Mês/Ano'],
                    y=monthly_data['Base_Acumulada'],
                    mode='lines+markers',
                    name='Base de Alunos',
                    line=dict(color='#1E88E5', width=3)
                ))
                
                fig.add_trace(go.Bar(
                    x=monthly_data['Mês/Ano'],
                    y=monthly_data['Novas_Matrículas'],
                    name='Novas Matrículas',
                    marker_color='#4CAF50'
                ))
                
                fig.add_trace(go.Bar(
                    x=monthly_data['Mês/Ano'],
                    y=monthly_data['Cancelamentos'] * -1,  # Valores negativos para visualização
                    name='Cancelamentos',
                    marker_color='#F44336'
                ))
                
                fig.update_layout(
                    title="Evolução da Base de Alunos",
                    xaxis_title="Mês",
                    yaxis_title="Quantidade de Alunos",
                    barmode='relative',
                    hovermode="x",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Não há dados suficientes para mostrar a evolução da base de alunos.")
            
            # Distribuição por status
            st.subheader("Distribuição de Alunos por Status")
            
            if 'status' in students_df.columns:
                status_counts = students_df['status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Quantidade']
                
                # Mapear nomes de status
                status_map = {
                    'active': 'Ativo',
                    'canceled': 'Cancelado',
                    'suspended': 'Suspenso',
                    'graduated': 'Formado'
                }
                status_counts['Status'] = status_counts['Status'].map(lambda x: status_map.get(x, x))
                
                # Gráfico de pizza de status
                if not status_counts.empty:
                    fig = px.pie(
                        status_counts, 
                        names='Status', 
                        values='Quantidade',
                        title="Distribuição de Alunos por Status",
                        color='Status',
                        color_discrete_map={
                            'Ativo': '#4CAF50',
                            'Cancelado': '#F44336',
                            'Suspenso': '#FFC107',
                            'Formado': '#2196F3'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Não há dados suficientes para mostrar a distribuição por status.")
            else:
                st.info("Não há informações de status nos dados dos alunos.")
            
            # Origem de matrícula
            if 'registration_origin' in students_df.columns:
                st.subheader("Origem de Matrícula")
                
                origin_counts = students_df['registration_origin'].value_counts().reset_index()
                origin_counts.columns = ['Origem', 'Quantidade']
                
                if not origin_counts.empty:
                    # Se houver muitas origens, mostrar apenas as 5 principais
                    if len(origin_counts) > 5:
                        other_count = origin_counts.iloc[5:]['Quantidade'].sum()
                        top_origins = origin_counts.iloc[:5].copy()
                        other_row = pd.DataFrame({'Origem': ['Outros'], 'Quantidade': [other_count]})
                        origin_counts = pd.concat([top_origins, other_row], ignore_index=True)
                    
                    fig = px.bar(
                        origin_counts, 
                        x='Origem', 
                        y='Quantidade',
                        title="Distribuição por Origem de Matrícula",
                        color='Origem',
                        text='Quantidade'
                    )
                    fig.update_traces(texttemplate='%{text}', textposition='outside')
                    fig.update_layout(xaxis_title="Origem", yaxis_title="Quantidade de Alunos")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Não há dados suficientes para mostrar a distribuição por origem.")
            else:
                st.info("Não há informações de origem de matrícula nos dados dos alunos.")
        else:
            st.info("Não há dados suficientes para análise de alunos.")

    # Projeções Financeiras
    with tab3:
        st.subheader("Projeções Financeiras")
        
        # Projeção de receita futura com base nas matrículas atuais
        active_students = get_active_students(students_df)
        
        if not active_students.empty and 'monthly_fee' in active_students.columns:
            # Calcular receita mensal projetada com base nos alunos ativos
            current_monthly_revenue = active_students['monthly_fee'].sum()
            
            # Projetar os próximos 12 meses
            st.subheader("Projeção de Receita para os Próximos 12 Meses")
            
            # Opções de cenário
            cenario = st.radio(
                "Cenário de Projeção",
                ["Conservador (sem novos alunos)", "Moderado (crescimento de 5% ao mês)", "Otimista (crescimento de 10% ao mês)"],
                horizontal=True
            )
            
            # Definir taxa de crescimento com base no cenário
            if cenario == "Conservador (sem novos alunos)":
                growth_rate = 0
            elif cenario == "Moderado (crescimento de 5% ao mês)":
                growth_rate = 0.05
            else:  # Otimista
                growth_rate = 0.10
            
            # Definir taxa de cancelamento
            churn_rate = 0.03  # 3% de cancelamento por mês
            
            # Calcular projeção
            months = 12
            projection_data = []
            
            current_revenue = current_monthly_revenue
            current_students = len(active_students)
            
            for i in range(1, months + 1):
                month_date = datetime.now() + timedelta(days=30 * i)
                month_name = month_date.strftime('%b/%Y')
                
                # Calcular cancelamentos
                churned_students = round(current_students * churn_rate)
                revenue_loss = churned_students * (current_revenue / current_students) if current_students > 0 else 0
                
                # Calcular novos alunos
                new_students = round(current_students * growth_rate)
                revenue_gain = new_students * (current_revenue / current_students) if current_students > 0 else 0
                
                # Atualizar valores para o próximo mês
                current_students = current_students - churned_students + new_students
                current_revenue = current_revenue - revenue_loss + revenue_gain
                
                projection_data.append({
                    'Mês': month_name,
                    'Receita Projetada': current_revenue,
                    'Alunos Projetados': current_students
                })
            
            # Criar DataFrame
            projection_df = pd.DataFrame(projection_data)
            
            # Gráfico de projeção
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=projection_df['Mês'],
                y=projection_df['Receita Projetada'],
                mode='lines+markers',
                name='Receita Projetada',
                line=dict(color='#1E88E5', width=3)
            ))
            
            fig.update_layout(
                title=f"Projeção de Receita - Cenário {cenario.split('(')[0].strip()}",
                xaxis_title="Mês",
                yaxis_title="Receita Projetada (R$)",
                hovermode="x"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Métricas principais da projeção
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="Receita Atual", 
                    value=format_currency(current_monthly_revenue)
                )
            
            with col2:
                projected_revenue_end = projection_df.iloc[-1]['Receita Projetada']
                revenue_change = ((projected_revenue_end / current_monthly_revenue) - 1) * 100 if current_monthly_revenue > 0 else 0
                
                st.metric(
                    label="Receita Projetada (12 meses)", 
                    value=format_currency(projected_revenue_end),
                    delta=f"{revenue_change:.1f}%"
                )
            
            with col3:
                projected_students_end = projection_df.iloc[-1]['Alunos Projetados']
                students_change = ((projected_students_end / len(active_students)) - 1) * 100 if len(active_students) > 0 else 0
                
                st.metric(
                    label="Alunos Projetados (12 meses)", 
                    value=int(projected_students_end),
                    delta=f"{students_change:.1f}%"
                )
            
            # Mostrar dados tabulares
            with st.expander("Ver dados detalhados da projeção"):
                # Formatar valores de receita
                projection_df['Receita Formatada'] = projection_df['Receita Projetada'].apply(lambda x: format_currency(x))
                display_df = projection_df[['Mês', 'Receita Formatada', 'Alunos Projetados']]
                display_df.columns = ['Mês', 'Receita Projetada', 'Alunos Projetados']
                st.dataframe(display_df, use_container_width=True)
        else:
            st.info("Não há dados suficientes para projeções financeiras. Certifique-se de que existem alunos ativos com valores de mensalidade cadastrados.")

    # Análise de Desempenho
    with tab4:
        st.subheader("Análise de Desempenho")
        
        if not students_df.empty and not payments_df.empty and not internships_df.empty:
            # Análise de correlações
            active_students = get_active_students(students_df)
            
            if not active_students.empty:
                # Relação entre horas de estágio e pagamentos
                st.subheader("Relação Entre Participação em Estágios e Pagamentos")
                
                # Criar DataFrame para análise
                analysis_data = []
                
                for _, student in active_students.iterrows():
                    student_phone = student['phone']
                    
                    # Obter total de horas de estágio
                    internship_hours = 0
                    if not internships_df.empty and 'students' in internships_df.columns and 'hours' in internships_df.columns:
                        # Verificar se a coluna students é do tipo string
                        internships_df['students'] = internships_df['students'].astype(str)
                        # Agora podemos usar str.contains com segurança
                        student_internships = internships_df[internships_df['students'].str.contains(student_phone, na=False)]
                        if not student_internships.empty:
                            internship_hours = student_internships['hours'].sum()
                    
                    # Obter status de pagamentos
                    student_payments = payments_df[payments_df['phone'] == student_phone]
                    
                    if not student_payments.empty:
                        status_column = get_payment_status_column(student_payments)
                        total_payments = len(student_payments)
                        paid_payments = len(student_payments[student_payments[status_column] == 'paid'])
                        payment_rate = (paid_payments / total_payments) * 100 if total_payments > 0 else 0
                        
                        analysis_data.append({
                            'Aluno': student['name'],
                            'Telefone': student_phone,
                            'Horas de Estágio': internship_hours,
                            'Taxa de Pagamento': payment_rate
                        })
                
                # Criar DataFrame
                analysis_df = pd.DataFrame(analysis_data)
                
                if len(analysis_df) > 5:  # Verificar se há dados suficientes
                    # Gráfico de dispersão
                    fig = px.scatter(
                        analysis_df, 
                        x='Horas de Estágio', 
                        y='Taxa de Pagamento',
                        hover_name='Aluno',
                        title="Relação Entre Horas de Estágio e Taxa de Pagamento",
                        trendline='ols',  # Adicionar linha de tendência
                        labels={
                            'Horas de Estágio': 'Total de Horas de Estágio',
                            'Taxa de Pagamento': 'Taxa de Pagamento (%)'
                        }
                    )
                    
                    fig.update_layout(
                        xaxis_title="Horas de Estágio",
                        yaxis_title="Taxa de Pagamento (%)"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Calcular correlação
                    correlation = analysis_df['Horas de Estágio'].corr(analysis_df['Taxa de Pagamento'])
                    
                    if correlation > 0.3:
                        insight = "Os dados indicam uma correlação positiva entre a participação em estágios e a pontualidade de pagamento. Alunos que participam mais ativamente dos estágios tendem a manter seus pagamentos em dia."
                    elif correlation < -0.3:
                        insight = "Os dados indicam uma correlação negativa entre a participação em estágios e a pontualidade de pagamento. Curiosamente, alunos com mais horas de estágio tendem a ter taxas de pagamento menores."
                    else:
                        insight = "Não há uma correlação significativa entre a participação em estágios e a pontualidade de pagamento com base nos dados atuais."
                    
                    st.info(insight)
                else:
                    st.info("Não há dados suficientes para análise de correlação entre estágios e pagamentos.")
                
                # Análise de segmentação de alunos
                if len(active_students) > 5:
                    st.subheader("Segmentação de Alunos")
                    
                    # Criar DataFrame para segmentação
                    if 'monthly_fee' in active_students.columns:
                        segment_data = []
                        
                        for _, student in active_students.iterrows():
                            student_phone = student['phone']
                            monthly_fee = student['monthly_fee']
                            
                            # Estágios
                            internship_hours = 0
                            if not internships_df.empty and 'students' in internships_df.columns and 'hours' in internships_df.columns:
                                # Verificar se a coluna students é do tipo string
                                internships_df['students'] = internships_df['students'].astype(str)
                                # Agora podemos usar str.contains com segurança
                                student_internships = internships_df[internships_df['students'].str.contains(student_phone, na=False)]
                                if not student_internships.empty:
                                    internship_hours = student_internships['hours'].sum()
                            
                            # Pagamentos
                            student_payments = payments_df[payments_df['phone'] == student_phone]
                            payment_score = 0
                            
                            if not student_payments.empty:
                                status_column = get_payment_status_column(student_payments)
                                total_payments = len(student_payments)
                                paid_payments = len(student_payments[student_payments[status_column] == 'paid'])
                                payment_score = (paid_payments / total_payments) * 100 if total_payments > 0 else 0
                            
                            segment_data.append({
                                'Aluno': student['name'],
                                'Mensalidade': monthly_fee,
                                'Horas de Estágio': internship_hours,
                                'Pontuação de Pagamento': payment_score
                            })
                        
                        segment_df = pd.DataFrame(segment_data)
                        
                        # Normalizar valores para segmentação
                        segment_df['Mensalidade_norm'] = (segment_df['Mensalidade'] - segment_df['Mensalidade'].min()) / (segment_df['Mensalidade'].max() - segment_df['Mensalidade'].min()) if segment_df['Mensalidade'].max() > segment_df['Mensalidade'].min() else 0
                        segment_df['Estágio_norm'] = (segment_df['Horas de Estágio'] - segment_df['Horas de Estágio'].min()) / (segment_df['Horas de Estágio'].max() - segment_df['Horas de Estágio'].min()) if segment_df['Horas de Estágio'].max() > segment_df['Horas de Estágio'].min() else 0
                        segment_df['Pagamento_norm'] = segment_df['Pontuação de Pagamento'] / 100
                        
                        # Calcular valor do aluno (simples)
                        segment_df['Valor_Total'] = (segment_df['Mensalidade_norm'] * 0.5) + (segment_df['Estágio_norm'] * 0.2) + (segment_df['Pagamento_norm'] * 0.3)
                        
                        # Classificar alunos
                        segment_df['Segmento'] = pd.qcut(
                            segment_df['Valor_Total'], 
                            3, 
                            labels=['Precisa Atenção', 'Regular', 'Destaque']
                        )
                        
                        # Gráfico de bolhas
                        fig = px.scatter(
                            segment_df, 
                            x='Mensalidade', 
                            y='Horas de Estágio',
                            size='Pontuação de Pagamento', 
                            color='Segmento',
                            hover_name='Aluno',
                            title="Segmentação de Alunos",
                            size_max=30,
                            color_discrete_map={
                                'Destaque': '#4CAF50',
                                'Regular': '#FFC107',
                                'Precisa Atenção': '#F44336'
                            }
                        )
                        
                        fig.update_layout(
                            xaxis_title="Mensalidade (R$)",
                            yaxis_title="Horas de Estágio"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Distribuição de segmentos
                        segment_counts = segment_df['Segmento'].value_counts().reset_index()
                        segment_counts.columns = ['Segmento', 'Quantidade']
                        
                        fig = px.pie(
                            segment_counts, 
                            names='Segmento', 
                            values='Quantidade',
                            title="Distribuição de Segmentos de Alunos",
                            color='Segmento',
                            color_discrete_map={
                                'Destaque': '#4CAF50',
                                'Regular': '#FFC107',
                                'Precisa Atenção': '#F44336'
                            }
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Insights baseados na segmentação
                        destaque_count = len(segment_df[segment_df['Segmento'] == 'Destaque'])
                        atencao_count = len(segment_df[segment_df['Segmento'] == 'Precisa Atenção'])
                        
                        destaque_pct = (destaque_count / len(segment_df)) * 100 if len(segment_df) > 0 else 0
                        atencao_pct = (atencao_count / len(segment_df)) * 100 if len(segment_df) > 0 else 0
                        
                        st.subheader("Insights de Segmentação")
                        
                        insight_text = f"""
                        - **{destaque_pct:.1f}%** dos alunos estão no segmento de **Destaque**, representando alunos com alto valor para a instituição.
                        - **{atencao_pct:.1f}%** dos alunos estão no segmento **Precisa Atenção**, que podem se beneficiar de acompanhamento mais próximo.
                        """
                        
                        st.markdown(insight_text)
                        
                        # Lista dos alunos que precisam de atenção
                        if atencao_count > 0:
                            with st.expander("Ver alunos que precisam de atenção"):
                                attention_students = segment_df[segment_df['Segmento'] == 'Precisa Atenção']
                                st.dataframe(
                                    attention_students[['Aluno', 'Mensalidade', 'Horas de Estágio', 'Pontuação de Pagamento']],
                                    use_container_width=True
                                )
                    else:
                        st.info("Não há informações de mensalidade para realizar a segmentação.")
                else:
                    st.info("Não há dados suficientes para segmentação de alunos.")
            else:
                st.info("Não há alunos ativos para realizar a análise de desempenho.")
        else:
            st.info("Não há dados suficientes para análise de desempenho. Certifique-se de que existem alunos, pagamentos e estágios cadastrados.")
