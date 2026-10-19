import os
import sys

def test_connection():
    # Carrega .env se existir
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    
    if not os.path.exists(env_path):
        print("SUPABASE: falha na conexão")
        print("[MOTIVO] Arquivo .env não encontrado na raiz do projeto.")
        print("[AÇÃO] Crie o arquivo .env com SUPABASE_URL e SUPABASE_KEY.")
        sys.exit(1)
        
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        # Fallback de leitura manual simples sem dependência externa
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip("'\"")

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        print("SUPABASE: falha na conexão")
        print("[MOTIVO] Variáveis SUPABASE_URL ou SUPABASE_KEY não estão definidas no arquivo .env.")
        sys.exit(1)

    # Teste de conexão HTTPS REST no endpoint da API do Supabase
    try:
        import urllib.request
        import urllib.error

        # Faz requisição de verificação ao endpoint REST do Supabase
        # Endpoint padrão: /rest/v1/ (retorna status HTTP 200 com a OpenAPI spec se a chave for válida)
        url = f"{supabase_url.rstrip('/')}/rest/v1/"
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}"
        }

        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 204):
                print("SUPABASE: conexão estabelecida com sucesso")
                sys.exit(0)
            else:
                print("SUPABASE: falha na conexão")
                print(f"[MOTIVO] Resposta HTTP inesperada do servidor: {resp.status}")
                sys.exit(1)
    except urllib.error.HTTPError as e:
        if e.code in (200, 204):
            print("SUPABASE: conexão estabelecida com sucesso")
            sys.exit(0)
        else:
            print("SUPABASE: falha na conexão")
            print(f"[MOTIVO] Erro HTTP {e.code}: Verifique se SUPABASE_URL e SUPABASE_KEY estão corretos.")
            sys.exit(1)
    except Exception as e:
        print("SUPABASE: falha na conexão")
        print(f"[MOTIVO] Erro ao tentar conectar: {type(e).__name__}")
        sys.exit(1)

if __name__ == "__main__":
    test_connection()
