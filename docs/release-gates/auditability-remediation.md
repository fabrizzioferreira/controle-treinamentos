# Auditability Remediation Evidence

Data: 2026-06-06
Status: remediado parcialmente sem schema; operacoes sensiveis reais continuam
bloqueadas.
Branch observada: `safety-baseline-financeiro-20260602-193550`
Worktree observado: sujo antes e depois.

## 1. Resumo executivo

Foi implementada auditabilidade minima compativel usando as colunas JSONB ja
existentes em `auditoria_eventos`. Nenhuma migration, seed, restore, cleanup,
backup real, script operacional destrutivo ou endpoint destrutivo foi executado.

O helper central `record_audit_event` agora adiciona `audit_metadata` operacional
quando tecnicamente disponivel: `request_id`, `correlation_id`, origem, endpoint,
path, metodo HTTP, IP, user-agent, resultado, sucesso/falha e checksum. O
enriquecimento preserva metadados existentes, incluindo eventos financeiros.

## 2. Fontes lidas

- `docs/release-gates/auditability-gate-register.md`
- `backend/src/controle_treinamentos/audit.py`
- `backend/src/controle_treinamentos/core/audit_utils.py`
- `backend/src/controle_treinamentos/blueprints/auth/routes.py`
- `backend/src/controle_treinamentos/db/schema.py`
- `backend/src/controle_treinamentos/financeiro_audit_events.py`

## 3. Lacunas auditaveis identificadas

| Area | Estado apos remediacao | Observacao |
| --- | --- | --- |
| Login sucesso | Parcial sem schema | Evento `auth.login.succeeded` best-effort quando ha DB configurado fora de `TESTING`. |
| Logout | Parcial sem schema | Evento `auth.logout.succeeded` best-effort para usuario autenticado. |
| Falha de login | Parcial | Usuario conhecido pode ser auditado; usuario inexistente exige schema/ator anonimo. |
| Usuarios/RBAC/role/permissao/desativacao | Parcial | Eventos existentes recebem envelope JSONB; acoes especificas ainda exigem testes por fluxo. |
| Financeiro/fechamento/reabertura/parametros | Parcial melhorado | `audit_metadata` existente e enriquecido sem sobrescrever contrato financeiro. |
| Tripulantes/treinamentos/anexos | Parcial melhorado | Eventos existentes passam a receber request metadata pelo helper central. |
| PDF/CSV/downloads | Parcial melhorado | Helpers aceitam `checksum` e `result` opcionais; preview permanece lacuna. |
| Backups/jobs | Parcial | Enqueue/requeue podem receber envelope; execucao final de backup ainda exige schema/plano. |
| Restore/scripts/cleanup/migrations/seeds | Bloqueado | Exigem ator tecnico, origem, resultado e checksums nativos antes de executar real. |

## 4. Correcoes feitas sem schema

- `record_audit_event` enriquece payloads com `audit_metadata` operacional.
- Campos vazios em `audit_metadata` sao preenchidos sem sobrescrever valores
  existentes.
- Quando evento nao tem payload anterior/novo, o helper cria payload minimo com
  `audit_metadata`.
- `audit_document_generation` aceita `checksum` e `result` opcionais.
- `audit_relevant_download` aceita `checksum` e `result` opcionais para downloads
  relevantes.
- Auth registra auditoria persistida best-effort para login sucesso, logout e
  falhas com usuario conhecido quando ha DB configurado em ambiente nao `TESTING`.
- Login hint e mascarado; senha/token/email completo nao sao persistidos.

## 5. Lacunas que exigem schema versionado

- Falha de login anonima ou usuario inexistente.
- Campos nativos e indexados para request/correlation/IP/user-agent/origem/
  resultado/checksum.
- Ator tecnico/anonimo/script/job sem violar FK de `usuarios`.
- Trilha mestre para restore, cleanup, migration, repair, seed e bootstrap.
- Ligacao nativa entre backups/jobs/artefatos e `auditoria_eventos`.

Plano criado: `docs/release-gates/auditability-schema-upgrade-plan.md`.

## 6. Dados sensiveis preservados

Continuam mascarados ou omitidos:

- Senha e hash de senha.
- Token, authorization, API key, cookie e secrets.
- CPF/documento completo.
- Telefone completo.
- Email completo.
- Foto, arquivo bruto, anexo e PDF bruto.
- Login de auth quando pode ser email: gravado apenas como hint mascarado.

## 7. Arquivos alterados

- `backend/src/controle_treinamentos/audit.py`
- `backend/src/controle_treinamentos/core/audit_utils.py`
- `backend/src/controle_treinamentos/blueprints/auth/routes.py`
- `tests/unit/test_audit_operational_context.py`
- `tests/unit/test_business_audit_utils.py`
- `docs/release-gates/auditability-schema-upgrade-plan.md`
- `docs/release-gates/auditability-remediation.md`

