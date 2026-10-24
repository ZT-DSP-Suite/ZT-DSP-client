// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (c) 2026 ZT-DSP Suite maintainers (copyright holder: SCAL-ROAM)

//! Version contract (single source of truth).
//!
//! Word-for-word aligned with the Python reference implementation `zt_dsp_py/version.py`:
//!
//! - **total-guide version (docs version)**: `1.0.2`, used only for the revision count of the Master Guide
//!   document itself; it does not participate in network communication;
//! - **client version**: `ZT-DSP_<prefix>-<major.minor.patch>`; this implementation is `ZT-DSP_RS-1.0.0`
//!   (language prefix RS = Rust);
//! - **server version**: the same shape, for example `ZT-DSP_SV-1.0.0` (repository `ZT-DSP-server`,
//!   currently a placeholder); `SV` is a role prefix rather than a language prefix;
//! - The relation between them is **many-to-many**: several implementations of the same kind whose protocol
//!   behaviour has not changed apply to the same total-guide version without any new declaration, and one
//!   total-guide version may apply to several client and server versions at once. Compatibility is never
//!   expressed by equality of version numbers;
//! - The handshake frame **carries no version string**: the phase-1 parameter JSON and the phase-4 AAD both contain neither a version nor
//!   a protocol identifier field. Whether the peer is compatible is reflected by the phase-3 confirmation tag verification.
//!
//! The correspondence between the document and the code is maintained by a **bidirectional declaration**, not bound by version numbers:
//! The code side declares "which documents this implementation applies to" (see `FOLLOWS_DOC` / `FOLLOWS_DOC_PATH` /
//! `APPLIES_TO_DOC_VERSIONS`).
//!
//! This module is the single source of truth; version strings must never be hardcoded anywhere else.

/// Code-side bidirectional declaration: which document this implementation follows.
// NOTE: this path points into the SIBLING repository ZT-DSP-docs.
// It does NOT resolve inside this repo -- this repo ships no copy of the protocol text.
// Once published, read it from the ZT-DSP-docs repository on GitHub.
pub const FOLLOWS_DOC: &str = "ZT-DSP Protocol Master Guide";

/// Code-side bidirectional declaration: the path of the followed document.
pub const FOLLOWS_DOC_PATH: &str = "ZT-DSP-docs/en/spec/ZT-DSP-1.0.2-Master_Guide.md";

/// Total-guide versions this implementation applies to (many-to-many: may hold several).
pub const APPLIES_TO_DOC_VERSIONS: &[&str] = &["1.0.0", "1.0.1", "1.0.2"];

/// docs version (document revision number, does not participate in network communication).
pub const DOCS_VERSION: &str = "1.0.2";

/// Role of this implementation: "client" or "server".
pub const ROLE: &str = "client";

/// language prefix (Rust = RS).
pub const LANGUAGE_PREFIX: &str = "RS";

/// implementation version: the numeric part of a client / server version.
pub const CODE_VERSION: &str = "1.0.0";

/// Build date segment: development builds carry `YYYYMMDD`; RC and release leave it empty.
/// Value is the commit date in UTC+8 (VERSIONING.md §3.1). Empty means "no date segment".
pub const BUILD_DATE: &str = "";

/// Compose `ZT-DSP_<prefix>-<version>[-<YYYYMMDD>]`.
///
/// An empty build date yields the release identifier. A non-empty one must be eight
/// digits, so a malformed date fails here rather than in a published identifier.
pub fn implementation_identifier(prefix: &str, code_version: &str, build_date: &str) -> String {
    if build_date.is_empty() {
        return format!("ZT-DSP_{}-{}", prefix, code_version);
    }
    assert!(
        build_date.len() == 8 && build_date.bytes().all(|b| b.is_ascii_digit()),
        "BUILD_DATE must be YYYYMMDD or empty"
    );
    format!("ZT-DSP_{}-{}-{}", prefix, code_version, build_date)
}

/// The identifier this build reports.
pub fn implementation_id() -> String {
    implementation_identifier(LANGUAGE_PREFIX, CODE_VERSION, BUILD_DATE)
}

/// Implementation identifier `ZT-DSP_RS-1.0.0` (release form).
///
/// Kept as a constant for callers that need the release form. While `BUILD_DATE` is empty
/// it equals `implementation_id()`; the unit tests hold the two together.
pub const IMPLEMENTATION_ID: &str = concat!("ZT-DSP_", "RS", "-", "1.0.0");

/// All client versions of this kind, applicable to the same total-guide versions.
pub const CLIENT_VERSIONS: &[&str] = &["ZT-DSP_PY-1.0.0", "ZT-DSP_RS-1.0.0"];

/// Server versions applicable to the same total-guide versions (placeholder, not implemented).
pub const SERVER_VERSIONS: &[&str] = &["ZT-DSP_SV-1.0.0"];

/// Single-line output version string for the CLI `--version`.
///
/// The two segments, in order: this implementation's client/server version identifier, and the total-guide version.
pub fn format_version() -> String {
    format!("{} (docs {})", implementation_id(), DOCS_VERSION)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn version_contract() {
        assert_eq!(IMPLEMENTATION_ID, "ZT-DSP_RS-1.0.0");
        assert_eq!(DOCS_VERSION, "1.0.2");
        assert_eq!(CODE_VERSION, "1.0.0");
        assert_eq!(LANGUAGE_PREFIX, "RS");
        assert_eq!(ROLE, "client");
        assert_eq!(FOLLOWS_DOC, "ZT-DSP Protocol Master Guide");
        assert_eq!(
            FOLLOWS_DOC_PATH,
            "ZT-DSP-docs/en/spec/ZT-DSP-1.0.2-Master_Guide.md"
        );
    }

    #[test]
    fn applicability_is_many_to_many() {
        assert_eq!(APPLIES_TO_DOC_VERSIONS, &["1.0.0", "1.0.1", "1.0.2"]);
        assert!(APPLIES_TO_DOC_VERSIONS.contains(&DOCS_VERSION));
        assert!(CLIENT_VERSIONS.contains(&IMPLEMENTATION_ID));
        assert!(!SERVER_VERSIONS.contains(&IMPLEMENTATION_ID));
        assert_eq!(SERVER_VERSIONS, &["ZT-DSP_SV-1.0.0"]);
    }

    #[test]
    fn format_version_two_segments() {
        assert_eq!(format_version(), "ZT-DSP_RS-1.0.0 (docs 1.0.2)");
    }

    #[test]
    fn build_date_is_empty_for_the_release_identifier() {
        assert_eq!(BUILD_DATE, "");
        assert_eq!(
            implementation_identifier("RS", "1.0.0", ""),
            "ZT-DSP_RS-1.0.0"
        );
        assert_eq!(implementation_id(), IMPLEMENTATION_ID);
    }

    #[test]
    fn build_date_appends_eight_digit_date() {
        assert_eq!(
            implementation_identifier("RS", "1.0.0", "20261023"),
            "ZT-DSP_RS-1.0.0-20261023"
        );
    }

    #[test]
    #[should_panic(expected = "BUILD_DATE must be YYYYMMDD or empty")]
    fn build_date_rejects_other_shapes() {
        implementation_identifier("RS", "1.0.0", "2026-10-23");
    }
}
