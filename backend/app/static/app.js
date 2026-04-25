const rootPath = document.body.dataset.rootPath || "";
const currentSiteCode = document.body.dataset.siteCode || "";
const currentSiteName = document.body.dataset.siteName || currentSiteCode;
const currentUsername = document.body.dataset.username || "";
const currentRole = document.body.dataset.role || "";
const apiUrl = (path) => `${rootPath}${path}`;

const photoInput = document.getElementById("photo");
const photoPreview = document.getElementById("photo-preview");
const previewPlaceholder = document.getElementById("preview-placeholder");
const plateInput = document.getElementById("plate-input");
const inspectorInput = document.getElementById("inspector");
const locationInput = document.getElementById("location");
const memoInput = document.getElementById("memo");
const scanBtn = document.getElementById("scan-btn");
const checkBtn = document.getElementById("check-btn");
const saveBtn = document.getElementById("save-btn");
const resetBtn = document.getElementById("reset-btn");
const candidateList = document.getElementById("candidate-list");
const ocrRaw = document.getElementById("ocr-raw");
const verdictCard = document.getElementById("verdict-card");
const verdictTitle = document.getElementById("verdict-title");
const verdictDetail = document.getElementById("verdict-detail");
const verdictMeta = document.getElementById("verdict-meta");
const verdictMatchNav = document.getElementById("verdict-match-nav");
const verdictMatchNote = document.getElementById("verdict-match-note");
const matchPrevBtn = document.getElementById("match-prev-btn");
const matchNextBtn = document.getElementById("match-next-btn");
const matchCounter = document.getElementById("match-counter");
const recentResults = document.getElementById("recent-results");
const searchResults = document.getElementById("search-results");
const registryStatus = document.getElementById("registry-status");
const registryFileInput = document.getElementById("registry-file-input");
const uploadRegistryBtn = document.getElementById("upload-registry-btn");
const registryFileNote = document.getElementById("registry-file-note");
const userList = document.getElementById("user-list");
const userCreateForm = document.getElementById("user-create-form");
const newUserUsernameInput = document.getElementById("new-user-username");
const newUserPasswordInput = document.getElementById("new-user-password");
const newUserRoleInput = document.getElementById("new-user-role");
const userRefreshBtn = document.getElementById("user-refresh-btn");
const siteList = document.getElementById("site-list");
const siteCreateForm = document.getElementById("site-create-form");
const newSiteCodeInput = document.getElementById("new-site-code");
const newSiteNameInput = document.getElementById("new-site-name");
const newSiteAdminUsernameInput = document.getElementById("new-site-admin-username");
const newSiteAdminPasswordInput = document.getElementById("new-site-admin-password");
const siteRefreshBtn = document.getElementById("site-refresh-btn");
const cctvRequestForm = document.getElementById("cctv-request-form");
const cctvPhotoInput = document.getElementById("cctv-photo");
const cctvLocationInput = document.getElementById("cctv-location");
const cctvSearchStartTimeInput = document.getElementById("cctv-search-start-time");
const cctvSearchEndTimeInput = document.getElementById("cctv-search-end-time");
const cctvContentInput = document.getElementById("cctv-content");
const cctvRequestList = document.getElementById("cctv-request-list");
const cctvRefreshBtn = document.getElementById("cctv-refresh-btn");
const geoStatus = document.getElementById("geo-status");
const statusBanner = document.getElementById("status-banner");
const quickMemoButtons = Array.from(document.querySelectorAll(".quick-chip"));
const mobileTabButtons = Array.from(document.querySelectorAll("[data-mobile-tab]"));
const mobileTabPanels = Array.from(document.querySelectorAll("[data-mobile-tab-panel]"));

const USER_ROLE_OPTIONS = [
  { value: "admin", label: "관리자", badgeClass: "badge-role-admin" },
  { value: "director", label: "소장", badgeClass: "badge-role-director" },
  { value: "manager", label: "과장", badgeClass: "badge-role-manager" },
  { value: "section_chief", label: "계장", badgeClass: "badge-role-section-chief" },
  { value: "team_lead", label: "팀장", badgeClass: "badge-role-team-lead" },
  { value: "staff", label: "주임", badgeClass: "badge-role-staff" },
  { value: "guard", label: "경비", badgeClass: "badge-role-guard" },
  { value: "cleaner", label: "미화", badgeClass: "badge-role-cleaner" },
];
const CCTV_ASSIGNMENT_ROLES = new Set(["admin", "director", "manager", "section_chief", "team_lead"]);
const currentCanAssignCctv = CCTV_ASSIGNMENT_ROLES.has(currentRole);
const EXCEL_UPLOAD_SUFFIXES = [".xlsx", ".xlsm"];
const CCTV_STATUS_OPTIONS = [
  { value: "requested", label: "요청", badgeClass: "badge-idle" },
  { value: "assigned", label: "배정", badgeClass: "badge-temp" },
  { value: "in_progress", label: "진행", badgeClass: "badge-temp" },
  { value: "done", label: "완료", badgeClass: "badge-ok" },
  { value: "cancelled", label: "취소", badgeClass: "badge-danger" },
];

let latestRawText = "";
let latestVerdict = null;
let currentGeo = { lat: null, lng: null };
let objectUrl = "";
let latestOcrBestPlate = "";
let latestOcrCandidates = [];
let currentCheckMatches = [];
let currentCheckIndex = 0;
let currentCheckRequestedPlate = "";
let cctvAssignees = [];
let activeMobileTab = "enforce";

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function phoneHref(value) {
  const raw = String(value ?? "").trim();
  if (!raw) return "";
  if (raw.startsWith("+")) {
    const digits = raw.slice(1).replace(/\D/g, "");
    return digits ? `+${digits}` : "";
  }
  return raw.replace(/\D/g, "");
}

function smsBodySeparator() {
  const ua = navigator.userAgent || "";
  const platform = navigator.platform || "";
  const isAppleMobile = /iPad|iPhone|iPod/.test(ua) || (platform === "MacIntel" && navigator.maxTouchPoints > 1);
  return isAppleMobile ? "&" : "?";
}

