# kap_core.abi3.so — Binary Integrity Record

## File
`kap_escrow/kap_core.abi3.so`

## Purpose
Rust-compiled extension implementing the low-level KAP escrow engine primitives
(WAL, atomic ledger operations). Built with `maturin` from the Rust source in `src/`.

## SHA-256 Checksum (v2.0.0-beta)
```
101b2890ba6b8038c89811504e83db84f5fe65a6c669c9b5f157c2d24e323486  kap_core.abi3.so
```

## How to verify
```bash
sha256sum kap_escrow/kap_core.abi3.so
```

## How to rebuild from source
```bash
# Requires: Rust toolchain + maturin
pip install maturin
maturin build --release --strip
cp target/wheels/*.whl dist/
# Then extract .so from the wheel and replace kap_core.abi3.so
```

## Supply Chain Notes
- This binary is ONLY used for performance-critical atomic operations.
- All security logic (signing, verification, policy) is in pure Python.
- In a production deployment, rebuild from source in CI rather than using
  the pre-compiled binary from this repository.
- See `src/engine.rs` and `src/wal.rs` for the full Rust source.
