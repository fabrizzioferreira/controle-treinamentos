# External Artifacts Inventory

Status: BLOQUEADO PARA LIMPEZA, REMOCAO OU REORGANIZACAO FISICA
Data: 2026-06-06
Escopo: artefatos externos, areas nao-fonte, builds locais, evidencias, wrappers, runtime, archives e referencias operacionais.

Este documento e um gate de preservacao. Ele nao autoriza apagar, mover, renomear, compactar, limpar, executar scripts, executar ferramentas `manual_unsafe`, alterar `.gitignore` ou reclassificar artefatos sem validacao humana.

## 1. Resumo executivo

Foram inventariadas as areas candidatas a limpeza antes da reorganizacao fisica. A regra aplicada foi conservadora: se ha duvida, referencia documental, wrapper, evidencia, worktree, build publicavel, manifest, historico, consumidor externo provavel ou ausencia de prova de nao uso, o item permanece preservado ou bloqueado.

Principais conclusoes:

- `archive/` tem `README.md` e `MANIFEST.md` e guarda snapshots, backups, copia aninhada e wrappers antigos classificados. Nao e fonte viva, mas tambem nao pode ser limpo sem provar perda de valor historico e ausencia de consumidor externo.
- `legacy/` e legado vivo documentado por `legacy/LIVE_LEGACY.md`; nao e area descartavel.
- `runtime/` contem evidencias, builds, perfis de browser, outputs P0, patches, PDFs, worktrees e snapshots locais. Tambem ha worktrees Git registrados dentro e fora do workspace.
- `frontend/dist/` e saida canonica gerada/publicavel do build, com `asset-manifest.json`; nao e fonte, mas pode ser necessario para validacao/publicacao atual.
- `frontend/runtime/`, `frontend/frontend/` e `frontend/ops/artifacts/` contem historico operacional e builds gerados. Permanecem bloqueados para limpeza em lote.
- `ops/artifacts/` contem evidencias de financeiro, HML/prod smoke, seguranca, clusters de teste, caches e perfis de browser. A propria governanca diz que e excecao local de evidencia historica, nao input canonico.
- `scripts/` contem wrappers historicos de compatibilidade protegidos por documentacao e teste; ausencia de consumidor externo nao foi provada.
- `backend/tools/manual_unsafe/` e explicitamente perigoso/manual; preservar e nao executar.
- PDFs na raiz e em `docs/reports/` sao relatorios e laudos de auditoria/diagnostico; preservar ate catalogacao documental.

Fontes reais consultadas:

- `README.md`
- `archive/README.md`
- `archive/MANIFEST.md`
- `legacy/README.md`
- `legacy/LIVE_LEGACY.md`
- `scripts/README.md`
- `ops/README.md`
- `frontend/README.md`
- `frontend/dist/asset-manifest.json`
- `frontend/frontend/dist/asset-manifest.json`
- `docs/governance/legacy-policy.md`
- `docs/governance/repo-topology.md`
- `docs/governance/root-entry-policy.md`
- `docs/governance/technical-conventions.md`
- `docs/operations/canonical-commands.md`
- `docs/operations/WINDOWS_SELF_HOSTED_SERVER.md`
- `docs/operations/RUNBOOK.md`
- `tests/unit/test_legacy_windows_compat.py`
- `ops/scripts/repo/validate_repo_hygiene.py`
- `git worktree list --porcelain`

## 2. Arquivo criado

Arquivo novo:

- `docs/release-gates/external-artifacts-inventory.md`

Arquivos existentes alterados:

- Nenhum.

Operacoes proibidas nao realizadas:

- Nada foi apagado.
- Nada foi movido.
- Nada foi renomeado.
- Nenhuma pasta foi limpa.
- Nenhum script foi executado.
- Nenhuma ferramenta `manual_unsafe` foi executada.
- Nenhum artefato foi compactado.
- `.gitignore` nao foi alterado.

## 3. Areas inventariadas

