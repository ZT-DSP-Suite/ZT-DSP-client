//! Version contract (single source of truth).
//!
//! Word-for-word aligned with the Python reference implementation `zt_dsp_py/version.py`:
//!
//! - **docs version**: `1.0.0`, used only for the revision count of the Master Guide document itself; it does not participate in network communication;
//! - **code version**: `ZT-DSP_<language_prefix>-<major.minor.patch>`; this implementation is `ZT-DSP_RS-1.0.0`
//!   (language prefix RS = Rust); it does not participate in network communication;
//! - The handshake frame **carries no version string**: the phase-1 parameter JSON and the phase-4 AAD both contain neither a version nor
//!   a protocol identifier field. Whether the peer is compatible is reflected by the phase-3 confirmation tag verification.
//!
//! Hardware support (TPM and HWID): this implementation contains **no** code that writes, reads or modifies a Trusted Platform Module
//! or a Hardware Identifier. The PSK and the token are ordinary configuration values supplied by the caller; keeping them secret is the
//! caller's responsibility. Binding them to a TPM/HWID is a protocol-level goal **planned for a later version**. This statement is
//! re-issued with every release; the authoritative per-version matrix is Appendix D.1 of the Master Guide.
//!
//! The correspondence between the document and the code is maintained by a **bidirectional declaration**, not bound by version numbers:
//! The code side declares "which document this implementation follows" (see `FOLLOWS_DOC` / `FOLLOWS_DOC_PATH`).
//!
//! This module is the single source of truth; version strings must never be hardcoded anywhere else.

/// Code-side bidirectional declaration: which document this implementation follows.
pub const FOLLOWS_DOC: &str = "ZT-DSP Protocol Master Guide";

/// Code-side bidirectional declaration: the path of the followed document.
pub const FOLLOWS_DOC_PATH: &str = "ZT-DSP-docs/en/spec/ZT-DSP_1.0.0_Master_Guide.md";

/// docs version (document revision number, does not participate in network communication).
pub const DOCS_VERSION: &str = "1.0.0";

/// code version: language prefix (Rust = RS).
pub const LANGUAGE_PREFIX: &str = "RS";

/// code version.
pub const CODE_VERSION: &str = "1.0.0";

/// Implementation identifier `ZT-DSP_RS-1.0.0`.
pub const IMPLEMENTATION_ID: &str = concat!("ZT-DSP_", "RS", "-", "1.0.0");

/// Single-line output version string for the CLI `--version`.
///
/// The two segments, in order: the code-version implementation identifier, and the docs version.
pub fn format_version() -> String {
    format!("{} (docs {})", IMPLEMENTATION_ID, DOCS_VERSION)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn version_contract() {
        assert_eq!(IMPLEMENTATION_ID, "ZT-DSP_RS-1.0.0");
        assert_eq!(DOCS_VERSION, "1.0.0");
        assert_eq!(CODE_VERSION, "1.0.0");
        assert_eq!(LANGUAGE_PREFIX, "RS");
        assert_eq!(FOLLOWS_DOC, "ZT-DSP Protocol Master Guide");
        assert_eq!(FOLLOWS_DOC_PATH, "ZT-DSP-docs/en/spec/ZT-DSP_1.0.0_Master_Guide.md");
    }

    #[test]
    fn format_version_two_segments() {
        assert_eq!(format_version(), "ZT-DSP_RS-1.0.0 (docs 1.0.0)");
    }
}
