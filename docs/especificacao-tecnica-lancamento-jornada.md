# Especificação Técnica — Módulo Lançamento de Jornada

Documento gerado por análise estática do repositório `controle-treinamentos`, sem alterar código de aplicação. Evidências principais: frontend em `frontend/src/features/financeiro/bonificacoes-page.js`, serviço em `frontend/src/services/financeiro-lancamentos-jornada-api.js`, rotas em `backend/src/controle_treinamentos/api/http/financeiro/routes.py`, aplicação em `backend/src/controle_treinamentos/application/financeiro_lancamentos_jornada.py`, motor horário em `backend/src/controle_treinamentos/application/financeiro_bonificacao_horaria.py`, motor de produtividade em `backend/src/controle_treinamentos/application/financeiro_bonificacao_produtividade.py`, schema/migrations em `backend/src/controle_treinamentos/db/schema.py` e `backend/src/controle_treinamentos/db/migrations.py`, contratos em `backend/src/controle_treinamentos/contracts/financeiro_http.py`.

Observação de escopo: não houve introspecção contra uma base em produção. Onde o código depende de dados cadastrados, parâmetros financeiros ou estado real do banco, o documento marca como "a confirmar".

## 1. Visão geral do módulo

### 1.1. Finalidade

O módulo Lançamento de Jornada é a superfície operacional única para registrar uma jornada/linha vinculada a uma missão operacional e alimentar, a partir desse mesmo lançamento:

- Bonificação Horária.
- Produtividade.
- Relatórios individuais.
- Relatórios gerais.
- Extrato por período.
- PDFs de fechamento/consulta.
- Auditoria financeira.

O próprio frontend comunica essa intenção: "Lance uma vez e alimente os relatórios de Bonificação Horária e Produtividade com a mesma fonte operacional".

### 1.2. Escopo funcional

O módulo cobre:

- Consulta de grade mensal por competência, função e tripulante.
- Criação de linha de jornada.
- Edição de linha existente.
- Exclusão segura, implementada como cancelamento da missão vinculada.
- Preview financeiro sem persistência.
- Recálculo de linha.
- Recálculo da grade/competência.
- Exportação de PDF da grade.
- Abertura de painéis de produtividade consolidada, extrato por período, relatório geral de horas, relatório geral de produtividade e relatório individual.

Não foi encontrada operação nativa de duplicar linha.

### 1.3. Escopo técnico

A "linha de jornada" não é uma tabela física própria. Ela é um read model/write facade composto por:

- `financeiro_missoes_operacionais`: dados operacionais da missão.
- `financeiro_missao_tripulantes`: participantes e função financeira/operacional da linha.
- `financeiro_calculos_horarios`: cálculo horário vigente da linha.
- `financeiro_calculos_produtividade`: consolidação mensal por tripulante/função.

O `id` exposto como `linha_id` vem de `financeiro_missao_tripulantes.id`.

### 1.4. Dependências principais

- Cadastro de tripulantes (`tripulantes`).
- Cadastro de aeronaves/equipamentos (`equipamentos`).
- Competências financeiras (`financeiro_competencias`).
- Parâmetros financeiros (`financeiro_parametros`).
- Feriados financeiros/nacionais (`financeiro_feriados`).
- Períodos operacionais/férias de tripulantes (`tripulante_periodos_operacionais`, quando disponível).
- Auditoria (`record_audit_event` e catálogo `financeiro_audit_events.py`).
- Gerador de PDF.
- Autenticação/permissões (`backend/src/controle_treinamentos/auth.py`).

### 1.5. Limites do módulo

- Não persiste uma entidade `lancamento_jornada` independente.
- Não recalcula relatórios no frontend; cálculos oficiais vêm do backend.
- Preview não substitui cálculo persistido.
- Edição de `tripulante_id` ou `funcao` da linha é bloqueada no backend.
- Mutação é bloqueada se a competência financeira estiver fechada.
- Campos de regime, limites e memória de cálculo são rastreados principalmente em JSON (`memoria_calculo`, `parametros_usados`), não em colunas dedicadas para todos os detalhes.

## 2. Arquitetura atual

### 2.1. Frontend

Arquivos principais:

- `frontend/src/app/route-registry.js:63`: rota canônica `#/financeiro/lancamentos-jornada`.
- `frontend/src/shell/navigation.js:39`: item de navegação "Lançamentos de Jornada".
- `frontend/src/pages-financeiro.js`: exporta o renderizador.
- `frontend/src/features/financeiro/bonificacoes-page.js`: implementação da tela.
- `frontend/src/services/financeiro-lancamentos-jornada-api.js`: adapter HTTP e normalização de payload/resposta.

Particularidades:

- A implementação vive no arquivo histórico `bonificacoes-page.js`, apesar de renderizar a página de Jornada.
- Rotas legadas `#/financeiro/bonificacoes`, `#/financeiro/bonificacoes/horaria` e `#/financeiro/bonificacoes/produtividade` apontam para a mesma página por compatibilidade.
- O serviço declara `sourceOfTruth: "backend"` e endpoints nativos para grade, criação e cancelamento.
- A UI usa uma tabela larga com rolagem horizontal (`min-width: 1840px`) e hint de deslize no mobile.

### 2.2. Backend

Arquivos principais:

- `backend/src/controle_treinamentos/api/http/financeiro/routes.py:425`: endpoints HTTP do módulo.
- `backend/src/controle_treinamentos/application/financeiro_lancamentos_jornada.py`: orquestra CRUD, listagem, PDF, extrato, produtividade consolidada e recálculos.
- `backend/src/controle_treinamentos/application/financeiro_missoes.py`: criação/atualização/cancelamento/recalculo da missão operacional.
- `backend/src/controle_treinamentos/application/financeiro_bonificacao_horaria.py:225`: motor puro de cálculo horário.
- `backend/src/controle_treinamentos/application/financeiro_bonificacao_produtividade.py:150`: motor puro de produtividade.
- `backend/src/controle_treinamentos/application/financeiro_descanso_minimo.py`: contexto de descanso mínimo entre jornadas.
- `backend/src/controle_treinamentos/repositories/financeiro_lancamentos_jornada.py`: query/read model da grade.

### 2.3. Banco de dados

Tabelas diretamente envolvidas:

- `financeiro_missoes_operacionais`.
- `financeiro_missao_tripulantes`.
- `financeiro_calculos_horarios`.
- `financeiro_calculos_produtividade`.
- `financeiro_competencias`.
- `financeiro_parametros`.
- `financeiro_feriados`.
- `tripulantes`.
- `equipamentos`.

Não foram encontradas triggers específicas para Jornada no schema analisado.

### 2.4. Contratos/API

Contrato declarado em `backend/src/controle_treinamentos/contracts/financeiro_http.py:235` a `:436`, com endpoints:

- `GET /api/v1/financeiro/lancamentos-jornada`
- `POST /api/v1/financeiro/lancamentos-jornada`
- `POST /api/v1/financeiro/lancamentos-jornada/preview`
- `POST /api/v1/financeiro/lancamentos-jornada/recalcular-grade`
- `GET /api/v1/financeiro/lancamentos-jornada.pdf`
- `PATCH /api/v1/financeiro/lancamentos-jornada/{id}`
- `DELETE /api/v1/financeiro/lancamentos-jornada/{id}`
- `POST /api/v1/financeiro/lancamentos-jornada/{id}/recalcular`

### 2.5. Integrações

- Missões operacionais: Jornada cria/atualiza/cancela missão.
- Bonificação horária: recalcula por participante.
- Produtividade: recalcula competência após salvar/cancelar/recalcular.
- Relatórios/PDFs: leem cálculos persistidos vigentes.
- Auditoria: eventos próprios de jornada e eventos herdados de missão/cálculo/competência.
- Permissões: leitura, criação, edição, exclusão, recálculo e exportação têm permissões diferentes.

## 3. Entidades e tabelas envolvidas

### `financeiro_missoes_operacionais`

Finalidade: armazena a missão operacional base da linha de jornada.

Campos principais:

| Campo | Tipo | Obrigatório | Default | Regras/constraints |
|---|---:|---:|---|---|
| `id` | `BIGSERIAL` | sim | auto | PK |
| `org_id` | `TEXT` | sim | `default_single_tenant` | escopo organizacional |
| `competencia` | `TEXT` | sim | - | `YYYY-MM` |
| `data_missao` | `DATE` | sim | - | data inicial |
| `data_final` | `DATE` | não | - | `data_final IS NULL OR data_final >= data_missao` |
| `cavok_numero_voo` | `TEXT` | não | - | exibido como Rel. voo |
| `contratante` | `TEXT` | não | - | usado também em duplicidade |
| `chamado` | `TEXT` | não | - | exibido como N. DB |
| `aeronave_id` | `INTEGER` | não no banco, exigido pela Jornada | - | FK `equipamentos(id)` |
| `categoria_financeira_aeronave` | `TEXT` | não no banco, exigido pela Jornada | - | categorias normalizadas |
| `comandante_tripulante_id` | `INTEGER` | sim | - | FK `tripulantes(id)` |
| `copiloto_tripulante_id` | `INTEGER` | não | - | FK; pelo menos copiloto ou terceiro |
| `terceiro_tripulante_id` | `INTEGER` | não | - | FK |
| `terceiro_tripulante_funcao` | `TEXT` | condicional | - | `comandante` ou `copiloto`; consistente com terceiro |
| `tipo_tripulacao_jornada` | `TEXT` | sim | `simples` | `simples`, `composta`, `revezamento` |
| `horario_apresentacao` | `TIMESTAMP` | não | - | se ambos preenchidos, abandono > apresentação |
| `horario_abandono` | `TIMESTAMP` | não | - | se menor/igual apresentação, aplicação ajusta para dia seguinte |
| `pos_exec_min` | `INTEGER` | sim | `0` | `>= 0` |
| `trecho` | `TEXT` | não | - | texto livre |
| `houve_pernoite` | `BOOLEAN` | sim | `FALSE` | derivado de `quantidade_pernoites > 0` na aplicação |
| `quantidade_pernoites` | `INTEGER` | sim | `0` | `>= 0` |
| `cobertura_base` | `BOOLEAN` | sim | `FALSE` | agregado dos participantes |
| `operacao_especial` | `TEXT` | não | - | detecta Palmas/turbohélice |
| `justificativa` | `TEXT` | não | - | texto livre |
| `status` | `TEXT` | sim | `rascunho` | `rascunho`, `ativa`, `cancelada`, `recalculo_pendente` |
| `observacoes` | `TEXT` | não | - | texto livre |
| `created_by/created_at/updated_by/updated_at` | vários | parcial | timestamps | rastreio operacional |
| `deleted_by/deleted_at/delete_reason` | vários | não | - | exclusão lógica/cancelamento seguro |

Constraints relevantes:

- Comandante e copiloto distintos quando copiloto existe.
- Ao menos `copiloto_tripulante_id` ou `terceiro_tripulante_id`.
- Terceiro e função adicional devem ser ambos nulos ou ambos preenchidos.
- Terceiro deve ser distinto de comandante e copiloto.
- Regime deve estar no domínio `simples`, `composta`, `revezamento`.
- Horários válidos quando ambos presentes.

### `financeiro_missao_tripulantes`

Finalidade: materializa as linhas/participantes da missão. A linha de Jornada usa `id` desta tabela.

| Campo | Tipo | Obrigatório | Default | Regras |
|---|---:|---:|---|---|
| `id` | `BIGSERIAL` | sim | auto | PK/linha_id |
| `org_id` | `TEXT` | sim | `default_single_tenant` | escopo |
| `missao_operacional_id` | `BIGINT` | sim | - | FK missão, `ON DELETE CASCADE` |
| `tripulante_id` | `INTEGER` | sim | - | FK tripulantes |
| `funcao` | `TEXT` | sim | - | `comandante` ou `copiloto` |
| `cobertura_base` | `BOOLEAN` | sim | `FALSE` | por participante |
| `status` | `TEXT` | sim | `ativo` | `ativo`, `removido`, `cancelado` |
| `created_at` | `TIMESTAMP` | sim | `CURRENT_TIMESTAMP` | - |

Constraint: `UNIQUE(org_id, missao_operacional_id, tripulante_id)`.

Regra implícita importante: nas queries da Jornada, a função efetiva da linha é `tripulantes.funcao_operacional` se ela estiver em `comandante/copiloto`; caso contrário, usa `financeiro_missao_tripulantes.funcao`. Isso pode divergir da função da missão.

### `financeiro_calculos_horarios`

Finalidade: cálculo horário vigente/obsoleto por missão, tripulante e função.

| Campo | Tipo | Observações |
|---|---:|---|
| `id` | `BIGSERIAL` | PK |
| `org_id` | `TEXT` | escopo |
| `missao_operacional_id` | `BIGINT` | FK missão |
| `tripulante_id` | `INTEGER` | FK tripulante |
| `funcao` | `TEXT` | `comandante`/`copiloto` |
| `jornada_total_minutos` | `INTEGER` | duração real apresentação-abandono |
| `minutos_diurnos` | `INTEGER` | minutos em período diurno |
| `minutos_noturnos` | `INTEGER` | uso legado/compatibilidade |
| `minutos_noturnos_reais` | `INTEGER` | noite real antes de conversão |
| `horas_noturnas_convertidas` | `NUMERIC(10,4)` | noite + pré + pós em hora reduzida |
| `minutos_pre` | `INTEGER` | sobreposição com descanso mínimo |
| `minutos_pos` | `INTEGER` | extrapolação após limite regulamentar + pós execução |
| `domingo_feriado` | `BOOLEAN` | houve fatia especial |
| `valor_adicional_noturno` | `NUMERIC(14,2)` | noite normal |
| `valor_domingo_feriado_diurno` | `NUMERIC(14,2)` | dia especial |
| `valor_domingo_feriado_noturno` | `NUMERIC(14,2)` | noite especial |
| `valor_pre` | `NUMERIC(14,2)` | pré jornada |
| `valor_pos` | `NUMERIC(14,2)` | pós jornada/extrapolação |
| `total` | `NUMERIC(14,2)` | soma horária |
| `memoria_calculo` | `JSONB` | entradas, passos, avisos, fórmula |
| `parametros_usados` | `JSONB` | referências dos parâmetros |
| `calculation_version` | `TEXT` | default `v1`; motor atual `finance-hourly-v1` |
| `status` | `TEXT` | `calculado`, `recalculo_pendente`, `obsoleto` |
| `calculated_at` | `TIMESTAMP` | default current timestamp |

Índice único parcial: uma linha vigente por `(org_id, missao_operacional_id, tripulante_id, funcao)` quando `status <> 'obsoleto'`.

### `financeiro_calculos_produtividade`

Finalidade: cálculo consolidado mensal por tripulante/função.

Campos principais: `competencia`, `tripulante_id`, `funcao`, `categoria_aplicavel`, `valor_icao`, `valor_instrutor`, `valor_checador`, `valor_missoes_categoria_a`, `valor_missoes_categoria_b`, `valor_cobertura_base`, `valor_pernoite_comum`, `valor_excecao_palmas`, `produtividade_calculada`, `garantia_minima`, `total_devido`, `memoria_calculo`, `parametros_usados`, `calculation_version`, `status`.

Constraint: `UNIQUE(org_id, competencia, tripulante_id, funcao)`.

### `financeiro_competencias`

Finalidade: controla status da competência e totais/snapshot. Jornada lê status para bloquear mutações quando `fechada`.

### `financeiro_parametros`

Finalidade: fonte dos parâmetros de cálculo horário e produtividade.

Parâmetros horários obrigatórios por função/data:

- `duracao_hora_noturna_minutos`, unidade `minutos`.
- `periodo_diurno_inicio`, unidade `minutos_do_dia`.
- `periodo_diurno_fim`, unidade `minutos_do_dia`.
- `adicional_noturno`, unidade `valor`, por função.
- `domingo_feriado_diurno`, unidade `valor`, por função.
- `domingo_feriado_noturno`, unidade `valor`, por função.

Parâmetros de produtividade:

- `icao_sdea`
- `instrutor`
- `checador`
- `missao_categoria_a`
- `missao_categoria_b`
- `cobertura_base`
- `pernoite_comum_sem_cobertura`
- `garantia_minima`
- `excecao_palmas_turbohelice`

### `financeiro_feriados`

Finalidade: informa feriados nacionais ativos para fatiamento especial de cálculo.