| Path | Existe | Tipo | Contagem observada | Origem provavel | Finalidade | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `archive/` | Sim | Historico classificado | 604 arquivos | Movimentacoes antigas, snapshots e backups classificados | Auditoria, comparacao e historico | Preservar |
| `legacy/` | Sim | Legado vivo documentado | 7 arquivos | Frentes de consolidacao/compat | Registro de fluxos ainda vivos | Bloqueado |
| `runtime/` | Sim | Evidencia/runtime local | 27809 arquivos | Builds, QA, browser profiles, worktrees, smokes | Evidencias operacionais e scratch local | Bloqueado |
| `frontend/dist/` | Sim | Build gerado/publicavel | 55 arquivos | `frontend/scripts/build_frontend.py` | Artefato SPA separado | Revisar, nao limpar agora |
| `frontend/runtime/` | Sim | Historico operacional frontend | 2833 arquivos | Builds/checks/auditorias frontend | Evidencias de build/QA visual | Bloqueado |
| `frontend/frontend/` | Sim | Nested frontend artifact | 55 arquivos | Copia/build anterior com `dist/` e `runtime/` | Evidencia ou residuo historico a validar | Bloqueado |
| `frontend/ops/artifacts/` | Sim | Artefatos frontend ops | 52 arquivos | QA responsivo financeiro | Evidencia visual/build | Bloqueado |
| `ops/artifacts/` | Sim | Evidencias operacionais | 4606 arquivos | HML/prod smoke, financeiro, security, clusters, caches | Evidencia operacional historica | Bloqueado |
| `scripts/` | Sim | Wrappers de compatibilidade | 7 arquivos | Caminhos historicos de CLI/Windows | Compatibilidade para consumidores antigos | Bloqueado |
| `backend/tools/` | Sim | Ferramentas operacionais | 17 arquivos | Runtime/manutencao/data/manual unsafe/compat | Entrypoints canonicos e perigosos isolados | Preservar |
| `backend/tools/manual_unsafe/` | Sim | Ferramentas manuais perigosas | 4 arquivos | Repair, cleanup e remocao schema historica | Uso manual com risco operacional | Bloqueado |
| `backend/tools/compat_residual/` | Sim | Compat residual | 2 arquivos | Sync snapshot historico | Caminho residual documentado | Bloqueado |
| `docs/reports/` | Sim | Relatorios e evidencias documentais | 6 arquivos | Auditorias e relatorios de execucao | Evidencia formal | Preservar |
| PDFs na raiz | Sim | Laudos/relatorios | 5 PDFs | Auditoria, diagnostico e mapeamento | Evidencia documental | Preservar |
| Worktrees Git | Sim | Worktrees locais/externos | 13 entradas em `git worktree list` | Releases/codex/hotfixes | Estados de release e comparacao | Bloqueado |
| Logs/dumps/backups/builds | Sim | Artefatos gerados | 554 `.log`, 50 `.dmp`, 30 `.gz`, 182 `.pdf` nas areas de evidencia | Browser, QA, backup/drill, artefatos | Evidencia e diagnostico | Bloqueado |

## 4. Archive

| Path | Tipo | Evidencia | Consumidor interno encontrado | Consumidor externo provavel | Risco de apagar | Risco de mover | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `archive/README.md` | Governanca local | Define que nada em `archive/` deve ser importado, executado, buildado, testado ou usado em release | `README.md`, `docs/governance/legacy-policy.md`, `docs/governance/repo-topology.md` | Auditores e revisores historicos | Alto: perde regra de classificacao | Alto: quebra referencias de governanca | Preservar |
| `archive/MANIFEST.md` | Manifest de inventario | Lista `repo-snapshots`, `temp-backups`, `old-wrappers` e copia aninhada | Governance docs e README | Auditoria/review externo | Critico: perde origem, motivo e status | Alto: caminhos manifestados deixam de bater | Preservar |
| `archive/repo-snapshots/` | Snapshots de build | Builds `frontend-build-prod-*` e hotfixes | `archive/MANIFEST.md`, `docs/governance/tmp-classification.md` | Comparacao historica de frontend | Alto: perde baseline visual/build | Medio/alto: docs apontam para caminho | Preservar |
| `archive/temp-backups/` | Backups temporarios classificados | `src-app-backup-*`, `nested-repo-copy-*`, smoke JSON, rollback manifest | `archive/MANIFEST.md`, repo topology | Auditoria, rollback historico, comparacao antiga | Critico: perda de arvore antiga e evidencias | Critico: copia aninhada tem regra propria | Bloqueado |
| `archive/old-wrappers/` | Wrappers antigos | Backups de entrypoints antigos | `archive/MANIFEST.md`, `legacy-policy.md` | Consumidor historico nao comprovado ausente | Alto: perde trilha de migracao | Alto: quebra referencias historicas | Preservar |

