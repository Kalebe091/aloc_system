import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime

# Adiciona a pasta raiz do projeto ao Python para ele achar a pasta 'database'
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

# Importa o módulo de banco de dados
from database import db_connection as db 

# Configuração da página
st.set_page_config(page_title="Minha Grade - Anhanguera", page_icon="🎓", layout="centered")

# CSS para estilo mobile-friendly
st.markdown("""
    <style>
    .stSelectbox { margin-bottom: 20px; }
    .aula-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .aula-header { font-size: 18px; font-weight: bold; color: #31333F; }
    .aula-info { font-size: 14px; color: #555; margin-top: 5px;}
    .tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        margin-right: 5px;
    }
    .tag-presencial { background-color: #d1fae5; color: #065f46; }
    .tag-online { background-color: #dbeafe; color: #1e40af; }
    .tag-turno { background-color: #eee; color: #333; }
    </style>
""", unsafe_allow_html=True)

st.title("🎓 Portal do Aluno")
st.warning("Aviso: Esta aplicação está em testes e pode apresentar instabilidades.")
st.write("Consulte sua grade horária e sala de aula.")

# --- FILTROS DE SELEÇÃO ---
st.info("👇 Selecione seus dados abaixo:") 

# 1. Selecionar Curso
df_cursos = db.run_query("SELECT id_curso, nome FROM tb_cursos ORDER BY nome")
curso_nomes = df_cursos['nome'].tolist()
curso_selecionado = st.selectbox("Selecione seu Curso:", [""] + curso_nomes)

if curso_selecionado:
    # Pega o ID do curso
    id_curso = int(df_cursos[df_cursos['nome'] == curso_selecionado]['id_curso'].values[0])
    
    # 2. Selecionar Semestre (Busca apenas semestres que possuem turmas deste curso)
    query_semestres = """
        SELECT DISTINCT s.id_semestre, s.descricao 
        FROM tb_semestres s
        JOIN tb_turmas t ON t.id_semestre = s.id_semestre
        WHERE t.id_curso = %s
        ORDER BY s.id_semestre
    """
    df_semestres = db.run_query(query_semestres, params=(id_curso,))
    
    if not df_semestres.empty:
        semestre_dict = {row['descricao']: row['id_semestre'] for i, row in df_semestres.iterrows()}
        semestre_selecionado = st.selectbox("Selecione seu Semestre:", [""] + list(semestre_dict.keys()))

        if semestre_selecionado:
            id_semestre = semestre_dict[semestre_selecionado]

            # 3. Selecionar Turma (Filtrada por Curso e Semestre)
            query_turmas = """
                SELECT id_turma, identificacao 
                FROM tb_turmas 
                WHERE id_curso = %s AND id_semestre = %s
                ORDER BY identificacao
            """
            df_turmas = db.run_query(query_turmas, params=(id_curso, id_semestre))
            
            if not df_turmas.empty:
                turma_dict = {row['identificacao']: row['id_turma'] for i, row in df_turmas.iterrows()}
                turma_nome = st.selectbox("Selecione sua Turma:", [""] + list(turma_dict.keys()))
                
                if turma_nome:
                    id_turma = turma_dict[turma_nome]
                    
                    # --- MOSTRAR A GRADE ---
                    st.markdown("---")
                    st.subheader(f"📅 Grade: {turma_nome}")
                    st.caption(f"{curso_selecionado} - {semestre_selecionado}")
                    
                    df_grade = db.get_grade_do_aluno(id_turma)
                    
                    if df_grade.empty:
                        st.warning("Nenhuma aula encontrada para esta turma.")
                    else:
                        # Ordem correta dos dias
                        ordem_dias = ['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado']
                        # Filtra apenas dias que têm aula
                        dias_com_aula = [d for d in ordem_dias if d in df_grade['dia_semana'].unique()]
                        
                        # Cria as abas
                        tabs = st.tabs(dias_com_aula)
                        
                        for i, dia in enumerate(dias_com_aula):
                            with tabs[i]:
                                aulas_dia = df_grade[df_grade['dia_semana'] == dia]
                                
                                for _, aula in aulas_dia.iterrows():
                                    # Define estilos das tags
                                    mod = aula['modalidade']
                                    cor_tag = "tag-online" if mod in ['EAD', 'Híbrido'] else "tag-presencial"
                                    
                                    # Renderiza o Card
                                    st.markdown(f"""
                                    <div class="aula-card">
                                        <div class="aula-header">{aula['disciplina']}</div>
                                        <div style="margin: 8px 0;">
                                            <span class="tag {cor_tag}">{mod}</span>
                                            <span class="tag tag-turno">{aula['turno']}</span>
                                        </div>
                                        <div class="aula-info">
                                            📍 <b>Sala:</b> {aula['sala']} <br>
                                            👨‍🏫 <b>Prof:</b> {aula['professor']}
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
            else:
                st.warning("Nenhuma turma encontrada para este semestre.")
    else:
        st.warning("Não há turmas cadastradas para este curso ainda.")

# Rodapé
st.markdown("---")
st.caption("Sistema de Gestão Acadêmica - Faculdade Anhanguera")