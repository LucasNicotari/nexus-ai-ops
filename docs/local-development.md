# Desenvolvimento e operação local

## Pré-requisitos

- Python 3.13 disponível no `PATH`;
- Docker Desktop iniciado, com backend WSL 2 funcional;
- Git;
- portas locais livres: 5432, 8000, 3000 e 9090.

## Instalação

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Edite `.env` antes de iniciar serviços. `POSTGRES_PASSWORD`, `GRAFANA_ADMIN_PASSWORD` e `NEXUS_API_KEYS` são locais e nunca devem ser enviados ao Git. O formato de `NEXUS_API_KEYS` é uma lista separada por vírgula de `chave:papel`; os endpoints operacionais requerem o papel `reader`.

## Banco e migrations

```powershell
docker compose up -d postgres
docker compose ps
python -m alembic upgrade head
```

`docker compose ps` deve mostrar `postgres` como `healthy`. Migrations são um passo explícito, pois o repositório não cria schema automaticamente.

## Cenário completo de demonstração

```powershell
.\.venv\Scripts\python.exe scripts/run_demo.py
.\.venv\Scripts\uvicorn.exe nexus.api.app:app --reload
```

Em outro terminal:

```powershell
docker compose --profile observability up -d
```

O script de demonstração executa migrations, gera o dataset temporal, valida, persiste por UPSERT e registra uma execução de modelo. Ele não remove o estado prévio.

## Uso da API

`GET /health` não exige chave. As demais rotas exigem o cabeçalho abaixo:

```powershell
$headers = @{ "X-NEXUS-API-Key" = "sua-chave-local" }
Invoke-RestMethod http://localhost:8000/analytics/services -Headers $headers
```

A documentação interativa está em `http://localhost:8000/docs`. Cada resposta deve incluir `X-Request-ID`, útil para correlacionar a chamada com logs e métricas.

## Observabilidade

- Grafana: `http://localhost:3000`;
- Prometheus: `http://localhost:9090`;
- Dashboard provisionado: `NEXUS / NEXUS API Overview`.

O Prometheus coleta a API iniciada no host via `host.docker.internal:8000`. Faça algumas chamadas autenticadas à API para criar séries de taxa e latência. Os cards de eventos/anomalias dependem de dados no PostgreSQL; execute `run_demo.py` antes de gravar a demonstração.

## Parar o ambiente

```powershell
docker compose --profile observability down
```

Esse comando para e remove containers e rede, mas preserva o volume nomeado do PostgreSQL. Para apagar dados deliberadamente, use o comando de volume somente após confirmar que o ambiente local pode ser descartado.

## Diagnóstico objetivo

| Sintoma | Verificação | Ação provável |
| --- | --- | --- |
| `docker compose` não conecta | `docker version` | Inicie o Docker Desktop e aguarde o daemon. |
| Banco não fica saudável | `docker compose logs postgres` | Verifique credenciais e a porta 5432. |
| API retorna 401/403 | confira `NEXUS_API_KEYS` e `X-NEXUS-API-Key` | Use chave configurada com papel `reader`. |
| Grafana sem séries | abra `/metrics` e faça requisições | Confirme API em 8000 e profile `observability` ativo. |
| Teste de integração ignorado | confira `RUN_POSTGRES_INTEGRATION` | Defina a variável e inicie o PostgreSQL. |
