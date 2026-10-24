# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 ZT-DSP Suite contributors

"""Version contract for the ZT-DSP server role.

The shape is the same as zt_dsp_py.version: the same three bidirectional
declaration constants, the same DOCUMENT_REVISION notion.  The only
difference is the identity of the role: a client names itself with a
language prefix (PY / RS), a server names itself with a role prefix (SV),
because one language may host several server roles.

The handshake frame carries no version string at all - neither the Phase 1
parameter JSON nor the Phase 4 AAD contains a version or protocol field.
"""

from __future__ import annotations

#: The document this implementation follows.
DOCS_NAME = "ZT-DSP Protocol Master Guide"

#: Path of the followed document, relative to the sibling documentation repo.
#: NOTE: that path resolves in ZT-DSP-docs, not in this repository.
DOCS_PATH = "ZT-DSP-docs/en/spec/ZT-DSP-1.0.2-Master_Guide.md"

#: The document revisions this implementation applies to (many-to-many).
DOCS_VERSIONS = ["1.0.0", "1.0.1", "1.0.2"]

#: Role implemented by this package.
ROLE = "server"

#: Role prefix.  Clients use a language prefix; servers use a role prefix.
LANGUAGE_PREFIX = "SV"

#: Implementation version.
CODE_VERSION = "1.0.0"

#: Build date segment: development builds carry `-YYYYMMDD`; RC and release leave it empty.
#: Value is the commit date in UTC+8. Release candidates and releases leave it empty,
#: so the published identifier keeps its numeric form.
BUILD_DATE = "20261025"


def implementation_identifier(
    prefix: str, code_version: str, build_date: str = ""
) -> str:
    """Compose `ZT-DSP_<prefix>-<version>[-<YYYYMMDD>]`.

    An empty build date yields the release identifier. A non-empty one must be eight
    digits. A malformed date raises ValueError here rather than producing a published
    identifier.
    """
    if not build_date:
        return f"ZT-DSP_{prefix}-{code_version}"
    if len(build_date) != 8 or not build_date.isdigit():
        raise ValueError("BUILD_DATE must be YYYYMMDD or empty")
    return f"ZT-DSP_{prefix}-{code_version}-{build_date}"


#: Document revision this implementation was written against.
DOCUMENT_REVISION = "1.0.2"

#: Client implementations this server is interoperable with.
CLIENT_VERSIONS = ["ZT-DSP_PY-1.0.0", "ZT-DSP_RS-1.0.0"]

#: Server implementations sharing the same document revision.
SERVER_VERSIONS = ["ZT-DSP_SV-1.0.0"]

#: The identifier of this implementation, e.g. ZT-DSP_SV-1.0.0-20261025 for a development build.
IMPLEMENTATION_ID = implementation_identifier(LANGUAGE_PREFIX, CODE_VERSION, BUILD_DATE)

#: Name of the executable / entry point.
PROGRAM_NAME = "zt-dsp-server"


def format_version() -> str:
    """Single-line version string used by --version and the startup banner."""
    return f"{IMPLEMENTATION_ID} (docs {DOCUMENT_REVISION})"


def asserts() -> None:
    """Self-check of the version contract.

    Raises AssertionError if the constants contradict each other.  Called at
    import time so that a broken contract fails loudly rather than producing
    an implementation that claims to speak a document version it does not.
    """
    assert DOCS_VERSIONS, "DOCS_VERSIONS must not be empty"
    assert DOCUMENT_REVISION in DOCS_VERSIONS, (
        f"DOCUMENT_REVISION {DOCUMENT_REVISION!r} is not in DOCS_VERSIONS {DOCS_VERSIONS!r}"
    )
    assert ROLE == "server", ROLE
    assert LANGUAGE_PREFIX == "SV", LANGUAGE_PREFIX
    assert implementation_identifier("SV", CODE_VERSION, "") == "ZT-DSP_SV-1.0.0", (
        IMPLEMENTATION_ID
    )
    assert IMPLEMENTATION_ID == f"ZT-DSP_SV-1.0.0-{BUILD_DATE}", IMPLEMENTATION_ID
    assert DOCS_PATH.startswith("ZT-DSP-docs/"), DOCS_PATH


asserts()