function buildSmsBody(plateValue = "") {
  const plate = String(plateValue || plateInput?.value || "").trim();
  const location = locationInput?.value.trim();
  const memo = memoInput?.value.trim();
  const lines = ["[주차 안내]"];
  if (plate) lines.push(`차량번호: ${plate}`);
  if (location) lines.push(`위치: ${location}`);
  if (memo) lines.push(`사유: ${memo}`);
  lines.push("차량 이동 또는 확인 부탁드립니다.");
  return lines.join("\n");
}

function smsHref(value, plateValue = "") {
  const recipient = phoneHref(value);
  if (!recipient) return "";
  return `sms:${recipient}${smsBodySeparator()}body=${encodeURIComponent(buildSmsBody(plateValue))}`;
}

function contactActionsMarkup(value, plateValue = "", tone = "") {
  const label = String(value ?? "").trim();
  const href = phoneHref(label);
  if (!href) {
    return escapeHtml(label || "-");
  }
  const toneClass = tone ? ` contact-actions-${tone}` : "";
  return `
    <span class="contact-actions${toneClass}">
      <span class="contact-number">${escapeHtml(label)}</span>
      <span class="contact-action-row">
        <a class="contact-action" href="tel:${escapeHtml(href)}">전화</a>
        <a class="contact-action contact-sms" href="${escapeHtml(smsHref(label, plateValue))}" data-sms-phone="${escapeHtml(label)}" data-sms-plate="${escapeHtml(plateValue || "")}">문자</a>
      </span>
    </span>
  `;
}

function refreshSmsLinks(root = document) {
  root.querySelectorAll("[data-sms-phone]").forEach((link) => {
    const href = smsHref(link.dataset.smsPhone || "", link.dataset.smsPlate || "");
    if (href) {
      link.setAttribute("href", href);
    }
  });
}

function verdictClass(verdict) {
  if (verdict === "OK") return "verdict-ok";
  if (verdict === "TEMP") return "verdict-temp";
  if (verdict === "BLOCKED" || verdict === "EXPIRED" || verdict === "UNREGISTERED") return "verdict-danger";
  return "verdict-idle";
}

function badgeClass(verdict) {
  if (verdict === "OK") return "badge-ok";
  if (verdict === "TEMP") return "badge-temp";
  if (verdict === "BLOCKED" || verdict === "EXPIRED" || verdict === "UNREGISTERED") return "badge-danger";
  return "badge-idle";
}

function userRoleOption(role) {
  return USER_ROLE_OPTIONS.find((item) => item.value === role) || USER_ROLE_OPTIONS[USER_ROLE_OPTIONS.length - 1];
}

function userRoleOptionsMarkup(selectedRole) {
  return USER_ROLE_OPTIONS.map((item) => `<option value="${item.value}" ${item.value === selectedRole ? "selected" : ""}>${item.label}</option>`).join("");
}

function cctvStatusOption(status) {
  return CCTV_STATUS_OPTIONS.find((item) => item.value === status) || CCTV_STATUS_OPTIONS[0];
}

function cctvStatusOptionsMarkup(selectedStatus) {
  return CCTV_STATUS_OPTIONS.map((item) => `<option value="${item.value}" ${item.value === selectedStatus ? "selected" : ""}>${item.label}</option>`).join("");
}

function cctvAssigneeOptionsMarkup(selectedUsername) {
  const options = ['<option value="">담당자 선택</option>'];
  options.push(
    ...cctvAssignees.map((user) => {
      const label = `${user.username} · ${user.role_label || user.role || "-"}`;
      return `<option value="${escapeHtml(user.username)}" ${user.username === selectedUsername ? "selected" : ""}>${escapeHtml(label)}</option>`;
    })
  );
  return options.join("");
}

function cctvWeightOptionsMarkup(selectedWeight) {
  const weight = Number(selectedWeight || 1);
  return [1, 2, 3, 4, 5]
    .map((item) => `<option value="${item}" ${item === weight ? "selected" : ""}>가중치 ${item}</option>`)
    .join("");
}

function setStatus(message, tone = "idle") {
  statusBanner.textContent = message;
  statusBanner.className = `status-banner status-${tone}`;
}

function mobileTabStorageKey() {
  return `parking:${currentSiteCode || "default"}:${currentRole || "role"}:mobile-tab`;
}

function refreshActiveMobileTab(tab) {
  if (tab === "cctv") {
    loadCctvRequests().catch(() => {});
  } else if (tab === "recent") {
    loadRecent().catch(() => {});
  } else if (tab === "admin") {
    loadRegistryStatus().catch(() => {});
    loadUsers().catch(() => {});
    loadSites().catch(() => {});
  }
}

function activateMobileTab(tab, options = {}) {
  const allowedTabs = new Set(mobileTabButtons.map((button) => button.dataset.mobileTab));
  const nextTab = allowedTabs.has(tab) ? tab : "enforce";
  activeMobileTab = nextTab;

  mobileTabPanels.forEach((panel) => {
    panel.classList.toggle("is-mobile-active", panel.dataset.mobileTabPanel === nextTab);
  });
  mobileTabButtons.forEach((button) => {
    const isActive = button.dataset.mobileTab === nextTab;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });

  localStorage.setItem(mobileTabStorageKey(), nextTab);
  document.body.classList.add("mobile-tabs-ready");

  if (options.refresh !== false) {
    refreshActiveMobileTab(nextTab);
  }
  if (options.scroll !== false && window.matchMedia("(max-width: 720px)").matches) {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

function initMobileTabs() {
  if (!mobileTabButtons.length || !mobileTabPanels.length) {
    return;
  }
  const saved = localStorage.getItem(mobileTabStorageKey()) || "enforce";
  activateMobileTab(saved, { refresh: false, scroll: false });
}

function persistField(key, value) {
  localStorage.setItem(`parking:${key}`, value);
}

function hydrateFields() {
  inspectorInput.value = localStorage.getItem("parking:inspector") || "";
  locationInput.value = localStorage.getItem("parking:location") || "";
}

function syncQuickMemoState() {
  const current = memoInput.value.trim();
  quickMemoButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.memo === current);
  });
  refreshSmsLinks();
}

