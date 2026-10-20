# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 ZT-DSP Suite maintainers (copyright holder: SCAL-ROAM)

"""End-to-end test: full real-TCP two-end flow + CLI contract (the automated version of the local two-instance experience in the README quick start)."""

import socket
import subprocess
import sys
import threading
from pathlib import Path

from zt_dsp_py.crypto import secure_random
from zt_dsp_py.errors import ZTDSPError
from zt_dsp_py.frames import force_close_socket
from zt_dsp_py.handshake import HandshakePeer
from zt_dsp_py.params import ZTDSPParams
from zt_dsp_py.session import SecureSession
from zt_dsp_py.version import format_version

REPO_ROOT = Path(__file__).resolve().parents[2]
PSK = bytes(range(32))


def test_localhost_two_instance_flow() -> None:
    """Listener accepts → four-phase handshake → two messages exchanged in each direction → close and clean up."""
    params = ZTDSPParams()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    port = server.getsockname()[1]
    server.listen(1)
    outcome = {}

    def listen_side() -> None:
        conn, _addr = server.accept()
        conn.settimeout(15)
        peer = HandshakePeer(PSK, params, "responder")
        material = peer.perform_handshake(conn)
        session = SecureSession(material)
        outcome["recv1"] = session.recv_packet(conn)
        session.send_packet(conn, "responder receipt".encode("utf-8"))
        outcome["recv2"] = session.recv_packet(conn)
        session.wipe()
        force_close_socket(conn)

    t = threading.Thread(target=listen_side)
    t.start()

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(15)
    client.connect(("127.0.0.1", port))
    cpeer = HandshakePeer(PSK, params, "initiator")
    cmaterial = cpeer.perform_handshake(client)
    csession = SecureSession(cmaterial)
    csession.send_packet(client, "hello, responder".encode("utf-8"))
    reply = csession.recv_packet(client)
    csession.send_packet(client, b"bye")
    csession.wipe()
    force_close_socket(client)

    t.join(15)
    force_close_socket(server)

    assert outcome["recv1"] == "hello, responder".encode("utf-8")
    assert reply == "responder receipt".encode("utf-8")
    assert outcome["recv2"] == b"bye"


def test_psk_mismatch_over_tcp_no_crash() -> None:
    """PSK mismatch: the initiator sees the confirmation tag comparison fail → security error (the peer returns no diagnostic at all)."""
    params = ZTDSPParams()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    port = server.getsockname()[1]
    server.listen(1)
    outcome = {}

    def listen_side() -> None:
        conn, _addr = server.accept()
        conn.settimeout(15)
        peer = HandshakePeer(secure_random(32), params, "responder")
        try:
            peer.perform_handshake(conn)
        except Exception as exc:  # noqa: BLE001
            outcome["error"] = exc
        finally:
            force_close_socket(conn)

    t = threading.Thread(target=listen_side)
    t.start()

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(15)
    client.connect(("127.0.0.1", port))
    cpeer = HandshakePeer(PSK, params, "initiator")
    try:
        cpeer.perform_handshake(client)
        raise AssertionError("handshake must fail when the PSK does not match")
    except ZTDSPError as exc:
        assert "anchor confirmation failed" in str(exc)
    finally:
        force_close_socket(client)

    t.join(15)
    force_close_socket(server)
    from zt_dsp_py.errors import ZTDSPSecurityError

    assert isinstance(outcome.get("error"), ZTDSPSecurityError)


# =============================================================================
# CLI contract (README main parameters)
# =============================================================================


def test_cli_version() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "zt_dsp_py", "--version"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
        encoding="utf-8",
    )
    assert proc.stdout.strip() == format_version()
    expected = "ZT-DSP_PY-1.0.0 (docs 1.0.1)"
    assert proc.stdout.strip() == expected


def test_cli_requires_psk() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "zt_dsp_py", "--role", "listen"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    assert proc.returncode != 0
    assert "must be provided" in proc.stderr


def test_cli_rejects_weak_psk() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "zt_dsp_py", "--role", "listen", "--psk", "00" * 32],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    assert proc.returncode != 0
    assert "entropy too low" in proc.stderr


def test_cli_rejects_bad_padding_range() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "zt_dsp_py",
            "--role",
            "listen",
            "--psk",
            "ab" * 32,
            "--padding-min",
            "2000",
            "--padding-max",
            "100",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    assert proc.returncode != 0
