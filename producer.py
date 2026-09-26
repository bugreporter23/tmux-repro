"""Emit one complete synchronized update when the test writes to the FIFO."""

import os
import pathlib
import sys

control = os.open(sys.argv[1], os.O_RDWR)
pathlib.Path(sys.argv[2]).write_text(os.environ["TERM"] + "\n")
os.write(1, (
    b"Move the selection with the arrow keys. Watch the cursor.\r\n"
    b"Application updates run continuously at 30 Hz. F2 pauses/resumes.\r\n"
    b"The cursor should follow your keys while updates are running.\r\n"
    b"\r\n"
    + b"abcdefghijklmnopqrstuvwxyz 0123456789 ABCDEFGHIJKLMNOPQRSTUVWXYZ\r\n" * 6
))
os.write(1, b"\x1b[5;20H")
while os.read(control, 1):
    os.write(1, b"\x1b[?2026h\x1b[7;11H.\x1b[?2026l")
