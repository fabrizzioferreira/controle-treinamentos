# Reorganization Rollback Plan

Data: 2026-06-06
Status: PLANO DOCUMENTAL CRIADO - ROLLBACK REAL NAO EXECUTADO
Escopo: rollback especifico da reorganizacao fisica do repositorio, cobrindo codigo, branch, commits, tags, imports, rotas, aliases, contratos, frontend build/dist, backend app, configuracoes, banco/schema, migrations, seeds, repositories, dados criticos, jobs, backups, restore, scripts, runtime, archive, legacy, ops artifacts, PDFs/CSVs, documentacao de release gate e evidencias de teste.

Este documento e um gate de seguranca de release. Ele nao autoriza reorganizacao fisica, rollback real, backup real, restore, migration, seed, alteracao de banco, move, rename, alteracao de import, contrato, rota ou alias.

Rollback real exige validacao humana explicita de Release Management, SRE/Ops, Backend, QA, Produto, Seguranca e, quando houver impacto financeiro ou de dados, responsavel financeiro/DBA.

## 1. Resumo executivo

A Frente 1.5 terminou com decisao `BLOQUEADO`. Um dos bloqueadores criticos era a ausencia de plano de rollback especifico da reorganizacao fisica. Este arquivo cria o plano documental exigido em `docs/release-gates/reorganization-rollback-plan.md`.

Decisao deste plano:

- A reorganizacao fisica permanece `BLOQUEADA`.
- Nenhum rollback foi executado.
- Nenhum backup foi executado.
- Nenhum restore foi executado.
- Nenhuma migration foi executada.
- Nenhum seed foi executado.
- Nenhum banco foi alterado.
- Nenhum codigo de produto foi alterado por este plano.
- Nenhum arquivo foi movido ou renomeado.
- Nenhum import, contrato, rota ou alias foi alterado.

O rollback proposto e preferencialmente baseado em reversao controlada de commits/PRs ou retorno ao artefato de release anterior, nunca em improviso manual durante incidente. Para banco, restore e ultima linha de defesa e so pode ocorrer com backup validado, ambiente de manutencao, owner humano e evidencia de post-check.

## 2. Dependencias e fontes

Este plano depende diretamente dos registros existentes da Frente 1.5:

- `docs/release-gates/reorganization-release-gate-decision.md`
- `docs/release-gates/contract-freeze-register.md`
- `docs/release-gates/data-reader-writer-map.md`
- `docs/release-gates/external-artifacts-inventory.md`
- `docs/release-gates/routes-aliases-freeze-map.md`
- `docs/release-gates/auditability-gate-register.md`
- `docs/release-gates/baseline-p0-execution.md`
- Relatorio da Frente 1.5 em `docs/reports/relatorio-rico-frente-1-5-10-prompts-reorganizacao-fisica-2026-06-06.pdf`
- Runbooks operacionais existentes, especialmente `docs/operations/ROLLBACK_CHECKLIST.md`, `docs/operations/RELEASE_MANAGEMENT.md`, `docs/operations/RUNBOOK.md`, `docs/operations/frontend_publish_safety.md`, `docs/operations/DATABASE_EVOLUTION.md` e `docs/operations/canonical-commands.md`

As fontes acima congelam contratos, rotas, dados, artifacts externos e auditabilidade. Este plano nao substitui esses registros; ele os usa como pre-condicao de seguranca.

## 3. Estado Git observado

Observacao feita durante a criacao deste documento:

- Branch atual: `safety-baseline-financeiro-20260602-193550`
- Estado do working tree: sujo.
- `docs/release-gates/` aparece como diretorio nao rastreado no status observado.
- Existem alteracoes modificadas e nao rastreadas preexistentes em backend, frontend, tests, docs/reports, PDFs raiz, `frontend/frontend/` e outros paths.

Implicacoes:

- O estado atual nao e base limpa para iniciar reorganizacao fisica.
- O estado atual nao deve ser usado como tag de rollback sem revisao humana.
- Qualquer plano real de reorganizacao deve partir de commit limpo, com branch dedicada, base registrada, pacote de evidencias e owner humano.
- Este documento nao valida nem aprova as alteracoes preexistentes no working tree.

## 4. Estrategia de branch, commit e tag

### 4.1 Branch de reorganizacao

Estrategia recomendada, nao executada:

- Criar uma branch dedicada somente depois de worktree limpo e gate reaberto.
- Nome sugerido: `codex/reorganizacao-fisica-YYYYMMDD`.
- A branch deve nascer do commit base aprovado, nao de working tree sujo.
- A branch deve conter apenas mudancas da reorganizacao fisica aprovada.
- Mudancas de produto, schema, contrato, rota, alias, seed, migration, cleanup ou refatoracao funcional devem ficar fora dessa branch.

Regra: se for preciso alterar comportamento para a reorganizacao compilar ou passar testes, a reorganizacao deixa de ser fisica e deve voltar para triagem arquitetural.

### 4.2 Commit base

Antes da reorganizacao, registrar:

- Commit SHA completo da base limpa.
- Branch de origem.
- Timestamp com timezone.
- `git status` limpo.
- Hashes ou manifests dos artifacts relevantes.
- Versao de frontend dist publicada ou validada.
- Release ID anterior conhecida.

O commit base e o primeiro ponto de retorno. Sem commit base limpo, rollback fica `BLOQUEADO`.

### 4.3 Tags

Estrategia recomendada, nao executada:

- Criar tag anotada para base antes da reorganizacao, por exemplo `reorg-base-YYYYMMDD-HHMM`.
- Criar tag de candidato de reorganizacao apenas depois de testes e validacao humana.
- Nunca mover uma tag ja publicada para "corrigir" historico.
- Nunca apagar tag de release sem aprovacao humana explicita.
- Se uma tag apontar para candidato ruim, criar tag corretiva ou rollback release, preservando a trilha.

### 4.4 Commits de rollback

Ordem preferencial:

1. Reverter PR/merge da reorganizacao com commit de rollback auditavel.
2. Reverter sequencia linear de commits da reorganizacao, do mais novo para o mais antigo.
3. Reapontar deploy para artifact anterior somente quando o pacote anterior for conhecido e validado.
4. Usar restore de banco apenas se houve alteracao real de dados/schema e depois de aprovacao humana.

`git reset --hard` nao e estrategia padrao de rollback de release. Pode descartar alteracoes locais e apagar contexto de auditoria. Se algum operador considerar reset, isso vira `STOP-THE-LINE`.

## 5. Rollback de codigo fonte

Escopo coberto:

- Codigo fonte backend e frontend.
- Imports.
- Rotas.
- Aliases.
- Contracts.
- Repositories.
- Scripts versionados.
- Documentacao de release gate alterada pela reorganizacao.

Estrategia:

- Rollback de codigo deve ser feito por revert de commits da reorganizacao ou retorno ao artifact de release anterior.
- Nao corrigir imports manualmente durante incidente, exceto em hotfix aprovado e documentado.
- Nao criar novos paths, adapters ou aliases durante rollback sem contract review.
- Nao apagar arquivos novos de forma manual sem saber se foram incluidos em commits de reorganizacao, build ou evidencia.
- Confirmar que todos os imports voltaram aos paths anteriores por testes estaticos e contract tests antes de declarar rollback concluido.

Critico:

- Se a reorganizacao tiver alterado imports, o rollback deve restaurar o grafo de imports anterior por revert atomico.
- Se a reorganizacao tiver alterado rotas, aliases ou contracts, o rollback deve restaurar exatamente o estado congelado pelos registros da Frente 1.5.
- Se houver conflito entre rollback de codigo e dados gerados durante a janela, escalar para incidente; nao improvisar transformacao de dados.

## 6. Rollback de branch

Rollback de branch e controle de fluxo, nao operacao de filesystem.

Plano:

- Congelar merges na branch de reorganizacao ao primeiro criterio de abortar.
- Criar branch de rollback a partir da branch alvo, se rollback precisar virar PR.
- Reverter commits da reorganizacao em branch separada.
- Validar o rollback em ambiente isolado.
- Manter a branch original preservada para investigacao.
- Nao apagar branch ate fechar evidencias, RCA e aprovacao humana.

Rollback antes de merge:

- Fechar PR de reorganizacao.
- Preservar branch para auditoria.
- Marcar release gate como `BLOQUEADO`.

Rollback depois de merge:

- Criar PR de rollback.
- Reverter merge commit ou range linear.
- Exigir nova rodada de smoke/contract/build antes de promover.

## 7. Rollback de commits

