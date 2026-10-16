import {
  api,
  buildErrorMessage,
  capabilitySet,
  confirmAction,
  escapeAttr,
  escapeHtml,
  formatDateBr,
  formatFileSize,
  renderInlineFeedback,
  showFlash,
  trainingStatusClass,
  withActionBusy,
} from "../../lib.js";
import { renderShell } from "../../shell.js";
import { renderTrainingAttachmentSection } from "./attachments.js";
import {
  buildDuePreview,
  renderHoursReference,
} from "./program-helpers.js";
import { wireCriticalFormDraftProtection } from "../../shared/forms/draft-protection.js";

function buildRecordDueLabel(record, periodicidadeMeses = record?.periodicidade_meses) {
  const dueDate = String(record?.data_vencimento || "").trim();
  if (dueDate) return formatDateBr(dueDate);
  if (!Number(periodicidadeMeses || 0)) return "Sem validade";
  return "-";
}

function buildRecordSegmentOptions(templateSegments, record) {
  const safeTemplateSegments = Array.isArray(templateSegments) ? templateSegments : [];
  const segmentId = record?.segmento_teorico_id;
  if (!segmentId || safeTemplateSegments.some((item) => String(item.id) === String(segmentId))) {
    return safeTemplateSegments;
  }
  return [
    {
      id: segmentId,
      nome_segmento: record.segmento_nome || record.nome_segmento || "Segmento vinculado ao registro",
      modelo_segmento: record.modelo_segmento || "Atual",
      periodicidade_meses: Number(record.periodicidade_meses || 0),
      registro_atual: true,
    },
    ...safeTemplateSegments,
  ];
}

function buildRecordAircraftOptions(modelosAeronave, recordAircraftModel) {
  const safeOptions = Array.isArray(modelosAeronave) ? modelosAeronave : [];
  const aircraftModel = String(recordAircraftModel || "").trim();
  if (!aircraftModel || safeOptions.some((item) => String(item.aeronave_modelo) === aircraftModel)) {
    return safeOptions;
  }
  return [
    {
      aeronave_modelo: aircraftModel,
      registro_atual: true,
    },
    ...safeOptions,
  ];
}

