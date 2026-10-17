# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 ZT-DSP Suite maintainers (copyright holder: SCAL-ROAM)

"""Version contract (single source of truth).

This project does not use a single abstract "code version". It has **three kinds of
versioned carrier**, and the relation between them is many-to-many:

total-guide version (docs version)
    The revision number of the Master Guide itself, written as `docs 1.0.0`.
    Used only for the revision counting of the document; it takes no part in network communication.

client version
    A client-side implementation, identified as `ZT-DSP_<prefix>-<major.minor.revision>`,
    for example `ZT-DSP_PY-1.0.0` (Python) or `ZT-DSP_RS-1.0.0` (Rust).

server version
    A server-side implementation, identified the same way, for example `ZT-DSP_SV-1.0.0`
    (repository `ZT-DSP-server`, currently a placeholder with no implementation yet).

Applicability (many-to-many)
    Several client/server versions may apply to the **same** total-guide version: a family of
    implementations of the same kind whose protocol behaviour has not changed needs no new
    declaration. Conversely, **one** total-guide version may apply to several client and
    server versions at once. Compatibility is therefore never expressed by equality of version
    numbers, only by the declarations below.

Hardware support (TPM and HWID)
    This implementation contains **no** code that writes, reads or modifies a Trusted Platform Module
    or a Hardware Identifier. The PSK and the token are ordinary configuration values supplied by the
    caller; keeping them secret is the caller's responsibility. Binding them to a TPM/HWID was an earlier design goal; it is now **deprecated and will be removed in a
    later revision**. This statement is re-issued with every release;
    the authoritative statement is the TPM/HWID support declaration in Master Guide section 4.1.4.

The correspondence between documentation and code is maintained via a **bidirectional declaration**, not bound by version numbers:

    - Doc side: each document's header declares "which implementations this document applies to"
    - Code side: declares "which documents this implementation applies to" -- see the
      FOLLOWS_DOC / FOLLOWS_DOC_PATH / APPLIES_TO_DOC_VERSIONS constants below

Handshake frames **carry no protocol-identifier constants**: the Phase 1 parameter JSON and the Phase 4 AAD
contain no version string. Whether the peer is compatible is reflected by the Phase 3 confirmation-label check.

Hard-coding version strings anywhere is forbidden; this module is the single source of truth.
"""

# --- Code-side bidirectional declaration: which document this implementation applies to ---
# NOTE: this path points into the SIBLING repository ZT-DSP-docs.
# It does NOT resolve inside this repo -- this repo ships no copy of the protocol text.
# Once published, read it from the ZT-DSP-docs repository on GitHub.
FOLLOWS_DOC: str = "ZT-DSP Protocol Master Guide"
FOLLOWS_DOC_PATH: str = "ZT-DSP-docs/en/spec/ZT-DSP-1.0.0-Master_Guide.md"

# --- Total-guide versions this implementation applies to (many-to-many: may hold several) ---
APPLIES_TO_DOC_VERSIONS: tuple[str, ...] = ("1.0.0", "1.0.1")

# --- total-guide version (document revision number; takes no part in network communication) ---
DOCS_VERSION: str = "1.0.1"

# --- Role of this implementation: "client" or "server" ---
ROLE: str = "client"

# --- language prefix; `SV` is a role prefix (server) rather than a language one ---
LANGUAGE_PREFIX: str = "PY"

# --- implementation version: the numeric part of a client / server version ---
CODE_VERSION: str = "1.0.0"

IMPLEMENTATION_ID: str = f"ZT-DSP_{LANGUAGE_PREFIX}-{CODE_VERSION}"

# --- All client versions of this kind, applicable to the same total-guide versions ---
CLIENT_VERSIONS: tuple[str, ...] = ("ZT-DSP_PY-1.0.0", "ZT-DSP_RS-1.0.0")

# --- Server versions applicable to the same total-guide versions (placeholder, not implemented) ---
SERVER_VERSIONS: tuple[str, ...] = ("ZT-DSP_SV-1.0.0",)


def format_version() -> str:
    """The single-line version string for the CLI --version output.

    In order: this implementation's client/server version identifier, then the total-guide version.
    """
    return f"{IMPLEMENTATION_ID} (docs {DOCS_VERSION})"
