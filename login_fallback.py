import streamlit as st
import hashlib
import pandas as pd
import os
from datetime import datetime

# Função para calcular o hash MD5 da senha
def hash_senha(senha):
    """Gera um hash MD5 para a senha fornecida"""
    return hashlib.md5(senha.encode()).hexdigest()

# Função para carregar usuários do arquivo CSV (fallback)
def carregar_usuarios():
    """Carrega usuários de um arquivo CSV ou cria uma lista padrão se o arquivo não existir"""
    # Usuário admin padrão
    usuarios_padrao = [{
        "username": "admin",
        "name": "Administrador",
        "password_hash": "0192023a7bbd73250516f069df18b500",  # hash de admin123
        "level": "admin",
        "created_at": datetime.now().strftime("%Y-%m-%d")
    }]
    
    # Verificar se existe um arquivo CSV de usuários
    csv_path = 'data/users.csv'
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            return df
        except:
            # Em caso de erro, retornar lista padrão
            return pd.DataFrame(usuarios_padrao)
    else:
        # Se o arquivo não existir, criar diretório se necessário
        os.makedirs('data', exist_ok=True)
        
        # Criar DataFrame e salvar
        df = pd.DataFrame(usuarios_padrao)
        df.to_csv(csv_path, index=False)
        
        return df

# Função para salvar usuários em CSV
def salvar_usuarios(df):
    """Salva usuários em um arquivo CSV"""
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/users.csv', index=False)

# Função para verificar login
def verificar_login(usuario, senha):
    """Verifica se o usuário e senha correspondem a um usuário válido"""
    # Calcular hash da senha
    senha_hash = hash_senha(senha)
    
    # Carregar usuários
    usuarios_df = carregar_usuarios()
    
    # Verificar se o usuário existe
    usuario_row = usuarios_df[usuarios_df['username'] == usuario]
    
    if usuario_row.empty:
        return False
    
    # Verificar senha
    if usuario_row.iloc[0]['password_hash'] == senha_hash:
        # Armazenar informações do usuário na sessão
        st.session_state['autenticado'] = True
        st.session_state['usuario'] = usuario
        st.session_state['nome'] = usuario_row.iloc[0]['name']
        st.session_state['nivel'] = usuario_row.iloc[0]['level']
        
        return True
    
    return False

# Função para verificar se o usuário está autenticado
def verificar_autenticacao():
    """Verifica se o usuário está autenticado na sessão atual"""
    if 'autenticado' in st.session_state and st.session_state['autenticado']:
        return True
    
    return False

# Função para logout
def logout():
    """Remove informações de autenticação da sessão"""
    if 'autenticado' in st.session_state:
        del st.session_state['autenticado']
    
    if 'usuario' in st.session_state:
        del st.session_state['usuario']
    
    if 'nome' in st.session_state:
        del st.session_state['nome']
    
    if 'nivel' in st.session_state:
        del st.session_state['nivel']

# Função para exibir página de login
def mostrar_pagina_login():
    """Exibe o formulário de login"""
    st.title("Login")
    
    # Logo no centro
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("assets/images/logo.png", width=200)
        except:
            st.write("Tertúlia Libras")
    
    # Formulário de login
    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        
        submitted = st.form_submit_button("Entrar")
        
        if submitted:
            if verificar_login(usuario, senha):
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    
    # Informações adicionais
    st.info("Este é um sistema de gestão para a Tertúlia Libras. Para acessar, utilize suas credenciais.")
    
    # Créditos
    st.markdown("---")
    st.caption("© Tertúlia Libras - Todos os direitos reservados")

