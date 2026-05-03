const rootPath = document.body.dataset.rootPath || "";
const currentSiteCode = document.body.dataset.siteCode || "";
const currentSiteName = document.body.dataset.siteName || currentSiteCode;
const currentUsername = document.body.dataset.username || "";
const currentRole = document.body.dataset.role || "";
const currentCanManageVehicles = document.body.dataset.canManageVehicles === "1";
const apiUrl = (path) => `${rootPath}${path}`;
const defaultCapturePlaceholderImage = apiUrl("/static/parking-app-icon.png");

const photoInput = document.getElementById("photo");
const photoPreview = document.getElementById("photo-preview");
const previewPlaceholder = document.getElementById("preview-placeholder");
const plateInput = document.getElementById("plate-input");
const inspectorInput = document.getElementById("inspector");
const locationInput = document.getElementById("location");
const memoInput = document.getElementById("memo");
const scanBtn = document.getElementById("scan-btn");
const checkBtn = document.getElementById("check-btn");
const captureButtonLabel = photoInput?.closest(".capture-button");
const saveBtn = document.getElementById("save-btn");
const resetBtn = document.getElementById("reset-btn");
const candidateList = document.getElementById("candidate-list");
const ocrNote = document.getElementById("ocr-note");
const ocrLearningPanel = document.getElementById("ocr-learning-panel");
const ocrLearningTitle = document.getElementById("ocr-learning-title");
const ocrLearningText = document.getElementById("ocr-learning-text");
const ocrLearningBadge = document.getElementById("ocr-learning-badge");
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
const registryPreserveManualInput = document.getElementById("registry-preserve-manual");
const vehicleQueryInput = document.getElementById("vehicle-query");
const vehicleSearchBtn = document.getElementById("vehicle-search-btn");
const vehicleCreateBtn = document.getElementById("vehicle-create-btn");
const vehicleBackupBtn = document.getElementById("vehicle-backup-btn");
const vehicleNewPlateInput = document.getElementById("vehicle-new-plate");
const vehicleNewUnitInput = document.getElementById("vehicle-new-unit");
const vehicleNewOwnerInput = document.getElementById("vehicle-new-owner");
const vehicleNewPhoneInput = document.getElementById("vehicle-new-phone");
const vehicleBackupList = document.getElementById("vehicle-backup-list");
const vehicleList = document.getElementById("vehicle-list");
const capturePlaceholderInput = document.getElementById("capture-placeholder-input");
const uploadCapturePlaceholderBtn = document.getElementById("upload-capture-placeholder-btn");
const deleteCapturePlaceholderBtn = document.getElementById("delete-capture-placeholder-btn");
const capturePlaceholderNote = document.getElementById("capture-placeholder-note");
const userList = document.getElementById("user-list");
const userCreateForm = document.getElementById("user-create-form");
const newUserUsernameInput = document.getElementById("new-user-username");
const newUserPasswordInput = document.getElementById("new-user-password");
const newUserRoleInput = document.getElementById("new-user-role");
const newUserVehicleManagerInput = document.getElementById("new-user-vehicle-manager");
const userRefreshBtn = document.getElementById("user-refresh-btn");
const userFilterForm = document.getElementById("user-filter-form");
const userQueryInput = document.getElementById("user-query");
const userRoleFilterInput = document.getElementById("user-role-filter");
const userFilterResetBtn = document.getElementById("user-filter-reset-btn");
const userLoadMoreBtn = document.getElementById("user-load-more-btn");
const siteList = document.getElementById("site-list");
const siteCreateForm = document.getElementById("site-create-form");
const newSiteCodeInput = document.getElementById("new-site-code");
const newSiteNameInput = document.getElementById("new-site-name");
const newSiteAdminUsernameInput = document.getElementById("new-site-admin-username");
const newSiteAdminPasswordInput = document.getElementById("new-site-admin-password");
const siteRefreshBtn = document.getElementById("site-refresh-btn");
const siteFilterForm = document.getElementById("site-filter-form");
const siteQueryInput = document.getElementById("site-query");
const siteFilterResetBtn = document.getElementById("site-filter-reset-btn");
const siteLoadMoreBtn = document.getElementById("site-load-more-btn");
const billingStatus = document.getElementById("billing-status");
const billingRefreshBtn = document.getElementById("billing-refresh-btn");
const billingInquiryForm = document.getElementById("billing-inquiry-form");
const billingRequestedPlanInput = document.getElementById("billing-requested-plan");
const billingContactNameInput = document.getElementById("billing-contact-name");
const billingContactPhoneInput = document.getElementById("billing-contact-phone");
const billingContactEmailInput = document.getElementById("billing-contact-email");
const billingMessageInput = document.getElementById("billing-message");
const cctvRequestForm = document.getElementById("cctv-request-form");
const cctvPhotoInput = document.getElementById("cctv-photo");
const cctvLocationInput = document.getElementById("cctv-location");
const cctvSearchStartTimeInput = document.getElementById("cctv-search-start-time");
const cctvSearchEndTimeInput = document.getElementById("cctv-search-end-time");
const cctvContentInput = document.getElementById("cctv-content");
const cctvRequestList = document.getElementById("cctv-request-list");
const cctvRefreshBtn = document.getElementById("cctv-refresh-btn");
const cctvLoadMoreBtn = document.getElementById("cctv-load-more-btn");
const contactCategoryFilterInput = document.getElementById("contact-category-filter");
const contactQueryInput = document.getElementById("contact-query");
const contactSearchBtn = document.getElementById("contact-search-btn");
const contactRefreshBtn = document.getElementById("contact-refresh-btn");
const contactList = document.getElementById("contact-list");
const contactForm = document.getElementById("contact-form");
const contactCategoryInput = document.getElementById("contact-category");
const contactNameInput = document.getElementById("contact-name");
const contactPhoneInput = document.getElementById("contact-phone");
const contactDutyInput = document.getElementById("contact-duty");
const contactMemoInput = document.getElementById("contact-memo");
const contactFavoriteInput = document.getElementById("contact-favorite");
const historyFilterForm = document.getElementById("history-filter-form");
const historyQueryInput = document.getElementById("history-query");
const historyVerdictInput = document.getElementById("history-verdict");
const historyRangeInput = document.getElementById("history-range");
const historyDateFromInput = document.getElementById("history-date-from");
const historyDateToInput = document.getElementById("history-date-to");
const historyResetBtn = document.getElementById("history-reset-btn");
const historyLoadMoreBtn = document.getElementById("history-load-more-btn");
const historyExportPreviewBtn = document.getElementById("history-export-preview-btn");
const exportModal = document.getElementById("export-modal");
const exportCloseBtn = document.getElementById("export-close-btn");
const exportSummary = document.getElementById("export-summary");
const exportPreview = document.getElementById("export-preview");
const exportPdfBtn = document.getElementById("export-pdf-btn");
const exportExcelBtn = document.getElementById("export-excel-btn");
const geoStatus = document.getElementById("geo-status");
const statusBanner = document.getElementById("status-banner");
const quickMemoButtons = Array.from(document.querySelectorAll(".quick-chip"));
const mobileTabButtons = Array.from(document.querySelectorAll("[data-mobile-tab]"));
const mobileTabPanels = Array.from(document.querySelectorAll("[data-mobile-tab-panel]"));
const firstUseGuide = document.getElementById("first-use-guide");

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
const currentIsAdmin = currentRole === "admin";
const EXCEL_UPLOAD_SUFFIXES = [".xlsx", ".xlsm"];
const CCTV_STATUS_OPTIONS = [
  { value: "requested", label: "요청", badgeClass: "badge-idle" },
  { value: "assigned", label: "배정", badgeClass: "badge-temp" },
  { value: "in_progress", label: "진행", badgeClass: "badge-temp" },
  { value: "done", label: "완료", badgeClass: "badge-ok" },
  { value: "cancelled", label: "취소", badgeClass: "badge-danger" },
];
const CONTACT_CATEGORY_OPTIONS = [
  { value: "internal", label: "사내", badgeClass: "badge-ok" },
  { value: "public", label: "공공기관", badgeClass: "badge-temp" },
  { value: "vendor", label: "업체", badgeClass: "badge-idle" },
];

