# P0 Legacy Photo Fallback Remediation

Data: 2026-06-07

## Falha tratada

`test_legacy_photo_fallback_is_centralized_outside_bases_route`

## Causa raiz

`backend/src/controle_treinamentos/blueprints/bases/routes.py` ainda expunha o helper legado `_decode_photo_data_uri`, mantendo a responsabilidade de fallback de foto dentro da rota de bases. A policy exige que esse fallback fique centralizado fora da rota.

## Novo local central

`backend/src/controle_treinamentos/application/tripulante_media.py`, via `load_tripulante_photo_payload()`.

Esse helper central preserva leitura por `foto_storage_ref` e fallback compativel via `foto_base64`, incluindo mime types `image/jpeg`, `image/png` e `image/webp`.

## Arquivos alterados

- `backend/src/controle_treinamentos/blueprints/bases/routes.py`
- `tests/integration/test_supertest_regression.py`
- `docs/release-gates/p0-legacy-photo-fallback-remediation.md`

## Correcao aplicada

- Removido o wrapper `_decode_photo_data_uri` de `bases/routes.py`.
- Mantida a resposta de foto da rota de bases delegando para `load_tripulante_photo_payload()`.
- Atualizado o teste de compatibilidade JPG/WebP para validar diretamente o helper central.

Nao houve alteracao de rotas, contrato de download/foto, storage real, schema ou auditoria.

## Evidencia

Antes:

```text
.\.venv\Scripts\python.exe -m pytest -q -k test_legacy_photo_fallback_is_centralized_outside_bases_route -vv --tb=long
FAILED tests/unit/test_legacy_blob_freeze_policy.py::test_legacy_photo_fallback_is_centralized_outside_bases_route
AssertionError: assert '_decode_photo_data_uri' not in bases_route
```

Teste alvo depois:

```text
.\.venv\Scripts\python.exe -m pytest -q tests\unit\test_legacy_blob_freeze_policy.py::test_legacy_photo_fallback_is_centralized_outside_bases_route -vv --tb=short
1 passed in 0.75s
```

Subset direto de documentos/fotos:

```text
.\.venv\Scripts\python.exe -m pytest -q tests\unit\test_legacy_blob_freeze_policy.py tests\unit\test_media_storage.py tests\unit\test_document_storage_policy.py tests\integration\test_supertest_regression.py::test_tripulante_photo_payload_accepts_jpg_and_webp_data_uri tests\integration\test_supertest_regression.py::test_tripulante_media_photo_payload_accepts_jpg_and_webp
32 passed in 2.51s
```

Checagem textual:

```text
rg -n "_decode_photo_data_uri|base64\.b64decode|load_tripulante_photo_payload" backend\src\controle_treinamentos\blueprints\bases\routes.py
22:from ...application.tripulante_media import load_tripulante_photo_payload
126:    payload = load_tripulante_photo_payload(dict(row or {}))
```

Observacao: uma tentativa de subset mais amplo incluindo contratos autenticados de tripulantes falhou em `/api/v1/session/login` por auditoria estrita tentando gravar usuario fake no DB real. Essa falha e externa ao fallback de foto em bases e nao altera a evidencia do bloqueador tratado.

## Resultado

Bloqueador removido: SIM
