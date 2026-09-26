#!/usr/bin/env python3
"""Show the copy-mode cursor under continuous application updates."""

import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import zipfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("tmux", type=Path, help="tmux executable")
parser.add_argument("output", type=Path, help="new directory for logs")
parser.add_argument("--producer", type=Path,
                    default=Path(__file__).with_name("producer.py"))
parser.add_argument("--revision", help="source revision to include in the report")
args = parser.parse_args()
if not sys.stdin.isatty() or not sys.stdout.isatty():
    parser.error("run this demo in a terminal")
if "TMUX" in os.environ:
    parser.error("run this demo from a terminal outside tmux")

binary = str(args.tmux.resolve(strict=True))
producer = str(args.producer.resolve(strict=True))
output = args.output.resolve()
output.mkdir(mode=0o700)
columns, rows = os.get_terminal_size()
report = [
    subprocess.check_output(["uname", "-sp"], text=True).strip(),
    f"Binary: {binary}",
    "Terminal: attached directly to the invoking terminal",
    "TERM outside: " + os.environ["TERM"],
    "Config: /dev/null; status line shows demo instructions",
]
if args.revision:
    report.append("Source revision: " + args.revision)

updates = True


def toggle_updates(signum, frame):
    global updates
    updates = not updates


signal.signal(signal.SIGUSR1, toggle_updates)

with tempfile.TemporaryDirectory(prefix="tmux-repro-") as tmp:
    root = Path(tmp)
    fifo = root / "control"
    os.mkfifo(fifo)
    environment = {
        "HOME": tmp, "TMPDIR": tmp, "PATH": "/usr/bin:/bin",
        "SHELL": "/bin/sh", "TERM": os.environ["TERM"], "LC_ALL": "C",
    }
    command = [binary, "-S", str(root / "socket")]

    def tmux(*arguments):
        return subprocess.check_output(
            [*command, *arguments], cwd=output, env=environment, text=True,
            timeout=5,
        ).strip()

    control = os.open(fifo, os.O_RDWR)
    client = None
    tmux("-vv", "-f", "/dev/null", "new-session", "-d", "-s", "test",
         "-x", str(columns), "-y", str(rows), sys.executable, "-u",
         producer, str(fifo), str(output / "inside-term.txt"))
    try:
        report.append(tmux("-V"))
        tmux("bind-key", "-n", "F2", "run-shell", f"kill -USR1 {os.getpid()}")
        tmux("set-option", "-g", "status-format[0]",
             "Updates ON (30 Hz) | F2: pause/resume | Arrows: cursor | Ctrl-b d: exit")
        client = subprocess.Popen(
            [*command, "-vv", "attach-session", "-t", "test"],
            cwd=output, env=environment,
        )
        time.sleep(0.5)
        report.append("TERM inside: " + (output / "inside-term.txt").read_text().strip())
        tmux("copy-mode", "-t", "test:0.0")
        previous_updates = None
        while client.poll() is None:
            if updates != previous_updates:
                label = "ON (30 Hz)" if updates else "PAUSED"
                tmux("set-option", "-g", "status-format[0]",
                     f"Updates {label} | F2: pause/resume | Arrows: cursor | Ctrl-b d: exit")
                report.append(f"{time.time():.6f}: application updates {label}")
                previous_updates = updates
            if updates:
                os.write(control, b"u")
            time.sleep(1 / 30)
    finally:
        tmux("kill-server")
        if client is not None:
            client.wait(timeout=5)
        os.close(control)
        (output / "report.txt").write_text("\n".join(report) + "\n")

archive = output.with_suffix(".zip")
with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as bundle:
    for path in sorted(output.iterdir()):
        bundle.write(path, path.name)
print(f"Logs: {archive}")
