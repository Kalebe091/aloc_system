import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime

# --- CONFIGURAÇÃO DE CAMINHOS ---
# Adiciona a pasta raiz do projeto ao Python para ele achar a pasta 'database'
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

# Agora importamos do novo local renomeado
from database import db_connection as db

# Configuração Mobile-First
st.set_page_config(page_title="Sou Docente - Anhanguera", page_icon="👨‍🏫", layout="centered")

# CSS Estilizado para Professores
st.markdown("""
    <style>
    .stSelectbox { margin-bottom: 25px; }
    
    /* Card da Aula */ 
    .prof-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 6px solid #2563eb; /* Azul Institucional */
    }
    
    /* Destaque para a Sala (Gigante) */
    .sala-badge {
        font-size: 24px;
        font-weight: 800;
        color: #2563eb;
        background-color: #eff6ff;
        padding: 5px 15px;
        border-radius: 8px;
        display: inline-block;
        margin-bottom: 10px;
    }
    
    .disciplina-title { font-size: 18px; font-weight: bold; color: #1f2937; margin-bottom: 5px; }
    .turma-info { font-size: 14px; color: #4b5563; display: flex; align-items: center; gap: 5px; }
    .turno-tag { 
        background-color: #f3f4f6; color: #374151; 
        padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

st.title("👨‍🏫 Portal do Docente")
st.warning("Aviso: esta aplicacao esta em testes e pode apresentar instabilidades.")
st.write("Bem-vindo(a)! Consulte sua alocação de salas.")

# --- SELEÇÃO DE PROFESSOR ---
df_profs = db.run_query("SELECT id_docente, nome FROM tb_docentes ORDER BY nome")
prof_nomes = df_profs['nome'].tolist()

prof_selecionado = st.selectbox("Quem é você?", [""] + prof_nomes, placeholder="Selecione seu nome na lista...")

if prof_selecionado:
    # Busca o ID
    id_prof = int(df_profs[df_profs['nome'] == prof_selecionado]['id_docente'].values[0])
    
    st.divider()
    
    # Busca a grade
    df_grade = db.get_grade_do_professor(id_prof)
    
    if df_grade.empty:
        st.info("📅 Nenhuma aula encontrada na sua grade para esta semana.")
    else:
        st.subheader(f"🗓️ Agenda Semanal: {prof_selecionado.split()[0]}")
        
        # Abas por dia da semana
        dias_na_grade = df_grade['dia_semana'].unique().tolist()
        tabs = st.tabs(dias_na_grade)
        
        for i, dia in enumerate(dias_na_grade):
            with tabs[i]:
                aulas_dia = df_grade[df_grade['dia_semana'] == dia]
                
                for _, row in aulas_dia.iterrows():
                    # Ícone baseado no turno
                    icone_turno = "🌙" if row['turno'] == 'Noturno' else "☀️" if row['turno'] == 'Matutino' else "🌤️"
                    
                    # CORREÇÃO: O HTML abaixo não pode ter espaços no início das linhas
                    st.markdown(f"""
<div class="prof-card">
    <div style="display:flex; justify-content:space-between; align-items:start;">
        <div class="sala-badge">🚪 {row['sala']}</div>
        <span class="turno-tag">{icone_turno} {row['turno']}</span>
    </div>
    <div class="disciplina-title">{row['disciplina']}</div>
    <div class="turma-info">
        🎓 <b>Turmas:</b> {row['turmas_unificadas']}
    </div>
    <div class="turma-info" style="margin-top:5px;">
        📍 <b>Tipo:</b> {row['modalidade']} ({row['tipo_sala']})
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.caption("🔒 Acesso restrito ao corpo docente - Anhanguera")