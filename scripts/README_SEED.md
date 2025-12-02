# Script de Seed - População do Banco de Dados

Este script popula o banco de dados com dados de exemplo para facilitar o desenvolvimento e testes.

## 📋 O que o script cria

O script `seed_database.py` cria dados em todas as entidades que possuem CRUD:

### Entidades populadas:

1. **Empresas (Companies)** - 5 empresas de exemplo
   - Dados completos: CNPJ, endereço, contato, status, tipo de licença
   - Algumas empresas incluem histórico de renovações de contrato

2. **Clientes (Customers)** - 14 clientes de exemplo
   - Vinculados às empresas criadas
   - Distribuídos entre diferentes tipos de licença (Start/Hub)

3. **Licenças (Licenses)** - 1 licença por cliente
   - Vinculadas aos clientes
   - Status ativo com portal_id gerado

4. **Equipe Direta (Direta)** - 4 membros
   - Sócios e colaboradores
   - Com funções, remunerações e políticas de comissão

5. **Indicadores (Indicadores)** - 3 indicadores
   - Vinculados a empresas
   - Com políticas de comissão

6. **Parceiros (Parceiros)** - 3 parceiros
   - Tipos: Agente autorizado, Sindicato, Prefeitura
   - Níveis de comissão: Ouro, Prata, Bronze
   - Cada parceiro possui 3 negócios associados

7. **Negócios (Negocios)** - 9 negócios (3 por parceiro)
   - Tipos: Pré-Pago e Pós-Pago
   - Com valores, quantidades de licenças e datas

8. **Mensagens (Messages)** - 8 mensagens
   - Vinculadas a clientes
   - Tipos: HSM e texto
   - Status: sent, pending, failed

## 🚀 Como usar

### Opção 1: Usando Make (Recomendado)

**Linux/Mac:**
```bash
cd api
make seed
```

**Windows (PowerShell):**
```powershell
cd api
.\make.bat seed
```

### Opção 2: Executando diretamente

**Com ambiente virtual ativado:**
```bash
cd api
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

python scripts/seed_database.py
```

**Sem ambiente virtual (se as dependências estiverem instaladas globalmente):**
```bash
cd api
python scripts/seed_database.py
```

## ⚙️ Pré-requisitos

1. **Banco de dados configurado**: O arquivo `.env` deve estar configurado com a conexão do MongoDB
2. **Dependências instaladas**: Todas as dependências do projeto devem estar instaladas
3. **Ambiente virtual ativado** (recomendado)

## 📝 Estrutura dos dados

### Empresas
- Nomes realistas de empresas brasileiras
- CNPJs válidos (14 dígitos)
- Endereços em diferentes cidades brasileiras
- Status variados: ativo, suspenso, em_negociacao
- Tipos de licença: Start e Hub

### Clientes
- Nomes completos (mínimo 2 palavras)
- Emails válidos
- Telefones no formato brasileiro
- Vinculados a empresas existentes

### Licenças
- Vinculadas aos clientes
- Tipo de licença correspondente ao cliente
- Portal IDs gerados aleatoriamente

### Equipe Direta
- CPFs válidos (11 dígitos)
- Tipos: sócio ou colaborador
- Funções variadas
- Remunerações e comissões definidas

### Indicadores
- Vinculados a empresas
- Políticas de comissão variadas

### Parceiros
- Tipos: Agente autorizado, Sindicato, Prefeitura
- Níveis de comissão: Ouro, Prata, Bronze
- Vinculados a empresas

### Negócios
- Empresas terceiras
- Tipos: Pré-Pago e Pós-Pago
- Valores de negociação
- Datas de início e pagamento

### Mensagens
- Conteúdo variado
- Tipos: HSM e texto
- Status: sent, pending, failed
- Vinculadas a clientes

## ⚠️ Avisos

1. **Dados de teste**: Este script cria dados de exemplo. Não use em produção!
2. **Duplicação**: Executar o script múltiplas vezes criará dados duplicados
3. **Validações**: O script respeita todas as validações dos modelos (CNPJ, CPF, emails, etc.)

## 🔄 Limpar dados

Para limpar os dados criados, você pode:

1. **Deletar manualmente** via interface da aplicação
2. **Limpar o banco de dados** diretamente no MongoDB
3. **Usar scripts de limpeza** (se disponíveis)

## 🐛 Troubleshooting

### Erro de conexão com MongoDB
- Verifique se o MongoDB está rodando
- Confirme as configurações no arquivo `.env`
- Teste a conexão com: `make verify-env`

### Erro de importação
- Certifique-se de estar no diretório `api/`
- Ative o ambiente virtual
- Verifique se todas as dependências estão instaladas

### Erro de validação
- Os dados de exemplo seguem todas as validações
- Se houver erro, verifique os logs para identificar o problema

## 📊 Estatísticas

Após executar o script, você terá aproximadamente:
- 5 empresas
- 14 clientes
- 14 licenças
- 4 membros da equipe direta
- 3 indicadores
- 3 parceiros
- 9 negócios
- 8 mensagens

**Total: ~60 registros** distribuídos em todas as coleções do sistema.

