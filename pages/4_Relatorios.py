import streamlit as st
import pandas as pd
import plotly.express as px
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
            load_internships_data,
            format_currency,
            get_active_students,
            get_overdue_payments,
            get_student_internship_hours
        )
    except ImportError as e:
        st.error(f"Erro ao importar módulos: {e}")
        st.info("Esta funcionalidade requer conexão com o banco de dados.")
        st.stop()
    
    st.title("Relatórios")
    
    # Carregar dados
    students_df = load_students_data()
    payments_df = load_payments_data()
    internships_df = load_internships_data()
    
    # Verificar se há dados
    if students_df.empty:
        st.warning("Não há alunos cadastrados para gerar relatórios.")
        st.stop()
    
    # Criar abas para diferentes relatórios
    tab1, tab2, tab3, tab4 = st.tabs([
        "Financeiro", 
        "Alunos", 
        "Estágios",
        "Pagamentos Atrasados"
    ])
    
    # Aba Relatório Financeiro
    with tab1:
        st.subheader("Relatório Financeiro")
        
        # Seleção de período
        col1, col2 = st.columns(2)
        with col1:
            # Filtro de mês
            current_month = datetime.now().month
            month_filter = st.selectbox(
                "Mês:",
                list(range(1, 13)),
                index=current_month - 1,
                format_func=lambda x: calendar.month_name[x],
                key="finance_month"
            )
        with col2:
            # Filtro de ano
            current_year = datetime.now().year
            year_filter = st.selectbox(
                "Ano:",
                list(range(current_year - 2, current_year + 3)),
                index=2,
                key="finance_year"
            )
        
        # Calcular totais
        if not payments_df.empty and 'month' in payments_df.columns and 'year' in payments_df.columns:
            # Filtrar pagamentos do período
            period_payments = payments_df[
                (payments_df['month'] == month_filter) &
                (payments_df['year'] == year_filter)
            ]
            
            # Calcular métricas
            total_expected = 0
            total_received = 0
            total_pending = 0
            total_overdue = 0
            
            if not period_payments.empty and 'amount' in period_payments.columns and 'status' in period_payments.columns:
                total_expected = period_payments['amount'].sum()
                total_received = period_payments[period_payments['status'] == 'paid']['amount'].sum()
                
                # Pagamentos pendentes
                pending_payments = period_payments[period_payments['status'] == 'pending']
                total_pending = pending_payments['amount'].sum()
                
                # Pagamentos atrasados
                today = datetime.now().date()
                overdue_mask = (
                    (pending_payments['status'] == 'pending') &
                    (pd.to_datetime(pending_payments['due_date']).dt.date < today)
                )
                
                total_overdue = pending_payments[overdue_mask]['amount'].sum() if 'due_date' in pending_payments.columns else 0
            
            # Exibir métricas
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Esperado", format_currency(total_expected))
                st.metric("Total Recebido", format_currency(total_received))
            with col2:
                st.metric("Total Pendente", format_currency(total_pending))
                st.metric("Total Atrasado", format_currency(total_overdue))
            
            # Gráfico de pizza com status dos pagamentos
            if not period_payments.empty:
                # Preparar dados para o gráfico
                status_counts = {
                    "Recebido": total_received,
                    "Pendente": total_pending - total_overdue,
                    "Atrasado": total_overdue
                }
                
                # Remover zeros
                status_counts = {k: v for k, v in status_counts.items() if v > 0}
                
                if status_counts:
                    status_df = pd.DataFrame({
                        "Status": list(status_counts.keys()),
                        "Valor": list(status_counts.values())
                    })
                    
                    fig = px.pie(
                        status_df, 
                        values="Valor", 
                        names="Status",
                        color="Status",
                        color_discrete_map={
                            "Recebido": "#28a745",
                            "Pendente": "#007bff",
                            "Atrasado": "#dc3545"
                        },
                        title=f"Distribuição de Pagamentos - {calendar.month_name[month_filter]}/{year_filter}"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            
            # Gráfico de barras com receita por mês (últimos 6 meses)
            st.subheader("Receita por Mês (Últimos 6 meses)")
            
            # Calcular meses anteriores
            current_date = datetime(year_filter, month_filter, 1)
            months = []
            
            for i in range(5, -1, -1):
                previous_date = current_date - timedelta(days=i*30)
                months.append((previous_date.month, previous_date.year))
            
            # Calcular receita para cada mês
            monthly_revenue = []
            
            for month, year in months:
                month_payments = payments_df[
                    (payments_df['month'] == month) &
                    (payments_df['year'] == year) &
                    (payments_df['status'] == 'paid')
                ] if not payments_df.empty else pd.DataFrame()
                
                revenue = month_payments['amount'].sum() if not month_payments.empty and 'amount' in month_payments.columns else 0
                
                monthly_revenue.append({
                    "Mês": f"{calendar.month_name[month][:3]}/{year}",
                    "Receita": revenue,
                    "order": f"{year}-{month:02d}"  # Para ordenação correta
                })
            
            if monthly_revenue:
                revenue_df = pd.DataFrame(monthly_revenue)
                revenue_df = revenue_df.sort_values("order")
                
                fig = px.bar(
                    revenue_df, 
                    x="Mês", 
                    y="Receita",
                    title="Receita Mensal",
                    labels={"Receita": "Valor (R$)"},
                    text_auto='.2s'
                )
                
                # Formatar valores no eixo Y
                fig.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.2f")
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Não há dados de pagamentos disponíveis para gerar o relatório financeiro.")
    
    # Aba Relatório de Alunos
    with tab2:
        st.subheader("Relatório de Alunos")
        
        # Calcular métricas
        total_students = len(students_df)
        
        # Alunos ativos e cancelados
        active_students = get_active_students(students_df)
        active_count = len(active_students) if not active_students.empty else 0
        
        # Cancelados
        canceled_count = 0
        if 'status' in students_df.columns:
            canceled_count = len(students_df[students_df['status'] == 'canceled'])
        
        # Exibir métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Alunos", total_students)
        with col2:
            st.metric("Alunos Ativos", active_count)
        with col3:
            st.metric("Alunos Cancelados", canceled_count)
        
        # Distribuição por tipo de curso
        if 'course_type' in students_df.columns:
            course_counts = students_df['course_type'].value_counts().reset_index()
            course_counts.columns = ['Tipo de Curso', 'Quantidade']
            
            # Gráfico de pizza
            fig = px.pie(
                course_counts, 
                values="Quantidade", 
                names="Tipo de Curso",
                title="Distribuição por Tipo de Curso"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Origem dos cadastros
        if 'registration_origin' in students_df.columns:
            origin_counts = students_df['registration_origin'].value_counts().reset_index()
            origin_counts.columns = ['Origem', 'Quantidade']
            
            # Limitar a 10 origens mais comuns
            if len(origin_counts) > 10:
                other_count = origin_counts.iloc[10:]['Quantidade'].sum()
                origin_counts = origin_counts.iloc[:10]
                origin_counts.loc[len(origin_counts)] = ['Outros', other_count]
            
            # Gráfico de barras
            fig = px.bar(
                origin_counts, 
                x="Origem", 
                y="Quantidade",
                title="Origem dos Cadastros",
                text_auto=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Matrículas por mês
        if 'enrollment_date' in students_df.columns:
            # Converter para datetime
            students_df['enrollment_date'] = pd.to_datetime(students_df['enrollment_date'])
            
            # Extrair mês e ano
            students_df['enrollment_month'] = students_df['enrollment_date'].dt.month
            students_df['enrollment_year'] = students_df['enrollment_date'].dt.year
            
            # Agrupar por mês e ano
            enrollments = students_df.groupby(['enrollment_year', 'enrollment_month']).size().reset_index()
            enrollments.columns = ['Ano', 'Mês', 'Quantidade']
            
            # Adicionar campo para ordenação e exibição
            enrollments['mes_ano'] = enrollments.apply(lambda x: f"{calendar.month_name[x['Mês']][:3]}/{x['Ano']}", axis=1)
            enrollments['order'] = enrollments.apply(lambda x: f"{x['Ano']}-{x['Mês']:02d}", axis=1)
            
            # Ordenar
            enrollments = enrollments.sort_values('order')
            
            # Limitar aos últimos 12 meses
            if len(enrollments) > 12:
                enrollments = enrollments.iloc[-12:]
            
            # Gráfico de linha
            fig = px.line(
                enrollments, 
                x="mes_ano", 
                y="Quantidade",
                title="Matrículas por Mês",
                markers=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Aba Relatório de Estágios
    with tab3:
        st.subheader("Relatório de Estágios")
        
        if not internships_df.empty:
            # Total de horas
            total_hours = internships_df['hours'].sum() if 'hours' in internships_df.columns else 0
            
            # Média de horas por aluno
            if 'phone' in internships_df.columns and 'hours' in internships_df.columns:
                student_hours = internships_df.groupby('phone')['hours'].sum()
                avg_hours = student_hours.mean()
                max_hours = student_hours.max()
                min_hours = student_hours.min() if len(student_hours) > 0 else 0
            else:
                avg_hours = 0
                max_hours = 0
                min_hours = 0
            
            # Exibir métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Horas de Estágio", f"{total_hours:.1f}h")
            with col2:
                st.metric("Média por Aluno", f"{avg_hours:.1f}h")
            with col3:
                st.metric("Máximo por Aluno", f"{max_hours:.1f}h")
            
            # Top alunos com mais horas
            if not students_df.empty and 'phone' in students_df.columns and 'name' in students_df.columns:
                # Juntar dados
                student_hours_df = pd.DataFrame({'phone': student_hours.index, 'hours': student_hours.values})
                student_hours_df = pd.merge(student_hours_df, students_df[['phone', 'name']], on='phone', how='left')
                
                # Ordenar
                student_hours_df = student_hours_df.sort_values('hours', ascending=False)
                
                # Mostrar top 10
                st.subheader("Top 10 Alunos com Mais Horas de Estágio")
                top_students = student_hours_df.head(10)
                
                for i, (_, row) in enumerate(top_students.iterrows(), 1):
                    st.info(f"{i}. {row['name']} - {row['hours']:.1f}h")
                
                # Gráfico de barras
                fig = px.bar(
                    top_students,
                    x="name",
                    y="hours",
                    title="Top 10 Alunos por Horas de Estágio",
                    labels={"name": "Aluno", "hours": "Horas"},
                    text_auto='.1f'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Distribuição por tópico
            if 'topic' in internships_df.columns and 'hours' in internships_df.columns:
                topic_hours = internships_df.groupby('topic')['hours'].sum().reset_index()
                topic_hours = topic_hours.sort_values('hours', ascending=False)
                
                # Gráfico de pizza
                fig = px.pie(
                    topic_hours,
                    values="hours",
                    names="topic",
                    title="Distribuição de Horas por Tópico"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Estágios por mês
            if 'date' in internships_df.columns:
                # Converter para datetime
                internships_df['date'] = pd.to_datetime(internships_df['date'])
                
                # Extrair mês e ano
                internships_df['month'] = internships_df['date'].dt.month
                internships_df['year'] = internships_df['date'].dt.year
                
                # Agrupar por mês e ano
                monthly_internships = internships_df.groupby(['year', 'month'])['hours'].sum().reset_index()
                
                # Adicionar campo para ordenação e exibição
                monthly_internships['mes_ano'] = monthly_internships.apply(lambda x: f"{calendar.month_name[x['month']][:3]}/{x['year']}", axis=1)
                monthly_internships['order'] = monthly_internships.apply(lambda x: f"{x['year']}-{x['month']:02d}", axis=1)
                
                # Ordenar
                monthly_internships = monthly_internships.sort_values('order')
                
                # Limitar aos últimos 12 meses
                if len(monthly_internships) > 12:
                    monthly_internships = monthly_internships.iloc[-12:]
                
                # Gráfico de linha
                fig = px.line(
                    monthly_internships,
                    x="mes_ano",
                    y="hours",
                    title="Horas de Estágio por Mês",
                    labels={"mes_ano": "Mês/Ano", "hours": "Horas"},
                    markers=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Não há dados de estágios disponíveis para gerar relatórios.")
    
    # Aba Pagamentos Atrasados
    with tab4:
        st.subheader("Relatório de Pagamentos Atrasados")
        
        # Obter pagamentos atrasados
        overdue_payments = get_overdue_payments(students_df, payments_df)
        
        if not overdue_payments.empty:
            # Contar alunos com pagamentos atrasados
            overdue_count = overdue_payments['phone'].nunique() if 'phone' in overdue_payments.columns else 0
            
            # Calcular total atrasado
            total_overdue = overdue_payments['amount'].sum() if 'amount' in overdue_payments.columns else 0
            
            # Calcular média de dias de atraso
            avg_days_overdue = overdue_payments['days_overdue'].mean() if 'days_overdue' in overdue_payments.columns else 0
            
            # Exibir métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Alunos com Atraso", overdue_count)
            with col2:
                st.metric("Total em Atraso", format_currency(total_overdue))
            with col3:
                st.metric("Média de Dias em Atraso", f"{avg_days_overdue:.1f} dias")
            
            # Tabela de pagamentos atrasados
            if 'name' in overdue_payments.columns and 'amount' in overdue_payments.columns and 'days_overdue' in overdue_payments.columns:
                # Agrupar por aluno
                student_overdue = overdue_payments.groupby('phone').agg({
                    'name': 'first',
                    'amount': 'sum',
                    'days_overdue': 'mean'
                }).reset_index()
                
                # Ordenar por dias de atraso
                student_overdue = student_overdue.sort_values('days_overdue', ascending=False)
                
                # Formatar valores
                student_overdue['amount'] = student_overdue['amount'].apply(format_currency)
                student_overdue['days_overdue'] = student_overdue['days_overdue'].apply(lambda x: f"{x:.0f} dias")
                
                # Renomear colunas
                student_overdue.columns = ['Telefone', 'Nome', 'Valor Total', 'Dias de Atraso']
                
                # Exibir tabela
                st.dataframe(student_overdue, use_container_width=True)
            
            # Gráfico de barras com valores atrasados por aluno
            if 'name' in overdue_payments.columns and 'amount' in overdue_payments.columns:
                student_amount = overdue_payments.groupby('name')['amount'].sum().reset_index()
                student_amount = student_amount.sort_values('amount', ascending=False)
                
                # Limitar a 10 alunos
                if len(student_amount) > 10:
                    student_amount = student_amount.head(10)
                
                # Gráfico
                fig = px.bar(
                    student_amount,
                    x="name",
                    y="amount",
                    title="Top Alunos com Maior Valor em Atraso",
                    labels={"name": "Aluno", "amount": "Valor em Atraso"},
                    text_auto='.2s'
                )
                
                # Formatar valores no eixo Y
                fig.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.2f")
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Distribuição por faixa de atraso
            if 'days_overdue' in overdue_payments.columns:
                # Definir faixas de atraso
                bins = [0, 7, 15, 30, 60, 90, float('inf')]
                labels = ['Até 7 dias', '8-15 dias', '16-30 dias', '31-60 dias', '61-90 dias', '> 90 dias']
                
                # Categorizar
                overdue_payments['atraso_categoria'] = pd.cut(
                    overdue_payments['days_overdue'],
                    bins=bins,
                    labels=labels,
                    right=False
                )
                
                # Contar por categoria
                category_counts = overdue_payments['atraso_categoria'].value_counts().reset_index()
                category_counts.columns = ['Categoria', 'Quantidade']
                
                # Ordenar por categoria
                order_map = {label: i for i, label in enumerate(labels)}
                category_counts['order'] = category_counts['Categoria'].map(order_map)
                category_counts = category_counts.sort_values('order')
                
                # Gráfico
                fig = px.bar(
                    category_counts,
                    x="Categoria",
                    y="Quantidade",
                    title="Distribuição por Tempo de Atraso",
                    text_auto=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("Não há pagamentos atrasados no momento.")