let latestRawText = "";
let latestVerdict = null;
let currentGeo = { lat: null, lng: null };
let objectUrl = "";
let latestOcrBestPlate = "";
let latestOcrCandidates = [];
let latestNativeOcr = null;
let nativeOcrWaiters = [];
let currentCheckMatches = [];
let currentCheckIndex = 0;
let currentCheckRequestedPlate = "";
let scanAttemptCount = 0;
let cctvAssignees = [];
let activeMobileTab = "enforce";
let historyOffset = 0;
let historyHasMore = false;
const HISTORY_PAGE_SIZE = 20;
let exportRows = [];
let exportTruncated = false;
let cctvOffset = 0;
let cctvHasMore = false;
const CCTV_PAGE_SIZE = 20;
let cctvRequestRows = [];
let userOffset = 0;
let userHasMore = false;
const USER_PAGE_SIZE = 20;
let userRows = [];
let siteOffset = 0;
let siteHasMore = false;
const SITE_PAGE_SIZE = 20;
let siteRows = [];

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function compactPlateValue(value) {
  return String(value ?? "")
    .trim()
    .toUpperCase()
    .replace(/[\s\-_/.:]/g, "")
    .replace(/[^\dA-Z가-힣|!$]/g, "");
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

function contactCategoryOption(category) {
  return CONTACT_CATEGORY_OPTIONS.find((item) => item.value === category) || CONTACT_CATEGORY_OPTIONS[0];
}

function contactCategoryOptionsMarkup(selectedCategory) {
  return CONTACT_CATEGORY_OPTIONS.map((item) => `<option value="${item.value}" ${item.value === selectedCategory ? "selected" : ""}>${item.label}</option>`).join("");
}

function setStatus(message, tone = "idle") {
  statusBanner.textContent = message;
  statusBanner.className = `status-banner status-${tone}`;
}

function updateOcrLearningPanel() {
  if (!ocrLearningPanel || !ocrLearningTitle || !ocrLearningText || !ocrLearningBadge) return;
  const currentPlate = compactPlateValue(plateInput?.value || "");
  const suggestedPlate = compactPlateValue(latestOcrBestPlate);
  const hasOcrSignal = Boolean(latestRawText || latestOcrCandidates.length || latestNativeOcr?.raw_text || latestNativeOcr?.candidates?.length);

  let state = "idle";
  let title = "촬영 후 번호를 확인해 주세요.";
  let text = "번호를 그대로 저장하거나 고쳐 저장하면 다음 판독 후보 정렬에 반영됩니다.";
  let badge = "대기";

  if (hasOcrSignal && !currentPlate) {
    state = "ready";
    title = "후보를 선택하거나 차량번호를 입력해 주세요.";
    text = "확인한 번호로 저장하면 이 사진의 OCR 결과가 학습 데이터로 누적됩니다.";
    badge = "확인 필요";
  } else if (hasOcrSignal && suggestedPlate && currentPlate && suggestedPlate !== currentPlate) {
    state = "corrected";
    title = "사용자 교정값이 학습됩니다.";
    text = `${suggestedPlate} 후보를 ${currentPlate}로 고쳐 저장하면 다음부터 이 유형의 오인식이 줄어듭니다.`;
    badge = "교정 학습";
  } else if (hasOcrSignal && currentPlate) {
    state = "accepted";
    title = "확인한 번호가 학습됩니다.";
    text = "저장 시 현재 번호가 올바른 판독값으로 기록되어 다음 후보 정렬에 반영됩니다.";
    badge = "확인 학습";
  }

  ocrLearningPanel.className = `learning-panel learning-${state}`;
  ocrLearningTitle.textContent = title;
  ocrLearningText.textContent = text;
  ocrLearningBadge.textContent = badge;
  if (ocrNote) {
    ocrNote.textContent =
      state === "corrected"
        ? "잘못 판독된 번호를 고쳐 저장하면 이 시스템의 OCR 후보 정렬이 실제 현장 데이터에 맞게 좋아집니다."
        : "사진을 선택하면 자동으로 OCR을 시도합니다. 결과가 틀리면 차량번호를 직접 고쳐 저장해 주세요. 그 교정 이력은 다음 판독 후보 정렬에 다시 반영됩니다.";
  }
}

function readStoredValue(key, fallback = "") {
  try {
    return window.localStorage?.getItem(key) ?? fallback;
  } catch {
    return fallback;
  }
}

function writeStoredValue(key, value) {
  try {
    window.localStorage?.setItem(key, value);
  } catch {
    // Storage can be unavailable in some embedded browser modes.
  }
}

function mobileTabStorageKey() {
  return `parking:${currentSiteCode || "default"}:${currentRole || "role"}:mobile-tab`;
}

function firstUseGuideStorageKey() {
  return `parking:${currentSiteCode || "default"}:${currentRole || "role"}:first-use-guide-open`;
}

function initFirstUseGuide() {
  if (!firstUseGuide) {
    return;
  }
  const saved = readStoredValue(firstUseGuideStorageKey(), "");
  if (saved === "0") {
    firstUseGuide.open = false;
  } else if (saved === "1") {
    firstUseGuide.open = true;
  } else if (window.matchMedia("(max-width: 720px)").matches) {
    firstUseGuide.open = false;
  }
  firstUseGuide.addEventListener("toggle", () => {
    writeStoredValue(firstUseGuideStorageKey(), firstUseGuide.open ? "1" : "0");
  });
}

function refreshActiveMobileTab(tab) {
  if (tab === "cctv") {
    loadCctvAssignees()
      .catch(() => {})
      .finally(() => loadCctvRequests().catch(() => {}));
  } else if (tab === "contacts") {
    loadContacts().catch(() => {});
  } else if (tab === "recent") {
    loadRecent().catch(() => {});
  } else if (tab === "vehicle-db") {
    loadVehicleBackups().catch(() => {});
  } else if (tab === "admin") {
    loadRegistryStatus().catch(() => {});
    loadBillingStatus().catch(() => {});
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

  writeStoredValue(mobileTabStorageKey(), nextTab);
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
  const saved = readStoredValue(mobileTabStorageKey(), "enforce") || "enforce";
  activateMobileTab(saved, { refresh: false, scroll: false });
}

function scheduleBackgroundLoad(callback) {
  if (typeof window.requestIdleCallback === "function") {
    window.requestIdleCallback(callback, { timeout: 2500 });
    return;
  }
  window.setTimeout(callback, 300);
}

function persistField(key, value) {
  writeStoredValue(`parking:${key}`, value);
}

function hydrateFields() {
  inspectorInput.value = readStoredValue("parking:inspector", "");
  locationInput.value = readStoredValue("parking:location", "");
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

function setCapturePlaceholderImage(imageUrl) {
  const url = String(imageUrl || "").trim();
  if (!previewPlaceholder) return;
  const backgroundUrl = url || defaultCapturePlaceholderImage;
  previewPlaceholder.style.backgroundImage = `linear-gradient(rgba(255,255,255,0.68), rgba(255,255,255,0.76)), url("${backgroundUrl.replaceAll('"', "%22")}")`;
  previewPlaceholder.classList.toggle("has-custom-image", Boolean(url));
  previewPlaceholder.classList.toggle("has-default-image", !url);
}

function updateCaptureLimitState() {
  const reachedLimit = scanAttemptCount >= 2;
  if (photoInput) {
    photoInput.disabled = reachedLimit;
  }
  if (captureButtonLabel) {
    captureButtonLabel.classList.toggle("is-disabled", reachedLimit);
    const label = captureButtonLabel.querySelector("span");
    if (label) {
      label.textContent = reachedLimit ? "촬영 2회 완료" : `번호판 촬영 ${scanAttemptCount}/2`;
    }
  }
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
  updateOcrLearningPanel();
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
    { label: "동", value: data.building || "-" },
    { label: "호수", value: data.unit_number || "-" },
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
  updateOcrLearningPanel();
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
      updateOcrLearningPanel();
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
        <div>${escapeHtml(row.owner_name || "-")} / ${escapeHtml(row.building || "-")}동 ${escapeHtml(row.unit_number || "-")}호</div>
        <div class="subtle contact-line"><span>연락처</span>${contactActionsMarkup(row.phone, row.plate)}</div>
        <div class="subtle">${escapeHtml(row.note || "비고 없음")}</div>
      </article>
    `)
    .join("");
  attachResultClickHandlers(searchResults);
  refreshSmsLinks(searchResults);
}

function renderRecent(rows, append = false) {
  if (!rows?.length) {
    if (!append) {
      recentResults.className = "list-board empty-state";
      recentResults.textContent = "조회된 단속 기록이 없습니다.";
    }
    return;
  }
  recentResults.className = "list-board";
  const markup = rows
    .map((row) => `
      <article class="result-item enforcement-item" data-enforcement-row="${escapeHtml(row.id)}">
        <div class="result-top">
          <button type="button" class="result-title pick-button" data-plate-pick="${escapeHtml(row.plate)}">${escapeHtml(row.plate)}</button>
          <span class="result-badge ${badgeClass(row.verdict)}">${escapeHtml(row.verdict)}</span>
        </div>
        <div>${escapeHtml(row.verdict_message || "-")}</div>
        <div class="subtle">${escapeHtml(row.location || "-")} · ${escapeHtml(row.inspector || "-")} · ${escapeHtml(displayDateTime(row.created_at))}</div>
        <div class="subtle">${escapeHtml(row.owner_name || "-")} / ${escapeHtml(row.unit || "-")}${row.memo ? ` · ${escapeHtml(row.memo)}` : ""}</div>
        ${row.photo_path ? `<a class="contact-action" href="${escapeHtml(row.photo_path)}" target="_blank" rel="noopener">사진 보기</a>` : ""}
        <div class="enforcement-edit-grid">
          <label>
            <span>차량번호</span>
            <input data-enforcement-plate value="${escapeHtml(row.plate || "")}" autocomplete="off">
          </label>
          <label>
            <span>단속자</span>
            <input data-enforcement-inspector value="${escapeHtml(row.inspector || "")}" autocomplete="off">
          </label>
          <label>
            <span>위치</span>
            <input data-enforcement-location value="${escapeHtml(row.location || "")}" autocomplete="off">
          </label>
          <label>
            <span>메모</span>
            <input data-enforcement-memo value="${escapeHtml(row.memo || "")}" autocomplete="off">
          </label>
        </div>
        <div class="user-action-row">
          <button type="button" class="secondary-btn" data-enforcement-save>수정 저장</button>
          <button type="button" class="danger-btn" data-enforcement-delete>삭제</button>
        </div>
      </article>
    `)
    .join("");
  if (append) {
    recentResults.insertAdjacentHTML("beforeend", markup);
  } else {
    recentResults.innerHTML = markup;
  }
  attachResultClickHandlers(recentResults);
  attachEnforcementCrudHandlers(recentResults);
}

function enforcementRowPayload(row) {
  return {
    plate: row.querySelector("[data-enforcement-plate]")?.value.trim() || "",
    inspector: row.querySelector("[data-enforcement-inspector]")?.value.trim() || "",
    location: row.querySelector("[data-enforcement-location]")?.value.trim() || "",
    memo: row.querySelector("[data-enforcement-memo]")?.value.trim() || "",
  };
}

function attachEnforcementCrudHandlers(root) {
  root.querySelectorAll("[data-enforcement-save]").forEach((button) => {
    button.addEventListener("click", () => saveEnforcementRow(button).catch((error) => alert(error.message)));
  });
  root.querySelectorAll("[data-enforcement-delete]").forEach((button) => {
    button.addEventListener("click", () => deleteEnforcementRow(button).catch((error) => alert(error.message)));
  });
}

async function saveEnforcementRow(button) {
  const row = button.closest("[data-enforcement-row]");
  if (!row) return;
  const eventId = row.dataset.enforcementRow;
  const payload = enforcementRowPayload(row);
  if (!payload.plate) {
    alert("차량번호를 입력해 주세요.");
    return;
  }

  setStatus(`단속 기록 #${eventId} 수정 중`, "active");
  await fetchJson(apiUrl(`/api/enforcement/events/${encodeURIComponent(eventId)}`), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  await loadRecent();
  setStatus(`단속 기록 #${eventId} 수정 완료`, "success");
}

async function deleteEnforcementRow(button) {
  const row = button.closest("[data-enforcement-row]");
  if (!row) return;
  const eventId = row.dataset.enforcementRow;
  const plate = row.querySelector("[data-enforcement-plate]")?.value.trim() || "";
  if (!confirm(`${plate || `#${eventId}`} 단속 기록을 삭제하시겠습니까?`)) {
    return;
  }

  setStatus(`단속 기록 #${eventId} 삭제 중`, "active");
  await fetchJson(apiUrl(`/api/enforcement/events/${encodeURIComponent(eventId)}`), { method: "DELETE" });
  await loadRecent();
  setStatus(`단속 기록 #${eventId} 삭제 완료`, "success");
}

function enforcementExportTableMarkup(rows) {
  if (!rows?.length) {
    return '<div class="empty-state export-empty">출력할 단속 기록이 없습니다.</div>';
  }
  return `
    <table class="export-table">
      <thead>
        <tr>
          <th>장소(층)</th>
          <th>단속시간</th>
          <th>차량번호</th>
          <th>위반내용</th>
          <th>연락처&위치</th>
          <th>경고장</th>
          <th>문자</th>
          <th>통화</th>
          <th>동호수</th>
          <th>차주</th>
          <th>단속자</th>
          <th>판정</th>
        </tr>
      </thead>
      <tbody>
        ${rows
          .map((row) => {
            const contactLocation = [row.phone, row.location].filter(Boolean).join(" / ");
            return `
              <tr>
                <td>${escapeHtml(row.location || "")}</td>
                <td>${escapeHtml(displayDateTime(row.created_at))}</td>
                <td>${escapeHtml(row.plate || "")}</td>
                <td>${escapeHtml(row.memo || row.verdict_message || "")}</td>
                <td>${escapeHtml(contactLocation)}</td>
                <td></td>
                <td></td>
                <td></td>
                <td>${escapeHtml(row.unit || "")}</td>
                <td>${escapeHtml(row.owner_name || "")}</td>
                <td>${escapeHtml(row.inspector || "")}</td>
                <td>${escapeHtml(row.verdict || "")}</td>
              </tr>
            `;
          })
          .join("")}
      </tbody>
    </table>
  `;
}

function renderExportPreview(data) {
  exportRows = Array.isArray(data.items) ? data.items : [];
  exportTruncated = Boolean(data.truncated);
  const countText = `${formatCount(exportRows.length)}건`;
  const truncatedText = exportTruncated ? ` · 최대 ${formatCount(data.limit || exportRows.length)}건까지만 표시됩니다.` : "";
  if (exportSummary) {
    exportSummary.textContent = `${data.site_name || currentSiteName || "-"} (${data.site_code || currentSiteCode || "-"}) · 출력 대상 ${countText}${truncatedText}`;
  }
  if (exportPreview) {
    exportPreview.innerHTML = enforcementExportTableMarkup(exportRows);
  }
  if (exportPdfBtn) exportPdfBtn.disabled = !exportRows.length;
  if (exportExcelBtn) exportExcelBtn.disabled = !exportRows.length;
}

async function openExportPreview() {
  if (!exportModal) return;
  exportModal.hidden = false;
  exportRows = [];
  if (exportSummary) exportSummary.textContent = "출력할 기록을 불러오는 중입니다.";
  if (exportPreview) exportPreview.innerHTML = "";
  if (exportPdfBtn) exportPdfBtn.disabled = true;
  if (exportExcelBtn) exportExcelBtn.disabled = true;

  const params = historyExportParams();
  params.set("limit", "1000");
  const data = await fetchJson(`${apiUrl("/api/enforcement/export/rows")}?${params.toString()}`);
  renderExportPreview(data);
}

function closeExportPreview() {
  if (exportModal) {
    exportModal.hidden = true;
  }
}

function printExportPdf() {
  if (!exportRows.length) {
    alert("출력할 단속 기록이 없습니다.");
    return;
  }
  const printWindow = window.open("", "_blank");
  if (!printWindow) {
    alert("팝업이 차단되어 PDF 미리보기를 열지 못했습니다. 브라우저 팝업 허용 후 다시 시도하세요.");
    return;
  }
  const generatedAt = displayDateTime(new Date().toISOString());
  printWindow.document.write(`
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <title>불법주차단속대장</title>
      <style>
        body { font-family: "Malgun Gothic", "Noto Sans KR", sans-serif; color: #111; margin: 24px; }
        h1 { text-align: center; margin: 0 0 10px; font-size: 24px; }
        .meta { display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 12px; }
        table { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 11px; }
        th, td { border: 1px solid #555; padding: 6px 5px; vertical-align: middle; word-break: break-word; }
        th { background: #eef3f0; text-align: center; }
        @page { size: A4 landscape; margin: 12mm; }
      </style>
    </head>
    <body>
      <h1>불법주차단속대장</h1>
      <div class="meta">
        <span>${escapeHtml(currentSiteName || currentSiteCode || "-")}</span>
        <span>출력일 ${escapeHtml(generatedAt)} · ${escapeHtml(formatCount(exportRows.length))}건</span>
      </div>
      ${enforcementExportTableMarkup(exportRows)}
      <script>window.onload = () => { window.print(); };</script>
    </body>
    </html>
  `);
  printWindow.document.close();
}

function downloadExportExcel() {
  const params = historyExportParams();
  window.location.href = `${apiUrl("/api/enforcement/export.xlsx")}?${params.toString()}`;
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
      <div class="subtle">수동 등록/수정 차량: ${escapeHtml(status.manual_vehicle_count || 0)}대</div>
      <div class="subtle">AI 학습 누적: ${escapeHtml(learning.total_feedback || 0)}건 / 사용자 교정: ${escapeHtml(learning.corrected_feedback || 0)}건</div>
      <div class="subtle">${lastFeedback ? `최근 학습: ${escapeHtml(lastFeedback.suggested_plate || "-")} → ${escapeHtml(lastFeedback.corrected_plate || "-")} (${escapeHtml(lastFeedback.created_at || "-")})` : "아직 OCR 학습 이력이 없습니다."}</div>
    </div>
    <div class="import-file-list">${fileMarkup}</div>
  `;
  renderVehicleBackups(status.backups || []);
}

function vehiclePayloadFromRow(row) {
  return {
    plate: row.querySelector("[data-vehicle-plate]")?.value.trim() || "",
    unit: row.querySelector("[data-vehicle-unit]")?.value.trim() || "",
    owner_name: row.querySelector("[data-vehicle-owner]")?.value.trim() || "",
    phone: row.querySelector("[data-vehicle-phone]")?.value.trim() || "",
    status: row.querySelector("[data-vehicle-status]")?.value.trim() || "active",
    note: row.querySelector("[data-vehicle-note]")?.value.trim() || "",
  };
}

function renderVehicleList(data) {
  if (!vehicleList) return;
  const rows = Array.isArray(data?.items) ? data.items : [];
  if (!rows.length) {
    vehicleList.className = "list-board empty-state";
    vehicleList.textContent = data?.message || "조회된 등록차량이 없습니다.";
    return;
  }
  vehicleList.className = "list-board";
  const canManage = Boolean(data.can_manage);
  const row = rows[0];
  vehicleList.innerHTML = `
      <article class="result-item vehicle-item" data-vehicle-row="${escapeHtml(row.plate || "")}">
        <div class="result-top">
          <div>
            <div class="result-title">${escapeHtml(row.plate || "-")}</div>
            <div class="subtle">${escapeHtml(row.owner_name || "-")} / ${escapeHtml(row.unit || "-")}</div>
          </div>
          <span class="result-badge ${row.manual_override ? "badge-temp" : "badge-ok"}">${row.manual_override ? "수동" : "Excel"}</span>
        </div>
        <div class="enforcement-edit-grid">
          <label><span>차량번호</span><input data-vehicle-plate value="${escapeHtml(row.plate || "")}" ${canManage ? "" : "disabled"}></label>
          <label><span>동호수</span><input data-vehicle-unit value="${escapeHtml(row.unit || "")}" ${canManage ? "" : "disabled"}></label>
          <label><span>차주</span><input data-vehicle-owner value="${escapeHtml(row.owner_name || "")}" ${canManage ? "" : "disabled"}></label>
          <label><span>연락처</span><input data-vehicle-phone value="${escapeHtml(row.phone || "")}" ${canManage ? "" : "disabled"}></label>
          <label><span>상태</span><input data-vehicle-status value="${escapeHtml(row.status || "active")}" ${canManage ? "" : "disabled"}></label>
          <label><span>비고</span><input data-vehicle-note value="${escapeHtml(row.note || "")}" ${canManage ? "" : "disabled"}></label>
        </div>
        ${canManage ? `
          <div class="user-action-row">
            <button type="button" class="secondary-btn" data-vehicle-save>수정 저장</button>
            <button type="button" class="danger-btn" data-vehicle-delete>삭제</button>
          </div>
        ` : ""}
      </article>
    `;
  vehicleList.querySelectorAll("[data-vehicle-save]").forEach((button) => {
    button.addEventListener("click", () => saveVehicleRow(button).catch((error) => alert(error.message)));
  });
  vehicleList.querySelectorAll("[data-vehicle-delete]").forEach((button) => {
    button.addEventListener("click", () => deleteVehicleRow(button).catch((error) => alert(error.message)));
  });
}

function renderVehicleBackups(backups) {
  if (!vehicleBackupList) return;
  if (!backups?.length) {
    vehicleBackupList.className = "status-board empty-state";
    vehicleBackupList.textContent = "아직 등록차량 DB 백업이 없습니다.";
    return;
  }
  vehicleBackupList.className = "status-board";
  vehicleBackupList.innerHTML = backups
    .map((backup) => `
      <div class="import-file-item" data-vehicle-backup="${escapeHtml(backup.id)}">
        <strong>${escapeHtml(backup.backup_name || `백업 #${backup.id}`)}</strong>
        <span>${escapeHtml(backup.vehicles_count || 0)}대 · ${escapeHtml(displayDateTime(backup.created_at))}</span>
        <button type="button" class="ghost-btn" data-vehicle-restore>복구</button>
      </div>
    `)
    .join("");
  vehicleBackupList.querySelectorAll("[data-vehicle-restore]").forEach((button) => {
    button.addEventListener("click", () => restoreVehicleBackup(button).catch((error) => alert(error.message)));
  });
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
                ${user.can_manage_vehicles ? '<span class="self-chip">DB 권한</span>' : ""}
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
            <label class="inline-check">
              <input type="checkbox" data-user-vehicle-manager ${user.can_manage_vehicles ? "checked" : ""}>
              <span>등록차량 DB 접근/관리 권한</span>
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

function displayDateTimeInputValue(value) {
  const text = String(value || "").replace(" ", "T");
  return text.slice(0, 16);
}

function displayDateTimeRange(startValue, endValue) {
  const start = displayDateTime(startValue);
  const end = displayDateTime(endValue);
  if (start === end) {
    return start;
  }
  return `${start} ~ ${end}`;
}

function formatCount(value) {
  return Number(value || 0).toLocaleString("ko-KR");
}

function formatLimit(value) {
  const limit = Number(value || 0);
  return limit > 0 ? formatCount(limit) : "무제한";
}

function billingMetricLabel(metric) {
  return {
    users: "사용자",
    vehicles: "등록차량",
    monthly_records: "월 단속기록",
    monthly_cctv: "월 CCTV 요청",
  }[metric] || metric;
}

function playBillingBridge() {
  return window.ParkingBilling && typeof window.ParkingBilling.purchase === "function" ? window.ParkingBilling : null;
}

function playBillingActionMarkup(plan, isCurrent, playBillingRequired) {
  if (!playBillingRequired) {
    return "";
  }
  const productId = plan.google_play_product_id || "";
  if (isCurrent) {
    return '<div class="subtle">현재 적용 중인 Google Play 구독입니다.</div>';
  }
  if (!productId) {
    return '<div class="subtle">Google Play 상품 ID가 설정되지 않았습니다.</div>';
  }
  if (!playBillingBridge()) {
    return '<div class="subtle">Android 앱에서 로그인하면 Google Play 구독 버튼이 표시됩니다.</div>';
  }
  return `<button type="button" class="primary-btn billing-play-btn" data-play-subscribe="${escapeHtml(productId)}">Google Play 구독</button>`;
}

function attachPlayBillingHandlers(root = document) {
  root.querySelectorAll("[data-play-subscribe]").forEach((button) => {
    button.addEventListener("click", () => {
      const bridge = playBillingBridge();
      if (!bridge) {
        alert("Google Play 결제는 Android 앱에서 사용할 수 있습니다.");
        return;
      }
      const productId = button.dataset.playSubscribe || "";
      setStatus("Google Play 구독 화면을 여는 중", "active");
      bridge.purchase(productId, `${currentSiteCode || "site"}:${currentUsername || "user"}`);
    });
  });
}

async function verifyPlayPurchase(productId, purchaseToken) {
  if (!productId || !purchaseToken) {
    alert("Google Play 구매 정보를 확인할 수 없습니다.");
    return;
  }
  setStatus("Google Play 구독 검증 중", "active");
  const data = await fetchJson(apiUrl("/api/billing/google-play/verify"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      product_id: productId,
      purchase_token: purchaseToken,
    }),
  });
  renderBillingStatus(data.billing_status);
  setStatus(data.entitlement_active ? "Google Play 구독 적용 완료" : "구독 상태 확인 필요", data.entitlement_active ? "success" : "warn");
}

window.handleParkingPlayPurchase = (productId, purchaseToken) => {
  verifyPlayPurchase(productId, purchaseToken).catch((error) => alert(error.message));
};

window.handleParkingPlayBillingError = (message) => {
  alert(message || "Google Play 결제 처리 중 오류가 발생했습니다.");
};

window.addEventListener("parkingPlayPurchase", (event) => {
  const detail = event.detail || {};
  verifyPlayPurchase(detail.productId, detail.purchaseToken).catch((error) => alert(error.message));
});

function renderBillingStatus(status) {
  if (!billingStatus) return;
  const billing = status?.billing || {};
  const currentPlan = status?.current_plan || {};
  const usage = status?.usage || {};
  const planCode = currentPlan.code || billing.plan || "trial";
  const metrics = ["users", "vehicles", "monthly_records", "monthly_cctv"];
  const usageMarkup = metrics
    .map((metric) => {
      const limit = currentPlan[`${metric}_limit`];
      const used = Number(usage[metric] || 0);
      const limitNumber = Number(limit || 0);
      const percent = limitNumber > 0 ? Math.min(100, Math.round((used / limitNumber) * 100)) : 0;
      return `
        <div class="billing-usage-row">
          <div>
            <strong>${escapeHtml(billingMetricLabel(metric))}</strong>
            <span>${escapeHtml(formatCount(used))} / ${escapeHtml(formatLimit(limit))}</span>
          </div>
          <div class="billing-meter" aria-hidden="true"><span style="width: ${percent}%"></span></div>
        </div>
      `;
    })
    .join("");
  const plans = Array.isArray(status?.plans) ? status.plans : [];
  const planMarkup = plans
    .map((plan) => {
      const isCurrent = plan.code === planCode;
      return `
        <article class="billing-plan-card ${isCurrent ? "is-current" : ""}">
          <div class="result-top">
            <strong>${escapeHtml(plan.name)}</strong>
            <span class="result-badge ${isCurrent ? "badge-ok" : "badge-idle"}">${isCurrent ? "현재" : "선택 가능"}</span>
          </div>
          <div class="billing-price">${escapeHtml(plan.display_price || "-")}</div>
          <div class="subtle">사용자 ${escapeHtml(formatLimit(plan.users_limit))}명 · 차량 ${escapeHtml(formatLimit(plan.vehicles_limit))}대</div>
          <div class="subtle">단속 ${escapeHtml(formatLimit(plan.monthly_records_limit))}건/월 · CCTV ${escapeHtml(formatLimit(plan.monthly_cctv_limit))}건/월</div>
          <div class="subtle">${escapeHtml(plan.support || "-")}</div>
          ${playBillingActionMarkup(plan, isCurrent, Boolean(status?.play_billing_required))}
        </article>
      `;
    })
    .join("");
  const inquiries = Array.isArray(status?.latest_inquiries) ? status.latest_inquiries : [];
  const inquiryMarkup = inquiries.length
    ? inquiries
        .map((item) => `
          <div class="billing-inquiry-row">
            <strong>${escapeHtml(item.requested_plan || "-")}</strong>
            <span>${escapeHtml(item.contact_name || item.contact_phone || item.contact_email || "-")}</span>
            <span>${escapeHtml(displayDateTime(item.created_at))}</span>
          </div>
        `)
        .join("")
    : '<div class="subtle">등록된 업그레이드 문의가 없습니다.</div>';
  const trialText = billing.trial_days_remaining !== null && billing.trial_days_remaining !== undefined
    ? ` · 체험 ${escapeHtml(billing.trial_days_remaining)}일 남음`
    : "";
  const paymentNotice = status?.play_billing_required
    ? "Google Play 출시 앱에서 디지털 구독을 판매할 때는 Play 결제 연동 모드로 운영합니다."
    : status?.sales_contact_url
      ? `<a class="contact-action" href="${escapeHtml(status.sales_contact_url)}" target="_blank" rel="noopener">상담 링크 열기</a>`
      : "문의 등록 후 운영자가 결제 안내를 진행합니다.";

  billingStatus.className = "status-board billing-board";
  billingStatus.innerHTML = `
    <div class="result-item">
      <div class="result-top">
        <div>
          <div class="result-title">${escapeHtml(status?.site_name || currentSiteName || "-")}</div>
          <div class="subtle">${escapeHtml(status?.site_code || currentSiteCode || "-")} · ${escapeHtml(billing.status_label || "-")}${trialText}</div>
        </div>
        <span class="result-badge badge-ok">${escapeHtml(billing.plan_label || currentPlan.name || "-")}</span>
      </div>
      <div class="billing-price">${escapeHtml(currentPlan.display_price || "-")}</div>
      <div class="subtle">${paymentNotice}</div>
    </div>
    <div class="billing-usage-grid">${usageMarkup}</div>
    <div class="billing-plan-grid">${planMarkup}</div>
    <div class="billing-inquiry-list">
      <strong>최근 문의</strong>
      ${inquiryMarkup}
    </div>
  `;
  attachPlayBillingHandlers(billingStatus);
}

function toDateTimeLocal(date) {
  const pad = (value) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function historyRangeValues() {
  const range = historyRangeInput?.value || "";
  const now = new Date();
  if (range === "today") {
    const start = new Date(now);
    start.setHours(0, 0, 0, 0);
    const end = new Date(now);
    end.setHours(23, 59, 59, 999);
    return { dateFrom: toDateTimeLocal(start), dateTo: toDateTimeLocal(end) };
  }
  if (range === "7d") {
    const start = new Date(now);
    start.setDate(start.getDate() - 7);
    start.setHours(0, 0, 0, 0);
    return { dateFrom: toDateTimeLocal(start), dateTo: toDateTimeLocal(now) };
  }
  if (range === "custom") {
    return {
      dateFrom: historyDateFromInput?.value.trim() || "",
      dateTo: historyDateToInput?.value.trim() || "",
    };
  }
  return { dateFrom: "", dateTo: "" };
}

function historyExportParams() {
  const { dateFrom, dateTo } = historyRangeValues();
  const params = new URLSearchParams();
  const q = historyQueryInput?.value.trim() || "";
  const verdict = historyVerdictInput?.value || "";
  if (q) params.set("q", q);
  if (verdict) params.set("verdict", verdict);
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);
  return params;
}

function syncHistoryRangeState() {
  const isCustom = historyRangeInput?.value === "custom";
  document.querySelector(".history-custom-range")?.classList.toggle("is-visible", isCustom);
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
          <div class="cctv-edit-grid">
            <label>
              <span>위치</span>
              <input data-cctv-location value="${escapeHtml(row.location || "")}" autocomplete="off">
            </label>
            <label>
              <span>시작 시간</span>
              <input data-cctv-start-time type="datetime-local" value="${escapeHtml(displayDateTimeInputValue(row.search_start_time || row.search_time))}">
            </label>
            <label>
              <span>끝 시간</span>
              <input data-cctv-end-time type="datetime-local" value="${escapeHtml(displayDateTimeInputValue(row.search_end_time || row.search_time))}">
            </label>
            <label class="cctv-edit-content">
              <span>내용</span>
              <textarea data-cctv-content rows="2">${escapeHtml(row.content || "")}</textarea>
            </label>
          </div>
          ${renderCctvAdminControls(row)}
          <div class="user-action-row">
            <button type="button" class="secondary-btn" data-cctv-save>수정 저장</button>
            ${currentCanAssignCctv || row.requester_username === currentUsername ? '<button type="button" class="danger-btn" data-cctv-delete>삭제</button>' : ""}
          </div>
        </article>
      `;
    })
    .join("");

  cctvRequestList.querySelectorAll("[data-cctv-save]").forEach((button) => {
    button.addEventListener("click", () => saveCctvAssignment(button).catch((error) => alert(error.message)));
  });
  cctvRequestList.querySelectorAll("[data-cctv-delete]").forEach((button) => {
    button.addEventListener("click", () => deleteCctvRequest(button).catch((error) => alert(error.message)));
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

function nativeOcrAvailable() {
  try {
    return Boolean(window.ParkingNativeOcr?.isAvailable?.());
  } catch (_) {
    return false;
  }
}

function resolveNativeOcrWaiters(payload) {
  const waiters = nativeOcrWaiters;
  nativeOcrWaiters = [];
  waiters.forEach((resolve) => resolve(payload || null));
}

window.handleNativePlateOcr = (payload) => {
  latestNativeOcr = payload && typeof payload === "object" ? payload : null;
  if (latestNativeOcr?.candidates?.length) {
    renderCandidates(latestNativeOcr.candidates);
    const elapsed = Number(latestNativeOcr.elapsed_ms || 0);
    setStatus(`휴대폰 OCR 후보 ${latestNativeOcr.candidates.length}개 감지${elapsed ? ` · ${elapsed}ms` : ""}`, "active");
  }
  updateOcrLearningPanel();
  resolveNativeOcrWaiters(latestNativeOcr);
};

function waitForNativeOcr(timeoutMs = 1400) {
  if (!nativeOcrAvailable()) {
    return Promise.resolve(null);
  }
  if (latestNativeOcr?.raw_text || latestNativeOcr?.candidates?.length || latestNativeOcr?.error) {
    return Promise.resolve(latestNativeOcr);
  }
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      nativeOcrWaiters = nativeOcrWaiters.filter((waiter) => waiter !== done);
      resolve(null);
    }, timeoutMs);
    const done = (payload) => {
      clearTimeout(timer);
      resolve(payload || null);
    };
    nativeOcrWaiters.push(done);
  });
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
  if (scanAttemptCount > 2) {
    plateInput.focus();
    await runCheck();
    return;
  }
  if (!photoInput.files?.length) {
    if (plateInput.value.trim()) {
      await runCheck();
      return;
    }
    alert("사진을 선택하거나 차량번호를 직접 입력해 주세요.");
    return;
  }

  setStatus(nativeOcrAvailable() ? "휴대폰 OCR 판독 중" : "번호판 OCR 판독 중", "active");
  const nativeOcr = await waitForNativeOcr();
  const formData = new FormData();
  formData.append("photo", photoInput.files[0]);
  formData.append("manual_plate", plateInput.value.trim());
  if (nativeOcr?.raw_text || nativeOcr?.candidates?.length) {
    formData.append("client_ocr_provider", nativeOcr.provider || "android-mlkit");
    formData.append("client_ocr_raw_text", nativeOcr.raw_text || "");
    formData.append("client_ocr_candidates", JSON.stringify(nativeOcr.candidates || []));
    setStatus("휴대폰 OCR 결과로 등록차량 DB 조회 중", "active");
  } else if (nativeOcr?.error) {
    geoStatus.textContent = nativeOcr.error;
  }

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
    if (scanAttemptCount >= 2 && result.match.verdict === "UNREGISTERED") {
      plateInput.focus();
      setStatus("2회 촬영 후 미등록입니다. 직접 조회로 전환합니다.", "danger");
      await runCheck();
      setStatus("2회 촬영 후 미등록입니다. 차량번호를 확인해 직접 조회하세요.", "danger");
    }
  } else {
    setStatus("후보를 확인해 수동 선택해 주세요.", "warn");
  }
  if (result.error) {
    geoStatus.textContent = result.error;
  } else if (result.server_ocr_used) {
    geoStatus.textContent = "휴대폰 OCR 후보가 없어 서버 보조 OCR을 사용했습니다.";
  }
  updateOcrLearningPanel();
}

function vibrate(pattern) {
  if (navigator.vibrate) {
    navigator.vibrate(pattern);
  }
}

function resetWorkflow() {
  photoInput.value = "";
  latestNativeOcr = null;
  resolveNativeOcrWaiters(null);
  scanAttemptCount = 0;
  updateCaptureLimitState();
  updatePreview(null);
  plateInput.value = "";
  memoInput.value = "";
  latestRawText = "";
  ocrRaw.hidden = true;
  ocrRaw.textContent = "";
  renderCandidates([]);
  renderIdleVerdict();
  syncQuickMemoState();
  updateOcrLearningPanel();
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

  const saved = await fetchJson(apiUrl("/api/enforcement/submit"), { method: "POST", body: formData });
  await loadRecent();
  vibrate([80, 40, 80]);
  resetWorkflow();
  const learning = saved.ocr_learning_feedback || {};
  if (learning.recorded && learning.corrected) {
    setStatus("기록 저장 완료 · 교정값이 OCR 학습에 반영됐습니다.", "success");
  } else if (learning.recorded) {
    setStatus("기록 저장 완료 · 확인값이 OCR 학습에 반영됐습니다.", "success");
  } else {
    setStatus("기록 저장 완료", "success");
  }
}

async function searchRegistry() {
  const q = document.getElementById("search-query").value.trim();
  const data = await fetchJson(`${apiUrl("/api/registry/search")}?q=${encodeURIComponent(q)}`);
  renderSearchResults(data);
}

async function loadRecent({ append = false } = {}) {
  if (!recentResults) return;
  const offset = append ? historyOffset : 0;
  const params = historyExportParams();
  params.set("limit", String(HISTORY_PAGE_SIZE));
  params.set("offset", String(offset));

  const data = await fetchJson(`${apiUrl("/api/enforcement/history")}?${params.toString()}`);
  const rows = Array.isArray(data.items) ? data.items : [];
  renderRecent(rows, append);
  historyOffset = append ? historyOffset + rows.length : rows.length;
  historyHasMore = Boolean(data.has_more);
  if (historyLoadMoreBtn) {
    historyLoadMoreBtn.hidden = !historyHasMore;
  }
}

async function loadRegistryStatus() {
  if (!registryStatus) return;
  const data = await fetchJson(apiUrl("/api/registry/status"));
  renderRegistryStatus(data);
}

async function loadVehicleBackups() {
  if (!vehicleBackupList || !currentCanManageVehicles) return;
  const data = await fetchJson(apiUrl("/api/registry/backups"));
  renderVehicleBackups(data);
}

async function syncRegistry() {
  setStatus("Excel 등록차량 동기화 중", "active");
  await fetchJson(apiUrl("/api/registry/sync"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preserve_manual: registryPreserveManualInput?.checked !== false }),
  });
  await loadRegistryStatus();
  await searchRegistry();
  await loadVehicles();
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
    const params = new URLSearchParams({ preserve_manual: registryPreserveManualInput?.checked === false ? "0" : "1" });
    result = await fetchJson(`${apiUrl("/api/registry/upload")}?${params.toString()}`, { method: "POST", body: formData });
  } catch (error) {
    setRegistryFileNote(`업로드 실패:\n${error.message || error}`, "error");
    setStatus("Excel 업로드 실패", "danger");
    throw error;
  }
  registryFileInput.value = "";
  renderRegistrySelection();
  await loadRegistryStatus();
  await searchRegistry();
  await loadVehicles();
  setStatus(`${result.saved_count}개 Excel 업로드 및 동기화 완료`, "success");
}

