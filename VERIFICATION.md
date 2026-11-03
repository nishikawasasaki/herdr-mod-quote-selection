# Verification

Checked on 2026-11-03. Runtime: macOS, Herdr App 0.1.12, hc 0.1.17, Codex 0.166.0, Claude Code 2.1.316 and 2.1.317.

The public package is derived from the locally working `reply-annotation` prototype. `quote.py` differs only in the feature name in one error message; `main.js` differs only in the feature name and the helper's Mod directory. The invisible overlay manifest is unchanged. No active Mod, key binding or layout was changed while preparing this package.

Earlier runtime trials of the same helper confirmed both agents preserve a multiline draft, append quoted lines, place a typed cursor marker below the quote, and do not submit. The final shortcut entry point was exercised with Codex in main-usage and the shipped main layout; no progress dialog/dimming remained after the invisible-overlay change. The user also confirmed the working shortcut and latency improvement. Those observations apply to the prototype identity, not an independent public-package installation.

Preview imagery is illustrative and is not runtime evidence.

## Public package checks

- `herdr-app check mods/quote-selection`: passed with the installed Herdr binary. The sandboxed run could not connect to macOS input services; the normal local check passed.
- `python3 -m unittest quote_test.py`: 9 passed. `node --test annotation.test.mjs`: 3 passed.
- Fresh runtime trials used the public `main.js` callback with the real local `exec`/Python helper, and a fictional selection supplied at the clipboard boundary. The App home was the package root, exercising the actual `mods/quote-selection/quote.py` path. This was a VM harness plus live TUIs, not a native installation of the public Mod ID or a new physical mouse/shortcut test.
- Codex 0.166.0 and Claude Code 2.1.317: preserved `draft first` and `draft second` with the cursor initially moved into the first line; appended Japanese/full-width/emoji and a second quoted line; a typed marker appeared below the blank reply line. Both stayed idle with turn count unchanged. No prompt was submitted.
- The public manifest is byte-identical to the tested invisible-overlay prototype. The public main/helper changes are only the Mod path and feature name. The installed prototype source hashes remained unchanged during packaging.
- The Claude trial had preexisting nonblocking SessionStart hook errors because `node` was absent from that child environment. The input tests passed; no hook configuration was changed.
- The preview was rendered locally with Quick Look from `assets/preview.html`; it contains fictional text only. Visual inspection found no real session/account/path/log content. No image metadata contained a user path.
- No layout folder or generated App AGENTS/type/config files are included in the Git-visible package.

The native public-ID installation and community image screening remain separate from these checks. Reuse the documented tests when a user chooses to install this package; do not replace an existing shortcut without checking conflicts.

## Repeated quotation and viewport limits

- A further disposable-session trial in Codex 0.166.0 and Claude Code 2.1.317 appended quote A, comment A, quote B, comment B through the unmodified helper and PTY input. Ordering was preserved and both remained idle with turn counts unchanged.
- Without a trailing newline on comment A, the resulting separator is `comment A\n> B`, not `comment A\n\n> B`. No automatic blank separator is claimed.
- The user reported successfully reading older messages and adding several quotations/comments in the installed prototype. This is user confirmation, not an automated viewport measurement.
- Automated GUI viewport verification could not obtain a current Herdr window. Consequently reading-position preservation, including physical typing in fullscreen mode, remains unverified. The Mod contains no viewport save/restore logic.
