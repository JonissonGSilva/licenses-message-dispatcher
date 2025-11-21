"""Serviço de console para exibir informações de inicialização."""
import sys
from typing import Dict, Optional, Any
import httpx
from app.database import Database
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class StartupConsole:
    """Classe para exibir informações formatadas no console durante o startup."""
    
    @staticmethod
    def print_banner():
        """Exibe banner de inicialização."""
        banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     🚀 API Message Dispatcher - MVP                   ║
║                                                               ║
║     ✅ Deploy realizado com sucesso!                          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    @staticmethod
    def print_separator():
        """Exibe separador visual."""
        print("═" * 63)
    
    @staticmethod
    async def get_public_ip() -> Optional[str]:
        """Obtém o IP público da aplicação."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("https://api.ipify.org?format=json")
                if response.status_code == 200:
                    return response.json().get("ip")
        except Exception as e:
            logger.debug(f"Erro ao obter IP público: {e}")
            return None
    
    @staticmethod
    async def check_mongodb_status() -> Dict[str, Any]:
        """Verifica o status da conexão com MongoDB."""
        status = {
            "connected": False,
            "error": None,
            "database": None,
            "host": None
        }
        
        try:
            db = Database.get_database()
            if db is None:
                status["error"] = "Database não inicializado"
                return status
            
            # Testa conexão
            await db.command('ping')
            
            # Obtém informações do banco
            status["connected"] = True
            status["database"] = settings.mongodb_db_name
            
            # Extrai host da URL (sem credenciais)
            if "@" in settings.mongodb_url:
                host = settings.mongodb_url.split("@")[-1].split("/")[0]
                status["host"] = host
            else:
                status["host"] = settings.mongodb_url.split("//")[-1].split("/")[0]
            
        except Exception as e:
            status["error"] = str(e)
            logger.debug(f"Erro ao verificar MongoDB: {e}")
        
        return status
    
    @staticmethod
    def format_status_icon(status: bool) -> str:
        """Retorna ícone baseado no status."""
        return "✅" if status else "❌"
    
    @staticmethod
    def print_service_status(service_name: str, status: Dict[str, Any]):
        """Exibe status formatado de um serviço."""
        icon = StartupConsole.format_status_icon(status.get("connected", False))
        print(f"  {icon} {service_name}")
        
        if status.get("connected"):
            if status.get("host"):
                print(f"     Host: {status['host']}")
            if status.get("database"):
                print(f"     Database: {status['database']}")
        else:
            error = status.get("error", "Desconectado")
            print(f"     Erro: {error}")
    
    @staticmethod
    async def display_startup_info():
        """Exibe todas as informações de inicialização."""
        # Banner
        StartupConsole.print_banner()
        
        # Informações da aplicação
        print("📋 Informações da Aplicação:")
        print(f"  Versão: 1.0.0")
        print(f"  Ambiente: {settings.environment}")
        print(f"  Porta: {settings.api_port}")
        StartupConsole.print_separator()
        
        # Status dos serviços
        print("🔌 Status dos Serviços:")
        
        # MongoDB
        mongodb_status = await StartupConsole.check_mongodb_status()
        StartupConsole.print_service_status("MongoDB", mongodb_status)
        
        StartupConsole.print_separator()
        
        # IP Público
        print("🌐 Informações de Rede:")
        print("  Obtendo IP público...")
        public_ip = await StartupConsole.get_public_ip()
        
        if public_ip:
            print(f"  ✅ IP Público: {public_ip}")
            print()
            print("  💡 Adicione este IP na whitelist do MongoDB Atlas:")
            print(f"     MongoDB Atlas → Security → Network Access → Add IP: {public_ip}/32")
        else:
            print("  ⚠️  Não foi possível obter o IP público")
            print("  💡 Verifique manualmente o IP no MongoDB Atlas")
        
        StartupConsole.print_separator()
        
        # URLs
        print("🔗 Endpoints Disponíveis:")
        print(f"  • API: http://0.0.0.0:{settings.api_port}")
        print(f"  • Health Check: http://0.0.0.0:{settings.api_port}/health")
        print(f"  • Documentação: http://0.0.0.0:{settings.api_port}/docs")
        
        StartupConsole.print_separator()
        
        # Mensagem final
        print("✨ Aplicação pronta para receber requisições!")
        print()
        sys.stdout.flush()

