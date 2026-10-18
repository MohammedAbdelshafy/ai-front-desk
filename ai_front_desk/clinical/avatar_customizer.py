"""Reusable, privacy-preserving Dr. Mia avatar customization widget."""
from __future__ import annotations

from html import escape

AVATAR_ASSETS = {
    "mia-avatar.js": ("application/javascript; charset=utf-8", "mia-avatar.js"),
    "mia-avatar.css": ("text/css; charset=utf-8", "mia-avatar.css"),
}


def render_avatar_customizer(title: str = "Personalize Mia") -> str:
    """Return the same customizer for each Mia app.

    Profile preferences live in browser localStorage on the current origin.
    Photos are resized in-browser and are never posted to this Python server.
    """
    safe_title = escape(title, quote=True)
    return f"""
<link rel="stylesheet" href="/assets/mia-avatar.css">
<section class="mia-avatar-customizer" data-mia-avatar-widget aria-label="{safe_title}">
  <div class="mia-avatar-shell mia-avatar-current" data-mia-avatar-shell>
    <img data-mia-avatar-image data-default-src="" alt="Current Dr. Mia avatar" hidden>
    <span data-mia-avatar-emoji aria-hidden="true">🤖</span>
  </div>
  <div class="mia-avatar-copy">
    <strong>{safe_title}</strong>
    <p>Choose a clinician persona or use your own portrait. Your photo stays in this browser.</p>
  </div>
  <button class="mia-avatar-open" type="button" data-mia-avatar-open>Change avatar</button>
  <dialog class="mia-avatar-dialog" data-mia-avatar-dialog aria-labelledby="mia-avatar-dialog-title">
    <div class="mia-avatar-dialog-head">
      <div><div class="mia-avatar-kicker">Your workspace · personal appearance</div>
      <h2 id="mia-avatar-dialog-title">Make Mia look like you</h2></div>
      <button class="mia-avatar-close" type="button" data-mia-avatar-close aria-label="Close avatar settings">×</button>
    </div>
    <p class="mia-avatar-note">This changes Mia's visual avatar, not her medical knowledge, permissions, clinical role, or safety rules.</p>
    <div class="mia-avatar-presets" role="group" aria-label="Choose an avatar">
      <button type="button" data-mia-avatar-preset="mia"><span>🤖</span><strong>Classic Mia</strong></button>
      <button type="button" data-mia-avatar-preset="clinician-f"><span>👩🏻‍⚕️</span><strong>Clinician</strong></button>
      <button type="button" data-mia-avatar-preset="clinician-m"><span>👨🏻‍⚕️</span><strong>Clinician</strong></button>
      <button type="button" data-mia-avatar-preset="neutral"><span>🧑🏻‍⚕️</span><strong>Neutral</strong></button>
      <button type="button" data-mia-avatar-preset="bot"><span>🩺</span><strong>Care assistant</strong></button>
    </div>
    <label class="mia-avatar-upload">
      <span class="mia-avatar-upload-icon">＋</span>
      <span><strong>Use your own portrait</strong><small>JPEG, PNG or WebP · up to 8 MB · resized locally</small></span>
      <input type="file" accept="image/jpeg,image/png,image/webp" data-mia-avatar-upload>
    </label>
    <p class="mia-avatar-status" data-mia-avatar-status role="status" aria-live="polite">Your current choice is saved in this browser.</p>
    <div class="mia-avatar-actions">
      <button type="button" data-mia-avatar-export>Export for other Mia apps</button>
      <label class="mia-avatar-import">Import avatar settings<input type="file" accept="application/json,.json" data-mia-avatar-import></label>
      <button type="button" class="mia-avatar-reset" data-mia-avatar-reset>Reset</button>
    </div>
    <p class="mia-avatar-privacy">Privacy: the photo is stored in browser storage after resizing. It is not uploaded or sent to an AI service. Local prototype apps running on different ports have separate browser storage, so export/import is provided. Production apps should sync this preference through the signed-in user's account profile.</p>
  </dialog>
</section>
<script src="/assets/mia-avatar.js" defer></script>
"""
