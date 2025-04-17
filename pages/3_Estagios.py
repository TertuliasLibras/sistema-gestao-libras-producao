import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from utils import (
    load_students_data, 
    load_internships_data,
    save_internships_data,
    format_phone,
    get_active_students,
    get_student_internship_hours
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
    st.title("Gerenciamento de Estágios")

# Load data
students_df = load_students_data()
internships_df = load_internships_data()

# Create tabs for different operations
tab1, tab2, tab3 = st.tabs(["Registrar Estágio", "Listar Estágios", "Horas por Aluno"])

with tab1:
    st.subheader("Registrar Novo Estágio")
    
    if students_df is not None and not students_df.empty:
        # Get active students
        active_students = get_active_students(students_df)
        
        if not active_students.empty:
            with st.form("internship_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    date = st.date_input("Data do Estágio", datetime.now())
                    
                    duration_hours = st.number_input(
                        "Duração (horas)",
                        min_value=0.5,
                        max_value=10.0,
                        value=2.0,
                        step=0.5
                    )
                
                with col2:
                    topic = st.text_input("Tema do Estágio")
                
                # Multi-select for students who participated
                student_options = active_students.apply(lambda x: f"{format_phone(x['phone'])} - {x['name']}", axis=1).tolist()
                student_values = active_students['phone'].tolist()
                
                selected_students = st.multiselect(
                    "Alunos Participantes",
                    options=student_values,
                    format_func=lambda x: f"{format_phone(x)} - {active_students[active_students['phone'] == x]['name'].values[0]}"
                )
                
                notes = st.text_area("Observações", height=80)
                
                submitted = st.form_submit_button("Registrar Estágio")
                
                if submitted:
                    if not topic:
                        st.error("O tema do estágio é obrigatório!")
                    elif not selected_students:
                        st.error("Selecione pelo menos um aluno participante!")
                    else:
                        # Create new internship record
                        new_internship = {
                            'date': date.strftime('%Y-%m-%d'),
                            'topic': topic,
                            'duration_hours': duration_hours,
                            'students': ','.join([str(student) for student in selected_students]),
                            'notes': notes
                        }
                        
                        # Add to dataframe
                        if internships_df is None or internships_df.empty:
                            internships_df = pd.DataFrame([new_internship])
                        else:
                            internships_df = pd.concat([internships_df, pd.DataFrame([new_internship])], ignore_index=True)
                        
                        # Save data
                        save_internships_data(internships_df)
                        
                        st.success("Estágio registrado com sucesso!")
        else:
            st.warning("Não há alunos ativos cadastrados para registrar estágios.")
    else:
        st.info("Não há alunos cadastrados ainda.")

with tab2:
    st.subheader("Lista de Estágios")
    
    # Filter options
    st.write("Filtros:")
    col1, col2 = st.columns(2)
    
    with col1:
        date_range = st.date_input(
            "Período",
            value=(
                datetime.now() - timedelta(days=30),
                datetime.now()
            ),
            help="Selecione o período para filtrar os estágios"
        )
    
    with col2:
        topic_filter = st.text_input("Filtrar por Tema")
    
    if internships_df is not None and not internships_df.empty:
        # Convert date to datetime
        internships_df['date'] = pd.to_datetime(internships_df['date'])
        
        # Apply filters
        filtered_df = internships_df.copy()
        
        # Date range filter
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = filtered_df[
                (filtered_df['date'].dt.date >= start_date) &
                (filtered_df['date'].dt.date <= end_date)
            ]
        
        # Topic filter
        if topic_filter:
            filtered_df = filtered_df[
                filtered_df['topic'].str.lower().str.contains(topic_filter.lower(), na=False)
            ]
        
        # Display dataframe
        if not filtered_df.empty:
            # Create a copy with formatted data for display
            display_df = filtered_df.copy()
            
            # Format date
            display_df['date'] = display_df['date'].dt.strftime('%d/%m/%Y')
            
            # Format students for display
            def format_students(students_str):
                if not students_str or pd.isna(students_str):
                    return ""
                
                # Converter para string se não for string
                if not isinstance(students_str, str):
                    students_str = str(students_str)
                
                student_phones = students_str.split(',')
                student_names = []
                
                for phone in student_phones:
                    if phone.strip() and students_df is not None and not students_df.empty:
                        student = students_df[students_df['phone'] == phone.strip()]
                        if not student.empty:
                            name = student['name'].values[0]
                            student_names.append(name)
                
                return ", ".join(student_names)
            
            display_df['student_names'] = display_df['students'].apply(format_students)
            
            # Count students
            display_df['student_count'] = display_df['students'].apply(
                lambda x: len(x.split(',')) if not pd.isna(x) and x.strip() else 0
            )
            
            # Display dataframe
            st.dataframe(
                display_df[['date', 'topic', 'duration_hours', 'student_count', 'student_names']],
                use_container_width=True,
                column_config={
                    'date': 'Data',
                    'topic': 'Tema',
                    'duration_hours': 'Duração (horas)',
                    'student_count': 'Nº de Alunos',
                    'student_names': 'Alunos Participantes'
                }
            )
            
            st.info(f"Total de estágios: {len(filtered_df)}")
            
            # Calculate total hours
            total_hours = filtered_df['duration_hours'].sum()
            st.metric("Total de Horas de Estágio", f"{total_hours:.1f}h")
            
            # Export option
            if st.button("Exportar Lista (CSV)"):
                export_df = filtered_df.copy()
                # Format date for export
                export_df['date'] = export_df['date'].dt.strftime('%d/%m/%Y')
                # Convert to CSV
                csv = export_df.to_csv(index=False).encode('utf-8')
                
                # Create download button
                st.download_button(
                    "Baixar CSV",
                    csv,
                    "estagios.csv",
                    "text/csv",
                    key='download-csv'
                )
        else:
            st.warning("Nenhum estágio encontrado com os filtros selecionados.")
    else:
        st.info("Não há estágios registrados ainda.")

with tab3:
    st.subheader("Horas de Estágio por Aluno")
    
    if students_df is not None and not students_df.empty and internships_df is not None and not internships_df.empty:
        # Calculate hours per student
        student_hours = []
        
        for _, student in students_df.iterrows():
            hours = get_student_internship_hours(internships_df, student['phone'])
            
            # Get all topics for this student
            student_topics = []
            
            for _, internship in internships_df.iterrows():
                students_in_internship = str(internship['students']).split(',')
                students_in_internship = [s.strip() for s in students_in_internship]
                
                if student['phone'] in students_in_internship:
                    student_topics.append(internship['topic'])
            
            # Remove duplicates
            unique_topics = list(set(student_topics))
            
            student_hours.append({
                'phone': student['phone'],
                'name': student['name'],
                'status': student['status'],
                'total_hours': hours,
                'topic_count': len(unique_topics),
                'topics': ", ".join(unique_topics[:5]) + ("..." if len(unique_topics) > 5 else "")
            })
        
        # Create dataframe
        hours_df = pd.DataFrame(student_hours)
        
        # Add filter for active/inactive students
        status_filter = st.radio(
            "Status do Aluno",
            options=["Todos", "Ativos", "Cancelados"],
            horizontal=True,
            index=1
        )
        
        # Apply filter
        if status_filter == "Ativos":
            hours_df = hours_df[hours_df['status'] == 'active']
        elif status_filter == "Cancelados":
            hours_df = hours_df[hours_df['status'] == 'canceled']
        
        # Sort by total hours
        hours_df = hours_df.sort_values('total_hours', ascending=False)
        
        # Format phone
        hours_df['phone'] = hours_df['phone'].apply(format_phone)
        
        # Format status
        hours_df['status'] = hours_df['status'].map({
            'active': 'Ativo',
            'canceled': 'Cancelado'
        })
        
        # Display dataframe
        st.dataframe(
            hours_df[['name', 'phone', 'status', 'total_hours', 'topic_count', 'topics']],
            use_container_width=True,
            column_config={
                'name': 'Nome',
                'phone': 'Telefone',
                'status': 'Status',
                'total_hours': 'Total de Horas',
                'topic_count': 'Temas Diferentes',
                'topics': 'Temas Realizados'
            }
        )
        
        # Calculate averages
        avg_hours = hours_df[hours_df['status'] == 'Ativo']['total_hours'].mean()
        max_hours = hours_df['total_hours'].max()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Média de Horas (Alunos Ativos)", f"{avg_hours:.1f}h" if not np.isnan(avg_hours) else "0h")
        
        with col2:
            st.metric("Maior Quantidade de Horas", f"{max_hours:.1f}h" if not np.isnan(max_hours) else "0h")
    else:
        st.info("Não há dados suficientes para calcular as horas de estágio por aluno.")
