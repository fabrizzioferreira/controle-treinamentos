# P0 - Grade de voo HTTP 500 - webreq-mq9klaed-n5afod4rkd

Data: 2026-06-11
Modulo: Financeiro / Lancamentos de Jornada
Severidade: P0

## Incidente

Falha informada pela tela ao gerar/lancar voo na grade:

- Mensagem: `Falha HTTP 500`
- Codigo exibido: `webreq-mq9klaed-n5afod4rkd`
- Tela: `#/financeiro/lancamentos-jornada`

O codigo `webreq-mq9klaed-n5afod4rkd` nao foi localizado literalmente nos logs do backend em `C:\srv\controle-treinamentos\logs` nem em `C:\srv-data\controle-treinamentos`. Isso indica que o codigo exibido pode ter sido gerado pelo cliente ao compor a falha HTTP. A investigacao usou tambem eventos de backend do mesmo endpoint.

## Endpoint

- Metodo: `POST`
- Path: `/api/v1/financeiro/lancamentos-jornada`
- View: `financeiro.api_finance_journey_line_create`
- Permissao: `finance:missions:create`
- Fluxo secundario: recalc automatico de bonificacao horaria e produtividade apos criacao da missao operacional.

## Evidencia de log correlata

Foi encontrado evento historico de `HTTP 500` no mesmo endpoint:

- Request: `webreq-mprb3hz3-ylfh988776`
- Usuario: `9`
- Release: `release_20260529_2885414_terceiro_sem_segundo`
- Causa tecnica registrada: excecao SQL em `listar_participacoes_produtividade_por_competencia`, com token literal `{_EFFECTIVE_CREW_FUNCTION_SQL}` dentro da query.
- Stack: `api_finance_journey_line_create -> criar_linha_jornada -> _recalculate_after_journey_save -> recalcular_competencia_financeira -> recalcular_produtividade_competencia`.

Mesmo com a query ja corrigida na release atual, o fluxo ainda tinha risco estrutural: a missao era criada com commit antes do recalc e antes da busca final da linha de jornada. Assim, uma falha posterior podia retornar erro para a tela deixando persistencia parcial.

## Reproducao segura

Foi executada reproducao com configuracao e banco de producao, porem com `db.commit` interceptado e `rollback` final:

- Caso normal: criou linha transacionalmente, recalculou e carregou a grade.
- Caso com falha SQL real forçada dentro do recalc: `select * from tabela_inexistente_para_testar_savepoint`.
- Resultado do caso forçado: a linha criada continuou localizavel na mesma transacao e o retorno passou a ser pendencia estruturada:
  - `status: pendente`
  - `error.code: finance_journey_auto_recalculation_failed`
  - `error.details.error_type: UndefinedTable`
- Confirmacao pos-teste: `persisted_test_missions = 0`.

Payload seguro usado na reproducao:

```json
{
  "competencia": "2026-06",
  "data_missao": "2026-06-11",
  "data": "2026-06-11",
  "data_final": "2026-06-11",
  "aeronave_id": 10,
  "categoria_financeira_aeronave": "b",
  "tripulante_id": 101,
  "funcao": "comandante",
  "comandante_tripulante_id": 101,
  "copiloto_tripulante_id": 12,
  "horario_apresentacao": "08:00",
  "horario_abandono": "10:00",
  "quantidade_pernoites": 0
}
```

## Causa raiz

O `POST /api/v1/financeiro/lancamentos-jornada` dependia de subrotinas com `commit()` e `rollback()` proprios:

- `criar_missao_operacional` comitava antes da linha de jornada ser finalizada.
- `recalcular_missao_operacional` comitava ou rollbackava dentro do fluxo de criacao.
- `recalcular_produtividade_competencia` aceitava `commit=False`, mas ainda fazia rollback total no `except`.

Isso tornava o fluxo nao atomico. Uma excecao inesperada no recalc automatico podia:

- devolver `HTTP 500` ao lancar voo;
- deixar missao/participantes persistidos antes da resposta final;
- exigir recalc manual posterior para normalizar a grade.

## Correcao

Aplicada correcao minima e transacional:

- `criar_missao_operacional(..., commit=False)` para uso por transacao externa.
- `recalcular_missao_operacional(..., commit=False)` para uso por transacao externa.
- `recalcular_competencia_financeira(..., commit=False)` para uso por transacao externa na release de producao.
- `recalcular_produtividade_competencia(..., commit=False)` deixa de executar rollback total quando o chamador controla a transacao.
- `criar_linha_jornada` agora faz um unico commit no final do fluxo.
- O recalc automatico da grade roda dentro de `SAVEPOINT finance_journey_recalc`.
- Falha inesperada no recalc automatico volta apenas ao savepoint e retorna pendencia estruturada, sem quebrar a transacao principal nem esconder a causa.
- Payload invalido continua propagando `DomainValidationError` com status 400/422 conforme a validacao.

## Testes executados

```text
.\.venv\Scripts\python -m pytest tests\unit\test_financeiro_lancamentos_jornada_application.py tests\unit\test_financeiro_missoes_application.py tests\unit\test_financeiro_bonificacoes_application.py -q
50 passed

.\.venv\Scripts\python -m pytest tests\architecture\test_financeiro_lancamentos_jornada_frontend.py tests\contract\test_financeiro_frontend_bonificacoes_horaria.py tests\unit\test_financeiro_competencias_application.py -q
38 passed
```

## Decisao

BLOQUEADOR REMOVIDO.

## Deploy

Release publicada em producao:

- `C:\srv\controle-treinamentos\releases\release_20260611_p0_grade_voo_savepoint`

Arquivos de runtime alterados na release:

- `backend/src/controle_treinamentos/application/financeiro_lancamentos_jornada.py`
- `backend/src/controle_treinamentos/application/financeiro_missoes.py`
- `backend/src/controle_treinamentos/application/financeiro_competencias.py`
- `backend/src/controle_treinamentos/application/financeiro_bonificacoes.py`

Validacoes da release candidata antes do restart:

- Caso normal sem commit: `ok=true`, `recalc_status=calculado`, `productivity_status=calculado`.
- Caso com SQL quebrado dentro do savepoint: `ok=true`, `recalc_status=pendente`, `error_code=finance_journey_auto_recalculation_failed`, `error_type=UndefinedTable`.
- Confirmacao de limpeza: `persisted_test_missions=0`.

Validacao pos-deploy:

- Servico `CT-App-Prod`: `Running`.
- `/healthz`: `status=ok`, `database=ok`.
- Logs de startup: `release_id=release_20260611_p0_grade_voo_savepoint`.
