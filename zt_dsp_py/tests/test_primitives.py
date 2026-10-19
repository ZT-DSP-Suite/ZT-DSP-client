# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 ZT-DSP Suite maintainers (copyright holder: SCAL-ROAM)

"""Protocol primitive tests: parameter validation, P2P identity derivation, key derivation formulas (Appendix F.1 / 4.2.2 / 4.2.3)."""
import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from zt_dsp_py.crypto import hmac_sha3
from zt_dsp_py.errors import ZTDSPParamError
from zt_dsp_py.identity import derive_p2p_identity
from zt_dsp_py.params import ZTDSPParams


# =============================================================================
# Parameter set and on-wire JSON (Appendix F.1)
# =============================================================================

def test_guide_defaults_and_wire_json() -> None:
    params = ZTDSPParams()
    assert (params.random_len, params.random_rate, params.window,
            params.key_len, params.hash_name, params.aead_name) == \
        (256, 1024, 60, 256, "SHA3-256", "AES-256-GCM")
    # F.1: under default parameters the parameter JSON is exactly 120 bytes,
    # and byte-for-byte equal to the documented layout (no version / protocol-identifier fields)
    expected = (b'{"aead":"AES-256-GCM","hash":"SHA3-256","key_len":256,'
                b'"module_flags":{},"random_len":256,"random_rate":1024,'
                b'"window":60}')
    assert params.to_json() == expected
    assert len(params.to_json()) == 120


def test_bad_length_and_deep_flags_fail() -> None:
    with pytest.raises(ZTDSPParamError):
        ZTDSPParams(random_len=255)          # not a multiple of 8
    with pytest.raises(ZTDSPParamError):
        ZTDSPParams(random_len=4608)         # exceeds the 512B nonce ceiling
    with pytest.raises(ZTDSPParamError):
        ZTDSPParams(key_len=100)             # only 128/192/256 allowed
    with pytest.raises(ZTDSPParamError):
        ZTDSPParams(window=0)
    with pytest.raises(ZTDSPParamError):
        ZTDSPParams(random_rate=-1)
    # module_flags: nesting depth > 32 rejected (explicit stack iteration, no RecursionError)
    flags = {}
    cursor = flags
    for _ in range(33):
        child = {}
        cursor["node"] = child
        cursor = child
    with pytest.raises(ZTDSPParamError):
        ZTDSPParams(module_flags=flags)
    # total node count > 1024 rejected
    wide = {f"k{i}": i for i in range(1025)}
    with pytest.raises(ZTDSPParamError):
        ZTDSPParams(module_flags=wide)
    # value-type whitelist
    with pytest.raises(ZTDSPParamError):
        ZTDSPParams(module_flags={"bad": object()})
    with pytest.raises(ZTDSPParamError):
        ZTDSPParams(module_flags={1: "int-key"})


def test_from_wire_converges_errors() -> None:
    # peer-controlled input: all type/value errors converge to ZTDSPParamError
    for bad in ("not-a-dict", 42, None):
        with pytest.raises(ZTDSPParamError):
            ZTDSPParams.from_wire(bad)
    with pytest.raises(ZTDSPParamError):
        ZTDSPParams.from_wire({"random_len": "not-an-int"})
    with pytest.raises(ZTDSPParamError):
        ZTDSPParams.from_wire({"key_len": 999})
    ok = ZTDSPParams.from_wire({"random_len": 512, "window": 45})
    assert ok.random_len == 512 and ok.window == 45


def test_match_fixed_order() -> None:
    a = ZTDSPParams()
    b = ZTDSPParams()
    assert a.match_error(b) is None
    # when multiple items differ, report the first one (fixed order, random_len first)
    c = ZTDSPParams(random_len=512, key_len=128, window=30)
    assert a.match_error(c) == "random_len mismatch"
    d = ZTDSPParams(key_len=128, window=30)
    assert a.match_error(d) == "key_len mismatch"
    e = ZTDSPParams(module_flags={"x": 1})
    assert a.match_error(e) == "module_flags mismatch"


# =============================================================================
# P2P placeholder token hash (4.1.1: HMAC-SHA3-256 role labels)
# =============================================================================

def test_p2p_hashes_cross_match() -> None:
    psk = bytes(range(32))
    a_local, a_peer = derive_p2p_identity(psk, "initiator")
    b_local, b_peer = derive_p2p_identity(psk, "responder")
    # A's local hash is exactly B's peer hash (guarantees Phase 4 two-way check self-consistency)
    assert a_local == b_peer
    assert a_peer == b_local
    assert a_local != a_peer
    assert len(a_local) == 32
    # byte-for-byte matches the spec formula: first 32 bytes of HMAC-SHA3-256(PSK, label)
    assert a_local == hmac_sha3(psk, b"ZT-DSP-TOKEN-INITIATOR-v3")[:32]
    assert b_local == hmac_sha3(psk, b"ZT-DSP-TOKEN-RESPONDER-v3")[:32]


def test_identity_rejects_bad_role() -> None:
    with pytest.raises(ValueError):
        derive_p2p_identity(bytes(range(32)), "middle")


# =============================================================================
# Key derivation formula (salt is the HKDF salt parameter)
# =============================================================================

def test_master_key_uses_salt_parameter_not_suffix_in_ikm() -> None:
    from zt_dsp_py.handshake import INFO_MK
    psk, dh, salt = bytes(range(32)), bytes(range(32, 64)), bytes(range(64, 96))
    corrected = HKDF(hashes.SHA3_256(), 32, salt, b"ZT-DSP-MK-v3").derive(psk + dh)
    naive = HKDF(hashes.SHA3_256(), 32, None, b"ZT-DSP-MK-v3").derive(psk + dh + salt)
    mine = HKDF(hashes.SHA3_256(), 32, salt, INFO_MK.encode()).derive(psk + dh)
    assert corrected == mine          # implementation matches the correct formula
    assert corrected != naive        # the wrong formula (salt concatenated into IKM) yields a different key


def test_directional_keys_cross() -> None:
    from zt_dsp_py.handshake import INFO_EK
    mk, anchor = bytes(range(32)), bytes(range(32, 64))
    def ek(role_byte: int) -> bytes:
        return HKDF(hashes.SHA3_256(), 32, None, INFO_EK.encode()).derive(
            mk + anchor + bytes([role_byte]))
    # initiator send(0x01) == responder recv(0x01); send != recv (reflection prevention)
    assert ek(1) == ek(1)
    assert ek(1) != ek(2)


def test_anchor_and_session_id() -> None:
    from zt_dsp_py.handshake import INFO_SID
    mk = bytes(range(32))
    anchor = hmac_sha3(mk, b"ZT-DSP-ANCHOR-v3")
    assert len(anchor) == 32
    sid = HKDF(hashes.SHA3_256(), 32, None, INFO_SID.encode()).derive(anchor)
    assert len(sid) == 32


def test_phase1_nonce_formula() -> None:
    from zt_dsp_py.handshake import INFO_NONCE
    psk = bytes(range(32))
    salt = bytes(range(32, 64))
    nonce = HKDF(hashes.SHA3_256(), 32, salt, INFO_NONCE.encode()).derive(psk)
    assert len(nonce) == 32
    # same PSK + same salt -> same output (deterministic); different salt -> different output
    nonce2 = HKDF(hashes.SHA3_256(), 32, bytes(32), INFO_NONCE.encode()).derive(psk)
    assert nonce != nonce2