async function renderTrainingProgramRecordPage(treinamentoId = null) {
  if (!treinamentoId) {
    window.location.hash = "#/treinamentos";
    return;
  }
  try {
    const capabilities = capabilitySet();
    const [detailResponse, optionsResponse] = await Promise.all([
      api(`/api/v1/treinamentos-tripulantes/${treinamentoId}`),
      api("/api/v1/treinamentos-tripulantes/options"),
    ]);
    const record = detailResponse.data?.item;
    const optionsPayload = optionsResponse.data?.options || {};
    const options = {
      tripulantes: Array.isArray(optionsPayload.tripulantes) ? optionsPayload.tripulantes : [],
      tipos_treinamento: Array.isArray(optionsPayload.tipos_treinamento) ? optionsPayload.tipos_treinamento : [],
      modelos_aeronave: Array.isArray(optionsPayload.modelos_aeronave) ? optionsPayload.modelos_aeronave : [],
    };
    if (!record) {
      throw new Error("Registro de treinamento nÃ£o encontrado.");
    }
    const recordAircraftModel = String(record.aeronave_modelo_snapshot || record.aeronave_modelo || "");
    const templateResponse = await api(
      `/api/v1/treinamentos-tripulantes/template?${new URLSearchParams({
        tipo_treinamento_id: String(record.tipo_treinamento_id),
        aeronave_modelo: recordAircraftModel,
      }).toString()}`,
    );
    const template = templateResponse.data.template;
    const segmentOptions = buildRecordSegmentOptions(template?.segmentos, record);
    const aircraftOptions = buildRecordAircraftOptions(options.modelos_aeronave, recordAircraftModel);
    const duePreview = { label: buildRecordDueLabel(record) };

    renderShell(
      `
        <div class="training-record-detail-page-shell priority-page-surface ui-page-shell ui-stack">
        <div class="page-header entity-detail-header priority-page-header ui-page-header ui-surface">
          <div>
            <h1>Editar treinamento por segmento</h1>
            <p class="page-subtitle">Registro individual criado a partir da selecao de segmentos.</p>
            <div class="entity-status-row ui-cluster">
              <span class="status-pill ${trainingStatusClass(record.status_calculado || record.status || "")}">${escapeHtml(record.status_calculado || record.status || "status nÃ£o calculado")}</span>
              <span class="status-pill status-gray">${escapeHtml(record.tipo_treinamento_nome || "Tipo nÃ£o informado")}</span>
              <span class="status-pill status-gray">${(record.attachments || []).length} PDF${(record.attachments || []).length === 1 ? "" : "s"} anexado${(record.attachments || []).length === 1 ? "" : "s"}</span>
            </div>
          </div>
          <div class="page-header-actions">
            <a class="button-link secondary" href="#/treinamentos">Voltar para a lista</a>
          </div>
        </div>

        <section class="panel training-record-form-panel ui-surface ui-stack">
          <div id="training-record-feedback" aria-live="polite"></div>
          <form id="training-program-record-form" class="form-grid entity-form-grid training-record-form ui-form-grid" novalidate>
            <section class="form-section entity-form-section ui-surface ui-stack ui-form-section">
              <div class="form-section-header">
                <h2>Contexto do treinamento</h2>
                <p>Tripulante, tipo e segmento governam vencimento e consistÃªncia do registro.</p>
                <div class="section-feedback ui-field-help" id="trainingContextSectionFeedback" aria-live="polite"></div>
              </div>
              <div class="form-grid form-grid-compact ui-form-grid ui-form-density-compact">
            <label>
              Tripulante
              <select name="tripulante_id" id="trainingRecordTripulante" required aria-describedby="trainingRecordTripulanteFeedback">
                <option value="">Selecione</option>
                ${(options.tripulantes || []).map((item) => `<option value="${item.id}" ${String(record.tripulante_id) === String(item.id) ? "selected" : ""}>${escapeHtml(item.label || item.nome)}</option>`).join("")}
              </select>
              <span class="field-feedback ui-field-help" id="trainingRecordTripulanteFeedback" aria-live="polite"></span>
            </label>
            <label>
              Tipo de treinamento
              <select name="tipo_treinamento_id" id="trainingRecordType" required aria-describedby="trainingRecordTypeFeedback">
                ${(options.tipos_treinamento || [])
                  .map(
                    (item) => `
                      <option value="${item.id}" data-exige-aeronave="${item.exige_aeronave ? 1 : 0}" ${String(record.tipo_treinamento_id) === String(item.id) ? "selected" : ""}>${escapeHtml(item.nome)}</option>
                    `,
                  )
                  .join("")}
              </select>
              <span class="field-feedback ui-field-help" id="trainingRecordTypeFeedback" aria-live="polite"></span>
            </label>
            <label>
              Modelo de aeronave
              <select name="aeronave_modelo" id="trainingRecordAircraft" aria-describedby="trainingRecordAircraftFeedback">
                <option value="">Modelo de aeronave</option>
                ${aircraftOptions.map((item) => `<option value="${escapeAttr(item.aeronave_modelo)}" ${recordAircraftModel === String(item.aeronave_modelo) ? "selected" : ""}>${escapeHtml(item.aeronave_modelo)}${item.registro_atual ? " Â· vinculado ao registro" : ""}</option>`).join("")}
              </select>
              <span class="field-feedback ui-field-help" id="trainingRecordAircraftFeedback" aria-live="polite"></span>
            </label>
            <label>
              Segmento
              <select name="segmento_id" id="trainingRecordSegment" required aria-describedby="trainingRecordSegmentFeedback">
                ${segmentOptions.map((item) => `<option value="${item.id}" data-periodicity="${escapeAttr(item.periodicidade_meses)}" ${String(record.segmento_teorico_id) === String(item.id) ? "selected" : ""}>${escapeHtml(item.nome_segmento)} Â· ${escapeHtml(item.modelo_segmento)}${item.registro_atual ? " Â· vinculado ao registro" : ""}</option>`).join("")}
              </select>
              <span class="field-feedback ui-field-help" id="trainingRecordSegmentFeedback" aria-live="polite"></span>
            </label>
              </div>
            </section>
            <section class="form-section entity-form-section ui-surface ui-stack ui-form-section">
              <div class="form-section-header">
                <h2>Datas e evidÃªncia</h2>
                <p>A realizaÃ§Ã£o recalcula o vencimento previsto e orienta a aÃ§Ã£o operacional.</p>
                <div class="section-feedback ui-field-help" id="trainingDatesSectionFeedback" aria-live="polite"></div>
              </div>
              <div class="form-grid form-grid-compact ui-form-grid ui-form-density-compact">
            <label>Data de realizaÃ§Ã£o<input type="date" name="data_realizacao" id="trainingRecordDate" value="${escapeAttr(record.data_realizacao || "")}" required aria-describedby="trainingRecordDateFeedback"><span class="field-feedback ui-field-help" id="trainingRecordDateFeedback" aria-live="polite"></span></label>
            <label>Data de vencimento<input type="text" id="trainingRecordDuePreview" value="${escapeAttr(duePreview.label)}" readonly><span class="field-help ui-field-help">Calculada a partir da realizaÃ§Ã£o e periodicidade do segmento.</span></label>
            <label class="full-width ui-form-field-long">ObservaÃ§Ã£o<textarea name="observacao" rows="3">${escapeHtml(record.observacao || "")}</textarea></label>
            ${
              record.ctac_required
                ? `
                  <label>Solo horas (CTAC)<input type="number" step="0.1" min="0" name="ctac_solo_horas" inputmode="decimal" value="${escapeAttr(record.ctac_solo_horas ?? "")}"></label>
                  <label>Voo PIC/SIC horas (CTAC)<input type="number" step="0.1" min="0" name="ctac_voo_pic_sic_horas" inputmode="decimal" value="${escapeAttr(record.ctac_voo_pic_sic_horas ?? "")}"></label>
                  <label>Voo CREW horas (CTAC)<input type="number" step="0.1" min="0" name="ctac_voo_crew_horas" inputmode="decimal" value="${escapeAttr(record.ctac_voo_crew_horas ?? "")}"></label>
                `
                : ""
            }
              </div>
            </section>
            <div class="form-actions full-width entity-sticky-actions ui-form-actions ui-form-sticky-actions">
              ${capabilities.has("treinamentos:edit") ? '<button type="submit" id="training-program-record-submit">Salvar alteraÃ§Ãµes</button>' : ""}
              ${capabilities.has("treinamentos:delete") ? '<button type="button" class="button-link secondary" id="training-program-record-delete">Excluir registro</button>' : ""}
            </div>
          </form>
        </section>

        ${renderHoursReference(template)}
        ${renderTrainingAttachmentSection(treinamentoId, record.attachments || [], capabilities)}
        </div>
      `,
      "Editar Treinamento por Segmento",
    );

    const recordFeedback = document.getElementById("training-record-feedback");
    const originalTypeId = String(record.tipo_treinamento_id || "");
    const originalSegmentId = String(record.segmento_teorico_id || "");
    const originalRealizationDate = String(record.data_realizacao || "");
    const originalAircraftModel = recordAircraftModel;
    const attachmentInput = document.getElementById("treinamentoAttachmentInput");
    const attachmentState = document.getElementById("treinamentoAttachmentUploadState");

    function setFieldFeedback(input, message = "", kind = "error") {
      if (!input) return true;
      const feedbackId = input.getAttribute("aria-describedby");
      const feedback = feedbackId ? document.getElementById(feedbackId) : null;
      input.setAttribute("aria-invalid", message && kind === "error" ? "true" : "false");
      if (feedback) {
        feedback.textContent = message;
        feedback.dataset.kind = message ? kind : "";
      }
      return !message || kind !== "error";
    }

    function validateRequiredInput(input, message) {
      return setFieldFeedback(input, String(input?.value || "").trim() ? "" : message);
    }

    function setUploadState(target, message, kind = "") {
      if (!target) return;
      target.textContent = message;
      target.dataset.kind = kind;
    }

    function setSectionFeedback(id, message = "", kind = "error") {
      const target = document.getElementById(id);
      if (!target) return;
      target.textContent = message;
      target.dataset.kind = message ? kind : "";
    }

    function validatePdfFile(file, target) {
      if (!file) {
        setUploadState(target, "Selecione um PDF antes de anexar.", "error");
        return false;
      }
      if (file.type !== "application/pdf" && !String(file.name || "").toLowerCase().endsWith(".pdf")) {
        setUploadState(target, "Arquivo invÃ¡lido. Envie apenas PDF.", "error");
        return false;
      }
      if (file.size > 20 * 1024 * 1024) {
        setUploadState(target, "Arquivo maior que 20 MB. Escolha um PDF menor.", "error");
        return false;
      }
      return true;
    }

    function validateTrainingRecordForm() {
      const contextValidations = [
        validateRequiredInput(document.getElementById("trainingRecordTripulante"), "Selecione o tripulante."),
        validateRequiredInput(document.getElementById("trainingRecordType"), "Selecione o tipo de treinamento."),
        validateRequiredInput(document.getElementById("trainingRecordSegment"), "Selecione o segmento."),
      ];
      const dateValidations = [
        validateRequiredInput(document.getElementById("trainingRecordDate"), "Informe a data de realizaÃ§Ã£o."),
      ];
      const aircraftInput = document.getElementById("trainingRecordAircraft");
      if (aircraftInput?.required) {
        contextValidations.push(validateRequiredInput(aircraftInput, "Selecione o modelo de aeronave."));
      } else {
        setFieldFeedback(aircraftInput, "");
      }
      setSectionFeedback(
        "trainingContextSectionFeedback",
        contextValidations.every(Boolean) ? "" : "Revise o contexto do registro.",
      );
      setSectionFeedback(
        "trainingDatesSectionFeedback",
        dateValidations.every(Boolean) ? "" : "Informe a realizaÃ§Ã£o para recalcular o vencimento.",
      );
      const validations = [...contextValidations, ...dateValidations];
      return validations.every(Boolean);
    }

    function syncRecordHints() {
      const typeSelect = document.getElementById("trainingRecordType");
      const aircraftSelect = document.getElementById("trainingRecordAircraft");
      const segmentSelect = document.getElementById("trainingRecordSegment");
      const dateInput = document.getElementById("trainingRecordDate");
      const dueInput = document.getElementById("trainingRecordDuePreview");
      const submitButton = document.getElementById("training-program-record-submit");
      if (!typeSelect || !aircraftSelect || !segmentSelect || !dateInput || !dueInput) return;
      const typeOption = typeSelect.options[typeSelect.selectedIndex];
      aircraftSelect.required = typeOption?.dataset?.exigeAeronave === "1";
      const templateKeyChanged = String(typeSelect.value || "") !== originalTypeId || String(aircraftSelect.value || "") !== originalAircraftModel;
      segmentSelect.disabled = templateKeyChanged;
      if (submitButton) submitButton.disabled = templateKeyChanged;
      if (templateKeyChanged) {
        setFieldFeedback(segmentSelect, "Recarregue a lista para trocar tipo ou aeronave.", "warning");
        renderInlineFeedback(
          recordFeedback,
          "Para trocar tipo de treinamento ou aeronave, volte para a lista e carregue novamente os segmentos pela seleÃ§Ã£o inicial.",
          "warning",
        );
        return;
      }
      setFieldFeedback(segmentSelect, "");
      renderInlineFeedback(recordFeedback, "");
      const segmentOption = segmentSelect.options[segmentSelect.selectedIndex];
      const recordDatesUnchanged =
        String(dateInput.value || "") === originalRealizationDate && String(segmentSelect.value || "") === originalSegmentId;
      dueInput.value = recordDatesUnchanged
        ? buildRecordDueLabel(record, segmentOption?.dataset?.periodicity || record.periodicidade_meses)
        : buildDuePreview(dateInput.value, segmentOption?.dataset?.periodicity || 0).label;
    }

    document.getElementById("trainingRecordType")?.addEventListener("change", syncRecordHints);
    document.getElementById("trainingRecordAircraft")?.addEventListener("change", syncRecordHints);
    document.getElementById("trainingRecordSegment")?.addEventListener("change", syncRecordHints);
    document.getElementById("trainingRecordDate")?.addEventListener("change", syncRecordHints);
    document.querySelectorAll("#training-program-record-form [required]").forEach((input) => {
      input.addEventListener("blur", () => validateRequiredInput(input, "Campo obrigatÃ³rio."));
      input.addEventListener("change", () => setFieldFeedback(input, ""));
    });
    const trainingDraft = wireCriticalFormDraftProtection({
      form: "training-program-record-form",
      formKey: `treinamento:${treinamentoId}`,
      baselineFields: {
        tripulante_id: record.tripulante_id ?? "",
        segmento_id: record.segmento_teorico_id ?? "",
        data_realizacao: record.data_realizacao || "",
        observacao: record.observacao || "",
        ctac_solo_horas: record.ctac_solo_horas ?? "",
        ctac_voo_pic_sic_horas: record.ctac_voo_pic_sic_horas ?? "",
        ctac_voo_crew_horas: record.ctac_voo_crew_horas ?? "",
      },
      includeFields: [
        "tripulante_id",
        "segmento_id",
        "data_realizacao",
        "observacao",
        "ctac_solo_horas",
        "ctac_voo_pic_sic_horas",
        "ctac_voo_crew_horas",
      ],
      feedbackTarget: recordFeedback,
      restoreMessage: "Rascunho local recuperado. Revise e salve para persistir o treinamento.",
    });
    syncRecordHints();

    document.getElementById("training-program-record-form")?.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!validateTrainingRecordForm()) {
        renderInlineFeedback(recordFeedback, "Revise os campos destacados antes de salvar.", "error");
        document.querySelector("#training-program-record-form [aria-invalid='true']")?.focus();
        return;
      }
      const submitButton = document.getElementById("training-program-record-submit");
      await withActionBusy(submitButton, "Salvando...", async () => {
        try {
          await api(`/api/v1/treinamentos-tripulantes/${treinamentoId}`, {
            method: "PUT",
            json: Object.fromEntries(new FormData(event.currentTarget).entries()),
          });
          trainingDraft?.clear({ reason: "save_success" });
          showFlash("Registro atualizado com sucesso.", "success");
          await renderTrainingProgramRecordPage(treinamentoId);
        } catch (error) {
          renderInlineFeedback(recordFeedback, buildErrorMessage(error), "error");
        }
      });
    });

    document.getElementById("training-program-record-delete")?.addEventListener("click", async () => {
      const deleteButton = document.getElementById("training-program-record-delete");
      if (!confirmAction({
        title: "Excluir este registro de treinamento?",
        subject: `${record.tripulante_nome || "-"} - ${record.tipo_treinamento_nome || "-"} - ${record.segmento_nome || "-"}`,
        consequence: "O registro deixarÃ¡ de contar no histÃ³rico e nos vencimentos do tripulante.",
      })) return;
      await withActionBusy(deleteButton, "Excluindo...", async () => {
        try {
          await api(`/api/v1/treinamentos-tripulantes/${treinamentoId}`, { method: "DELETE" });
          trainingDraft?.clear({ reason: "delete_success" });
          showFlash("Registro removido com sucesso.", "success");
          window.location.hash = "#/treinamentos";
        } catch (error) {
          renderInlineFeedback(recordFeedback, buildErrorMessage(error), "error");
        }
      });
    });

    document.getElementById("treinamento-attachment-form")?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const submitButton = event.currentTarget.querySelector('button[type="submit"]');
      const file = attachmentInput?.files?.[0];
      if (!validatePdfFile(file, attachmentState)) {
        attachmentInput?.focus();
        return;
      }
      setUploadState(attachmentState, `${file.name} Â· ${formatFileSize(file.size)} Â· anexando...`, "busy");
      await withActionBusy(submitButton, "Anexando...", async () => {
        try {
          await api(`/api/v1/treinamentos-tripulantes/${treinamentoId}/attachments`, {
            method: "POST",
            body: new FormData(event.currentTarget),
          });
          showFlash("Anexo enviado com sucesso.", "success");
          await renderTrainingProgramRecordPage(treinamentoId);
        } catch (error) {
          setUploadState(attachmentState, `${file.name} Â· falha ao anexar`, "error");
          renderInlineFeedback(recordFeedback, buildErrorMessage(error), "error");
        }
      });
    });
    attachmentInput?.addEventListener("change", () => {
      const file = attachmentInput.files?.[0];
      if (!file) {
        setUploadState(attachmentState, "Nenhum PDF selecionado.");
        return;
      }
      if (validatePdfFile(file, attachmentState)) {
        setUploadState(attachmentState, `${file.name} Â· ${formatFileSize(file.size)} Â· pronto para anexar`, "ready");
      }
    });

    document.querySelectorAll(".treinamento-attachment-delete").forEach((button) => {
      button.addEventListener("click", async () => {
        if (!confirmAction({
          title: "Excluir este anexo PDF?",
          subject: "Anexo do treinamento selecionado",
          consequence: "O arquivo deixarÃ¡ de ficar disponÃ­vel neste registro de treinamento.",
        })) return;
        await withActionBusy(button, "Excluindo...", async () => {
          try {
            await api(`/api/v1/treinamentos-tripulantes/${treinamentoId}/attachments/${button.dataset.attachmentId}`, { method: "DELETE" });
            showFlash("Anexo removido com sucesso.", "success");
            await renderTrainingProgramRecordPage(treinamentoId);
          } catch (error) {
            renderInlineFeedback(recordFeedback, buildErrorMessage(error), "error");
          }
        });
      });
    });
  } catch (error) {
    showFlash(buildErrorMessage(error), "error");
    renderShell("<section class='panel'><div class='empty'>Falha ao carregar o registro de treinamento.</div></section>", "Editar Treinamento por Segmento");
  }
}

export async function renderTreinamentoFormPage(treinamentoId = null) {
  return renderTrainingProgramRecordPage(treinamentoId);
}

