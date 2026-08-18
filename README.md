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

Para experimentos temporais, geração de dashboards ou avaliação futura de modelos, gere três dias de dados em intervalos de cinco minutos. O dataset inclui ciclo diário de carga e janelas recorrentes de degradação:

```powershell
.\.venv\Scripts\python.exe scripts/generate_temporal_training_data.py
```

Os dois datasets seguem o mesmo contrato de evento. Componentes futuros devem reutilizar esse contrato, não criar formatos paralelos.

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

## ML Prediction

The supervised baseline estimates anomaly risk from metric, metric value, relative deviation from the synthetic metric baseline, service, and host. It uses a class-balanced Random Forest with four-fold stratified cross-validation and a 0.20 alert threshold to favor recall in this small, imbalanced dataset. Severity, event ID, and `is_anomaly` are excluded from features to avoid information leakage. Fixed baselines are deliberately limited to this synthetic stage; production requires rolling historical baselines.

```powershell
.\.venv\Scripts\python.exe scripts/predict_anomaly_risk.py
```

## Temporal validation

The temporal pipeline derives lag, rolling mean, rolling standard deviation, deviation from the prior window, and hour-of-day features. It splits whole timestamps into train (60%), validation (20%), and test (20%) partitions. The alert threshold is selected on validation only; test data remains isolated until final evaluation.

```powershell
.\.venv\Scripts\python.exe scripts/generate_temporal_training_data.py
.\.venv\Scripts\python.exe scripts/evaluate_temporal_risk.py
```

## API

The initial FastAPI layer is read-only and exposes data already persisted in PostgreSQL. It does not train ML models during HTTP requests.

```powershell
.\.venv\Scripts\uvicorn.exe nexus.api.app:app --reload
```

Available routes: `GET /health`, `GET /events?limit=100&offset=0`, `GET /analytics/metrics`, `GET /analytics/services`, and interactive documentation at `/docs`.

## Model registry

The temporal model can be trained and registered locally. The serialized `joblib` artifact stays in `data/models/`, while the run metadata, evaluation metrics, and held-out predictions are stored in PostgreSQL and exposed by the API.

```powershell
.\.venv\Scripts\python.exe scripts/generate_temporal_training_data.py
.\.venv\Scripts\python.exe scripts/train_and_register_temporal_model.py
```

Read registered runs at `GET /ml/runs` and their persisted predictions at `GET /ml/runs/{model_run_id}/predictions`.

## Continuous Integration

GitHub Actions runs tests, Ruff lint, and Ruff format checks on every push and on pull requests targeting `main`. PostgreSQL integration tests remain opt-in and are not run in CI until the workflow provisions a database service.

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
- [x] ML Prediction
- [x] Anomaly Detection
- [ ] MLflow
- [x] FastAPI
- [ ] Observability
- [ ] Local AI Assistant
- [ ] AIOps Intelligence
- [ ] Automated Tests
- [ ] CI/CD
- [ ] Production-like Local Environment