Matriz de decisao:

| Forma da reorganizacao | Estrategia preferida | Observacao |
| --- | --- | --- |
| Um merge commit | Revert do merge commit com mainline correta | Exige revisao humana do mainline |
| Sequencia linear de commits | Revert em ordem inversa | Preserva historico e auditoria |
| Squash merge | Revert do commit squash | Mais simples, mas exige confirmar escopo completo |
| Commits misturados com produto | STOP-THE-LINE | Separar reorg de produto antes de rollback |
| Commits com migration/seed/schema | STOP-THE-LINE + DBA | Rollback de codigo pode nao reverter dados |

Regra: rollback de commit nao deve incluir alteracoes funcionais novas. Se algo alem da reversao for necessario, abrir hotfix separado e validar como release independente.

## 8. Rollback de tags

Plano:

- Identificar tag de base e tag de candidato.
- Se o candidato foi publicado com tag errada, nao mover a tag silenciosamente.
- Criar tag de rollback ou release corretiva.
- Registrar no release gate qual tag foi promovida, qual foi bloqueada e qual ficou como referencia historica.

Tags sao evidencia de release. Excluir ou reescrever tag sem autorizacao e criterio `STOP-THE-LINE`.

## 9. Rollback de imports

Imports sao contrato interno durante reorganizacao fisica.

Plano:

- Reverter imports por commit rollback, nao por busca/substituicao manual durante incidente.
- Confirmar que imports relativos/absolutos voltaram ao estado anterior.
- Confirmar que entrypoints de Flask, scripts canonicos, workers, jobs e testes encontram os modulos.
- Confirmar que nenhum adapter temporario foi deixado como solucao permanente.

Sinais de abortar:

- Import cycle novo.
- ImportError no boot do backend.
- Lazy import quebrando rota SPA.
- Module path novo sem owner.
- Alias criado para mascarar move incompleto.

## 10. Rollback de rotas

Rotas congeladas estao em `docs/release-gates/routes-aliases-freeze-map.md`.

Plano:

- Restaurar hash routes SPA canonicas e internas.
- Restaurar rotas Flask SSR/backend.
- Restaurar redirects e deep links.
- Restaurar paths PDF/CSV/export.
- Restaurar rotas operacionais `/healthz`, `/api/internal/metrics`, `/monitoramento`, `/backups`, `/jobs/<id>/status`, `/jobs/<id>/reativar` e cron fallbacks quando impactados.

Nenhuma rota pode ser removida durante rollback para "simplificar" o retorno. Rota sem menu tambem e contrato.

## 11. Rollback de aliases

Aliases congelados incluem, entre outros:

- `#/financeiro/bonificacoes`
- `#/financeiro/bonificacoes/horaria`
- `#/financeiro/bonificacoes/produtividade`
- `/tipos`
- `/tipos-treinamento`
- `/dashboard`
- `/tripulantes`
- `/treinamentos`
- `/treinamentos/consolidado`

Plano:

- Restaurar aliases por rollback de codigo.
- Preservar adapters de compatibilidade.
- Nao remover alias com base em ausencia de menu.
- Nao criar alias novo como workaround sem contract review.
- Validar uso externo por logs/telemetria antes de qualquer mudanca futura.

## 12. Rollback de contracts

Contracts congelados estao em `docs/release-gates/contract-freeze-register.md`.

Cobertura obrigatoria:

- HTTP JSON.
- Envelopes de erro.
- Auth/session/CSRF/capabilities/RBAC.
- Frontend services/state.
- PDF/CSV/export.
- Schema/repository boundaries.
- Jobs/scripts/env.
- Auditoria/logs/metricas.
- Financeiro.
- Tripulantes, treinamentos, documentos e cadastro raiz.

Plano:

- Reverter qualquer alteracao de status code, header, campo JSON, permissao, envelope, nome de arquivo, query param ou path.
- Manter serializacao financeira decimal como contrato.
- Manter datas, competencias e status de dominio sem normalizacao.
- Reexecutar contract tests em ambiente autorizado antes de declarar rollback efetivo.

## 13. Rollback de frontend build

Frontend build e artifact, nao fonte primaria.

Plano:

- Usar artifact frontend anterior conhecido e validado.
- Preservar `asset-manifest.json` do build anterior.
- Comparar fingerprints esperados antes de publicar.
- Nao reconstruir em emergencia sem aprovacao de Release Manager, salvo quando artifact anterior estiver indisponivel e houver ambiente reprodutivel.
- Registrar build ID, checksum, origem e operador.

Se a reorganizacao alterou `frontend/src`, rollback de build sozinho nao basta. O codigo fonte e o artifact publicado precisam apontar para o mesmo candidato aprovado.

## 14. Rollback de frontend dist

`frontend/dist/` e classificado pelo inventario como build gerado/publicavel e bloqueado para limpeza em lote.

Plano:

- Nao apagar `frontend/dist/` manualmente.
- Publicar dist anterior por troca atomica no mecanismo operacional aprovado.
- Confirmar `asset-manifest.json`, entrypoints e assets fingerprintados.
- Preservar dist ruim para investigacao, se storage permitir.
- Evitar limpeza de cache sem plano de headers e impacto no browser.

Criticos:

- Se servidor externo serve diretamente `frontend/dist/`, rollback deve coordenar host/static server.
- Se CDN/cache existir, invalidacao deve ser humana e registrada.
- Se assets antigos foram removidos, risco de tela branca vira `STOP-THE-LINE`.

## 15. Rollback de backend app

Plano:

- Reapontar backend para release/artifact anterior aprovado.
- Restaurar env/config compativel com esse release.
- Reiniciar runtime pelo caminho operacional documentado.
- Validar boot, `/healthz`, login/session, routes principais e logs.
- Confirmar que workers/jobs usam a mesma versao do backend app.

Nao fazer:

- Nao rodar migration como parte automatica do rollback.
- Nao alterar schema para fazer app antigo subir sem DBA.
- Nao editar imports ou rotas em producao para contornar boot quebrado.

## 16. Rollback de configuracoes

Configuracoes cobertas:

- `.env` e exemplos de env.
- Config de servico Windows.
- Caddy/proxy.
- Variaveis de frontend origin/CORS.
- Cookies/session/security.
- AISWEB, email, backup, jobs, metrics e Sentry.

Plano:

- Restaurar configuracao do pacote anterior.
- Validar que secrets nao foram impressos ou versionados.
- Nao rotacionar secrets como parte do rollback, exceto se o incidente for vazamento.
- Nao mudar `DATABASE_URL` sem owner DBA/SRE.
- Registrar diffs de config em evidencia segura.

## 17. Rollback de banco/schema

Regra central: reorganizacao fisica nao deve alterar banco nem schema.

Plano:

- Antes da reorganizacao, confirmar que nao ha migration, seed, schema bootstrap ou repair no escopo.
- Se schema mudou por engano, acionar `STOP-THE-LINE`.
- Separar rollback de codigo de recuperacao de dados.
- Avaliar forward fix, migration corretiva ou restore somente com DBA.
- Restore de banco exige backup validado, janela de manutencao, aceite humano e post-check.

Tabelas criticas mapeadas em `data-reader-writer-map.md` permanecem bloqueadas, incluindo:

- `usuarios`, `auditoria_eventos`, `request_error_events`.
- `tripulantes`, `pilotos`, `historico_status_piloto`, `bases`.
- `treinamentos`, `tipos_treinamento`, `segmentos_teoricos`, `horas_voo_aeronave`.
- `treinamento_anexos_pdf`, `tripulante_arquivos_pdf`, `notificacoes_treinamento`.
- `financeiro_*`, `pernoites_operacionais`, `equipamentos`.
- `backups_execucoes`, `background_jobs`, `background_job_executions`, `sistema_controle`.

Nenhuma dessas tabelas pode ser assumida segura por rollback de codigo isolado.

## 18. Rollback de migrations

Plano:

- Migrations nao fazem parte da reorganizacao fisica.
- Se migration foi incluida no PR de reorganizacao, bloquear merge.
- Se migration foi executada acidentalmente, congelar writes, coletar evidencia e escalar DBA.
- Nao executar downgrade automatico sem teste especifico.
- Nao editar tabela de controle de migration manualmente.

Rollback de migration e evento de banco, nao simples revert de arquivo.

## 19. Rollback de seeds

Plano:

- Seeds nao fazem parte da reorganizacao fisica.
- Se seed foi incluido no PR, remover antes de qualquer aprovacao.
- Se seed foi executado acidentalmente, tratar como alteracao de dados.
- Comparar dados afetados com snapshot/backup.
- Reverter via plano de dados aprovado, nao por delete manual.

