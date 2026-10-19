# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 ZT-DSP Suite maintainers (copyright holder: SCAL-ROAM)

"""Tests for the transport layer's handling of the input.

A server process started in the background has no terminal on its input, so the
input ends at once. The sending must stop there and the receiving must go on.
"""

import socket
import threading
import time

from zt_dsp_py.handshake import HandshakePeer
from zt_dsp_py.params import ZTDSPParams
from zt_dsp_py.session import SecureSession
from zt_dsp_py.transport import ChatSession

PSK = bytes(range(32))


def _pair():
    """Return two connected sockets with a finished handshake on both ends."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    port = server.getsockname()[1]
    server.listen(1)
    box = {}

    def listen_side() -> None:
        conn, _addr = server.accept()
        conn.settimeout(15)
        peer = HandshakePeer(PSK, ZTDSPParams(), "responder")
        material = peer.perform_handshake(conn)
        box["conn"] = conn
        box["session"] = SecureSession(material)

    worker = threading.Thread(target=listen_side)
    worker.start()
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(15)
    client.connect(("127.0.0.1", port))
    peer = HandshakePeer(PSK, ZTDSPParams(), "initiator")
    material = peer.perform_handshake(client)
    worker.join(15)
    server.close()
    return client, SecureSession(material), box["conn"], box["session"]


def test_end_of_input_stops_only_the_sending(monkeypatch) -> None:
    """The input ends: the sending stops and the session stays alive."""
    client, client_session, conn, server_session = _pair()
    chat = ChatSession(server_session, conn)

    def end_of_input(*_args, **_kwargs):
        raise EOFError()

    monkeypatch.setattr("builtins.input", end_of_input)
    chat._send_loop()

    assert chat._running is True
    client_session.send_packet(client, "still here".encode("utf-8"))
    assert server_session.recv_packet(conn) == "still here".encode("utf-8")
    chat.shutdown()
    client.close()
    conn.close()


def test_quit_command_closes_the_session(monkeypatch) -> None:
    """The quit command is an explicit order: the session closes."""
    client, _client_session, conn, server_session = _pair()
    chat = ChatSession(server_session, conn)
    monkeypatch.setattr("builtins.input", lambda *_args: "/quit")
    chat._send_loop()
    assert chat._running is False
    client.close()
    conn.close()


def test_disabled_input_keeps_receiving(monkeypatch) -> None:
    """With the input switched off, the session receives and reads nothing."""
    client, client_session, conn, server_session = _pair()
    chat = ChatSession(server_session, conn, read_stdin=False)

    def refuse(*_args, **_kwargs):
        raise AssertionError("the input must not be read")

    monkeypatch.setattr("builtins.input", refuse)
    worker = threading.Thread(target=chat.start)
    worker.start()
    try:
        client_session.send_packet(client, "served".encode("utf-8"))
        deadline = time.time() + 5
        while server_session.seq_recv < 0 and time.time() < deadline:
            time.sleep(0.05)
        assert server_session.seq_recv >= 0
    finally:
        client.close()
        worker.join(5)
        chat.shutdown()
        conn.close()
