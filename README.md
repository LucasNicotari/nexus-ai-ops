# NEXUS AI Ops

🚧 **Em desenvolvimento**

NEXUS é uma plataforma local de operações e inteligência de TI orientada por IA. O projeto evoluirá incrementalmente para coletar, validar, armazenar e analisar dados sintéticos de operações, detectar anomalias e apoiar a investigação de incidentes.

## Objetivo

Construir uma base profissional e reproduzível para explorar AIOps, engenharia de dados, Machine Learning e observabilidade sem depender de serviços pagos externos.

## Visão arquitetural

Diagrama arquitetural: reservado para uma etapa futura, após a definição dos fluxos de dados e requisitos de negócio.

## Stack atual

- Python 3.13
- pytest
- Ruff
- Docker Compose
- PostgreSQL 17
- psycopg 3

## Como executar

Crie e ative o ambiente virtual, instale as dependências de desenvolvimento e execute as verificações:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
```

## Dados sintéticos de operações

O primeiro dataset contém medições de CPU, memória, latência HTTP e taxa de erros de hosts e serviços fictícios. Cada evento possui identificador, timestamp UTC, host, serviço, métrica, unidade, severidade e indicador de anomalia.

O gerador usa uma seed fixa por padrão, portanto produz sempre os mesmos 120 eventos — importante para testes reproduzíveis e comparação futura de modelos.

```powershell
.\.venv\Scripts\python.exe scripts/generate_synthetic_events.py
```

O CSV gerado em `data/synthetic/operational_events.csv` é um artefato local ignorado pelo Git e pode ser recriado a qualquer momento.

## Ingestão de dados

A ingestão atual lê o CSV e converte cada linha em um `OperationalEvent` validado. Ela exige todas as colunas do contrato, timestamps com timezone, valores numéricos válidos e `is_anomaly` como `true` ou `false`. Ainda não há persistência: a próxima etapa de qualidade de dados avaliará o conteúdo antes de introduzirmos o PostgreSQL.

## Qualidade de dados

Após a ingestão, o NEXUS avalia cada lote e produz um relatório sem interromper a análise do restante dos eventos. As regras atuais verificam IDs duplicados, ordenação temporal, métricas conhecidas e faixas plausíveis de valor. Essa separação evita confundir arquivo malformado (erro de ingestão) com dado operacional suspeito (problema de qualidade).

## Camada PostgreSQL

Eventos aprovados são persistidos na tabela `operational_events` do PostgreSQL local. A camada usa `psycopg` e SQL explícito, com `event_id` como chave primária e upsert para tornar reexecuções idempotentes.

```powershell
.\.venv\Scripts\python.exe scripts/generate_synthetic_events.py
.\.venv\Scripts\python.exe scripts/load_synthetic_events.py
```

Para executar o teste de integração com o PostgreSQL do Compose:

```powershell
$env:RUN_POSTGRES_INTEGRATION = "1"
pytest -m integration
```

## Incident Analytics

Nesta fase, incidentes são indicadores derivados de eventos anômalos — não uma entidade de negócio definitiva. O relatório agrega volume, média, mínimo, máximo e anomalias por métrica, além de priorizar serviços pela quantidade de sinais anômalos e críticos.

```powershell
.\.venv\Scripts\python.exe scripts/analyze_incidents.py
```

## Anomaly Detection

O baseline de ML usa `IsolationForest` separadamente para cada métrica. Ele aprende somente com os valores medidos e não usa `is_anomaly` no treinamento; o rótulo sintético serve apenas para avaliar precisão e recall. O agrupamento por métrica impede a comparação indevida entre unidades incompatíveis, como porcentagens e milissegundos.

```powershell
.\.venv\Scripts\python.exe scripts/detect_anomalies.py
```

Para preparar o banco local, copie `.env.example` para `.env`, ajuste a senha local e execute:

```powershell
docker compose up -d
docker compose ps
```

## Roadmap

- [x] Environment & Project Foundation
- [x] Synthetic IT Data
- [x] Data Ingestion
- [x] Data Quality
- [x] PostgreSQL Data Layer
- [x] Incident Analytics
- [ ] ML Prediction
- [x] Anomaly Detection
- [ ] MLflow
- [ ] FastAPI
- [ ] Observability
- [ ] Local AI Assistant
- [ ] AIOps Intelligence
- [ ] Automated Tests
- [ ] CI/CD
- [ ] Production-like Local Environment
