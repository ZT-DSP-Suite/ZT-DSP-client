# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 ZT-DSP Suite maintainers (copyright holder: SCAL-ROAM)

"""Protocol-layer exception hierarchy (Master Guide, Appendix H.5).

The upper layer must distinguish "retry" from "terminate" by exception type:
- ZTDSPSecurityError: security event — always terminate the session and
  securely wipe the keys; never retry;
- ZTDSPParamError: parameter problem — handshake-phase failure;
- SilentDropError (a subclass of ZTDSPParamError): a signal that **this
  side has already entered strict silence** — once the upper layer catches it,
  it must never again send any data to the peer or close the connection
  (the silent path has taken over; see Appendix F.2);
- ZTDSPProtocolError: frame-format problem;
- ZTDSPCryptoError: cryptographic failure (a low-order point is an attack in
  itself; handle it as a security event);
- ZTDSPTimeoutError: timeout (a half-packet timeout must be accompanied by a
  forced socket close).
"""

from __future__ import annotations


class ZTDSPError(Exception):
    """Base class for ZT-DSP protocol exceptions."""


class ZTDSPSecurityError(ZTDSPError):
    """Security event: PSK mismatch, anchor confirmation failure, replay /
    out-of-order delivery, session-ID mismatch, AEAD decryption failure,
    unknown payload format, two-way Token Hash verification failure, etc."""


class ZTDSPParamError(ZTDSPError):
    """Parameter problem: parameters on the two sides do not match, or a
    parameter value is illegal."""


class SilentDropError(ZTDSPParamError):
    """Strict silence signal (Appendix F.2): this side (the responder) has
    entered silent suspension — it sends no bytes and does not close the
    connection actively. The upper layer must never write data to the peer
    or close the connection again."""


class ZTDSPProtocolError(ZTDSPError):
    """Frame-format problem: length over the limit, invalid JSON, structural
    length contradiction, nonce length mismatch, etc."""


class ZTDSPCryptoError(ZTDSPError):
    """Cryptographic failure: weak DH output (low-order point / all-zero),
    derivation failure, algorithm not supported."""


class ZTDSPTimeoutError(ZTDSPError):
    """Timeout: handshake timeout, total read deadline exhausted, half-packet
    timeout, no packets in the data phase."""
