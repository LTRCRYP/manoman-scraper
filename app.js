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
      list = list.filter((j) => selectedSources.has(j.source || ""));
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

  function run() {
    searchEl.addEventListener("input", () => render(filterJobs()));
    sortEl.addEventListener("change", () => render(filterJobs()));

    fetch("data/jobs.json")
      .then((r) => {
        if (!r.ok) throw new Error(r.statusText);
        return r.json();
      })
      .then((data) => {
        allJobs = data.jobs || [];
        allJobs.forEach((j) => {
          if (j.source) sources.add(j.source);
        });
        buildSourceFilters();
        metaEl.textContent = `Last updated: loading… • ${allJobs.length} jobs`;
        return fetch("data/last_run.txt").then((r) => (r.ok ? r.text() : ""));
      })
      .then((lastRun) => {
        if (lastRun) {
          try {
            const d = new Date(lastRun.trim());
            metaEl.textContent = `Last updated: ${d.toLocaleString()} • ${allJobs.length} jobs`;
          } else {
            metaEl.textContent = `${allJobs.length} jobs`;
          }
        }
        render(filterJobs());
      })
      .catch((err) => {
        metaEl.textContent = "Failed to load jobs: " + err.message;
        jobsBody.innerHTML = "";
        emptyMsg.hidden = false;
        emptyMsg.textContent = "Could not load data/jobs.json.";
      });
  }

  run();
})();
