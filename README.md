# Copy-mode cursor misplaced while an application emits synchronized updates

While using Codex CLI with `--no-alt-screen`, I noticed that the cursor in
tmux copy mode stopped following my keys while Codex was working. Selection
still worked, and the cursor recovered when application output stopped.

## Reproduce visually

From a Linux terminal **outside tmux**, with Nix and flakes enabled:

```sh
nix run . -- logs
```

The demo enters copy mode with a selection started. Move with the arrow keys
and watch the cursor beside the highlighted text. The status line shows
application updates switching **OFF / ON every eight seconds**.

- **Expected:** the cursor follows your keys in both phases.
- **Observed:** during ON, the selection changes but the cursor is misplaced.
  It recovers about a second into OFF.

Press **Ctrl-b, then d** to exit. Compare with the same demo using the fix:

```sh
nix run .#patched -- logs-patched
```

The Python application emits complete DECSET 2026 updates at 30 Hz during ON.
The demo uses a private server, `-f /dev/null`, and an instruction status line.
Nix pins tmux to
[`94796f6b`](https://github.com/tmux/tmux/commit/94796f6b1182507efac8a272fc309a79e22e58a5)
(Git master checked on 2026-09-26). The comparison build applies
`pane_mode = s->mode` in `server_client_reset_state()`.

With an existing tmux build, Python 3 alone is sufficient:

```sh
python3 repro.py /absolute/path/to/tmux logs
```

Use a fresh output directory for each run.

## Reporting

Following tmux's [contribution guidelines](https://github.com/tmux/tmux/blob/master/.github/CONTRIBUTING.md),
the demo records `uname -sp`, tmux version, inside/outside `$TERM`, config,
update phase timestamps, and `-vv` server, client and output logs.
Attach **logs.zip** directly to the issue and include your terminal's name and
version. A short recording showing ON and OFF would illustrate the symptom.

The server uses a temporary home, a clean environment and generated text.
Related reports: [#5525](https://github.com/tmux/tmux/issues/5525)
(copy-mode cursor flicker) and [#5403](https://github.com/tmux/tmux/issues/5403)
(copy-mode refresh during synchronized output).