### `tripulantes`

Usada para validar existência/status ativo, função operacional efetiva, categoria operacional, CPF/licença e flags de produtividade (`sdea`, instrutor, checador etc.).

### `equipamentos`

Usada para validar aeronave ativa, nome/tipo e categoria financeira.

## 4. Dicionário completo de campos

| UI | Técnico principal | Tipo | Origem | Manual/auto | Obrig. Jornada | Default | Validações/dependências | Impacto |
|---|---|---:|---|---|---:|---|---|---|
| Data inicial | `data`/`data_missao` | date | UI -> missão | manual | sim | filtro competência/new | formato date; deve pertencer à competência; base de horários | cálculo, relatórios, feriados, competência |
| Data final | `data_final` | date | UI -> missão | manual | não | data inicial | não anterior à inicial | virada de dia, fatiamento, relatórios |
| Comandante | `comandante_tripulante_id` | int | tripulantes | manual/derivado | sim | filtro/linha | ativo; distinto; obrigatório | participante, cálculo, produtividade, auditoria |
| Segundo tripulante | `copiloto_tripulante_id` | int | tripulantes | manual/derivado | condicional | vazio | ativo; distinto; exige copiloto ou terceiro | participante e cálculo |
| 3º tripulante | `terceiro_tripulante_id` | int | tripulantes | manual | não | vazio | se informado exige função; distinto | participante adicional |
| Função 3º trip. | `terceiro_tripulante_funcao` | enum | UI | manual | condicional | vazio | `comandante` ou `copiloto`; consistente com terceiro | função financeira do terceiro |
| Tripulante da linha | `tripulante_id` | int | derivado da tripulação/filtro | automático na UI; obrigatório no payload | sim | filtro | deve ser um dos tripulantes e ativo | chave da linha/cálculo |
| Função da linha | `funcao` | enum | derivado/efetivo | automático na UI; obrigatório no payload | sim | filtro ou função operacional | `comandante`/`copiloto`; não editável após criar | cálculo, parâmetros, relatórios |
| Aeronave | `aeronave_id` | int | equipamentos | manual | sim | vazio | deve existir e estar ativa | categoria, produtividade, relatórios |
| Categoria/tipo | `categoria_financeira_aeronave`/`tipo` | text/enum | equipamento/payload | automático com aeronave; editável como texto | sim no payload Jornada | categoria do equipamento | aceita aliases `a`, `b`, `turbohelice_palmas`, `vd/vn/normal` com fallback | produtividade/categoria |
| Rel. voo | `relatorio_voo`/`cavok_numero_voo` | text | UI | manual | não | vazio | texto livre; entra na duplicidade quando combinado | relatórios/PDF |
| N. DB | `numero_db`/`chamado` | text | UI | manual | não | vazio | texto livre; entra na duplicidade quando combinado | relatórios/PDF |
| Contratante | `contratante` | text | UI | manual | não | vazio | texto livre; entra na duplicidade quando combinado | relatórios/PDF |
| Trecho | `trecho` | text | UI | manual | não | vazio | texto livre | descrição em extrato/PDF |
| Pernoites | `quantidade_pernoites` | int | UI | manual | não | `0` | inteiro não negativo | produtividade/pernoite comum/cobertura |
| Houve pernoite | `houve_pernoite` | bool | aplicação | automático | não | `false` | `quantidade_pernoites > 0` | produtividade |
| Cobertura | `cobertura_base` + participantes | bool | UI | manual por tripulante; agregado automático | não | `false` | só conta se pernoites > 0 | produtividade/cobertura |
| Cond. especial | `operacao_especial` | text | UI | manual | não | vazio | texto livre; reconhece Palmas/turbohélice | produtividade exceção Palmas |
| Regime jornada | `tipo_tripulacao_jornada` | enum | UI | manual | não | `simples` | `simples`, `composta`, `revezamento` | limite de jornada e pós cálculo |
| Apresentação | `hora_apresentacao`/`horario_apresentacao` | time/datetime | UI | manual | não para salvar; sim para cálculo não zero | vazio | `HH:MM`/ISO; base data inicial | jornada/diurna/noturna/limite |
| Abandono | `hora_abandono`/`horario_abandono` | time/datetime | UI | manual | não para salvar; sim para cálculo não zero | vazio | `HH:MM`/ISO; se <= apresentação soma 1 dia | jornada/fatiamento |
| Pós exec. min | `pos_exec_min` | int | UI | manual | não | `0` | não negativo | amplia fim efetivo para extrapolação |
| Justif. | `justificativa` | text | UI | manual | não | vazio | texto livre | auditoria/relatórios |
| Obs | `observacao`/`observacoes` | text | UI | manual | não | vazio | texto livre | auditoria/relatórios |
| Diurna | `minutos_diurnos` | int | cálculo | automático | não | `0` | não negativo | relatório horário |
| Noturna | `minutos_noturnos_reais`/`minutos_noturnos` | int | cálculo | automático | não | `0` | não negativo | hora reduzida/valor noturno |
| Pré calc min | `minutos_pre` | int | cálculo descanso mínimo | automático | não | `0` | depende de jornada anterior | valor pré |
| Pós calc | `minutos_pos` | int | cálculo limite jornada | automático | não | `0` | depende de regime e pós execução | valor pós |
| Total | `total`/`calculo_total` | money | cálculo | automático | não | `0.00` | soma valores horários vigentes | grade/PDF/indicadores |
| Status | `status` | enum derivado | missão/linha/cálculo | automático | não | `pendente` | cancelada, ativo, calculado, pendente | UI, bloqueios, relatórios |

Comportamento em dados legados:

- `data_final` ausente cai para `data_missao`.
- `tipo_tripulacao_jornada` ausente/vazio vira `simples`.
- `minutos_noturnos_reais` ausente cai para `minutos_noturnos`.
- `cobertura_base` da missão funciona como fallback para participantes quando flags individuais antigas não existem.
- Categoria legada `vd`, `vn`, `normal` tenta usar categoria do equipamento; sem equipamento vira `nao_aplicavel`.

## 5. Regras de negócio

### 5.1. Regras de criação

- A competência é obrigatória e deve estar em `YYYY-MM`.
- `data`/`data_missao`, `tripulante_id`, `funcao`, `aeronave_id` e categoria financeira são obrigatórios no contrato Jornada.
- A data inicial deve estar dentro da competência informada.
- A competência não pode estar fechada.
- Tripulante informado deve existir e estar ativo.
- Aeronave deve existir e estar ativa.
- Deve haver comandante e ao menos segundo tripulante ou terceiro tripulante.
- Comandante, segundo e terceiro devem ser distintos.
- Terceiro tripulante exige função; função de terceiro sem tripulante é inválida.
- Ao criar pela Jornada, status padrão enviado à missão é `ativa`.
- Horários podem ficar em branco; nesse caso a missão é salva e o cálculo horário vigente fica zerado com aviso.
- Após criar, o backend recalcula a missão e tenta recalcular produtividade da competência na mesma transação.

### 5.2. Regras de edição

- Busca por `linha_id` (`financeiro_missao_tripulantes.id`).
- Se não existir: `finance_journey_line_not_found`.
- Se competência da missão estiver fechada: bloqueia.
- Alterar `tripulante_id` ou `funcao` é explicitamente bloqueado com `finance_journey_crew_change_not_supported`.
- Demais campos são transformados em payload de missão e salvos via `atualizar_missao_operacional`.
- Após atualizar, recalcula missão e produtividade.

### 5.3. Regras de exclusão/inativação

- Exige `motivo` ou `reason`.
- Se não houver motivo: `finance_journey_line_delete_reason_required`.
- Se linha não tiver missão vinculada: `finance_journey_line_without_mission_delete_blocked`.
- A ação cancela a missão operacional vinculada, invalida/recalcula dependências e recalcula produtividade.
- Resposta retorna `action: "cancelled"`.
- Não há hard delete da linha pela rota de Jornada.

### 5.4. Regras de competência/período

- Leitura é permitida em competência fechada.
- Criação, edição, exclusão e recálculo são bloqueados quando a competência está `fechada`.
- UI bloqueia editar, excluir/recalcular e adicionar linha quando `statusCompetencia` é `fechada`.
- Data inicial fora do mês da competência gera `finance_journey_date_outside_competencia`.

