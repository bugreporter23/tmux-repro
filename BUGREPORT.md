# Copy-mode cursor gets stuck during synchronized application output

### Motivation

I first saw this with Codex CLI 0.157.1 (`--no-alt-screen`) in tmux 3.8-rc2.
While Codex was working, moving around in copy mode left the visible cursor
stuck. Selection worked, and cursor movement recovered when Codex became idle.

With LLM-assisted debugging, I reduced the trigger to a Python application
emitting synchronized updates. The trace led to `server_client_reset_state()`:
cursor coordinates come from the displayed copy-mode screen, but the
`MODE_SYNC` check uses the underlying application's screen.

The proposed change uses the displayed screen's mode too, which fixes this
reproduction. The trace also suggests application synchronization remains
active until its timeout in copy mode, so there may be a deeper issue with
its lifetime. I'd appreciate review of whether this cursor check is the right
place to address the symptom and whether the synchronization handling also
needs attention.

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

<!-- Attach logs.zip from this run directly to the issue before submitting. -->
