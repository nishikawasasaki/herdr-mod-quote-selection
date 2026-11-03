# Quote Selection

A brief another agent can use to build this mod from an empty folder. The files beside it are one implementation. Read the installed `~/.config/herdr-app/AGENTS.md`, `herdr.d.ts` and `gpui-kit.d.ts` first; never edit generated files or shipped mods.

## What you see

Select terminal text in Claude Code or Codex, then press Cmd+Shift+A. The selected text appears at the end of the same terminal's draft as Markdown blockquote lines. A blank line below the quote is ready for the reply. Keep the existing draft and never submit it.

No layout change, panel, progress dialog, dimming, success toast or terminal focus grab. Failures produce a notification. Error messages in this implementation are Japanese.

## How it behaves

1. Capture `focused()?.terminal` once when invoked. If missing, notify and stop; never infer a target from another tab or an old address.
2. Read the clipboard with `exec("/usr/bin/env", ["LC_ALL=en_US.UTF-8", "/usr/bin/pbpaste"])`. Herdr copies terminal selections on release. This is a clipboard-based feature, not a selection identity API.
3. Pass the captured address and text as separate arguments, after `--`, to `python3 <appHome>/mods/quote-selection/quote.py`. Never construct a shell command with the selected text.
4. Normalize CRLF/CR; prefix every line with `> `; end with two newlines. Reject empty/whitespace-only input and control characters other than tab/newline.
5. Use `hc get` to validate the terminal reports `codex`, `claude-code` or `claude` and a normal input state. This build accepts idle/done/working, rejects other states, and still validates the input screen.
6. Attach through a local pseudo-terminal sized to the target. Read the terminal cursor from ANSI cursor-position sequences. Answer hc's initial DA1 request before the first paint; otherwise attach waits for its 500 ms display-query timeout.
7. Read the screen using `hc read`. Find the final composer marker (`›` for Codex, `❯` for Claude). Find its lower boundary from the current standard footer or horizontal ruler; do not mistake response text for the draft.
8. Move to the true draft end using Ctrl+E, then Down only within the detected composer. Confirm the cursor and composer text stabilize, ignoring streamed response text above it. Bound the work; if the composer cannot be identified, do not paste.
9. Add a newline first when a draft exists. Paste each quoted line separately using bracketed-paste sequences and use Ctrl+J between lines and for the reply gap. Whole multiline paste can become a collapsed Claude paste chip, so preserve normal reply cursor placement. Never send CR/Enter, `hc send`, or a submit command.
10. Close the hc attachment client without ending the target agent. Close the invisible overlay, retain/restore focus to the captured terminal, and show only failures as notifications.

## Built from

- `mods/quote-selection/main.js`: a `gpui-kit` View using `focused`, `props`, `exec`, `appHome`, `notify`, `closeOverlay`, and `run("pane.focus", {terminal})`. Async work uses `cx.spawn`.
- `mods/quote-selection/mod.json`: `place: "none"`, overlay `kind: "window"`, `frame: "none"`. Render a zero-size element so the command can run without a visible dialog or modal dimming.
- `mods/quote-selection/quote.py`: Python standard library only (`pty`, `fcntl`, `termios`, `subprocess`, `select`, etc.). The implemented transport is local macOS.
- `keys.json`: merge `global.cmd-shift-a = "mod.open:quote-selection"` into existing settings. Preserve every unrelated binding and resolve conflicts, including terminal and layout-specific sections.
- Tests beside the implementation; Node is a development dependency only. No package installation is needed at runtime.
- `preview.png`: a clearly labelled illustration with fictional text, generated from `assets/preview.html`. It is not proof of runtime behavior and must contain no real sessions, account details, paths or logs.
- No `layouts/` directory and no changes to Herdr/App/Core/agent binaries.

## Watch out

Mods are trusted code with command access. Read every file before installing. This mod reads the clipboard and the target terminal's screen; it temporarily sends editor movement and paste bytes. The clipboard text travels in process arguments, so do not promise secrecy from local process inspection. It does not deliberately log text or use HTTP/AI APIs.

The mod does not save or restore a viewport position. Fullscreen conversation scrolling belongs to the agent and is distinct from terminal scrollback. Do not promise reading-position preservation. When an existing draft ends with a comment and no newline, the next quote gets one newline before it, not a blank separator; the user can add a newline before invoking to leave a blank line.

An old clipboard value can be quoted when there is no fresh selection. Do not change the clipboard between selecting and invoking. Use Shift-selection when the program captures mouse events. Do not edit the same draft while insertion runs.

The current parser assumes standard key bindings and footer/prompt presentation. Vim mode, custom keys/footers, drafts larger than the visible composer and remote terminals are outside the supported scope. Working-state input has a mocked regression test, not a demonstrated live streaming guarantee. Do not silently weaken validation to accommodate an unknown screen.

The older local prototype used Mod ID `reply-annotation`; this package is `quote-selection` throughout. Do not migrate or overwrite an existing user's settings automatically. Repeated invocation while an overlay is open follows Herdr's `mod.open` toggle behavior; wait for the insertion to finish before invoking again.

## Done when

- `herdr-app check mods/quote-selection` passes with the installed matching Herdr.
- Python tests and Node tests pass.
- In disposable Claude Code and Codex sessions, select fictional text, invoke the shortcut, and confirm `> ` on each quoted line, a reply gap and cursor below it, existing multiline draft preserved, no turn submitted, and no progress dialog/dimming.
- Include Japanese text, full-width characters, emoji, and a cursor starting in the middle of a multiline draft. Type a harmless marker afterward to prove cursor placement; never press Enter to test submission.
- Empty selection, unknown terminal/composer, clipboard failure and control-character input produce no quote insertion and a useful failure notification.
- The shortcut works in existing layouts without adding Mod panels or `terminal_menu`; normal typing remains available.
- Installation leaves unrelated keys/layouts/mods untouched. Publication files contain no personal paths, session identifiers, real logs or generated AGENTS/type files.

## Sharing

Follow https://herdr.dev/mods/ for package shape and community listing. Publishing, changing repository visibility, pushing and adding a topic require separate user authorization. This recipe grants none of those permissions.