### 5.5. Regras de tripulantes

- Funções financeiras válidas: `comandante`, `copiloto`.
- A função efetiva na query pode vir de `tripulantes.funcao_operacional`, não apenas da função do participante.
- Para recálculo deve existir ao menos um comandante e dois tripulantes distintos.
- Tripulante inativo bloqueia criação/edição via validação Jornada.
- A UI não permite editar diretamente "Tripulante da linha" e "Função da linha"; esses campos são derivados da seleção de comandante/copiloto/terceiro e dos filtros.

### 5.6. Regras de aeronave

- `aeronave_id` é obrigatório na Jornada, embora a coluna seja nullable.
- Aeronave deve estar ativa.
- Seleção de aeronave no frontend preenche `categoria_financeira_aeronave`/`tipo` a partir do option dataset.
- Limpar aeronave limpa também categoria/tipo no draft.

### 5.7. Regras de jornada

- Apresentação e abandono são opcionais para salvar pela Jornada.
- Se ambos existem e abandono <= apresentação, o backend soma um dia ao abandono.
- Se abandono não tem data explícita e `data_final > data_missao`, usa `data_final` para o abandono.
- Jornada total = diferença em minutos entre apresentação e abandono.
- Jornada sem horários gera cálculo zero persistido com warning.

### 5.8. Regras de pernoite

- `quantidade_pernoites` não pode ser negativa.
- `houve_pernoite` é verdadeiro somente se quantidade > 0.
- Tipo exibido:
  - `sem_pernoite` quando quantidade <= 0.
  - `cobertura_base` quando há cobertura.
  - `pernoite_comum` quando há pernoite sem cobertura.
- Pernoite comum remunerável = `max(quantidade_pernoites - 1, 0)`.
- Produtividade aplica pernoite comum somente a partir do segundo pernoite e sem cobertura.

### 5.9. Regras de cobertura

- UI exibe checkboxes de cobertura por comandante, segundo e terceiro tripulante.
- Cobertura só é enviada como verdadeira se `quantidade_pernoites > 0`.
- `cobertura_base` da missão é agregado: verdadeiro se algum participante tem cobertura.
- Produtividade soma `quantidade_cobertura_base * parâmetro_cobertura_base`.
- Se flag geral `cobertura_base=True` chegar ao motor sem missões contadas, o motor força contagem mínima 1.

### 5.10. Regras de condição especial

- Campo livre `operacao_especial`.
- A condição Palmas/turbohélice é detectada por texto normalizado contendo `palmas` e termos como `turbohelice`, `turboelice`, `turbo`, `helice` ou `elice`.
- Também há categoria canônica `turbohelice_palmas`.
- Impacta produtividade via parâmetro `excecao_palmas_turbohelice`.

### 5.11. Regras de regime de jornada

- Regimes válidos: `simples`, `composta`, `revezamento`.
- Default: `simples`.
- Armazenado em `financeiro_missoes_operacionais.tipo_tripulacao_jornada`.
- Exibido na grade como "Regime jornada" e editado por radio/segmento.
- Impacta exclusivamente o limite regulamentar usado para calcular `minutos_pos`.
- Dados antigos sem regime são migrados/defaultados para `simples`.
- Evitar inferência automática indevida: o regime vem do campo persistido; se ausente/vazio, o default é explícito `simples`.
- Auditoria do regime aplicado fica em `tipo_tripulacao_jornada`, `memoria_calculo.inputs` e serialização de cálculo.

### 5.12. Regras de justificativa e observação

- `justificativa` e `observacao` são textos livres.
- `observacao` no frontend é enviado também como `observacoes`.
- Não há validação de obrigatoriedade encontrada.
- Entram na persistência da missão e podem aparecer em relatórios/auditoria.

## 6. Cálculos

### Cálculo 1: Intervalo de jornada

Objetivo: obter início/fim e duração real da jornada.

Entrada: `data_missao`, `data_final`, `horario_apresentacao`, `horario_abandono`.

Fórmula natural:

- Converte apresentação e abandono para `datetime`.
- Se abandono não possui data explícita e `data_final > data_missao`, combina abandono com `data_final`.
- Se abandono <= apresentação, soma 1 dia ao abandono.
- Jornada total = minutos entre apresentação e abandono.

Pseudocódigo:

```text
start = parse_datetime(apresentacao, base=data_missao)
end = parse_datetime(abandono, base=data_missao)
if end_sem_data_explicit and data_final > data_missao:
    end = combine(data_final, end.time)
if end <= start:
    end = end + 1 day
jornada_total_minutos = floor((end - start).minutes)
if jornada_total_minutos <= 0:
    erro bonificacao_horaria_jornada_invalida
```

Saída: `jornada_total_minutos`, intervalo resolvido em memória.

Local: `financeiro_bonificacao_horaria.py:638` e `:225`.

Exemplo: apresentação `23:00`, abandono `10:20` no dia seguinte -> 680 minutos.

Edge cases:

- Horários ausentes no fluxo Jornada não entram no motor; são zerados em `financeiro_missoes.py`.
- Data final anterior à inicial gera erro antes do motor.

### Cálculo 2: Fatiamento diurno/noturno

Objetivo: separar minutos em período diurno e noturno, normal e domingo/feriado.

Entrada: intervalo resolvido, parâmetros `periodo_diurno_inicio`, `periodo_diurno_fim`, feriados.

Fórmula natural:

- Divide o intervalo por dias de calendário.
- Para cada dia, classifica se é domingo ou feriado.
- Dentro de cada dia, calcula interseção com período diurno parametrizado.
- Minutos fora do diurno são noturnos.

Pseudocódigo:

```text
for each calendar slice in interval:
    special = date is Sunday or date in feriados
    day_minutes = overlap(slice, diurnal_window)
    night_minutes = slice.minutes - day_minutes
    bucket = special ? special : normal
    bucket.diurnal += day_minutes
    bucket.night += night_minutes
```

Saídas: `minutos_diurnos`, `minutos_noturnos_reais`, fatias em `memoria_calculo`.

Local: `financeiro_bonificacao_horaria.py:951` e `:1002`.

Exemplo canônico: 08:00-18:00 com diurno 06:00-18:00 -> 600 diurnos, 0 noturnos.

### Cálculo 3: Hora reduzida/noturna convertida

Objetivo: converter minutos noturnos, pré e pós em horas reduzidas.

Entrada: `minutos_noturnos_reais`, `minutos_pre`, `minutos_pos`, parâmetro `duracao_hora_noturna_minutos`.

Fórmula natural:

- Horas reduzidas = minutos remuneráveis noturnos/pré/pós divididos pela duração da hora noturna.
- Arredonda apenas a saída de `horas_noturnas_convertidas` para 4 casas; valores monetários usam precisão interna e arredondam em centavos.

Pseudocódigo:

```text
converted = (normal_night + special_night + pre + pos) / duracao_hora_noturna_minutos
horas_noturnas_convertidas = round_half_up(converted, 4)
```

Saída: `horas_noturnas_convertidas`.

Local: `financeiro_bonificacao_horaria.py:225`.

Exemplo de teste: 105 minutos noturnos com hora reduzida de 52,5 min -> 2,0000 horas.

### Cálculo 4: Limite regulamentar por regime

Objetivo: determinar o horário limite da jornada antes de extrapolação.

Entrada: `horario_apresentacao`, `tipo_tripulacao_jornada`, tabela regulamentar.

Fórmula natural:

- Usa tabela de 96 pontos de 15 em 15 minutos.
- Cada linha possui duração máxima para `simples`, `composta`, `revezamento`.
- Se apresentação cai exatamente no bucket, usa valor exato.
- Se cai entre buckets, interpola linearmente e arredonda para minuto inteiro com `ROUND_HALF_UP`.
- Se tabela ausente, usa tabela padrão hardcoded no motor.

Pseudocódigo:

```text
entries = tabela_configurada or DEFAULT_JORNADA_REGULAMENTAR
duration = interpolate(entries[regime], minute_of_day(apresentacao))
limite_jornada = apresentacao + duration minutes
```

Saídas: `limite_jornada`, `limite_jornada_minutos` em memória/serialização.

Local: `financeiro_bonificacao_horaria.py:43`, `:785`, `:806`.

Exemplos de teste:

