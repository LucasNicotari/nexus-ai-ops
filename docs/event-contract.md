# Contrato de eventos operacionais

`OperationalEvent` é o contrato que une gerador, ingestão, qualidade, banco, analytics e ML. Criar um formato alternativo em uma nova integração quebraria essa rastreabilidade.

| Campo | Tipo | Regra | Exemplo |
| --- | --- | --- | --- |
| `event_id` | UUID/string | Identificador único e chave de idempotência | `f1c2...` |
| `timestamp` | datetime UTC | Precisa conter timezone | `2026-08-20T14:05:00+00:00` |
| `host` | string | Origem técnica do sinal | `worker-01` |
| `service` | string | Domínio operacional a priorizar | `billing-worker` |
| `metric_name` | string | Métrica conhecida pelo validador | `http_latency_ms` |
| `metric_value` | número | Dentro da faixa plausível da métrica | `842.7` |
| `unit` | string | Unidade compatível com a métrica | `ms` |
| `severity` | string | Classificação operacional | `warning` |
| `is_anomaly` | booleano | Rótulo sintético para avaliação | `true` |

## Regras importantes

O timestamp deve ser UTC para permitir ordenação e janelas temporais coerentes. `event_id` não é apenas um campo de auditoria: ele torna a carga idempotente no PostgreSQL. O campo `is_anomaly` é conhecido no dataset sintético para medir baselines; ele não entra como feature de treinamento, pois isso seria vazamento direto do alvo.

## Extensão segura

Novos campos devem ser adicionados de forma compatível e acompanhados de: atualização do contrato, regra de ingestão, migration se persistido, teste de qualidade e atualização desta documentação. Um conector externo deve converter seus dados para este contrato na borda do sistema, e não propagar seu formato proprietário pelo núcleo.
