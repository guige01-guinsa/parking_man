const rootPath = document.body.dataset.rootPath || "";
const apiUrl = (path) => `${rootPath}${path}`;

const photoInput = document.getElementById("photo");
const plateInput = document.getElementById("plate-input");
const inspectorInput = document.getElementById("inspector");
const locationInput = document.getElementById("location");
const memoInput = document.getElementById("memo");
const candidateList = document.getElementById("candidate-list");
const ocrRaw = document.getElementById("ocr-raw");
const verdictCard = document.getElementById("verdict-card");
const verdictTitle = document.getElementById("verdict-title");
const verdictDetail = document.getElementById("verdict-detail");
const verdictMeta = document.getElementById("verdict-meta");
const recentResults = document.getElementById("recent-results");
const searchResults = document.getElementById("search-results");
const registryStatus = document.getElementById("registry-status");
const geoStatus = document.getElementById("geo-status");

let latestRawText = "";
let latestVerdict = null;
let currentGeo = { lat: null, lng: null };

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
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

function renderVerdict(data) {
  latestVerdict = data;
  verdictCard.className = `verdict-card ${verdictClass(data.verdict)}`;
  verdictCard.querySelector(".verdict-label").textContent = data.verdict;
  verdictTitle.textContent = `${data.plate} · ${data.message}`;
  verdictDetail.textContent = data.owner_name || data.unit ? `${data.owner_name || "-"} / ${data.unit || "-"}` : "차량 등록정보가 없습니다.";

  const meta = [
    ["차량번호", data.plate || "-"],
    ["상태", data.status || "-"],
    ["동호수", data.unit || "-"],
    ["차주", data.owner_name || "-"],
    ["시작일", data.valid_from || "-"],
    ["만료일", data.valid_to || "-"],
  ];
  verdictMeta.innerHTML = meta
    .map(([label, value]) => `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`)
    .join("");
}

function renderCandidates(items) {
  if (!items?.length) {
    candidateList.innerHTML = "";
    return;
  }
  candidateList.innerHTML = items
    .map((candidate) => `<button type="button" class="candidate-chip" data-plate="${escapeHtml(candidate)}">${escapeHtml(candidate)}</button>`)
    .join("");
  candidateList.querySelectorAll("[data-plate]").forEach((button) => {
    button.addEventListener("click", () => {
      plateInput.value = button.dataset.plate || "";
      runCheck();
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
          <span class="result-title">${escapeHtml(row.plate)}</span>
          <span class="result-badge ${badgeClass((row.status || "active").toUpperCase() === "BLOCKED" ? "BLOCKED" : (row.status || "active") === "temp" ? "TEMP" : "OK")}">${escapeHtml(row.status || "active")}</span>
        </div>
        <div>${escapeHtml(row.owner_name || "-")} / ${escapeHtml(row.unit || "-")}</div>
        <div class="subtle">${escapeHtml(row.note || "비고 없음")}</div>
      </article>
    `)
    .join("");
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
          <span class="result-title">${escapeHtml(row.plate)}</span>
          <span class="result-badge ${badgeClass(row.verdict)}">${escapeHtml(row.verdict)}</span>
        </div>
        <div>${escapeHtml(row.verdict_message || "-")}</div>
        <div class="subtle">${escapeHtml(row.location || "-")} · ${escapeHtml(row.inspector || "-")} · ${escapeHtml(row.created_at || "-")}</div>
      </article>
    `)
    .join("");
}

function renderRegistryStatus(status) {
  if (!registryStatus) return;
  const last = status.last_sync;
  registryStatus.innerHTML = `
    <div class="result-item">
      <div class="result-top">
        <span class="result-title">등록차량 ${escapeHtml(status.vehicle_count)}</span>
        <span class="result-badge ${badgeClass(last?.status === "success" ? "OK" : last?.status === "failed" ? "BLOCKED" : "IDLE")}">${escapeHtml(last?.status || "대기")}</span>
      </div>
      <div>폴더: ${escapeHtml(status.import_dir)}</div>
      <div class="subtle">${escapeHtml(last?.message || "아직 동기화 이력이 없습니다.")}</div>
    </div>
  `;
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
  const data = await fetchJson(`${apiUrl("/api/registry/check")}?plate=${encodeURIComponent(plate)}`);
  renderVerdict(data);
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

  const formData = new FormData();
  formData.append("photo", photoInput.files[0]);
  formData.append("manual_plate", plateInput.value.trim());

  const result = await fetchJson(apiUrl("/api/ocr/scan"), { method: "POST", body: formData });
  latestRawText = result.raw_text || "";
  renderCandidates(result.candidates || []);
  ocrRaw.hidden = !latestRawText;
  ocrRaw.textContent = latestRawText;

  if (result.best_plate) {
    plateInput.value = result.best_plate;
  }
  if (result.match) {
    renderVerdict(result.match);
  }
  if (result.error) {
    geoStatus.textContent = result.error;
  }
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

  const formData = new FormData();
  formData.append("plate", plateInput.value.trim());
  formData.append("inspector", inspectorInput.value.trim());
  formData.append("location", locationInput.value.trim());
  formData.append("memo", memoInput.value.trim());
  formData.append("raw_ocr_text", latestRawText);
  if (currentGeo.lat !== null) formData.append("lat", String(currentGeo.lat));
  if (currentGeo.lng !== null) formData.append("lng", String(currentGeo.lng));
  if (photoInput.files?.length) formData.append("photo", photoInput.files[0]);

  await fetchJson(apiUrl("/api/enforcement/submit"), { method: "POST", body: formData });
  await loadRecent();
  alert("단속 기록이 저장되었습니다.");
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
  await fetchJson(apiUrl("/api/registry/sync"), { method: "POST" });
  await loadRegistryStatus();
  await searchRegistry();
  alert("Excel 등록차량 정보를 다시 읽었습니다.");
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

document.getElementById("scan-btn")?.addEventListener("click", () => runScan().catch((error) => alert(error.message)));
document.getElementById("check-btn")?.addEventListener("click", () => runCheck().catch((error) => alert(error.message)));
document.getElementById("save-btn")?.addEventListener("click", () => saveEvent().catch((error) => alert(error.message)));
document.getElementById("search-btn")?.addEventListener("click", () => searchRegistry().catch((error) => alert(error.message)));
document.getElementById("sync-btn")?.addEventListener("click", () => syncRegistry().catch((error) => alert(error.message)));
document.getElementById("geo-btn")?.addEventListener("click", loadGeolocation);
document.getElementById("search-query")?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    searchRegistry().catch((error) => alert(error.message));
  }
});

loadRecent().catch((error) => {
  recentResults.className = "list-board empty-state";
  recentResults.textContent = error.message;
});
loadRegistryStatus().catch(() => {});