Seeds podem criar usuarios, permissoes, parametros e dados base. Isso exige auditoria e validacao humana.

## 20. Rollback de repositories

Repositories sao fronteira de acesso a dados e estao congelados pelo mapa de dados.

Plano:

- Reverter moves/refactors de repositories por commit rollback.
- Confirmar que SQL aliases, nomes de colunas e serializers voltaram ao contrato anterior.
- Confirmar que application services consomem a mesma forma dos rows.
- Confirmar que repository tests e contract tests passam antes de declarar rollback.

Sinais de abortar:

- Query alterada durante reorganizacao.
- Join ou filtro financeiro alterado.
- Soft delete virando delete fisico.
- Serializer sem campo esperado.
- Mudanca de precisao decimal.

## 21. Rollback de dados criticos

Dados criticos nao devem mudar em reorganizacao fisica.

Plano se houver suspeita de alteracao:

1. Parar a promocao da reorganizacao.
2. Preservar logs, request IDs, correlation IDs, manifests e artifacts.
3. Identificar tabelas e registros afetados.
4. Bloquear writes apenas por mecanismo operacional aprovado.
5. Comparar com backup/snapshot validado.
6. Decidir entre forward fix, script corretivo auditado ou restore.
7. Executar somente apos validacao humana.

Dados financeiros, RBAC, documentos, anexos, jobs, auditoria e backups nao podem ser "ajustados" por script rapido sem auditoria.

## 22. Rollback de jobs

Jobs cobertos:

- `send_daily_notifications`
- `run_backup`
- Workers de `background_jobs`
- Dead-letter/requeue
- Jobs de notificacao e backup acionados por UI, worker ou cron fallback

Plano:

- Rollback do backend app deve incluir workers e scripts que compartilham codigo.
- Durante incidente real, avaliar pausa de workers somente com Ops.
- Nao reprocessar dead-letter como parte automatica do rollback.
- Nao limpar historico de job para "destravar" release.
- Confirmar idempotency keys e attempts antes de qualquer requeue.

Se job executou com codigo reorganizado e produziu efeito, tratar como impacto de dados/artifacts.

## 23. Rollback de backups

Backups sao pre-condicao, nao acao automatica deste plano.

Plano:

- Antes da reorganizacao, identificar ultimo backup valido, manifest, checksums e escopo.
- Confirmar se backup cobre DB, assets/documentos e configuracoes.
- Confirmar que backup pertence a janela correta.
- Confirmar restore drill ou evidencia equivalente.
- Nao disparar backup real neste documento.

Se backup valido nao existir, reorganizacao fisica fica `BLOQUEADA`.

## 24. Rollback de restore

Restore e ultima linha de defesa.

Plano:

- Restore real exige incidente declarado ou janela controlada.
- Restore real exige DBA/SRE, Release Manager e owner de negocio.
- Restore real exige backup validado, plano de downtime, comunicacao e post-check.
- Restore real deve preservar evidencia antes/depois.
- Restore real nao pode ser disparado apenas por falha de build ou import.

Se rollback de codigo resolver o incidente sem perda de dados, restore nao deve ser executado.

## 25. Rollback de scripts

Scripts congelados pelo Contract Freeze Register e External Artifacts Inventory:

- `backend/tools/runtime/run.py`
- `frontend/scripts/build_frontend.py`
- `backend/tools/maintenance/run_backups.py`
- `backend/tools/maintenance/run_jobs_worker.py`
- `backend/tools/maintenance/run_notifications.py`
- `backend/tools/maintenance/bootstrap_db_schema.py`
- `backend/tools/maintenance/bootstrap_seed_data.py`
- `backend/tools/manual_unsafe/**`
- `ops/scripts/**`
- `scripts/**` wrappers de compatibilidade

Plano:

- Scripts movidos pela reorganizacao devem voltar por rollback de commits.
- Wrappers de compatibilidade nao devem ser removidos sem prova de consumidor externo ausente.
- `manual_unsafe` nao deve ser executado para rollback de reorganizacao.
- Scripts de cleanup, repair, migration e seed ficam bloqueados.

## 26. Rollback de runtime