## 8. Testes adicionados ou reexecutados

Observacao: uma primeira tentativa do comando principal falhou com `5 failed, 27
passed` porque `create_app()` ainda recebeu um `DATABASE_URL` configurado no
ambiente de teste e a nova auditoria de auth tentou inserir eventos para
usuarios dublês inexistentes em `usuarios`. A FK de `auditoria_eventos` bloqueou
a escrita, nao houve commit valido, e a protecao foi ajustada para nao persistir
auth audit em `TESTING` salvo opt-in explicito `AUTH_AUDIT_ENABLED_IN_TESTING`.
A rodada aceita e a posterior, registrada abaixo.

Comando principal:

```powershell
& {
  $env:APP_ENV='testing'
  Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
  Remove-Item Env:E2E_DATABASE_URL -ErrorAction SilentlyContinue
  $env:PYTHONDONTWRITEBYTECODE='1'
  $baseTemp = Join-Path $env:TEMP ('pytest-audit-p0-' + [guid]::NewGuid().ToString('N'))
  .\.venv\Scripts\python.exe -m pytest -q --tb=short --disable-warnings -p no:cacheprovider --basetemp $baseTemp tests/unit/test_audit_hardening.py tests/unit/test_audit_utils_tripulante_payload.py tests/unit/test_business_audit_utils.py tests/unit/test_audit_operational_context.py tests/unit/test_financeiro_audit_events.py tests/contract/test_api_session_contract.py
}
```

Resultado: `32 passed in 18.57s`.

Comando ampliado:

```powershell
& {
  $env:APP_ENV='testing'
  Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
  Remove-Item Env:E2E_DATABASE_URL -ErrorAction SilentlyContinue
  $env:PYTHONDONTWRITEBYTECODE='1'
  $baseTemp = Join-Path $env:TEMP ('pytest-audit-p0-broad-' + [guid]::NewGuid().ToString('N'))
  .\.venv\Scripts\python.exe -m pytest -q --tb=short --disable-warnings -p no:cacheprovider --basetemp $baseTemp tests/unit/test_audit_hardening.py tests/unit/test_audit_utils_tripulante_payload.py tests/unit/test_business_audit_utils.py tests/unit/test_audit_operational_context.py tests/unit/test_financeiro_audit_events.py tests/unit/test_financeiro_missoes_application.py tests/unit/test_financeiro_parametros_application.py tests/unit/test_financeiro_feriados_application.py tests/unit/test_financeiro_competencias_application.py tests/unit/test_financeiro_relatorios_application.py tests/unit/test_financeiro_produtividade_relatorio_geral.py tests/unit/test_financeiro_horas_totais_voadas.py tests/contract/test_api_session_contract.py tests/contract/test_api_tripulante_media_contract.py tests/contract/test_api_treinamentos_contract.py tests/contract/test_api_training_program_contract.py tests/contract/test_pdf_export_contracts.py
}
```

Resultado: `192 passed in 124.41s`.

## 9. Operacoes nao executadas

- Operacao sensivel real: NAO EXECUTADA.
- Migration: NAO EXECUTADA.
- Seed: NAO EXECUTADO.
- Restore: NAO EXECUTADO.
- Cleanup: NAO EXECUTADO.
- Backup real: NAO EXECUTADO.
- Endpoint destrutivo: NAO EXECUTADO.
- Banco real nos comandos aceitos: NAO USADO intencionalmente.
- Alteracao de schema: NAO EXECUTADA.

## 10. Operacoes ainda bloqueadas

- Falha de login anonima com auditoria persistida nativa.
- Scripts de restore/postcheck.
- Cleanup operacional e cleanup de auditoria.
- Migration, repair, bootstrap e seed.
- Execucao final de backup ligada nativamente a ator/request/checksum.
- Preview de documento como auditoria persistida obrigatoria.
- Qualquer operacao sensivel sem teste de auditoria dedicado e validacao humana.

## 11. Resultado do gate

Liberacao parcial tecnica: eventos que ja passam por `record_audit_event` agora
recebem envelope operacional minimo sem schema. O gate completo permanece
bloqueado para operacoes que exigem ator anonimo/tecnico, colunas nativas,
checksums consultaveis, scripts operacionais ou banco real isolado.

## 12. Proximo passo

Rodar P0 consolidado nao destrutivo e, em seguida, planejar `AUDIT-SCHEMA-V1` em
ambiente isolado com migration versionada, dual-write e backfill validado por
teste. Rollback ou validacao real exige aprovacao humana.
