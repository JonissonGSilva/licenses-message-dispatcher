"""
Script de seed para popular o banco de dados com dados de exemplo.
Este script cria dados em todas as entidades que possuem CRUD.

Nota sobre campos automáticos:
- O campo 'isCompanyActive' é preenchido automaticamente pelos repositórios
  quando customers, indicadores ou parceiros são vinculados a empresas.
  Este campo reflete se a empresa está ativa (status="ativo" e active=True).

Uso:
    python scripts/seed_database.py
    ou
    python -m scripts.seed_database
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List
import random

# Adiciona o diretório raiz ao path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Database
from app.models.company import CompanyCreate, ContractRenovated
from app.models.customer import CustomerCreate
from app.models.license import LicenseCreate
from app.models.team import (
    DiretaCreate, 
    IndicadorCreate, 
    ParceiroCreate, 
    NegocioCreate
)
from app.models.message import MessageCreate
from app.repositories.company_repository import CompanyRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.license_repository import LicenseRepository
from app.repositories.team_repository import (
    DiretaRepository,
    IndicadorRepository,
    ParceiroRepository,
    NegocioRepository
)
from app.repositories.message_repository import MessageRepository
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


# Dados de exemplo para seed
COMPANIES_DATA = [
    {
        "name": "TechSolutions Brasil Ltda",
        "cnpj": "12345678000190",
        "email": "contato@techsolutions.com.br",
        "phone": "5511987654321",
        "address": "Av. Paulista, 1000",
        "city": "São Paulo",
        "state": "SP",
        "zip_code": "01310-100",
        "linked": True,
        "active": True,
        "status": "ativo",
        "employee_count": 250,
        "license_type": "Hub",
        "contract_expiration": datetime.now(timezone.utc) + timedelta(days=365),
    },
    {
        "name": "Inovação Digital S.A.",
        "cnpj": "98765432000111",
        "email": "contato@inovacaodigital.com.br",
        "phone": "5511987654322",
        "address": "Rua das Flores, 500",
        "city": "Rio de Janeiro",
        "state": "RJ",
        "zip_code": "20040-020",
        "linked": True,
        "active": True,
        "status": "ativo",
        "employee_count": 180,
        "license_type": "Start",
        "contract_expiration": datetime.now(timezone.utc) + timedelta(days=180),
    },
    {
        "name": "Sistemas Avançados EIRELI",
        "cnpj": "11223344000155",
        "email": "contato@sistemasavancados.com.br",
        "phone": "5511987654323",
        "address": "Av. Atlântica, 200",
        "city": "Belo Horizonte",
        "state": "MG",
        "zip_code": "30130-000",
        "linked": True,
        "active": True,
        "status": "ativo",
        "employee_count": 120,
        "license_type": "Hub",
        "contract_expiration": datetime.now(timezone.utc) + timedelta(days=270),
    },
    {
        "name": "Cloud Services Brasil",
        "cnpj": "55667788000199",
        "email": "contato@cloudservices.com.br",
        "phone": "5511987654324",
        "address": "Rua da Praia, 300",
        "city": "Florianópolis",
        "state": "SC",
        "zip_code": "88015-000",
        "linked": True,
        "active": True,
        "status": "em_negociacao",
        "employee_count": 90,
        "license_type": "Start",
        "contract_expiration": datetime.now(timezone.utc) + timedelta(days=90),
    },
    {
        "name": "Data Analytics Corp",
        "cnpj": "99887766000122",
        "email": "contato@dataanalytics.com.br",
        "phone": "5511987654325",
        "address": "Av. Ipiranga, 800",
        "city": "Porto Alegre",
        "state": "RS",
        "zip_code": "90010-000",
        "linked": False,
        "active": True,
        "status": "suspenso",
        "employee_count": 200,
        "license_type": "Hub",
        "contract_expiration": datetime.now(timezone.utc) - timedelta(days=30),
    },
]

CUSTOMERS_DATA = [
    # Clientes para TechSolutions
    {"name": "João Silva Santos", "email": "joao.silva@email.com", "phone": "5511999887766", "license_type": "Hub"},
    {"name": "Maria Oliveira Costa", "email": "maria.oliveira@email.com", "phone": "5511999887767", "license_type": "Hub"},
    {"name": "Pedro Almeida Lima", "email": "pedro.almeida@email.com", "phone": "5511999887768", "license_type": "Start"},
    {"name": "Ana Paula Ferreira", "email": "ana.ferreira@email.com", "phone": "5511999887769", "license_type": "Hub"},
    {"name": "Carlos Eduardo Rocha", "email": "carlos.rocha@email.com", "phone": "5511999887770", "license_type": "Start"},
    
    # Clientes para Inovação Digital
    {"name": "Fernanda Souza Martins", "email": "fernanda.martins@email.com", "phone": "5511999887771", "license_type": "Start"},
    {"name": "Ricardo Pereira Gomes", "email": "ricardo.gomes@email.com", "phone": "5511999887772", "license_type": "Start"},
    {"name": "Juliana Rodrigues Barbosa", "email": "juliana.barbosa@email.com", "phone": "5511999887773", "license_type": "Hub"},
    
    # Clientes para Sistemas Avançados
    {"name": "Roberto Carlos Mendes", "email": "roberto.mendes@email.com", "phone": "5511999887774", "license_type": "Hub"},
    {"name": "Patricia Santos Araújo", "email": "patricia.araujo@email.com", "phone": "5511999887775", "license_type": "Start"},
    {"name": "Lucas Henrique Dias", "email": "lucas.dias@email.com", "phone": "5511999887776", "license_type": "Hub"},
    
    # Clientes para Cloud Services
    {"name": "Amanda Costa Ribeiro", "email": "amanda.ribeiro@email.com", "phone": "5511999887777", "license_type": "Start"},
    {"name": "Bruno Felipe Nunes", "email": "bruno.nunes@email.com", "phone": "5511999887778", "license_type": "Start"},
]

DIRETA_DATA = [
    {
        "name": "Roberto Silva",
        "cpf": "12345678901",
        "phone": "5511998765432",
        "email": "roberto.silva@empresa.com",
        "type": "sócio",
        "function": "Diretor Comercial",
        "remuneration": "R$ 15.000,00",
        "commission": "5% sobre vendas acima de R$ 100.000",
    },
    {
        "name": "Carla Mendes",
        "cpf": "23456789012",
        "phone": "5511998765433",
        "email": "carla.mendes@empresa.com",
        "type": "sócio",
        "function": "Diretora de Operações",
        "remuneration": "R$ 12.000,00",
        "commission": "3% sobre vendas acima de R$ 50.000",
    },
    {
        "name": "Fernando Costa",
        "cpf": "34567890123",
        "phone": "5511998765434",
        "email": "fernando.costa@empresa.com",
        "type": "colaborador",
        "function": "Gerente de Vendas",
        "remuneration": "R$ 8.000,00",
        "commission": "2% sobre todas as vendas",
    },
    {
        "name": "Mariana Alves",
        "cpf": "45678901234",
        "phone": "5511998765435",
        "email": "mariana.alves@empresa.com",
        "type": "colaborador",
        "function": "Analista Comercial",
        "remuneration": "R$ 5.500,00",
        "commission": "1% sobre vendas acima de R$ 30.000",
    },
]

INDICADOR_DATA = [
    {
        "name": "Paulo Roberto",
        "phone": "5511997654321",
        "email": "paulo.roberto@indicador.com",
        "commission": "10% sobre primeira venda, 5% sobre renovações",
    },
    {
        "name": "Sandra Beatriz",
        "phone": "5511997654322",
        "email": "sandra.beatriz@indicador.com",
        "commission": "12% sobre primeira venda, 6% sobre renovações",
    },
    {
        "name": "Marcos Antonio",
        "phone": "5511997654323",
        "email": "marcos.antonio@indicador.com",
        "commission": "8% sobre primeira venda, 4% sobre renovações",
    },
]

PARCEIRO_DATA = [
    {
        "name": "José Carlos",
        "type": "Agente autorizado",
        "phone": "5511996543210",
        "email": "jose.carlos@parceiro.com",
        "commission": "Ouro",
    },
    {
        "name": "Ana Beatriz",
        "type": "Sindicato",
        "phone": "5511996543211",
        "email": "ana.beatriz@parceiro.com",
        "commission": "Prata",
    },
    {
        "name": "Carlos Eduardo",
        "type": "Prefeitura",
        "phone": "5511996543212",
        "email": "carlos.eduardo@parceiro.com",
        "commission": "Bronze",
    },
]

NEGOCIO_DATA = [
    {
        "third_party_company": "Empresa Parceira A",
        "type": "Pré-Pago",
        "license_count": 50,
        "negotiation_value": "R$ 25.000,00",
        "contract_duration": "12 meses",
        "start_date": datetime.now(timezone.utc) - timedelta(days=30),
        "payment_date": datetime.now(timezone.utc) - timedelta(days=5),
    },
    {
        "third_party_company": "Empresa Parceira B",
        "type": "Pós-Pago",
        "license_count": 100,
        "negotiation_value": "R$ 60.000,00",
        "contract_duration": "24 meses",
        "start_date": datetime.now(timezone.utc) - timedelta(days=60),
        "payment_date": datetime.now(timezone.utc) - timedelta(days=10),
    },
    {
        "third_party_company": "Empresa Parceira C",
        "type": "Pré-Pago",
        "license_count": 30,
        "negotiation_value": "R$ 15.000,00",
        "contract_duration": "6 meses",
        "start_date": datetime.now(timezone.utc) - timedelta(days=15),
        "payment_date": datetime.now(timezone.utc) - timedelta(days=2),
    },
]

MESSAGES_DATA = [
    {"content": "Bem-vindo ao sistema Hub! Sua licença foi ativada com sucesso.", "message_type": "hsm", "status": "sent"},
    {"content": "Sua licença Start está prestes a expirar. Renove agora e ganhe 10% de desconto!", "message_type": "hsm", "status": "sent"},
    {"content": "Parabéns! Você foi promovido para licença Hub. Aproveite os novos recursos!", "message_type": "hsm", "status": "sent"},
    {"content": "Lembrete: Pagamento da licença vence em 7 dias. Evite interrupções no serviço.", "message_type": "text", "status": "pending"},
    {"content": "Novo recurso disponível! Acesse o portal para conhecer as novidades.", "message_type": "hsm", "status": "sent"},
    {"content": "Obrigado por escolher nossos serviços. Sua opinião é muito importante para nós!", "message_type": "text", "status": "sent"},
    {"content": "Promoção especial: Renove sua licença e ganhe 2 meses grátis!", "message_type": "hsm", "status": "pending"},
    {"content": "Sua solicitação foi processada com sucesso. Em breve você receberá mais informações.", "message_type": "text", "status": "sent"},
]


async def seed_companies() -> List[str]:
    """Cria empresas e retorna lista de IDs criados."""
    logger.info("🌱 Criando empresas...")
    company_ids = []
    
    for company_data in COMPANIES_DATA:
        try:
            # Adiciona histórico de renovações para algumas empresas
            if random.random() > 0.5:  # 50% das empresas têm histórico
                company_data["contract_renovated"] = [
                    ContractRenovated(
                        age_contract=12,
                        type_contract=1,
                        isExpirated=False,
                    ),
                    ContractRenovated(
                        age_contract=24,
                        type_contract=2,
                        isExpirated=False,
                    ),
                ]
            
            company_create = CompanyCreate(**company_data)
            company = await CompanyRepository.create(company_create)
            company_ids.append(str(company.id))
            logger.info(f"  ✅ Empresa criada: {company.name} (ID: {company.id})")
        except Exception as e:
            logger.error(f"  ❌ Erro ao criar empresa {company_data['name']}: {e}")
    
    logger.info(f"📊 Total de empresas criadas: {len(company_ids)}")
    return company_ids


async def seed_customers(company_ids: List[str]) -> List[str]:
    """
    Cria clientes vinculados a empresas e retorna lista de IDs criados.
    
    Nota: O campo 'isCompanyActive' é preenchido automaticamente pelo repositório
    baseado no status da empresa (status="ativo" e active=True).
    """
    logger.info("🌱 Criando clientes...")
    customer_ids = []
    
    # Distribui clientes entre as empresas
    # Apenas cria customers para empresas ativas (status="ativo" e active=True)
    customers_per_company = len(CUSTOMERS_DATA) // len(company_ids)
    remaining_customers = len(CUSTOMERS_DATA) % len(company_ids)
    
    customer_index = 0
    for i, company_id in enumerate(company_ids):
        # Busca a empresa para obter o nome e status
        company = await CompanyRepository.find_by_id(company_id)
        if not company:
            continue
        
        # Verifica se a empresa está ativa (status="ativo" e active=True)
        # Apenas cria customers para empresas ativas
        is_company_active = (
            company.status == "ativo" and 
            company.active is True
        )
        
        if not is_company_active:
            logger.info(f"  ⏭️  Pulando empresa '{company.name}' (status: {company.status}, active: {company.active}) - não está ativa")
            # Ainda assim distribui os customers para outras empresas
            # Calcula quantos clientes pular
            num_customers = customers_per_company + (1 if i < remaining_customers else 0)
            customer_index += num_customers
            continue
        
        # Calcula quantos clientes criar para esta empresa
        num_customers = customers_per_company + (1 if i < remaining_customers else 0)
        
        for j in range(num_customers):
            if customer_index >= len(CUSTOMERS_DATA):
                break
            
            customer_data = CUSTOMERS_DATA[customer_index].copy()
            customer_data["company"] = company.name  # Vincula à empresa pelo nome
            # O campo 'isCompanyActive' será preenchido automaticamente pelo repositório
            
            try:
                customer_create = CustomerCreate(**customer_data)
                customer = await CustomerRepository.create(customer_create)
                customer_ids.append(str(customer.id))
                
                # Verifica se o campo isCompanyActive foi preenchido corretamente
                if customer.company and isinstance(customer.company, dict):
                    is_active = customer.company.get("isCompanyActive", None)
                    logger.info(
                        f"  ✅ Cliente criado: {customer.name} (ID: {customer.id}) "
                        f"- Empresa: {customer.company.get('name', 'N/A')} "
                        f"(isCompanyActive: {is_active})"
                    )
                else:
                    logger.info(f"  ✅ Cliente criado: {customer.name} (ID: {customer.id})")
            except Exception as e:
                logger.error(f"  ❌ Erro ao criar cliente {customer_data['name']}: {e}")
            
            customer_index += 1
    
    logger.info(f"📊 Total de clientes criados: {len(customer_ids)}")
    return customer_ids


async def seed_licenses(customer_ids: List[str]) -> List[str]:
    """Cria licenças vinculadas a clientes e retorna lista de IDs criados."""
    logger.info("🌱 Criando licenças...")
    license_ids = []
    
    for customer_id in customer_ids:
        try:
            customer = await CustomerRepository.find_by_id(customer_id)
            if not customer:
                continue
            
            # Cria licença com o mesmo tipo do cliente
            license_create = LicenseCreate(
                customer_id=customer.id,
                license_type=customer.license_type,
                status="active",
                portal_id=f"LIC-{random.randint(10000, 99999)}",
            )
            license = await LicenseRepository.create(license_create)
            license_ids.append(str(license.id))
            logger.info(f"  ✅ Licença criada: {license.license_type} para cliente {customer.name} (ID: {license.id})")
        except Exception as e:
            logger.error(f"  ❌ Erro ao criar licença para cliente {customer_id}: {e}")
    
    logger.info(f"📊 Total de licenças criadas: {len(license_ids)}")
    return license_ids


async def seed_direta() -> List[str]:
    """Cria equipe direta e retorna lista de IDs criados."""
    logger.info("🌱 Criando equipe direta...")
    direta_ids = []
    
    for direta_data in DIRETA_DATA:
        try:
            direta_create = DiretaCreate(**direta_data)
            direta = await DiretaRepository.create(direta_create)
            direta_ids.append(str(direta.id))
            logger.info(f"  ✅ Membro direta criado: {direta.name} (ID: {direta.id})")
        except Exception as e:
            logger.error(f"  ❌ Erro ao criar direta {direta_data.get('name', 'N/A')}: {e}")
    
    logger.info(f"📊 Total de membros direta criados: {len(direta_ids)}")
    return direta_ids


async def seed_indicadores(company_ids: List[str]) -> List[str]:
    """
    Cria indicadores vinculados a empresas e retorna lista de IDs criados.
    
    Nota: O campo 'isCompanyActive' é preenchido automaticamente pelo repositório
    baseado no status da empresa (status="ativo" e active=True).
    """
    logger.info("🌱 Criando indicadores...")
    indicador_ids = []
    
    # Distribui indicadores entre empresas
    # Apenas cria indicadores para empresas ativas
    for i, indicador_data in enumerate(INDICADOR_DATA):
        if i < len(company_ids):
            company = await CompanyRepository.find_by_id(company_ids[i])
            if company:
                # Verifica se a empresa está ativa
                is_company_active = (
                    company.status == "ativo" and 
                    company.active is True
                )
                if not is_company_active:
                    logger.info(f"  ⏭️  Pulando empresa '{company.name}' para indicador - não está ativa")
                    continue
                indicador_data["company"] = company.name
                # O campo 'isCompanyActive' será preenchido automaticamente pelo repositório
        
        try:
            indicador_create = IndicadorCreate(**indicador_data)
            indicador = await IndicadorRepository.create(indicador_create)
            indicador_ids.append(str(indicador.id))
            logger.info(f"  ✅ Indicador criado: {indicador.name} (ID: {indicador.id})")
        except Exception as e:
            logger.error(f"  ❌ Erro ao criar indicador {indicador_data.get('name', 'N/A')}: {e}")
    
    logger.info(f"📊 Total de indicadores criados: {len(indicador_ids)}")
    return indicador_ids


async def seed_parceiros(company_ids: List[str]) -> List[str]:
    """
    Cria parceiros com negócios e retorna lista de IDs criados.
    
    Nota: O campo 'isCompanyActive' é preenchido automaticamente pelo repositório
    baseado no status da empresa (status="ativo" e active=True).
    """
    logger.info("🌱 Criando parceiros...")
    parceiro_ids = []
    
    # Distribui parceiros entre empresas
    # Apenas cria parceiros para empresas ativas
    for i, parceiro_data in enumerate(PARCEIRO_DATA):
        if i < len(company_ids):
            company = await CompanyRepository.find_by_id(company_ids[i])
            if company:
                # Verifica se a empresa está ativa
                is_company_active = (
                    company.status == "ativo" and 
                    company.active is True
                )
                if not is_company_active:
                    logger.info(f"  ⏭️  Pulando empresa '{company.name}' para parceiro - não está ativa")
                    continue
                parceiro_data["company"] = company.name
                # O campo 'isCompanyActive' será preenchido automaticamente pelo repositório
        
        try:
            parceiro_create = ParceiroCreate(**parceiro_data)
            parceiro = await ParceiroRepository.create(parceiro_create)
            parceiro_ids.append(str(parceiro.id))
            logger.info(f"  ✅ Parceiro criado: {parceiro.name} (ID: {parceiro.id})")
            
            # Cria negócios para cada parceiro
            for negocio_data in NEGOCIO_DATA:
                try:
                    negocio_create = NegocioCreate(**negocio_data)
                    negocio = await NegocioRepository.create(negocio_create, str(parceiro.id))
                    logger.info(f"    ✅ Negócio criado: {negocio.third_party_company} (ID: {negocio.id})")
                except Exception as e:
                    logger.error(f"    ❌ Erro ao criar negócio {negocio_data.get('third_party_company', 'N/A')}: {e}")
                    
        except Exception as e:
            logger.error(f"  ❌ Erro ao criar parceiro {parceiro_data.get('name', 'N/A')}: {e}")
    
    logger.info(f"📊 Total de parceiros criados: {len(parceiro_ids)}")
    return parceiro_ids


async def seed_messages(customer_ids: List[str]) -> List[str]:
    """Cria mensagens vinculadas a clientes e retorna lista de IDs criados."""
    logger.info("🌱 Criando mensagens...")
    message_ids = []
    
    # Distribui mensagens entre clientes
    for i, message_data in enumerate(MESSAGES_DATA):
        if i < len(customer_ids):
            customer = await CustomerRepository.find_by_id(customer_ids[i])
            if customer:
                message_data["customer_id"] = customer.id
                message_data["phone"] = customer.phone
                message_data["license_type"] = customer.license_type
        else:
            # Se não houver cliente suficiente, usa dados aleatórios
            random_customer_id = random.choice(customer_ids)
            customer = await CustomerRepository.find_by_id(random_customer_id)
            if customer:
                message_data["customer_id"] = customer.id
                message_data["phone"] = customer.phone
                message_data["license_type"] = customer.license_type
        
        try:
            message_create = MessageCreate(**message_data)
            message = await MessageRepository.create(message_create)
            message_ids.append(str(message.id))
            logger.info(f"  ✅ Mensagem criada: {message.content[:50]}... (ID: {message.id})")
        except Exception as e:
            logger.error(f"  ❌ Erro ao criar mensagem: {e}")
    
    logger.info(f"📊 Total de mensagens criadas: {len(message_ids)}")
    return message_ids


async def main():
    """Função principal que executa o seed completo."""
    logger.info("=" * 60)
    logger.info("🚀 Iniciando seed do banco de dados...")
    logger.info("=" * 60)
    
    try:
        # Conecta ao banco de dados
        await Database.connect()
        logger.info("✅ Conectado ao banco de dados")
        
        # Executa seed em ordem (respeitando dependências)
        company_ids = await seed_companies()
        customer_ids = await seed_customers(company_ids)
        license_ids = await seed_licenses(customer_ids)
        direta_ids = await seed_direta()
        indicador_ids = await seed_indicadores(company_ids)
        parceiro_ids = await seed_parceiros(company_ids)
        message_ids = await seed_messages(customer_ids)
        
        # Resumo final
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ Seed concluído com sucesso!")
        logger.info("=" * 60)
        logger.info(f"📊 Resumo:")
        logger.info(f"   - Empresas: {len(company_ids)}")
        logger.info(f"   - Clientes: {len(customer_ids)}")
        logger.info(f"   - Licenças: {len(license_ids)}")
        logger.info(f"   - Equipe Direta: {len(direta_ids)}")
        logger.info(f"   - Indicadores: {len(indicador_ids)}")
        logger.info(f"   - Parceiros: {len(parceiro_ids)}")
        logger.info(f"   - Mensagens: {len(message_ids)}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Erro durante o seed: {e}", exc_info=True)
        raise
    finally:
        # Desconecta do banco de dados
        await Database.disconnect()
        logger.info("✅ Desconectado do banco de dados")


if __name__ == "__main__":
    asyncio.run(main())

