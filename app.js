(function () {
  const searchEl = document.getElementById("search");
  const sourceFiltersEl = document.getElementById("source-filters");
  const sortEl = document.getElementById("sort");
  const jobsBody = document.getElementById("jobs-body");
  const metaEl = document.getElementById("meta");
  const emptyMsg = document.getElementById("empty-msg");

  let allJobs = [];
  let sources = new Set();

  function formatDate(iso) {
    if (!iso) return "—";
    try {
      const d = new Date(iso);
      return d.toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return iso;
    }
  }

  function filterJobs() {
    const query = (searchEl.value || "").trim().toLowerCase();
    const selectedSources = new Set(
      Array.from(document.querySelectorAll(".source-checkbox:checked")).map(
        (c) => c.dataset.source
      )
    );
    let list = allJobs;
    if (query) {
      list = list.filter(
        (j) =>
          (j.title || "").toLowerCase().includes(query) ||
          (j.company || "").toLowerCase().includes(query)
      );
    }
    if (selectedSources.size > 0) {
      list = list.filter((j) => {
        const s = (j.source != null && j.source !== "") ? String(j.source) : "";
        return selectedSources.has(s) || (s === "" && selectedSources.has(""));
      });
    }
    const sortBy = sortEl.value;
    if (sortBy === "posted_date") {
      list = [...list].sort((a, b) => {
        const da = a.posted_date ? new Date(a.posted_date).getTime() : 0;
        const db = b.posted_date ? new Date(b.posted_date).getTime() : 0;
        return db - da;
      });
    } else if (sortBy === "company") {
      list = [...list].sort((a, b) =>
        (a.company || "").localeCompare(b.company || "")
      );
    } else if (sortBy === "title") {
      list = [...list].sort((a, b) =>
        (a.title || "").localeCompare(b.title || "")
      );
    }
    return list;
  }

  function render(jobs) {
    jobsBody.innerHTML = jobs
      .map(
        (j) => `
      <tr>
        <td class="company">${escapeHtml(j.company || "—")}</td>
        <td class="title">${escapeHtml(j.title || "—")}</td>
        <td class="location">${escapeHtml(j.location || "—")}</td>
        <td class="posted">${formatDate(j.posted_date)}</td>
        <td class="source">${escapeHtml(j.source || "—")}</td>
        <td><a href="${escapeAttr(j.url)}" target="_blank" rel="noopener">Apply</a></td>
      </tr>
    `
      )
      .join("");
    emptyMsg.hidden = jobs.length > 0;
  }

  function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  function escapeAttr(s) {
    if (!s) return "#";
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML.replace(/"/g, "&quot;");
  }

  function buildSourceFilters() {
    const sorted = Array.from(sources).sort();
    sourceFiltersEl.innerHTML = sorted
      .map(
        (src) => `
      <label>
        <input type="checkbox" class="source-checkbox" data-source="${escapeAttr(src)}" checked />
        ${escapeHtml(src)}
      </label>
    `
      )
      .join("");
    sourceFiltersEl.querySelectorAll(".source-checkbox").forEach((cb) => {
      cb.addEventListener("change", () => {
        render(filterJobs());
      });
    });
  }

  function dataUrl(path) {
    var origin = window.location.origin;
    var pathname = window.location.pathname || "/";
    if (pathname.endsWith(".html") || pathname.endsWith("/")) {
      pathname = pathname.replace(/\/[^/]*$/, "") || "/";
    }
    if (!pathname.endsWith("/")) pathname += "/";
    return origin + pathname + path;
  }

  function showError(msg, detail) {
    metaEl.textContent = msg;
    jobsBody.innerHTML = "";
    emptyMsg.hidden = false;
    emptyMsg.textContent = detail || "Could not load data.";
  }

  function run() {
    searchEl.addEventListener("input", () => render(filterJobs()));
    sortEl.addEventListener("change", () => render(filterJobs()));

    const timeout = setTimeout(() => {
      showError(
        "Load timed out.",
        "Open this page over HTTP (e.g. run: python -m http.server 8000, then visit http://localhost:8000). Do not open index.html directly from disk (file://)."
      );
    }, 12000);

    fetch(dataUrl("data/jobs.json"))
      .then((r) => {
        clearTimeout(timeout);
        if (!r.ok) throw new Error(r.status + " " + r.statusText);
        return r.json();
      })
      .then((data) => {
        const list = Array.isArray(data.jobs) ? data.jobs : [];
        allJobs = list;
        sources.clear();
        allJobs.forEach((j) => {
          if (j.source) sources.add(String(j.source));
        });
        metaEl.textContent = `${allJobs.length} jobs`;
        buildSourceFilters();
        render(filterJobs());
        return fetch(dataUrl("data/last_run.txt")).then((r) => (r.ok ? r.text() : ""));
      })
      .then((lastRun) => {
        if (lastRun && lastRun.trim()) {
          try {
            const d = new Date(lastRun.trim());
            if (!isNaN(d.getTime())) {
              metaEl.textContent = `Last updated: ${d.toLocaleString()} • ${allJobs.length} jobs`;
            }
          } catch (_) {}
        }
        render(filterJobs());
      })
      .catch((err) => {
        clearTimeout(timeout);
        showError(
          "Failed to load jobs: " + err.message,
          "Serve this folder over HTTP (e.g. python -m http.server 8000) and open http://localhost:8000. Opening index.html from disk (file://) will not work."
        );
      });
  }

  run();
})();