function updatePreview(file) {
  if (objectUrl) {
    URL.revokeObjectURL(objectUrl);
    objectUrl = "";
  }

  if (!file) {
    photoPreview.hidden = true;
    previewPlaceholder.hidden = false;
    photoPreview.removeAttribute("src");
    return;
  }

  objectUrl = URL.createObjectURL(file);
  photoPreview.src = objectUrl;
  photoPreview.hidden = false;
  previewPlaceholder.hidden = true;
}

function renderIdleVerdict() {
  latestVerdict = null;
  latestOcrBestPlate = "";
  latestOcrCandidates = [];
  currentCheckMatches = [];
  currentCheckIndex = 0;
  currentCheckRequestedPlate = "";
  verdictCard.className = "verdict-card verdict-idle";
  verdictCard.querySelector(".verdict-label").textContent = "대기 중";
  verdictTitle.textContent = "차량을 촬영하거나 번호를 입력해 주세요.";
  verdictDetail.textContent = "정상 등록, 임시 등록, 기간 만료, 차단 여부를 즉시 확인합니다.";
  verdictMatchNav.hidden = true;
  verdictMatchNote.hidden = true;
  verdictMatchNote.textContent = "";
  verdictMeta.innerHTML = "";
  saveBtn.textContent = "단속 기록 저장";
}

function toMatchItem(data) {
  return {
    plate: data.plate || "",
    verdict: data.verdict || "UNREGISTERED",
    message: data.message || "미등록 차량",
    unit: data.unit || null,
    owner_name: data.owner_name || null,
    phone: data.phone || null,
    status: data.status || null,
    valid_from: data.valid_from || null,
    valid_to: data.valid_to || null,
  };
}

function renderMatchNavigator(data) {
  const matchCount = Number(data.match_count || currentCheckMatches.length || 0);
  const isSuffix = data.match_mode === "suffix";
  const hasMultiple = isSuffix && matchCount > 1;

  verdictMatchNav.hidden = !hasMultiple;
  verdictMatchNote.hidden = !isSuffix;

  if (hasMultiple) {
    matchCounter.textContent = `${currentCheckIndex + 1} / ${matchCount}`;
    verdictMatchNote.textContent = `뒤 4자리 ${currentCheckRequestedPlate || data.requested_plate || "-"} 일치 차량 ${matchCount}대입니다. 화살표로 순서대로 확인해 주세요.`;
  } else if (isSuffix && matchCount === 1) {
    verdictMatchNote.textContent = `뒤 4자리 ${currentCheckRequestedPlate || data.requested_plate || "-"} 일치 차량 1대를 찾았습니다.`;
  } else if (isSuffix) {
    verdictMatchNote.textContent = `뒤 4자리 ${currentCheckRequestedPlate || data.requested_plate || "-"}와 일치하는 등록차량이 없습니다.`;
  } else {
    verdictMatchNote.textContent = "";
  }

  matchPrevBtn.disabled = !hasMultiple;
  matchNextBtn.disabled = !hasMultiple;
}

function renderVerdict(data) {
  latestVerdict = data;
  verdictCard.className = `verdict-card ${verdictClass(data.verdict)}`;
  verdictCard.querySelector(".verdict-label").textContent = data.verdict;
  verdictTitle.textContent = `${data.plate} · ${data.message}`;
  verdictDetail.textContent = data.owner_name || data.unit ? `${data.owner_name || "-"} / ${data.unit || "-"}` : "차량 등록정보가 없습니다.";

  const meta = [
    { label: "차량번호", value: data.plate || "-" },
    { label: "상태", value: data.status || "-" },
    { label: "동호수", value: data.unit || "-" },
    { label: "차주", value: data.owner_name || "-" },
    { label: "연락처", html: contactActionsMarkup(data.phone, data.plate, "light") },
    { label: "시작일", value: data.valid_from || "-" },
    { label: "만료일", value: data.valid_to || "-" },
  ];
  verdictMeta.innerHTML = meta
    .map((item) => `<div><dt>${escapeHtml(item.label)}</dt><dd>${item.html ?? escapeHtml(item.value || "-")}</dd></div>`)
    .join("");

  if (data.verdict === "OK") {
    saveBtn.textContent = "정상 확인 저장";
  } else if (data.verdict === "TEMP") {
    saveBtn.textContent = "임시 등록 확인 저장";
  } else {
    saveBtn.textContent = "단속 기록 저장";
  }

  renderMatchNavigator(data);
  refreshSmsLinks(verdictMeta);
}

function applyCheckResponse(data) {
  const rawMatches = Array.isArray(data.matches) ? data.matches : [];
  currentCheckRequestedPlate = data.requested_plate || plateInput.value.trim();
  currentCheckMatches = rawMatches.length ? rawMatches.map(toMatchItem) : [toMatchItem(data)];
  currentCheckIndex = Math.min(Math.max(Number(data.match_index || 0), 0), Math.max(currentCheckMatches.length - 1, 0));

  const active = currentCheckMatches[currentCheckIndex];
  if (active?.plate && data.match_count) {
    plateInput.value = active.plate;
  }
  renderVerdict({
    ...data,
    ...active,
  });
}

function shiftCheckMatch(step) {
  if (currentCheckMatches.length < 2) {
    return;
  }
  currentCheckIndex = (currentCheckIndex + step + currentCheckMatches.length) % currentCheckMatches.length;
  const active = currentCheckMatches[currentCheckIndex];
  if (!active) {
    return;
  }
  plateInput.value = active.plate || plateInput.value;
  renderVerdict({
    ...latestVerdict,
    ...active,
    requested_plate: currentCheckRequestedPlate,
    match_mode: "suffix",
    match_count: currentCheckMatches.length,
    match_index: currentCheckIndex,
  });
  setStatus(`${plateInput.value} ${currentCheckIndex + 1}/${currentCheckMatches.length} 확인 중`, active.verdict === "OK" ? "success" : active.verdict === "TEMP" ? "warn" : "danger");
}

