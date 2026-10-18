(() => {
  "use strict";
  const KEY = "mia.avatar.profile.v1";
  const DEFAULT_PROFILE = { version: 1, kind: "preset", preset: "mia" };
  const PRESETS = {
    mia: { label: "Classic Mia", emoji: "🤖" },
    "clinician-f": { label: "Clinician", emoji: "👩🏻‍⚕️" },
    "clinician-m": { label: "Clinician", emoji: "👨🏻‍⚕️" },
    neutral: { label: "Neutral clinician", emoji: "🧑🏻‍⚕️" },
    bot: { label: "Care assistant", emoji: "🩺" }
  };
  const MAX_UPLOAD_BYTES = 8 * 1024 * 1024;
  const MAX_STORED_IMAGE_CHARS = 650000;

  function normalizeProfile(value) {
    if (!value || value.version !== 1) return { ...DEFAULT_PROFILE };
    if (value.kind === "preset" && Object.prototype.hasOwnProperty.call(PRESETS, value.preset)) {
      return { version: 1, kind: "preset", preset: value.preset };
    }
    if (value.kind === "photo" && typeof value.imageData === "string" &&
        /^data:image\/jpeg;base64,/.test(value.imageData) &&
        value.imageData.length <= MAX_STORED_IMAGE_CHARS) {
      return { version: 1, kind: "photo", imageData: value.imageData };
    }
    return { ...DEFAULT_PROFILE };
  }

  function readProfile() {
    try {
      const raw = localStorage.getItem(KEY);
      return raw ? normalizeProfile(JSON.parse(raw)) : { ...DEFAULT_PROFILE };
    } catch (_) {
      return { ...DEFAULT_PROFILE };
    }
  }

  function say(message) {
    document.querySelectorAll("[data-mia-avatar-status]").forEach(node => { node.textContent = message; });
  }

  function saveProfile(profile) {
    const safe = normalizeProfile(profile);
    try {
      localStorage.setItem(KEY, JSON.stringify(safe));
      say("Avatar preference saved in this browser.");
    } catch (_) {
      say("Browser storage is full or unavailable. This change may not persist after you close the page.");
    }
    applyProfile(safe);
  }

  function applyFace(shell, profile) {
    const image = shell.querySelector("[data-mia-avatar-image]");
    const emoji = shell.querySelector("[data-mia-avatar-emoji]");
    if (profile.kind === "photo") {
      if (image) {
        image.src = profile.imageData;
        image.hidden = false;
      }
      if (emoji) emoji.hidden = true;
      shell.classList.add("mia-avatar-has-photo");
      shell.setAttribute("aria-label", "Personalized Dr. Mia avatar");
      return;
    }
    const preset = PRESETS[profile.preset] || PRESETS.mia;
    const defaultSrc = image ? (image.dataset.defaultSrc || "") : "";
    if (image && profile.preset === "mia" && defaultSrc) {
      image.src = defaultSrc;
      image.hidden = false;
      if (emoji) emoji.hidden = true;
    } else {
      if (image) image.hidden = true;
      if (emoji) {
        emoji.textContent = preset.emoji;
        emoji.hidden = false;
      }
    }
    shell.classList.remove("mia-avatar-has-photo");
    shell.setAttribute("aria-label", preset.label);
  }

  function applyProfile(profile) {
    document.querySelectorAll("[data-mia-avatar-shell]").forEach(shell => applyFace(shell, profile));
    document.querySelectorAll("[data-mia-avatar-preset]").forEach(button => {
      const selected = profile.kind === "preset" && profile.preset === button.dataset.miaAvatarPreset;
      button.setAttribute("aria-pressed", selected ? "true" : "false");
      button.classList.toggle("is-selected", selected);
    });
  }

  function openDialog(dialog) {
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "open");
  }

  async function compactImage(file) {
    if (!file || !["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      throw new Error("Choose a JPEG, PNG or WebP image.");
    }
    if (file.size > MAX_UPLOAD_BYTES) throw new Error("Choose an image smaller than 8 MB.");
    const originalURL = URL.createObjectURL(file);
    try {
      const image = await new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = () => reject(new Error("The image could not be opened."));
        img.src = originalURL;
      });
      const maxSide = 480;
      const scale = Math.min(1, maxSide / Math.max(image.naturalWidth, image.naturalHeight));
      const canvas = document.createElement("canvas");
      canvas.width = Math.max(1, Math.round(image.naturalWidth * scale));
      canvas.height = Math.max(1, Math.round(image.naturalHeight * scale));
      const ctx = canvas.getContext("2d");
      if (!ctx) throw new Error("Image processing is unavailable in this browser.");
      ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
      const data = canvas.toDataURL("image/jpeg", 0.82);
      if (data.length > MAX_STORED_IMAGE_CHARS) throw new Error("This image is still too large after resizing. Choose a smaller photo.");
      return data;
    } finally {
      URL.revokeObjectURL(originalURL);
    }
  }

  async function importSettings(file) {
    if (!file || file.size > 900000) throw new Error("Avatar settings file is too large.");
    const parsed = JSON.parse(await file.text());
    const profile = normalizeProfile(parsed);
    if (profile.kind !== parsed.kind || (parsed.kind === "photo" && !profile.imageData)) {
      throw new Error("That file is not a supported Mia avatar profile.");
    }
    saveProfile(profile);
    say("Avatar settings imported.");
  }

  function init() {
    applyProfile(readProfile());
    document.querySelectorAll("[data-mia-avatar-open]").forEach(button => {
      button.addEventListener("click", () => {
        const root = button.closest("[data-mia-avatar-widget]");
        const dialog = root && root.querySelector("[data-mia-avatar-dialog]");
        if (dialog) openDialog(dialog);
      });
    });
    document.querySelectorAll("[data-mia-avatar-close]").forEach(button => {
      button.addEventListener("click", () => {
        const dialog = button.closest("dialog");
        if (dialog && typeof dialog.close === "function") dialog.close();
        else if (dialog) dialog.removeAttribute("open");
      });
    });
    document.querySelectorAll("[data-mia-avatar-preset]").forEach(button => {
      button.addEventListener("click", () => saveProfile({ version: 1, kind: "preset", preset: button.dataset.miaAvatarPreset }));
    });
    document.querySelectorAll("[data-mia-avatar-upload]").forEach(input => {
      input.addEventListener("change", async () => {
        try {
          const file = input.files && input.files[0];
          if (!file) return;
          const imageData = await compactImage(file);
          saveProfile({ version: 1, kind: "photo", imageData });
          say("Photo resized and saved locally in this browser. No upload was made.");
        } catch (error) {
          say(error && error.message ? error.message : "Could not save this photo.");
        } finally {
          input.value = "";
        }
      });
    });
    document.querySelectorAll("[data-mia-avatar-reset]").forEach(button => {
      button.addEventListener("click", () => saveProfile({ ...DEFAULT_PROFILE }));
    });
    document.querySelectorAll("[data-mia-avatar-export]").forEach(button => {
      button.addEventListener("click", () => {
        const blob = new Blob([JSON.stringify(readProfile(), null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "mia-avatar-profile.json";
        link.click();
        URL.revokeObjectURL(url);
        say("Export created. Import this JSON in another Mia app. It may contain your portrait.");
      });
    });
    document.querySelectorAll("[data-mia-avatar-import]").forEach(input => {
      input.addEventListener("change", async () => {
        try {
          await importSettings(input.files && input.files[0]);
        } catch (error) {
          say(error && error.message ? error.message : "Could not import settings.");
        } finally {
          input.value = "";
        }
      });
    });
    window.addEventListener("storage", event => {
      if (event.key === KEY) applyProfile(readProfile());
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true });
  else init();
})();