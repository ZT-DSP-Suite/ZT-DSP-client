# ZT-DSP_RS-1.0.0

**Zero Trust Dynamic Synchronization Protocol** — Rust official implementation (client version **1.0.0**, implementation identifier `ZT-DSP_RS-1.0.0`) | Compliant with the *ZT-DSP Protocol Master Guidance* (**docs 1.0.0**)

A **complete Rust reference implementation** of Volume 4 (core protocol minimal set) and Appendices F/G/H (byte-by-byte specification / traffic analysis defense / state machine and timeout matrix) of the *ZT-DSP Protocol Master Guidance Library (1.0.0)*, which is **byte-for-byte interoperable on the wire** with the official Python implementation `ZT-DSP_PY-1.0.0` (interoperability verification below). It also has built-in benchmarks (handshake / throughput / cryptographic primitives) and can serve as a performance baseline for cross-language implementations.

## Relationship to the Python Official Implementation

- On-wire behavior takes `zt_dsp_py` (ZT-DSP_PY-1.0.0) as the byte-for-byte standard: the four frame layouts, the parameter JSON (default 120B), the derivation formulas (MK/EK/SID/nonce aligned parameter by parameter), transcript construction, AAD/nonce construction, the measured 165B heartbeat size, etc. — all match;
- Defence rules are **built in** as design and regression tests (see the "Hardening Comparison" section below);
- Implementations in different languages may share the same implementation version number and are distinguished by prefix; the relation to the total-guide version is many-to-many (see the naming conventions in the repository root README).

## Directory Layout

```
├── Cargo.toml / Cargo.lock   project manifests (version 1.0.0; single bin target)
├── README.md
├── zt-dsp-rs.rs              single entry: flat pull-in via #[path] + fn main + inline integration tests
├── version.rs                single source of truth for the version contract (total-guide version / client version / applicability / followed document)
├── errors.rs                 protocol-layer error system (typed convergence of Appendix H.5 in Rust)
├── params.rs                 parameter sets and validation (F.1: seven fixed-order matches; module_flags caps)
├── identity.rs               P2P placeholder token hash (4.1.1: HMAC-SHA3-256 role labels)
├── crypto.rs                 HKDF(RFC 5869) / HMAC / AES-GCM / constant-time comparison / entropy check
├── kex.rs                    X25519 ephemeral key exchange (F.3: silent on low-order points, private key zeroized on Drop)
├── frames.rs                 codecs for the four wire frame types + whole-frame shared deadline reads (F / H.3 Slowloris)
├── handshake.rs              four-phase handshake state machine (F.2 strict silent drop; H.1/H.2 dual state machines)
├── session.rs                encrypted session: ratchet / replay / padding / time window / heartbeat (F.5 eight-step pipeline; Appendix G)
├── transport.rs              listen/connect runners + three-thread chat session (H.6 idempotent cleanup) + connection rate limiting
├── cli.rs                    minimal CLI (--role/--psk-*/bench/pskgen)
├── bench.rs                  benchmarks (handshake/throughput/primitives)
└── interop_test.py           single-file cross-language interop verification (PY↔RS interop + RC1.3 generation measured)
```

> **Layout note**: all source files are **laid flat at the project root** (no `src/`, `tests/`, `interop/`
> subdirectories); modules are pulled in via `#[path]` from the root entry `zt-dsp-rs.rs`, with integration tests inlined there.
> This project is one of the **official implementations**, a sibling of `zt_dsp_py/` (the Python official implementation), so this layout may be kept long-term;
> if another language is to become an official implementation, add a sibling directory at the repository root named after its implementation ID.

## Build

Dependencies: Rust 1.75+ (the `rustup` default stable is fine), no other system dependencies.

```bash
cargo build --release
```

> **Windows GNU toolchain note**: when the project is on a path containing non-ASCII characters (`zt_dsp_rs/`),
> dlltool of `x86_64-pc-windows-gnu` cannot handle the Chinese path, causing `windows-sys` to fail to compile.
> Workaround (either one):
>
> ```bash
> # Option 1: point the target directory at an ASCII path (recommended)
> export CARGO_TARGET_DIR="C:/zt-dsp-rs-target"
> cargo build --release
>
> # Option 2: switch to the MSVC toolchain
> rustup default stable-x86_64-pc-windows-msvc
> ```

## Quick Start

```bash
# Generate a PSK (64 hex digits)
zt-dsp-rs pskgen > psk.txt

# Listener (responder side)
zt-dsp-rs --role listen --port 37291 --psk-file psk.txt

# Connector (initiator side)
zt-dsp-rs --role connect --host 127.0.0.1 --port 37291 --psk-file psk.txt

# Environment variable approach (recommended for scripts)
export ZT_DSP_PSK=$(zt-dsp-rs pskgen)
zt-dsp-rs --role listen --port 37291 --psk-env
```

Type a message and press Enter to send; exit with `/quit`, `/exit`, `/q` or Ctrl+C.

### Main Parameters

