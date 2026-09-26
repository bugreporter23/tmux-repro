# tmux copy-mode cursor repro

This Python demo emits synchronized application updates at 30 Hz.

Run from a Linux terminal outside tmux, with Nix flakes enabled:

```sh
nix run . -- logs
nix run .#patched -- logs-patched
```

The demo enters copy mode. Move the cursor with the arrow keys; on the
affected build the visible cursor gets stuck. F2 pauses/resumes updates;
pausing lets the cursor recover after about a second. Ctrl-b, then d exits.

The build pins Git master at [`94796f6b`](https://github.com/tmux/tmux/commit/94796f6b1182507efac8a272fc309a79e22e58a5)
(checked 2026-09-26). The comparison build applies `pane_mode = s->mode`.
The demo uses `-f /dev/null` and records `-vv` logs plus platform/TERM details.

Use fresh log directories. Attach `logs.zip` and your terminal's name/version
when [reporting](https://github.com/tmux/tmux/blob/master/.github/CONTRIBUTING.md).
With an existing build: `python3 repro.py /path/to/tmux logs`.

Context: observed with Codex CLI 0.157.1 (`--no-alt-screen`) in tmux 3.8-rc2.
The visible copy-mode cursor stops following arrow keys while Codex is working
and recovers when it becomes idle.
