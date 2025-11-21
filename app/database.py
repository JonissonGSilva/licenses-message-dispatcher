"""Configuração e conexão com MongoDB."""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    """Classe para gerenciar conexão com MongoDB."""
    
    client: AsyncIOMotorClient = None
    database = None
    
    @classmethod
    async def connect(cls):
        """Conecta ao MongoDB."""
        # Verifica se é MongoDB Atlas antes do try para usar nos excepts
        is_atlas = "mongodb+srv://" in settings.mongodb_url
        
        try:
            # Configurações de conexão com timeouts apropriados
            connection_kwargs = {
                "serverSelectionTimeoutMS": 30000,  # 30 segundos
                "connectTimeoutMS": 20000,  # 20 segundos
                "socketTimeoutMS": 20000,  # 20 segundos
            }
            
            # Para MongoDB Atlas (mongodb+srv://), SSL é configurado automaticamente pelo Motor
            # Mas podemos adicionar configurações específicas se necessário
            
            if is_atlas:
                logger.info("Detectado MongoDB Atlas - SSL/TLS será configurado automaticamente")
                # Para debug: se houver problemas de SSL, pode tentar com tlsAllowInvalidCertificates
                # Mas isso não é recomendado para produção
                # connection_kwargs["tlsAllowInvalidCertificates"] = True  # Apenas para debug
            
            # Mascara a URL para não expor credenciais no log
            url_display = settings.mongodb_url
            if "@" in url_display:
                # Mostra apenas o host, não as credenciais
                url_display = url_display.split("@")[-1]
            
            logger.info(f"Conectando ao MongoDB: {url_display}")
            logger.debug(f"Database: {settings.mongodb_db_name}")
            
            cls.client = AsyncIOMotorClient(settings.mongodb_url, **connection_kwargs)
            cls.database = cls.client[settings.mongodb_db_name]
            
            # Testa a conexão
            logger.debug("Testando conexão com ping...")
            await cls.client.admin.command('ping')
            logger.info("Conexão com MongoDB estabelecida com sucesso")
            
        except ServerSelectionTimeoutError as e:
            error_msg = f"Timeout ao conectar ao MongoDB (30s)"
            logger.error(error_msg)
            logger.error(f"Detalhes: {str(e)}")
            logger.error("")
            logger.error("Possíveis causas:")
            logger.error("  1. String de conexão incorreta no arquivo .env")
            logger.error("  2. IP não está na whitelist do MongoDB Atlas")
            logger.error("  3. Credenciais incorretas (usuário/senha)")
            logger.error("  4. Problemas de rede/firewall bloqueando conexão")
            logger.error("  5. MongoDB Atlas está fora do ar")
            logger.error("")
            if is_atlas:
                logger.error("Para MongoDB Atlas, verifique:")
                logger.error("  - Network Access: Adicione seu IP (ou 0.0.0.0/0 para todos)")
                logger.error("  - Database Access: Verifique usuário e senha")
            raise ConnectionFailure(error_msg) from e
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            
            logger.error(f"Erro ao conectar ao MongoDB: {error_type}")
            logger.error(f"Detalhes: {error_msg}")
            
            # Detecta erros específicos de SSL/TLS
            if "SSL" in error_msg or "TLS" in error_msg or "ssl" in error_msg.lower() or "tls" in error_msg.lower():
                logger.error("")
                logger.error("⚠️  ERRO DE SSL/TLS DETECTADO")
                logger.error("")
                logger.error("Soluções possíveis:")
                logger.error("  1. Verifique se está usando 'mongodb+srv://' para MongoDB Atlas")
                logger.error("  2. Atualize o Python e as dependências:")
                logger.error("     pip install --upgrade motor pymongo")
                logger.error("  3. Verifique se o OpenSSL está atualizado")
                logger.error("  4. Tente usar uma versão diferente do Python (3.10 ou 3.11)")
                logger.error("")
                logger.error("Para debug temporário, você pode tentar adicionar no código:")
                logger.error("  connection_kwargs['tlsAllowInvalidCertificates'] = True")
                logger.error("  (NÃO RECOMENDADO PARA PRODUÇÃO)")
            
            logger.error("")
            logger.error("Stack trace completo:", exc_info=True)
            raise ConnectionFailure(f"Erro ao conectar ao MongoDB: {error_msg}") from e
    
    @classmethod
    async def disconnect(cls):
        """Desconecta do MongoDB."""
        if cls.client:
            cls.client.close()
            logger.info("Desconectado do MongoDB")
    
    @classmethod
    def get_database(cls):
        """Retorna a instância do banco de dados."""
        return cls.database

