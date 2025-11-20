"""Script para testar webhook de licença criada."""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"


def test_webhook_licenca_criada():
    """Testa o webhook de licença criada."""
    url = f"{BASE_URL}/api/webhooks/licenca-criada"
    
    payload = {
        "evento": "licenca-criada",
        "portal_id": "LIC-TEST-001",
        "cliente_email": "teste.webhook@example.com",
        "cliente_telefone": "5511999999999",
        "tipo_licenca": "Hub",
        "dados_extras": {
            "nome": "Cliente Teste Webhook",
            "empresa": "Empresa Teste"
        }
    }
    
    print("Enviando webhook de licença criada...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        print("✅ Sucesso!")
        print(json.dumps(result, indent=2))
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Resposta: {e.response.text}")
        return None


if __name__ == "__main__":
    print("=" * 50)
    print("Teste de Webhook - Licença Criada")
    print("=" * 50)
    print()
    
    result = test_webhook_licenca_criada()
    
    if result:
        print()
        print("=" * 50)
        print("Próximos passos:")
        print("1. Verifique se o cliente foi criado:")
        print(f"   curl {BASE_URL}/api/clientes")
        print()
        print("2. Verifique se a licença foi criada:")
        print(f"   curl {BASE_URL}/api/licencas")
        print()
        print("3. Verifique se a mensagem foi enviada:")
        print(f"   curl {BASE_URL}/api/mensagens")
        print("=" * 50)
    else:
        sys.exit(1)

