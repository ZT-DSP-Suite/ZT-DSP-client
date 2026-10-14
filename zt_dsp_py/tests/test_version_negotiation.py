"""Version negotiation and policy floor (1.1.0).

Before 1.1.0 the parameter JSON carried no version at all, so there was nothing to
negotiate and nothing to pin: a future algorithm swap would have had no wire-level
hook, and a stripped field would have gone unnoticed. 1.1.0 adds a mandatory "proto"
field that travels inside the Phase 1 frame and therefore into the handshake
transcript, plus a hard floor on the negotiated session-key length.

These tests pin the three properties that make that meaningful:
  1. the version is on the wire and lands in the transcript (so confirmation tags cover it);
  2. a peer that omits "proto" is refused, not guessed at;
  3. the key-length floor is enforced on peer-supplied values, not just local ones.
"""

import json

import pytest

from zt_dsp_py.errors import ZTDSPParamError
from zt_dsp_py.params import (
    MIN_KEY_BITS,
    PROTO_VERSION,
    SUPPORTED_PROTO_VERSIONS,
    ZTDSPParams,
)

# The exact bytes a 1.0.0 peer sends: no proto field, 120 bytes.
LEGACY_1_0_0_JSON = (
    b'{"aead":"AES-256-GCM","hash":"SHA3-256","key_len":256,'
    b'"module_flags":{},"random_len":256,"random_rate":1024,"window":60}'
)


def test_version_is_on_the_wire_and_is_mandatory() -> None:
    wire = ZTDSPParams().to_wire()
    assert wire["proto"] == PROTO_VERSION
    # it is genuinely part of the bytes that get hashed into the transcript
    assert b'"proto":"' in ZTDSPParams().to_json()


def test_pre_1_1_peer_is_refused_not_downgraded() -> None:
    legacy = json.loads(LEGACY_1_0_0_JSON)
    assert "proto" not in legacy, "fixture drifted: this must stay a 1.0.0 payload"
    with pytest.raises(ZTDSPParamError) as ei:
        ZTDSPParams.from_wire(legacy)
    assert "downgrade" in str(ei.value)


def test_unknown_version_is_refused() -> None:
    for bad in ("9.9.9", "1.0.0", ""):
        with pytest.raises(ZTDSPParamError) as ei:
            ZTDSPParams.from_wire({"proto": bad})
        assert "downgrade" in str(ei.value) or "unsupported protocol version" in str(ei.value)


def test_key_length_floor_applies_to_peer_values() -> None:
    for below in (8, 128, 192):
        with pytest.raises(ZTDSPParamError) as ei:
            ZTDSPParams.from_wire({"proto": PROTO_VERSION, "key_len": below})
        assert str(MIN_KEY_BITS) in str(ei.value)
    ok = ZTDSPParams.from_wire({"proto": PROTO_VERSION, "key_len": 512})
    assert ok.key_len == 512, "the floor is a minimum, not a single allowed size"


def test_version_mismatch_is_reported_first() -> None:
    a = ZTDSPParams()
    peer = ZTDSPParams()
    # simulate a peer speaking a different version by bypassing the constructor guard
    object.__setattr__(peer, "proto_version", "1.0.0")
    assert a.match_error(peer) == "proto_version mismatch"


def test_supported_version_list_has_no_fallback() -> None:
    # An unknown version must never resolve to a default: the list is exhaustive on purpose.
    assert tuple(SUPPORTED_PROTO_VERSIONS) == ("1.1.0",)
    assert PROTO_VERSION in SUPPORTED_PROTO_VERSIONS
