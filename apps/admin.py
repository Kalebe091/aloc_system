import streamlit as st
import pandas as pd
import sys
import os
import time
from streamlit_calendar import calendar

# --- CONFIGURAÇÃO DE CAMINHOS ---
# Adiciona a pasta raiz do projeto ao Python para ele achar a pasta 'database'
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

# Agora importamos do novo local renomeado, chamando de 'db' para manter compatibilidade
from database import db_connection as db 

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SGA Anhanguera", layout="wide", page_icon="🔒")

st.title("🛡️ Painel Administrativo - Anhanguera")
st.markdown("---")

# --- LÓGICA DE LOGIN (GATEKEEPER) ---

if 'logado' not in st.session_state:
    st.session_state['logado'] = False
    st.session_state['usuario_nome'] = ''

def tela_login():
    st.markdown("<h1 style='text-align: center;'>🔒 Acesso Restrito - SGA</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        with st.form("login_form"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            btn_entrar = st.form_submit_button("Entrar", type="primary")
            
            if btn_entrar:
                sucesso, nome = db.verificar_login(usuario, senha)
                if sucesso:
                    st.session_state['logado'] = True
                    st.session_state['usuario_nome'] = nome
                    st.success("Login realizado! Redirecionando...")
                    time.sleep(1)
                    st.rerun() # Recarrega a página para entrar no sistema
                else:
                    st.error("Usuário ou senha incorretos.")

# SE NÃO ESTIVER LOGADO, MOSTRA LOGIN E PARA TUDO
if not st.session_state['logado']:
    tela_login()
    st.stop() # <--- Isso impede que o resto do código carreue sem login

# --- MENU LATERAL ---
with st.sidebar:
    st.write(f"👤 Olá, **{st.session_state['usuario_nome']}**")
    if st.button("Sair (Logout)"):
        st.session_state['logado'] = False
        st.rerun()
    st.markdown("---")

menu = st.sidebar.radio(
    "Gerenciamento",
    ["Visão Geral", "Salas", "Docentes", "Cursos & Turmas", "Alocações (Grade)", "Nova Alocação", "Gerenciar Grade", "Calendário Visual"]
)

# --- 1. VISÃO GERAL (DASHBOARD) ---
if menu == "Visão Geral":
    st.subheader("📊 Estatísticas do Sistema")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Buscando contagens reais do banco
    # Tratamento de erro simples caso as tabelas estejam vazias
    try:
        qtd_salas = db.run_query("SELECT COUNT(*) FROM tb_salas").iloc[0,0]
        qtd_profs = db.run_query("SELECT COUNT(*) FROM tb_docentes").iloc[0,0]
        qtd_turmas = db.run_query("SELECT COUNT(*) FROM tb_turmas").iloc[0,0]
        qtd_aulas = db.run_query("SELECT COUNT(*) FROM tb_alocacoes").iloc[0,0]
    except:
        qtd_salas, qtd_profs, qtd_turmas, qtd_aulas = 0, 0, 0, 0
    
    col1.metric("Salas Cadastradas", qtd_salas)
    col2.metric("Docentes Ativos", qtd_profs)
    col3.metric("Turmas Registradas", qtd_turmas)
    col4.metric("Aulas Alocadas", qtd_aulas)
    
    st.info("Bem-vindo, Administrador. Use o menu lateral para gerenciar o banco de dados.")

# --- 2. GERENCIAR SALAS ---
elif menu == "Salas":
    st.subheader("🏢 Gestão de Salas")
    
    with st.expander("➕ Cadastrar Nova Sala"):
        with st.form("form_sala"):
            nome = st.text_input("Nome da Sala (ex: Sala 40)")
            cap = st.number_input("Capacidade", min_value=1, value=50)
            tipo = st.selectbox("Tipo", ["Teorica", "Laboratorio", "Auditorio"])
            
            if st.form_submit_button("Salvar Sala"):
                sql = "INSERT INTO tb_salas (nome, capacidade, tipo) VALUES (%s, %s, %s)"
                sucesso, msg = db.run_command(sql, (nome, cap, tipo))
                if sucesso:
                    st.success("Sala cadastrada!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Erro: {msg}")

    st.write("### Salas Existentes")
    df_salas = db.run_query("SELECT * FROM tb_salas ORDER BY nome")
    st.dataframe(df_salas, use_container_width=True)

# --- 3. GERENCIAR DOCENTES ---
elif menu == "Docentes":
    st.subheader("👨‍🏫 Gestão de Docentes")
    
    col_form, col_grid = st.columns([1, 2])
    
    with col_form:
        st.write("#### Novo Docente")
        with st.form("form_prof"):
            nome_prof = st.text_input("Nome Completo")
            email_prof = st.text_input("E-mail (Opcional)")
            
            if st.form_submit_button("Cadastrar"):
                sql = "INSERT INTO tb_docentes (nome, email) VALUES (%s, %s)"
                sucesso, msg = db.run_command(sql, (nome_prof, email_prof))
                if sucesso:
                    st.success("Docente salvo!")
                    st.rerun()
                else: 
                    st.error(msg)
    
    with col_grid:
        st.write("#### Lista de Docentes")
        df_profs = db.run_query("SELECT * FROM tb_docentes ORDER BY nome")
        st.dataframe(df_profs, use_container_width=True, height=500)

# --- 4. CURSOS E TURMAS ---
elif menu == "Cursos & Turmas":
    tab1, tab2 = st.tabs(["Cursos", "Turmas"])
    
    with tab1:
        st.subheader("Lista de Cursos")
        df_cursos = db.run_query("SELECT * FROM tb_cursos ORDER BY nome")
        st.dataframe(df_cursos, use_container_width=True)
        
    with tab2:
        st.subheader("Turmas Cadastradas")
        sql_turmas = """
            SELECT t.identificacao, t.qtd_alunos, c.nome as curso_nome
            FROM tb_turmas t
            JOIN tb_cursos c ON t.id_curso = c.id_curso
            ORDER BY c.nome, t.identificacao
        """
        df_turmas = db.run_query(sql_turmas)
        st.dataframe(df_turmas, use_container_width=True)

# --- 5. VISÃO DA GRADE (ALOCAÇÕES) ---
elif menu == "Alocações (Grade)":
    st.subheader("📅 Grade Horária Geral")
    
    dia_filtro = st.selectbox("Filtrar por Dia:", 
        ["Todos", "Segunda", "Terca", "Quarta", "Quinta", "Sexta", "Sabado"])
    
    sql_grade = """
        SELECT 
            a.dia_semana,
            s.nome AS sala,
            prof.nome AS professor,
            d.nome AS disciplina,
            STRING_AGG(t.identificacao, ' + ') AS turmas,
            CASE 
                WHEN SUM(t.qtd_alunos) > s.capacidade THEN '🔴 LOTADO'
                ELSE '🟢 OK'
            END AS status
        FROM tb_alocacoes a
        JOIN tb_salas s ON a.id_sala = s.id_sala
        JOIN tb_docentes prof ON a.id_docente = prof.id_docente
        JOIN tb_disciplinas d ON a.id_disciplina = d.id_disciplina
        JOIN tb_alocacao_turmas atur ON a.id_alocacao = atur.id_alocacao
        JOIN tb_turmas t ON atur.id_turma = t.id_turma
    """
    
    if dia_filtro != "Todos":
        sql_grade += f" WHERE a.dia_semana = '{dia_filtro}'"
        
    sql_grade += " GROUP BY a.id_alocacao, a.dia_semana, s.nome, s.capacidade, prof.nome, d.nome ORDER BY s.nome"
    
    df_grade = db.run_query(sql_grade)
    st.dataframe(df_grade, use_container_width=True)


# --- 6. NOVA ALOCAÇÃO (CORAÇÃO DO SISTEMA) ---
elif menu == "Nova Alocação":
    st.subheader("📝 Agendar Nova Aula")
    
    # Listas básicas
    df_profs = db.run_query("SELECT id_docente, nome FROM tb_docentes ORDER BY nome")
    df_cursos = db.run_query("SELECT id_curso, nome FROM tb_cursos ORDER BY nome")
    
    # --- Passo 1: Quando? ---
    st.info("1️⃣ Selecione o horário para verificarmos a disponibilidade.")
    c_dia, c_turno = st.columns(2)
    dia = c_dia.selectbox("Dia da Semana", ["Segunda", "Terca", "Quarta", "Quinta", "Sexta", "Sabado"])
    turno = c_turno.selectbox("Turno", ["Noturno", "Matutino", "Vespertino"])
    
    # --- VALIDAÇÃO EM TEMPO REAL ---
    df_salas = db.run_query("SELECT id_sala, nome, capacidade FROM tb_salas ORDER BY nome")
    sql_ocupadas = f"SELECT id_sala FROM tb_alocacoes WHERE dia_semana = '{dia}' AND turno = '{turno}'"
    df_ocupadas = db.run_query(sql_ocupadas)
    
    lista_ids_ocupados = []
    if not df_ocupadas.empty:
        lista_ids_ocupados = df_ocupadas['id_sala'].tolist()
    
    sala_options = {}
    primeira_livre = None
    
    for index, row in df_salas.iterrows():
        id_s = row['id_sala']
        nome_s = row['nome']
        cap_s = row['capacidade']
        
        if id_s in lista_ids_ocupados:
            label = f"🚫 {nome_s} (OCUPADA - {cap_s} lug.)"
        else:
            label = f"✅ {nome_s} (Livre - {cap_s} lug.)"
            if primeira_livre is None: primeira_livre = label
            
        sala_options[label] = id_s
    
    st.markdown("---")
    
    # --- Passo 2: Onde? ---
    st.write("2️⃣ Escolha a Sala")
    
    # Tenta focar na primeira livre
    idx_padrao = list(sala_options.keys()).index(primeira_livre) if primeira_livre else 0
    sala_label = st.selectbox("Salas Disponíveis:", list(sala_options.keys()), index=idx_padrao)
    id_sala_selecionada = sala_options[sala_label]
    
    sala_esta_ocupada = "🚫" in sala_label
    if sala_esta_ocupada:
        st.error("⚠️ Atenção: Esta sala JÁ ESTÁ OCUPADA neste horário!")

    # --- Passo 3: O Quê e Quem? ---
    st.markdown("---")
    st.write("3️⃣ Detalhes da Aula")
    
    col_curso, col_disc = st.columns(2)
    
    # Filtro Dinâmico de Disciplinas
    curso_filtro = col_curso.selectbox("Filtrar por Curso:", df_cursos['nome'])
    
    # CORREÇÃO CRÍTICA DO NUMPY INT64:
    # Usamos int() para converter o valor do pandas antes de usar no filtro
    id_curso_filtro = int(df_cursos[df_cursos['nome'] == curso_filtro]['id_curso'].values[0])
    
    df_disc = db.run_query(f"SELECT id_disciplina, nome FROM tb_disciplinas WHERE id_curso = {id_curso_filtro} ORDER BY nome")
    
    disc_dict = {row['nome']: row['id_disciplina'] for i, row in df_disc.iterrows()}
    
    if not disc_dict:
        st.warning("Nenhuma disciplina encontrada para este curso.")
        disc_nome = None
    else:
        disc_nome = col_disc.selectbox("Disciplina", list(disc_dict.keys()))
    
    id_disc_selecionada = disc_dict.get(disc_nome) if disc_nome else None
    
    c_prof, c_mod = st.columns(2)
    prof_dict = {row['nome']: row['id_docente'] for i, row in df_profs.iterrows()}
    prof_nome = c_prof.selectbox("Docente", list(prof_dict.keys()))
    id_prof = prof_dict[prof_nome]
    
    mod = c_mod.selectbox("Modalidade", ["Presencial", "Hibrido", "Semipresencial", "EAD"])

    # --- Passo 4: Turmas (Multi-Select) ---
    st.markdown("---")
    st.write("4️⃣ Turmas Participantes")
    
    sql_turmas = """
        SELECT t.id_turma, t.identificacao, c.nome as curso, t.qtd_alunos
        FROM tb_turmas t JOIN tb_cursos c ON t.id_curso = c.id_curso
        ORDER BY c.nome, t.identificacao
    """
    df_turmas = db.run_query(sql_turmas)
    
    turmas_dict = {}
    for i, row in df_turmas.iterrows():
        label = f"{row['identificacao']} | {row['curso']} ({row['qtd_alunos']} alunos)"
        turmas_dict[label] = row['id_turma']
        
    turmas_labels = st.multiselect("Selecione uma ou mais turmas:", list(turmas_dict.keys()))
    ids_turmas = [turmas_dict[l] for l in turmas_labels]
    
    # --- Botão de Salvar ---
    st.markdown("---")
    bloqueado = sala_esta_ocupada or not ids_turmas or not id_disc_selecionada
    
    if st.button("💾 Confirmar Alocação", type="primary", disabled=bloqueado):
        dados = {
            'dia': dia, 'turno': turno, 'modalidade': mod,
            'id_sala': id_sala_selecionada, 'id_docente': id_prof,
            'id_disciplina': id_disc_selecionada
        }
        sucesso, msg = db.criar_alocacao_completa(dados, ids_turmas)
        if sucesso:
            st.success(msg)
            st.balloons()
            time.sleep(2)
            st.rerun()
        else:
            st.error(msg)
            
    if sala_esta_ocupada:
        st.warning("Escolha uma sala livre (✅) para liberar o botão.")

# --- 7. GERENCIAR GRADE (EXCLUIR) ---
elif menu == "Gerenciar Grade":
    st.subheader("⚙️ Gerenciamento da Grade")
    
    tab_del, tab_exp = st.tabs(["🗑️ Excluir Aulas", "📥 Exportar Relatórios"])
    
    with tab_del:
        st.warning("Cuidado: A exclusão é permanente.")
        filtro_dia = st.selectbox("Filtrar Dia para Exclusão", ["Todos", "Segunda", "Terca", "Quarta", "Quinta", "Sexta"])
        
        sql_lista = """
            SELECT 
                a.id_alocacao, a.dia_semana, s.nome AS sala, d.nome AS disciplina, 
                prof.nome AS professor, STRING_AGG(t.identificacao, ', ') AS turmas
            FROM tb_alocacoes a
            JOIN tb_salas s ON a.id_sala = s.id_sala
            JOIN tb_docentes prof ON a.id_docente = prof.id_docente
            JOIN tb_disciplinas d ON a.id_disciplina = d.id_disciplina
            JOIN tb_alocacao_turmas atur ON a.id_alocacao = atur.id_alocacao
            JOIN tb_turmas t ON atur.id_turma = t.id_turma
        """
        if filtro_dia != "Todos":
            sql_lista += f" WHERE a.dia_semana = '{filtro_dia}'"
            
        sql_lista += " GROUP BY a.id_alocacao, a.dia_semana, s.nome, d.nome, prof.nome ORDER BY a.dia_semana, s.nome"
        
        df_aulas = db.run_query(sql_lista)
        
        if not df_aulas.empty:
            st.dataframe(df_aulas, use_container_width=True)
            
            lista_opcoes = {}
            for index, row in df_aulas.iterrows():
                label = f"ID {row['id_alocacao']} | {row['dia_semana']} | {row['sala']} | {row['disciplina']}"
                lista_opcoes[label] = row['id_alocacao']
            
            escolha = st.selectbox("Escolha a aula para remover:", list(lista_opcoes.keys()))
            id_para_deletar = lista_opcoes[escolha]
            
            if st.button("🗑️ Confirmar Exclusão", type="primary"):
                sucesso, msg = db.deletar_alocacao(id_para_deletar)
                if sucesso:
                    st.success("Aula removida!")
                    st.rerun()
                else:
                    st.error(msg)
        else:
            st.info("Nenhuma aula encontrada.")

    with tab_exp:
        st.write("Baixe a grade completa.")
        # Reutilizamos a query de grade completa
        sql_relatorio = "SELECT * FROM tb_alocacoes" # Simplificado para teste, pode usar a query completa
        df_export = db.run_query("SELECT * FROM tb_alocacoes")
        csv = df_export.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar CSV", data=csv, file_name='grade.csv', mime='text/csv')

# --- 8. CALENDÁRIO VISUAL ---
elif menu == "Calendário Visual":
    st.subheader("🗓️ Visão Semanal Interativa")
    
    eventos_calendario = db.get_dados_calendario()
    
    calendar_options = {
        "editable": False,
        "navLinks": True,
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "timeGridWeek,dayGridMonth"
        },
        "initialView": "timeGridWeek",
        "slotMinTime": "07:00:00",
        "slotMaxTime": "23:00:00",
        "allDaySlot": False,
        "locale": "pt-br",
    }
    
    calendar(events=eventos_calendario, options=calendar_options)