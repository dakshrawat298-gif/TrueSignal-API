const fmtId = (id) => (id ? escapeHtml(id) : "—");

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
    status.innerHTML = `<div class="empty-state"><div class="big">Signal lost</div>Could not reach the leaderboard service. <br/>${err.message}</div>`;
    return;
  }

  const candidates = data.candidates || [];

  // Stats
  document.getElementById("stat-count").textContent = data.count ?? candidates.length;
  document.getElementById("stat-top").textContent = candidates.length ? candidates[0].score : "—";

  if (!candidates.length) {
    rows.innerHTML = "";
    podium.innerHTML = "";
    status.innerHTML = `<div class="empty-state"><div class="big">No signals yet</div>The leaderboard is empty. Run the scoring batch to populate <code>team_submission.csv</code>.</div>`;
    return;
  }

  renderPodium(podium, candidates.slice(0, 3));
  renderRows(rows, candidates);
}

function renderPodium(container, top) {
  // Visual order: 2nd, 1st, 3rd for a classic podium
  const order = [top[1], top[0], top[2]].filter(Boolean);
  container.innerHTML = order
    .map((c) => {
      const label = c.rank === 1 ? "Top Signal" : c.rank === 2 ? "Runner-up" : "Third";
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

loadLeaderboard();
