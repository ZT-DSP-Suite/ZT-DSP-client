# -*- coding: utf-8 -*-
"""Version contract (single source of truth).

This project has exactly two version numbers:

docs version
    The revision number of the documentation itself, written as `docs 1.0.0`.
    Used only for the revision counting of the master-guidance document; it takes no part in network communication.

code version
    The version of the implementation and protocol behavior, written as `code 1.0.0`.
    To identify a specific implementation, use the identifier `ZT-DSP_<language_prefix>-<major.minor.revision>`;
    this implementation is `ZT-DSP_PY-1.0.0`. Implementations in different languages may share the same version number, distinguished by the language prefix.

Hardware support (TPM and HWID)
    This implementation contains **no** code that writes, reads or modifies a Trusted Platform Module
    or a Hardware Identifier. The PSK and the token are ordinary configuration values supplied by the
    caller; keeping them secret is the caller's responsibility. Binding them to a TPM/HWID is a
    protocol-level goal **planned for a later version**. This statement is re-issued with every release;
    the authoritative per-version matrix is Appendix D.1 of the Master Guide.

The correspondence between documentation and code is maintained via a **bidirectional declaration**, not bound by version numbers:

    - Doc side: each document's header declares "which code settings this document governs"
    - Code side: declares "which document this implementation follows" -- see FOLLOWS_DOC / FOLLOWS_DOC_PATH below

Handshake frames **carry no protocol-identifier constants**: the Phase 1 parameter JSON and the Phase 4 AAD
contain no version string. Whether the peer is compatible is reflected by the Phase 3 confirmation-label check.

Hard-coding version strings anywhere is forbidden; this module is the single source of truth.
"""

# --- Code-side bidirectional declaration: which document this implementation follows ---
FOLLOWS_DOC: str = "ZT-DSP Protocol Master Guide"
FOLLOWS_DOC_PATH: str = "ZT-DSP-docs/en/spec/ZT-DSP_1.0.0_Master_Guide.md"

# --- docs version (documentation revision number; takes no part in network communication) ---
DOCS_VERSION: str = "1.0.0"

# --- code version (implementation and protocol-behavior version, two sides of one coin) ---
LANGUAGE_PREFIX: str = "PY"
CODE_VERSION: str = "1.0.0"
IMPLEMENTATION_ID: str = f"ZT-DSP_{LANGUAGE_PREFIX}-{CODE_VERSION}"


def format_version() -> str:
    """The single-line version string for the CLI --version output.

    In order: the code-version implementation identifier, then the docs version.
    """
    return f"{IMPLEMENTATION_ID} (docs {DOCS_VERSION})"
