(() => {
  "use strict";

  const state = { records: [], currentId: null, view: "overview", toastTimer: null };
  const $ = (selector, root) => (root || document).querySelector(selector);
  const $$ = (selector, root) => Array.from((root || document).querySelectorAll(selector));

  const fieldLabels = {
    age_group: "Age group",
    reason_for_visit: "Reason for visit",
    symptom_duration: "Symptom timeline",
    allergy_status: "Allergies",
    allergy_details: "Allergy and reaction details",
    medication_status: "Current medicines",
    medication_details: "Medicine details",
    antibiotic_status: "Current/recent antibiotics",
    antibiotic_details: "Antibiotic details",
    condition_status: "Ongoing conditions",
    condition_details: "Condition details",
    surgery_status: "Surgery/hospitalization",
    surgery_details: "Procedure details",
    anesthesia_reaction_status: "Anesthesia reactions",
    anesthesia_details: "Anesthesia reaction details",
    dental_history: "Relevant dental history"
  };
  const groups = [
    { title: "Visit overview", keys: ["age_group", "reason_for_visit", "symptom_duration", "dental_history"] },
    { title: "Medicines and allergies", keys: ["allergy_status", "allergy_details", "medication_status", "medication_details", "antibiotic_status", "antibiotic_details"] },
    { title: "Medical and procedural history", keys: ["condition_status", "condition_details", "surgery_status", "surgery_details", "anesthesia_reaction_status", "anesthesia_details"] }
  ];
  const statusLabels = { awaiting_review: "Awaiting review", reviewed: "Reviewed", needs_clarification: "Needs clarification" };
  const answerLabels = { yes: "Yes", no: "No", unsure: "Not sure", under_18: "Under 18", "18_39": "18–39", "40_64": "40–64", "65_plus": "65+", prefer_not_to_say: "Prefer not to say" };

  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, char => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[char]);
  }

  function formatDate(value) {
    if (!value) return "Not recorded";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "Not recorded";
    return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" }).format(date);
  }

  function shortDate(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" }).format(date);
  }

  function initials(label) {
    return String(label || "DP").split(/\s+/).filter(Boolean).slice(0, 2).map(part => part.charAt(0)).join("").toUpperCase();
  }

  function statusClass(status) {
    if (status === "reviewed") return "status-reviewed";
    if (status === "needs_clarification") return "status-clarify";
    return "status-awaiting";
  }

  function statusBadge(status) {
    return '<span class="mini-status ' + statusClass(status) + '">' + esc(statusLabels[status] || status) + "</span>";
  }

  function showToast(message, isError) {
    const toast = $("#toast");
    toast.textContent = message;
    toast.classList.toggle("error", Boolean(isError));
    toast.hidden = false;
    if (state.toastTimer) window.clearTimeout(state.toastTimer);
    state.toastTimer = window.setTimeout(() => { toast.hidden = true; }, 3600);
  }

  async function api(path, options) {
    const response = await fetch(path, Object.assign({ cache: "no-store" }, options || {}));
    let data;
    try { data = await response.json(); }
    catch (_) { data = { error: "The local demo returned an unreadable response." }; }
    if (!response.ok) throw new Error(data.error || "The action could not be completed.");
    return data;
  }

  function switchView(view) {
    state.view = view;
    ["overview", "intake", "records", "detail"].forEach(name => {
      const section = $("#view-" + name);
      if (section) section.hidden = name !== view;
    });
    $$(".nav-item").forEach(button => {
      const active = (view === "detail" ? "records" : view) === button.dataset.view;
      button.classList.toggle("active", active);
      if (active) button.setAttribute("aria-current", "page");
      else button.removeAttribute("aria-current");
    });
    const labels = { overview: "Overview", intake: "New intake", records: "Patient records", detail: "Patient record" };
    $("#breadcrumb-current").textContent = labels[view] || "Overview";
    if (view === "overview") renderOverview();
    if (view === "records") renderRecords();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function recordSummary(record) {
    const a = record.answers || {};
    return String(a.reason_for_visit || "Reason not supplied");
  }

  function renderStats() {
    const records = state.records;
    $("#nav-count").textContent = String(records.length);
    $("#stat-total").textContent = String(records.length);
    $("#stat-awaiting").textContent = String(records.filter(item => item.status === "awaiting_review").length);
    $("#stat-reviewed").textContent = String(records.filter(item => item.status === "reviewed").length);
    $("#stat-clarify").textContent = String(records.filter(item => item.status === "needs_clarification").length);
  }

  function renderRecent() {
    const target = $("#recent-records");
    const records = state.records.slice(0, 4);
    if (!records.length) {
      target.innerHTML = '<div class="empty-state">No demo records yet. Start a fictional intake to see the review workflow.</div>';
      return;
    }
    target.innerHTML = records.map(record =>
      '<div class="recent-row"><div class="record-person"><span class="person-initial">' + esc(initials(record.answers.patient_label)) +
      '</span><span><strong>' + esc(record.answers.patient_label) + '</strong><small>' + esc(shortDate(record.created_at)) + " · " + esc(record.form_version) +
      '</small></span></div>' + statusBadge(record.status) +
      '<button class="row-open" data-open-record="' + esc(record.id) + '" aria-label="Open ' + esc(record.answers.patient_label) + '">›</button></div>'
    ).join("");
  }

  function renderOverview() {
    renderStats();
    renderRecent();
  }

  function renderRecords() {
    const target = $("#records-body");
    const search = ($("#record-search")?.value || "").trim().toLowerCase();
    const status = $("#status-filter")?.value || "all";
    const records = state.records.filter(record => {
      const label = String(record.answers.patient_label || "").toLowerCase();
      const reason = String(record.answers.reason_for_visit || "").toLowerCase();
      return (!search || label.includes(search) || reason.includes(search)) && (status === "all" || record.status === status);
    });
    $("#records-description").textContent = records.length + " matching synthetic record" + (records.length === 1 ? "" : "s");
    $("#records-count").textContent = records.length + " record" + (records.length === 1 ? "" : "s");
    if (!records.length) {
      target.innerHTML = '<tr><td colspan="5" class="empty-state">No records match these filters.</td></tr>';
      return;
    }
    target.innerHTML = records.map(record =>
      "<tr><td><div class=\"patient-cell\"><span class=\"person-initial\">" + esc(initials(record.answers.patient_label)) +
      "</span><span>" + esc(record.answers.patient_label) + "</span></div></td><td><div class=\"table-reason\">" + esc(recordSummary(record)) +
      "</div></td><td><span class=\"table-date\">" + esc(formatDate(record.created_at)) + "</span></td><td>" + statusBadge(record.status) +
      '</td><td><button class="table-open" data-open-record="' + esc(record.id) + '">Review record</button></td></tr>'
    ).join("");
  }

  function detailValue(key, value) {
    if (value == null || String(value).trim() === "") return '<span class="answer-empty">Not provided</span>';
    if (key.endsWith("_status") || key === "age_group") return esc(answerLabels[value] || value);
    return esc(value);
  }

  function buildAnswerGroup(group, answers) {
    const rows = group.keys.map(key =>
      "<div class=\"answer-row\"><dt>" + esc(fieldLabels[key] || key) + "</dt><dd>" + detailValue(key, answers[key]) + "</dd></div>"
    ).join("");
    return '<section class="detail-card"><h2>' + esc(group.title) + '</h2><p class="card-subtitle">Patient-reported information · Original answers preserved</p><dl class="answer-list">' + rows + "</dl></section>";
  }

  function reviewFlags(answers) {
    const candidates = [
      ["allergy_status", "allergy_details", "Allergy history"],
      ["medication_status", "medication_details", "Current medicines"],
      ["antibiotic_status", "antibiotic_details", "Current/recent antibiotics"],
      ["condition_status", "condition_details", "Ongoing conditions"],
      ["surgery_status", "surgery_details", "Surgical history"],
      ["anesthesia_reaction_status", "anesthesia_details", "Anesthesia reactions"]
    ].filter(item => answers[item[0]] === "yes" || answers[item[0]] === "unsure");

    if (!candidates.length) {
      return '<div class="review-flag neutral"><span class="flag-mark">✓</span><div><strong>No affirmative or uncertain responses in these sections</strong><p>The dentist still needs to verify that the submitted history is complete and current.</p></div></div>';
    }
    return candidates.map(item => {
      const answer = answers[item[0]];
      const desc = answer === "unsure" ? "Patient selected “Not sure”. Clarification may be needed." : "Patient selected “Yes”. Confirm details with the patient.";
      return '<div class="review-flag"><span class="flag-mark">!</span><div><strong>' + esc(item[2]) + " · " + esc(answerLabels[answer]) + "</strong><p>" + esc(desc) + "</p>" +
        (answers[item[1]] ? '<p>' + esc(answers[item[1]]) + "</p>" : "") + "</div></div>";
    }).join("");
  }

  function renderReviewHistory(record) {
    const reviews = record.reviews || [];
    if (!reviews.length) return '<div class="empty-state">No review action has been recorded yet.</div>';
    return '<div class="review-history">' + reviews.slice().reverse().map(item =>
      '<div class="review-history-item"><strong>' + esc(item.reviewer) + " · " + esc(statusLabels[item.outcome] || item.outcome) +
      "</strong><small>" + esc(formatDate(item.created_at)) + "</small>" +
      (item.notes ? "<p>" + esc(item.notes) + "</p>" : "") + "</div>"
    ).join("") + "</div>";
  }

  function renderAudit(record) {
    const items = record.audit_events || [];
    if (!items.length) return '<div class="empty-state">No audit events recorded.</div>';
    return '<div class="review-history">' + items.slice().reverse().map(item =>
      '<div class="review-history-item"><strong>' + esc(item.action.replace(/_/g, " ")) + "</strong><small>" + esc(formatDate(item.created_at)) + "</small></div>"
    ).join("") + "</div>";
  }

  function renderDetail(record) {
    const answers = record.answers;
    const content = $("#detail-content");
    content.innerHTML =
      '<div class="detail-heading"><div class="detail-identity"><span class="detail-avatar">' + esc(initials(answers.patient_label)) +
      '</span><div><p class="eyebrow">DENTAL INTAKE / SYNTHETIC RECORD</p><h1>' + esc(answers.patient_label) +
      '</h1><p>Submitted ' + esc(formatDate(record.created_at)) + " · Form " + esc(record.form_version) + '</p></div></div><div>' + statusBadge(record.status) + '</div></div>' +
      '<div class="detail-section-grid"><div class="detail-stack">' + groups.map(group => buildAnswerGroup(group, answers)).join("") +
      '<section class="detail-card"><h2>Review history</h2><p class="card-subtitle">Review outcomes and notes added in this demo.</p>' + renderReviewHistory(record) + '</section>' +
      '<section class="detail-card"><h2>Audit trail</h2><p class="card-subtitle">Recorded actions, not a security certification.</p>' + renderAudit(record) + '</section></div>' +
      '<div class="detail-stack"><section class="detail-card"><h2>Items to confirm</h2><p class="card-subtitle">Administrative review prompts based on the patient's own answers. These are not clinical risk scores.</p><div class="review-flag-list">' + reviewFlags(answers) + '</div></section>' +
      '<section class="detail-card"><h2>Record clinician review</h2><p class="card-subtitle">Demo only. Reviewer labels are not authentication or a real clinical signature.</p>' +
      '<form id="review-form" class="review-form"><label class="field"><span>Demo reviewer label <b>*</b></span><input name="reviewer" required maxlength="80" value="Demo Clinician"></label>' +
      '<label class="field"><span>Review outcome <b>*</b></span><select name="outcome" required><option value="reviewed">Reviewed</option><option value="needs_clarification"' + (record.status === "needs_clarification" ? " selected" : "") + '>Needs clarification</option></select></label>' +
      '<label class="field"><span>Review note</span><textarea name="notes" maxlength="1200" placeholder="Fictional review note only."></textarea></label>' +
      '<button class="button button-primary" type="submit" id="save-review">Save demo review <span>→</span></button><p id="review-error" class="form-error" role="alert" hidden></p></form></section></div></div>';
    const form = $("#review-form");
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const button = $("#save-review");
      const error = $("#review-error");
      error.hidden = true;
      if (!form.reportValidity()) return;
      const payload = Object.fromEntries(new FormData(form).entries());
      button.disabled = true;
      button.textContent = "Saving review…";
      try {
        const updated = await api("/api/intakes/" + encodeURIComponent(record.id) + "/review", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        state.currentId = updated.id;
        await refreshRecords();
        await openRecord(updated.id, false);
        showToast("Demo review saved.", false);
      } catch (err) {
        error.textContent = err.message || "Could not save the demo review.";
        error.hidden = false;
        button.disabled = false;
        button.innerHTML = "Save demo review <span>→</span>";
      }
    });
  }

  async function openRecord(id, notify) {
    try {
      const record = await api("/api/intakes/" + encodeURIComponent(id));
      state.currentId = record.id;
      renderDetail(record);
      switchView("detail");
      if (notify) showToast("Opened synthetic patient record.", false);
    } catch (err) {
      showToast(err.message || "Could not open record.", true);
      switchView("records");
    }
  }

  async function refreshRecords() {
    const data = await api("/api/intakes");
    state.records = Array.isArray(data.items) ? data.items : [];
    renderStats();
    renderRecent();
    if (state.view === "records") renderRecords();
  }

  function renderQuestionField(field) {
    const conditional = Boolean(field.conditional_on);
    const fullWidth = field.full_width !== false;
    const className = "field" + (fullWidth ? " full-field" : "") + (conditional ? " conditional-field" : "");
    const conditionalAttrs = conditional
      ? ' data-for="' + esc(field.conditional_on) + '" hidden'
      : "";
    const requiredMark = field.required ? " <b>*</b>" : "";
    const help = field.help_text ? '<small>' + esc(field.help_text) + "</small>" : "";
    const maxLength = field.max_length ? ' maxlength="' + Number(field.max_length) + '"' : "";
    const placeholder = field.placeholder ? ' placeholder="' + esc(field.placeholder) + '"' : "";

    if (field.type === "choice") {
      const options = (field.options || []).map(option =>
        '<label><input type="radio" name="' + esc(field.id) + '" value="' + esc(option.value) + '"' +
        (field.required ? " required" : "") + '><span>' + esc(option.label) + "</span></label>"
      ).join("");
      return '<fieldset class="field full-field status-fieldset"><legend>' + esc(field.label) +
        requiredMark + '</legend><div class="radio-row">' + options + "</div></fieldset>";
    }

    let control = "";
    if (field.type === "textarea") {
      control = '<textarea name="' + esc(field.id) + '" rows="' + Number(field.rows || 2) + '"' +
        maxLength + placeholder + (field.required ? " required" : "") + (conditional ? " disabled" : "") + "></textarea>";
    } else if (field.type === "select") {
      const choices = (field.options || []).map(option =>
        '<option value="' + esc(option.value) + '">' + esc(option.label) + "</option>"
      ).join("");
      control = '<select name="' + esc(field.id) + '"' + (field.required ? " required" : "") +
        '><option value="">Choose an option</option>' + choices + "</select>";
    } else {
      control = '<input type="text" name="' + esc(field.id) + '"' + maxLength + placeholder +
        (field.required ? " required" : "") + ' autocomplete="off">';
    }

    const star = conditional
      ? ' <b class="conditional-star" style="display:none">*</b>'
      : requiredMark;
    return '<label class="' + className + '"' + conditionalAttrs + '><span>' + esc(field.label) +
      star + "</span>" + control + help + "</label>";
  }

  function renderQuestionnaire(schema) {
    $("#form-step-label").textContent = schema.approval_status === "draft_requires_dentist_approval"
      ? "DRAFT QUESTIONNAIRE"
      : "PATIENT FORM";
    $("#questionnaire-title").textContent = schema.title || "Dental history";
    $("#questionnaire-description").textContent = "Form version " + (schema.version || "unknown") +
      " · Choose “Not sure” when you don't know an answer.";
    const container = $("#questionnaire-container");
    const sections = Array.isArray(schema.sections) ? schema.sections : [];
    container.innerHTML = sections.map(section => {
      const fields = (section.fields || []).map(renderQuestionField).join("");
      return '<div class="form-section"><div class="form-section-heading"><span class="section-number">' +
        esc(section.number || "") + "</span><div><h3>" + esc(section.title || "") +
        "</h3><p>" + esc(section.description || "") + '</p></div></div><div class="field-grid">' +
        fields + "</div></div>";
    }).join("");
    const notice = $("#questionnaire-status");
    notice.textContent = schema.notice || "Review this draft with a qualified dentist before clinical use.";
    notice.hidden = false;
  }

  function syncConditionalFields() {
    $$(".conditional-field").forEach(wrapper => {
      const fieldName = wrapper.dataset.for;
      const chosen = $('input[name="' + fieldName + '"]:checked');
      const active = Boolean(chosen && chosen.value === "yes");
      const textarea = $("textarea", wrapper);
      wrapper.hidden = !active;
      if (textarea) {
        textarea.required = active;
        textarea.disabled = !active;
        wrapper.classList.toggle("is-active", active);
        if (!active) textarea.value = "";
      }
    });
  }

  function initIntakeForm() {
    const form = $("#intake-form");
    $$('input[type="radio"]', form).forEach(input => input.addEventListener("change", syncConditionalFields));
    syncConditionalFields();
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const error = $("#form-error");
      const submit = $("#submit-intake");
      error.hidden = true;
      if (!form.reportValidity()) {
        error.textContent = "Please complete the required fields. If you do not know an answer, choose “Not sure”.";
        error.hidden = false;
        return;
      }
      const payload = Object.fromEntries(new FormData(form).entries());
      submit.disabled = true;
      submit.textContent = "Saving demo history…";
      try {
        const created = await api("/api/intakes", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        await refreshRecords();
        form.reset();
        form.elements.patient_label.value = "Demo Patient Casey";
        form.elements.age_group.value = "40_64";
        form.elements.reason_for_visit.value = "Routine check-up. Fictional example only.";
        syncConditionalFields();
        await openRecord(created.id, false);
        showToast("Synthetic intake saved for dentist review.", false);
      } catch (err) {
        error.textContent = err.message || "Could not save this demo intake.";
        error.hidden = false;
        submit.disabled = false;
        submit.innerHTML = 'Submit demo history <span>→</span>';
      } finally {
        submit.disabled = false;
        submit.innerHTML = 'Submit demo history <span>→</span>';
      }
    });
  }

  document.addEventListener("click", event => {
    const viewButton = event.target.closest("[data-view]");
    if (viewButton) {
      switchView(viewButton.dataset.view);
      return;
    }
    const openButton = event.target.closest("[data-open-record]");
    if (openButton) {
      openRecord(openButton.dataset.openRecord, true);
      return;
    }
  });

  $("#back-to-records").addEventListener("click", () => switchView("records"));
  $("#record-search").addEventListener("input", renderRecords);
  $("#status-filter").addEventListener("change", renderRecords);

  function initImages() {
    $("img").forEach(img => {
      img.addEventListener("error", () => {
        img.classList.add("is-hidden");
        if (img.classList.contains("mia-hero-image")) {
          const fallback = $("#mia-hero-fallback");
          if (fallback) fallback.classList.add("is-visible");
        }
        const avatarFallback = img.parentElement ? $(".avatar-fallback", img.parentElement) : null;
        if (avatarFallback) avatarFallback.classList.add("is-visible");
      });
    });
  }

  async function init() {
    try {
      const health = await api("/api/health");
      if (health.mode !== "synthetic-demo-only" || health.real_patient_data_allowed !== false) {
        throw new Error("The demo safety configuration is not correct.");
      }
      const questionnaire = await api("/api/questionnaire");
      if (!questionnaire || !Array.isArray(questionnaire.sections)) {
        throw new Error("The question bank is unavailable.");
      }
      renderQuestionnaire(questionnaire);
      initIntakeForm();
      syncConditionalFields();
      await refreshRecords();
    } catch (err) {
      showToast("Could not initialize the local demo: " + (err.message || "unknown error"), true);
    }
  }

  initImages();
  init();
})();