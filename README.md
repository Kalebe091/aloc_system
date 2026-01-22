# 🏫 SGA - Sistema de Gestão de Alocação (Aloc System)

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge&logo=google%20gemini&logoColor=white)

Sistema completo desenvolvido em Python para o gerenciamento inteligente de alocação de salas de aula, horários e turmas universitárias. O projeto foca na resolução de conflitos de agendamento e oferece portais específicos para diferentes perfis de usuário.

## 🚀 Sobre o Projeto

O **Aloc System** foi projetado para resolver a complexidade logística de instituições de ensino. Diferente de planilhas estáticas, ele utiliza um banco de dados relacional robusto na nuvem para garantir integridade e acesso em tempo real.

### 🤖 Diferencial: AI-Powered Development
Este projeto foi desenvolvido utilizando **Engenharia Assistida por IA (Google Gemini)**. O modelo foi utilizado para:
* **Otimização de Algoritmos:** Lógica refinada para detecção de colisão de horários (sala/professor).
* **Arquitetura de Banco de Dados:** Modelagem SQL eficiente e normalizada.
* **Refatoração de Código:** Garantia de boas práticas e Clean Code.

## 🎯 Funcionalidades Principais

### 🔐 Painel Administrativo
- **Gestão Completa (CRUD):** Salas, Docentes, Cursos e Disciplinas.
- **Alocação Inteligente:** Sistema que impede automaticamente o agendamento de duas aulas na mesma sala ou com o mesmo professor no mesmo horário.
- **Dashboard:** Métricas visuais de ocupação e distribuição.
- **Grade Interativa:** Calendário visual para gestão de horários.

### 🎓 Portal do Aluno
- **Consulta Rápida:** Filtros por Curso, Semestre e Turma.
- **Design Responsivo:** Interface adaptada para acesso via celular.
- **Transparência:** Visualização clara de sala, professor e disciplina.

### 👨‍🏫 Portal do Docente
- **Grade Personalizada:** O professor vê apenas as suas aulas.
- **Agrupamento Inteligente:** Detecção automática de turmas unificadas (ex: Direito 9º e 10º semestre na mesma sala).

## 🛠️ Stack Tecnológica

* **Frontend & Interface:** [Streamlit](https://streamlit.io/)
* **Linguagem:** Python 3.11+
* **Banco de Dados:** PostgreSQL (Hospedado no [Neon Tech](https://neon.tech))
* **Inteligência & Code Assist:** Google Gemini
* **Bibliotecas Chave:**
    * `pandas` (Manipulação de dados)
    * `sqlalchemy` & `psycopg2` (Conexão e ORM)
    * `bcrypt` (Segurança e Criptografia de senhas)
    * `streamlit-calendar` (Componentes visuais)

## 📂 Estrutura do Projeto

```text
/aloc_system
├── .streamlit/         # Configurações e Segredos (Local)
├── apps/               # Módulos da Aplicação
│   ├── admin.py        # Painel do Administrador
│   ├── portal_aluno.py # Visão do Estudante
│   └── portal_docente.py # Visão do Professor
├── database/           # Núcleo do Backend
│   ├── db_connection.py # Gerenciador de Conexão Híbrida (Cloud/Local)
│   └── criar_usuario.py # Scripts de manutenção
├── assets/             # Recursos visuais
└── requirements.txt    # Dependências do projeto

```

## 📦 Como Rodar Localmente

1. **Clone o repositório:**
```bash
git clone [https://github.com/SEU_USUARIO/aloc_system.git](https://github.com/SEU_USUARIO/aloc_system.git)
cd aloc_system

```


2. **Crie um ambiente virtual (Opcional, mas recomendado):**
```bash
python -m venv venv
# No Windows:
.\venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

```


3. **Instale as dependências:**
```bash
pip install -r requirements.txt

```


4. **Configuração do Banco de Dados:**
* O sistema tenta conectar automaticamente ao **Neon Tech** se as credenciais estiverem configuradas.
* Caso contrário, ele busca um banco PostgreSQL local (`localhost`).
* Para configurar o acesso local ao banco da nuvem, crie um arquivo `.streamlit/secrets.toml` com sua URL de conexão.


5. **Execute a aplicação:**
Para rodar o painel administrativo:
```bash
streamlit run apps/admin.py

```



---

<div align="center">
<sub>Desenvolvido por Kalebe Vasconcelos com apoio de Google Gemini AI</sub>
</div>

```

```
