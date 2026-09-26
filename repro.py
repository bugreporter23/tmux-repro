#!/usr/bin/env python3
"""Compare tmux's copy cursor with the cursor in its terminal output."""

import argparse
import fcntl
import os
from pathlib import Path
import pty
import select
import struct
import subprocess
import sys
import tempfile
import termios
import time
import zipfile

import pyte


class Terminal(pyte.Screen):
    def report_device_status(self, mode, private=False):
        # Private DSR includes tmux's colour-theme query (CSI ? 996 n).
        if not private:
            super().report_device_status(mode)


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("tmux", type=Path, help="tmux executable")
parser.add_argument("output", type=Path, help="new directory for logs")
parser.add_argument("--producer", type=Path,
                    default=Path(__file__).with_name("producer.py"))
parser.add_argument("--revision", help="source revision to include in the report")
args = parser.parse_args()
binary = str(args.tmux.resolve(strict=True))
output = args.output.resolve()
output.mkdir(mode=0o700)
screen = Terminal(80, 24)
stream = pyte.ByteStream(screen)
report = []


def record(message):
    print(message, flush=True)
    report.append(message)


with tempfile.TemporaryDirectory(prefix="tmux-repro-") as tmp:
    root = Path(tmp)
    fifo = root / "control"
    os.mkfifo(fifo)
    environment = {
        "HOME": tmp, "TMPDIR": tmp, "PATH": "/usr/bin:/bin",
        "SHELL": "/bin/sh", "TERM": "xterm-256color", "LC_ALL": "C",
    }
    command = [binary, "-S", str(root / "socket")]

    def tmux(*arguments):
        return subprocess.check_output(
            [*command, *arguments], cwd=output, env=environment, text=True,
            timeout=5,
        ).strip()

    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
    client = None
    control = os.open(fifo, os.O_RDWR)
    with (output / "terminal.bin").open("wb") as capture:
        def drain(seconds=0.1):
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                ready, _, _ = select.select(
                    [master], [], [], max(0, deadline - time.monotonic())
                )
                if ready:
                    data = os.read(master, 65536)
                    if not data:
                        raise RuntimeError("tmux client closed its terminal")
                    capture.write(data)
                    stream.feed(data)

        def check_cursor(label):
            tmux("send-keys", "-t", "test:0.0", "-X", "cursor-left")
            drain()
            state = tmux("display-message", "-p", "-t", "test:0.0",
                         "#{copy_cursor_x},#{copy_cursor_y},#{synchronized_output_flag}")
            x, y, sync = map(int, state.split(","))
            expected = (x + 1, y + 1)
            # pyte uses x == columns for a cursor awaiting automatic wrap.
            actual = (min(screen.cursor.x + 1, screen.columns), screen.cursor.y + 1)
            matches = actual == expected
            record(f"{label}: expected={expected}, terminal={actual}, "
                   f"app_sync={sync}: {'PASS' if matches else 'FAIL'}")
            return matches

        tmux("-vv", "-f", "/dev/null", "new-session", "-d", "-s", "test",
             "-x", "80", "-y", "24", sys.executable, "-u",
             str(args.producer.resolve(strict=True)), str(fifo),
             str(output / "inside-term.txt"))
        try:
            tmux("set-option", "-g", "status", "off")
            client = subprocess.Popen(
                [*command, "-vv", "attach-session", "-t", "test"],
                stdin=slave, stdout=slave, stderr=slave,
                cwd=output, env=environment,
            )
            drain(0.5)
            record(subprocess.check_output(["uname", "-sp"], text=True).strip())
            record(tmux("-V"))
            if args.revision:
                record("Source revision: " + args.revision)
            record(f"Binary: {binary}")
            record("Terminal: Python PTY (80x24), output interpreted by pyte")
            record("TERM outside: " + environment["TERM"])
            record("TERM inside: " + (output / "inside-term.txt").read_text().strip())
            record("Config: /dev/null; status off")
            record("Cursor coordinates: (column, row), starting at 1")
            tmux("copy-mode", "-t", "test:0.0")
            drain()
            if not check_cursor("Before application update"):
                raise RuntimeError("baseline cursor check failed")
            os.write(control, b"u")
            drain()
            reproduced = not check_cursor("After complete application update")
            drain(1.1)
            if not check_cursor("After synchronization timeout"):
                raise RuntimeError("cursor did not recover after timeout")
            record("BUG REPRODUCED" if reproduced else "PASS: cursor stayed correct")
        finally:
            tmux("kill-server")
            if client is not None:
                client.wait(timeout=5)
            os.close(control)
            os.close(slave)
            os.close(master)
            (output / "report.txt").write_text("\n".join(report) + "\n")

archive = output.with_suffix(".zip")
with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as bundle:
    for path in sorted(output.iterdir()):
        bundle.write(path, path.name)
print(f"Logs: {archive}")
sys.exit(1 if reproduced else 0)
