// Mobile navigation toggle + auto-dismiss for flash messages.
document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("nav-toggle");
  const menu = document.getElementById("nav-menu");
  if (button && menu) {
    button.addEventListener("click", () => {
      const open = menu.classList.toggle("hidden") === false;
      button.setAttribute("aria-expanded", String(open));
    });
  }

  document.querySelectorAll("[data-dismiss]").forEach((el) => {
    el.addEventListener("click", () => el.closest("[data-flash]").remove());
  });
});
