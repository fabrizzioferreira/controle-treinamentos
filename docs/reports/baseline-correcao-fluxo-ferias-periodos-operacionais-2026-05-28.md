# Baseline tecnico - Correcao do fluxo de ferias/periodos operacionais

Data: 2026-05-28
Workspace: `C:\apps\controle-treinamentos`
Status: backend pronto para HML; producao condicionada a smoke autenticado com banco de homologacao.

## 1. Problema original

Ao tentar cadastrar um periodo de ferias na tela de tripulantes, a interface exibia:

`Cadastro de perÃ­odos operacionais ainda nÃ£o estÃ¡ habilitado neste backend. Codigo: webreq-...`

O problema tinha dois sintomas:

- o cadastro retornava `501` porque o backend mantinha o fluxo como placeholder;
- a mensagem vinha com mojibake porque o literal estava salvo corrompido no backend.

## 2. Causa-raiz

A causa-raiz funcional era desalinhamento entre frontend publicado e backend:

- o artefato frontend publicado ja renderizava formulario de ferias e chamava `GET`, `POST` e `DELETE` em `/api/v1/tripulantes/{id}/periodos-operacionais`;
- o backend possuia apenas rotas de compatibilidade;
- `GET` retornava sempre `items: []`;
- `POST` e `DELETE` retornavam `501 tripulante_periodos_operacionais_not_implemented`;
- nao havia tabela, repository ou use case para persistir periodos.

A causa-raiz de encoding era local ao backend: a mensagem de erro estava salva como mojibake no literal Python da rota.

## 3. Correções realizadas

- Substituido o placeholder por fluxo backend real.
- Criada tabela propria `tripulante_periodos_operacionais`.
- Implementado cadastro de periodo de ferias com retorno `201`.
- Implementada listagem real com retorno `items`.
- Implementado cancelamento logico via `DELETE`, preservando historico com `status = cancelado`.
- Implementadas validacoes de `tipo`, `data_inicio`, `data_fim`, intervalo e `observacao`.
- Bloqueada sobreposicao entre periodos ativos.
- Corrigido encoding das mensagens envolvidas usando Unicode correto.
- Incluida a nova tabela no schema/bootstrap canonico.
- Periodos operacionais passaram a contar como dependencia historica do tripulante, evitando exclusao fisica acidental.

## 4. Arquivos/módulos afetados

- `backend/src/controle_treinamentos/api/http/cadastros/routes.py`
  - troca das rotas placeholder por chamadas aos use cases reais.
- `backend/src/controle_treinamentos/application/tripulante_operational_periods.py`
  - novo modulo de regras, validacao, serializacao, transacao e auditoria.
- `backend/src/controle_treinamentos/repositories/tripulante_operational_periods.py`
  - novo repository de leitura, insercao, sobreposicao e cancelamento.
- `backend/src/controle_treinamentos/db/schema.py`
  - nova tabela, constraints, indices e colunas esperadas.
- `backend/src/controle_treinamentos/repositories/tripulantes.py`
  - periodos operacionais adicionados ao resumo de dependencias.
- `backend/src/controle_treinamentos/application/tripulantes.py`
  - exclusao fisica de tripulante passa a considerar periodos como vinculo historico.
- `tests/contract/test_api_tripulantes_contract.py`
  - contratos de listagem, criacao, validacao e cancelamento.
- `tests/unit/test_tripulante_operational_periods.py`
  - testes de dominio e ciclo criar/listar/cancelar.

## 5. Testes executados

Comandos executados:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\contract\test_api_tripulantes_contract.py -q
```

Resultado: `16 passed`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_tripulante_operational_periods.py -q
```

Resultado: `4 passed`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_tripulante_status_normalization.py -q
```

Resultado: `3 passed`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_tripulante_operational_status_owner.py::test_delete_tripulante_financeiro_mission_dependency_inactivates_instead_of_physical_delete tests\integration\test_supertest_regression.py -k "ferias or status_filter" -q
```

Resultado: `2 passed, 34 deselected`.

Validacoes adicionais:

- schema/bootstrap confirmou `tripulante_periodos_operacionais`;
- varredura nos arquivos tocados nao encontrou `perÃ`, `nÃ£o`, `estÃ¡`, `Ãƒ` ou `not_implemented`;
- `git diff --check` sem erro de whitespace, apenas avisos esperados de line ending no Windows.

## 6. Dados preservados

A correcao preserva dados existentes porque:

- nao altera `pilotos.status`;
- nao altera `tripulantes.status`;
- nao altera `historico_status_piloto`;
- nao altera calculos financeiros existentes;
- nao reutiliza tabela de status como tabela de periodo;
- nao usa `DELETE` fisico para cancelar ferias;
- nao define `ON DELETE CASCADE` na FK de `tripulante_periodos_operacionais`;
- passa a impedir exclusao fisica de tripulante quando houver periodos registrados.

Nao houve escrita contra banco real de producao durante a validacao.

## 7. Riscos residuais

- O fluxo de ferias existe no artefato frontend publicado, mas nao esta presente no `frontend/src` atual; rebuild sem reconciliacao pode remover a UI.
- A integracao financeira ainda nao consome periodos de ferias para recalculo de produtividade/garantia minima.
- O smoke autenticado completo ainda precisa ser executado em HML com banco de homologacao.
- A tabela nova exige bootstrap/migration aplicado antes do uso em ambiente persistente.
- Existe uma falha conhecida fora do escopo em `tests/unit/test_tripulante_operational_status_owner.py`, relacionada a `financeiro_calculos_horarios.py::status_alias_from_snapshot`.
- Ha outros mojibakes historicos no repositorio fora do fluxo corrigido; nao foram alterados por seguranca de escopo.

## 8. Próximos passos recomendados

1. Aplicar bootstrap/migration em HML.
2. Executar smoke autenticado em HML: abrir tela, cadastrar ferias, listar, cancelar e conferir banco.
3. Reconciliar `frontend/src` com o artefato publicado que contem `tripulanteFeriasForm`.
4. Definir contrato financeiro para consumo dos periodos em produtividade/garantia minima.
5. Criar validacao operacional pre-release com contagem antes/depois em `tripulante_periodos_operacionais`.
6. Tratar mojibakes remanescentes em frente separada, com varredura e testes proprios.