Decisao: `archive/` nao e fonte viva, mas fica preservado. Limpeza futura exige revisar `archive/MANIFEST.md`, provar ausencia de referencia viva e ausencia de valor de auditoria.

## 5. Legacy

| Path | Tipo | Evidencia | Consumidor interno encontrado | Consumidor externo provavel | Risco de apagar | Risco de mover | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `legacy/README.md` | Governanca de legado vivo | Declara que `legacy/` existe porque ha fluxos ainda usados/testados | `README.md`, `docs/governance/legacy-policy.md`, `repo-topology.md` | Equipe que opera SSR/documentos | Critico: remove criterio de permanencia | Alto: referencias e criterios quebram | Bloqueado |
| `legacy/LIVE_LEGACY.md` | Inventario de legado vivo | Lista SSR, operacoes SSR compat, File legado, midia/status de tripulante | Contratos SSR/API, docs, tests | Usuarios com bookmarks/rotas SSR | Critico: apaga justificativa de compat | Critico: aparenta liberar remocao indevida | Bloqueado |
| `legacy/domains/` | Dominio legado | SSR HTML e fluxos vivos | `legacy/LIVE_LEGACY.md` | Operacao que ainda usa SSR | Alto | Alto | Bloqueado |
| `legacy/data-compat/` | Compat de dados | Midia/status de tripulante e formatos antigos | `legacy/LIVE_LEGACY.md`, contracts/tests de compat residual | Bancos historicos/restores | Critico: quebra leitura de dados antigos | Critico: muda semantica de compat | Bloqueado |

Decisao: `legacy/` nao pode ser limpo, movido ou tratado como backlog removivel. Saida exige consumidor substituto, teste, contrato atualizado e validacao humana.

## 6. Runtime

| Path | Tipo | Evidencia | Consumidor interno encontrado | Consumidor externo provavel | Risco de apagar | Risco de mover | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `runtime/` | Scratch/evidencia local | `repo-topology.md` e `root-entry-policy.md` classificam como excecao local gitignored, nao fonte | Docs de release gates e relatorios citam evidencias; `git worktree list` registra worktrees | Operadores, QA, Codex/release worktrees | Critico: perda de evidencia P0, QA, patches, worktrees | Critico: worktrees podem quebrar Git | Bloqueado |
| `runtime/pytest-baseline-p0-*` | Evidencia QA P0 | Pastas P0 recentes de 2026-06-06 | `docs/release-gates/baseline-p0-execution.md` depende de evidencias | Gatekeepers/QA | Critico: apaga prova de baseline vermelha/bloqueada | Alto | Bloqueado |
| `runtime/worktrees/terceiro-tripulante` | Worktree Git | Registrado em `git worktree list --porcelain` | Git metadata | Git/worktree externo e comparacao de release | Critico: corrompe worktree | Critico: mover sem `git worktree` quebra repo | Bloqueado |
| `runtime/codex-release-cobertura-branch` | Worktree Git | Registrado em `git worktree list --porcelain` | Git metadata | Branch `codex/cobertura-base-participante-prod` | Critico | Critico | Bloqueado |
| `runtime/frontend-build-*` | Builds locais | Varios builds frontend listados | Relatorios e validacoes frontend | QA visual e comparacao | Alto: perde comparacao de build | Medio/alto | Bloqueado |
| `runtime/evidence/` | Evidencias operacionais | Smokes, db-cleanups, JSONs | Release/baseline docs | Auditoria operacional | Critico: perde evidencia de execucao | Alto | Bloqueado |
| `runtime/release-gate-browser-validation/` | Perfil/validacao browser | Perfis Edge/Chrome e logs | Browser validation | QA manual | Alto | Medio/alto | Bloqueado |
| `runtime/tmp/` | Temporarios e builds | Muitos `asset-manifest.json`, perfis browser e builds | Pode conter evidencia nao consolidada | Investigacao/hotfix local | Alto ate classificar | Alto | Revisar depois |
| `runtime/*.pdf`, `runtime/*.png`, `runtime/*.patch`, `runtime/smoke-*.json` | Evidencia solta | PDFs financeiros QA, screenshot prod, patch e smokes | Relatorios/QA | Auditoria e comparacao | Alto | Medio | Preservar |

