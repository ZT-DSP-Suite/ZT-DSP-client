# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 ZT-DSP Suite maintainers (copyright holder: SCAL-ROAM)
"""Cross-implementation interop, wired into pytest.

Before this file existed, interop_test.py ran nowhere: pytest did not
collect it and cargo had no test target for it. A green unit suite then
said nothing about whether the two implementations agree.
"""

import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
RS_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "zt_dsp_rs"))
INTEROP = os.path.join(RS_DIR, "interop_test.py")


def _binary():
    for name in ("zt-dsp-rs", "zt-dsp-rs.exe"):
        for profile in ("release", "debug"):
            p = os.path.join(RS_DIR, "target", profile, name)
            if os.path.exists(p):
                return p
    return None


@pytest.mark.skipif(not os.path.exists(INTEROP), reason="interop_test.py not present")
def test_cross_implementation_interop():
    if _binary() is None:
        pytest.skip("Rust binary not built; run cargo build --release in zt_dsp_rs")
    r = subprocess.run(
        [sys.executable, "interop_test.py"],
        cwd=RS_DIR,
        capture_output=True,
        text=True,
        timeout=180,
    )
    out = (r.stdout or "") + (r.stderr or "")
    assert r.returncode == 0, out[-1500:]
    assert "interop suite passed" in out.lower(), out[-800:]
