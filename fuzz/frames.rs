//! ZT-DSP frame parser fuzz target (Rust / cargo-fuzz).
//
// The frame readers take a `&mut TcpStream`, because that is what they really consume
// on the wire. Fuzzing them therefore means feeding bytes through a socket pair rather
// than calling a re-implementation -- a re-implementation would drift from the real
// parser and quietly stop covering it.
//
// Invariant under test: **untrusted input must never cause a panic or an abort.**
// Every rejection must arrive as `Err`, never as a crash. A panic here is a remote
// denial-of-service in the handshake path.
//
// Corpus/repro:
//   cargo +nightly fuzz run frames -- fuzz/artifacts/frames/crash-<hash>

#![no_main]

use libfuzzer_sys::fuzz_target;
use std::io::Write;
use std::os::unix::net::UnixStream;
use std::time::{Duration, Instant};

use zt_dsp_rs::frames::{
    read_confirm, read_data_header, read_pub_key, read_phase_one,
};

// Bounded so a pathological input cannot stall the fuzzer; still far above any
// legitimate frame (the largest is a Phase 4 packet bounded by MAX_CIPHERTEXT).
const MAX_INPUT: usize = 64 * 1024;

fuzz_target!(|data: &[u8]| {
    let data = if data.len() > MAX_INPUT {
        &data[..MAX_INPUT]
    } else {
        data
    };

    // One fresh socket pair per input: the readers are stateful (they consume from the
    // stream and may force-close it), so they cannot be reused across iterations.
    let (mut writer, mut reader) = match UnixStream::pair() {
        Ok(p) => p,
        Err(_) => return,
    };
    let _ = writer.write_all(data);
    let _ = writer.shutdown(std::net::Shutdown::Write);

    // A deadline is mandatory: without one a half-packet input would block forever,
    // which is a fuzzing bug, not a finding.
    let deadline = Some(Instant::now() + Duration::from_millis(50));

    // Each entry point gets its own pair: a reader that consumed the stream (or
    // force-closed it) would starve the next one.
    if let Ok((mut w, mut r)) = UnixStream::pair() {
        let _ = w.write_all(data);
        let _ = w.shutdown(std::net::Shutdown::Write);
        // Whatever it returns, it must return -- a panic is the bug we are hunting.
        let _ = read_phase_one(&mut r, deadline);
    }

    if let Ok((mut w, mut r)) = UnixStream::pair() {
        let _ = w.write_all(data);
        let _ = w.shutdown(std::net::Shutdown::Write);
        let _ = read_pub_key(&mut r, deadline);
    }

    if let Ok((mut w, mut r)) = UnixStream::pair() {
        let _ = w.write_all(data);
        let _ = w.shutdown(std::net::Shutdown::Write);
        let _ = read_confirm(&mut r, deadline);
    }

    if let Ok((mut w, mut r)) = UnixStream::pair() {
        let _ = w.write_all(data);
        let _ = w.shutdown(std::net::Shutdown::Write);
        let _ = read_data_header(&mut r, deadline);
    }
});