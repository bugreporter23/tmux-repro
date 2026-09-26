# tmux copy-mode cursor repro

Seen with Codex CLI `--no-alt-screen`: while Codex works, the copy-mode cursor
is misplaced even though selection works. This Python demo emits the same
kind of synchronized updates at 30 Hz.

Run from a Linux terminal outside tmux, with Nix flakes enabled:

```sh
nix run . -- logs
nix run .#patched -- logs-patched
```

Move with the arrow keys. The cursor should follow the selection; on the
affected build it stays elsewhere. F2 pauses/resumes updates; pausing lets the
cursor recover after about a second. Ctrl-b, then d exits.

The build pins Git master at [`94796f6b`](https://github.com/tmux/tmux/commit/94796f6b1182507efac8a272fc309a79e22e58a5)
(checked 2026-09-26). The comparison build applies `pane_mode = s->mode`.
The demo uses `-f /dev/null` and records `-vv` logs plus platform/TERM details.

Use fresh log directories. Attach `logs.zip` and your terminal's name/version
when [reporting](https://github.com/tmux/tmux/blob/master/.github/CONTRIBUTING.md).
With an existing build: `python3 repro.py /path/to/tmux logs`.
