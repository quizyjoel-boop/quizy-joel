let knownNotificationIds = new Set();
let notificationsLoaded = false;

const translations = {
  fr: {
    "Home": "Accueil", "Report an issue": "Signaler un probleme", "Report an Issue": "Signaler un probleme",
    "Citizen login": "Connexion citoyen", "Staff login": "Connexion admin", "My dashboard": "Mon tableau de bord",
    "Log out": "Deconnexion", "View public map": "Voir la carte publique", "Back to map": "Retour a la carte",
    "Report. Track. Resolve.": "Signaler. Suivre. Resoudre.", "Make Douala Better.": "Ameliorons Douala.",
    "What can you report?": "Que pouvez-vous signaler ?", "Small reports, visible action.": "Des signalements, des actions visibles.",
    "Potholes": "Nids-de-poule", "Streetlights": "Eclairage public", "Waste": "Dechets",
    "Other": "Autre", "How it works": "Comment ca marche", "Report": "Signaler", "City Acts": "La ville agit", "You Track": "Vous suivez",
    "Total Reports": "Signalements totaux", "In Progress": "En cours", "My reports": "Mes signalements",
    "Operations dashboard": "Tableau de bord des operations", "Total": "Total", "Submitted": "Soumis", "Resolved": "Resolus",
    "No reports yet": "Aucun signalement", "Report your first issue": "Signaler votre premier probleme",
    "No new notifications.": "Aucune nouvelle notification.", "Private area for authorized CityReport administrators only.": "Espace prive reserve aux administrateurs autorises de CityReport."
  }
};

function applyLanguage(language) {
  const dictionary = translations[language] || {};
  document.querySelectorAll("body *:not(script):not(style)").forEach(element => {
    if (element.children.length || !element.textContent.trim()) return;
    const original = element.dataset.originalText || element.textContent.trim();
    element.dataset.originalText = original;
    if (dictionary[original]) element.textContent = dictionary[original];
    else if (language === "en") element.textContent = original;
  });
  document.documentElement.lang = language;
  localStorage.setItem("cityreport-language", language);
}

function setupPreferences() {
  const languageSelect = document.getElementById("languageSelect");
  const themeToggle = document.getElementById("themeToggle");
  const language = localStorage.getItem("cityreport-language") || "en";
  const theme = localStorage.getItem("cityreport-theme") || "light";
  if (languageSelect) {
    languageSelect.value = language;
    languageSelect.addEventListener("change", event => applyLanguage(event.target.value));
  }
  document.documentElement.dataset.theme = theme;
  if (themeToggle) {
    themeToggle.textContent = theme === "dark" ? "☀" : "☾";
    themeToggle.setAttribute("aria-label", theme === "dark" ? "Switch to light mode" : "Switch to dark mode");
    themeToggle.addEventListener("click", () => {
      const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = nextTheme;
      localStorage.setItem("cityreport-theme", nextTheme);
      themeToggle.textContent = nextTheme === "dark" ? "☀" : "☾";
      themeToggle.setAttribute("aria-label", nextTheme === "dark" ? "Switch to light mode" : "Switch to dark mode");
    });
  }
  if (language === "fr") applyLanguage(language);
}

setupPreferences();

function showNotificationToast(message) {
  const toast = document.createElement("div");
  toast.className = "notification-toast";
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.classList.add("visible"), 10);
  setTimeout(() => {
    toast.classList.remove("visible");
    setTimeout(() => toast.remove(), 250);
  }, 4500);
}

function renderNotifications(items) {
  const dropdown = document.getElementById("notifDropdown");
  if (!dropdown) return;
  dropdown.replaceChildren();

  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "notif-empty";
    empty.textContent = "No new notifications.";
    dropdown.appendChild(empty);
    return;
  }

  items.forEach(item => {
    const entry = document.createElement("button");
    entry.type = "button";
    entry.className = "notif-item";
    const message = document.createElement("strong");
    message.textContent = item.message;
    const details = document.createElement("span");
    details.textContent = `${item.ref_code || ""} - ${new Date(item.created_at).toLocaleString()}`;
    entry.append(message, details);
    entry.addEventListener("click", async () => {
      await fetch(`/notifications/mark_read/${item.id}`, { method: "POST" });
      knownNotificationIds.delete(item.id);
      entry.remove();
      fetchNotif(false);
    });
    dropdown.appendChild(entry);
  });
}

async function fetchNotif(showToast = true) {
  const response = await fetch("/notifications");
  if (!response.ok) return;
  const data = await response.json();
  const items = data.notifications || [];
  const count = document.getElementById("notifCount");
  if (count) {
    count.textContent = data.unread_count || 0;
    count.hidden = !data.unread_count;
  }

  if (showToast && notificationsLoaded) {
    items.filter(item => !knownNotificationIds.has(item.id)).forEach(item => {
      showNotificationToast(item.message.includes("resolved") ? "Status updated to Resolved" : item.message);
    });
  }
  knownNotificationIds = new Set(items.map(item => item.id));
  notificationsLoaded = true;
  renderNotifications(items);
}

function toggleNotif() {
  const dropdown = document.getElementById("notifDropdown");
  if (!dropdown) return;
  const isHidden = dropdown.style.display === "none";
  dropdown.style.display = isHidden ? "block" : "none";
  if (isHidden) fetchNotif(false);
}

const notificationBell = document.querySelector(".notif-bell");
notificationBell?.addEventListener("keydown", event => {
  if (event.key === "Enter" || event.key === " ") toggleNotif();
});

fetchNotif(false);
setInterval(() => fetchNotif(true), 30000);
