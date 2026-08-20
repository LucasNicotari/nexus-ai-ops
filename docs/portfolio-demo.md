# Roteiro de demonstração para portfólio

## Narrativa recomendada (45 a 60 segundos)

1. **Problema, 0–5 s** — “Eventos operacionais chegam sem contexto e dificultam priorização.”
2. **Fluxo, 5–12 s** — mostre o fluxograma do README e destaque qualidade antes de persistência.
3. **Dados e execução, 12–22 s** — execute `scripts/run_demo.py`; o terminal prova geração, validação, UPSERT e registro do modelo.
4. **API, 22–32 s** — abra Swagger, faça uma chamada autenticada e evidencie `X-Request-ID`.
5. **Observabilidade, 32–48 s** — Grafana: taxa, p95, eventos persistidos, anomalias e serviços críticos.
6. **Limite honesto, 48–55 s** — “MVP local com dados sintéticos; conectores, SSO e alertas são próximas extensões.”

## Preparação

```powershell
.\.venv\Scripts\python.exe scripts/run_demo.py
.\.venv\Scripts\uvicorn.exe nexus.api.app:app --reload
docker compose --profile observability up -d
```

Faça chamadas autenticadas antes de abrir o Grafana para preencher os gráficos de API. Feche janelas pessoais e desative notificações antes de gravar.

## Gravação local

`scripts/record_linkedin_demo.ps1` prepara a demonstração, abre as interfaces e grava em `artifacts/videos/`. O arquivo de vídeo é deliberadamente ignorado pelo Git: o repositório versiona o código e o roteiro, não artefatos pesados nem conteúdo de tela potencialmente sensível.

## O que não afirmar

Não descreva o NEXUS como sistema corporativo pronto, detector universal de incidentes ou plataforma de remediação autônoma. A força do portfólio está em mostrar as decisões verificáveis: contrato único, validação, migrations, idempotência, separação temporal, API protegida e observabilidade.
