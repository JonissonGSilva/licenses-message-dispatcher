# Padrão de CSV para Importação

Este documento define o padrão oficial de colunas aceitas para arquivos CSV de importação de clientes.

## Colunas Aceitas

O sistema aceita **apenas** os seguintes nomes de colunas:

| Coluna | Português | Inglês | Obrigatória |
|--------|-----------|--------|-------------|
| Nome do Cliente | `nome` | `name` | ✅ Sim |
| Email | `email` | `email` | ❌ Não |
| Telefone | `telefone` | `phone` | ✅ Sim |
| Tipo de Licença | `tipo_licenca` | `license_type` | ✅ Sim |
| Empresa | `empresa` | `company` | ❌ Não |

## Exemplo de CSV

### Em Português:
```csv
nome,email,telefone,tipo_licenca,empresa
João Silva,joao.silva@example.com,11999999999,Hub,Empresa XYZ
Maria Santos,maria.santos@example.com,21888888888,Start,Empresa ABC
```

### Em Inglês:
```csv
name,email,phone,license_type,company
João Silva,joao.silva@example.com,11999999999,Hub,Empresa XYZ
Maria Santos,maria.santos@example.com,21888888888,Start,Empresa ABC
```

## Regras de Validação

### Nome (`nome` / `name`)
- **Obrigatório:** Sim
- **Tipo:** String
- **Validação:** Não pode estar vazio

### Email (`email`)
- **Obrigatório:** Não
- **Tipo:** String
- **Validação:** Deve ser um email válido (se fornecido)

### Telefone (`telefone` / `phone`)
- **Obrigatório:** Sim
- **Tipo:** String numérica
- **Validação:** 
  - Mínimo 10 dígitos
  - Código do país (+55) será adicionado automaticamente se não presente

### Tipo de Licença (`tipo_licenca` / `license_type`)
- **Obrigatório:** Sim
- **Tipo:** String
- **Valores aceitos:** `Start` ou `Hub` (case-insensitive)
- **Normalizações automáticas:**
  - `S` → `Start`
  - `H` → `Hub`
  - `Starter` → `Start`
  - `Basic` → `Start`

### Empresa (`empresa` / `company`)
- **Obrigatório:** Não
- **Tipo:** String
- **Validação:** Nenhuma

## Importante

⚠️ **Apenas os termos padrão listados acima são aceitos.** 

O sistema não aceita variações como:
- ❌ `cliente`, `customer` (use `nome` ou `name`)
- ❌ `celular`, `whatsapp` (use `telefone` ou `phone`)
- ❌ `tipo`, `licenca`, `license`, `plano` (use `tipo_licenca` ou `license_type`)
- ❌ `organizacao`, `organization` (use `empresa` ou `company`)

## Normalização Automática

O sistema normaliza automaticamente os nomes das colunas para o formato interno em inglês:
- `nome` → `name`
- `telefone` → `phone`
- `tipo_licenca` → `license_type`
- `empresa` → `company`
- `email` → `email` (já está em inglês)

Isso permite que você use nomes em português ou inglês, mas garante consistência interna.

