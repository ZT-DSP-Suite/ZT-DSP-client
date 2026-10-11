# -*- coding: utf-8 -*-
"""Cryptographic primitives layer (Master Guide 1.0.0 Section 4.2 /
Appendices F.3-F.5).

Default suite: X25519 + HKDF-SHA3-256 + HMAC-SHA3-256 + AES-256-GCM.
The hash algorithm is selected by the hash_name parameter (officially
supported: SHA3-256/384/512 and SHA-256/384/512, Appendix F.1); the
official AEAD implementation contains only AES-256-GCM.

Security statements:
- X25519 low-order point / out-of-bounds public keys (all zeros, u=1,
  etc.) must converge to ZTDSPCryptoError -
  these are peer-controllable inputs, and a raw ValueError must never
  escape (Appendix F.3 DH failure judgment);
- All-zero DH output is likewise judged as a low-order point attack;
- AEAD decryption failure converges to ZTDSPSecurityError (an
  authentication failure means tampering or key mismatch);
- The Python layer cannot guarantee that OpenSSL-internal memory is
  erased; secure_zero is best effort.
"""

from __future__ import annotations

import hmac as _stdlib_hmac
import math
import secrets
from collections import Counter
from typing import Optional, Tuple, Union

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes, hmac as _crypto_hmac, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from .errors import ZTDSPCryptoError, ZTDSPSecurityError

X25519_PUB_LEN: int = 32
SESSION_SALT_LEN: int = 32
NEXT_SEED_LEN: int = 32
GCM_NONCE_LEN: int = 12

_HASH_MAP = {
    "SHA3-256": hashes.SHA3_256,
    "SHA3-384": hashes.SHA3_384,
    "SHA3-512": hashes.SHA3_512,
    "SHA-256": hashes.SHA256,
    "SHA-384": hashes.SHA384,
    "SHA-512": hashes.SHA512,
}


# =============================================================================
# Basic helpers
# =============================================================================

def secure_random(n: int) -> bytes:
    """Cryptographically secure random bytes."""
    return secrets.token_bytes(n)


def secure_zero(buf: Optional[Union[bytearray, memoryview]]) -> None:
    """Securely zero a memory buffer (best effort; OpenSSL-internal
    memory is not controllable from the Python layer)."""
    if buf is None:
        return
    try:
        for i in range(len(buf)):
            buf[i] = 0
    except Exception:
        pass


def constant_time_compare(a: bytes, b: bytes) -> bool:
    """Constant-time comparison, defending against timing side-channel
    attacks (Appendix F.4 confirmation tag check)."""
    return _stdlib_hmac.compare_digest(a, b)


def hmac_sha3(key: bytes, message: bytes) -> bytes:
    """HMAC-SHA3-256 (fixed algorithm - token hash derivation does not
    vary with params.hash_name; see Master Guide 1.0.0 Section
    4.1.1 placeholder path)."""
    h = _crypto_hmac.HMAC(key, hashes.SHA3_256())
    h.update(message)
    return h.finalize()


def check_entropy(data: bytes, min_bits: float = 3.5) -> None:
    """Entropy check; catches obviously weak PSK (Appendix E.4: can
    only catch obviously weak keys)."""
    counts = Counter(data)
    length = len(data)
    if length == 0:
        raise ValueError("Data is empty")
    entropy = -sum((c / length) * math.log2(c / length) for c in counts.values())
    if entropy < min_bits:
        raise ValueError(
            f"PSK entropy too low ({entropy:.2f} bits/byte); use a cryptographically secure random source")


# =============================================================================
# Crypto suite
# =============================================================================

class CryptoSuite:
    """Cryptographic primitive set bound to the hash_name parameter."""

    __slots__ = ("hash_name", "aead_name", "_hash_cls")

    def __init__(self, hash_name: str = "SHA3-256", aead_name: str = "AES-256-GCM") -> None:
        hash_cls = _HASH_MAP.get(hash_name)
        if hash_cls is None:
            raise ZTDSPCryptoError(
                f"Unsupported hash algorithm: {hash_name}; available: {', '.join(sorted(_HASH_MAP))}")
        if aead_name != "AES-256-GCM":
            raise ZTDSPCryptoError(
                f"Unsupported AEAD algorithm: {aead_name}; the official implementation only contains AES-256-GCM")
        self.hash_name = hash_name
        self.aead_name = aead_name
        self._hash_cls = hash_cls

    # ------------------------------------------------------------------
    # HKDF / HMAC
    # ------------------------------------------------------------------
    def hkdf(self, ikm: bytes, info: str, length_bits: int,
             salt: Optional[bytes] = None) -> bytes:
        """HKDF (RFC 5869). Note that salt is a **standalone salt
        parameter**, not material concatenated into the IKM (General
        Directive, Section 4.2.2)."""
        hkdf = HKDF(
            algorithm=self._hash_cls(),
            length=length_bits // 8,
            salt=salt,
            info=info.encode("utf-8"),
        )
        return hkdf.derive(ikm)

    def hmac(self, key: bytes, message: bytes) -> bytes:
        """HMAC-<hash>."""
        h = _crypto_hmac.HMAC(key, self._hash_cls())
        h.update(message)
        return h.finalize()

    # ------------------------------------------------------------------
    # X25519 (Appendix F.3 ordering constraints and failure judgment)
    # ------------------------------------------------------------------
    def generate_ephemeral_keypair(self) -> Tuple[X25519PrivateKey, bytes]:
        """Generate an ephemeral X25519 key pair; returns
        (private key object, 32B raw public key)."""
        priv = X25519PrivateKey.generate()
        pub = priv.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return priv, pub

    def dh_exchange(self, private_key: X25519PrivateKey,
                    peer_public_bytes: bytes) -> bytes:
        """X25519 shared secret computation. Failure judgments (F.3):
        public key length != 32B; computation raises an error (low-order
        point or out-of-bounds public key); all-zero output. All converge
        to ZTDSPCryptoError."""
        if len(peer_public_bytes) != X25519_PUB_LEN:
            raise ZTDSPCryptoError("Peer public key length is abnormal")
        try:
            peer_pub = X25519PublicKey.from_public_bytes(peer_public_bytes)
            dh = private_key.exchange(peer_pub)
        except (ValueError, TypeError) as exc:
            raise ZTDSPCryptoError(
                f"Invalid peer public key (low-order point or out of bounds): {exc}") from exc
        if dh == b"\x00" * len(dh):
            raise ZTDSPCryptoError("Weak DH output detected (all zeros); possible low-order point attack")
        return dh

    # ------------------------------------------------------------------
    # AEAD (Appendix F.5)
    # ------------------------------------------------------------------
    def aead_encrypt(self, key: bytes, nonce: bytes, plaintext: bytes,
                     aad: bytes) -> bytes:
        """AES-256-GCM encryption; output = ciphertext || 16B
        authentication tag."""
        return AESGCM(key).encrypt(nonce, plaintext, aad)

    def aead_decrypt(self, key: bytes, nonce: bytes, ciphertext: bytes,
                     aad: bytes) -> bytes:
        """AES-256-GCM decryption and authentication. Any failure
        converges to ZTDSPSecurityError."""
        try:
            return AESGCM(key).decrypt(nonce, ciphertext, aad)
        except InvalidTag as exc:
            raise ZTDSPSecurityError(
                f"AEAD decryption or integrity check failed: {exc}") from exc
        except Exception as exc:
            raise ZTDSPSecurityError(
                f"AEAD decryption or integrity check failed: {exc}") from exc
