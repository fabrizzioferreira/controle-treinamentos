# Documents Storage P0 Remediation

## Resumo executivo

Remediacao do bloco P0 de documentos, storage, anexos, fotos e auditoria de
download da Frente 1.5. A investigacao confirmou falhas de fixture/path
temporario no Windows com workspace gerenciado, lacuna de fixture de usuario
para auditoria strict e um wrapper de compatibilidade de foto ausente em bases.

Resultado final do subset ampliado: 111 passed.

## Contexto observado

- Branch: `safety-baseline-financeiro-20260602-193550`
- Working tree: suja antes desta remediacao, com alteracoes preexistentes fora
  do escopo.
- Baseline consultada: `docs/release-gates/baseline-p0-execution.md`
- Auditability gate consultado:
  `docs/release-gates/auditability-gate-register.md`
- Data reader/writer map consultado:
  `docs/release-gates/data-reader-writer-map.md`

## Testes falhos identificados

Falhas de documentos/storage citadas na baseline:

- `tests/unit/test_media_storage.py::test_write_tripulante_photo_uses_tripulante_folder`
- `tests/unit/test_media_storage.py::test_write_documents_and_training_attachments_are_grouped_by_tripulante`
- `tests/contract/test_api_tripulante_media_contract.py::test_api_tripulante_photo_upload_persists_blob_and_get_returns_binary`
- `tests/contract/test_api_tripulante_media_contract.py::test_api_tripulante_file_get_returns_binary`
- `tests/contract/test_api_treinamentos_contract.py::test_api_treinamento_attachment_get_returns_binary`
- `tests/integration/test_supertest_regression.py::test_bases_decode_photo_data_uri_accepts_jpg_and_webp`

Durante a reproducao local tambem surgiu erro de coleta por import circular
entre `api.http.cadastros.routes` e `routes_training_program`, corrigido como
pre-requisito para executar o subset.

## Causa raiz por falha

1. `PermissionError` em escrita atomica:
   - Classificacao: problema de path temporario/permissao de filesystem em teste.
   - Causa: `--basetemp runtime/pytest-*` dentro do workspace permite escrita
     direta, mas bloqueia `os.replace`/rename no ambiente gerenciado Windows.
   - Correcao: fixture `media_storage_tmp_path` usando `tempfile.TemporaryDirectory`
     no temp do sistema e `MEDIA_STORAGE_ROOT` apontado para esse diretorio.

2. Upload de foto retornando 500:
   - Classificacao: mesmo problema de path temporario.
   - Causa: upload exercitava `write_tripulante_photo`, que falhava ao renomear
     o arquivo temporario dentro de `runtime/pytest-*`.
   - Correcao: contrato de upload passou a usar `media_storage_tmp_path`.

3. Download audit strict com FK de usuario:
   - Classificacao: lacuna de fixture de usuario/auditoria.
   - Causa: autenticacao do teste mockava o repositorio de usuarios, mas
     `audit_relevant_download` resolvia outro DB para persistencia strict,
     tentando inserir `realizado_por=31` ou `41` sem usuario correspondente.
   - Correcao: fixture de auditoria strict local ao teste, com usuario valido,
     savepoint, insert, commit e assercoes do evento `download`.

4. `_decode_photo_data_uri` ausente em bases:
   - Classificacao: contrato de compatibilidade divergente.
   - Causa: rota de bases ainda tinha consumidor/teste para o wrapper legado,
     mas o modulo nao expunha mais a funcao.
   - Correcao: wrapper local restaurado delegando para
     `load_tripulante_photo_payload`, preservando o comportamento legado.

5. Import circular em cadastros API:
   - Classificacao: bug de organizacao/import em runtime de teste.
   - Causa: `routes.py` importava `cadastros_bp` antes de definir helpers
     privados usados por `routes_training_program`.
   - Correcao: import de `cadastros_bp` movido para depois de `_file_payload`
     e `_upload_contract`.

