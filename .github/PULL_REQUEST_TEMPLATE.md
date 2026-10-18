# Pull requests

This repository ships a security protocol. Reviewers should treat every diff as
security-relevant until shown otherwise.

## Before you open

- [ ] `python -m pytest zt_dsp_py/tests -q` is green
- [ ] `cd zt_dsp_rs && cargo test --release` is green
- [ ] `python zt_dsp_rs/interop_test.py --suite interop` passes, **if** you touched
      either implementation. This is the only check that exercises both languages
      against each other over a real connection.

## What reviewers will ask

**Did you change wire format, key derivation, or the handshake?** Then the Master Guide
must change too, in `ZT-DSP-docs`, in **both** `cn/` and `en/`. Code and spec are
separate repositories and neither pulls from the other — a protocol change that is not
in the spec is a change to an undocumented protocol.

**Did you touch either implementation?** Both are reference implementations. If you change one side,
confirm the other still agrees. The shared vectors in `test-vectors/vectors.json` are
what make that checkable: if a derivation changes, regenerate them and expect the diff.

**Did you change a constant?** HKDF labels (`INFO_*`), frame offsets, and length limits
are byte-for-byte protocol surface. They are pinned by the shared vectors and by the
label-guard test.

**Did you add a dependency?** Justify it in the PR description. This code links a
cryptographic protocol; dependency count is a security property.

## Reporting vulnerabilities

Do not open a public issue for a vulnerability. See `SECURITY.md`.