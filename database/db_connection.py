import psycopg2
import pandas as pd
import streamlit as st
import bcrypt
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import os
import toml

# ==============================================================================
# 1. CONFIGURAÇÃO E CONEXÃO
# ==============================================================================

# Configuração Padrão (Fallback para Localhost sem Nuvem)
# Evita o erro 'DB_CONFIG not defined'
DB_CONFIG = {
    "dbname": "sga_anhanguera",
    "user": "postgres",
    "password": "admin",
    "host": "localhost",
    "port": "5432"
}

def carregar_url_banco():
    """
    Tenta encontrar a URL de conexão (Neon) em 2 lugares:
    1. Segredos do Streamlit (Cloud).
    2. Arquivo secrets.toml local (VS Code).
    """
    url = None
    
    # Tentativa A: Streamlit Cloud
    try:
        if "POSTGRES_URL" in st.secrets:
            url = st.secrets["POSTGRES_URL"]
    except:
        pass 

    # Tentativa B: Arquivo local secrets.toml
    if not url:
        try:
            base_path = os.path.dirname(os.path.dirname(__file__))
            secrets_path = os.path.join(base_path, ".streamlit", "secrets.toml")
            if os.path.exists(secrets_path):
                data = toml.load(secrets_path)
                if "POSTGRES_URL" in data:
                    url = data["POSTGRES_URL"]
        except Exception:
            pass # Falha silenciosa se não achar arquivo local

    return url

# Lógica de Inicialização da Engine
DATABASE_URL_RAW = carregar_url_banco()

if DATABASE_URL_RAW:
    # Ajuste para SQLAlchemy (postgres:// -> postgresql://)
    SQLALCHEMY_URL = DATABASE_URL_RAW.replace("postgres://", "postgresql://", 1)
else:
    # URL Local
    SQLALCHEMY_URL = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

# Cria a Engine Global (Pandas)
engine = create_engine(SQLALCHEMY_URL)

def get_connection():
    """Retorna uma conexão crua (psycopg2) para INSERT/UPDATE."""
    try:
        if DATABASE_URL_RAW:
            return psycopg2.connect(DATABASE_URL_RAW)
        else:
            return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ Erro de Conexão: {e}")
        return None

# ==============================================================================
# 2. FUNÇÕES BASE (LEITURA E ESCRITA)
# ==============================================================================

def run_query(query, params=None):
    """Executa SELECT e retorna DataFrame."""
    try:
        with engine.connect() as conn:
            return pd.read_sql(query, conn, params=params)
    except Exception as e:
        st.error(f"Erro na consulta SQL: {e}")
        return pd.DataFrame()

def run_command(command, params=None):
    """Executa INSERT, UPDATE, DELETE."""
    conn = get_connection()
    if not conn:
        return False, "Sem conexão com o banco."
    
    try:
        cur = conn.cursor()
        cur.execute(command, params)
        conn.commit()
        cur.close()
        return True, "Sucesso!"
    except Exception as e:
        return False, str(e)
    finally:
        if conn: conn.close()

# ==============================================================================
# 3. AUTENTICAÇÃO (LOGIN)
# ==============================================================================

def verificar_login(usuario, senha_digitada):
    sql = "SELECT senha_hash, nome FROM tb_usuarios WHERE usuario = %s"
    df = run_query(sql, params=(usuario,))
    
    if df.empty:
        return False, None
    
    hash_banco = df.iloc[0]['senha_hash']
    nome_usuario = df.iloc[0]['nome']
    
    senha_bytes = senha_digitada.encode('utf-8')
    
    if isinstance(hash_banco, str):
        hash_bytes = hash_banco.encode('utf-8')
    else:
        hash_bytes = hash_banco
    
    if bcrypt.checkpw(senha_bytes, hash_bytes):
        return True, nome_usuario
    else:
        return False, None

# ==============================================================================
# 4. GESTÃO DE ALOCAÇÕES (TRANSAÇÕES)
# ==============================================================================

def criar_alocacao_completa(dados_aula, lista_ids_turmas):
    conn = get_connection()
    if not conn: return False, "Erro de conexão"
    
    cursor = conn.cursor()
    try:
        # 1. Inserir Aula Principal
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
        
        # 2. Inserir Vínculos com Turmas
        sql_vinculo = "INSERT INTO tb_alocacao_turmas (id_alocacao, id_turma) VALUES (%s, %s)"
        for id_turma in lista_ids_turmas:
            cursor.execute(sql_vinculo, (id_gerado, id_turma))
            
        conn.commit()
        return True, "Alocação realizada com sucesso!"
    except Exception as e:
        conn.rollback()
        return False, f"Erro na transação: {str(e)}"
    finally:
        cursor.close()
        conn.close()

def deletar_alocacao(id_alocacao):
    sql = "DELETE FROM tb_alocacoes WHERE id_alocacao = %s"
    return run_command(sql, (id_alocacao,))

# ==============================================================================
# 5. CALENDÁRIO VISUAL
# ==============================================================================

def get_dados_calendario():
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
    map_dias = {'Segunda': 0, 'Terca': 1, 'Quarta': 2, 'Quinta': 3, 'Sexta': 4, 'Sabado': 5}
    map_horarios = {
        'Matutino': {'start': '08:00:00', 'end': '11:30:00'},
        'Vespertino': {'start': '14:00:00', 'end': '17:30:00'},
        'Noturno': {'start': '19:00:00', 'end': '22:00:00'}
    }
    
    hoje = datetime.now()
    inicio_semana = hoje - timedelta(days=hoje.weekday()) 
    
    if not df.empty:
        for _, row in df.iterrows():
            if row['dia_semana'] in map_dias and row['turno'] in map_horarios:
                delta = map_dias[row['dia_semana']]
                data_ev = (inicio_semana + timedelta(days=delta)).strftime('%Y-%m-%d')
                hrs = map_horarios[row['turno']]
                
                event = {
                    "title": f"{row['sala']} | {row['professor']}",
                    "start": f"{data_ev}T{hrs['start']}",
                    "end": f"{data_ev}T{hrs['end']}",
                    "resourceId": row['sala'],
                    "extendedProps": {
                        "disciplina": row['disciplina'],
                        "capacidade": row['capacidade']
                    },
                    "backgroundColor": "#FF4B4B" if row['turno'] == 'Noturno' else "#3DD56D" if row['turno'] == 'Matutino' else "#FFC107"
                }
                events.append(event)
    return events

# ==============================================================================
# 6. PORTAIS (ALUNO E DOCENTE)
# ==============================================================================

def get_turmas_por_curso(id_curso):
    sql = "SELECT id_turma, identificacao FROM tb_turmas WHERE id_curso = %s ORDER BY identificacao"
    return run_query(sql, params=(id_curso,))

def get_grade_do_aluno(id_turma):
    sql = """
        SELECT 
            a.dia_semana, a.turno, a.modalidade,
            s.nome AS sala, s.tipo AS tipo_sala,
            d.nome AS disciplina, prof.nome AS professor
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
            END, a.turno
    """
    return run_query(sql, params=(id_turma,))

def get_grade_do_professor(id_docente):
    sql = """
        SELECT 
            a.dia_semana, a.turno, a.modalidade,
            s.nome AS sala, s.tipo AS tipo_sala,
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
            END, a.turno
    """
    return run_query(sql, params=(id_docente,))