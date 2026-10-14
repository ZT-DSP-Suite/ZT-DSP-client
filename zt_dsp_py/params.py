# -*- coding: utf-8 -*-
"""Protocol parameter set (Master Guide, Appendix B / F.1).

Every parameter may be declared freely by the server operator in their
database; both communicating parties must match exactly before they can
connect. On-wire structure of the parameter JSON: keys in lexicographic
order, compact separators, UTF-8 encoding (F.1 -- exactly 136 bytes under
the default parameters).

Version handling (1.1.0): the parameter JSON carries a mandatory
``proto`` field. The Phase 1 frame -- including this field -- is part of
the handshake transcript, so the negotiated version is covered by the
Phase 3 confirmation tags. A 1.0.0 peer sends no ``proto`` and is refused
outright rather than guessed at: that refusal is the downgrade block, and
no code path silently continues on an older protocol.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from .errors import ZTDSPParamError

# --- Default parameters (Appendix B.1) ---
RANDOM_LEN: int = 256          # Connection-random length (bits, multiple of 8)
RANDOM_RATE: int = 1024        # Random generation rate (times/sec)
WINDOW: int = 60               # Negotiation window (seconds; both parties must agree; != timestamp window)
TIME_WINDOW: int = 30          # Timestamp window (seconds, per-peer configurable)
KEY_LEN: int = 256             # Session key length (bits, only 128/192/256)
HASH_NAME: str = "SHA3-256"
AEAD_NAME: str = "AES-256-GCM"

# --- Upper-limit constants (Appendix F.6; all upper-limit checks must run before reading the corresponding payload) ---
MAX_PARAM_JSON: int = 4096         # Phase 1 param_json
MAX_IDENTITY: int = 8192           # Phase 1 identity_blob
MAX_NONCE: int = 512               # Phase 1 connection random
MAX_CIPHERTEXT: int = 1 << 20      # Phase 4 ct_len (1 MiB)
MAX_PAD: int = 2048                # Phase 4 random padding
# User plaintext limit = 1 MiB - 64 - fmt(1) - Token Hash(64) - ts(8) - next_seed(32) - pad_len(2) - MAX_PAD
MAX_PLAINTEXT: int = ((1 << 20) - 64 - 1 - 64 - 8 - 32 - 2 - MAX_PAD)  # 1046357

# module_flags validation limits (guards against recursive bombs / node explosion)
MAX_FLAG_DEPTH: int = 32
MAX_FLAG_NODES: int = 1024

# --- Version negotiation and security floor (1.1.0) ---
PROTO_VERSION: str = "1.1.0"                             # Protocol version spoken by this build
SUPPORTED_PROTO_VERSIONS: Tuple[str, ...] = ("1.1.0",)   # No silent fallback: anything else is rejected
MIN_KEY_BITS: int = 256                                 # Policy floor: never negotiate below 256-bit keys

_ALLOWED_FLAG_TYPES = (str, int, float, bool, list, dict, type(None))


def validate_module_flags(flags: Dict[str, Any]) -> None:
    """module_flags validation (F.1): keys must be strings; values may only be
    str/int/float/bool/list/dict/null; nesting depth <= 32 and total node
    count <= 1024. Uses explicit-stack iteration instead of recursion, so
    peer-controlled deep nesting cannot trigger a RecursionError."""
    if not isinstance(flags, dict):
        raise ZTDSPParamError(f"module_flags must be a dict, got {type(flags)}")
    stack: list = [(flags, 0)]
    nodes = 0
    while stack:
        current, depth = stack.pop()
        if depth > MAX_FLAG_DEPTH:
            raise ZTDSPParamError(f"module_flags nesting depth exceeds the limit of {MAX_FLAG_DEPTH}")
        for key, value in current.items():
            nodes += 1
            if nodes > MAX_FLAG_NODES:
                raise ZTDSPParamError(f"module_flags node count exceeds the limit of {MAX_FLAG_NODES}")
            if not isinstance(key, str):
                raise ZTDSPParamError(f"module_flags keys must be str, got {type(key)}")
            if isinstance(value, dict):
                stack.append((value, depth + 1))
            elif isinstance(value, list):
                for item in value:
                    nodes += 1
                    if nodes > MAX_FLAG_NODES:
                        raise ZTDSPParamError(
                            f"module_flags node count exceeds the limit of {MAX_FLAG_NODES}")
                    if isinstance(item, dict):
                        stack.append((item, depth + 1))
                    elif not isinstance(item, _ALLOWED_FLAG_TYPES):
                        raise ZTDSPParamError(
                            f"module_flags value type {type(item)} is not supported, "
                            f"only str/int/float/bool/list/dict/None are allowed")
            elif not isinstance(value, _ALLOWED_FLAG_TYPES):
                raise ZTDSPParamError(
                    f"module_flags value type {type(value)} is not supported, "
                    f"only str/int/float/bool/list/dict/None are allowed")


@dataclass(frozen=True)
class ZTDSPParams:
    """ZT-DSP protocol parameter set. frozen: cannot be accidentally modified during the handshake."""

    proto_version: str = PROTO_VERSION
    random_len: int = RANDOM_LEN
    random_rate: int = RANDOM_RATE
    window: int = WINDOW
    key_len: int = KEY_LEN
    hash_name: str = HASH_NAME
    aead_name: str = AEAD_NAME
    module_flags: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.random_len, int) or self.random_len <= 0 or self.random_len % 8 != 0:
            raise ZTDSPParamError("random_len must be a positive integer and a multiple of 8")
        if self.random_len // 8 > MAX_NONCE:
            raise ZTDSPParamError(
                f"random_len/8 must not exceed the connection random upper limit of {MAX_NONCE} bytes")
        if self.proto_version not in SUPPORTED_PROTO_VERSIONS:
            raise ZTDSPParamError(
                f"unsupported protocol version {self.proto_version!r}; this build speaks "
                f"{SUPPORTED_PROTO_VERSIONS} -- refusing to downgrade")
        if not isinstance(self.key_len, int) or self.key_len % 8 != 0:
            raise ZTDSPParamError("key_len must be an integer and a multiple of 8")
        if self.key_len < MIN_KEY_BITS:
            # Policy floor. Peer-supplied values reach us through from_wire(), which builds
            # through this same constructor, so an offered 128-bit key is rejected here too.
            raise ZTDSPParamError(
                f"key_len must be at least {MIN_KEY_BITS} bits; refusing to negotiate a "
                f"{self.key_len}-bit session key")
        if not isinstance(self.window, int) or self.window <= 0:
            raise ZTDSPParamError("window must be a positive integer")
        if not isinstance(self.random_rate, int) or self.random_rate <= 0:
            raise ZTDSPParamError("random_rate must be a positive integer")
        validate_module_flags(self.module_flags)

    # ------------------------------------------------------------------
    # On-wire serialization (F.1)
    # ------------------------------------------------------------------
    def to_wire(self) -> Dict[str, Any]:
        """On-wire key/value pairs of the parameter JSON. Key order is guaranteed by json.dumps(sort_keys=True).

        ``proto`` is mandatory: the negotiated version travels on the wire and, through the
        Phase 1 frame, into the handshake transcript.
        """
        return {
            "proto": self.proto_version,
            "random_len": self.random_len,
            "random_rate": self.random_rate,
            "window": self.window,
            "key_len": self.key_len,
            "hash": self.hash_name,
            "aead": self.aead_name,
            "module_flags": self.module_flags,
        }

    def to_json(self) -> bytes:
        """Compact JSON bytes (keys lexicographic, no spaces, UTF-8). 136 bytes under the default parameters."""
        try:
            return json.dumps(
                self.to_wire(), separators=(",", ":"), sort_keys=True,
                ensure_ascii=False,
            ).encode("utf-8")
        except (ValueError, TypeError, RecursionError) as exc:
            raise ZTDSPParamError(f"parameter serialization failed: {exc}") from exc

    @classmethod
    def from_wire(cls, d: Any) -> "ZTDSPParams":
        """Builds a parameter set from the peer's JSON dict. Peer-controlled
        input: all type/value errors are funneled into ZTDSPParamError;
        ValueError/TypeError must not escape (Appendix H.4)."""
        if not isinstance(d, dict):
            raise ZTDSPParamError("peer parameter payload must be a JSON object")
        try:
            module_flags = d.get("module_flags", {})
            if not isinstance(module_flags, dict):
                raise ZTDSPParamError("module_flags must be a dict")
            proto = d.get("proto")
            if proto is None:
                # A pre-1.1 peer sends no version field. Guessing one here is exactly the
                # downgrade this field exists to prevent, so refuse and say why.
                raise ZTDSPParamError(
                    "peer sent no proto version field (pre-1.1 peer); refusing to downgrade "
                    f"from {PROTO_VERSION}")
            return cls(
                proto_version=str(proto),
                random_len=int(d.get("random_len", RANDOM_LEN)),
                random_rate=int(d.get("random_rate", RANDOM_RATE)),
                window=int(d.get("window", WINDOW)),
                key_len=int(d.get("key_len", KEY_LEN)),
                hash_name=str(d.get("hash", HASH_NAME)),
                aead_name=str(d.get("aead", AEAD_NAME)),
                module_flags=dict(module_flags),
            )
        except (ZTDSPParamError, ValueError, TypeError, RecursionError) as exc:
            if isinstance(exc, ZTDSPParamError):
                raise
            raise ZTDSPParamError(f"peer parameters invalid: {exc}") from exc

    # ------------------------------------------------------------------
    # Eight-item matching check (F.1: fixed order; stop at the first mismatch)
    # ------------------------------------------------------------------
    def match_error(self, peer: "ZTDSPParams") -> Optional[str]:
        """Compares item by item against the peer's parameters; returns the reason of the first mismatch, or None when all are equal."""
        if peer.proto_version != self.proto_version:
            return "proto_version mismatch"
        if peer.random_len != self.random_len:
            return "random_len mismatch"
        if peer.key_len != self.key_len:
            return "key_len mismatch"
        if peer.window != self.window:
            return "window mismatch"
        if peer.random_rate != self.random_rate:
            return "random_rate mismatch"
        if peer.hash_name != self.hash_name:
            return "hash mismatch"
        if peer.aead_name != self.aead_name:
            return "aead mismatch"
        if peer.module_flags != self.module_flags:
            return "module_flags mismatch"
        return None

    def padding_range(self) -> Optional[Tuple[int, int]]:
        """The padding range is held separately on the sender side (CLI --padding-min/max) and does not enter the parameter JSON."""
        return None