- 23:00 simples -> limite 08:30, 570 min.
- 23:00 composta -> limite 11:30, 750 min.
- 12:00 simples -> duração 592 min.
- 12:00 composta -> 750 min.
- 12:00 revezamento -> 1067 min.

Risco: o backend tenta buscar tabela em `produtividade_parametros` (`jornada_tabela_regulamentar`); se falhar, usa hardcode. Confirmar se essa tabela existe no ambiente alvo.

### Cálculo 5: Pós cálculo/extrapolação

Objetivo: calcular minutos depois do limite regulamentar, considerando pós-execução.

Entrada: abandono, `pos_exec_min`, `limite_jornada`.

Fórmula natural:

- Fim efetivo = abandono + `pos_exec_min`.
- Se fim efetivo > limite, `minutos_pos` = diferença.
- Caso contrário, zero.
- O intervalo pós também é fatiado entre normal/especial para valor monetário.

Pseudocódigo:

```text
duty_effective_end = abandono + pos_exec_min
if duty_effective_end > limite_jornada:
    minutos_pos = minutes(limite_jornada, duty_effective_end)
else:
    minutos_pos = 0
```

Saída: `minutos_pos`, `valor_pos`.

Local: `financeiro_bonificacao_horaria.py:225`.

Exemplo de teste: 23:00-10:20 simples, limite 08:30 -> `minutos_pos = 110`.

### Cálculo 6: Pré cálculo por descanso mínimo

Objetivo: remunerar/indicar período que invade repouso mínimo regulamentar entre jornadas.

Entrada: última jornada válida anterior à competência, linhas da competência por tripulante, fim da jornada anterior, início da próxima.

Fórmula natural:

- Para cada tripulante, ordena jornadas por início.
- Calcula a duração da jornada anterior.
- Repouso exigido: 12h se duração <= 12h; 16h se duração > 12h e <= 15h; 24h se duração > 15h.
- Descanso mínimo até = fim anterior + repouso exigido.
- Se início da próxima < descanso mínimo até, envia `descanso_minimo_ate` ao motor.
- `minutos_pre` = minutos de apresentação até `min(descanso_minimo_ate, abandono)`.

Pseudocódigo:

```text
for tripulante in linhas:
    sort by start
    duracao = minutes(previous.end - previous.start)
    repouso = repouso_minimo_exigido_minutos(duracao)
    if current.start < previous.end + repouso:
        context[current.mission][tripulante] = previous.end + repouso
```

Saída: `minutos_pre`, `valor_pre`.

Local: `financeiro_descanso_minimo.py`, `financeiro_bonificacao_horaria.py:225`.

Exemplo de teste: descanso até 06:00, jornada 04:00-09:30 -> `minutos_pre = 120`.

### Cálculo 7: Valores horários

Objetivo: monetizar adicional noturno, domingo/feriado diurno/noturno, pré e pós.

Entradas: fatias normais/especiais, parâmetros financeiros.

Fórmula natural:

- Noite normal: horas reduzidas normais * `adicional_noturno`.
- Domingo/feriado diurno: horas diurnas especiais * `domingo_feriado_diurno`.
- Domingo/feriado noturno: horas noturnas especiais reduzidas * `domingo_feriado_noturno`.
- Pré normal: minutos pré normais / duração hora noturna * `adicional_noturno`.
- Pré especial: minutos pré especiais / duração hora noturna * `domingo_feriado_noturno`.
- Pós segue a mesma lógica de pré.
- Total = soma dos cinco valores.

Pseudocódigo:

```text
valor_adicional_noturno = normal_night_hours * adicional_noturno
valor_domingo_feriado_diurno = special_day_hours * domingo_feriado_diurno
valor_domingo_feriado_noturno = special_night_hours * domingo_feriado_noturno
valor_pre = normal_pre_hours * adicional_noturno + special_pre_hours * domingo_feriado_noturno
valor_pos = normal_pos_hours * adicional_noturno + special_pos_hours * domingo_feriado_noturno
total = round_money(sum(values))
```

Arredondamento: `ROUND_HALF_UP` para centavos.

Local: `financeiro_bonificacao_horaria.py:225`.

Exemplo de teste: 2026-04-04 06:15-19:30, comandante com parâmetros 92,18/92,18/184,36 -> total 447,73; `minutos_pos=165`; `horas_noturnas_convertidas=4,8571`.

### Cálculo 8: Cálculo zero por horários ausentes

Objetivo: permitir salvar lançamento incompleto sem quebrar grade.

Entrada: missão sem apresentação ou sem abandono.

Fórmula natural: todos os minutos e valores são zero; status do cálculo fica `calculado`; memória inclui warning `finance_hourly_missing_times_zeroed`. O passo interno da memória usa `rule_key: jornada_sem_horarios`.

Pseudocódigo:

```text
if missing(apresentacao) or missing(abandono):
    save calculation with all minutes/values = 0
    memory.warnings += finance_hourly_missing_times_zeroed
    memory.steps[].rule_key = jornada_sem_horarios
```

Local: `financeiro_missoes.py:1037`, `:1051`.

### Cálculo 9: Produtividade, pernoite, cobertura e Palmas

Objetivo: consolidar produtividade mensal por tripulante/função.

Entrada: participações da competência, categoria da aeronave, pernoites, cobertura, condição especial, flags cadastrais do tripulante, parâmetros.

Fórmula natural resumida:

- Conta missões categoria A/B.
- Conta cobertura de base.
- Conta pernoite comum sem cobertura a partir do segundo pernoite.
- Detecta exceção Palmas/turbohélice.
- Soma valores cadastrais (`icao_sdea`, `instrutor`, `checador`), missões por categoria, cobertura, pernoite comum e exceções.
- Aplica proporcionalidade de férias em componentes cadastrais/garantia.
- `total_devido = max(produtividade_calculada, garantia_minima)`, salvo quando garantia não se aplica.

Pseudocódigo:

```text
counts.categoria_a = count(missoes categoria a)
counts.categoria_b = count(missoes categoria b)
if missao.cobertura_base:
    counts.cobertura_base += quantidade_pernoites or 1
else if quantidade_pernoites > 1:
    counts.pernoite_comum += quantidade_pernoites - 1
if palmas_turbohelice:
    counts.excecao_palmas += 1

produtividade_sem_piso =
    valor_icao + valor_instrutor + valor_checador +
    valor_categoria_a + valor_categoria_b +
    valor_cobertura_base + valor_pernoite_comum

if excecao_palmas_turbohelice:
    valor_excecao_palmas = max(piso_palmas_proporcional - produtividade_sem_piso, 0)
else:
    valor_excecao_palmas = quantidade * parametro_excecao

produtividade_calculada = produtividade_sem_piso + valor_excecao_palmas
total_devido = max(produtividade_calculada, garantia_minima)
```

Local: `financeiro_bonificacao_produtividade.py:150`, `_mission_counts` em `:786`.

### Cálculo 10: Indicadores da grade

Objetivo: gerar cards/resumo da competência.

Fórmula natural:

- `total_geral` = soma de totais horários pagáveis + total produtividade pagável.
- `hora_reduzida_total` = soma de hora reduzida.
- `excecoes` = linhas com warnings/condição especial.
- `alertas_descanso` = linhas com `pos_exec_min > 0`.
- Domingos/feriados vêm da classificação de linhas/datas.

Local: `financeiro_lancamentos_jornada.py:644`.

## 7. Fluxos funcionais

### 7.1. Criar lançamento

1. Usuário clica "Adicionar linha".
2. UI cria draft `new`, foca primeiro campo e inicia preview como insuficiente.
3. Usuário preenche campos.
4. UI monta payload com `updatePayloadFromDraft`.
5. Validação frontend verifica campos mínimos e tripulação.
6. `POST /api/v1/financeiro/lancamentos-jornada`.
7. Backend transforma em missão operacional.
8. Valida competência aberta, tripulante/aeronave ativos, data/categoria/tripulação.
9. Cria missão com participantes.
10. Recalcula missão.
11. Recalcula produtividade da competência.
12. Audita `finance.journey_line.created` e eventos de missão/cálculo.
13. UI recarrega grade.

### 7.2. Editar lançamento

