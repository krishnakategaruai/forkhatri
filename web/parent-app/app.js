const modules = [
  { id: "vyapar", name: "Vyapar", icon: "✦", status: "Available", description: "Discover trusted businesses, professionals and meaningful opportunities.", color: "#b66a26", bg: "#fff0dc", orb: "#fff8ee", route: "#module-vyapar" },
  { id: "milavn", name: "Milavn", icon: "◌", status: "Available", description: "Find activities, meet people and participate in community life.", color: "#4f6fbe", bg: "#eaf1ff", orb: "#f4f7ff", route: "#module-milavn" },
  { id: "mangaly", name: "Mangaly", icon: "♡", status: "Available", description: "Explore a thoughtful, trusted matrimonial journey with family context.", color: "#9e5d7b", bg: "#f8eaf1", orb: "#fcf4f8", route: "#module-mangaly" },
  { id: "counsel", name: "Counsel", icon: "◈", status: "Coming soon", description: "Connect with verified professionals when you need guidance.", color: "#7e8797", bg: "#f1f2f5", orb: "#fafafa", planned: true, route: "#module-counsel" },
  { id: "payments", name: "Payment Services", icon: "₹", status: "Coming soon", description: "Everyday payments and benefits, designed around member utility.", color: "#7e8797", bg: "#f1f2f5", orb: "#fafafa", planned: true, route: "#module-payments" },
  { id: "finance", name: "Loans & Finance", icon: "↗", status: "Coming soon", description: "Explore financial products and trusted partner pathways.", color: "#7e8797", bg: "#f1f2f5", orb: "#fafafa", planned: true, route: "#module-finance" }
];

const activityMarkup = `
  <div class="activity-item"><span class="activity-icon icon-vyapar">✦</span><div><strong>New opportunities match your interests</strong><p>Vyapar · 2 hours ago</p></div><span class="activity-arrow">→</span></div>
  <div class="activity-item"><span class="activity-icon icon-milavn">◌</span><div><strong>Saturday founders' circle is this evening</strong><p>Milavn · Tomorrow at 6:00 PM</p></div><span class="activity-arrow">→</span></div>
  <div class="activity-item"><span class="activity-icon icon-system">✓</span><div><strong>Your ForKhatri profile is ready</strong><p>Account · Add a language preference to personalize your experience</p></div><span class="activity-arrow">→</span></div>
  <div class="activity-item"><span class="activity-icon icon-vyapar">✦</span><div><strong>Your saved opportunity has a new update</strong><p>Vyapar · Yesterday</p></div><span class="activity-arrow">→</span></div>
`;

const moduleCard = (item) => `
  <article class="module-card ${item.planned ? "planned" : ""}" style="--card-color:${item.color};--card-bg:${item.bg};--card-orb:${item.orb}">
    <div class="module-top"><span class="module-icon" aria-hidden="true">${item.icon}</span><span class="module-status">${item.status}</span></div>
    <div><h3>${item.name}</h3><p>${item.description}</p><button class="module-action" type="button" data-module="${item.id}" ${item.planned ? "aria-disabled=\"true\"" : ""}>${item.planned ? "Coming later" : "Open module"} <span aria-hidden="true">${item.planned ? "·" : "→"}</span></button></div>
  </article>`;

document.querySelector("#module-grid").innerHTML = modules.slice(0, 3).map(moduleCard).join("");
document.querySelector("#module-grid-expanded").innerHTML = modules.map(moduleCard).join("");
document.querySelector(".activity-list-large").innerHTML = activityMarkup;

const views = [...document.querySelectorAll("[data-view-panel]")];
const navLinks = [...document.querySelectorAll(".nav-link")];
function showView(viewName) {
  views.forEach((view) => view.classList.toggle("active-view", view.dataset.viewPanel === viewName));
  navLinks.forEach((link) => link.classList.toggle("active", link.dataset.view === viewName));
  window.location.hash = viewName;
  document.querySelector("#main-content").focus({ preventScroll: true });
}

function showToast(message) {
  const toast = document.querySelector(".toast");
  toast.textContent = message;
  toast.classList.add("show");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("show"), 2800);
}

function closePopovers() {
  document.querySelectorAll(".notification-popover, .member-popover").forEach((popover) => {
    popover.classList.remove("open");
    popover.setAttribute("aria-hidden", "true");
  });
  document.querySelectorAll("[aria-expanded=true]").forEach((button) => button.setAttribute("aria-expanded", "false"));
}

document.addEventListener("click", (event) => {
  const nav = event.target.closest(".nav-link");
  if (nav) { event.preventDefault(); showView(nav.dataset.view); return; }

  const action = event.target.closest("[data-action]");
  if (action) {
    const actionName = action.dataset.action;
    if (actionName === "explore") showView("modules");
    if (actionName === "activity") showView("activity");
    if (actionName === "account") showView("account");
    if (actionName === "help") showToast("Support will be available from your shared ForKhatri account.");
    if (actionName === "signout") showToast("Sign out will connect to ForKhatri Identity & Trust.");
    closePopovers();
    return;
  }

  const moduleButton = event.target.closest("[data-module]");
  if (moduleButton && moduleButton.dataset.module) {
    const item = modules.find((module) => module.id === moduleButton.dataset.module);
    if (item?.planned) showToast(`${item.name} is coming to your ForKhatri home soon.`);
    else showToast(`${item.name} will open here with your existing ForKhatri session.`);
    return;
  }

  if (event.target.closest(".notification-trigger")) {
    const popover = document.querySelector(".notification-popover");
    const next = !popover.classList.contains("open");
    closePopovers();
    popover.classList.toggle("open", next); popover.setAttribute("aria-hidden", String(!next));
    event.target.closest(".notification-trigger").setAttribute("aria-expanded", String(next));
    return;
  }

  if (event.target.closest(".member-menu-trigger")) {
    const popover = document.querySelector(".member-popover");
    const next = !popover.classList.contains("open");
    closePopovers();
    popover.classList.toggle("open", next); popover.setAttribute("aria-hidden", String(!next));
    event.target.closest(".member-menu-trigger").setAttribute("aria-expanded", String(next));
    return;
  }

  if (event.target.closest(".close-popover")) { closePopovers(); return; }
  if (!event.target.closest(".notification-popover, .member-popover")) closePopovers();
});

document.querySelector("#global-search").addEventListener("keydown", (event) => {
  if (event.key === "Enter") showToast(`Search will connect to ForKhatri modules: “${event.target.value || "your community"}”`);
});

document.addEventListener("keydown", (event) => {
  if (event.key === "/" && document.activeElement.tagName !== "INPUT") { event.preventDefault(); document.querySelector("#global-search").focus(); }
  if (event.key === "Escape") closePopovers();
});

const initialView = window.location.hash.replace("#", "");
if (["home", "modules", "activity", "account"].includes(initialView)) showView(initialView);
