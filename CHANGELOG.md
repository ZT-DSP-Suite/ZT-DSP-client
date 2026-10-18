# Changelog

All notable changes to this repository are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Note on authority:** this file is a convenience record, not the source of truth. The
governing change history is `git log`. If the two ever disagree, `git log` wins.

## [Unreleased]

### Added

- **Shared known-answer test vectors** (`test-vectors/vectors.json`), consumed by *both*
  the Python and the Rust implementation. Before this, each implementation had its own
  private tests and the only cross-implementation evidence was a live loopback
  handshake. The vectors pin RFC 5869 (HKDF), RFC 7748 (X25519), the full ZT-DSP
  derivation chain (PSK‖DH → MK → anchor → session_id → directional EK → ratchet), the
  wire format, and a deterministic AEAD ciphertext.
- Fuzz targets for the frame parsers (`fuzz/`, atheris + cargo-fuzz), run weekly
  by `.github/workflows/fuzz.yml`. The frame readers consume attacker-controlled length
  prefixes; they now have continuous coverage instead of hand-written cases only.
- Library target for the Rust crate (`zt_dsp_rs`), so the protocol can be depended on
  and the fuzz target can link against it.
- `dependabot.yml` for pip, cargo and GitHub Actions.
- `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, and a pull request template.

### Changed

- CI now pins **every** action to a commit SHA. Two steps in the interop job were left
  on movable tags, which contradicted the stated policy on that file's own header.
- The interop CI job is renamed from `Interop (Python <-> Rust, byte-level)` to
  `Live handshake interop`. It verifies a real handshake in both directions; byte-level
  equality is verified by the shared vectors, not by this job.
- `interop_test.py` no longer synchronises with fixed `time.sleep()` calls. It waits for
  the actual readiness and handshake markers, and asserts per side rather than on the
  concatenated output.
- The Rust integration tests moved from the binary entry point into the library, so they
  can reach the modules directly.

### Fixed

- **20 source references pointed at appendix letters that no longer exist.** The docs repo
  commit `6e1d425` ("Prune stale appendices") removed appendices A / D / E, whose content
  had moved into the client README, but 20 docstrings and comments across `cli.py`,
  `crypto.py`, `cli.rs`, `crypto.rs`, `integration_tests.rs` and three test modules still
  cited "Appendix E" / E.2 / E.3 / E.4 / E.5 -- including `cli.py:148`, a string printed to
  the user. The existing docs-to-code checks compare constants and values, not
  cross-references, so nothing caught it. All 20 now point at the location that actually
  holds the material (client README, or Master Guide Appendix B for the PSK rules).
- Added `test_doc_refs.py`, which parses the appendix headings out of the spec and fails on
  any cited letter that is absent, so this class of defect cannot return silently. It skips
  when the docs repo is not checked out (this repo's own CI).
- `CryptoSuite.hkdf` accepted only `str` for `info`, so the Python implementation
  **could not express RFC 5869's binary-info test vectors** and could not validate its
  own HKDF against the RFC. It now accepts `str` or `bytes`, matching the Rust signature
  (`&[u8]`) and RFC 5869.

## [1.0.0]

- Initial protocol implementation, following ZT-DSP Protocol Master Guide 1.0.0.