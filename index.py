import subprocess
import time
import sys
import os

# --- CONFIGURAÇÃO MANUAL DO PYTHON ---
# Caminho baseado nos seus logs anteriores. 
# O "r" antes das aspas serve para o Python aceitar as barras invertidas do Windows.
PYTHON_EXECUTABLE = r"C:\Users\TI\AppData\Local\Programs\Python\Python314\python.exe"

# Se o caminho acima não existir, tenta achar o padrão do sistema (fallback)
if not os.path.exists(PYTHON_EXECUTABLE):
    print(f"⚠️  Atenção: Não achei o Python em {PYTHON_EXECUTABLE}")
    print("Tentando usar o comando 'python' padrão do sistema...")
    PYTHON_EXECUTABLE = "python" # Tenta o comando global

# --- DIRETÓRIOS ---
base_dir = os.path.dirname(os.path.abspath(__file__))

apps = [
    (os.path.join(base_dir, "apps", "admin.py"), "8501"),
    (os.path.join(base_dir, "apps", "portal_aluno.py"), "8502"),
    (os.path.join(base_dir, "apps", "portal_docente.py"), "8503")
]

print("🚀 INICIANDO SGA (FORÇANDO PYTHON CORRETO)")
print(f"🐍 Usando Python: {PYTHON_EXECUTABLE}")
print("------------------------------------------------")

processes = []

try:
    for filename, port in apps:
        if not os.path.exists(filename):
            print(f"❌ ARQUIVO NÃO ENCONTRADO: {filename}")
            continue

        print(f"▶️  Subindo {os.path.basename(filename)} na porta {port}...")
        
        # Aqui usamos o PYTHON_EXECUTABLE que definimos lá em cima
        p = subprocess.Popen(
            [PYTHON_EXECUTABLE, "-m", "streamlit", "run", filename, "--server.port", port],
            cwd=base_dir
        )
        processes.append(p)
        time.sleep(2)

    print("\n✅ Todos os sistemas foram iniciados!")
    print("------------------------------------------------")
    
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n🛑 Encerrando...")
    for p in processes:
        p.terminate()