1. Usuário clica "Editar".
2. UI cria draft a partir da linha.
3. Tripulante/função da linha ficam derivados, não são inputs.
4. Alterações disparam preview com debounce.
5. Salvar envia `PATCH /{linha_id}`.
6. Backend bloqueia troca de tripulante/função.
7. Atualiza missão e recalcula.
8. Audita `finance.journey_line.updated`.

### 7.3. Salvar lançamento

- Exibe "Salvando..." no botão.
- Em sucesso, mostra flash:
  - cálculo vigente atualizado;
  - produtividade recalculada ou pendente.
- Limpa `editingRowKey`, drafts e erros.
- Recarrega grade.

### 7.4. Recarregar lançamento

- Filtros chamam `loadJornadaGrade`.
- Estado vai para `loading`.
- Serviço chama grade e opções.
- Se linhas retornam: `ready`; se vazio: `empty`.
- Previews de linhas são semeados a partir do cálculo persistido e depois atualizados.

### 7.5. Recalcular

- Recalcular linha: `POST /{linha_id}/recalcular`, bloqueia missão cancelada e competência fechada.
- Recalcular grade: lista até 5000 linhas da competência, calcula descanso mínimo, recalcula cada missão e produtividade.
- UI expõe botão "Recalcular grade" quando há linhas, permissão e competência aberta.

### 7.6. Excluir/inativar

- UI exige não haver linha em edição.
- Confirma ação com modal/confirm helper.
- Motivo é gerado pela UI e enviado como `motivo`.
- Backend cancela missão vinculada e recalcula produtividade.
- UI recarrega a grade.

### 7.7. Gerar relatório

- PDF da grade: botão "Exportar PDF".
- Relatório individual: painel ou botões por linha para Horária/Produtividade.
- Relatório geral de horas e produtividade: painéis próprios.
- Extrato por período: consulta e exportação PDF.
- PDFs validam assinatura `%PDF` e trailer `%%EOF` no backend e no frontend.

### 7.8. Validar competência

- Leitura: permitida.
- Mutação: `validar_competencia_aberta_para_mutacao`.
- Se fechada: `competencia_financeira_fechada`.

### 7.9. Tratar erro

- Erros de domínio retornam payload padronizado.
- UI usa `buildErrorMessage`.
- Erros de permissão aparecem como warning em operações específicas.
- Erros de preview marcam célula como `error`.

## 8. Contratos de API

### `GET /api/v1/financeiro/lancamentos-jornada`

Finalidade: listar grade mensal.

Query:

```json
{
  "competencia": "2026-04",
  "funcao": "comandante",
  "tripulante_id": 7,
  "status": "calculado",
  "page": 1,
  "page_size": 100
}
```

Observação: o frontend envia `page_size=500`, mas o backend limita `_page_size_arg` a 100. Divergência confirmada.

Resposta:

```json
{
  "code": "finance_journey_grid_ok",
  "contexto": {},
  "indicadores": {},
  "linhas": [],
  "produtividade": [],
  "permissoes": {},
  "status_competencia": "aberta",
  "pagination": {},
  "filters": {}
}
```

Validações/erros: competência inválida (`finance_invalid_competence` na rota ou `finance_journey_invalid_competencia` na aplicação), permissão.

### `POST /api/v1/financeiro/lancamentos-jornada`

Finalidade: criar linha/missão.

Payload mínimo funcional:

```json
{
  "competencia": "2026-04",
  "data": "2026-04-04",
  "data_missao": "2026-04-04",
  "data_final": "2026-04-04",
  "tripulante_id": 7,
  "funcao": "comandante",
  "comandante_tripulante_id": 7,
  "copiloto_tripulante_id": 8,
  "aeronave_id": 12,
  "categoria_financeira_aeronave": "categoria a",
  "tipo_tripulacao_jornada": "simples",
  "hora_apresentacao": "06:15",
  "hora_abandono": "19:30",
  "pos_exec_min": 0,
  "quantidade_pernoites": 0,
  "participantes": [
    {"tripulante_id": 7, "funcao": "comandante", "funcao_missao": "comandante", "cobertura_base": false},
    {"tripulante_id": 8, "funcao": "copiloto", "funcao_missao": "copiloto", "cobertura_base": false}
  ]
}
```

Resposta:

```json
{
  "code": "finance_journey_line_created",
  "linha": {},
  "mission": {},
  "recalculation": {}
}
```

Erros principais: campos obrigatórios, categoria ausente/inválida, tripulante/aeronave inválidos, tripulação inválida, competência fechada, duplicidade de missão.

### `PATCH /api/v1/financeiro/lancamentos-jornada/{id}`

Finalidade: atualizar linha/missão.

Payload: mesmos campos da criação, parciais são mesclados com existente. Não enviar troca de `tripulante_id`/`funcao`; se enviar diferente, bloqueia.

Resposta: `code: finance_journey_line_updated`, `linha`, `mission`, `recalculation`.

### `DELETE /api/v1/financeiro/lancamentos-jornada/{id}`

Finalidade: exclusão segura/cancelamento.

Payload:

```json
{"motivo": "Correção operacional solicitada pelo usuário"}
```

Resposta:

```json
{
  "code": "finance_journey_line_cancelled",
  "linha": {},
  "mission": {},
  "mission_id": 123,
  "competencia": "2026-04",
  "recalculation": {},
  "action": "cancelled"
}
```

### `POST /api/v1/financeiro/lancamentos-jornada/preview`

Finalidade: simular cálculo sem persistir.

Payload: igual ao create/update.

Respostas:

- Dados insuficientes: `status: pendente_dados`, `pendencias`.
- Dados suficientes: preview retornado por `preview_missao_operacional`.

Não há evento de auditoria declarado para preview.

### `POST /api/v1/financeiro/lancamentos-jornada/{id}/recalcular`

Finalidade: recalcular missão/linha.

Payload: rota ignora corpo.

Resposta: `code: finance_journey_line_recalculated`, `linha`, `recalculation`.

### `POST /api/v1/financeiro/lancamentos-jornada/recalcular-grade`

Finalidade: recalcular missões da competência e produtividade.

Payload:

```json
{
  "competencia": "2026-04",
  "funcao": "comandante",
  "tripulante_id": 7
}
```

Resposta: grade completa recalculada.

### `GET /api/v1/financeiro/lancamentos-jornada.pdf`

Finalidade: exportar PDF da grade.

Query: `competencia` obrigatório; `funcao`, `tripulante_id`, `status` opcionais.

Resposta: `application/pdf`, filename `lancamentos-jornada-{competencia}{sufixos}.pdf`.

Bloqueio: se houver linhas horárias não persistidas antes da exportação, retorna conflito `finance_hourly_unpersisted_lines`.

## 9. Comportamento da interface

### 9.1. Layout

- Hero com título, descrição, nota de fonte única e botões de relatórios/exportação.
- Filtros em painel: competência, função, tripulante, gerar grade, limpar.
- Contexto mensal com cards: competência, função operacional, tripulantes, resultado atual.
- Indicadores financeiros: total geral, linhas, hora reduzida, exceções, alertas descanso, domingos, feriados, valor normal.
- Fluxo operacional visual de 4 passos.
- Painel opcional de insights/relatórios.
- Grade principal com 30 colunas.

### 9.2. Campos visíveis

Colunas da grade:

`#`, Data inicial, Data final, Comandante, Segundo tripulante, 3º tripulante, Tripulante da linha, Função da linha, Aeronave, Rel. voo, N. DB, Contratante, Trecho, Pernoites, Cobertura, Cond. especial, Regime jornada, Apresentação, Abandono, Pós exec. min, Justif., Obs, Tipo, Diurna, Noturna, Pré calc min, Pós calc, Total, Status, Ações.

### 9.3. Campos editáveis

Na linha editável:

- Inputs date: Data inicial, Data final.
- Selects: comandante, segundo tripulante, terceiro tripulante, função do terceiro, aeronave.
- Text inputs: Rel. voo, N. DB, Contratante, Trecho, Cond. especial, Justif., Obs, Tipo.
- Number inputs: Pernoites, Pós exec. min.
- Radio/segmento: Regime jornada.
- Time inputs: Apresentação, Abandono.
- Checkboxes: cobertura por participante.

### 9.4. Campos automáticos

- Tripulante da linha.
- Função da linha.
- Categoria/tipo quando aeronave é selecionada.
- `houve_pernoite`.
- `cobertura_base` agregada.
- Diurna, Noturna, Pré calc, Pós calc, Total, Status.
- Preview.

