// Global utilities shared across all pages

function showToast(msg, type = "success") {
  const t = document.getElementById("toast");
  if (!t) return;
  t.textContent = msg;
  t.className = `toast ${type}`;
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.add("hidden"), 3500);
}

function syncProfile() {
  showToast("Syncing with SAM.gov…", "success");
  fetch("/api/profile/sync", { method: "POST" })
    .then(r => r.json())
    .then(d => {
      if (d.ok) {
        showToast("Profile synced from SAM.gov", "success");
        setTimeout(() => location.reload(), 1200);
      } else {
        showToast("Sync failed: " + d.error, "error");
      }
    })
    .catch(e => showToast("Network error: " + e, "error"));
}