async function loadVehicles() {
  if (!vehicleList) return;
  const q = vehicleQueryInput?.value.trim() || "";
  if (!q) {
    renderVehicleList({ items: [], message: "조회할 차량번호, 동호수, 차주 또는 연락처를 입력해 주세요." });
    return;
  }
  const params = new URLSearchParams({ q });
  const data = await fetchJson(`${apiUrl("/api/registry/vehicles")}?${params.toString()}`);
  renderVehicleList(data);
}

async function createVehicle() {
  if (!vehicleNewPlateInput) return;
  const payload = {
    plate: vehicleNewPlateInput.value.trim(),
    unit: vehicleNewUnitInput?.value.trim() || "",
    owner_name: vehicleNewOwnerInput?.value.trim() || "",
    phone: vehicleNewPhoneInput?.value.trim() || "",
    status: "active",
    note: "수동 등록",
  };
  if (!payload.plate) {
    alert("차량번호를 입력해 주세요.");
    return;
  }
  setStatus("등록차량 수동 등록 중", "active");
  await fetchJson(apiUrl("/api/registry/vehicles"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  vehicleNewPlateInput.value = "";
  if (vehicleNewUnitInput) vehicleNewUnitInput.value = "";
  if (vehicleNewOwnerInput) vehicleNewOwnerInput.value = "";
  if (vehicleNewPhoneInput) vehicleNewPhoneInput.value = "";
  if (vehicleQueryInput) vehicleQueryInput.value = payload.plate;
  await loadRegistryStatus();
  await loadVehicles();
  setStatus("등록차량 수동 등록 완료", "success");
}

async function saveVehicleRow(button) {
  const row = button.closest("[data-vehicle-row]");
  if (!row) return;
  const originalPlate = row.dataset.vehicleRow || "";
  const payload = vehiclePayloadFromRow(row);
  if (!payload.plate) {
    alert("차량번호를 입력해 주세요.");
    return;
  }
  setStatus(`${originalPlate} 등록차량 수정 중`, "active");
  await fetchJson(apiUrl(`/api/registry/vehicles/${encodeURIComponent(originalPlate)}`), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  await loadRegistryStatus();
  await loadVehicles();
  setStatus(`${payload.plate} 등록차량 수정 완료`, "success");
}

async function deleteVehicleRow(button) {
  const row = button.closest("[data-vehicle-row]");
  if (!row) return;
  const plate = row.dataset.vehicleRow || "";
  if (!confirm(`${plate} 등록차량을 삭제하시겠습니까?`)) return;
  setStatus(`${plate} 등록차량 삭제 중`, "active");
  await fetchJson(apiUrl(`/api/registry/vehicles/${encodeURIComponent(plate)}`), { method: "DELETE" });
  await loadRegistryStatus();
  await loadVehicles();
  setStatus(`${plate} 등록차량 삭제 완료`, "success");
}

async function createVehicleBackup() {
  setStatus("등록차량 DB 백업 중", "active");
  await fetchJson(apiUrl("/api/registry/backups"), { method: "POST" });
  await loadRegistryStatus();
  await loadVehicleBackups();
  setStatus("등록차량 DB 백업 완료", "success");
}

async function restoreVehicleBackup(button) {
  const row = button.closest("[data-vehicle-backup]");
  if (!row) return;
  const backupId = row.dataset.vehicleBackup;
  if (!confirm("현재 등록차량 DB를 백업한 뒤 선택한 백업으로 복구하시겠습니까?")) return;
  setStatus(`등록차량 DB 백업 #${backupId} 복구 중`, "active");
  await fetchJson(apiUrl(`/api/registry/backups/${encodeURIComponent(backupId)}/restore`), { method: "POST" });
  await loadRegistryStatus();
  await loadVehicleBackups();
  await loadVehicles();
  setStatus(`등록차량 DB 백업 #${backupId} 복구 완료`, "success");
}

async function loadSiteSettings() {
  const settings = await fetchJson(apiUrl("/api/site/settings"));
  setCapturePlaceholderImage(settings.capture_placeholder_image_url || "");
  if (capturePlaceholderNote) {
    capturePlaceholderNote.textContent = settings.capture_placeholder_image_url ? "현재 사용자 지정 이미지를 사용 중입니다." : "현재 기본 화면을 사용 중입니다.";
  }
}

function renderCapturePlaceholderSelection() {
  if (!capturePlaceholderInput || !capturePlaceholderNote) return false;
  const file = capturePlaceholderInput.files?.[0];
  if (!file) {
    capturePlaceholderNote.textContent = "현재 기본 화면을 사용 중입니다.";
    return false;
  }
  if (!file.type.startsWith("image/")) {
    capturePlaceholderNote.textContent = "이미지 파일만 선택할 수 있습니다.";
    return false;
  }
  capturePlaceholderNote.textContent = `선택됨: ${file.name}`;
  return true;
}

async function uploadCapturePlaceholderImage() {
  if (!capturePlaceholderInput?.files?.length) {
    alert("촬영 초기화면 이미지를 먼저 선택해 주세요.");
    return;
  }
  if (!renderCapturePlaceholderSelection()) {
    alert(capturePlaceholderNote?.textContent || "이미지 선택 내용을 확인해 주세요.");
    return;
  }

  setStatus("촬영 초기화면 이미지 저장 중", "active");
  const formData = new FormData();
  formData.append("image", capturePlaceholderInput.files[0]);
  const settings = await fetchJson(apiUrl("/api/site/settings/capture-placeholder"), { method: "POST", body: formData });
  capturePlaceholderInput.value = "";
  setCapturePlaceholderImage(settings.capture_placeholder_image_url || "");
  if (capturePlaceholderNote) {
    capturePlaceholderNote.textContent = "촬영 초기화면 이미지 저장 완료";
  }
  setStatus("촬영 초기화면 이미지 저장 완료", "success");
}

async function deleteCapturePlaceholderImage() {
  if (!confirm("촬영 초기화면 이미지를 삭제하고 기본 화면으로 되돌릴까요?")) {
    return;
  }
  setStatus("촬영 초기화면 이미지 삭제 중", "active");
  const settings = await fetchJson(apiUrl("/api/site/settings/capture-placeholder"), { method: "DELETE" });
  if (capturePlaceholderInput) capturePlaceholderInput.value = "";
  setCapturePlaceholderImage(settings.capture_placeholder_image_url || "");
  if (capturePlaceholderNote) {
    capturePlaceholderNote.textContent = "촬영 초기화면 이미지를 삭제했습니다. 현재 기본 화면을 사용 중입니다.";
  }
  setStatus("촬영 초기화면 이미지 삭제 완료", "success");
}

async function loadCctvAssignees() {
  if (!currentCanAssignCctv) return;
  cctvAssignees = await fetchJson(apiUrl("/api/cctv/assignees"));
}

async function loadCctvRequests({ append = false } = {}) {
  if (!cctvRequestList) return;
  const offset = append ? cctvOffset : 0;
  const params = new URLSearchParams({
    limit: String(CCTV_PAGE_SIZE + 1),
    offset: String(offset),
  });
  const data = await fetchJson(`${apiUrl("/api/cctv/requests")}?${params.toString()}`);
  const items = Array.isArray(data) ? data.slice(0, CCTV_PAGE_SIZE) : [];
  cctvRequestRows = append ? [...cctvRequestRows, ...items] : items;
  renderCctvRequests(cctvRequestRows);
  cctvOffset = offset + items.length;
  cctvHasMore = Array.isArray(data) && data.length > CCTV_PAGE_SIZE;
  if (cctvLoadMoreBtn) {
    cctvLoadMoreBtn.hidden = !cctvHasMore;
  }
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
  const location = row.querySelector("[data-cctv-location]")?.value.trim() || "";
  const searchStartTime = row.querySelector("[data-cctv-start-time]")?.value || "";
  const searchEndTime = row.querySelector("[data-cctv-end-time]")?.value || "";
  const content = row.querySelector("[data-cctv-content]")?.value.trim() || "";
  if (!location || !searchStartTime || !searchEndTime || !content) {
    alert("위치, 시작 시간, 끝 시간, 내용을 모두 입력해 주세요.");
    return;
  }
  if (searchEndTime < searchStartTime) {
    alert("끝 시간은 시작 시간 이후로 입력해 주세요.");
    return;
  }

  setStatus(`CCTV 요청 #${requestId} 작업지시 저장 중`, "active");
  const payload = {
    location,
    search_start_time: searchStartTime,
    search_end_time: searchEndTime,
    content,
  };
  if (currentCanAssignCctv) {
    payload.assigned_to = assignee;
    payload.work_weight = workWeight;
    payload.instruction = instruction;
    payload.status = status;
  }
  await fetchJson(apiUrl(`/api/cctv/requests/${encodeURIComponent(requestId)}`), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  await loadCctvRequests();
  setStatus(`CCTV 요청 #${requestId} 수정 완료`, "success");
}

async function deleteCctvRequest(button) {
  const row = button.closest("[data-cctv-row]");
  if (!row) return;
  const requestId = row.dataset.cctvRow;
  const location = row.querySelector("[data-cctv-location]")?.value.trim() || "";
  if (!confirm(`${location || `#${requestId}`} CCTV 요청을 삭제하시겠습니까?`)) {
    return;
  }

  setStatus(`CCTV 요청 #${requestId} 삭제 중`, "active");
  await fetchJson(apiUrl(`/api/cctv/requests/${encodeURIComponent(requestId)}`), { method: "DELETE" });
  await loadCctvRequests();
  setStatus(`CCTV 요청 #${requestId} 삭제 완료`, "success");
}

function contactPayloadFromForm() {
  return {
    category: contactCategoryInput?.value || "internal",
    name: contactNameInput?.value.trim() || "",
    phone: contactPhoneInput?.value.trim() || "",
    duty: contactDutyInput?.value.trim() || "",
    memo: contactMemoInput?.value.trim() || "",
    is_favorite: Boolean(contactFavoriteInput?.checked),
    sort_order: 0,
  };
}

function contactPayloadFromRow(row) {
  return {
    category: row.querySelector("[data-contact-category]")?.value || "internal",
    name: row.querySelector("[data-contact-name]")?.value.trim() || "",
    phone: row.querySelector("[data-contact-phone]")?.value.trim() || "",
    duty: row.querySelector("[data-contact-duty]")?.value.trim() || "",
    memo: row.querySelector("[data-contact-memo]")?.value.trim() || "",
    is_favorite: Boolean(row.querySelector("[data-contact-favorite]")?.checked),
    sort_order: Number(row.querySelector("[data-contact-sort]")?.value || 0),
  };
}

function renderContactAdminEditor(row) {
  if (!currentIsAdmin) {
    return "";
  }
  return `
    <div class="contact-edit-grid">
      <label>
        <span>분류</span>
        <select data-contact-category>${contactCategoryOptionsMarkup(row.category || "internal")}</select>
      </label>
      <label>
        <span>이름</span>
        <input data-contact-name value="${escapeHtml(row.name || "")}" autocomplete="off">
      </label>
      <label>
        <span>연락처</span>
        <input data-contact-phone value="${escapeHtml(row.phone || "")}" inputmode="tel" autocomplete="off">
      </label>
      <label>
        <span>담당업무</span>
        <input data-contact-duty value="${escapeHtml(row.duty || "")}" autocomplete="off">
      </label>
      <label class="contact-edit-wide">
        <span>메모</span>
        <input data-contact-memo value="${escapeHtml(row.memo || "")}">
      </label>
      <label>
        <span>순서</span>
        <input data-contact-sort type="number" min="0" max="9999" value="${escapeHtml(row.sort_order || 0)}">
      </label>
      <label class="checkbox-field contact-row-favorite">
        <input data-contact-favorite type="checkbox" ${row.is_favorite ? "checked" : ""}>
        <span>상단 고정</span>
      </label>
    </div>
    <div class="user-action-row">
      <button type="button" class="secondary-btn" data-contact-save>수정 저장</button>
      <button type="button" class="danger-btn" data-contact-delete>삭제</button>
    </div>
  `;
}

function renderContacts(rows) {
  if (!contactList) return;
  if (!rows?.length) {
    contactList.className = "list-board empty-state";
    contactList.textContent = "등록된 연락처가 없습니다.";
    return;
  }

  contactList.className = "list-board contact-list";
  contactList.innerHTML = rows
    .map((row) => {
      const category = contactCategoryOption(row.category);
      return `
        <article class="result-item contact-item" data-contact-row="${escapeHtml(row.id)}">
          <div class="result-top">
            <div>
              <div class="contact-title-row">
                <span class="result-title">${escapeHtml(row.name || "-")}</span>
                ${row.is_favorite ? '<span class="self-chip">상단</span>' : ""}
              </div>
              <div class="subtle">${escapeHtml(row.duty || "담당업무 미입력")}</div>
            </div>
            <span class="result-badge ${category.badgeClass}">${escapeHtml(row.category_label || category.label)}</span>
          </div>
          <div class="contact-phone-block">${contactActionsMarkup(row.phone)}</div>
          ${row.memo ? `<div class="subtle contact-memo">${escapeHtml(row.memo)}</div>` : ""}
          ${renderContactAdminEditor(row)}
        </article>
      `;
    })
    .join("");
  refreshSmsLinks(contactList);
  contactList.querySelectorAll("[data-contact-save]").forEach((button) => {
    button.addEventListener("click", () => saveContactRow(button).catch((error) => alert(error.message)));
  });
  contactList.querySelectorAll("[data-contact-delete]").forEach((button) => {
    button.addEventListener("click", () => deleteContactRow(button).catch((error) => alert(error.message)));
  });
}

async function loadContacts() {
  if (!contactList) return;
  const params = new URLSearchParams({ limit: "100" });
  const category = contactCategoryFilterInput?.value || "";
  const q = contactQueryInput?.value.trim() || "";
  if (category) params.set("category", category);
  if (q) params.set("q", q);
  const rows = await fetchJson(`${apiUrl("/api/contacts")}?${params.toString()}`);
  renderContacts(Array.isArray(rows) ? rows : []);
}

async function createContact(event) {
  event.preventDefault();
  const payload = contactPayloadFromForm();
  if (!payload.name || !payload.phone) {
    alert("이름과 연락처를 입력해 주세요.");
    return;
  }
  setStatus("연락처 등록 중", "active");
  await fetchJson(apiUrl("/api/contacts"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  contactForm.reset();
  await loadContacts();
  setStatus("연락처 등록 완료", "success");
}

async function saveContactRow(button) {
  const row = button.closest("[data-contact-row]");
  if (!row) return;
  const contactId = row.dataset.contactRow;
  const payload = contactPayloadFromRow(row);
  if (!payload.name || !payload.phone) {
    alert("이름과 연락처를 입력해 주세요.");
    return;
  }
  setStatus("연락처 수정 중", "active");
  await fetchJson(apiUrl(`/api/contacts/${encodeURIComponent(contactId)}`), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  await loadContacts();
  setStatus("연락처 수정 완료", "success");
}

async function deleteContactRow(button) {
  const row = button.closest("[data-contact-row]");
  if (!row) return;
  const contactId = row.dataset.contactRow;
  const name = row.querySelector("[data-contact-name]")?.value || row.querySelector(".result-title")?.textContent || "";
  if (!confirm(`${name || "선택한 연락처"}를 삭제하시겠습니까?`)) {
    return;
  }
  setStatus("연락처 삭제 중", "active");
  await fetchJson(apiUrl(`/api/contacts/${encodeURIComponent(contactId)}`), { method: "DELETE" });
  await loadContacts();
  setStatus("연락처 삭제 완료", "success");
}

async function loadUsers({ append = false } = {}) {
  if (!userList) return;
  const offset = append ? userOffset : 0;
  const params = new URLSearchParams({
    limit: String(USER_PAGE_SIZE + 1),
    offset: String(offset),
  });
  const q = userQueryInput?.value.trim() || "";
  const role = userRoleFilterInput?.value || "";
  if (q) params.set("q", q);
  if (role) params.set("role", role);

  const data = await fetchJson(`${apiUrl("/api/users")}?${params.toString()}`);
  const items = Array.isArray(data) ? data.slice(0, USER_PAGE_SIZE) : [];
  userRows = append ? [...userRows, ...items] : items;
  renderUserList(userRows);
  userOffset = offset + items.length;
  userHasMore = Array.isArray(data) && data.length > USER_PAGE_SIZE;
  if (userLoadMoreBtn) {
    userLoadMoreBtn.hidden = !userHasMore;
  }
}

async function loadSites({ append = false } = {}) {
  if (!siteList) return;
  const offset = append ? siteOffset : 0;
  const params = new URLSearchParams({
    limit: String(SITE_PAGE_SIZE + 1),
    offset: String(offset),
  });
  const q = siteQueryInput?.value.trim() || "";
  if (q) params.set("q", q);

  const data = await fetchJson(`${apiUrl("/api/sites")}?${params.toString()}`);
  const items = Array.isArray(data) ? data.slice(0, SITE_PAGE_SIZE) : [];
  siteRows = append ? [...siteRows, ...items] : items;
  renderSiteList(siteRows);
  siteOffset = offset + items.length;
  siteHasMore = Array.isArray(data) && data.length > SITE_PAGE_SIZE;
  if (siteLoadMoreBtn) {
    siteLoadMoreBtn.hidden = !siteHasMore;
  }
}

async function loadBillingStatus() {
  if (!billingStatus) return;
  const data = await fetchJson(apiUrl("/api/billing/status"));
  renderBillingStatus(data);
}

async function submitBillingInquiry(event) {
  event.preventDefault();
  if (!billingInquiryForm || !billingRequestedPlanInput) return;

  const requestedPlan = billingRequestedPlanInput.value;
  const contactName = billingContactNameInput?.value.trim() || "";
  const contactPhone = billingContactPhoneInput?.value.trim() || "";
  const contactEmail = billingContactEmailInput?.value.trim() || "";
  const message = billingMessageInput?.value.trim() || "";

  if (!contactName && !contactPhone && !contactEmail && !message) {
    alert("연락처 또는 문의 내용을 하나 이상 입력해 주세요.");
    return;
  }

  setStatus("업그레이드 문의 등록 중", "active");
  const data = await fetchJson(apiUrl("/api/billing/inquiries"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      requested_plan: requestedPlan,
      contact_name: contactName || null,
      contact_phone: contactPhone || null,
      contact_email: contactEmail || null,
      message: message || null,
    }),
  });
  billingInquiryForm.reset();
  billingRequestedPlanInput.value = requestedPlan;
  renderBillingStatus(data);
  setStatus("업그레이드 문의 등록 완료", "success");
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
  const canManageVehicles = Boolean(newUserVehicleManagerInput?.checked);

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
    body: JSON.stringify({ username, password, role, can_manage_vehicles: canManageVehicles }),
  });

  newUserUsernameInput.value = "";
  newUserPasswordInput.value = "";
  newUserRoleInput.value = "guard";
  if (newUserVehicleManagerInput) newUserVehicleManagerInput.checked = false;
  await loadUsers();
  await loadBillingStatus();
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
  const canManageVehicles = Boolean(row.querySelector("[data-user-vehicle-manager]")?.checked);

  setStatus(`사용자 ${username} 정보 저장 중`, "active");
  await fetchJson(apiUrl(`/api/users/${encodeURIComponent(username)}`), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      role,
      password: password || null,
      can_manage_vehicles: canManageVehicles,
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
  latestNativeOcr = null;
  resolveNativeOcrWaiters(null);
  if (file) {
    scanAttemptCount += 1;
    updateCaptureLimitState();
  }
  updatePreview(file || null);
  if (file) {
    runScan().catch((error) => alert(error.message));
  } else {
    setStatus("촬영 대기 중", "idle");
  }
});

registryFileInput?.addEventListener("change", renderRegistrySelection);
capturePlaceholderInput?.addEventListener("change", renderCapturePlaceholderSelection);

plateInput?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    runCheck().catch((error) => alert(error.message));
  }
});

plateInput?.addEventListener("input", () => refreshSmsLinks());
plateInput?.addEventListener("input", updateOcrLearningPanel);
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
  button.addEventListener("click", (event) => {
    event.preventDefault();
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
vehicleSearchBtn?.addEventListener("click", () => loadVehicles().catch((error) => alert(error.message)));
vehicleCreateBtn?.addEventListener("click", () => createVehicle().catch((error) => alert(error.message)));
vehicleBackupBtn?.addEventListener("click", () => createVehicleBackup().catch((error) => alert(error.message)));
vehicleQueryInput?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    loadVehicles().catch((error) => alert(error.message));
  }
});
uploadCapturePlaceholderBtn?.addEventListener("click", () => uploadCapturePlaceholderImage().catch((error) => alert(error.message)));
deleteCapturePlaceholderBtn?.addEventListener("click", () => deleteCapturePlaceholderImage().catch((error) => alert(error.message)));
userRefreshBtn?.addEventListener("click", () => loadUsers().catch((error) => alert(error.message)));
siteRefreshBtn?.addEventListener("click", () => loadSites().catch((error) => alert(error.message)));
billingRefreshBtn?.addEventListener("click", () => loadBillingStatus().catch((error) => alert(error.message)));
billingInquiryForm?.addEventListener("submit", (event) => submitBillingInquiry(event).catch((error) => alert(error.message)));
userFilterForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  loadUsers().catch((error) => alert(error.message));
});
userFilterResetBtn?.addEventListener("click", () => {
  userFilterForm?.reset();
  loadUsers().catch((error) => alert(error.message));
});
userLoadMoreBtn?.addEventListener("click", () => loadUsers({ append: true }).catch((error) => alert(error.message)));
siteFilterForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  loadSites().catch((error) => alert(error.message));
});
siteFilterResetBtn?.addEventListener("click", () => {
  siteFilterForm?.reset();
  loadSites().catch((error) => alert(error.message));
});
siteLoadMoreBtn?.addEventListener("click", () => loadSites({ append: true }).catch((error) => alert(error.message)));
cctvRequestForm?.addEventListener("submit", (event) => createCctvRequest(event).catch((error) => alert(error.message)));
cctvRefreshBtn?.addEventListener("click", () => loadCctvRequests().catch((error) => alert(error.message)));
cctvLoadMoreBtn?.addEventListener("click", () => loadCctvRequests({ append: true }).catch((error) => alert(error.message)));
contactForm?.addEventListener("submit", (event) => createContact(event).catch((error) => alert(error.message)));
contactRefreshBtn?.addEventListener("click", () => loadContacts().catch((error) => alert(error.message)));
contactSearchBtn?.addEventListener("click", () => loadContacts().catch((error) => alert(error.message)));
contactCategoryFilterInput?.addEventListener("change", () => loadContacts().catch((error) => alert(error.message)));
contactQueryInput?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    loadContacts().catch((error) => alert(error.message));
  }
});
historyFilterForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  loadRecent().catch((error) => alert(error.message));
});
historyResetBtn?.addEventListener("click", () => {
  if (historyFilterForm) {
    historyFilterForm.reset();
  }
  syncHistoryRangeState();
  loadRecent().catch((error) => alert(error.message));
});
historyRangeInput?.addEventListener("change", syncHistoryRangeState);
historyLoadMoreBtn?.addEventListener("click", () => loadRecent({ append: true }).catch((error) => alert(error.message)));
historyExportPreviewBtn?.addEventListener("click", () => openExportPreview().catch((error) => alert(error.message)));
exportCloseBtn?.addEventListener("click", closeExportPreview);
exportModal?.addEventListener("click", (event) => {
  if (event.target === exportModal) {
    closeExportPreview();
  }
});
exportPdfBtn?.addEventListener("click", printExportPdf);
exportExcelBtn?.addEventListener("click", downloadExportExcel);
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
renderCapturePlaceholderSelection();
setCapturePlaceholderImage("");
updateCaptureLimitState();
renderCandidates([]);
renderIdleVerdict();
setStatus("촬영 대기 중", "idle");
syncHistoryRangeState();
initFirstUseGuide();
initMobileTabs();