### 9.5. Estados de loading

- "Carregando grade".
- "Gerando..." no filtro.
- "Salvando...", "Excluindo...", "Recalculando...", "Exportando..." nos botões.
- "Calculando..." no preview.
- Painéis de relatório possuem estados de exportação/carregamento.

### 9.6. Estados de erro

- Grade: "Não foi possível gerar a grade" com botão tentar novamente.
- Linha: feedback inline em `role=alert`.
- Preview: pill vermelho ou amarelo com mensagem.
- Exportação PDF: valida tipo de conteúdo e integridade PDF.
- Permissão: estado "Sem permissão financeira" ou warning.

### 9.7. Estados vazios

- Inicial: "Nenhuma grade gerada ainda".
- Grade vazia: "Grade vazia".
- Tabela sem linhas: "Nenhum lançamento encontrado".
- Extrato sem lançamentos.
- Produtividade sem consolidado.

### 9.8. Comportamento responsivo

- Acima de 1500px: indicadores em 8 colunas.
- Até 1500px: indicadores em 4 colunas.
- Até 1400px: hero vira uma coluna.
- Até 1180px: filtros/formulários viram uma coluna; contexto/mini-grid/fluxo em 2 colunas.
- Até 820px: seção head vira grid; botões flexíveis.
- Até 520px: cards/painéis reduzem padding/raio; indicadores/contexto em uma coluna; ações viram grid; hint de rolagem horizontal aparece.
- Até 380px: ações do hero em uma coluna.
- A tabela não vira cards; permanece horizontalmente rolável.

### 9.9. Mensagens ao usuário

Mensagens identificadas:

- "Linha de jornada criada no backend."
- "Linha de jornada salva no backend."
- "Cálculo vigente atualizado pelo backend."
- "Produtividade da competência recalculada."
- "Produtividade pendente: ..."
- "Recálculo pendente: ..."
- "Salve ou descarte a linha em edição antes de excluir um lançamento."
- "Exclusão segura indisponível para esta linha..."
- "Lançamento excluído com cancelamento seguro da missão vinculada..."
- "Grade enviada para recálculo da competência pelo backend."
- "PDF do fechamento validado e download iniciado."
- "Preencha data, aeronave e tripulação."
- "Faltam: data/aeronave/tipo/categoria/tripulante/função."
- "Informe o comandante da missão."
- "Informe o segundo tripulante ou o terceiro tripulante da missão."
- "Comandante e segundo tripulante não podem ser o mesmo tripulante."
- "O terceiro tripulante deve ser diferente do comandante e do segundo tripulante."

## 10. Auditoria, logs e rastreabilidade

### 10.1. Eventos registrados

Catálogo em `financeiro_audit_events.py`:

- `finance.journey_grid.generated`
- `finance.journey_line.created`
- `finance.journey_line.updated`
- `finance.journey_line.cancelled`
- `finance.journey_line.deleted` (catalogado, mas fluxo Jornada usa cancelamento)
- `finance.journey_line.recalculated`
- `finance.journey_grid.recalculated`
- `finance.journey_grid.exported`
- `finance.extract.period.generated`
- `finance.productivity.consolidated.generated`
- `finance.report.individual.generated`
- `finance.export.generated`

Eventos correlatos:

- `finance.mission.created/updated/cancelled/recalculated`.
- `finance.calculation.updated/superseded`.
- `finance.hourly_bonus.calculated`.
- `finance.productivity.calculated`.
- `finance.period.recalculated`.

### 10.2. Alterações rastreadas

Para linha de jornada:

- `competencia`
- `linha_id`
- `mission_id`
- `before`
- `after`
- `reason` quando aplicável
- filtros/contagem em grade/exportação

### 10.3. Memória de cálculo

Horária:

- `memoria_calculo` registra inputs, parâmetros, fatias, passos, avisos e versão.
- `parametros_usados` registra parâmetros usados.
- `calculation_version` esperado: `finance-hourly-v1`.

Produtividade:

- `memoria_calculo` registra contagens, flags cadastrais, férias, fórmulas e avisos.
- `calculation_version` esperado: `finance-productivity-v1`.

### 10.4. Evidências para conferência

Para conferir uma linha:

- Missão (`financeiro_missoes_operacionais`).
- Participante (`financeiro_missao_tripulantes`).
- Cálculo horário vigente.
- Cálculo de produtividade vigente da competência.
- Parâmetros usados em JSON.
- Eventos de auditoria por `linha_id`/`mission_id`.
- Status de competência.
- PDF/exportação gerado, se houver.

### 10.5. Lacunas de auditoria

- Regime usado no cálculo fica em campo e memória, mas não há uma coluna dedicada em `financeiro_calculos_horarios` para `tipo_tripulacao_jornada`; serializadores tentam extrair da missão/memória.
- A tabela regulamentar aplicada pode ser hardcoded quando a busca em `produtividade_parametros` falha.
- Preview não gera auditoria.
- Catálogo usa `finance:missions:cancel` para `finance.journey_line.cancelled`, enquanto permissão real da rota é `finance:missions:delete`. Divergência a confirmar/avaliar.

## 11. Relatórios, PDFs e exportações

### 11.1. Campos exibidos

PDF da grade de Jornada inclui contexto, filtros, indicadores e linhas com dados como data, tripulante, função, aeronave, relatório de voo, trecho, horários, minutos e valores.

Relatórios individuais leem cálculos persistidos vigentes; não recalculam missão no momento do PDF.

Extrato por período exibe linhas horárias/produtividade, subtotais e alertas.

Horas totais voadas consolidam por função/competência usando linhas de Jornada e cálculos horários vigentes.

### 11.2. Agrupamentos

- Grade: ordenada por data, missão, função efetiva e linha.
- Produtividade consolidada: por tripulante e por função.
- Horas totais voadas: por tripulante/função.
- Relatórios individuais: por tripulante/função/tipo.

### 11.3. Totais

- Grade: `total_geral`, horário, produtividade, hora reduzida, exceções.
- Produtividade: `produtividade_calculada`, `garantia_minima`, `total_devido`, componentes.
- Horária: soma de adicionais e total por cálculo vigente.

### 11.4. Fórmulas

As fórmulas vêm dos motores descritos na seção 6 e das memórias persistidas.

### 11.5. Filtros

- Competência.
- Função.
- Tripulante.
- Status.
- Tipo do extrato (`horaria`, `produtividade`, `ambos`).
- Data inicial/final no extrato.

### 11.6. Divergências possíveis

- Frontend solicita até 500 linhas, backend limita 100.
- Relatórios usam apenas persistidos; preview disponível na grade pode não aparecer nos relatórios.
- Cálculos pendentes/obsoletos/cancelados são excluídos dos totais ativos.
- Função efetiva pode divergir da função de missão quando `tripulantes.funcao_operacional` está preenchida.

## 12. Dados legados e compatibilidade

### 12.1. Campos antigos

- Rotas legadas de bonificações apontam para Jornada.
- `chamado` é exibido como `numero_db`.
- `cavok_numero_voo` é exibido como `relatorio_voo`.
- `observacoes` convive com `observacao`.
- `minutos_noturnos` convive com `minutos_noturnos_reais`.

### 12.2. Defaults

- `tipo_tripulacao_jornada`: `simples`.
- `pos_exec_min`: `0`.
- `quantidade_pernoites`: `0`.
- `houve_pernoite`: `false`.
- `cobertura_base`: `false`.
- Status da missão criada pela Jornada: `ativa`.

### 12.3. Fallbacks

- `data_final` ausente -> `data_missao`.
- Categoria `vd/vn/normal` -> categoria do equipamento se houver; senão `nao_aplicavel`.
- `minutos_noturnos_reais` ausente -> `minutos_noturnos`.
- Cobertura individual ausente -> cobertura da missão.
- Tabela regulamentar ausente -> tabela padrão hardcoded.

### 12.4. Inconsistências conhecidas

- Nome do arquivo frontend é `bonificacoes-page.js`, não `lancamentos-jornada-page.js`.
- `finance.journey_line.cancelled` no catálogo declara permissão `finance:missions:cancel`, mas a rota usa `finance:missions:delete`.
- `POST /{id}/recalcular` no contrato declara payload mínimo `motivo`, mas a rota ignora o corpo.
- Frontend `page_size=500` vs backend máximo 100.