## Arquivos alterados

- `backend/src/controle_treinamentos/api/http/cadastros/routes.py`
- `backend/src/controle_treinamentos/blueprints/bases/routes.py`
- `tests/conftest.py`
- `tests/unit/test_media_storage.py`
- `tests/unit/test_document_storage_policy.py`
- `tests/unit/test_document_storage_monitoring.py`
- `tests/contract/test_api_tripulante_media_contract.py`
- `tests/contract/test_api_treinamentos_contract.py`
- `docs/release-gates/documents-storage-p0-remediation.md`

Observacao: a working tree ja possuia alteracoes preexistentes em alguns
arquivos. Esta remediacao nao reverteu nem assumiu ownership dessas mudancas.

## Contratos preservados

Preservados:

- Content-Type de foto, PDF e anexos.
- `Content-Disposition` inline para preview.
- `Content-Disposition` attachment para download.
- Headers de file access: `X-File-Access-Action`,
  `X-File-Link-Policy`, `X-File-Link-Expires`,
  `X-Content-Type-Options`, `X-Frame-Options` quando aplicavel.
- Erro JSON para documento/anexo indisponivel.
- Status de anexo/documento.
- Hash e storage ref em contratos de documento.
- Politica de preview versus download.

## Auditoria preservada ou corrigida

Auditoria strict foi preservada. Nenhum fallback silencioso foi adicionado.

Correcoes de fixture:

- Downloads `preview` continuam sem persistir evento relevante.
- Downloads `download` continuam chamando `audit_relevant_download`.
- Fake DB estrito valida usuario existente no teste.
- Eventos `download` sao inseridos e commitados no fixture.
- FK nao foi ignorada, relaxada ou removida.

## Storage e path temporario usado

O storage de teste passou a usar fixture segura:

```text
tempfile.TemporaryDirectory(prefix="controle-media-storage-")
```

O valor e aplicado via:

```text
MEDIA_STORAGE_ROOT=<temp do sistema>/controle-media-storage-*
```

Esse path fica fora do workspace e evita o bloqueio de rename observado em
`runtime/pytest-*`. Nenhum path real de producao foi usado.

## Testes reexecutados

Reproducao focada apos desbloquear coleta:

```text
5 failed
```

Validacao focada apos correcao:

```text
5 passed in 9.92s
```

Regressao de bases isolada:

```text
1 passed in 1.61s
```

Subset ampliado final de documentos/storage/fotos/anexos/download:

```text
111 passed in 83.80s (0:01:23)
```

## Comandos operacionais nao executados

Os comandos abaixo foram deliberadamente NAO EXECUTADOS:

- Migration - NAO EXECUTADO
- Seed - NAO EXECUTADO
- Alteracao de schema - NAO EXECUTADO
- Backup real - NAO EXECUTADO
- Restore real - NAO EXECUTADO
- Endpoint destrutivo real - NAO EXECUTADO
- Delete fisico de arquivo real - NAO EXECUTADO
- Limpeza manual de storage real - NAO EXECUTADO
- Alteracao global de PDF/CSV - NAO EXECUTADO

## Resultado pos-correcao

O subset P0 de documentos/storage executado nesta remediacao ficou verde:

```text
111 passed in 83.80s (0:01:23)
```

## Riscos remanescentes

- Working tree permanece suja por alteracoes preexistentes fora deste escopo.
- Uma execucao anterior gerou artefatos de teste em `runtime/pytest-*`; nenhuma
  limpeza manual foi executada por seguranca.
- A validacao cobre o subset de documentos/storage/anexos/fotos/download, nao a
  baseline P0 consolidada inteira.
- A aprovacao final de release gate continua exigindo validacao humana.

## Proximo passo recomendado

Reexecutar a baseline P0 consolidada em ambiente controlado e registrar a
macroarea de documentos/storage como corrigida condicionalmente, mantendo
auditoria strict habilitada.
