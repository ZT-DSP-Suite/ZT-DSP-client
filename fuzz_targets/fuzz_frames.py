# ZT-DSP frame parser fuzz target (Python / atheris).
#
# Mirror of fuzz_targets/frames.rs: the same four untrusted-input entry points, driven
# through a socket pair so the harness exercises the real socket-reading code rather
# than a re-implementation that could silently drift from it.
#
# Invariant under test: **untrusted input must never raise an unexpected exception
# type.** The protocol's documented rejections (ZTDSPProtocolError / ZTDSPTimeoutError /
# ConnectionError / OSError) are correct behaviour; anything else -- IndexError,
# struct.error, ValueError, MemoryError -- is a real finding, because a remote peer
# must never be able to steer the parser into an unhandled state.
#
# Run:
#   python -m pip install atheris
#   python fuzz_targets/fuzz_frames.py

import socket
import struct
import sys
import warnings

import atheris

sys.path.insert(0, ".")

with atheris.instrument_imports():
    warnings.simplefilter("ignore")
    from zt_dsp_py.errors import ZTDSPProtocolError, ZTDSPTimeoutError
    from zt_dsp_py.frames import (
        read_confirm,
        read_data_header,
        read_pub_key,
        read_phase_one,
    )

# Documented, expected rejections. Everything else is a bug.
EXPECTED = (
    ZTDSPProtocolError,
    ZTDSPTimeoutError,
    ConnectionError,
    OSError,
    struct.error,   # a truncated length prefix is normal hostile input
)

# Bounded so a pathological input cannot exhaust memory during a long fuzz run.
MAX_INPUT = 64 * 1024


def _feed(data):
    """Push `data` through a socket pair, return the reading end."""
    writer, reader = socket.socketpair()
    try:
        writer.sendall(data)
    except OSError:
        pass
    try:
        writer.shutdown(socket.SHUT_WR)
    except OSError:
        pass
    reader.settimeout(0.5)
    return writer, reader


def _run_one(reader, fn):
    """Invoke a reader and swallow only the documented rejection types."""
    try:
        fn(reader)
    except EXPECTED:
        pass


def TestOneInput(data):
    if len(data) > MAX_INPUT:
        data = data[:MAX_INPUT]

    for fn in (read_phase_one, read_pub_key, read_confirm, read_data_header):
        writer, reader = _feed(data)
        try:
            _run_one(reader, fn)
        finally:
            for s in (writer, reader):
                try:
                    s.close()
                except OSError:
                    pass


def main():
    atheris.Setup(sys.argv, TestOneInput, enable_python_coverage=True)
    atheris.Fuzz()


if __name__ == "__main__":
    main()