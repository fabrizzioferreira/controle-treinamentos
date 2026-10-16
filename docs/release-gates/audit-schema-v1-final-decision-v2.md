# AUDIT-SCHEMA-V1 Final Decision V2

Data: 2026-06-07
Status anterior: PENDENTE
Decisao final: ADIADO COM RISCO ACEITO

## 1. Escopo da decisao

Esta decisao substitui o status `PENDENTE` de `AUDIT-SCHEMA-V1`.

Ela nao aprova migration, nao altera banco real, nao executa backfill, nao
executa restore, cleanup, seed, repair, bootstrap, backup real ou operacao
sensivel. Ela tambem nao aprova registro de dados sensiveis em claro.

Fontes lidas:

- `docs/release-gates/auditability-schema-upgrade-plan.md`
- `docs/release-gates/auditability-remediation.md`
- `docs/release-gates/audit-schema-v1-decision.md`
- `docs/release-gates/baseline-p0-after-final-remediation.md`

## 2. Decisao

`AUDIT-SCHEMA-V1` fica ADIADO COM RISCO ACEITO para o escopo estrito de
planejamento e documentacao da Frente 2.1.

O adiamento nao libera operacoes sensiveis reais nem reorganizacao fisica.
`AUDIT-SCHEMA-V1` continua sendo pre-condicao para qualquer execucao real que
exija ator anonimo/tecnico, correlacao nativa, checksum consultavel, trilha de
artifact metadata, migration, restore, cleanup, seed, repair, bootstrap, backup
real, jobs criticos ou DB real.

## 3. Owner, prazo e escopo do risco

Owner do risco de release: Release Gatekeeper.

Co-owners obrigatorios antes de qualquer implementacao ou execucao real:

- Security Architect: politica de dados sensiveis, IP, user-agent, actor_ref e
  artifact metadata.
- Data Architect/DBA: migration versionada, rollback, indices, backfill e
  validacao em banco descartavel.
- QA Lead: plano de testes e baseline apos implementacao.

Prazo para reavaliacao: ate 2026-06-14 ou antes do primeiro dry-run com banco
descartavel, o que ocorrer primeiro.

Escopo aceito:

- Avancar para 2.1 documental.
- Preparar proposta executavel de migration, dual-write, testes e rollback.
- Preparar runbook e matriz de dados sensiveis.

Escopo nao aceito:

- Aplicar migration.
- Iniciar reorganizacao fisica.
- Executar operacao sensivel real.
- Usar banco real como validacao.
- Rodar restore, cleanup, seed, repair, bootstrap ou backup real.
- Promover release com lacunas de auditoria nativa para operacoes sensiveis.

## 4. Justificativa

A remediacao atual ja fornece auditabilidade minima via `audit_metadata` em
JSONB para fluxos que passam por `record_audit_event`, com mascaramento de
credenciais e sem schema novo. A baseline P0 consolidada segura apos as quatro
remediacoes finais passou com `1448 passed, 0 failed, 0 errors`.

Mesmo assim, o plano `AUDIT-SCHEMA-V1` ainda nao pode ser aprovado para
aplicacao porque faltam:

- migration idempotente versionada;
- rollback ensaiado;
- politica final de minimizacao/retencao para IP e user-agent;
- politica final de `actor_ref` e artifact metadata;
- dual-write implementado e testado;
- teste de contrato de schema e indices;
- ambiente descartavel autorizado para migration/backfill/rollback.

Portanto, a decisao correta e aceitar temporariamente o risco somente para
documentacao e planejamento, mantendo os bloqueios operacionais.

## 5. Avaliacao por campo