function renderCandidates(items) {
  if (!items?.length) {
    candidateList.innerHTML = '<span class="subtle">후보가 없으면 차량번호를 직접 입력해 주세요.</span>';
    return;
  }
  candidateList.innerHTML = items
    .map((candidate, index) => `
      <button type="button" class="candidate-chip ${index === 0 ? "is-primary" : ""}" data-plate="${escapeHtml(candidate)}">
        ${escapeHtml(candidate)}
      </button>
    `)
    .join("");
  candidateList.querySelectorAll("[data-plate]").forEach((button) => {
    button.addEventListener("click", () => {
      plateInput.value = button.dataset.plate || "";
      setStatus(`후보 번호 ${button.dataset.plate} 선택`, "active");
      runCheck().catch((error) => alert(error.message));
    });
  });
}

function attachResultClickHandlers(root) {
  root.querySelectorAll("[data-plate-pick]").forEach((button) => {
    button.addEventListener("click", () => {
      plateInput.value = button.dataset.platePick || "";
      runCheck().catch((error) => alert(error.message));
    });
  });
}

function renderSearchResults(rows) {
  if (!rows?.length) {
    searchResults.className = "list-board empty-state";
    searchResults.textContent = "검색 결과가 없습니다.";
    return;
  }
  searchResults.className = "list-board";
  searchResults.innerHTML = rows
    .map((row) => `
      <article class="result-item">
        <div class="result-top">
          <button type="button" class="result-title pick-button" data-plate-pick="${escapeHtml(row.plate)}">${escapeHtml(row.plate)}</button>
          <span class="result-badge ${badgeClass((row.status || "active").toUpperCase() === "BLOCKED" ? "BLOCKED" : (row.status || "active") === "temp" ? "TEMP" : "OK")}">${escapeHtml(row.status || "active")}</span>
        </div>
        <div>${escapeHtml(row.owner_name || "-")} / ${escapeHtml(row.unit || "-")}</div>
        <div class="subtle contact-line"><span>연락처</span>${contactActionsMarkup(row.phone, row.plate)}</div>
        <div class="subtle">${escapeHtml(row.note || "비고 없음")}</div>
      </article>
    `)
    .join("");
  attachResultClickHandlers(searchResults);
  refreshSmsLinks(searchResults);
}

function renderRecent(rows) {
  if (!rows?.length) {
    recentResults.className = "list-board empty-state";
    recentResults.textContent = "저장된 단속 기록이 없습니다.";
    return;
  }
  recentResults.className = "list-board";
  recentResults.innerHTML = rows
    .map((row) => `
      <article class="result-item">
        <div class="result-top">
          <button type="button" class="result-title pick-button" data-plate-pick="${escapeHtml(row.plate)}">${escapeHtml(row.plate)}</button>
          <span class="result-badge ${badgeClass(row.verdict)}">${escapeHtml(row.verdict)}</span>
        </div>
        <div>${escapeHtml(row.verdict_message || "-")}</div>
        <div class="subtle">${escapeHtml(row.location || "-")} · ${escapeHtml(row.inspector || "-")} · ${escapeHtml(row.created_at || "-")}</div>
      </article>
    `)
    .join("");
  attachResultClickHandlers(recentResults);
}

function renderRegistryStatus(status) {
  if (!registryStatus) return;
  const last = status.last_sync;
  const learning = status.ocr_learning || {};
  const lastFeedback = learning.last_feedback;
  const importFiles = Array.isArray(status.import_files) ? status.import_files : [];
  const fileMarkup = importFiles.length
    ? importFiles
        .map((file) => `<div class="import-file-item"><strong>${escapeHtml(file.name)}</strong><span>${escapeHtml(file.modified_at || "-")} · ${escapeHtml(file.size || 0)} bytes</span></div>`)
        .join("")
    : '<div class="subtle">아직 업로드된 Excel 파일이 없습니다.</div>';
  registryStatus.innerHTML = `
    <div class="result-item">
      <div class="result-top">
        <span class="result-title">등록차량 ${escapeHtml(status.vehicle_count)}</span>
        <span class="result-badge ${badgeClass(last?.status === "success" ? "OK" : last?.status === "failed" ? "BLOCKED" : "IDLE")}">${escapeHtml(last?.status || "대기")}</span>
      </div>
      <div>아파트: ${escapeHtml(status.site_name || currentSiteName || "-")} (${escapeHtml(status.site_code || currentSiteCode || "-")})</div>
      <div>폴더: ${escapeHtml(status.import_dir)}</div>
      <div class="subtle">${escapeHtml(last?.message || "아직 동기화 이력이 없습니다.")}</div>
      <div class="subtle">AI 학습 누적: ${escapeHtml(learning.total_feedback || 0)}건 / 사용자 교정: ${escapeHtml(learning.corrected_feedback || 0)}건</div>
      <div class="subtle">${lastFeedback ? `최근 학습: ${escapeHtml(lastFeedback.suggested_plate || "-")} → ${escapeHtml(lastFeedback.corrected_plate || "-")} (${escapeHtml(lastFeedback.created_at || "-")})` : "아직 OCR 학습 이력이 없습니다."}</div>
    </div>
    <div class="import-file-list">${fileMarkup}</div>
  `;
}

function registryFileErrors(files) {
  return files.flatMap((file) => {
    const name = file.name || "이름 없는 파일";
    const lowerName = name.toLowerCase();
    if (name.startsWith("~$")) {
      return [`${name}: Excel 임시 잠금 파일입니다. Excel에서 원본 파일을 닫고 실제 파일을 선택해 주세요.`];
    }
    if (!EXCEL_UPLOAD_SUFFIXES.some((suffix) => lowerName.endsWith(suffix))) {
      return [`${name}: .xlsx 또는 .xlsm 파일만 업로드할 수 있습니다.`];
    }
    if (file.size <= 0) {
      return [`${name}: 파일이 비어 있습니다.`];
    }
    return [];
  });
}

