# Testes e CI

## Pirâmide de validação

| Nível | Foco | Exemplo |
| --- | --- | --- |
| Unitário | Domínio e regras isoladas | Parsing, qualidade, features temporais e autorização. |
| Integração | Contrato real com PostgreSQL | Persistência, UPSERT e leitura de analytics. |
| Qualidade estática | Consistência de código | `ruff check` e `ruff format --check`. |
| Configuração | Compose válido antes de subir | `docker compose config --quiet`. |

## Comandos locais

```powershell
$env:RUN_POSTGRES_INTEGRATION = "1"
pytest
ruff check .
ruff format --check .
docker compose config --quiet
```

Os testes de integração dependem de PostgreSQL acessível e da variável `RUN_POSTGRES_INTEGRATION=1`. Essa escolha evita que a suíte pareça verde por ter ignorado silenciosamente testes que exigem infraestrutura.

## CI

GitHub Actions executa a suíte e Ruff em pushes e pull requests para `main`. O objetivo do CI não é substituir a demonstração manual: é impedir que regressões básicas, erros de formatação ou quebras do contrato avancem para a branch principal.

## Critério de mudança

Uma alteração que muda contrato, schema, comportamento de ML ou endpoint deve incluir teste proporcional e atualizar a documentação afetada. Alterações de migration devem ser testadas com banco limpo e com o caminho de upgrade, pois a compatibilidade de schema é parte do produto.