# Função para gerenciar usuários (apenas administradores)
def pagina_gerenciar_usuarios():
    """Exibe a página de gerenciamento de usuários (apenas para administradores)"""
    if not verificar_autenticacao():
        mostrar_pagina_login()
        return
    
    # Verificar se é administrador
    if st.session_state.get('nivel') != 'admin':
        st.error("Acesso negado. Apenas administradores podem acessar esta página.")
        return
    
    st.title("Gerenciar Usuários")
    
    # Carregar usuários
    usuarios_df = carregar_usuarios()
    
    # Criar abas
    tab_list, tab_new, tab_edit = st.tabs(["Lista de Usuários", "Novo Usuário", "Editar Usuário"])
    
    # Aba Lista de Usuários
    with tab_list:
        st.subheader("Usuários Cadastrados")
        
        if not usuarios_df.empty:
            # Ocultar hash da senha
            display_df = usuarios_df.copy()
            if 'password_hash' in display_df.columns:
                display_df['password_hash'] = '********'
            
            st.dataframe(display_df)
        else:
            st.info("Nenhum usuário cadastrado.")
    
    # Aba Novo Usuário
    with tab_new:
        st.subheader("Cadastrar Novo Usuário")
        
        with st.form("new_user_form"):
            username = st.text_input("Nome de usuário")
            name = st.text_input("Nome completo")
            password = st.text_input("Senha", type="password")
            confirm_password = st.text_input("Confirmar senha", type="password")
            
            level = st.selectbox(
                "Nível de acesso",
                ["user", "admin"],
                format_func=lambda x: "Administrador" if x == "admin" else "Usuário Comum"
            )
            
            submitted = st.form_submit_button("Cadastrar")
            
            if submitted:
                # Validação
                if not username or not name or not password:
                    st.error("Todos os campos são obrigatórios.")
                elif password != confirm_password:
                    st.error("As senhas não coincidem.")
                else:
                    # Verificar se usuário já existe
                    if not usuarios_df.empty and username in usuarios_df['username'].values:
                        st.error(f"Usuário '{username}' já existe.")
                    else:
                        # Criar novo usuário
                        novo_usuario = {
                            "username": username,
                            "name": name,
                            "password_hash": hash_senha(password),
                            "level": level,
                            "created_at": datetime.now().strftime("%Y-%m-%d")
                        }
                        
                        # Adicionar ao DataFrame
                        new_row = pd.DataFrame([novo_usuario])
                        
                        if usuarios_df.empty:
                            usuarios_df = new_row
                        else:
                            usuarios_df = pd.concat([usuarios_df, new_row], ignore_index=True)
                        
                        # Salvar no CSV
                        salvar_usuarios(usuarios_df)
                        
                        st.success(f"Usuário '{username}' cadastrado com sucesso!")
    
    # Aba Editar Usuário
    with tab_edit:
        st.subheader("Editar Usuário")
        
        if not usuarios_df.empty:
            # Selecionar usuário
            selected_user = st.selectbox(
                "Selecione o usuário",
                usuarios_df['username'].tolist()
            )
            
            # Obter dados do usuário
            user_data = usuarios_df[usuarios_df['username'] == selected_user].iloc[0]
            
            with st.form("edit_user_form"):
                # Nome completo
                name = st.text_input("Nome completo", value=user_data['name'])
                
                # Senha (opcional)
                st.write("Deixe em branco para manter a senha atual:")
                password = st.text_input("Nova senha", type="password")
                confirm_password = st.text_input("Confirmar nova senha", type="password")
                
                # Nível de acesso
                level = st.selectbox(
                    "Nível de acesso",
                    ["user", "admin"],
                    index=0 if user_data['level'] == "user" else 1,
                    format_func=lambda x: "Administrador" if x == "admin" else "Usuário Comum"
                )
                
                submitted = st.form_submit_button("Atualizar")
                
                if submitted:
                    # Validação
                    if not name:
                        st.error("O nome é obrigatório.")
                    elif password and password != confirm_password:
                        st.error("As senhas não coincidem.")
                    else:
                        # Atualizar usuário
                        usuarios_df.loc[usuarios_df['username'] == selected_user, 'name'] = name
                        usuarios_df.loc[usuarios_df['username'] == selected_user, 'level'] = level
                        
                        # Atualizar senha se fornecida
                        if password:
                            usuarios_df.loc[usuarios_df['username'] == selected_user, 'password_hash'] = hash_senha(password)
                        
                        # Salvar no CSV
                        salvar_usuarios(usuarios_df)
                        
                        st.success(f"Usuário '{selected_user}' atualizado com sucesso!")
            
            # Excluir usuário
            if st.button("Excluir Usuário", type="primary", help="Esta ação não pode ser desfeita!"):
                # Não permitir excluir o último administrador
                admin_count = len(usuarios_df[usuarios_df['level'] == 'admin'])
                is_admin = user_data['level'] == 'admin'
                
                if is_admin and admin_count <= 1:
                    st.error("Não é possível excluir o último administrador.")
                else:
                    # Excluir usuário
                    usuarios_df = usuarios_df[usuarios_df['username'] != selected_user]
                    
                    # Salvar no CSV
                    salvar_usuarios(usuarios_df)
                    
                    st.success(f"Usuário '{selected_user}' excluído com sucesso!")
                    st.rerun()
        else:
            st.info("Nenhum usuário cadastrado.")
