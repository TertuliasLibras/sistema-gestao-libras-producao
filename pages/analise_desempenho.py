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
    format_phone,
    format_currency,
    get_active_students,
    get_student_internship_hours,
    get_student_internship_topics
)
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
    .insight-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        margin-bottom: 1rem;
        border-left: 5px solid #4CAF50;
    }
    .insight-title {
        color: #1E3A8A;
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
    }
    .insight-content {
        color: #333;
    }
    .warning-card {
        border-left: 5px solid #FFC107;
    }
    .critical-card {
        border-left: 5px solid #F44336;
    }
    .info-card {
        border-left: 5px solid #2196F3;
    }
    .success-card {
        border-left: 5px solid #4CAF50;
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
    st.title("Análise de Desempenho")

# Carregar dados
students_df = load_students_data()
payments_df = load_payments_data()
internships_df = load_internships_data()

# Verificar se temos dados suficientes
if students_df is None or students_df.empty:
    st.info("Não há alunos cadastrados para análise de desempenho.")
    st.stop()

# Função para renderizar cards de insights
def render_insight_card(title, content, tipo="info"):
    st.markdown(f"""
    <div class="insight-card {tipo}-card">
        <div class="insight-title">{title}</div>
        <div class="insight-content">{content}</div>
    </div>
    """, unsafe_allow_html=True)

# Análise geral do curso
st.header("Análise Geral do Curso")

# Contagem de alunos por status
active_students = get_active_students(students_df)
canceled_students = students_df[students_df['status'] == 'canceled'] if 'status' in students_df.columns else pd.DataFrame()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total de Alunos", len(students_df))
with col2:
    st.metric("Alunos Ativos", len(active_students))
with col3:
    st.metric("Alunos Cancelados", len(canceled_students))

# Gráfico de pizza com status dos alunos
status_counts = students_df['status'].value_counts().reset_index()
status_counts.columns = ['Status', 'Contagem']
status_counts['Status'] = status_counts['Status'].map({'active': 'Ativo', 'canceled': 'Cancelado'})

fig = px.pie(status_counts, values='Contagem', names='Status', 
             title='Distribuição de Alunos por Status',
             color_discrete_sequence=px.colors.sequential.Viridis)
st.plotly_chart(fig, use_container_width=True)

# Distribuição de alunos por mês de matrícula
if 'enrollment_date' in students_df.columns:
    # Converter para datetime
    students_df['enrollment_date'] = pd.to_datetime(students_df['enrollment_date'])
    
    # Extrair mês e ano
    students_df['enrollment_month'] = students_df['enrollment_date'].dt.month
    students_df['enrollment_year'] = students_df['enrollment_date'].dt.year
    
    # Agrupar por mês e ano
    enrollment_counts = students_df.groupby(['enrollment_year', 'enrollment_month']).size().reset_index(name='count')
    enrollment_counts['month_name'] = enrollment_counts['enrollment_month'].apply(lambda x: calendar.month_name[x])
    enrollment_counts['year_month'] = enrollment_counts.apply(lambda x: f"{x['enrollment_year']}-{x['enrollment_month']:02d}", axis=1)
    
    # Ordenar por ano e mês
    enrollment_counts = enrollment_counts.sort_values('year_month')
    
    # Criar gráfico de barras
    fig = px.bar(enrollment_counts, x='month_name', y='count', 
                 color='enrollment_year', 
                 title='Matrículas por Mês',
                 labels={'count': 'Número de Matrículas', 'month_name': 'Mês', 'enrollment_year': 'Ano'})
    st.plotly_chart(fig, use_container_width=True)
    
    # Insights sobre crescimento
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Matrículas nos últimos 3 meses
    recent_enrollments = students_df[
        (students_df['enrollment_date'] > (datetime.now() - timedelta(days=90)))
    ]
    
    # Tendência de crescimento
    if not recent_enrollments.empty:
        enrollment_rate = len(recent_enrollments) / 3  # média mensal dos últimos 3 meses
        render_insight_card(
            "Tendência de Crescimento",
            f"Nos últimos 3 meses, o curso teve uma média de {enrollment_rate:.1f} novas matrículas por mês.",
            "info"
        )

# Análise de Pagamentos
st.header("Análise de Pagamentos")

if payments_df is not None and not payments_df.empty:
    # Converter datas para datetime
    payments_df['due_date'] = pd.to_datetime(payments_df['due_date'])
    payments_df['payment_date'] = pd.to_datetime(payments_df['payment_date'])
    
    # Calcular taxa de pagamentos em dia
    paid_payments = payments_df[payments_df['status'] == 'paid']
    if not paid_payments.empty and 'payment_date' in paid_payments.columns and 'due_date' in paid_payments.columns:
        # Remover NAs
        paid_with_dates = paid_payments.dropna(subset=['payment_date', 'due_date'])
        
        if not paid_with_dates.empty:
            # Calcular pagamentos em dia
            on_time_payments = paid_with_dates[paid_with_dates['payment_date'] <= paid_with_dates['due_date']]
            on_time_rate = len(on_time_payments) / len(paid_with_dates) * 100
            
            st.metric("Taxa de Pagamentos em Dia", f"{on_time_rate:.1f}%")
            
            # Card com insight sobre pagamentos
            if on_time_rate > 90:
                render_insight_card(
                    "Excelente Taxa de Pagamentos em Dia",
                    f"A taxa de {on_time_rate:.1f}% de pagamentos em dia indica um excelente compromisso dos alunos com o curso.",
                    "success"
                )
            elif on_time_rate > 75:
                render_insight_card(
                    "Boa Taxa de Pagamentos em Dia",
                    f"A taxa de {on_time_rate:.1f}% de pagamentos em dia é boa, mas há espaço para melhorias com lembretes proativos.",
                    "info"
                )
            else:
                render_insight_card(
                    "Atenção: Taxa de Pagamentos em Dia Baixa",
                    f"A taxa de {on_time_rate:.1f}% de pagamentos em dia indica a necessidade de um melhor sistema de lembretes e acompanhamento financeiro.",
                    "warning"
                )
    
    # Status dos pagamentos
    payment_status = payments_df['status'].value_counts().reset_index()
    payment_status.columns = ['Status', 'Contagem']
    payment_status['Status'] = payment_status['Status'].map({
        'paid': 'Pago',
        'pending': 'Pendente',
        'overdue': 'Atrasado',
        'canceled': 'Cancelado'
    })
    
    fig = px.pie(payment_status, values='Contagem', names='Status', 
                 title='Distribuição de Pagamentos por Status',
                 color_discrete_sequence=px.colors.sequential.Viridis)
    st.plotly_chart(fig, use_container_width=True)
    
    # Identificar pagamentos atrasados
    today = datetime.now().date()
    overdue_payments = payments_df[
        (payments_df['status'] == 'pending') & 
        (pd.to_datetime(payments_df['due_date']).dt.date < today)
    ]
    
    if not overdue_payments.empty:
        # Agrupar por aluno
        overdue_by_student = overdue_payments.groupby('phone').size().reset_index(name='count')
        overdue_by_student = overdue_by_student.merge(
            students_df[['phone', 'name']], 
            on='phone', 
            how='left'
        )
        
        # Mostrar alunos com pagamentos atrasados
        st.subheader("Alunos com Pagamentos Atrasados")
        
        # Formatar telefone
        overdue_by_student['phone_formatted'] = overdue_by_student['phone'].apply(format_phone)
        
        st.dataframe(
            overdue_by_student[['name', 'phone_formatted', 'count']],
            column_config={
                'name': 'Nome',
                'phone_formatted': 'Telefone',
                'count': 'Pagamentos Atrasados'
            },
            use_container_width=True
        )
        
        # Card de insight
        if len(overdue_by_student) > 5:
            render_insight_card(
                "Atenção: Alto Número de Alunos com Pagamentos Atrasados",
                f"Existem {len(overdue_by_student)} alunos com pagamentos atrasados. Considere implementar um sistema de lembretes automáticos.",
                "critical"
            )

# Análise de Estágios
st.header("Análise de Estágios")

if internships_df is not None and not internships_df.empty:
    # Converter data para datetime
    internships_df['date'] = pd.to_datetime(internships_df['date'])
    
    # Calcular horas totais de estágio
    total_hours = internships_df['duration_hours'].sum()
    
    # Média de horas por estágio
    avg_hours_per_internship = internships_df['duration_hours'].mean()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total de Horas de Estágio", f"{total_hours:.1f}h")
    with col2:
        st.metric("Média de Horas por Estágio", f"{avg_hours_per_internship:.1f}h")
    
    # Estágios por mês
    internships_df['month'] = internships_df['date'].dt.month
    internships_df['year'] = internships_df['date'].dt.year
    
    internships_by_month = internships_df.groupby(['year', 'month']).agg({
        'duration_hours': 'sum',
        'topic': 'count'
    }).reset_index()
    
    internships_by_month['month_name'] = internships_by_month['month'].apply(lambda x: calendar.month_name[x])
    internships_by_month['year_month'] = internships_by_month.apply(lambda x: f"{x['year']}-{x['month']:02d}", axis=1)
    internships_by_month = internships_by_month.sort_values('year_month')
    
    # Gráfico de horas de estágio por mês
    fig = px.bar(
        internships_by_month, 
        x='month_name', 
        y='duration_hours',
        color='year',
        title='Horas de Estágio por Mês',
        labels={'duration_hours': 'Horas de Estágio', 'month_name': 'Mês', 'year': 'Ano'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Temas mais frequentes
    topics_count = {}
    for _, row in internships_df.iterrows():
        topic = row['topic']
        if topic in topics_count:
            topics_count[topic] += 1
        else:
            topics_count[topic] = 1
    
    topics_df = pd.DataFrame({
        'Tema': list(topics_count.keys()),
        'Frequência': list(topics_count.values())
    }).sort_values('Frequência', ascending=False)
    
    # Mostrar temas mais frequentes
    st.subheader("Temas de Estágio Mais Frequentes")
    
    # Limitar aos top 10
    top_topics = topics_df.head(10)
    
    fig = px.bar(
        top_topics,
        x='Tema',
        y='Frequência',
        color='Frequência',
        title='Top 10 Temas de Estágio',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Insight sobre temas populares
    if not top_topics.empty:
        top_theme = top_topics.iloc[0]['Tema']
        render_insight_card(
            "Tema Mais Popular",
            f"O tema '{top_theme}' é o mais frequente nos estágios, mostrando forte interesse dos alunos nesta área.",
            "info"
        )

# Análise individual de alunos
st.header("Análise Individual de Alunos")

# Seleção de aluno
selected_student = st.selectbox(
    "Selecione um aluno para análise detalhada:",
    options=students_df['phone'].tolist(),
    format_func=lambda x: f"{format_phone(x)} - {students_df[students_df['phone'] == x]['name'].values[0]}"
)

# Analisar aluno selecionado
if selected_student:
    # Obter dados do aluno
    student = students_df[students_df['phone'] == selected_student].iloc[0]
    
    # Informações básicas
    st.subheader(f"Análise de {student['name']}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        enrollment_date = pd.to_datetime(student['enrollment_date']) if 'enrollment_date' in student.index and pd.notna(student['enrollment_date']) else None
        enrollment_date_str = enrollment_date.strftime('%d/%m/%Y') if enrollment_date else "N/A"
        st.metric("Data de Matrícula", enrollment_date_str)
    
    with col2:
        status_map = {'active': 'Ativo', 'canceled': 'Cancelado'}
        st.metric("Status", status_map.get(student['status'], student['status']))
    
    with col3:
        monthly_fee = format_currency(student['monthly_fee']) if 'monthly_fee' in student.index else "N/A"
        st.metric("Mensalidade", monthly_fee)
    
    # Análise de pagamentos do aluno
    if payments_df is not None and not payments_df.empty:
        student_payments = payments_df[payments_df['phone'] == selected_student]
        
        if not student_payments.empty:
            # Status dos pagamentos do aluno
            student_payment_status = student_payments['status'].value_counts().reset_index()
            student_payment_status.columns = ['Status', 'Contagem']
            student_payment_status['Status'] = student_payment_status['Status'].map({
                'paid': 'Pago',
                'pending': 'Pendente',
                'overdue': 'Atrasado',
                'canceled': 'Cancelado'
            })
            
            fig = px.pie(
                student_payment_status, 
                values='Contagem', 
                names='Status', 
                title='Status dos Pagamentos',
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Verificar pagamentos atrasados
            overdue_count = len(student_payments[student_payments['status'] == 'overdue'])
            pending_count = len(student_payments[student_payments['status'] == 'pending'])
            
            if overdue_count > 0:
                render_insight_card(
                    "Pagamentos Atrasados",
                    f"Este aluno possui {overdue_count} pagamento(s) atrasado(s). Entre em contato para regularizar a situação.",
                    "critical"
                )
            
            # Verificar pontualidade nos pagamentos
            paid_payments = student_payments[student_payments['status'] == 'paid']
            if not paid_payments.empty and 'payment_date' in paid_payments.columns and 'due_date' in paid_payments.columns:
                # Remover NAs
                paid_with_dates = paid_payments.dropna(subset=['payment_date', 'due_date'])
                
                if not paid_with_dates.empty:
                    # Calcular pagamentos em dia
                    on_time_payments = paid_with_dates[paid_with_dates['payment_date'] <= paid_with_dates['due_date']]
                    on_time_rate = len(on_time_payments) / len(paid_with_dates) * 100
                    
                    if on_time_rate > 90:
                        render_insight_card(
                            "Excelente Pontualidade",
                            f"O aluno tem {on_time_rate:.1f}% dos pagamentos realizados em dia, demonstrando excelente comprometimento financeiro.",
                            "success"
                        )
                    elif on_time_rate < 60:
                        render_insight_card(
                            "Baixa Pontualidade",
                            f"O aluno tem apenas {on_time_rate:.1f}% dos pagamentos realizados em dia. Considere um acompanhamento mais próximo.",
                            "warning"
                        )
    
    # Análise de estágios do aluno
    if internships_df is not None and not internships_df.empty:
        # Calcular horas de estágio
        student_hours = get_student_internship_hours(internships_df, selected_student)
        
        st.metric("Total de Horas de Estágio", f"{student_hours:.1f}h")
        
        # Obter tópicos de estágio
        student_topics = get_student_internship_topics(internships_df, selected_student)
        
        if student_topics:
            st.subheader("Temas de Estágio Realizados")
            
            # Criar dataframe para exibição
            topics_df = pd.DataFrame({'Tema': student_topics})
            topics_count = topics_df['Tema'].value_counts().reset_index()
            topics_count.columns = ['Tema', 'Frequência']
            
            fig = px.bar(
                topics_count,
                x='Tema',
                y='Frequência',
                title='Temas de Estágio Realizados',
                color='Frequência',
                color_continuous_scale=px.colors.sequential.Viridis
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Comparar com média da turma
            if len(students_df) > 0:
                avg_hours = internships_df['duration_hours'].sum() / len(students_df)
                
                if student_hours > avg_hours * 1.5:
                    render_insight_card(
                        "Destaque em Horas de Estágio",
                        f"Com {student_hours:.1f} horas, este aluno está bem acima da média da turma de {avg_hours:.1f} horas, demonstrando alto engajamento.",
                        "success"
                    )
                elif student_hours < avg_hours * 0.5 and student_hours > 0:
                    render_insight_card(
                        "Abaixo da Média em Horas de Estágio",
                        f"Com {student_hours:.1f} horas, este aluno está abaixo da média da turma de {avg_hours:.1f} horas. Incentive maior participação.",
                        "warning"
                    )
                elif student_hours == 0:
                    render_insight_card(
                        "Sem Registro de Estágios",
                        "Este aluno não possui nenhum registro de participação em estágios. Entre em contato para entender o motivo.",
                        "critical"
                    )
    
    # Recomendações personalizadas
    st.subheader("Recomendações Personalizadas")
    
    # Gerar recomendações baseadas na análise
    recomendacoes = []
    
    # Verificar pagamentos
    if payments_df is not None and not payments_df.empty:
        student_payments = payments_df[payments_df['phone'] == selected_student]
        
        if not student_payments.empty:
            # Verificar pagamentos atrasados
            overdue_count = len(student_payments[student_payments['status'] == 'overdue'])
            pending_count = len(student_payments[student_payments['status'] == 'pending'])
            
            if overdue_count > 0:
                recomendacoes.append(f"Entre em contato para regularizar os {overdue_count} pagamentos em atraso.")
            
            # Verificar pontualidade
            paid_payments = student_payments[student_payments['status'] == 'paid']
            if not paid_payments.empty and 'payment_date' in paid_payments.columns and 'due_date' in paid_payments.columns:
                paid_with_dates = paid_payments.dropna(subset=['payment_date', 'due_date'])
                
                if not paid_with_dates.empty:
                    on_time_payments = paid_with_dates[paid_with_dates['payment_date'] <= paid_with_dates['due_date']]
                    on_time_rate = len(on_time_payments) / len(paid_with_dates) * 100
                    
                    if on_time_rate < 70:
                        recomendacoes.append("Envie lembretes de pagamento com alguns dias de antecedência.")
    
    # Verificar estágios
    if internships_df is not None and not internships_df.empty:
        student_hours = get_student_internship_hours(internships_df, selected_student)
        avg_hours = internships_df['duration_hours'].sum() / len(students_df) if len(students_df) > 0 else 0
        
        if student_hours == 0:
            recomendacoes.append("Incentive a participação em estágios, explicando os benefícios para o desenvolvimento profissional.")
        elif student_hours < avg_hours * 0.5:
            recomendacoes.append("Ofereça temas de estágio mais alinhados com os interesses do aluno para aumentar o engajamento.")
        
        # Verificar diversidade de temas
        student_topics = get_student_internship_topics(internships_df, selected_student)
        if len(student_topics) <= 2 and student_hours > 0:
            recomendacoes.append("Sugira temas variados de estágio para ampliar o conhecimento em diferentes áreas de LIBRAS.")
    
    # Status do aluno
    if student['status'] == 'active':
        # Verificar tempo de matrícula
        enrollment_date = pd.to_datetime(student['enrollment_date']) if 'enrollment_date' in student.index and pd.notna(student['enrollment_date']) else None
        
        if enrollment_date:
            days_enrolled = (datetime.now().date() - enrollment_date.date()).days
            
            # Verificar se as variáveis necessárias estão definidas
            has_student_hours = 'student_hours' in locals() or 'student_hours' in globals()
            has_avg_hours = 'avg_hours' in locals() or 'avg_hours' in globals()
            
            if days_enrolled > 180:
                if (has_student_hours and has_avg_hours and student_hours < avg_hours * 0.3) or not recomendacoes:
                    recomendacoes.append("Realize uma pesquisa de satisfação para entender melhor as necessidades do aluno.")
    
    # Exibir recomendações
    if recomendacoes:
        for rec in recomendacoes:
            render_insight_card("Recomendação", rec, "info")
    else:
        render_insight_card(
            "Aluno com Bom Desempenho",
            "Este aluno está com todos os indicadores positivos! Continue acompanhando para manter o bom desempenho.",
            "success"
        )

st.header("Insights Gerais e Recomendações")

# Insights sobre a saúde financeira do curso
if payments_df is not None and not payments_df.empty:
    today = datetime.now().date()
    current_month = today.month
    current_year = today.year
    
    # Pagamentos do mês atual
    current_month_payments = payments_df[
        (payments_df['month_reference'] == current_month) &
        (payments_df['year_reference'] == current_year)
    ]
    
    if not current_month_payments.empty:
        # Taxa de pagamentos realizados
        payment_rate = len(current_month_payments[current_month_payments['status'] == 'paid']) / len(current_month_payments) * 100
        
        if payment_rate < 60:
            render_insight_card(
                "Atenção: Baixa Taxa de Pagamentos no Mês Atual",
                f"Apenas {payment_rate:.1f}% dos pagamentos do mês atual foram realizados. Considere enviar lembretes adicionais.",
                "warning"
            )

# Insights sobre engajamento nos estágios
if internships_df is not None and not internships_df.empty and students_df is not None and not students_df.empty:
    # Alunos sem participação em estágios
    active_students = get_active_students(students_df)
    
    if not active_students.empty:
        students_with_internships = set()
        
        for _, internship in internships_df.iterrows():
            students_str = str(internship['students'])
            student_phones = students_str.split(',')
            for phone in student_phones:
                if phone.strip():
                    students_with_internships.add(phone.strip())
        
        active_phones = set(active_students['phone'].astype(str))
        students_without_internships = active_phones - students_with_internships
        
        if students_without_internships:
            percentage = len(students_without_internships) / len(active_phones) * 100
            
            if percentage > 30:
                render_insight_card(
                    "Alunos Sem Participação em Estágios",
                    f"{len(students_without_internships)} alunos ativos ({percentage:.1f}%) não participaram de nenhum estágio. Considere um programa de incentivo.",
                    "critical"
                )

# Tendências de crescimento/declínio
if 'enrollment_date' in students_df.columns:
    students_df['enrollment_date'] = pd.to_datetime(students_df['enrollment_date'])
    
    # Últimos 6 meses
    six_months_ago = datetime.now() - timedelta(days=180)
    recent_students = students_df[students_df['enrollment_date'] >= six_months_ago]
    
    # Cancelados nos últimos 6 meses
    if 'cancellation_date' in students_df.columns:
        students_df['cancellation_date'] = pd.to_datetime(students_df['cancellation_date'])
        recent_cancellations = students_df[
            (students_df['status'] == 'canceled') &
            (students_df['cancellation_date'] >= six_months_ago)
        ]
        
        # Calcular taxa de crescimento líquido
        net_growth = len(recent_students) - len(recent_cancellations)
        
        if net_growth < 0:
            render_insight_card(
                "Alerta: Declínio no Número de Alunos",
                f"Nos últimos 6 meses, houve um declínio líquido de {abs(net_growth)} alunos. Revise as estratégias de retenção e captação.",
                "critical"
            )
        elif net_growth == 0:
            render_insight_card(
                "Crescimento Estagnado",
                "Nos últimos 6 meses, o número de matrículas igualou o número de cancelamentos. Considere novas estratégias de marketing.",
                "warning"
            )
        else:
            render_insight_card(
                "Crescimento Positivo",
                f"Nos últimos 6 meses, houve um crescimento líquido de {net_growth} alunos. Continue com as estratégias atuais.",
                "success"
            )
