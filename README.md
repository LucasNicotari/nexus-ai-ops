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

Para preparar o banco local, copie `.env.example` para `.env`, ajuste a senha local e execute:

```powershell
docker compose up -d
docker compose ps
```

## Roadmap

- [x] Environment & Project Foundation
- [x] Synthetic IT Data
- [ ] Data Ingestion
- [ ] Data Quality
- [ ] PostgreSQL Data Layer
- [ ] Incident Analytics
- [ ] ML Prediction
- [ ] Anomaly Detection
- [ ] MLflow
- [ ] FastAPI
- [ ] Observability
- [ ] Local AI Assistant
- [ ] AIOps Intelligence
- [ ] Automated Tests
- [ ] CI/CD
- [ ] Production-like Local Environment