function setRegistryFileNote(message, tone = "idle") {
  if (!registryFileNote) return;
  registryFileNote.textContent = message;
  registryFileNote.className = `subtle registry-file-note ${tone === "error" ? "is-error" : ""}`;
}

function renderRegistrySelection() {
  if (!registryFileInput || !registryFileNote) return false;
  const files = Array.from(registryFileInput.files || []);
  if (!files.length) {
    setRegistryFileNote("선택된 파일이 없습니다.");
    if (uploadRegistryBtn) uploadRegistryBtn.disabled = false;
    return false;
  }

  const errors = registryFileErrors(files);
  if (errors.length) {
    setRegistryFileNote(`선택 오류:\n${errors.join("\n")}`, "error");
    if (uploadRegistryBtn) uploadRegistryBtn.disabled = true;
    return false;
  }

  setRegistryFileNote(`선택됨: ${files.map((file) => file.name).join(", ")}`);
  if (uploadRegistryBtn) uploadRegistryBtn.disabled = false;
  return true;
}

function renderUserList(users) {
  if (!userList) return;
  if (!users?.length) {
    userList.className = "list-board empty-state";
    userList.textContent = "등록된 사용자가 없습니다.";
    return;
  }

  userList.className = "list-board";
  userList.innerHTML = users
    .map((user) => {
      const role = userRoleOption(user.role);
      const isCurrent = user.username === currentUsername;
      return `
        <article class="result-item user-item" data-user-row="${escapeHtml(user.username)}" data-original-role="${escapeHtml(user.role)}">
          <div class="result-top">
            <div>
              <div class="result-title user-title">
                <span>${escapeHtml(user.username)}</span>
                ${isCurrent ? '<span class="self-chip">내 계정</span>' : ""}
              </div>
              <div class="subtle">${escapeHtml(user.site_code || currentSiteCode || "-")} · 생성일 ${escapeHtml(user.created_at || "-")}</div>
            </div>
            <span class="result-badge ${role.badgeClass}">${escapeHtml(role.label)}</span>
          </div>
          <div class="field-grid user-form-grid">
            <label>
              <span>권한</span>
              <select data-user-role>
                ${userRoleOptionsMarkup(user.role)}
              </select>
            </label>
            <label>
              <span>새 비밀번호</span>
              <input type="password" data-user-password placeholder="변경할 때만 입력">
            </label>
          </div>
          <div class="user-action-row">
            <button type="button" class="secondary-btn" data-user-save>저장</button>
            <button type="button" class="ghost-btn" data-user-clear>입력 지우기</button>
            <button type="button" class="danger-btn" data-user-delete ${isCurrent ? "disabled" : ""}>삭제</button>
          </div>
        </article>
      `;
    })
    .join("");

  userList.querySelectorAll("[data-user-save]").forEach((button) => {
    button.addEventListener("click", () => saveUserRow(button).catch((error) => alert(error.message)));
  });
  userList.querySelectorAll("[data-user-clear]").forEach((button) => {
    button.addEventListener("click", () => resetUserRow(button));
  });
  userList.querySelectorAll("[data-user-delete]").forEach((button) => {
    button.addEventListener("click", () => deleteUserRow(button).catch((error) => alert(error.message)));
  });
}

function renderSiteList(sites) {
  if (!siteList) return;
  if (!sites?.length) {
    siteList.className = "list-board empty-state";
    siteList.textContent = "등록된 아파트가 없습니다.";
    return;
  }

  siteList.className = "list-board";
  siteList.innerHTML = sites
    .map((site) => {
      const isCurrent = site.site_code === currentSiteCode;
      return `
        <article class="result-item">
          <div class="result-top">
            <div>
              <div class="result-title user-title">
                <span>${escapeHtml(site.name || site.site_code || "-")}</span>
                ${isCurrent ? '<span class="self-chip">현재 아파트</span>' : ""}
              </div>
              <div class="subtle">${escapeHtml(site.site_code || "-")} · 생성일 ${escapeHtml(site.created_at || "-")}</div>
            </div>
            <span class="result-badge badge-idle">사용자 ${escapeHtml(site.users_count || 0)}</span>
          </div>
          <div class="subtle">등록차량 ${escapeHtml(site.vehicles_count || 0)}대</div>
        </article>
      `;
    })
    .join("");
}

function resetUserRow(button) {
  const row = button.closest("[data-user-row]");
  if (!row) return;
  const roleSelect = row.querySelector("[data-user-role]");
  const passwordInput = row.querySelector("[data-user-password]");
  if (roleSelect) {
    roleSelect.value = row.dataset.originalRole || "cleaner";
  }
  if (passwordInput) {
    passwordInput.value = "";
  }
}

function displayDateTime(value) {
  return String(value || "-").replace("T", " ").slice(0, 16);
}

function displayDateTimeRange(startValue, endValue) {
  const start = displayDateTime(startValue);
  const end = displayDateTime(endValue);
  if (start === end) {
    return start;
  }
  return `${start} ~ ${end}`;
}

function renderCctvAdminControls(row) {
  if (!currentCanAssignCctv) {
    return "";
  }
  return `
    <div class="cctv-assignment-grid">
      <label>
        <span>담당자</span>
        <select data-cctv-assignee>
          ${cctvAssigneeOptionsMarkup(row.assigned_to || "")}
        </select>
      </label>
      <label>
        <span>업무 가중치</span>
        <select data-cctv-weight>
          ${cctvWeightOptionsMarkup(row.work_weight)}
        </select>
      </label>
      <label>
        <span>상태</span>
        <select data-cctv-status>
          ${cctvStatusOptionsMarkup(row.status)}
        </select>
      </label>
    </div>
    <label class="cctv-instruction-label">
      <span>작업지시</span>
      <textarea data-cctv-instruction rows="2" placeholder="예: 18:20~18:40 103동 출입구 방향 확인">${escapeHtml(row.instruction || "")}</textarea>
    </label>
    <div class="user-action-row">
      <button type="button" class="secondary-btn" data-cctv-save>작업지시 저장</button>
    </div>
  `;
}

