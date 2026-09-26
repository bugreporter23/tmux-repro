# Copy-mode cursor gets stuck during synchronized application output

### Motivation

I first saw this with Codex CLI 0.157.1 (`--no-alt-screen`) in tmux 3.8-rc2.
While Codex was explicitly in the "working" mode (e.g. you prompted it and its
off doing its things), moving around the _cursor_ in copy mode visually removed
the cursor; I could not see it anymore.

The logical cursor was sitll there - could still do selection, but I would have
to guess where exactly my cursor was.

This was not an issue once codex stpoped working in the codex-cli; so I
suspected it was some kind of constant updating issue.

I got an LLM to generate a 1 line patch and this is what it had to say:

```
I ran Codex CLI 0.157.1 in an isolated tmux server and captured its PTY
output. While working, it emitted roughly 30 balanced DECSET 2026 updates
per second. Copy-mode cursor coordinates changed correctly, but tmux's
terminal output left the visible cursor elsewhere. Idle output stopped and
cursor movement recovered.

I reduced the trigger to a Python program emitting synchronized updates,
then traced server_client_reset_state(). It takes cursor coordinates from
s = wp->screen, the displayed screen, but checks MODE_SYNC on wp->base.mode,
the application's screen. Copy mode has its own screen. The application's
synchronization state can therefore suppress positioning of its cursor.

There is also a synchronization-lifetime issue in this path: application
output parsed during copy mode uses a screen_write_ctx with no pane.
Starting synchronization still uses the input context's pane, whereas
screen_write_end_sync() returns when ctx->wp is NULL. In the reproduction,
MODE_SYNC remains set after the end sequence until the one-second timeout;
repeated updates restart that timer.

I changed pane_mode = wp->base.mode to pane_mode = s->mode and built both
versions at 94796f6b1182507efac8a272fc309a79e22e58a5. The cursor mismatch
reproduced on the original and cleared with the patch. I also checked that
normal application cursor updates remain deferred until a synchronized
frame ends. In normal mode, wp->screen and &wp->base are the same screen.

I made the public reproduction interactive, entering plain copy mode with
continuous output and F2 to pause it. Private checks inspected cursor output,
including with terminal synchronization support advertised. The patch leaves
the synchronization-lifetime behavior above unchanged and also affects other
pane modes; my behavior checks covered normal mode and copy mode.
```

The patch worked; I'm currently running with this patch in my private nix
flakes, but I want confirmation that this is the right place to add it - not
good at terminal semantics.

I've attached a small repo (hopefully readable; the only thing that's
complicated is `repro.py` but it's mostly scaffolding; the visual bug is what
I'm targeting) built with nix that should show you what I mean. If that doesn't
work, then try codex v0.157 and entering copy mode while codex is working; else
I can send a video too.

### Issue description

In copy mode, the visible cursor stops following arrow keys while the
application underneath emits synchronized updates (DECSET 2026). It recovers
when application output stops. Selection still works.

### Reproduce

From a terminal outside tmux, with Nix flakes enabled:

```sh
git clone https://github.com/bugreporter23/tmux-repro.git
cd tmux-repro
nix run . -- logs
```

The demo starts tmux with `-f /dev/null`, enters copy mode, and emits complete
synchronized updates at 30 Hz. Move the cursor with the arrow keys: it should
follow each keypress, but stays misplaced. Press F2 to pause output; the cursor
recovers after about a second. F2 resumes output. Ctrl-b, then d exits.

For comparison, `nix run .#patched -- logs-patched` runs the same demo with
`pane_mode = s->mode` in `server_client_reset_state()`. The cursor follows arrow
keys while output continues.

### Required information

- tmux: `next-3.9`, Git master at
  [94796f6b](https://github.com/tmux/tmux/commit/94796f6b1182507efac8a272fc309a79e22e58a5)
  (checked 2026-09-26).
- Platform (`uname -sp`): `Linux unknown`.
- Terminal: Alacritty 0.17.0.
- `$TERM` outside tmux: `xterm-256color`; inside: `tmux-256color`.
- Config: `/dev/null`, with a status line for demo controls and F2 to pause
  output.

The demo saves `-vv` server, client and output logs in `logs.zip` on exit.