loadSiteSettings().catch(() => {});

const isCompactScreen = window.matchMedia("(max-width: 720px)").matches;

if (isCompactScreen) {
  if (activeMobileTab === "recent") {
    loadRecent().catch((error) => {
      recentResults.className = "list-board empty-state";
      recentResults.textContent = error.message;
    });
  }
  if (activeMobileTab === "cctv") {
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
  }
  if (activeMobileTab === "contacts") {
    loadContacts().catch((error) => {
      if (contactList) {
        contactList.className = "list-board empty-state";
        contactList.textContent = error.message;
      }
    });
  }
  if (activeMobileTab === "vehicle-db") {
    loadVehicleBackups().catch(() => {});
  }
  if (activeMobileTab === "admin") {
    loadRegistryStatus().catch(() => {});
    loadBillingStatus().catch(() => {});
    loadUsers().catch(() => {});
    loadSites().catch(() => {});
  }
} else {
  loadRecent().catch((error) => {
    recentResults.className = "list-board empty-state";
    recentResults.textContent = error.message;
  });
  loadRegistryStatus().catch(() => {});
  loadVehicleBackups().catch(() => {});
  loadBillingStatus().catch(() => {});
  loadUsers().catch(() => {});
  loadSites().catch(() => {});
  loadContacts().catch(() => {});
  scheduleBackgroundLoad(() => {
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
  });
}
