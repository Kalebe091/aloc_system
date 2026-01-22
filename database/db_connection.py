import psycopg2
import pandas as pd
import streamlit as st
import bcrypt
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA CONEXÃO ---
import psycopg2
import pandas as pd
import streamlit as st
import bcrypt
from sqlalchemy import create_engine
import os

# --- LÓGICA DE CONEXÃO HÍBRIDA (LOCAL vs NUVEM) ---

def get_db_url():
    """Retorna a URL de conexão, verificando se estamos na nuvem ou local."""
    
    # 1. Tenta pegar dos Segredos do Streamlit Cloud
    if "POSTGRES_URL" in st.secrets:
        url = st.secrets["POSTGRES_URL"]
        # Correção para SQLAlchemy (precisa ser postgresql://)
        return url.replace("postgres://", "postgresql://", 1)
    
    # 2. Se não achar segredos, tenta usar LOCALHOST (Fallback)
    else:
        # Ajuste aqui seus dados locais se precisar rodar no PC sem internet
        return "postgresql+psycopg2://postgres:admin@localhost:5432/sga_anhanguera"

# Cria a Engine do SQLAlchemy (usada pelo Pandas)
DATABASE_URL = get_db_url()
engine = create_engine(DATABASE_URL)

def get_connection():
    """Retorna uma conexão crua (psycopg2) para INSERT/UPDATE."""
    # O psycopg2 aceita a URL direta do Neon ou localhost
    if "POSTGRES_URL" in st.secrets:
        return psycopg2.connect(st.secrets["POSTGRES_URL"])
    else:
        # Conexão manual local
        return psycopg2.connect(
            dbname="sga_anhanguera",
            user="postgres",
            password="admin",
            host="localhost",
            port="5432"
        )

# --- FUNÇÕES DE LEITURA (IGUAIS AO ANTERIOR) ---
def run_query(query, params=None):
    try:
        with engine.connect() as conn:
            return pd.read_sql(query, conn, params=params)
    except Exception as e:
        st.error(f"Erro na consulta: {e}")
        return pd.DataFrame()

