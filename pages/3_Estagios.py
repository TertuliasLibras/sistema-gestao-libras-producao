import streamlit as st
import pandas as pd
from datetime import datetime
import os
from utils import (
    load_students_data, 
    load_internships_data,
    save_internships_data,
    format_phone,
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
    st.title("Gerenciamento de Estágios")

# Load data
students_df = load_students_data()
internships_df = load_internships_data()

# Create tabs for different operations
tab1, tab2, tab3 = st.tabs(["Registrar Estágio", "Listar Estágios", "Editar Estágios"])

# Helper function to format student list display
def format_students(students_str):
    if not students_str:
        return ""
    
    students_list = students_str.split(',')
    if len(students_list) > 3:
        return f"{', '.join(students_list[:3])} (+{len(students_list) - 3})"
    return students_str

with tab1:
    st.subheader("Registrar Novo Estágio")
    
    if students_df is not None and not students_df.empty:
        # Filter for active students only
        active_students = students_df[students_df['status'] == 'active']
        
        if not active_students.empty:
            with st.form("internship_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Allow selecting multiple students for group internships
                    selected_students = st.multiselect(
                        "Selecione os alunos participantes:",
                        options=active_students['phone'].tolist(),
                        format_func=lambda x: f"{format_phone(x)} - {active_students[active_students['phone'] == x]['name'].values[0]}"
                    )
                    
                    internship_date = st.date_input("Data do Estágio", datetime.now())
                    hours = st.number_input("Horas de Estágio", min_value=1, value=4, step=1)
                
                with col2:
                    topic = st.text_input("Tema/Assunto", help="O assunto principal abordado neste estágio")
                    location = st.text_input("Local do Estágio", help="Onde o estágio foi realizado")
                    supervisor = st.text_input("Supervisor", help="Nome do supervisor responsável")
                    
                notes = st.text_area("Observações", height=100)
                
                submitted = st.form_submit_button("Registrar Estágio")
                
                if submitted:
                    if not selected_students:
                        st.error("Por favor, selecione pelo menos um aluno.")
                    elif not topic:
                        st.error("O tema do estágio é obrigatório.")
                    else:
                        # Create new internship record
                        internship_id = f"INT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        
                        # Create a comma-separated list of student phones
                        students_str = ','.join(selected_students)
                        
                        new_internship = {
                            'internship_id': internship_id,
                            'students': students_str,
                            'date': internship_date.strftime('%Y-%m-%d'),
                            'hours': hours,
                            'topic': topic,
                            'location': location,
                            'supervisor': supervisor,
                            'notes': notes,
                            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # Add to dataframe
                        if internships_df is None or internships_df.empty:
                            internships_df = pd.DataFrame([new_internship])
                        else:
                            internships_df = pd.concat([internships_df, pd.DataFrame([new_internship])], ignore_index=True)
                        
                        # Save data
                        save_internships_data(internships_df)
                        
                        st.success(f"Estágio registrado com sucesso! ID: {internship_id}")
        else:
            st.warning("Não há alunos ativos no momento.")
    else:
        st.info("Não há alunos cadastrados ainda.")

with tab2:
    st.subheader("Lista de Estágios")
    
    # Filter options
    st.write("Filtros:")
    col1, col2 = st.columns(2)
    
    with col1:
        date_range = st.date_input(
            "Período (Início e Fim)",
            value=[
                datetime.now().replace(day=1),  # First day of current month
                datetime.now()  # Today
            ],
            key="date_range_filter"
        )
    
    with col2:
        if students_df is not None and not students_df.empty:
            student_options = ["Todos"] + students_df['phone'].tolist()
            
            student_filter = st.selectbox(
                "Filtrar por Aluno",
                options=student_options,
                format_func=lambda x: "Todos" if x == "Todos" else f"{format_phone(x)} - {students_df[students_df['phone'] == x]['name'].values[0]}"
            )
        else:
            student_filter = "Todos"
    
    if internships_df is not None and not internships_df.empty:
        # Apply filters
        filtered_df = internships_df.copy()
        
        # Date filter
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = filtered_df[
                (pd.to_datetime(filtered_df['date']) >= pd.to_datetime(start_date)) & 
                (pd.to_datetime(filtered_df['date']) <= pd.to_datetime(end_date))
            ]
        
        # Student filter
        if student_filter and student_filter != "Todos":
            # Filter internships where the selected student is in the comma-separated list
            filtered_df = filtered_df[filtered_df['students'].str.contains(student_filter, na=False)]
        
        # Display dataframe if not empty
        if not filtered_df.empty:
            # Create a copy with formatted data for display
            display_df = filtered_df.copy()
            
            # Format dates to Brazilian format (dd/mm/yyyy)
            display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%d/%m/%Y')
            
            # Format student list with names instead of phone numbers
            if students_df is not None and not students_df.empty:
                # Create a map of phone to name
                phone_to_name = dict(zip(students_df['phone'], students_df['name']))
                
                # Function to convert phone list to name list
                def phone_list_to_names(phones_str):
                    if not phones_str:
                        return ""
                    
                    phones = phones_str.split(',')
                    names = [phone_to_name.get(phone, phone) for phone in phones]
                    
                    # Truncate if too many names
                    if len(names) > 3:
                        return f"{', '.join(names[:3])} (+{len(names) - 3})"
                    return ', '.join(names)
                
                display_df['students_display'] = display_df['students'].apply(phone_list_to_names)
            else:
                display_df['students_display'] = display_df['students'].apply(format_students)
            
            # Select and reorder columns for display
            columns_to_display = [
                'internship_id', 'date', 'students_display', 'hours', 
                'topic', 'location', 'supervisor'
            ]
            
            # Remove columns that might not exist in older data
            columns_to_display = [col for col in columns_to_display if col in display_df.columns]
            
            # Custom column labels
            column_labels = {
                'internship_id': 'ID',
                'date': 'Data',
                'students_display': 'Alunos',
                'hours': 'Horas',
                'topic': 'Tema',
                'location': 'Local',
                'supervisor': 'Supervisor'
            }
            
            # Display the dataframe
            st.dataframe(
                display_df[columns_to_display], 
                use_container_width=True,
                column_config={col: column_labels.get(col, col) for col in columns_to_display}
            )
            
            # Calculate summary
            total_internships = len(filtered_df)
            total_hours = filtered_df['hours'].sum()
            
            if student_filter and student_filter != "Todos":
                # For a specific student, show their total hours
                student_name = students_df[students_df['phone'] == student_filter]['name'].values[0]
                st.info(f"""
                **Resumo para {student_name}:**
                * Total de estágios: {total_internships}
                * Total de horas: {total_hours}
                """)
            else:
                # For all students, show aggregate stats
                st.info(f"""
                **Resumo Geral:**
                * Total de estágios: {total_internships}
                * Total de horas: {total_hours}
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
                    "estagios.csv",
                    "text/csv",
                    key='download-csv-internships'
                )
        else:
            st.warning("Nenhum estágio encontrado com os filtros selecionados.")
    else:
        st.info("Não há estágios registrados ainda.")

with tab3:
    st.subheader("Editar Estágios")
    
    if internships_df is not None and not internships_df.empty:
        # Select internship to edit
        internship_ids = internships_df['internship_id'].tolist()
        
        # Format dates for better display
        internship_dates = pd.to_datetime(internships_df['date']).dt.strftime('%d/%m/%Y').tolist()
        
        # Format description for better readability
        internship_descriptions = [
            f"{id_} - {date} - {topic}"
            for id_, date, topic in zip(
                internship_ids, 
                internship_dates, 
                internships_df['topic'].tolist()
            )
        ]
        
        # Map descriptions back to IDs
        description_to_id = dict(zip(internship_descriptions, internship_ids))
        
        selected_description = st.selectbox(
            "Selecione o estágio para editar:",
            options=internship_descriptions
        )
        
        selected_id = description_to_id[selected_description]
        
        if selected_id:
            # Get selected internship data
            internship = internships_df[internships_df['internship_id'] == selected_id].iloc[0]
            
            # Get list of students in this internship
            student_phones = internship['students'].split(',') if pd.notna(internship['students']) else []
            
            # Create edit form
            with st.form("edit_internship_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    if students_df is not None and not students_df.empty:
                        # Allow updating student list
                        updated_students = st.multiselect(
                            "Alunos Participantes:",
                            options=students_df['phone'].tolist(),
                            default=student_phones,
                            format_func=lambda x: f"{format_phone(x)} - {students_df[students_df['phone'] == x]['name'].values[0]}"
                        )
                    else:
                        updated_students = student_phones
                    
                    internship_date = st.date_input(
                        "Data do Estágio", 
                        pd.to_datetime(internship['date']).date() if pd.notna(internship['date']) else datetime.now()
                    )
                    
                    hours = st.number_input(
                        "Horas de Estágio", 
                        min_value=1, 
                        value=int(internship['hours']), 
                        step=1
                    )
                
                with col2:
                    topic = st.text_input(
                        "Tema/Assunto", 
                        value=internship['topic'] if pd.notna(internship['topic']) else ""
                    )
                    
                    location = st.text_input(
                        "Local do Estágio", 
                        value=internship['location'] if pd.notna(internship['location']) else ""
                    )
                    
                    supervisor = st.text_input(
                        "Supervisor", 
                        value=internship['supervisor'] if pd.notna(internship['supervisor']) else ""
                    )
                
                notes = st.text_area(
                    "Observações", 
                    value=internship['notes'] if pd.notna(internship['notes']) else "", 
                    height=100
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    update_button = st.form_submit_button("Atualizar Dados")
                
                with col2:
                    delete_button = st.form_submit_button(
                        "Excluir Estágio", 
                        type="primary", 
                        use_container_width=True,
                        help="Atenção: Esta ação não pode ser desfeita!"
                    )
                
                if update_button:
                    # Update internship record
                    internships_df.loc[internships_df['internship_id'] == selected_id, 'date'] = internship_date.strftime('%Y-%m-%d')
                    internships_df.loc[internships_df['internship_id'] == selected_id, 'hours'] = hours
                    internships_df.loc[internships_df['internship_id'] == selected_id, 'topic'] = topic
                    internships_df.loc[internships_df['internship_id'] == selected_id, 'location'] = location
                    internships_df.loc[internships_df['internship_id'] == selected_id, 'supervisor'] = supervisor
                    internships_df.loc[internships_df['internship_id'] == selected_id, 'notes'] = notes
                    
                    # Update student list (comma-separated)
                    students_str = ','.join(updated_students)
                    internships_df.loc[internships_df['internship_id'] == selected_id, 'students'] = students_str
                    
                    # Save updated data
                    save_internships_data(internships_df)
                    
                    st.success("Dados do estágio atualizados com sucesso!")
                
                if delete_button:
                    # Confirmation for deletion
                    confirmation = st.checkbox("Confirmar exclusão do estágio", key="confirm_delete_internship")
                    
                    if confirmation:
                        # Remove internship from dataframe
                        internships_df = internships_df[internships_df['internship_id'] != selected_id]
                        
                        # Save updated data
                        save_internships_data(internships_df)
                        
                        st.success("Estágio excluído com sucesso!")
                        st.rerun()
                    else:
                        st.info("Marque a caixa de confirmação para excluir o estágio.")
    else:
        st.info("Não há estágios registrados ainda.")