`runtime/` contem evidencias, builds, perfis de browser, worktrees, patches e outputs P0. O inventario classifica a area como bloqueada para limpeza em lote.

Plano:

- Nao mover nem apagar `runtime/`.
- Preservar evidencias P0 e worktrees.
- Se uma reorganizacao criou novos runtime artifacts, catalogar antes de qualquer limpeza.
- Se worktree Git estiver envolvido, usar fluxo Git apropriado, nunca delete/move manual.

Rollback de runtime significa preservar evidencia e reverter referencias operacionais, nao limpar scratch para "ficar verde".

## 27. Rollback de archive

`archive/` nao e fonte viva, mas tem manifest, historico e valor de auditoria.

Plano:

- Nao limpar `archive/` como rollback.
- Nao mover snapshots ou temp-backups sem atualizar manifest e validar links.
- Se reorganizacao moveu `archive/`, reverter por commit rollback.
- Preservar `archive/MANIFEST.md` e referencias historicas.

## 28. Rollback de legacy

`legacy/` e legado vivo documentado.

Plano:

- Nao tratar `legacy/` como descartavel.
- Nao remover `legacy/LIVE_LEGACY.md`.
- Se reorganizacao moveu ou reclassificou legacy, reverter por commit rollback.
- Validar SSR, File legado, data-compat e consumidores externos antes de qualquer evolucao futura.

## 29. Rollback de ops artifacts

`ops/artifacts/` contem evidencias historicas, financeiras, HML/prod, security, clusters de teste, caches e perfis.

Plano:

- Nao limpar `ops/artifacts/` como parte de rollback.
- Preservar artifacts financeiros e security.
- Se artifacts foram publicados com candidato ruim, criar evidencia de supersedencia, nao apagar.
- Se algum artifact precisa sair do pacote publicado, manter copia investigativa e checksum.

## 30. Rollback de PDFs e CSVs

PDFs/CSVs sao contratos de arquivo e evidencia operacional.

Plano:

- Restaurar paths, content types, headers, filtros, nomes de arquivo e politicas.
- Preservar PDFs de auditoria, relatorios e laudos.
- Nao mover PDFs raiz ou `docs/reports` durante rollback.
- Validar `%PDF`, `%%EOF`, CSV UTF-8/BOM/delimiter e headers esperados antes de declarar rollback.
- Para PDFs financeiros, exigir validacao humana financeira.

## 31. Rollback da documentacao release-gates

Documentacao de gate e evidencia. Nao deve ser apagada para esconder falha.

Plano:

- Preservar documentos da Frente 1.5.
- Se reorganizacao alterou docs de gate indevidamente, reverter por commit rollback.
- Se uma decisao foi supersedida por rollback, criar novo registro de decisao, nao apagar o antigo.
- Manter `reorganization-rollback-plan.md` como pre-condicao do gate.
- Registrar evidencias de rollback em arquivo novo, por exemplo `docs/release-gates/reorganization-rollback-evidence-YYYYMMDD.md`, se rollback real ocorrer.

## 32. Rollback de evidencias de teste

Plano:

- Preservar baseline vermelha inicial.
- Preservar outputs de teste gerados sob `runtime/pytest-baseline-p0-*`.
- Nao sobrescrever evidencias antigas com novas rodadas.
- Cada nova execucao deve ter timestamp, ambiente, commit, branch, status Git e resultado.
- Teste que falha durante rollback nao deve ser removido do escopo; deve bloquear promocao.

## 33. Criterios de abortar

Abortar reorganizacao ou rollback se qualquer criterio ocorrer:

- Working tree sujo sem aceite humano.
- Commit base limpo nao identificado.
- Tag/base de rollback ausente.
- Baseline P0 vermelha ou bloqueada.
- Falha em auth/session/RBAC/capabilities/CSRF/401/403.
- Falha em contratos HTTP, erro, headers ou envelope JSON.
- Drift em rotas, aliases, redirects, deep links, PDF ou CSV.
- Drift em imports ou boot do backend.
- Build frontend falha ou dist nao corresponde ao manifest.
- Backend app nao sobe com artifact anterior.
- Alteracao de schema detectada.
- Migration, seed, repair ou cleanup incluido no escopo.
- Dados criticos alterados ou suspeitos.
- Job executado com codigo incorreto.
- Backup valido indisponivel.
- Restore necessario sem DBA/SRE/owner humano.
- Artifact externo sem classificacao.
- `archive`, `legacy`, `runtime`, `frontend/dist`, `ops/artifacts` ou PDFs foram apagados/movidos.
- Auditoria minima ausente para operacao sensivel.
- Falta de owner humano para decisao.

