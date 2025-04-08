import streamlit as st
import pandas as pd
from datetime import datetime

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
            load_internships_data,
            save_internships_data,
            get_student_internship_hours
        )
    except ImportError as e:
        st.error(f"Erro ao importar módulos: {e}")
        st.info("Esta funcionalidade requer conexão com o banco de dados.")
        st.stop()
    
    st.title("Gerenciamento de Estágios")
    
    # Carregar dados
    students_df = load_students_data()
    internships_df = load_internships_data()
    
    # Verificar se há alunos cadastrados
    if students_df.empty:
        st.warning("Não há alunos cadastrados.")
        st.stop()
    
    # Criar abas
    tab_list, tab_new, tab_manage = st.tabs(["Lista de Estágios", "Novo Estágio", "Gerenciar Estágio"])
    
    # Função auxiliar para formatar lista de alunos
    def format_students(students_str):
        """Converte uma string de telefones para lista de alunos"""
        if not students_str:
            return []
        
        # Separar telefones
        phones = students_str.split(',')
        
        # Formatar nomes dos alunos
        student_list = []
        for phone in phones:
            phone = phone.strip()
            if phone and 'name' in students_df.columns and 'phone' in students_df.columns:
                student_name = students_df[students_df['phone'] == phone]['name'].values
                if len(student_name) > 0:
                    student_list.append(f"{student_name[0]} ({phone})")
                else:
                    student_list.append(phone)
        
        return student_list
    
    # Aba Lista de Estágios
    with tab_list:
        st.subheader("Lista de Estágios Registrados")
        
        # Filtro de aluno
        all_students = ["Todos"] + students_df['name'].tolist() if 'name' in students_df.columns else ["Todos"]
        student_filter = st.selectbox(
            "Filtrar por aluno:",
            all_students,
            key="internship_list_student"
        )
        
        # Filtrar estágios
        if not internships_df.empty:
            # Aplicar filtro de aluno
            if student_filter != "Todos" and 'phone' in internships_df.columns:
                # Obter telefone do aluno
                if 'name' in students_df.columns and 'phone' in students_df.columns:
                    student_phone = students_df[students_df['name'] == student_filter]['phone'].iloc[0]
                    filtered_df = internships_df[internships_df['phone'] == student_phone]
                else:
                    filtered_df = internships_df
                    st.warning("Não foi possível filtrar por aluno (dados incompatíveis).")
            else:
                filtered_df = internships_df
            
            # Mostrar dados
            if not filtered_df.empty:
                # Juntar com dados dos alunos para exibir nome
                if 'phone' in filtered_df.columns and 'phone' in students_df.columns and 'name' in students_df.columns:
                    display_df = pd.merge(
                        filtered_df,
                        students_df[['phone', 'name']],
                        on='phone',
                        how='left'
                    )
                else:
                    display_df = filtered_df
                
                # Ordenar por data
                if 'date' in display_df.columns:
                    display_df = display_df.sort_values('date', ascending=False)
                
                # Colunas a exibir
                if 'name' in display_df.columns:
                    display_cols = ['name', 'date', 'topic', 'hours', 'location']
                else:
                    display_cols = ['phone', 'date', 'topic', 'hours', 'location']
                
                # Verificar se todas as colunas existem
                display_cols = [col for col in display_cols if col in display_df.columns]
                
                # Preparar dados para exibição
                display_view = display_df[display_cols].copy()
                
                st.dataframe(display_view, use_container_width=True)
                
                # Mostrar total de horas de estágio
                if 'hours' in filtered_df.columns:
                    total_hours = filtered_df['hours'].sum()
                    st.success(f"Total de horas de estágio: {total_hours}h")
                
                # Se filtrado por aluno, mostrar detalhes
                if student_filter != "Todos" and 'hours' in filtered_df.columns:
                    st.subheader(f"Detalhes de estágio para {student_filter}")
                    
                    # Agrupar por tópico
                    if 'topic' in filtered_df.columns:
                        topic_hours = filtered_df.groupby('topic')['hours'].sum().reset_index()
                        
                        # Mostrar horas por tópico
                        st.write("Horas por tópico:")
                        for _, row in topic_hours.iterrows():
                            st.info(f"{row['topic']}: {row['hours']}h")
            else:
                st.info("Nenhum estágio encontrado com os filtros selecionados.")
        else:
            st.info("Nenhum estágio registrado.")
    
    # Aba Novo Estágio
    with tab_new:
        st.subheader("Registrar Novo Estágio")
        
        with st.form("new_internship_form"):
            # Selecionar aluno
            student_name = st.selectbox(
                "Aluno:",
                students_df['name'].tolist() if 'name' in students_df.columns else [],
                key="new_internship_student"
            )
            
            # Obter telefone do aluno selecionado
            if 'name' in students_df.columns and 'phone' in students_df.columns:
                student_phone = students_df[students_df['name'] == student_name]['phone'].iloc[0]
            else:
                student_phone = ""
                st.warning("Não foi possível obter o telefone do aluno.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Data do estágio
                internship_date = st.date_input(
                    "Data do estágio",
                    datetime.now().date(),
                    key="new_internship_date"
                )
                
                # Tópico
                topic = st.selectbox(
                    "Tópico do estágio",
                    [
                        "Tradução consecutiva",
                        "Tradução simultânea",
                        "Interpretação em conferência",
                        "Interpretação educacional",
                        "Consultoria em acessibilidade",
                        "Preparação de materiais",
                        "Outro"
                    ],
                    key="new_internship_topic"
                )
                
                if topic == "Outro":
                    topic = st.text_input("Especifique o tópico:", key="new_internship_topic_other")
            
            with col2:
                # Horas
                hours = st.number_input(
                    "Horas de estágio",
                    min_value=0.5,
                    step=0.5,
                    value=2.0,
                    key="new_internship_hours"
                )
                
                # Local
                location = st.text_input("Local do estágio", key="new_internship_location")
                
                # Supervisor
                supervisor = st.text_input("Supervisor", key="new_internship_supervisor")
            
            # Descrição da atividade
            description = st.text_area("Descrição da atividade", key="new_internship_description")
            
            # Alunos participantes (multi-select)
            st.write("Selecione alunos adicionais que participaram deste estágio (opcional):")
            
            # Filtrar para não mostrar o aluno principal
            other_students = students_df[students_df['phone'] != student_phone] if not students_df.empty and 'phone' in students_df.columns else pd.DataFrame()
            
            selected_students = []
            if not other_students.empty and 'name' in other_students.columns and 'phone' in other_students.columns:
                # Criar opções de alunos com nomes
                student_options = {row['name']: row['phone'] for _, row in other_students.iterrows()}
                
                # Checkbox para cada aluno
                columns = st.columns(3)
                col_idx = 0
                
                for name, phone in student_options.items():
                    with columns[col_idx]:
                        if st.checkbox(name, key=f"student_{phone}"):
                            selected_students.append(phone)
                    
                    col_idx = (col_idx + 1) % 3
            
            submitted = st.form_submit_button("Registrar")
            
            if submitted:
                # Validação de dados
                if not student_phone:
                    st.error("Selecione um aluno válido.")
                elif not topic:
                    st.error("Informe o tópico do estágio.")
                elif hours <= 0:
                    st.error("A carga horária deve ser maior que zero.")
                else:
                    # Preparar dados para o aluno principal
                    new_internship = {
                        "phone": student_phone,
                        "date": internship_date.strftime("%Y-%m-%d"),
                        "topic": topic,
                        "hours": hours,
                        "location": location,
                        "supervisor": supervisor,
                        "description": description,
                        "students": ",".join([student_phone] + selected_students) if selected_students else student_phone
                    }
                    
                    # Adicionar ao DataFrame
                    new_row = pd.DataFrame([new_internship])
                    
                    # Se o DataFrame estiver vazio, criar um novo
                    if internships_df.empty:
                        internships_df = new_row
                    else:
                        internships_df = pd.concat([internships_df, new_row], ignore_index=True)
                    
                    # Se houver alunos adicionais, criar registros para eles também
                    for additional_phone in selected_students:
                        additional_internship = new_internship.copy()
                        additional_internship["phone"] = additional_phone
                        
                        additional_row = pd.DataFrame([additional_internship])
                        internships_df = pd.concat([internships_df, additional_row], ignore_index=True)
                    
                    # Salvar dados
                    try:
                        save_internships_data(internships_df)
                        
                        if selected_students:
                            total_students = len(selected_students) + 1
                            st.success(f"Estágio registrado com sucesso para {total_students} alunos!")
                        else:
                            st.success(f"Estágio registrado com sucesso para {student_name}!")
                    except Exception as e:
                        st.error(f"Erro ao salvar dados: {e}")
    
    # Aba Gerenciar Estágio
    with tab_manage:
        st.subheader("Gerenciar Estágio")
        
        if not internships_df.empty:
            # Selecionar aluno primeiro
            student_filter = st.selectbox(
                "Selecione o aluno:",
                students_df['name'].tolist() if 'name' in students_df.columns else [],
                key="manage_internship_student"
            )
            
            # Obter telefone do aluno selecionado
            if 'name' in students_df.columns and 'phone' in students_df.columns:
                student_phone = students_df[students_df['name'] == student_filter]['phone'].iloc[0]
            else:
                student_phone = ""
                st.warning("Não foi possível obter o telefone do aluno.")
            
            # Filtrar estágios do aluno
            student_internships = internships_df[internships_df['phone'] == student_phone].copy() if student_phone else pd.DataFrame()
            
            if not student_internships.empty:
                # Ordenar por data
                if 'date' in student_internships.columns:
                    student_internships = student_internships.sort_values('date', ascending=False)
                
                # Preparar lista de estágios para seleção
                internship_list = []
                for idx, row in student_internships.iterrows():
                    internship_id = row.get('id', None)
                    internship_date = row.get('date', '')
                    topic = row.get('topic', '')
                    hours = row.get('hours', 0)
                    
                    # Formatar texto para seleção
                    internship_text = f"{internship_date} - {topic} - {hours}h"
                    
                    internship_list.append((internship_text, internship_id or idx))
                
                # Selecionar estágio
                selected_internship = st.selectbox(
                    "Selecione o estágio:",
                    [text for text, _ in internship_list],
                    key="manage_internship_select"
                )
                
                # Obter ID do estágio selecionado
                selected_idx = [text for text, _ in internship_list].index(selected_internship)
                internship_id = internship_list[selected_idx][1]
                
                # Obter dados do estágio selecionado
                if isinstance(internship_id, int) and not isinstance(internship_id, bool):
                    internship_data = student_internships.iloc[internship_id]
                else:
                    internship_data = student_internships[student_internships['id'] == internship_id].iloc[0]
                
                # Exibir formulário de edição
                with st.form("edit_internship_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Data do estágio
                        internship_date = st.date_input(
                            "Data do estágio",
                            datetime.strptime(internship_data.get('date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date(),
                            key="edit_internship_date"
                        )
                        
                        # Tópico
                        topic_options = [
                            "Tradução consecutiva",
                            "Tradução simultânea",
                            "Interpretação em conferência",
                            "Interpretação educacional",
                            "Consultoria em acessibilidade",
                            "Preparação de materiais",
                            "Outro"
                        ]
                        
                        current_topic = internship_data.get('topic', '')
                        topic_index = topic_options.index(current_topic) if current_topic in topic_options else len(topic_options) - 1
                        
                        topic = st.selectbox(
                            "Tópico do estágio",
                            topic_options,
                            index=topic_index,
                            key="edit_internship_topic"
                        )
                        
                        if topic == "Outro" or topic_index == len(topic_options) - 1:
                            topic = st.text_input("Especifique o tópico:", value=current_topic, key="edit_internship_topic_other")
                    
                    with col2:
                        # Horas
                        hours = st.number_input(
                            "Horas de estágio",
                            min_value=0.5,
                            step=0.5,
                            value=float(internship_data.get('hours', 2.0)),
                            key="edit_internship_hours"
                        )
                        
                        # Local
                        location = st.text_input("Local do estágio", value=internship_data.get('location', ''), key="edit_internship_location")
                        
                        # Supervisor
                        supervisor = st.text_input("Supervisor", value=internship_data.get('supervisor', ''), key="edit_internship_supervisor")
                    
                    # Descrição da atividade
                    description = st.text_area("Descrição da atividade", value=internship_data.get('description', ''), key="edit_internship_description")
                    
                    # Alunos participantes
                    if 'students' in internship_data:
                        st.write("Alunos participantes:")
                        students_list = format_students(internship_data['students'])
                        for student in students_list:
                            st.info(student)
                    
                    submitted = st.form_submit_button("Atualizar")
                    
                    if submitted:
                        # Validação de dados
                        if not topic:
                            st.error("Informe o tópico do estágio.")
                        elif hours <= 0:
                            st.error("A carga horária deve ser maior que zero.")
                        else:
                            # Preparar dados
                            updated_internship = internship_data.copy()
                            updated_internship.update({
                                "date": internship_date.strftime("%Y-%m-%d"),
                                "topic": topic,
                                "hours": hours,
                                "location": location,
                                "supervisor": supervisor,
                                "description": description
                            })
                            
                            # Atualizar no DataFrame
                            if 'id' in internship_data and internship_data['id']:
                                internships_df.loc[internships_df['id'] == internship_data['id']] = updated_internship
                            else:
                                internships_df.iloc[internship_id] = updated_internship
                            
                            # Salvar dados
                            try:
                                save_internships_data(internships_df)
                                st.success(f"Estágio atualizado com sucesso!")
                            except Exception as e:
                                st.error(f"Erro ao salvar dados: {e}")
                
                # Excluir estágio
                if st.button("Excluir Estágio", type="primary", help="Cuidado! Esta ação não pode ser desfeita.", key="delete_internship"):
                    # Excluir do DataFrame
                    if 'id' in internship_data and internship_data['id']:
                        internships_df = internships_df[internships_df['id'] != internship_data['id']]
                    else:
                        internships_df = internships_df.drop(internship_id)
                    
                    # Salvar dados
                    try:
                        save_internships_data(internships_df)
                        st.success(f"Estágio excluído com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar dados: {e}")
            else:
                st.info(f"Não há estágios registrados para este aluno.")
        else:
            st.info("Nenhum estágio registrado.")
