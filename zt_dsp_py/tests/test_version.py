# -*- coding: utf-8 -*-
"""Version contract tests (docs / code dual version numbers; see the "Naming Rules" section of the root README)."""
from zt_dsp_py.version import (
    CODE_VERSION,
    DOCS_VERSION,
    FOLLOWS_DOC,
    FOLLOWS_DOC_PATH,
    IMPLEMENTATION_ID,
    LANGUAGE_PREFIX,
    format_version,
)


def test_docs_version_declaration() -> None:
    # docs version: the document's own revision number; it does not take part in network communication
    assert DOCS_VERSION == "1.0.0"


def test_code_version_implementation_id() -> None:
    # code version: implementation and protocol behavior version, ZT-DSP_<language prefix>-<major.minor.revision>
    assert LANGUAGE_PREFIX == "PY"
    assert CODE_VERSION == "1.0.0"
    assert IMPLEMENTATION_ID == "ZT-DSP_PY-1.0.0"
    assert IMPLEMENTATION_ID.endswith(f"-{CODE_VERSION}")


def test_follows_doc_declaration() -> None:
    # Bidirectional declaration on the code side: which document this implementation follows (the doc-to-code correspondence is not bound by version numbers)
    assert FOLLOWS_DOC == "ZT-DSP Protocol Master Guide"
    assert FOLLOWS_DOC_PATH == "ZT-DSP-docs/en/spec/ZT-DSP_1.0.0_Master_Guide.md"


def test_no_protocol_identifier_constant() -> None:
    # Online frames carry no protocol identifier constant: this constant should not exist in the version module
    import zt_dsp_py.version as version_module

    assert not hasattr(version_module, "PROTOCOL_VERSION")
    assert not hasattr(version_module, "PROTOCOL_IDENTIFIER_BYTES")


def test_format_version_contract() -> None:
    # Two segments: the code-version implementation ID and the docs version
    assert format_version() == "ZT-DSP_PY-1.0.0 (docs 1.0.0)"
