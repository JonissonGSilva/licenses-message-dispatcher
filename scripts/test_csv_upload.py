"""Script para testar upload de CSV."""
import requests
import sys
import os
import json

BASE_URL = "http://localhost:8000"
CSV_FILE = "exemplo_clientes.csv"


def test_csv_upload():
    """Testa upload de CSV."""
    url = f"{BASE_URL}/api/csv/upload"
    
    if not os.path.exists(CSV_FILE):
        print(f"❌ Arquivo CSV não encontrado: {CSV_FILE}")
        print("Certifique-se de que o arquivo existe no diretório raiz.")
        return None
    
    print("Enviando arquivo CSV...")
    print(f"URL: {url}")
    print(f"Arquivo: {CSV_FILE}")
    print("-" * 50)
    
    try:
        with open(CSV_FILE, "rb") as f:
            files = {"arquivo": (CSV_FILE, f, "text/csv")}
            response = requests.post(url, files=files)
            response.raise_for_status()
        
        result = response.json()
        print("✅ Sucesso!")
        print(f"Total de linhas: {result.get('total_linhas', 0)}")
        print(f"Clientes criados: {result.get('clientes_criados', 0)}")
        print(f"Erros: {len(result.get('erros', []))}")
        
        if result.get('erros'):
            print("\n⚠️  Erros encontrados:")
            for erro in result['erros']:
                print(f"  - {erro}")
        
        print("\n📊 Resumo:")
        print(json.dumps(result, indent=2, default=str))
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Resposta: {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return None


if __name__ == "__main__":
    import json
    
    print("=" * 50)
    print("Teste de Upload de CSV")
    print("=" * 50)
    print()
    
    result = test_csv_upload()
    
    if result:
        print()
        print("=" * 50)
        print("Próximos passos:")
        print("1. Liste os clientes criados:")
        print(f"   curl {BASE_URL}/api/clientes")
        print()
        print("2. Envie mensagens massivas:")
        print(f"   curl -X POST '{BASE_URL}/api/mensagens/enviar-massiva?tipo_licenca=Hub'")
        print("=" * 50)
    else:
        sys.exit(1)

