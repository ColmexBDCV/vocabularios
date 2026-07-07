(function () {
  const table = document.querySelector("[data-schema-table]");
  if (!table) return;

  const rows = Array.from(table.querySelectorAll("tbody tr"));
  const searchInput = document.querySelector("[data-table-search]");
  const templateFilter = document.querySelector("[data-template-filter]");
  const pageSizeSelect = document.querySelector("[data-page-size]");
  const summary = document.querySelector("[data-table-summary]");
  const currentPageEl = document.querySelector("[data-page-current]");
  const prevButton = document.querySelector("[data-page-prev]");
  const nextButton = document.querySelector("[data-page-next]");
  let currentPage = 1;

  function normalized(value) {
    return (value || "").toString().trim().toLowerCase();
  }

  function pageSize() {
    const value = pageSizeSelect ? pageSizeSelect.value : "25";
    return value === "all" ? Infinity : Number(value);
  }

  function filteredRows() {
    const query = normalized(searchInput && searchInput.value);
    const template = templateFilter ? templateFilter.value : "";
    return rows.filter((row) => {
      const matchesQuery = !query || normalized(row.dataset.search).includes(query);
      const rowTemplates = row.dataset.templates || "";
      const matchesTemplate = !template || rowTemplates.split("||").includes(template);
      return matchesQuery && matchesTemplate;
    });
  }

  function render() {
    const visible = filteredRows();
    const size = pageSize();
    const totalPages = size === Infinity ? 1 : Math.max(1, Math.ceil(visible.length / size));
    currentPage = Math.min(currentPage, totalPages);

    const start = size === Infinity ? 0 : (currentPage - 1) * size;
    const end = size === Infinity ? visible.length : start + size;
    const pageRows = new Set(visible.slice(start, end));

    rows.forEach((row) => {
      row.hidden = !pageRows.has(row);
    });

    if (summary) {
      const first = visible.length ? start + 1 : 0;
      const last = Math.min(end, visible.length);
      summary.textContent = `Mostrando ${first} a ${last} de ${visible.length} campos`;
    }

    if (currentPageEl) currentPageEl.textContent = String(currentPage);
    if (prevButton) prevButton.disabled = currentPage <= 1;
    if (nextButton) nextButton.disabled = currentPage >= totalPages;
  }

  function resetAndRender() {
    currentPage = 1;
    render();
  }

  if (searchInput) searchInput.addEventListener("input", resetAndRender);
  if (templateFilter) templateFilter.addEventListener("change", resetAndRender);
  if (pageSizeSelect) pageSizeSelect.addEventListener("change", resetAndRender);
  if (prevButton) {
    prevButton.addEventListener("click", () => {
      currentPage -= 1;
      render();
    });
  }
  if (nextButton) {
    nextButton.addEventListener("click", () => {
      currentPage += 1;
      render();
    });
  }

  render();
})();
