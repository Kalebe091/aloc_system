import bcrypt
import db_connection # Certifique-se que este arquivo está na mesma pasta

def criar_usuario_admin(usuario, senha_plana, nome):
    conn = db_connection.get_connection()
    if not conn:
        print("❌ Erro ao conectar no banco!")
        return

    cursor = conn.cursor()
    
    # 1. Gerar o Hash (Criptografia)
    bytes = senha_plana.encode('utf-8')
    salt = bcrypt.gensalt()
    hash_senha = bcrypt.hashpw(bytes, salt)
    
    # O hash precisa ser salvo como string no banco
    hash_str = hash_senha.decode('utf-8')
    
    try:
        # === CORREÇÃO AQUI ===
        # Ajustei os nomes das colunas para bater com o banco de dados (tb_usuarios)
        sql = "INSERT INTO tb_usuarios (usuario, senha_hash, nome) VALUES (%s, %s, %s)"
        
        cursor.execute(sql, (usuario, hash_str, nome))
        conn.commit()
        print(f"✅ Usuário '{usuario}' criado com sucesso!")
        
    except Exception as e:
        # Se der erro de chave duplicada (usuário já existe), avisa
        if "unique constraint" in str(e).lower():
             print(f"⚠️  O usuário '{usuario}' já existe!")
        else:
             print(f"❌ Erro: {e}")
    finally:
        conn.close()

# --- EXECUÇÃO ---
if __name__ == "__main__":
    # Cria o usuário admin padrão
    criar_usuario_admin("admin", "admin", "Kalebe Admin")