function renderCctvRequests(rows) {
  if (!cctvRequestList) return;
  if (!rows?.length) {
    cctvRequestList.className = "list-board empty-state";
    cctvRequestList.textContent = "등록된 CCTV 검색요청이 없습니다.";
    return;
  }

  cctvRequestList.className = "list-board cctv-list";
  cctvRequestList.innerHTML = rows
    .map((row) => {
      const status = cctvStatusOption(row.status);
      const photo = row.photo_path ? `<a class="contact-action" href="${escapeHtml(row.photo_path)}" target="_blank" rel="noopener">사진 보기</a>` : "";
      return `
        <article class="result-item cctv-item" data-cctv-row="${escapeHtml(row.id)}">
          <div class="result-top">
            <div>
              <div class="result-title">${escapeHtml(row.location || "-")}</div>
              <div class="subtle">요청자 ${escapeHtml(row.requester_username || "-")} · 검색 ${escapeHtml(displayDateTimeRange(row.search_start_time || row.search_time, row.search_end_time || row.search_time))}</div>
            </div>
            <span class="result-badge ${status.badgeClass}">${escapeHtml(status.label)}</span>
          </div>
          <div class="cctv-content">${escapeHtml(row.content || "-")}</div>
          <div class="cctv-meta-row">
            <span>가중치 ${escapeHtml(row.work_weight || 1)}</span>
            <span>담당 ${escapeHtml(row.assigned_to || "미배정")}</span>
            <span>등록 ${escapeHtml(displayDateTime(row.created_at))}</span>
            ${photo}
          </div>
          ${row.instruction && !currentCanAssignCctv ? `<div class="cctv-instruction-view">작업지시: ${escapeHtml(row.instruction)}</div>` : ""}
          ${renderCctvAdminControls(row)}
        </article>
      `;
    })
    .join("");

  cctvRequestList.querySelectorAll("[data-cctv-save]").forEach((button) => {
    button.addEventListener("click", () => saveCctvAssignment(button).catch((error) => alert(error.message)));
  });
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let message = `요청 실패: ${response.status}`;
    try {
      const body = await response.json();
      message = body.detail || message;
    } catch (_) {
      // ignore
    }
    throw new Error(message);
  }
  return response.json();
}

async function runCheck() {
  const plate = plateInput.value.trim();
  if (!plate) {
    alert("차량번호를 입력해 주세요.");
    return;
  }
  setStatus("등록차량 DB 조회 중", "active");
  const data = await fetchJson(`${apiUrl("/api/registry/check")}?plate=${encodeURIComponent(plate)}`);
  applyCheckResponse(data);
  if (data.match_mode === "suffix" && data.match_count > 1) {
    setStatus(`뒤 4자리 ${data.requested_plate} 일치 차량 ${data.match_count}대`, "warn");
  } else {
    setStatus(`${data.plate} 조회 완료`, data.verdict === "OK" ? "success" : data.verdict === "TEMP" ? "warn" : "danger");
  }
}

async function runScan() {
  if (!photoInput.files?.length) {
    if (plateInput.value.trim()) {
      await runCheck();
      return;
    }
    alert("사진을 선택하거나 차량번호를 직접 입력해 주세요.");
    return;
  }

  setStatus("번호판 OCR 판독 중", "active");
  const formData = new FormData();
  formData.append("photo", photoInput.files[0]);
  formData.append("manual_plate", plateInput.value.trim());

  const result = await fetchJson(apiUrl("/api/ocr/scan"), { method: "POST", body: formData });
  latestRawText = result.raw_text || "";
  latestOcrBestPlate = result.best_plate || "";
  latestOcrCandidates = Array.isArray(result.candidates) ? result.candidates : [];
  renderCandidates(result.candidates || []);
  ocrRaw.hidden = !latestRawText;
  ocrRaw.textContent = latestRawText;

  if (result.best_plate) {
    plateInput.value = result.best_plate;
  }
  if (result.match) {
    renderVerdict(result.match);
    setStatus(`${result.best_plate} 판독 완료`, result.match.verdict === "OK" ? "success" : result.match.verdict === "TEMP" ? "warn" : "danger");
  } else {
    setStatus("후보를 확인해 수동 선택해 주세요.", "warn");
  }
  if (result.error) {
    geoStatus.textContent = result.error;
  }
}

function vibrate(pattern) {
  if (navigator.vibrate) {
    navigator.vibrate(pattern);
  }
}

function resetWorkflow() {
  photoInput.value = "";
  updatePreview(null);
  plateInput.value = "";
  memoInput.value = "";
  latestRawText = "";
  ocrRaw.hidden = true;
  ocrRaw.textContent = "";
  renderCandidates([]);
  renderIdleVerdict();
  syncQuickMemoState();
  setStatus("다음 차량 촬영 준비", "idle");
}

async function saveEvent() {
  const plate = plateInput.value.trim();
  if (!plate) {
    alert("차량번호를 먼저 확인해 주세요.");
    return;
  }
  if (!latestVerdict) {
    await runCheck();
  }

  setStatus("단속 기록 저장 중", "active");
  const formData = new FormData();
  formData.append("plate", plateInput.value.trim());
  formData.append("inspector", inspectorInput.value.trim());
  formData.append("location", locationInput.value.trim());
  formData.append("memo", memoInput.value.trim());
  formData.append("raw_ocr_text", latestRawText);
  formData.append("ocr_best_plate", latestOcrBestPlate);
  formData.append("ocr_candidates", JSON.stringify(latestOcrCandidates));
  if (currentGeo.lat !== null) formData.append("lat", String(currentGeo.lat));
  if (currentGeo.lng !== null) formData.append("lng", String(currentGeo.lng));
  if (photoInput.files?.length) formData.append("photo", photoInput.files[0]);

  await fetchJson(apiUrl("/api/enforcement/submit"), { method: "POST", body: formData });
  await loadRecent();
  vibrate([80, 40, 80]);
  setStatus("기록 저장 완료", "success");
  resetWorkflow();
}

