import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import datetime, timedelta
from config import get_logo_path
from database import authenticate_user, load_users, save_user, update_user, delete_user

# Nome da variável de sessão para login
LOGIN_SESSION_VAR = "usuario_autenticado"
LOGIN_EXPIRY_VAR = "login_expiracao"
# Tempo de expiração da sessão em horas
LOGIN_EXPIRY_HOURS = 12

# Função para hash de senha
def hash_senha(senha):
    # Usando MD5 para compatibilidade com senhas existentes no sistema
    return hashlib.md5(senha.encode()).hexdigest()

# Função para carregar usuários
def carregar_usuarios():
    # Carregar usuários do banco de dados
    usuarios = load_users()
    
    if not usuarios:
        # Se não existirem usuários, criar o usuário admin padrão
        usuario_admin = {
            "username": "admin",
            "password_hash": hash_senha("admin123"),
            "name": "Administrador",
            "level": "admin",
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_user(usuario_admin)
        return pd.DataFrame([{
            "usuario": "admin",
            "senha_hash": hash_senha("admin123"),
            "nome": "Administrador", 
            "nivel": "admin"
        }])
    
    # Converter do formato do Supabase para o formato usado no aplicativo
    usuarios_convertidos = []
    for usuario in usuarios:
        usuarios_convertidos.append({
            "usuario": usuario.get("username", ""),
            "senha_hash": usuario.get("password_hash", ""),
            "nome": usuario.get("name", ""),
            "nivel": usuario.get("level", "usuario")
        })
    
    return pd.DataFrame(usuarios_convertidos)

def salvar_usuarios(df):
    # Para cada usuário no DataFrame, salvar no Supabase
    for _, row in df.iterrows():
        user_data = {
            "username": row["usuario"],
            "password_hash": row["senha_hash"],
            "name": row["nome"],
            "level": row["nivel"],
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Verificar se o usuário já existe para atualizar ou criar
        usuarios = load_users()
        usuario_existente = None
        user_id = None
        
        for u in usuarios:
            if u.get("username") == row["usuario"]:
                usuario_existente = u
                user_id = u.get("id")
                break
        
        if usuario_existente:
            update_user(user_id, user_data)
        else:
            save_user(user_data)

# Função para verificar login
def verificar_login(usuario, senha):
    # Calcular hash da senha fornecida
    senha_hash = hash_senha(senha)
    
    # Usar função direta do Supabase para autenticar
    user_data = authenticate_user(usuario, senha_hash)
    
    if user_data:
        # Obter informações do usuário - usar apenas o campo "level"
        nivel = user_data.get("level", "usuario")
        nome = user_data.get("name", usuario)
        
        # Definir expiração
        expiracao = datetime.now() + timedelta(hours=LOGIN_EXPIRY_HOURS)
        
        return True, nivel, nome, expiracao
    
    # Caso a autenticação direta falhe, tentar com o método do DataFrame para compatibilidade
    usuarios_df = carregar_usuarios()
    
    # Verificar se o usuário existe
    if usuario in usuarios_df["usuario"].values:
        # Obter o hash da senha armazenada
        senha_hash_stored = usuarios_df.loc[usuarios_df["usuario"] == usuario, "senha_hash"].values[0]
        
        # Verificar se a senha corresponde
        if senha_hash_stored == senha_hash:
            # Obter o nível de acesso
            nivel = usuarios_df.loc[usuarios_df["usuario"] == usuario, "nivel"].values[0]
            nome = usuarios_df.loc[usuarios_df["usuario"] == usuario, "nome"].values[0]
            
            # Definir expiração
            expiracao = datetime.now() + timedelta(hours=LOGIN_EXPIRY_HOURS)
            
            return True, nivel, nome, expiracao
    
    return False, None, None, None

# Função para verificar se o usuário está logado
def verificar_autenticacao():
    # Verificar primeiro no estado persistente do Streamlit
    if LOGIN_SESSION_VAR in st.session_state and LOGIN_EXPIRY_VAR in st.session_state:
        # Verificar se o login expirou
        if datetime.now() < st.session_state[LOGIN_EXPIRY_VAR]:
            return True
    
    return False

# Função para fazer logout
def logout():
    # Importar a função de logout universal
    from auth_wrapper import do_logout
    do_logout()
    
    # Removendo também as variáveis padrão
    if LOGIN_SESSION_VAR in st.session_state:
        del st.session_state[LOGIN_SESSION_VAR]
    
    if LOGIN_EXPIRY_VAR in st.session_state:
        del st.session_state[LOGIN_EXPIRY_VAR]

# Página de login
def mostrar_pagina_login():
    # Custom CSS para estilizar o logo
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
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .stButton > button {
            width: 100%;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header com logo
    col1, col2 = st.columns([1, 3])
    with col1:
        try:
            # Usar função para obter o caminho da logo
            logo_path = get_logo_path()
            st.image(logo_path, width=120)
        except Exception as e:
            st.warning(f"Erro ao carregar a logo: {e}")
            st.image('assets/images/logo.svg', width=120)
    with col2:
        st.title("Sistema de Gestão Libras")

    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    
    st.subheader("Login")
    
    # Formulário de login
    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        
        submetido = st.form_submit_button("Entrar")
        
        if submetido:
            if usuario and senha:
                autenticado, nivel, nome, expiracao = verificar_login(usuario, senha)
                
                if autenticado:
                    # Armazenar informações na sessão
                    from auth_wrapper import set_authentication
                    
                    # Definir as variáveis padrão
                    st.session_state[LOGIN_SESSION_VAR] = {
                        "usuario": usuario,
                        "nivel": nivel,
                        "nome": nome
                    }
                    st.session_state[LOGIN_EXPIRY_VAR] = expiracao
                    
                    # Também usar o wrapper para garantir consistência
                    set_authentication({
                        "usuario": usuario,
                        "nivel": nivel,
                        "nome": nome
                    }, expiracao)
                    
                    st.success(f"Bem-vindo, {nome}!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos")
            else:
                st.warning("Por favor, informe o usuário e a senha")
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Rodapé
    st.markdown("<div style='text-align: center; margin-top: 50px; opacity: 0.7;'>© 2025 Sistema de Gestão Libras</div>", unsafe_allow_html=True)

# Função para gerenciar usuários (somente para admin)
def pagina_gerenciar_usuarios():
    if not LOGIN_SESSION_VAR in st.session_state:
        st.error("Acesso negado. Você não está logado.")
        return
    
    # Verificar o nível de acesso sem mostrar na interface
    nivel_acesso = st.session_state[LOGIN_SESSION_VAR]['nivel']
    
    # Verificar se é admin
    if st.session_state[LOGIN_SESSION_VAR]["nivel"] != "admin":
        st.error("Acesso negado. Você não tem permissão para gerenciar usuários.")
        return
        
    # Se chegou aqui, é admin
    st.subheader("Gerenciar Usuários")
    
    usuarios_df = carregar_usuarios()
    
    # Criar novo usuário
    with st.expander("Adicionar Novo Usuário"):
        with st.form("novo_usuario_form"):
            novo_usuario = st.text_input("Nome de Usuário")
            nova_senha = st.text_input("Senha", type="password")
            confirmar_senha = st.text_input("Confirmar Senha", type="password")
            nome_completo = st.text_input("Nome Completo")
            nivel = st.selectbox("Nível de Acesso", ["usuario", "admin"])
            
            submetido = st.form_submit_button("Adicionar Usuário")
            
            if submetido:
                if not novo_usuario or not nova_senha or not nome_completo:
                    st.warning("Todos os campos são obrigatórios")
                elif nova_senha != confirmar_senha:
                    st.error("As senhas não coincidem")
                elif novo_usuario in usuarios_df["usuario"].values:
                    st.error("Este nome de usuário já existe")
                else:
                    # Adicionar novo usuário
                    novo_df = pd.DataFrame([{
                        "usuario": novo_usuario,
                        "senha_hash": hash_senha(nova_senha),
                        "nome": nome_completo,
                        "nivel": nivel
                    }])
                    
                    usuarios_df = pd.concat([usuarios_df, novo_df], ignore_index=True)
                    salvar_usuarios(usuarios_df)
                    st.success("Usuário adicionado com sucesso!")
                    st.rerun()
    
    # Listar usuários
    if not usuarios_df.empty:
        st.subheader("Usuários Cadastrados")
        
        # Criar cópia para exibição (sem mostrar hash)
        usuarios_exibicao = usuarios_df[["usuario", "nome", "nivel"]].copy()
        
        # Renomear colunas para exibição
        usuarios_exibicao.columns = ["Usuário", "Nome", "Nível de Acesso"]
        
        st.dataframe(usuarios_exibicao, use_container_width=True)
        
        # Alterar senha
        with st.expander("Alterar Senha de Usuário"):
            with st.form("alterar_senha_form"):
                usuario_selecionado = st.selectbox(
                    "Selecione o Usuário",
                    options=usuarios_df["usuario"].tolist()
                )
                
                nova_senha = st.text_input("Nova Senha", type="password")
                confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
                
                submetido = st.form_submit_button("Alterar Senha")
                
                if submetido:
                    if not nova_senha:
                        st.warning("Informe a nova senha")
                    elif nova_senha != confirmar_senha:
                        st.error("As senhas não coincidem")
                    else:
                        # Atualizar senha
                        usuarios_df.loc[usuarios_df["usuario"] == usuario_selecionado, "senha_hash"] = hash_senha(nova_senha)
                        salvar_usuarios(usuarios_df)
                        st.success("Senha alterada com sucesso!")
        
        # Remover usuário
        with st.expander("Remover Usuário"):
            with st.form("remover_usuario_form"):
                usuario_remover = st.selectbox(
                    "Selecione o Usuário para Remover",
                    options=usuarios_df[usuarios_df["usuario"] != "admin"]["usuario"].tolist()
                )
                
                st.warning("Esta ação não pode ser desfeita!")
                confirmacao = st.checkbox("Confirmo que desejo remover este usuário")
                
                submetido = st.form_submit_button("Remover Usuário")
                
                if submetido:
                    if not confirmacao:
                        st.error("Você precisa confirmar a remoção")
                    else:
                        # Remover usuário do Supabase
                        usuarios = load_users()
                        user_id = None
                        
                        # Encontrar o ID do usuário
                        for u in usuarios:
                            if u.get("username") == usuario_remover:
                                user_id = u.get("id")
                                break
                                
                        if user_id:
                            # Excluir usando a função do Supabase
                            delete_user(user_id)
                            
                            # Atualizar lista local
                            usuarios_df = usuarios_df[usuarios_df["usuario"] != usuario_remover]
                            st.success("Usuário removido com sucesso!")
                            st.rerun()
                        else:
                            st.error("Erro ao localizar o usuário no banco de dados.")

# Função para troca de senha do usuário logado
def pagina_trocar_senha():
    st.title("Trocar Senha")
    
    if not verificar_autenticacao():
        st.error("Você precisa estar logado para trocar a senha.")
        return
    
    usuario_atual = st.session_state[LOGIN_SESSION_VAR]['usuario']
    
    with st.form("trocar_senha_form"):
        st.write(f"Usuário: **{usuario_atual}**")
        
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
        
        submit_button = st.form_submit_button("Trocar Senha")
        
        if submit_button:
            if not senha_atual or not nova_senha or not confirmar_senha:
                st.error("Todos os campos são obrigatórios!")
            elif nova_senha != confirmar_senha:
                st.error("As senhas não coincidem!")
            else:
                # Verificar se a senha atual está correta
                senha_atual_hash = hash_senha(senha_atual)
                
                # Buscar o usuário no banco de dados
                usuarios = load_users()
                usuario_encontrado = None
                
                for usuario in usuarios:
                    if usuario['username'] == usuario_atual:
                        usuario_encontrado = usuario
                        break
                
                if not usuario_encontrado or usuario_encontrado['password_hash'] != senha_atual_hash:
                    st.error("Senha atual incorreta!")
                else:
                    # Atualizar a senha
                    nova_senha_hash = hash_senha(nova_senha)
                    usuario_atualizado = usuario_encontrado.copy()
                    usuario_atualizado['password_hash'] = nova_senha_hash
                    
                    # Salvar no banco de dados usando o id original
                    if 'id' in usuario_encontrado:
                        update_user(usuario_encontrado['id'], usuario_atualizado)
                    else:
                        # Tratamento alternativo se não houver ID
                        save_user(usuario_atualizado)
                    
                    st.success("Senha atualizada com sucesso!")
                    # Iniciar um contador para retornar ao dashboard
                    st.info("Redirecionando para o dashboard em 3 segundos...")
                    import time
                    time.sleep(3)
                    # Redirecionar
                    if 'mostrar_trocar_senha' in st.session_state:
                        st.session_state['mostrar_trocar_senha'] = False
                    st.rerun()

if __name__ == "__main__":
    mostrar_pagina_login()
