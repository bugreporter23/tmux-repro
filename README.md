# Copy-mode cursor remains misplaced after a synchronized application update

## Issue description

While using Codex CLI with `--no-alt-screen`, I noticed that moving the cursor
in tmux copy mode worked logically, but its visible position was wrong while
Codex was working. It recovered when application output stopped.

This reproducer reduces the trigger to one complete DECSET 2026 update from
a small Python program. It enters copy mode, emits the update underneath it,
then moves the copy cursor left. The cursor position in tmux's terminal output
should agree with `copy_cursor_x` and `copy_cursor_y`.

## Reproduce

On Linux with Nix and flakes enabled:

```sh
nix run . -- logs
```

The test builds tmux at
[`94796f6b`](https://github.com/tmux/tmux/commit/94796f6b1182507efac8a272fc309a79e22e58a5)
(Git master checked on 2026-09-26). Dependencies are pinned in `flake.lock`.
It starts a private server with `-f /dev/null`, turns the status line off,
and attaches a client to an 80×24 Python PTY. `pyte` tracks the terminal cursor.

Expected: all three cursor checks pass, exit status 0.
Affected build: the check after the application update fails, exit status 1;
the checks before the update and after the synchronization timeout pass.

Observed on the pinned build: expected cursor `(18, 5)`, terminal cursor
`(80, 1)` (column, row). `synchronized_output_flag` remains 1 after the
application's end-of-update sequence, until the timeout.

To test another tmux build, install Python 3 and `pyte`, then run:

```sh
python3 repro.py /absolute/path/to/tmux logs
```

Use a fresh output directory for each run.

## Required information and logs

Following tmux's [contribution guidelines](https://github.com/tmux/tmux/blob/master/.github/CONTRIBUTING.md),
`logs/report.txt` records the platform (`uname -sp`), tmux version, terminal,
inside/outside `$TERM`, config and observed cursor positions.
The server and attached client run with `-vv`.

Attach `logs.zip` directly to the issue. It contains the report, tmux server,
client and output logs, and the PTY output (`terminal.bin`). The test uses a
temporary home, a clean environment and generated text.

Related reports: [#5525](https://github.com/tmux/tmux/issues/5525)
(cursor flicker during copy-mode redraws) and
[#5403](https://github.com/tmux/tmux/issues/5403)
(copy-mode refresh during synchronized application output).

## Comparison

```sh
nix run .#patched -- logs-patched
```

This applies `pane_mode = s->mode` in `server_client_reset_state()` during the
Nix build and runs the same test. The change uses the displayed screen's mode
when deciding whether to position its cursor.
