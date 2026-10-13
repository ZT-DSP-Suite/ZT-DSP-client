# -*- coding: utf-8 -*-
"""ZT-DSP - Zero Trust Dynamic Synchronization Protocol.

Reference implementation (client version ZT-DSP_PY-1.0.0, applying to the
"ZT-DSP Protocol Master Guide", total-guide version 1.0.0).

Programming usage:

    from zt_dsp_py import ZTDSPParams, HandshakePeer, SecureSession

    peer = HandshakePeer(psk, ZTDSPParams(), role="responder")
    material = peer.perform_handshake(sock)      # blocks until the four-phase handshake completes
    session = SecureSession(material)
    session.send_packet(sock, b"hello")
    plaintext = session.recv_packet(sock)

This minimal release implements the protocol itself only (four-phase handshake +
full-duplex encrypted transmission). The extension modules (hook system, TCA,
AORS, Ocean Mode, and Emergency Mode) are out of scope.
"""

from .errors import (
    SilentDropError,
    ZTDSPCryptoError,
    ZTDSPError,
    ZTDSPParamError,
    ZTDSPProtocolError,
    ZTDSPSecurityError,
    ZTDSPTimeoutError,
)
from .handshake import HandshakePeer, SessionMaterial
from .identity import derive_p2p_identity
from .params import ZTDSPParams
from .session import SecureSession
from .version import (
    CODE_VERSION,
    DOCS_VERSION,
    FOLLOWS_DOC,
    FOLLOWS_DOC_PATH,
    IMPLEMENTATION_ID,
    LANGUAGE_PREFIX,
    format_version,
)

__version__ = CODE_VERSION
__docs_version__ = DOCS_VERSION
__implementation__ = IMPLEMENTATION_ID

__all__ = [
    "CODE_VERSION", "DOCS_VERSION", "FOLLOWS_DOC", "FOLLOWS_DOC_PATH",
    "IMPLEMENTATION_ID", "LANGUAGE_PREFIX",
    "format_version", "__version__", "__docs_version__", "__implementation__",
    "ZTDSPParams", "HandshakePeer", "SessionMaterial", "SecureSession",
    "derive_p2p_identity",
    "ZTDSPError", "ZTDSPSecurityError", "ZTDSPParamError", "SilentDropError",
    "ZTDSPProtocolError", "ZTDSPCryptoError", "ZTDSPTimeoutError",
]
