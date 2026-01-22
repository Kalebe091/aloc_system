# 🏫 SGA - Sistema de Gestão de Alocação (Aloc System)

Sistema completo desenvolvido em Python e Streamlit para o gerenciamento inteligente de alocação de salas de aula, horários e turmas. O sistema resolve conflitos de agendamento e oferece portais específicos para Administração, Alunos e Corpo Docente.

## 🚀 Funcionalidades

### 🔐 Painel Administrativo
- **Gestão de Banco de Dados:** CRUD completo de Salas, Docentes, Cursos e Disciplinas.
- **Alocação Inteligente:** Algoritmo que detecta conflitos de horário e capacidade de sala em tempo real.
- **Visão Geral:** Dashboard com métricas de ocupação.
- **Grade Visual:** Calendário interativo para visualização de aulas.

### 🎓 Portal do Aluno
- Consulta rápida de horários filtrados por Turma/Semestre.
- Visualização mobile-first (adaptada para celular).

### 👨‍🏫 Portal do Docente
- Acesso exclusivo à grade horária do professor.
- Agrupamento de turmas unificadas.

## 🛠️ Tecnologias Utilizadas
- **Frontend:** Streamlit (Python)
- **Backend:** Python 3.x
- **Banco de Dados:** PostgreSQL (Compatível com Neon Tech)
- **Bibliotecas:** Pandas, SQLAlchemy, Psycopg2, Bcrypt.

## 📂 Estrutura do Projeto
```text
/aloc_system
├── apps/               # Aplicações (Admin, Aluno, Docente)
├── database/           # Conexão e Scripts SQL
├── assets/             # Imagens e Estilos
└── requirements.txt    # Dependências