| Item | Estado atual | Decisao |
| --- | --- | --- |
| IP | Parcial em JSONB quando ha contexto HTTP | Nao expandir ate politica de minimizacao/retencao; nativo fica adiado |
| user-agent | Parcial em JSONB quando ha contexto HTTP | Nao expandir ate politica de minimizacao/retencao; nativo fica adiado |
| request_id | Parcial em JSONB | Nativo/indexado exigido antes de operacoes sensiveis reais |
| correlation_id | Parcial em JSONB | Nativo/indexado exigido antes de operacoes sensiveis reais |
| resultado | Parcial em JSONB | Nativo exigido para compliance operacional |
| origem | Parcial em JSONB | Nativo exigido para scripts, jobs e operacoes nao HTTP |
| checksum | Parcial em helpers de documento/download | Nativo/indexado exigido para artifacts, backup e restore |
| artifact metadata | Parcial e nao nativo | Exige politica para nome/tamanho/hash sem conteudo bruto |
| ator anonimo/tecnico | Lacuna estrutural por FK `usuarios` | Bloqueia auth anonimo, scripts, jobs e operacoes sensiveis |
| dados sensiveis | Mascaramento parcial ja existe | Politica final obrigatoria antes da migration |
| migration | Nao criada/aplicada | Bloqueada ate artefato versionado |
| rollback | Diretriz futura, nao ensaiada | Bloqueia aprovacao/aplicacao |
| testes | Unit/contract seguros existem para JSONB parcial | Testes de schema/indices/dual-write ainda obrigatorios |
| ambiente descartavel | Nao autorizado para DB real | Bloqueia migration, backfill, rollback e E2E real |

## 6. Riscos aceitos

Riscos aceitos apenas para 2.1 documental:

- Consultas de compliance continuam dependentes de JSONB para parte dos
  metadados.
- Ator anonimo/tecnico ainda nao existe como campo nativo.
- Checksums e artifact metadata ainda nao sao consultaveis por indice nativo.
- IP e user-agent ainda exigem decisao formal de minimizacao e retencao antes
  de virar campo nativo.
- Operacoes sensiveis permanecem sem autorizacao real ate o schema ser
  implementado ou nova excecao formal ser aprovada.

Controles compensatorios enquanto o risco estiver aceito:

- Nao executar operacoes sensiveis reais.
- Nao usar banco real sensivel.
- Nao rodar migration, seed, restore, cleanup, repair ou bootstrap.
- Manter auditoria JSONB existente para fluxos seguros.
- Manter mascaramento de senha, token, secrets, CPF completo, telefone
  completo, email completo, foto, arquivo bruto e PDF bruto.
- Reavaliar a decisao ate o prazo definido.

## 7. Operacoes bloqueadas

Continuam bloqueadas:

- Aplicacao real de `AUDIT-SCHEMA-V1`.
- Migration real.
- Backfill real.
- Restore real.
- Cleanup real.
- Repair real.
- Seed real.
- Bootstrap real.
- Backup real como validacao de release.
- Scripts operacionais sensiveis.
- Endpoints destrutivos.
- E2E/DB real sem ambiente descartavel autorizado.
- Reorganizacao fisica.
- Operacoes financeiras estruturais sensiveis sem trilha nativa.
- Mudancas estruturais em RBAC/usuarios, documentos/downloads, jobs, backup e
  auditoria.

## 8. Impacto nos gates

Avancar para 2.1 documental: permitido com restricoes.

Iniciar reorganizacao fisica: bloqueado.

Executar operacoes sensiveis: bloqueado.

Promover release como verde pleno: bloqueado ate resolver as restricoes de
DB/E2E/operacoes sensiveis ou formalizar nova excecao com ambiente descartavel,
owner, prazo, rollback e politica de dados sensiveis.

## 9. Proximos requisitos obrigatorios

Antes de mudar esta decisao para `APROVADO` ou `APROVADO COM RESTRICOES`, devem
existir:

- migration idempotente versionada de `AUDIT-SCHEMA-V1`;
- politica de dados sensiveis para IP, user-agent, actor_ref e artifact
  metadata;
- rollback ensaiado em banco descartavel;
- testes de schema, indices, dual-write, mascaramento e fluxos sensiveis;
- evidencia de ambiente descartavel;
- baseline P0 reexecutada apos implementacao;
- aceite humano de Security, Data/DBA, QA, Release e Product/Financeiro quando
  aplicavel.

## 10. Resultado

Pendencia substituida: SIM.

Decisao final: ADIADO COM RISCO ACEITO.

Gate para 2.1 documental: liberado com restricoes.

Gate para reorganizacao fisica e operacoes sensiveis: bloqueado.
