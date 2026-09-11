/**
 * voice.js
 * Wraps the browser Web Speech APIs (SpeechRecognition + SpeechSynthesis)
 * behind a small, safe interface. Text input always remains available as
 * a fallback -- voice is an enhancement, never the only path.
 */

(function () {
  const SpeechRecognitionImpl =
    window.SpeechRecognition || window.webkitSpeechRecognition || null;

  const synth = window.speechSynthesis || null;

  function isRecognitionSupported() {
    return !!SpeechRecognitionImpl;
  }

  function isSynthesisSupported() {
    return !!synth;
  }

  /**
   * Speak the given text aloud in the given BCP-47 language (e.g. "mr-IN").
   */
  function speak(text, lang) {
    if (!isSynthesisSupported() || !text) return;
    try {
      synth.cancel(); // stop anything currently speaking
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = lang || "en-IN";
      utterance.rate = 0.95;
      synth.speak(utterance);
    } catch (e) {
      /* fail silently -- speaking is a convenience feature */
    }
  }

  /**
   * Start listening once and return the recognized text via callback.
   * onResult(text) is called on success.
   * onError(reason) is called if recognition fails or is unsupported.
   * onStart() / onEnd() are optional lifecycle hooks for UI state.
   */
  function listenOnce(lang, onResult, onError, onStart, onEnd) {
    if (!isRecognitionSupported()) {
      if (onError) onError("unsupported");
      return null;
    }

    const recognition = new SpeechRecognitionImpl();
    recognition.lang = lang || "en-IN";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = function () {
      if (onStart) onStart();
    };

    recognition.onresult = function (event) {
      const transcript = event.results[0][0].transcript;
      if (onResult) onResult(transcript);
    };

    recognition.onerror = function (event) {
      if (onError) onError(event.error || "error");
    };

    recognition.onend = function () {
      if (onEnd) onEnd();
    };

    try {
      recognition.start();
    } catch (e) {
      if (onError) onError("start_failed");
      return null;
    }

    return recognition;
  }

  window.KalasetuVoice = {
    isRecognitionSupported: isRecognitionSupported,
    isSynthesisSupported: isSynthesisSupported,
    speak: speak,
    listenOnce: listenOnce,
  };
})();
