//! ZT-DSP_RS-1.0.0 — library entry point.
//!
//! The crate root is also the binary entry point (`zt-dsp-rs.rs`), which is the
//! project's documented flat layout: every module file lives in this directory and is
//! pulled in with `#[path]`. That convention is preserved here — this file exists so
//! the crate can **also** be consumed as a library.
//!
//! Why that matters: before this target existed, `zt-dsp-rs` could only ever be run as
//! a binary. A third party could not depend on the protocol implementation, and
//! integration tests could not `use` it (a `tests/` directory cannot see a bin-only
//! crate). The fuzz target in `fuzz_targets/frames.rs` depends on this target for the
//! same reason.
//!
//! Module layout is unchanged and stays flat; only the target type is added.

#[path = "version.rs"]
pub mod version;
#[path = "errors.rs"]
pub mod errors;
#[path = "params.rs"]
pub mod params;
#[path = "identity.rs"]
pub mod identity;
#[path = "crypto.rs"]
pub mod crypto;
#[path = "kex.rs"]
pub mod kex;
#[path = "frames.rs"]
pub mod frames;
#[path = "handshake.rs"]
pub mod handshake;
#[path = "session.rs"]
pub mod session;
#[path = "transport.rs"]
pub mod transport;
#[path = "cli.rs"]
pub mod cli;
#[path = "bench.rs"]
pub mod bench;

// Shared known-answer vectors. Test-only: this module reads test-vectors/vectors.json,
// which is a repository asset, not a runtime dependency. Gating it keeps the release
// binary free of JSON parsing and serde_json in the frame path.
#[cfg(test)]
#[path = "vectors.rs"]
mod vectors;

// Integration tests: real TCP bidirectional flow, CLI contract, defensive-rule
// regression (historic PoC scenarios must be "unbreakable"). They live with the
// library rather than the binary so they can reach the modules directly.
// The end-to-end binary smoke test is covered by interop_test.py.
#[cfg(test)]
#[path = "integration_tests.rs"]
mod integration_tests;
