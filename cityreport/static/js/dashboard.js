document.querySelectorAll(".status-select").forEach(select => {
  select.addEventListener("change", async () => {
    const reportId = select.dataset.reportId;
    const newStatus = select.value;
    select.disabled = true;
    try {
      const res = await fetch(`/admin/update_status/${reportId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      if (!res.ok) throw new Error("Update failed");
      const row = select.closest("tr");
      row.dataset.status = newStatus;
      const badge = row.querySelector(".badge");
      if (badge) {
        badge.className = `badge badge-${newStatus}`;
        badge.textContent = newStatus === "received" ? "Submitted" : newStatus.replace("_", " ");
      }
    } catch (e) {
      alert("Could not update status. Please try again.");
    } finally {
      select.disabled = false;
    }
  });
});

const applyFilters = () => {
  const status = document.getElementById("statusFilter")?.value || "";
  const category = document.getElementById("categoryFilter")?.value || "";
  const search = (document.getElementById("reportSearch")?.value || "").trim().toLowerCase();
  document.querySelectorAll(".report-table tbody tr[data-report-id]").forEach(row => {
    row.hidden = (status && row.dataset.status !== status) || (category && row.dataset.category !== category) || (search && !row.dataset.search.includes(search));
  });
};

document.getElementById("statusFilter")?.addEventListener("change", applyFilters);
document.getElementById("categoryFilter")?.addEventListener("change", applyFilters);
document.getElementById("reportSearch")?.addEventListener("input", applyFilters);