async function searchRegistry() {
  const q = document.getElementById("search-query").value.trim();
  const data = await fetchJson(`${apiUrl("/api/registry/search")}?q=${encodeURIComponent(q)}`);
  renderSearchResults(data);
}

async function loadRecent() {
  const data = await fetchJson(apiUrl("/api/enforcement/recent"));
  renderRecent(data);
}

async function loadRegistryStatus() {
  if (!registryStatus) return;
  const data = await fetchJson(apiUrl("/api/registry/status"));
  renderRegistryStatus(data);
}

async function syncRegistry() {
  setStatus("Excel 등록차량 동기화 중", "active");
  await fetchJson(apiUrl("/api/registry/sync"), { method: "POST" });
  await loadRegistryStatus();
  await searchRegistry();
  setStatus("등록차량 다시 읽기 완료", "success");
}

async function uploadRegistryFiles() {
  if (!registryFileInput?.files?.length) {
    alert("업로드할 Excel 파일을 먼저 선택해 주세요.");
    return;
  }
  if (!renderRegistrySelection()) {
    alert(registryFileNote?.textContent || "Excel 파일 선택 내용을 확인해 주세요.");
    return;
  }

  setStatus("Excel 업로드 및 동기화 중", "active");
  const formData = new FormData();
  Array.from(registryFileInput.files).forEach((file) => {
    formData.append("files", file);
  });

  let result;
  try {
    result = await fetchJson(apiUrl("/api/registry/upload"), { method: "POST", body: formData });
  } catch (error) {
    setRegistryFileNote(`업로드 실패:\n${error.message || error}`, "error");
    setStatus("Excel 업로드 실패", "danger");
    throw error;
  }
  registryFileInput.value = "";
  renderRegistrySelection();
  await loadRegistryStatus();
  await searchRegistry();
  setStatus(`${result.saved_count}개 Excel 업로드 및 동기화 완료`, "success");
}

async function loadCctvAssignees() {
  if (!currentCanAssignCctv) return;
  cctvAssignees = await fetchJson(apiUrl("/api/cctv/assignees"));
}

async function loadCctvRequests() {
  if (!cctvRequestList) return;
  const data = await fetchJson(apiUrl("/api/cctv/requests"));
  renderCctvRequests(data);
}

async function createCctvRequest(event) {
  event.preventDefault();
  if (!cctvPhotoInput?.files?.length) {
    alert("사진을 선택해 주세요.");
    return;
  }
  const location = cctvLocationInput?.value.trim() || "";
  const searchStartTime = cctvSearchStartTimeInput?.value.trim() || "";
  const searchEndTime = cctvSearchEndTimeInput?.value.trim() || "";
  const content = cctvContentInput?.value.trim() || "";
  if (!location || !searchStartTime || !searchEndTime || !content) {
    alert("사진, 위치, 시작 시간, 끝 시간, 내용을 모두 입력해 주세요.");
    return;
  }
  if (searchEndTime < searchStartTime) {
    alert("끝 시간은 시작 시간 이후로 입력해 주세요.");
    return;
  }

  setStatus("CCTV 검색요청 등록 중", "active");
  const formData = new FormData();
  formData.append("photo", cctvPhotoInput.files[0]);
  formData.append("location", location);
  formData.append("search_start_time", searchStartTime);
  formData.append("search_end_time", searchEndTime);
  formData.append("content", content);

  await fetchJson(apiUrl("/api/cctv/requests"), { method: "POST", body: formData });
  cctvRequestForm.reset();
  await loadCctvRequests();
  setStatus("CCTV 검색요청 등록 완료", "success");
}

async function saveCctvAssignment(button) {
  const row = button.closest("[data-cctv-row]");
  if (!row) return;
  const requestId = row.dataset.cctvRow;
  const assignee = row.querySelector("[data-cctv-assignee]")?.value || null;
  const workWeight = Number(row.querySelector("[data-cctv-weight]")?.value || 1);
  const status = row.querySelector("[data-cctv-status]")?.value || "requested";
  const instruction = row.querySelector("[data-cctv-instruction]")?.value || "";

  setStatus(`CCTV 요청 #${requestId} 작업지시 저장 중`, "active");
  await fetchJson(apiUrl(`/api/cctv/requests/${encodeURIComponent(requestId)}`), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      assigned_to: assignee,
      work_weight: workWeight,
      instruction,
      status,
    }),
  });
  await loadCctvRequests();
  setStatus(`CCTV 요청 #${requestId} 작업지시 저장 완료`, "success");
}

async function loadUsers() {
  if (!userList) return;
  const data = await fetchJson(apiUrl("/api/users"));
  renderUserList(data);
}

async function loadSites() {
  if (!siteList) return;
  const data = await fetchJson(apiUrl("/api/sites"));
  renderSiteList(data);
}

async function createSite() {
  if (!newSiteCodeInput || !newSiteNameInput || !newSiteAdminUsernameInput || !newSiteAdminPasswordInput) return;

  const siteCode = newSiteCodeInput.value.trim().toUpperCase();
  const name = newSiteNameInput.value.trim();
  const adminUsername = newSiteAdminUsernameInput.value.trim().toLowerCase();
  const adminPassword = newSiteAdminPasswordInput.value;

  if (!siteCode || !name || !adminUsername || !adminPassword) {
    alert("아파트 코드, 아파트명, 초기 관리자 계정을 모두 입력해 주세요.");
    return;
  }

  setStatus(`아파트 ${siteCode} 등록 중`, "active");
  await fetchJson(apiUrl("/api/sites"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      site_code: siteCode,
      name,
      admin_username: adminUsername,
      admin_password: adminPassword,
    }),
  });

  siteCreateForm?.reset();
  await loadSites();
  setStatus(`아파트 ${siteCode} 등록 완료`, "success");
}

