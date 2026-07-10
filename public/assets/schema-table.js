(function () {
  const table = document.querySelector("[data-schema-table]");
  if (!table) return;

  const tbody = table.querySelector("tbody");
  const rows = Array.from(tbody.querySelectorAll("tr"));
  const searchInput = document.querySelector("[data-table-search]");
  const sortButtons = Array.from(document.querySelectorAll("[data-sort-column]"));
  const pageSizeSelect = document.querySelector("[data-page-size]");
  const summary = document.querySelector("[data-table-summary]");
  const currentPageEl = document.querySelector("[data-page-current]");
  const prevButton = document.querySelector("[data-page-prev]");
  const nextButton = document.querySelector("[data-page-next]");
  let currentPage = 1;
  let sortColumn = "";
  let sortDirection = "asc";

  function normalized(value) {
    return (value || "").toString().trim().toLowerCase();
  }

  function pageSize() {
    const value = pageSizeSelect ? pageSizeSelect.value : "25";
    return value === "all" ? Infinity : Number(value);
  }

  function filteredRows() {
    const query = normalized(searchInput && searchInput.value);
    const result = rows.filter((row) => {
      const matchesQuery = !query || normalized(row.dataset.search).includes(query);
      return matchesQuery;
    });

    if (sortColumn) {
      result.sort((a, b) => {
        const aValue = normalized(a.dataset[sortColumn]);
        const bValue = normalized(b.dataset[sortColumn]);
        const comparison = aValue.localeCompare(bValue, "es", { sensitivity: "base" });
        return sortDirection === "desc" ? -comparison : comparison;
      });
    }

    return result;
  }

  function render() {
    const visible = filteredRows();
    const size = pageSize();
    const totalPages = size === Infinity ? 1 : Math.max(1, Math.ceil(visible.length / size));
    currentPage = Math.min(currentPage, totalPages);

    const start = size === Infinity ? 0 : (currentPage - 1) * size;
    const end = size === Infinity ? visible.length : start + size;
    const pageRows = visible.slice(start, end);
    const pageRowSet = new Set(pageRows);

    rows.forEach((row) => {
      row.hidden = !pageRowSet.has(row);
    });
    pageRows.forEach((row) => {
      tbody.appendChild(row);
    });

    if (summary) {
      const first = visible.length ? start + 1 : 0;
      const last = Math.min(end, visible.length);
      summary.textContent = `Showing ${first} to ${last} of ${visible.length} entries`;
    }

    if (currentPageEl) currentPageEl.textContent = String(currentPage);
    if (prevButton) prevButton.disabled = currentPage <= 1;
    if (nextButton) nextButton.disabled = currentPage >= totalPages;
  }

  function updateSortButtons() {
    sortButtons.forEach((button) => {
      const active = button.dataset.sortColumn === sortColumn;
      button.dataset.sortDirection = active ? sortDirection : "";
      const icon = button.querySelector("span");
      if (icon) {
        icon.textContent = active ? (sortDirection === "asc" ? "↑" : "↓") : "↕";
      }
      button.setAttribute("aria-sort", active ? (sortDirection === "asc" ? "ascending" : "descending") : "none");
    });
  }

  function resetAndRender() {
    currentPage = 1;
    render();
  }

  if (searchInput) searchInput.addEventListener("input", resetAndRender);
  sortButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const nextColumn = button.dataset.sortColumn;
      if (sortColumn === nextColumn) {
        sortDirection = sortDirection === "asc" ? "desc" : "asc";
      } else {
        sortColumn = nextColumn;
        sortDirection = "asc";
      }
      updateSortButtons();
      resetAndRender();
    });
  });
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

  updateSortButtons();
  render();
})();
