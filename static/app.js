const fmtId = (id) => (id ? escapeHtml(id) : "—");

const overlay = () => document.getElementById("overlay");

async function loadLeaderboard() {
  const rows = document.getElementById("rows");
  const podium = document.getElementById("podium");
  const status = document.getElementById("status");

  // Loading skeleton
  rows.innerHTML = Array.from({ length: 8 })
    .map(() => '<div class="skeleton-row"></div>')
    .join("");
  status.innerHTML = "";

  let data;
  try {
    const res = await fetch("/api/leaderboard", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch (err) {
    rows.innerHTML = "";
    podium.innerHTML = "";
    status.innerHTML = `<div class="empty-state"><div class="big">Signal lost</div>Could not reach the leaderboard service. <br/>${escapeHtml(
      err.message
    )}</div>`;
    return;
  }

  render(data, {
    emptyTitle: "No signals yet",
    emptyBody:
      "The leaderboard is empty. Run the scoring batch to populate <code>team_submission.csv</code>.",
  });
}

function render(data, opts = {}) {
  const rows = document.getElementById("rows");
  const podium = document.getElementById("podium");
  const status = document.getElementById("status");
  const candidates = data.candidates || [];

  // Stats
  document.getElementById("stat-count").textContent =
    data.count ?? candidates.length;
  document.getElementById("stat-top").textContent = candidates.length
    ? candidates[0].score
    : "—";

  if (!candidates.length) {
    rows.innerHTML = "";
    podium.innerHTML = "";
    status.innerHTML = `<div class="empty-state"><div class="big">${
      opts.emptyTitle || "No signals yet"
    }</div>${opts.emptyBody || ""}</div>`;
    return;
  }

  status.innerHTML = "";
  renderPodium(podium, candidates.slice(0, 3));
  renderRows(rows, candidates);
}

function renderPodium(container, top) {
  // Visual order: 2nd, 1st, 3rd for a classic podium
  const order = [top[1], top[0], top[2]].filter(Boolean);
  container.innerHTML = order
    .map((c) => {
      const label =
        c.rank === 1 ? "Top Signal" : c.rank === 2 ? "Runner-up" : "Third";
      return `
      <article class="podium-card rank-${c.rank}">
        <div class="medal">${c.rank}</div>
        <div class="podium-id">${fmtId(c.candidate_id)}</div>
        <div class="podium-tag">${label}</div>
        <div class="podium-score"><span class="num">${c.score}</span><span class="max">/ 100</span></div>
        <p class="podium-reason">${truncate(escapeHtml(c.reasoning), 180)}</p>
      </article>`;
    })
    .join("");
}

function renderRows(container, candidates) {
  container.innerHTML = candidates
    .map((c) => {
      const topClass = c.rank <= 3 ? " top" : "";
      const reason = escapeHtml(c.reasoning) || "<em>No reasoning recorded.</em>";
      const width = Math.max(0, Math.min(100, c.score));
      return `
      <div class="row${topClass}">
        <div class="row-rank">${String(c.rank).padStart(2, "0")}</div>
        <div class="row-id">${fmtId(c.candidate_id)}</div>
        <div class="score-pill" style="--w:${width * 0.84}%">${c.score}</div>
        <div class="reason">
          <div class="reason-text">${reason}</div>
          <button class="reason-toggle" type="button">Expand</button>
        </div>
      </div>`;
    })
    .join("");

  // Wire up expand toggles, only show when text is actually clamped
  container.querySelectorAll(".reason").forEach((el) => {
    const textEl = el.querySelector(".reason-text");
    const toggle = el.querySelector(".reason-toggle");
    if (textEl.scrollHeight - textEl.clientHeight < 4) {
      toggle.style.display = "none";
      return;
    }
    toggle.addEventListener("click", () => {
      const expanded = el.classList.toggle("expanded");
      toggle.textContent = expanded ? "Collapse" : "Expand";
    });
  });
}

/* ---------- Sandbox upload ---------- */

function showOverlay(show) {
  const el = overlay();
  if (show) el.removeAttribute("hidden");
  else el.setAttribute("hidden", "");
}

function showBanner(count) {
  const banner = document.getElementById("sandbox-banner");
  document.getElementById("sb-count").textContent = count;
  banner.removeAttribute("hidden");
}

function hideBanner() {
  document.getElementById("sandbox-banner").setAttribute("hidden", "");
}

const MAX_UPLOAD_BYTES = 2 * 1024 * 1024;
const TOO_LARGE_MESSAGE = "File too large. Please upload a sample file under 2MB.";

function showDropError(message) {
  const dz = document.getElementById("dropzone");
  const title = dz && dz.querySelector(".dz-title");
  if (title) title.textContent = message;
  if (dz) dz.classList.add("dz-error");
}

function clearDropError() {
  const dz = document.getElementById("dropzone");
  const title = dz && dz.querySelector(".dz-title");
  if (title) title.innerHTML = 'Drop a <code>.jsonl</code> sample to score live';
  if (dz) dz.classList.remove("dz-error");
}

async function uploadSandbox(file) {
  if (!file) return;
  const status = document.getElementById("status");
  clearDropError();

  // Client-side guard: reject oversized files instantly, never start the
  // overlay, so the UI can't hang waiting on a doomed upload.
  if (file.size > MAX_UPLOAD_BYTES) {
    showOverlay(false);
    showDropError(TOO_LARGE_MESSAGE);
    return;
  }

  showOverlay(true);

  const form = new FormData();
  form.append("file", file);

  let data;
  try {
    const res = await fetch("/api/sandbox_upload", {
      method: "POST",
      body: form,
    });
    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try {
        const body = await res.json();
        if (body.detail) detail = body.detail;
      } catch (_) {}
      // Server-side size rejection (413): surface it on the drop-zone and bail.
      if (res.status === 413) {
        showOverlay(false);
        showDropError(detail || TOO_LARGE_MESSAGE);
        return;
      }
      throw new Error(detail);
    }
    data = await res.json();
  } catch (err) {
    showOverlay(false);
    status.innerHTML = `<div class="empty-state"><div class="big">Upload failed</div>${escapeHtml(
      err.message
    )}</div>`;
    return;
  }

  showOverlay(false);
  showBanner(data.count ?? (data.candidates || []).length);
  render(data, {
    emptyTitle: "No candidates scored",
    emptyBody: "The uploaded file had no valid candidate records.",
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function initSandbox() {
  const dropzone = document.getElementById("dropzone");
  const input = document.getElementById("file-input");
  const uploadBtn = document.getElementById("upload-btn");
  const backBtn = document.getElementById("back-to-live");

  const pick = () => input.click();

  uploadBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    pick();
  });
  dropzone.addEventListener("click", pick);
  dropzone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      pick();
    }
  });

  input.addEventListener("change", () => {
    if (input.files && input.files[0]) {
      uploadSandbox(input.files[0]);
      input.value = ""; // allow re-uploading the same file
    }
  });

  ["dragenter", "dragover"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    })
  );
  dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer?.files?.[0];
    if (file) uploadSandbox(file);
  });

  backBtn.addEventListener("click", () => {
    hideBanner();
    loadLeaderboard();
  });
}

function truncate(str, n) {
  if (!str) return "";
  return str.length > n ? str.slice(0, n).trimEnd() + "…" : str;
}

function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

initSandbox();
loadLeaderboard();
