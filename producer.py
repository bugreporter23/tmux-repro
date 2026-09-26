"""Emit one complete synchronized update when the test writes to the FIFO."""

import os
import pathlib
import sys

control = os.open(sys.argv[1], os.O_RDWR)
pathlib.Path(sys.argv[2]).write_text(os.environ["TERM"] + "\n")
os.write(1, b"copy-mode cursor test: abcdefghijklmnopqrstuvwxyz\r\n" * 10)
os.write(1, b"\x1b[5;20H")
while os.read(control, 1):
    os.write(1, b"\x1b[?2026h\x1b[7;11H.\x1b[?2026l")
