#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ZT-DSP_RS-1.0.0 cross-language interop verification (single file).

All scenarios bind to the 127.0.0.1 loopback only. Suites:

  [interop]  with ZT-DSP_PY-1.0.0 (the current Python reference implementation, conforming to docs 1.0.0)
    A. Python listens (responder) ← Rust connects (initiator)   → expected: handshake + bidirectional message exchange
    B. Rust listens (responder)   ← Python connects (initiator) → expected: handshake + bidirectional message exchange

Usage:
  python interop_test.py [--rust-bin <zt-dsp-rs executable path>] [--suite interop]

Default binary lookup order:
  1) --rust-bin argument
  2) environment variable ZT_DSP_RS_BIN
  3) target/release/zt-dsp-rs(.exe)   (standard build path inside this directory)
"""

import argparse
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent                 # zt_dsp_rs → repository root

MSG_RS_TO_PY = "hello-from-rust-installer"
MSG_PY_TO_RS = "hello-from-python-reference"

py = sys.executable


def find_rust_bin(arg):
    candidates = []
    if arg:
        candidates.append(Path(arg))
    env = os.environ.get("ZT_DSP_RS_BIN")
    if env:
        candidates.append(Path(env))
    exe = "zt-dsp-rs.exe" if os.name == "nt" else "zt-dsp-rs"
    candidates.append(HERE / "target" / "release" / exe)
    for c in candidates:
        if c.is_file():
            return c
    raise SystemExit(
        "[!] zt-dsp-rs executable not found. Build it first and pass the path via "
        "--rust-bin, or set the environment variable ZT_DSP_RS_BIN."
    )


def spawn(cmd, **kw):
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True,
                            encoding="utf-8", errors="replace", bufsize=1, **kw)


def key_lines(t):
    keep = []
    for line in (t or "").splitlines():
        s = line.strip()
        if any(k in s for k in ("Handshake complete", "Handshake failed", "Anchor confirmed", "Security error",
                                "Silent Drop", "Connection", "Listening", "Failed", "Error")):
            keep.append("    " + s)
    return "\n".join(keep[-12:]) or "    (no key output)"


def run_scenario(name, listen_cmd, connect_cmd, wait_before_connect=1.5,
                 verbose=False, exchange=True):
    print(f"\n=== {name} ===")
    la = spawn(listen_cmd)
    time.sleep(wait_before_connect)
    ca = spawn(connect_cmd)
    try:
        if exchange:
            time.sleep(2.5)  # leave time for the handshake
            assert ca.stdin and la.stdin
            ca.stdin.write(MSG_RS_TO_PY + "\n")
            ca.stdin.flush()
            time.sleep(0.5)
            la.stdin.write(MSG_PY_TO_RS + "\n")
            la.stdin.flush()
            time.sleep(1.5)
            la.stdin.write("/quit\n")
            ca.stdin.write("/quit\n")
            la.stdin.flush()
            ca.stdin.flush()
        lo = la.communicate(timeout=40)[0]
        co = ca.communicate(timeout=40)[0]
    except subprocess.TimeoutExpired:
        la.kill(); ca.kill()
        lo = la.communicate()[0]; co = ca.communicate()[0]
        print("[timeout] process did not exit within 40 s (force-killed)")
    if verbose:
        print("--- listener full output ---")
        print(lo)
        print("--- connector full output ---")
        print(co)
    print("--- listener key output ---")
    print(key_lines(lo))
    print("--- connector key output ---")
    print(key_lines(co))
    return (lo or "") + "\n" + (co or "")


# =============================================================================
# [interop] interop with the current Python reference implementation
# =============================================================================

def suite_interop(rust_bin, port):
    psk = secrets.token_hex(32)
    # The Python side needs the repo root on PYTHONPATH to run as -m zt_dsp_py;
    # inject it into this process's environment; all children inherit it.
    os.environ["PYTHONPATH"] = str(REPO_ROOT)
    os.environ["PYTHONIOENCODING"] = "utf-8"
    py_launch = [py, "-u", "-m", "zt_dsp_py"]

    def rust_cmd(role, p):
        return [str(rust_bin), "--role", role, "--host", "127.0.0.1",
                "--port", str(p), "--psk", psk]

    def py_cmd(role, p):
        return py_launch + ["--role", role, "--port", str(p), "--psk", psk]

    ok = True
    for name, lcmd, ccmd, port_off in [
        ("A (Python listens ← Rust connects)", py_cmd("listen", port), rust_cmd("connect", port), 0),
        ("B (Rust listens ← Python connects)", rust_cmd("listen", port + 1), py_cmd("connect", port + 1), 0),
    ]:
        out = run_scenario(name, lcmd, ccmd)
        passed = ("Handshake complete" in out
                  and MSG_RS_TO_PY in out
                  and MSG_PY_TO_RS in out)
        print(f">> Result: {'[OK] pass: handshake + bidirectional message exchange' if passed else '[!] fail'}")
        ok = ok and passed
        time.sleep(1)

    if ok:
        print("\n[[ok]] interop suite passed: ZT-DSP_RS-1.0.0 and ZT-DSP_PY-1.0.0 interoperate on the wire"
              "(both conforming to docs 1.0.0)")
    else:
        print("\n[!] interop suite has failing scenarios")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rust-bin", default=None)
    ap.add_argument("--suite", choices=["all", "interop"], default="all")
    ap.add_argument("--port", type=int, default=37441)
    args = ap.parse_args()

    rust_bin = find_rust_bin(args.rust_bin)
    print(f"Rust binary: {rust_bin}")

    ok = True
    if args.suite in ("all", "interop"):
        ok = suite_interop(rust_bin, args.port) and ok

    print("\n[[ok]] all selected suites passed" if ok else "\n[!] failing scenarios present, see output above")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