# --- FUNÇÕES DE ESCRITA (IGUAIS AO ANTERIOR) ---
def run_command(command, params=None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(command, params)
        conn.commit()
        cur.close()
        return True, "Sucesso!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()



# --- 2. CONEXÃO RAW (Para Escritas/Transações Manuais) ---
def get_connection():
    """Abre uma conexão crua (psycopg2) para INSERT/UPDATE/DELETE."""
    return psycopg2.connect(**DB_CONFIG)

# --- FUNÇÕES DE LEITURA (Usam SQLAlchemy para evitar o Warning) ---

def run_query(query, params=None):
    """
    Para LEITURA de dados (SELECT). 
    Usa SQLAlchemy Engine para agradar o Pandas e sumir com o Warning.
    """
    try:
        with engine.connect() as conn:
            # Pandas aceita params, mas precisa ser lista/tupla
            df = pd.read_sql(query, conn, params=params)
            return df
    except Exception as e:
        st.error(f"Erro na consulta: {e}")
        return pd.DataFrame() # Retorna vazio em caso de erro

# --- FUNÇÕES DE ESCRITA (Mantemos psycopg2 para controle total) ---

def run_command(command, params=None):
    """Para ESCRITA de dados (INSERT, UPDATE, DELETE). Retorna Sucesso/Erro."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(command, params)
        conn.commit()
        cur.close()
        return True, "Comando executado com sucesso!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# --- AUTENTICAÇÃO ---

def verificar_login(usuario, senha_digitada):
    """
    Retorna (True, Nome) se a senha estiver correta.
    """
    # to match your PostgreSQL table structure.
    sql = "SELECT senha_hash, nome FROM tb_usuarios WHERE usuario = %s"
    
    # Using run_query to handle the connection safely
    df = run_query(sql, params=(usuario,))
    
    if df.empty:
        return False, None
    
    # Retrieve the hash from the correct column 'senha_hash'
    hash_banco = df.iloc[0]['senha_hash']
    nome_usuario = df.iloc[0]['nome']
    
    # Encode inputs to bytes for bcrypt
    senha_bytes = senha_digitada.encode('utf-8')
    
    # Ensure the hash from DB is also bytes (it might come as string)
    if isinstance(hash_banco, str):
        hash_bytes = hash_banco.encode('utf-8')
    else:
        hash_bytes = hash_banco # Assuming it's already bytes/memoryview
    
    # Verify password
    if bcrypt.checkpw(senha_bytes, hash_bytes):
        return True, nome_usuario
    else:
        return False, None

# --- TRANSAÇÕES COMPLEXAS (ALOCAÇÃO) ---

def criar_alocacao_completa(dados_aula, lista_ids_turmas):
    """
    Realiza uma TRANSAÇÃO no banco (INSERT em 2 tabelas ao mesmo tempo).
    Usa psycopg2 (get_connection) para ter controle de COMMIT/ROLLBACK.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Inserir a Aula Principal
        sql_aula = """
            INSERT INTO tb_alocacoes (dia_semana, turno, modalidade, id_sala, id_docente, id_disciplina)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id_alocacao;
        """
        cursor.execute(sql_aula, (
            dados_aula['dia'], dados_aula['turno'], dados_aula['modalidade'],
            dados_aula['id_sala'], dados_aula['id_docente'], dados_aula['id_disciplina']
        ))
        
        id_gerado = cursor.fetchone()[0]
        
        # 2. Inserir os vínculos com as turmas
        sql_vinculo = "INSERT INTO tb_alocacao_turmas (id_alocacao, id_turma) VALUES (%s, %s)"
        for id_turma in lista_ids_turmas:
            cursor.execute(sql_vinculo, (id_gerado, id_turma))
            
        conn.commit()
        return True, "Alocação realizada com sucesso!"
        
    except Exception as e:
        conn.rollback() # Cancela tudo se der erro
        return False, f"Erro na transação: {str(e)}"
        
    finally:
        cursor.close()
        conn.close()

def deletar_alocacao(id_alocacao):
    """Remove uma alocação."""
    sql = "DELETE FROM tb_alocacoes WHERE id_alocacao = %s"
    return run_command(sql, (id_alocacao,))

# --- CALENDÁRIO ---

def get_dados_calendario():
    """
    Busca as aulas e converte para o formato do Calendário.
    """
    # Usa run_query (SQLAlchemy) para leitura limpa
    sql = """
        SELECT 
            a.id_alocacao, a.dia_semana, a.turno,
            s.nome AS sala, prof.nome AS professor,
            d.nome AS disciplina, s.capacidade
        FROM tb_alocacoes a
        JOIN tb_salas s ON a.id_sala = s.id_sala
        JOIN tb_docentes prof ON a.id_docente = prof.id_docente
        JOIN tb_disciplinas d ON a.id_disciplina = d.id_disciplina
    """
    df = run_query(sql)
    
    events = []
    
    # Mapeamentos
    map_dias = {'Segunda': 0, 'Terca': 1, 'Quarta': 2, 'Quinta': 3, 'Sexta': 4, 'Sabado': 5}
    map_horarios = {
        'Matutino': {'start': '08:00:00', 'end': '11:30:00'},
        'Vespertino': {'start': '14:00:00', 'end': '17:30:00'},
        'Noturno': {'start': '19:00:00', 'end': '22:00:00'}
    }
    
    hoje = datetime.now()
    inicio_semana = hoje - timedelta(days=hoje.weekday()) 
    
    if not df.empty:
        for index, row in df.iterrows():
            if row['dia_semana'] in map_dias and row['turno'] in map_horarios:
                delta_dias = map_dias[row['dia_semana']]
                data_evento = (inicio_semana + timedelta(days=delta_dias)).strftime('%Y-%m-%d')
                
                horarios = map_horarios[row['turno']]
                
                event = {
                    "title": f"{row['sala']} | {row['professor']}",
                    "start": f"{data_evento}T{horarios['start']}",
                    "end": f"{data_evento}T{horarios['end']}",
                    "resourceId": row['sala'],
                    "extendedProps": {
                        "disciplina": row['disciplina'],
                        "capacidade": row['capacidade']
                    },
                    "backgroundColor": "#FF4B4B" if row['turno'] == 'Noturno' else "#3DD56D" if row['turno'] == 'Matutino' else "#FFC107",
                    "borderColor": "#ffffff"
                }
                events.append(event)
            
    return events

# --- FUNÇÕES PARA O PORTAL DO ALUNO ---

def get_turmas_por_curso(id_curso):
    """Retorna as turmas de um curso específico para o dropdown."""
    sql = "SELECT id_turma, identificacao FROM tb_turmas WHERE id_curso = %s ORDER BY identificacao"
    return run_query(sql, params=(id_curso,))

def get_grade_do_aluno(id_turma):
    """
    Busca todas as aulas de uma turma específica.
    Faz o JOIN reverso: Turma -> Alocacao_Turma -> Alocacao -> Sala/Prof/Disc
    """
    sql = """
        SELECT 
            a.dia_semana,
            a.turno,
            a.modalidade,
            s.nome AS sala,
            s.tipo AS tipo_sala,
            d.nome AS disciplina,
            prof.nome AS professor
        FROM tb_alocacoes a
        JOIN tb_alocacao_turmas atur ON a.id_alocacao = atur.id_alocacao
        JOIN tb_salas s ON a.id_sala = s.id_sala
        JOIN tb_disciplinas d ON a.id_disciplina = d.id_disciplina
        JOIN tb_docentes prof ON a.id_docente = prof.id_docente
        WHERE atur.id_turma = %s
        ORDER BY 
            CASE 
                WHEN a.dia_semana = 'Segunda' THEN 1
                WHEN a.dia_semana = 'Terca' THEN 2
                WHEN a.dia_semana = 'Quarta' THEN 3
                WHEN a.dia_semana = 'Quinta' THEN 4
                WHEN a.dia_semana = 'Sexta' THEN 5
                WHEN a.dia_semana = 'Sabado' THEN 6
            END,
            a.turno
    """
    return run_query(sql, params=(id_turma,))

def get_grade_do_professor(id_docente):
    """
    Busca a grade horária de um professor específico.
    Usa STRING_AGG para juntar as turmas caso seja uma sala unificada.
    """
    sql = """
        SELECT 
            a.dia_semana,
            a.turno,
            a.modalidade,
            s.nome AS sala,
            s.tipo AS tipo_sala,
            d.nome AS disciplina,
            STRING_AGG(t.identificacao, ' + ') AS turmas_unificadas
        FROM tb_alocacoes a
        JOIN tb_salas s ON a.id_sala = s.id_sala
        JOIN tb_disciplinas d ON a.id_disciplina = d.id_disciplina
        JOIN tb_alocacao_turmas atur ON a.id_alocacao = atur.id_alocacao
        JOIN tb_turmas t ON atur.id_turma = t.id_turma
        WHERE a.id_docente = %s
        GROUP BY a.id_alocacao, a.dia_semana, a.turno, a.modalidade, s.nome, s.tipo, d.nome
        ORDER BY 
            CASE 
                WHEN a.dia_semana = 'Segunda' THEN 1
                WHEN a.dia_semana = 'Terca' THEN 2
                WHEN a.dia_semana = 'Quarta' THEN 3
                WHEN a.dia_semana = 'Quinta' THEN 4
                WHEN a.dia_semana = 'Sexta' THEN 5
                WHEN a.dia_semana = 'Sabado' THEN 6
            END,
            a.turno
    """
    return run_query(sql, params=(id_docente,))