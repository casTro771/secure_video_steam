"""Small, deliberately insecure LFSR stream cipher for teaching."""

MAX_SEED = 0xFFFF
LFSR_PERIOD_BITS = 0xFFFF


def _validate_seed(seed: int) -> None:
    if not isinstance(seed, int) or not 1 <= seed <= MAX_SEED:
        raise ValueError("seed must be an integer from 1 to 65535")


def _next_bit(state: int) -> tuple[int, int]:
    """Return output bit and next state for x^16 + x^14 + x^13 + x^11 + 1."""
    # Output is the least significant bit; taps are bits 0, 2, 3, 5;
    # the register shifts right and the feedback bit enters bit 15.
    output = state & 1
    feedback = (state ^ (state >> 2) ^ (state >> 3) ^ (state >> 5)) & 1
    next_state = ((state >> 1) | (feedback << 15)) & MAX_SEED
    return output, next_state


def keystream(length: int, seed: int, offset: int = 0) -> bytes:
    """Return length keystream bytes, starting at an absolute byte offset."""
    _validate_seed(seed)
    if not isinstance(length, int) or length < 0:
        raise ValueError("length must be a non-negative integer")
    if not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a non-negative integer")

    state = seed
    # The sequence repeats every 65535 bits, so skipping modulo the period
    # gives the same state and keeps seeking fast for large offsets.
    for _ in range((offset * 8) % LFSR_PERIOD_BITS):
        _, state = _next_bit(state)

    out = bytearray(length)
    for i in range(length):
        byte = 0
        for _ in range(8):
            bit, state = _next_bit(state)
            byte = (byte << 1) | bit  # first generated bit is the MSB
        out[i] = byte
    return bytes(out)


def xor_bytes(data: bytes, seed: int, offset: int = 0) -> bytes:
    """Encrypt or decrypt data with the keystream at absolute byte offset."""
    stream = keystream(len(data), seed, offset)
    return bytes(d ^ k for d, k in zip(data, stream))