| Parameter | Default | Description |
|------|--------|------|
| `--port` | `37291` | port number |
| `--random-len` | `256` | join random number length (bits, multiple of 8) |
| `--random-rate` | `1024` | random number generation rate (per second) |
| `--window` | `60` | negotiation window (seconds, both sides must match) |
| `--time-window` | `30` | timestamp window (seconds, configurable per peer) |
| `--padding-min/max` | off | random padding range (0~2048B, may be enabled one-sided) |
| `--jitter` | `0` | send timing jitter (seconds) |
| `--retry-count / --retry-interval` | `3` / `5.0` | connection retries (initiator only) |
| `--silent-hold` | `15` | strict silent hold duration (seconds) |
| `--rate-limit` | `0` (off) | listener-side connection rate limiting (per second, rule P0-6) |

PSK injection precedence: `--psk-file` (recommended) > `--psk-env` > `--psk` (insecure).
Public default values and low-entropy keys are rejected (entropy < 3.5 bits/byte).

## Version Notes

| Item | Value |
|----|----|
| Implementation identifier | `ZT-DSP_RS-1.0.0` (language prefix RS, see the naming convention system in the repository root README) |
| docs version | `1.0.0` (revision of the master guidance followed by this implementation) |
| Followed document | *ZT-DSP Protocol Master Guidance*, path `ZT-DSP-docs/en/spec/ZT-DSP-1.0.0-Master_Guide.md` |

`--version` output (same format as the Python implementation): `ZT-DSP_RS-1.0.0 (docs 1.0.0)`

## Tests

```bash
cargo test
```

Coverage: version contract, parameter JSON byte-for-byte (120B), RFC 5869 official vectors, derivation formulas,
pre-validation of frame caps, Slowloris whole-frame overall deadline, two-sided handshake, PSK mismatch (safe error on both sides),
strict silent drop on parameter mismatch (zero-byte assertion), silent handling of low-order points (compute DH before replying), replay/tamper rejection,
out-of-window ratchet forward roll, one-sided padding interop, 165B heartbeat size, real TCP bidirectional flow,
Regression over five categories of typical vulnerabilities (PoC fails to penetrate).

## Interoperability Verification with ZT-DSP_PY

```bash
# Build release first (note the Windows GNU path tip above)
python interop_test.py --rust-bin <path to the zt-dsp-rs executable>   # PY↔RS interop + RC1.3 generation, --suite optional
```

Both directions verified (Python listen ↔ Rust connect, Rust listen ↔ Python connect):
four-phase handshake completed + bidirectional message interop (including Chinese) + graceful exit.
**Verified passing (2026-09-05, Python 3.14 / Rust 1.98 / Windows)**.

## Benchmarks (release build, loopback TCP, default parameters, measured on Windows / Rust 1.98)

| Item | Result |
|------|------|
| Full four-phase handshake | mean 2.19 ms (P50 2.05 ms / P95 3.17 ms), about 457 per second |
| Session throughput (16KiB/packet, including ratchet rotation per packet) | 78.6 MiB/s (about 5030 packets/second) |
| X25519 key generation + shared secret | 7495 per second |
| HKDF-SHA3-256 (32B output) | 233,000 per second |
| HMAC-SHA3-256 | 499,000 per second |
| AES-256-GCM (1KiB) | encryption 386 MB/s / decryption 447 MB/s |
| SHA3-256 | 284 MB/s |

Reproduce: `zt-dsp-rs bench [--handshakes N] [--throughput-mib M] [--primitive-iters K]`

## Hardening Comparison (behavioral differences relative to the Python reference implementation)

> The left column gives the defence-rule ID (`P0-x` / `P1-x`).

| ID | Issue | How this implementation handles it |
|------|------|--------------|
| P0-3 | Silent drain can be permanently held by "dripping bytes" + dangling FD | drain loop bounded by an **overall deadline**; force-closed after the hold is exhausted |
| P0-4 | Shared mutable timeout race on send/receive | send and receive paths each hold an independent lock and budget; state is guarded only by the `state` lock |
| P0-6 | No connection rate limiting | `--rate-limit` token bucket (off by default, behavior consistent with the official implementation) |
| P0-8 | PSK input path taint | values of `--psk-env`/`--psk` are **never** opened as paths (covered by regression tests) |
| P1-1 | No TCP_NODELAY | `set_nodelay(true)` enabled on all connections |
| P1-3 | PSK file BOM | UTF-8 BOM stripped on read |
| P1-4 | False positives in Windows permission checks | POSIX permission warnings only run on Unix |
| P1-5 | SO_REUSEADDR port preemption | not set on Windows (exclusive by default); TIME_WAIT reuse enabled on Unix only |
| P1-7 | Un-erasable key snapshots | all key material is `zeroize`d (including the EK snapshot on the send path and HKDF intermediates) |
| General | Typed error convergence | `errors::Error` enum (one-to-one with the H.5 exception tree), zero panics on peer input |

All other protocol behavior (five elements of strict silent drop, consume state before sending, constant-time comparison, forward ratchet roll within the window,
idempotent cleanup) is semantically consistent with the Python reference implementation, each pinned down by tests.

## License

MIT OR Apache-2.0 dual license — see [LICENSE-MIT](../LICENSE-MIT) and [LICENSE-APACHE](../LICENSE-APACHE) at the repository root.