## 34. Stop-the-line

`STOP-THE-LINE` deve ser declarado imediatamente quando:

- Alguem propuser executar rollback real sem validacao humana.
- Alguem propuser rodar backup, restore, migration, seed, repair ou cleanup fora de ambiente autorizado.
- Alguem propuser mover/renomear arquivos de produto enquanto gate esta bloqueado.
- Alguem propuser alterar imports, contracts, rotas ou aliases para "facilitar" rollback.
- Banco/schema foi alterado ou ha suspeita de alteracao.
- Dados financeiros, usuarios/RBAC, documentos, auditoria, jobs ou backups foram afetados.
- Nao existe artifact anterior validado para app/frontend.
- O rollback parcial pode deixar app e DB em versoes incompativeis.
- A evidencia de teste contradiz a aprovacao humana.

A acao apos `STOP-THE-LINE` e pausar promocao, preservar evidencia, comunicar owners e abrir decisao formal. Nao e executar comando corretivo imediato.

## 35. Checklist pre-reorganizacao

Todos os itens devem estar completos antes de qualquer reorganizacao fisica:

- [ ] Branch base limpa identificada.
- [ ] `git status` limpo registrado.
- [ ] Commit SHA completo registrado.
- [ ] Tag base criada ou estrategia equivalente aprovada.
- [ ] Branch dedicada definida.
- [ ] Escopo da reorganizacao limitado a moves/renames permitidos.
- [ ] Nenhum codigo de produto funcional no escopo.
- [ ] Nenhuma migration no escopo.
- [ ] Nenhum seed no escopo.
- [ ] Nenhuma alteracao de banco/schema no escopo.
- [ ] Nenhuma alteracao de import sem plano/teste.
- [ ] Nenhuma alteracao de contrato, rota ou alias.
- [ ] Contract Freeze Register revisado.
- [ ] Routes/Aliases Freeze Map revisado.
- [ ] Data Reader/Writer Map revisado.
- [ ] External Artifacts Inventory revisado.
- [ ] Auditability Gate Register revisado.
- [ ] Baseline P0 verde em ambiente autorizado.
- [ ] Frontend build/dist anterior identificado.
- [ ] Backend artifact anterior identificado.
- [ ] Config anterior identificada.
- [ ] Backup valido identificado.
- [ ] Restore drill/evidencia de restore validada.
- [ ] Jobs/workers/schedulers mapeados.
- [ ] Archive/legacy/runtime/artifacts classificados e preservados.
- [ ] PDFs/CSVs e relatorios classificados.
- [ ] Plano de rollback aprovado por humanos.
- [ ] Janela e criterio de abortar comunicados.

## 36. Checklist pos-reorganizacao

Todos os itens devem estar completos antes de promover qualquer reorganizacao:

- [ ] Diff contem apenas escopo aprovado.
- [ ] Imports resolvem sem adapters temporarios indevidos.
- [ ] Rotas SPA/SSR/backend preservadas.
- [ ] Aliases e redirects preservados.
- [ ] Contracts HTTP/PDF/CSV preservados.
- [ ] Frontend build executado em ambiente autorizado e manifest validado.
- [ ] Frontend dist publicado/validado de forma atomica.
- [ ] Backend app sobe com config aprovada.
- [ ] Workers/jobs usam versao compativel.
- [ ] Nenhuma migration executada.
- [ ] Nenhum seed executado.
- [ ] Nenhuma alteracao de schema detectada.
- [ ] Repositories e serializers preservam campos e semantica.
- [ ] Dados criticos sem alteracao inesperada.
- [ ] Archive/legacy/runtime/ops artifacts preservados.
- [ ] PDFs/CSVs preservados.
- [ ] Evidencias de teste anexadas.
- [ ] Release gate atualizado.
- [ ] Owners humanos assinaram a decisao.
- [ ] Plano de rollback permanece acionavel ate fim da janela de monitoramento.

## 37. Comandos sugeridos - todos NAO EXECUTADOS

Os comandos abaixo sao exemplos para runbook futuro. Nenhum foi executado por este plano.

