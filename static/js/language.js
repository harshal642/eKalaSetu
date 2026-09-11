/**
 * language.js
 * Keeps a local copy of the selected language in localStorage so it can
 * survive page refreshes even before the server session responds, and
 * exposes a small helper other scripts can use to switch language via
 * AJAX (used by the profile page's live language switch, in addition to
 * the normal form submit fallback).
 *
 * The Flask session is always the source of truth; localStorage here is
 * only a convenience mirror for the browser.
 */

(function () {
  const STORAGE_KEY = "kalasetu_lang";

  // Mirror the language rendered by the server into localStorage.
  const bodyLang = document.documentElement.getAttribute("lang");
  if (bodyLang) {
    try {
      localStorage.setItem(STORAGE_KEY, bodyLang);
    } catch (e) {
      /* localStorage may be unavailable in some browsers/modes; ignore */
    }
  }

  // Expose a small global helper for AJAX language switching.
  window.KalasetuLanguage = {
    switchLanguage: function (langCode, onDone) {
      fetch("/set-language", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ language: langCode }),
      })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (data.success) {
            try { localStorage.setItem(STORAGE_KEY, langCode); } catch (e) {}
          }
          if (typeof onDone === "function") onDone(data);
        })
        .catch(function () {
          if (typeof onDone === "function") onDone({ success: false });
        });
    },
  };
})();
