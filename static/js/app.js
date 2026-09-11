/**
 * app.js
 * General, page-independent frontend behaviour for Kalasetu.
 */

// Small helper: show an element by removing its inline "display:none".
function showEl(el) {
  if (el) el.style.display = "";
}

// Small helper: hide an element.
function hideEl(el) {
  if (el) el.style.display = "none";
}

// Prevent accidental double-submits on forms with a "Please wait" state.
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("form").forEach(function (form) {
    form.addEventListener("submit", function () {
      const submitBtns = form.querySelectorAll('button[type="submit"]');
      submitBtns.forEach(function (btn) {
        btn.disabled = true;
      });
    });
  });
});
