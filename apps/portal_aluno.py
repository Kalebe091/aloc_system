import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime

# Adiciona a pasta raiz do projeto ao Python para ele achar a pasta 'database'
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

# Agora importamos do novo local renomeado, mas chamamos de 'db' para não quebrar o resto do código
from database import db_connection as db 

# Configuração da página para parecer um app mobile
st.set_page_config(page_title="Minha Grade - Anhanguera", page_icon="🎓", layout="centered")

# CSS para deixar bonito no celular
st.markdown("""
    <style>
    .stSelectbox { margin-bottom: 20px; }
    .aula-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 10px;
    }
    .aula-header { font-size: 18px; font-weight: bold; color: #31333F; }
    .aula-info { font-size: 14px; color: #555; }
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
    </style>
""", unsafe_allow_html=True)

st.title("🎓 Portal do Aluno")
st.write("Consulte sua sala e horários da semana.")

# --- FILTROS DE SELEÇÃO ---
st.info("👇 Selecione seu curso e turma para ver a grade.")

# 1. Selecionar Curso
df_cursos = db.run_query("SELECT id_curso, nome FROM tb_cursos ORDER BY nome")
curso_nomes = df_cursos['nome'].tolist()
curso_selecionado = st.selectbox("Selecione seu Curso:", [""] + curso_nomes)

if curso_selecionado:
    # Pega o ID do curso
    id_curso = int(df_cursos[df_cursos['nome'] == curso_selecionado]['id_curso'].values[0])
    
    # 2. Selecionar Turma (Baseado no curso)
    df_turmas = db.get_turmas_por_curso(id_curso)
    
    if not df_turmas.empty:
        turma_dict = {row['identificacao']: row['id_turma'] for i, row in df_turmas.iterrows()}
        turma_nome = st.selectbox("Selecione sua Turma/Semestre:", [""] + list(turma_dict.keys()))
        
        if turma_nome:
            id_turma = turma_dict[turma_nome]
            
            # --- MOSTRAR A GRADE ---
            st.markdown("---")
            st.subheader(f"📅 Grade Semanal: {turma_nome}")
            
            df_grade = db.get_grade_do_aluno(id_turma)
            
            if df_grade.empty:
                st.warning("Nenhuma aula cadastrada para esta turma ainda.")
            else:
                # Organizar por abas (Dias da Semana)
                dias_disponiveis = df_grade['dia_semana'].unique().tolist()
                tabs = st.tabs(dias_disponiveis)
                
                # Para cada aba (Dia), mostramos os Cards das aulas
                for i, dia in enumerate(dias_disponiveis):
                    with tabs[i]:
                        # Filtra as aulas daquele dia
                        aulas_dia = df_grade[df_grade['dia_semana'] == dia]
                        
                        for _, aula in aulas_dia.iterrows():
                            # Define a cor da tag
                            cor_tag = "tag-online" if aula['modalidade'] in ['EAD', 'Semipresencial'] else "tag-presencial"
                            
                            # HTML do Card
                            st.markdown(f"""
                            <div class="aula-card">
                                <div class="aula-header">{aula['disciplina']}</div>
                                <div style="margin: 5px 0;">
                                    <span class="tag {cor_tag}">{aula['modalidade']}</span>
                                    <span class="tag" style="background:#eee;">{aula['turno']}</span>
                                </div>
                                <div class="aula-info">
                                    📍 <b>Sala:</b> {aula['sala']} <br>
                                    👨‍🏫 <b>Prof:</b> {aula['professor']}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
    else:
        st.warning("Não há turmas cadastradas para este curso.")

# Rodapé
st.markdown("---")
st.caption("Sistema de Gestão Acadêmica - Faculdade Anhanguera")