# ZT-DSP (Client Edition)

## 这里有什么

Python and Rust implementations, test vectors, and the licence set.

## 按什么找

Build with the DEV-GUIDE in ZT-DSP-docs; judge conformance with its CONFORMANCE-GUIDE.

**中文** ｜ [English](en/README.md)

> ZT-DSP — Zero Trust Dynamic Synchronization Protocol. This repository is the **client (reference) implementation**.

> ## Hardware support (TPM / HWID)
>
> **Neither implementation in this repository supports the TPM or the HWID.**
> `zt_dsp_py` and `zt_dsp_rs` contain no code that writes, reads or modifies a Trusted Platform Module
> or a Hardware Identifier. The PSK and the token are ordinary configuration values supplied by the
> caller (`--psk-file`, `--psk-env`, `--psk`); keeping them secret is the caller's responsibility.
> Binding keys to a TPM/HWID is a protocol-level design goal that is **planned for a later version**.
>
> This statement is re-issued with every release; the authoritative statement is the TPM/HWID
> support declaration in Master Guide section 4.1.4. For the current release it reads:
> write TPM — not supported; write HWID — not supported; read or modify TPM/HWID — not supported.

## Documentation

| 中文 | English |
|---|---|
| [cn/README.md](cn/README.md) | [en/README.md](en/README.md) |
| [cn/rust-implementation.md](cn/rust-implementation.md) | [en/rust-implementation.md](en/rust-implementation.md) |

Documentation follows a bilingual mirror layout: `cn/` and `en/` contain the same documents in Chinese and English respectively.

## Code

| Implementation directory | Language | Implementation ID |
|---|---|---|
| `zt_dsp_py/` | Python | `ZT-DSP_PY-1.0.0` |
| `zt_dsp_rs/` | Rust | `ZT-DSP_RS-1.0.0` |

The official development languages are **Python** and **Rust**; both implementations are
first-class and follow the same Protocol Master Guide (docs 1.0.0). Other languages can be
added following the implementation-identifier rule `ZT-DSP_<prefix>-<implementation version>`.

Source comments and docstrings are in English.

## Build and test

```bash
# Install -- the package metadata lives inside zt_dsp_py/, so point pip at that directory
python -m pip install -e ./zt_dsp_py

# Test suite: run from the repository root (the package is zt_dsp_py, not zt_dsp)
python -m pytest zt_dsp_py/tests -q

# Interactive wizard: run with no arguments on a terminal.
# With stdin/stdout redirected it prints usage and exits 0 instead of blocking.
python -m zt_dsp_py

# Direct command line
python -m zt_dsp_py --role listen  --port 37291 --psk-file ./psk.txt
python -m zt_dsp_py --role connect --host <peer ip> --port 37291 --psk-file ./psk.txt
```

Two known traps:

1. `pyproject.toml` sits inside `zt_dsp_py/`, so the install path is `./zt_dsp_py`, not the
   repository root; and the test suite imports `zt_dsp_py` only when run from the repository root
   (`pytest` started inside `zt_dsp_py/` fails with `No module named zt_dsp_py`).
2. Building the Rust crate from a non-ASCII working directory (for example a Chinese path on
   Windows) requires `CARGO_TARGET_DIR` to point at an ASCII path.

Rust official implementation (`zt_dsp_rs/`):

```bash
cd zt_dsp_rs
cargo test --release
cargo build --release
```

## Related repositories

| Repository | Role |
|---|---|
| `ZT-DSP-docs` | Protocol specification and terminology |
| `ZT-DSP-client` (this repository; local directory `ZT-DSP-client`) | Client edition (reference implementation) |
| `ZT-DSP-server` | Server edition (in design) |

## License

Licensed under **GNU AGPL-3.0-or-later**, or under a **commercial license** by separate arrangement. See [LICENSING.md](LICENSING.md) and [LICENSE](LICENSE).