### 12.5. Riscos de migração

- Regime de jornada defaultado para `simples` pode alterar expectativa se dados antigos deveriam ser compostos/revezamento.
- Função efetiva baseada no cadastro do tripulante pode alterar cálculo histórico se `funcao_operacional` mudar.
- Tabela regulamentar hardcoded pode divergir de tabela oficial se o cadastro esperado não existir.
- Linhas salvas sem horário têm cálculo zero `calculado`; replicação deve preservar esse comportamento.

## 13. Edge cases

- Virada de dia: abandono <= apresentação soma 1 dia.
- `data_final > data_missao` com abandono sem data explícita usa data final.
- Horário em branco: salva e persiste cálculo zero com warning.
- Data final anterior à inicial: erro de validação.
- Data inicial fora da competência: erro.
- Missão sem aeronave: bloqueada pela Jornada.
- Missão sem tripulante: bloqueada.
- Tripulante inativo: bloqueado.
- Aeronave inativa: bloqueada.
- Pernoite nulo: normaliza para 0.
- Cobertura nula: normaliza false/fallback.
- Cobertura com pernoite 0: não conta.
- Regime ausente: `simples`.
- Regime inválido: erro.
- Valor calculado negativo: motores usam máximos e validações; jornada total <=0 gera erro no motor.
- Duplicidade: missão duplicada se mesma combinação `cavok_numero_voo`, `contratante`, `chamado` em missão ativa/não deletada; se os três vazios, não verifica duplicidade.
- Edição após fechamento: bloqueada.
- Recalculo após alteração de regra/parâmetro: recálculo usa parâmetros vigentes e pode superseder cálculos duplicados.
- Cálculo horário duplicado vigente: recálculo marca duplicados como obsoletos antes de salvar vigente.
- Missão cancelada: não entra na listagem padrão; recálculo de linha cancelada bloqueia.
- Terceiro sem função ou função sem terceiro: erro.
- Terceiro igual a comandante/copiloto: erro.
- Função operacional do cadastro divergente da missão: query usa cadastro como função efetiva.
- Feriado no meio de jornada multi-dia: somente o dia do feriado entra como especial.
- Domingo->segunda: domingo especial, segunda normal.
- SDEA/instrutor/checador fora de vigência: produtividade emite warnings e pode não aplicar adicional.
- Parâmetro `BRL` legado ou não elegível: motor bloqueia por governança.
- PDF incompleto/sem assinatura: erro de validação.

## 14. Lacunas e pontos a confirmar

- Estado real das tabelas em produção, índices adicionais e possíveis constraints fora do schema versionado.
- Existência/uso real de `produtividade_parametros` para tabela regulamentar de jornada.
- Valores oficiais dos parâmetros financeiros por função e vigência.
- Política operacional para escolher `simples`, `composta` ou `revezamento`; código não infere.
- Se a função efetiva deve realmente priorizar `tripulantes.funcao_operacional` sobre função da missão.
- Se `finance:missions:cancel` no catálogo é erro ou permissão planejada.
- Motivo gerado pela UI em exclusão: documentar função exata `jornadaDeleteReason` se for necessário reproduzir texto literal.
- Testes visuais/mobile em navegador real não foram executados nesta análise.
- Mensagens do `domain_error_payload` dependem do handler global, não detalhado aqui.

## 15. Guia para replicação por outro desenvolvedor

1. Banco:
   - Criar as quatro tabelas principais com constraints e índices descritos.
   - Criar tabelas dependentes ou integrações com tripulantes, equipamentos, competências, parâmetros e feriados.
   - Garantir índice único parcial de cálculo horário vigente.
   - Migrar dados legados: `data_final`, `pos_exec_min`, terceiro tripulante, cobertura, `tipo_tripulacao_jornada`, `minutos_noturnos_reais`.

2. Backend:
   - Implementar camada de missão operacional.
   - Implementar facade de Jornada que transforma payload da linha em missão + participantes.
   - Manter `linha_id = financeiro_missao_tripulantes.id`.
   - Implementar validações de competência, tripulantes, aeronave, categoria, tripulação e troca de crew.

3. Contratos:
   - Reproduzir endpoints da seção 8.
   - Manter payloads alias (`data`/`data_missao`, `relatorio_voo`/`cavok_numero_voo`, `numero_db`/`chamado`, `observacao`/`observacoes`).
   - Retornar `linha`, `mission`, `recalculation`, `contexto`, `indicadores`, `produtividade`, `permissoes`, `status_competencia`.

4. Motor de cálculo:
   - Implementar motor horário puro com `finance-hourly-v1`.
   - Implementar tabela regulamentar por regime e interpolação.
   - Implementar fatiamento diário, domingo/feriado, hora reduzida, pré e pós.
   - Implementar cálculo zero para horários ausentes no fluxo de missão/Jornada.
   - Implementar motor de produtividade com `finance-productivity-v1`.

5. Frontend:
   - Criar rota `#/financeiro/lancamentos-jornada`.
   - Construir filtros, cards, painéis e grade de 30 colunas.
   - Derivar tripulante/função da linha.
   - Implementar preview com debounce de 520 ms.
   - Bloquear ações por permissão e competência fechada.

6. Relatórios:
   - PDF da grade com validação de integridade.
   - Relatório individual horária/produtividade.
   - Relatório geral de horas.
   - Relatório geral de produtividade.
   - Extrato por período, máximo 92 dias.

7. Testes:
   - Unitários dos motores de cálculo.
   - Unitários de aplicação Jornada.
   - Contratos HTTP.
   - Testes de frontend/arquitetura para rota, campos, permissões e payloads.
   - Casos de borda da seção 13.

8. Auditoria:
   - Registrar eventos da seção 10.
   - Persistir before/after em criação/edição/cancelamento/recalculo.
   - Persistir memória de cálculo e parâmetros usados.

## 16. Critérios de aceite para módulo replicado

- A grade lista as mesmas linhas para a mesma competência/filtros.
- `linha_id` corresponde ao participante da missão, não a uma tabela nova.
- Criar linha gera missão, participantes, cálculo horário e tentativa de produtividade.
- Editar não permite trocar tripulante/função da linha.
- Excluir cancela missão com motivo e recalcula produtividade.
- Competência fechada bloqueia mutações e permite leitura/exportação.
- Jornada sem horários salva e produz cálculo zero com warning.
- Regimes `simples`, `composta`, `revezamento` geram os mesmos limites de jornada.
- Fatiamento de domingo/feriado e hora reduzida bate com testes existentes.
- Pernoite comum conta somente a partir do segundo pernoite sem cobertura.
- Cobertura de base e Palmas/turbohélice impactam produtividade.
- PDFs só são baixados se forem `application/pdf` válidos e completos.
- Eventos de auditoria são emitidos com `linha_id`, `mission_id`, competência e before/after quando exigidos.
- Dados legados com regime ausente assumem `simples`.
- Frontend exibe os 30 campos da grade e mantém tripulante/função derivados.
- Contratos HTTP retornam os mesmos códigos, mensagens e formatos principais.

## 17. Checklist final de completude

- [x] Campos mínimos e campos exibidos mapeados.
- [x] Tabelas, colunas, constraints e índices principais mapeados.
- [x] Regras de criação, edição, exclusão e recálculo mapeadas.
- [x] Regras de competência/fechamento mapeadas.
- [x] Regras de tripulação, terceiro tripulante e função efetiva mapeadas.
- [x] Regras de aeronave/categoria mapeadas.
- [x] Regime de jornada e tabela regulamentar mapeados.
- [x] Cálculos horários, pré, pós, diurna, noturna e hora reduzida mapeados.
- [x] Produtividade, pernoite, cobertura e condição especial mapeados.
- [x] API e payloads principais documentados.
- [x] Comportamento de UI, loading, erro, vazio e responsivo documentado.
- [x] Auditoria, memória de cálculo e lacunas documentadas.
- [x] Relatórios/PDFs/exportações documentados.
- [x] Dados legados, defaults e fallbacks documentados.
- [x] Edge cases listados.
- [x] Pontos a confirmar explicitados.
- [x] Guia de replicação e critérios de aceite incluídos.