Decisao: `runtime/` fica bloqueado para limpeza em lote. Itens revisaveis so podem sair apos classificacao por lote, checksum/manifests e confirmacao de que nao sao worktree, evidencia P0, release, smoke, backup ou auditoria.

## 7. Frontend dist/runtime

| Path | Tipo | Evidencia | Consumidor interno encontrado | Consumidor externo provavel | Risco de apagar | Risco de mover | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `frontend/dist/` | Build gerado/publicavel | `frontend/README.md` e `docs/operations/canonical-commands.md`; `asset-manifest.json` com `build_version_utc=20260601-175754` | Build/publish docs, README, repo topology | Servidor HTTP estatico externo, HML/prod publish | Alto: quebra validacao/publish local corrente | Alto: paths publicaveis e manifests deixam de bater | Revisar, nao limpar agora |
| `frontend/dist/asset-manifest.json` | Manifest de build | Lista entrypoints fingerprintados | Frontend build/publish | Cache/publish externo | Alto: perde mapa de assets | Alto | Preservar com `dist/` |
| `frontend/runtime/` | Evidencias frontend | 2833 arquivos; builds/checks/auditorias | `docs/reports/relatorio-execucao-chat-task-force-2026-05-02.md` diz que nao foi limpo para preservar evidencia | QA visual e release | Alto: perda de historico operacional | Medio/alto | Bloqueado |
| `frontend/frontend/` | Nested frontend output | Contem `dist/` e `runtime/`; manifest `build_version_utc=20260529-181050` | `docs/reports` menciona `frontend/frontend/runtime` como historico fora de fonte viva | Possivel referencia local antiga | Alto ate provar origem/nao uso | Alto | Bloqueado |
| `frontend/ops/artifacts/` | Artefatos frontend ops | `financeiro-responsive/20260430-110311` | Docs relatorio e QA | Evidencia visual financeira | Alto: perde evidencia responsiva | Medio/alto | Bloqueado |

Decisao: `frontend/dist/` nao e fonte viva, mas e build gerado/publicavel no caminho canonico. Nao limpar sem provar que novo build foi gerado, publicado, validado e que nenhum servidor externo serve esse diretorio.

## 8. Ops artifacts

