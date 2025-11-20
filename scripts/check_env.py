"""Script para verificar se as variáveis de ambiente estão configuradas."""
import sys
import os
from pathlib import Path

# Configura encoding UTF-8 para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Adiciona o diretório raiz ao path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import settings


def check_env():
    """Verifica se as variáveis de ambiente estão configuradas."""
    print("=" * 60)
    print("Verificação de Variáveis de Ambiente")
    print("=" * 60)
    print()
    
    errors = []
    warnings = []
    
    # MongoDB
    print("📊 MongoDB:")
    print(f"  URL: {settings.mongodb_url}")
    print(f"  Database: {settings.mongodb_db_name}")
    
    # Verifica se é MongoDB Atlas
    if "mongodb+srv://" in settings.mongodb_url:
        print("  ✅ Usando MongoDB Atlas")
        print("  💡 Dica: Verifique se seu IP está na whitelist do Atlas")
    elif "mongodb://" in settings.mongodb_url:
        print("  ✅ Usando MongoDB local")
    else:
        warnings.append("Formato de URL do MongoDB pode estar incorreto")
        print("  ⚠️  Formato de URL pode estar incorreto")
    print()
    
    # WhatsApp
    print("📱 WhatsApp Cloud API:")
    if not settings.whatsapp_phone_number_id or settings.whatsapp_phone_number_id == "":
        errors.append("WHATSAPP_PHONE_NUMBER_ID não configurado")
        print("  ❌ WHATSAPP_PHONE_NUMBER_ID: NÃO CONFIGURADO")
    else:
        print(f"  ✅ WHATSAPP_PHONE_NUMBER_ID: {settings.whatsapp_phone_number_id[:10]}...")
    
    if not settings.whatsapp_access_token or settings.whatsapp_access_token == "":
        errors.append("WHATSAPP_ACCESS_TOKEN não configurado")
        print("  ❌ WHATSAPP_ACCESS_TOKEN: NÃO CONFIGURADO")
    else:
        print(f"  ✅ WHATSAPP_ACCESS_TOKEN: {settings.whatsapp_access_token[:10]}...")
    
    if not settings.whatsapp_verify_token or settings.whatsapp_verify_token == "":
        warnings.append("WHATSAPP_VERIFY_TOKEN não configurado")
        print("  ⚠️  WHATSAPP_VERIFY_TOKEN: NÃO CONFIGURADO")
    else:
        print(f"  ✅ WHATSAPP_VERIFY_TOKEN: {settings.whatsapp_verify_token[:10]}...")
    
    print(f"  API URL: {settings.whatsapp_api_url}")
    print()
    
    # Aplicação
    print("⚙️  Aplicação:")
    print(f"  Host: {settings.api_host}")
    print(f"  Port: {settings.api_port}")
    print(f"  Environment: {settings.environment}")
    print()
    
    # Verificação do arquivo .env
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        print(f"✅ Arquivo .env encontrado em: {env_file}")
    else:
        print(f"⚠️  Arquivo .env não encontrado em: {env_file}")
        print("   Execute: cp .env.example .env")
        warnings.append("Arquivo .env não encontrado")
    print()
    
    # Resumo
    print("=" * 60)
    if errors:
        print("❌ ERROS ENCONTRADOS:")
        for error in errors:
            print(f"  - {error}")
        print()
        print("Configure as variáveis no arquivo .env e tente novamente.")
        if "mongodb+srv://" in settings.mongodb_url:
            print()
            print("💡 MongoDB Atlas detectado!")
            print("   Consulte GUIA_MONGODB_ATLAS.md para ajuda com configuração.")
        return 1
    elif warnings:
        print("⚠️  AVISOS:")
        for warning in warnings:
            print(f"  - {warning}")
        print()
        print("Algumas configurações podem estar faltando, mas a aplicação pode funcionar.")
        if "mongodb+srv://" in settings.mongodb_url:
            print()
            print("💡 MongoDB Atlas detectado!")
            print("   Verifique se seu IP está na whitelist do Atlas.")
        return 0
    else:
        print("✅ Todas as configurações estão corretas!")
        if "mongodb+srv://" in settings.mongodb_url:
            print()
            print("💡 MongoDB Atlas configurado!")
            print("   Certifique-se de que seu IP está na whitelist do Atlas.")
        return 0


if __name__ == "__main__":
    sys.exit(check_env())

