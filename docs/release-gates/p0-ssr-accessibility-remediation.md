# P0 SSR Accessibility Remediation

Data: 2026-06-07

## Falha tratada

`test_shell_has_persistent_live_regions_focus_after_render_and_no_label_generation`

## Diferenca encontrada

O `base.html` ja mantinha as live regions persistentes e o suporte de foco por `id="mainContent"` e `tabindex="-1"`, mas a abertura do `main` estava como:

```html
<main class="content ui-content-region" id="mainContent" tabindex="-1">
```

O contrato do teste alvo exigia a assinatura literal:

```html
<main class="content" id="mainContent" tabindex="-1">
```

## Correcao aplicada

Restaurada a abertura do `main` em `backend/src/controle_treinamentos/templates/base.html` para o contrato esperado, sem alterar rotas, aliases, navegacao ou backend links.

## Evidencia de validacao

Teste alvo:

```text
.\.venv\Scripts\python.exe -m pytest -q tests\unit\test_accessibility_residual_28_fix.py::test_shell_has_persistent_live_regions_focus_after_render_and_no_label_generation
1 passed in 0.12s
```

Subset SSR/accessibility:

```text
.\.venv\Scripts\python.exe -m pytest -q tests\unit\test_accessibility_residual_28_fix.py tests\contract\test_backend_ssr_sidebar_shell.py tests\architecture\test_ssr_catalogos_boundaries.py tests\architecture\test_ssr_template_canonical_link_guards.py tests\architecture\test_ssr_treinamentos_boundaries.py tests\architecture\test_ssr_treinamentos_attachments_exports_boundaries.py
19 passed in 0.34s
```

## Resultado

Bloqueador removido: SIM