async function createUser() {
  if (!newUserUsernameInput || !newUserPasswordInput || !newUserRoleInput) return;

  const username = newUserUsernameInput.value.trim().toLowerCase();
  const password = newUserPasswordInput.value;
  const role = newUserRoleInput.value;

  if (!username) {
    alert("아이디를 입력해 주세요.");
    return;
  }
  if (!password) {
    alert("초기 비밀번호를 입력해 주세요.");
    return;
  }

  setStatus(`사용자 ${username} 등록 중`, "active");
  await fetchJson(apiUrl("/api/users"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, role }),
  });

  newUserUsernameInput.value = "";
  newUserPasswordInput.value = "";
  newUserRoleInput.value = "guard";
  await loadUsers();
  setStatus(`사용자 ${username} 등록 완료`, "success");
}

async function saveUserRow(button) {
  const row = button.closest("[data-user-row]");
  if (!row) return;

  const username = row.dataset.userRow || "";
  const roleSelect = row.querySelector("[data-user-role]");
  const passwordInput = row.querySelector("[data-user-password]");
  const role = roleSelect?.value || row.dataset.originalRole || "cleaner";
  const password = passwordInput?.value || "";

  setStatus(`사용자 ${username} 정보 저장 중`, "active");
  await fetchJson(apiUrl(`/api/users/${encodeURIComponent(username)}`), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      role,
      password: password || null,
    }),
  });

  await loadUsers();
  setStatus(`사용자 ${username} 정보 저장 완료`, "success");
}

async function deleteUserRow(button) {
  const row = button.closest("[data-user-row]");
  if (!row) return;

  const username = row.dataset.userRow || "";
  if (!confirm(`${username} 계정을 삭제하시겠습니까?`)) {
    return;
  }

  setStatus(`사용자 ${username} 삭제 중`, "active");
  await fetchJson(apiUrl(`/api/users/${encodeURIComponent(username)}`), {
    method: "DELETE",
  });
  await loadUsers();
  setStatus(`사용자 ${username} 삭제 완료`, "success");
}

function loadGeolocation() {
  if (!navigator.geolocation) {
    geoStatus.textContent = "이 브라우저는 위치 기능을 지원하지 않습니다.";
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (position) => {
      currentGeo = {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
      };
      geoStatus.textContent = `위치 저장 준비: ${currentGeo.lat.toFixed(5)}, ${currentGeo.lng.toFixed(5)}`;
    },
    (error) => {
      geoStatus.textContent = `위치 확인 실패: ${error.message}`;
    },
    { enableHighAccuracy: true, timeout: 8000 }
  );
}

photoInput?.addEventListener("change", () => {
  const file = photoInput.files?.[0];
  updatePreview(file || null);
  if (file) {
    runScan().catch((error) => alert(error.message));
  } else {
    setStatus("촬영 대기 중", "idle");
  }
});

registryFileInput?.addEventListener("change", renderRegistrySelection);

plateInput?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    runCheck().catch((error) => alert(error.message));
  }
});

plateInput?.addEventListener("input", () => refreshSmsLinks());
inspectorInput?.addEventListener("input", () => persistField("inspector", inspectorInput.value.trim()));
locationInput?.addEventListener("input", () => {
  persistField("location", locationInput.value.trim());
  refreshSmsLinks();
});
memoInput?.addEventListener("input", syncQuickMemoState);

quickMemoButtons.forEach((button) => {
  button.addEventListener("click", () => {
    memoInput.value = button.dataset.memo || "";
    syncQuickMemoState();
  });
});

mobileTabButtons.forEach((button) => {
  button.addEventListener("click", () => {
    activateMobileTab(button.dataset.mobileTab || "enforce");
  });
});

scanBtn?.addEventListener("click", () => runScan().catch((error) => alert(error.message)));
checkBtn?.addEventListener("click", () => runCheck().catch((error) => alert(error.message)));
saveBtn?.addEventListener("click", () => saveEvent().catch((error) => alert(error.message)));
resetBtn?.addEventListener("click", resetWorkflow);
matchPrevBtn?.addEventListener("click", () => shiftCheckMatch(-1));
matchNextBtn?.addEventListener("click", () => shiftCheckMatch(1));
document.getElementById("search-btn")?.addEventListener("click", () => searchRegistry().catch((error) => alert(error.message)));
document.getElementById("sync-btn")?.addEventListener("click", () => syncRegistry().catch((error) => alert(error.message)));
uploadRegistryBtn?.addEventListener("click", () => uploadRegistryFiles().catch((error) => alert(error.message)));
userRefreshBtn?.addEventListener("click", () => loadUsers().catch((error) => alert(error.message)));
siteRefreshBtn?.addEventListener("click", () => loadSites().catch((error) => alert(error.message)));
cctvRequestForm?.addEventListener("submit", (event) => createCctvRequest(event).catch((error) => alert(error.message)));
cctvRefreshBtn?.addEventListener("click", () => loadCctvRequests().catch((error) => alert(error.message)));
document.getElementById("geo-btn")?.addEventListener("click", loadGeolocation);
document.getElementById("search-query")?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    searchRegistry().catch((error) => alert(error.message));
  }
});
userCreateForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  createUser().catch((error) => alert(error.message));
});
siteCreateForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  createSite().catch((error) => alert(error.message));
});

hydrateFields();
syncQuickMemoState();
renderRegistrySelection();
renderCandidates([]);
renderIdleVerdict();
setStatus("촬영 대기 중", "idle");
initMobileTabs();

loadRecent().catch((error) => {
  recentResults.className = "list-board empty-state";
  recentResults.textContent = error.message;
});
loadRegistryStatus().catch(() => {});
loadUsers().catch(() => {});
loadSites().catch(() => {});
loadCctvAssignees()
  .catch(() => {})
  .finally(() => {
    loadCctvRequests().catch((error) => {
      if (cctvRequestList) {
        cctvRequestList.className = "list-board empty-state";
        cctvRequestList.textContent = error.message;
      }
    });
  });