| Path | Tipo | Evidencia | Consumidor interno encontrado | Consumidor externo provavel | Risco de apagar | Risco de mover | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ops/artifacts/` | Evidencia operacional historica | `repo-topology.md` e `root-entry-policy.md` tratam como excecao local de artifacts/evidencias | Relatorios e release gates | Auditoria de prod/HML, financeiro, security | Critico: perde provas operacionais | Alto: docs e pacotes podem apontar | Bloqueado |
| `ops/artifacts/financeiro-*` | Evidencia financeira | HML governance, prod parameters, prod release, QA, responsive, URL audit | Financeiro release docs/tests | Auditoria financeira | Critico: financeiro sensivel | Alto | Bloqueado |
| `ops/artifacts/dashboard-operacional-*` | Smoke dashboard | HML/prod smoke | Dashboard ops | Suporte operacional | Alto | Medio | Bloqueado |
| `ops/artifacts/security/` | Evidencia security | Pasta `security` | Security/release | Auditoria de seguranca | Critico | Alto | Bloqueado |
| `ops/artifacts/pg_*_cluster` | Clusters de teste | `pg_finance_test_cluster`, `pg_test_cluster` | Testes/QA DB | Validacao local | Alto ate classificar | Alto | Bloqueado |
| `ops/artifacts/ruff-cache*` | Cache/tooling | `ruff-cache`, `ruff-cache-run*` | Possivel hygiene/build logs | Nenhum confirmado | Baixo/medio, mas misturado em evidencia | Medio | Revisar depois |

Decisao: nao limpar `ops/artifacts/` em lote. Mesmo caches aparentemente revisaveis ficam preservados ate separar evidencias financeiras, security e prod.

## 9. Scripts/wrappers

| Path | Tipo | Evidencia | Consumidor interno encontrado | Consumidor externo provavel | Risco de apagar | Risco de mover | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `scripts/README.md` | Governanca de wrappers | Declara `scripts/` como compat controlada e fila de remocao | `README.md`, `legacy-policy.md`, `tests/unit/test_legacy_windows_compat.py` | Operadores antigos | Alto | Alto | Preservar |
| `scripts/backup/run_backups.py` | Wrapper compat | Delegado para `backend/tools/maintenance/run_backups.py` | Teste de shim e docs | Job/atalho externo de backup | Critico: backup antigo pode parar | Alto | Bloqueado |
| `scripts/database/run_db_consistency.py` | Wrapper compat | Delegado para `backend/tools/maintenance/run_db_consistency.py` | Teste de shim e docs | Rotina manual/atalho externo | Alto | Alto | Bloqueado |
| `scripts/jobs/run_jobs_worker.py` | Wrapper compat | Delegado para `backend/tools/maintenance/run_jobs_worker.py` | Teste de shim e docs | Agendador/worker antigo | Critico: jobs podem parar | Alto | Bloqueado |
| `scripts/jobs/run_notifications.py` | Wrapper compat | Delegado para `backend/tools/maintenance/run_notifications.py` | Teste de shim e docs | Chamada externa/manual antiga | Alto | Alto | Bloqueado |
| `scripts/windows/Invoke-AppService.ps1` | Wrapper Windows compat | Delegado para `ops/windows/scripts/Invoke-AppService.ps1`; docs migration citam service XML historico | Teste de shim e docs | Windows Service/atalho antigo | Critico: app pode nao subir | Critico | Bloqueado |
| `scripts/windows/Invoke-OperationalPython.ps1` | Wrapper Windows compat | Delegado para `ops/windows/scripts/Invoke-OperationalPython.ps1` | Teste de shim e docs | Task Scheduler antigo | Critico: rotinas podem parar | Critico | Bloqueado |
| `archive/old-wrappers/*.py` | Wrappers antigos arquivados | `archive/MANIFEST.md` | Historico | Consumidor antigo nao comprovado ausente | Alto historico | Alto | Preservar |

Decisao: `scripts/` nao fica liberado para remocao. A ausencia de consumidor operacional no repo nao prova ausencia externa.

## 10. Backend tools/manual unsafe

| Path | Tipo | Evidencia | Consumidor interno encontrado | Consumidor externo provavel | Risco de apagar | Risco de mover | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `backend/tools/runtime/run.py` | Runtime local canonico | `README.md`, `Makefile`, `canonical-commands.md` | Makefile `dev`, docs local runtime | Desenvolvedores/operacao local | Alto | Alto | Preservar |
| `backend/tools/maintenance/` | Manutencao canonica | `canonical-commands.md`, `RUNBOOK.md` | Backup, worker, notificacao, consistency, bootstrap | Task Scheduler/ops Windows | Critico | Critico | Preservar |
| `backend/tools/data/import_tripulantes_csv.py` | Import manual de dados | `repo-topology.md`, `DATABASE_EVOLUTION.md` | Ops/database | Operacao manual | Alto | Alto | Preservar |
| `backend/tools/manual_unsafe/cleanup_operational_data.py` | Cleanup destrutivo | `canonical-commands.md`, `RUNBOOK.md`, auditability gate | Manual unsafe | Operacao emergencial | Critico: perde ferramenta controlada | Critico: pode parecer seguro se movido | Bloqueado |
| `backend/tools/manual_unsafe/run_db_repair.py` | Repair manual perigoso | `canonical-commands.md`; `run_db_consistency.py --repair` redireciona | Database evolution, release gates | Operador DBA | Critico | Critico | Bloqueado |
| `backend/tools/manual_unsafe/remove_painel_tv_produtividade_schema.py` | Ferramenta historica perigosa | Docs de migracao citam remocao schema historica | Migration docs | Bancos historicos | Critico | Critico | Bloqueado |
| `backend/tools/compat_residual/sync_tripulantes_snapshot.py` | Compat residual | `canonical-commands.md`, `DATABASE_EVOLUTION.md` | Ops/database e testes de restore/compat | Homologacao/restore legado | Alto | Alto | Bloqueado |

Decisao: ferramentas `manual_unsafe` ficam congeladas e nao devem ser executadas neste gate. Mover poderia mascarar risco ou quebrar documentacao operacional.

## 11. PDFs e relatorios

| Path | Tipo | Evidencia | Consumidor interno encontrado | Consumidor externo provavel | Risco de apagar | Risco de mover | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `laudo-abas-treinamentos-e-equipamentos.pdf` | PDF raiz | Listagem raiz | Auditoria/manual | Stakeholders de produto | Alto | Medio/alto | Preservar |
| `laudo-auditoria-riscos-baseline-validacao-saas.pdf` | PDF raiz | Listagem raiz | Gate de auditoria | Auditoria/release | Alto | Medio/alto | Preservar |
| `relatorio-auditoria-rica-10-prompts-producao-20260606.pdf` | PDF raiz | Listagem raiz | Frente 1.4/release gates | Auditoria executiva | Alto | Medio/alto | Preservar |
| `relatorio-consolidado-diagnostico-repositorio-saas.pdf` | PDF raiz | Listagem raiz | Diagnostico repo | Governanca | Alto | Medio | Preservar |
| `relatorio-consolidado-mapeamento-funcional-produto-saas.pdf` | PDF raiz | Listagem raiz | Mapeamento funcional | Produto/operacao | Alto | Medio | Preservar |
| `docs/reports/*.pdf` | Relatorios formais | 4 PDFs em `docs/reports/` | Release gates e Frentes | Auditoria/reorganizacao | Alto | Medio | Preservar |
| `docs/reports/*.md` | Relatorios formais | `baseline-correcao-*`, `relatorio-execucao-chat-task-force-*` | Docs/reports; contem referencias a `frontend/dist`, runtime e artifacts | Auditoria historica | Alto | Medio | Preservar |
| `runtime/*.pdf` | PDFs QA financeiro | PDFs de bonificacao/produtividade QA | QA financeiro | Auditoria financeira | Alto | Medio | Bloqueado |
| `docs/archive/product/*.pdf` | Manual/documento historico | Encontrado em inventarios de arquivos | Docs archive | Usuarios/historico | Alto | Medio | Preservar |

Decisao: PDFs na raiz sao candidatos a futura reclassificacao documental, nao a remocao. Antes de mover, validar links externos, relatorios de auditoria e docs que os referenciam.

## 12. Consumidores internos encontrados

| Consumidor | Referencias encontradas | Impacto |
| --- | --- | --- |
| `README.md` | `frontend/dist`, `archive/`, `legacy/`, `scripts/`, `backend/tools`, `ops/windows` | Onboarding e comandos atuais dependem desses nomes |
| `docs/governance/repo-topology.md` | Define `archive`, `legacy`, `scripts`, `runtime`, `ops/artifacts`, `frontend/dist`, `backend/tools` | Fonte de governanca da topologia |
| `docs/governance/root-entry-policy.md` | Define excecoes para `frontend/dist` e `ops/artifacts`; proibe dumps/backups soltos | Base para qualquer limpeza futura |
| `docs/governance/legacy-policy.md` | Define compat, legacy, archive e remocao | Bloqueia remocao sem prova |
| `docs/operations/canonical-commands.md` | Comandos oficiais em `backend/tools`, `ops/windows`, `frontend/scripts` | Operacao e release dependem dos caminhos |
| `docs/operations/WINDOWS_SELF_HOSTED_SERVER.md` | `Invoke-AppService.ps1`, `Invoke-OperationalPython.ps1`, Task Scheduler, C:\srv paths | Operacao Windows/self-hosted |
| `scripts/README.md` | Lista wrappers mantidos e fila de remocao | Wrapper nao pode sair sem auditoria externa |
| `tests/unit/test_legacy_windows_compat.py` | Verifica existencia dos wrappers de `scripts/` | Teste protege compat |
| `ops/scripts/repo/validate_repo_hygiene.py` | Reconhece wrappers e governanca estrutural | Hygiene pode falhar se path mudar |
| `Makefile` | Usa `backend/tools/runtime/run.py`; target de release gate | Entrypoint local |
| `frontend/README.md` | Define build em `frontend/dist` e necessidade de HTTP externo | Publicacao/validacao frontend |
| `archive/MANIFEST.md` | Registra origem/status de archive | Auditoria historica |
| `legacy/LIVE_LEGACY.md` | Registra legado vivo | Bloqueia extracao/remocao sem substituto |
| `docs/reports/relatorio-execucao-chat-task-force-2026-05-02.md` | Cita `frontend/dist`, `frontend/runtime`, `frontend/frontend/runtime`, `frontend/ops/artifacts` e decisao de nao limpar evidencias | Evidencia que limpeza em lote ja foi evitada por razao operacional |
| `git worktree list --porcelain` | Registra worktrees dentro de `runtime/` e em `C:/srv/...` | Move/delete manual pode corromper worktrees |

## 13. Consumidores externos provaveis

| Area | Consumidor externo provavel | Evidencia | Risco |
| --- | --- | --- | --- |
| `scripts/windows/*` | Windows Service antigo, service XML, atalhos | `scripts/README.md`, docs migration de provisionamento e teste de shim | App ou rotinas deixam de subir |
| `ops/windows/scripts/*` | Windows Services e Task Scheduler oficiais | `docs/operations/WINDOWS_SELF_HOSTED_SERVER.md`, `Install-WindowsServices.ps1` | Operacao self-hosted quebra |
| `backend/tools/maintenance/*` | Task Scheduler, operadores e runbooks | `canonical-commands.md`, `RUNBOOK.md` | Backup, worker, notificacoes e consistencia param |
| `frontend/dist/` | Servidor HTTP estatico externo/HML/prod | `frontend/README.md`, `canonical-commands.md` | SPA publicada pode perder assets |
| `ops/artifacts/financeiro-*` | Auditoria financeira/release | Nomes HML/prod/governance e relatorios | Perda de evidencia sensivel |
| `runtime/evidence`, `runtime/pytest-baseline-p0-*` | QA/release gate | Baseline P0 e outputs recentes | Perda de evidencia formal |
| `archive/temp-backups/nested-repo-copy-*` | Automacao externa antiga nao comprovada ausente | `archive/MANIFEST.md`, `repo-topology.md` | Remocao pode quebrar path historico |
| `runtime/worktrees/*` e `C:/srv/...` | Git worktrees externos/releases | `git worktree list --porcelain` | Corrupcao de worktree/release |
| PDFs raiz e `docs/reports` | Stakeholders, auditoria e produto | Nomes de laudo/relatorio e docs release | Perda de contexto decisorio |

## 14. Itens bloqueados para remocao

| Item | Motivo do bloqueio |
| --- | --- |
| `archive/` inteiro | Tem manifest, historico classificado e copia aninhada com regra de saida |
| `legacy/` inteiro | E legado vivo, nao backlog removivel |
| `runtime/worktrees/*` | Registrado pelo Git como worktree |
| `runtime/pytest-baseline-p0-*` | Evidencia de baseline P0 |
| `runtime/evidence/` | Evidencia operacional |
| `runtime/release-gate-browser-validation/` | Evidencia de validacao browser |
| `frontend/dist/` | Build gerado/publicavel no caminho canonico; precisa validacao antes de limpeza |
| `frontend/runtime/` | Historico operacional frontend |
| `frontend/frontend/` | Nested artifact sem prova de nao uso |
| `frontend/ops/artifacts/` | Evidencia visual/financeira |
| `ops/artifacts/financeiro-*` | Evidencia financeira HML/prod/QA |
| `ops/artifacts/security/` | Evidencia de seguranca |
| `scripts/**` | Wrappers de compatibilidade congelados |
| `backend/tools/manual_unsafe/**` | Ferramentas perigosas, documentadas e isoladas |
| `backend/tools/compat_residual/**` | Caminho residual documentado |
| PDFs na raiz | Relatorios/laudos sem catalogacao final |
| `docs/reports/**` | Relatorios de auditoria e execucao |
| Worktrees externos `C:/srv/controle-treinamentos/releases/*` | Registrados pelo Git, fora do workspace |

## 15. Itens revisaveis no futuro

Estes itens nao estao liberados para limpeza agora; apenas podem entrar em uma frente futura de revisao com evidencia:

| Item | Por que pode ser revisavel | Pre-condicao |
| --- | --- | --- |
| `runtime/tmp/` | Parece conter muitos builds e perfis temporarios | Classificar por lote, preservar manifests/checksums e excluir worktree/evidencia |
| `ops/artifacts/ruff-cache*` | Aparencia de cache de tooling | Separar de evidencias financeiras/security e validar hygiene |
| Perfis de browser em `runtime/*profile*` e `ops/artifacts/**/chrome-*` | Podem ser caches de validacao | Confirmar que screenshots/logs/manifests ja foram extraidos |
| `frontend/frontend/` | Pode ser nested build antigo | Provar ausencia de referencia externa e registrar origem |
| PDFs raiz | Podem ser movidos para `docs/reports` ou `docs/archive` | Catalogar links externos, owners e valor de auditoria |
| `archive/repo-snapshots/frontend-*` | Snapshots antigos de build | Provar que nao ha comparacao/auditoria pendente |
| `archive/temp-backups/*` | Backups historicos | Provar ausencia externa, sem valor de auditoria e registrar decisao |
| `.dmp`, `.log`, `.gz` em areas de runtime/artifacts | Alguns podem ser dumps/caches de browser | Separar evidencias de suporte antes de descartar |

## 16. Criterios para limpeza futura

Nenhuma limpeza futura deve ocorrer sem todos os criterios aplicaveis:

1. Owner humano identificado para a area.
2. Classificacao explicita: fonte, compat, legacy, archive, evidencia, build, cache, dump, backup ou log.
3. Busca interna por path em docs, scripts, configs, tests e workflows.
4. Busca externa ou declaracao assinada para Windows Services, Task Scheduler, atalhos, servidores HTTP, releases `C:/srv`, cron e runbooks fora do repo.
5. Para worktrees: usar fluxo Git proprio, nunca delete/move manual de pasta.
6. Para `frontend/dist/`: gerar build novo, comparar `asset-manifest.json`, validar publicacao HTTP e confirmar que nenhum host serve o diretorio atual.
7. Para `ops/artifacts` e `runtime`: preservar manifest/checksum das evidencias que ficarem fora do repo.
8. Para PDFs/relatorios: catalogar destino documental e preservar links ou redirecionamentos.
9. Para wrappers: provar consumidor externo migrado ou ausente e atualizar `scripts/README.md`, testes de shim e docs operacionais.
10. Para `manual_unsafe`: manter isolamento e nao transformar em comando recorrente.
11. Para archive/legacy: atualizar manifest/inventario antes de qualquer remocao.
12. Validacao humana final registrada em release gate.

## 17. Proximo passo recomendado

Criar uma frente especifica de "external reference audit" antes de qualquer limpeza. Essa frente deve validar Windows Services, Task Scheduler, atalhos locais, servidor estatico frontend, worktrees `C:/srv`, relatorios de auditoria e artefatos financeiros. Ate essa auditoria existir, tratar este inventario como gate bloqueante: preservar tudo que esta listado como bloqueado ou preservar, e revisar apenas os itens classificados como revisaveis no futuro.