| Objetivo | Comando sugerido | Status |
| --- | --- | --- |
| Confirmar branch antes de reorganizacao | `git branch --show-current` | NAO EXECUTADO neste runbook |
| Confirmar status completo | `git status --short --untracked-files=all` | NAO EXECUTADO neste runbook |
| Registrar commit base | `git rev-parse HEAD` | NAO EXECUTADO |
| Criar branch dedicada | `git switch -c codex/reorganizacao-fisica-YYYYMMDD` | NAO EXECUTADO |
| Criar tag base anotada | `git tag -a reorg-base-YYYYMMDD-HHMM -m "Base antes da reorganizacao fisica"` | NAO EXECUTADO |
| Reverter merge de reorganizacao | `git revert -m 1 <merge_commit_sha>` | NAO EXECUTADO |
| Reverter commit squash | `git revert <squash_commit_sha>` | NAO EXECUTADO |
| Reverter range linear | `git revert <oldest_reorg_commit>^..<newest_reorg_commit>` | NAO EXECUTADO |
| Validar contratos | `python -m pytest tests/contract` | NAO EXECUTADO |
| Validar arquitetura | `python -m pytest tests/architecture` | NAO EXECUTADO |
| Build frontend | `python frontend/scripts/build_frontend.py` | NAO EXECUTADO |
| Smoke pos rollback | `python ops/scripts/smoke/post_deploy_smoke.py` | NAO EXECUTADO |
| Validar DB consistency read-only | `python backend/tools/maintenance/run_db_consistency.py` | NAO EXECUTADO |
| Restore postcheck | `python backend/tools/maintenance/run_restore_postcheck.py` | NAO EXECUTADO |
| Worker de jobs | `python backend/tools/maintenance/run_jobs_worker.py` | NAO EXECUTADO |
| Backup operacional | `python backend/tools/maintenance/run_backups.py` | NAO EXECUTADO |
| Bootstrap schema | `python backend/tools/maintenance/bootstrap_db_schema.py` | NAO EXECUTADO |
| Bootstrap seed | `python backend/tools/maintenance/bootstrap_seed_data.py` | NAO EXECUTADO |
| Repair manual unsafe | `python backend/tools/manual_unsafe/run_db_repair.py` | NAO EXECUTADO |
| Cleanup manual unsafe | `python backend/tools/manual_unsafe/cleanup_operational_data.py` | NAO EXECUTADO |

Observacao: comandos de backup, restore, migration, seed, repair, cleanup, job ou publicacao so podem ser executados em procedimento real com aprovacao humana, ambiente correto e evidencia propria.

## 38. Lacunas restantes

Mesmo com este plano criado, a reorganizacao fisica continua bloqueada por lacunas ja registradas:

- Baseline P0 esta `VERMELHA`.
- Worktree atual esta sujo.
- Nao ha commit base limpo aprovado para reorganizacao.
- Nao ha evidencia de rollback A/B/A especifica da reorganizacao.
- Auditabilidade ainda e parcial/insuficiente/bloqueada para operacoes criticas.
- Testes de e2e, banco real, restore, cleanup, migration e seed permanecem bloqueados sem ambiente isolado autorizado.
- Validacao humana final ainda nao foi registrada.
- Artefatos externos, runtime, archive, legacy, dist, PDFs e ops artifacts ainda exigem auditoria externa antes de qualquer limpeza/move.
- Contratos, rotas, aliases, schema, repositories, jobs, scripts e dados criticos permanecem congelados.

## 39. Proximo passo recomendado

O proximo passo seguro e reabrir a rodada de remediacao da Frente 1.5 apenas depois deste plano ser revisado por humanos.

Sequencia recomendada:

1. Revisar este plano com Release Manager, SRE/Ops, Backend, QA, Produto, Seguranca e Financeiro/DBA quando aplicavel.
2. Limpar ou isolar o working tree antes de qualquer nova baseline.
3. Corrigir falhas P0 sem misturar com reorganizacao fisica.
4. Reexecutar baseline P0 em ambiente isolado e autorizado.
5. Preparar evidencia de rollback dry-run ou A/B/A sem tocar banco real.
6. Somente depois de gate verde e aceite humano, criar branch dedicada de reorganizacao.

Ate la, nenhuma reorganizacao fisica deve iniciar.
