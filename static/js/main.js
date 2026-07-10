// main.js — shared behavior across all pages (mobile nav toggle)

document.addEventListener("DOMContentLoaded", () => {
  const navbar = document.getElementById("navbar");
  const navToggle = document.getElementById("navToggle");

  if (navToggle && navbar) {
    navToggle.addEventListener("click", () => {
      navbar.classList.toggle("open");
    });

    // Close mobile menu when a nav link is tapped
    navbar.querySelectorAll(".nav-links a").forEach((link) => {
      link.addEventListener("click", () => navbar.classList.remove("open"));
    });
  }
});
