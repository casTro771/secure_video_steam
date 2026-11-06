"""Student exercises for nonlinear stream-generator variants."""

from stream_cipher import LFSR_PERIOD_BITS, MAX_SEED, _next_bit

DEFAULT_GEFFE_SEEDS = (0xACE1, 0xBEEF, 0x1234)


def _validate(length: int, seeds: tuple[int, ...], offset: int) -> None:
    if not isinstance(length, int) or length < 0:
        raise ValueError("length must be a non-negative integer")
    if not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a non-negative integer")
    if any(not isinstance(seed, int) or not 1 <= seed <= MAX_SEED for seed in seeds):
        raise ValueError("every seed must be an integer from 1 to 65535")


def _nlfsr_step(state: int) -> tuple[int, int]:
    """One NLFSR step: base taps 0, 2, 3, 5 XOR (bit 1 AND bit 7)."""
    output = state & 1
    feedback = (
        state ^ (state >> 2) ^ (state >> 3) ^ (state >> 5)
        ^ ((state >> 1) & (state >> 7))
    ) & 1
    next_state = ((state >> 1) | (feedback << 15)) & MAX_SEED
    return output, next_state


def nlfsr_keystream(length: int, seed: int, offset: int = 0) -> bytes:
    """Generate bytes from an NLFSR with one nonlinear AND feedback term.

    Use the base feedback bits 0, 2, 3, and 5, then XOR them with
    (bit 1 AND bit 7). Output, shifting, offset, and packing match the LFSR.
    """
    _validate(length, (seed,), offset)
    state = seed
    # The NLFSR's cycle length depends on the seed (it is not always 65535),
    # so the offset is skipped bit by bit without a modulo shortcut.
    for _ in range(offset * 8):
        _, state = _nlfsr_step(state)

    out = bytearray(length)
    for i in range(length):
        byte = 0
        for _ in range(8):
            bit, state = _nlfsr_step(state)
            byte = (byte << 1) | bit  # first generated bit is the MSB
        out[i] = byte
    return bytes(out)


def geffe_keystream(
    length: int,
    seeds: tuple[int, int, int] = DEFAULT_GEFFE_SEEDS,
    offset: int = 0,
) -> bytes:
    """Combine three LFSR output bits with the nonlinear Geffe function.

    If the three output bits are x, y, and z, emit
    (x AND y) XOR ((1 XOR x) AND z). Each component uses the base LFSR.
    """
    if len(seeds) != 3:
        raise ValueError("the Geffe generator needs exactly three seeds")
    _validate(length, seeds, offset)
    s1, s2, s3 = seeds
    # All three components are the same maximal LFSR (period 65535 bits),
    # so skipping modulo the period lands each one on the correct state.
    for _ in range((offset * 8) % LFSR_PERIOD_BITS):
        _, s1 = _next_bit(s1)
        _, s2 = _next_bit(s2)
        _, s3 = _next_bit(s3)

    out = bytearray(length)
    for i in range(length):
        byte = 0
        for _ in range(8):
            x, s1 = _next_bit(s1)
            y, s2 = _next_bit(s2)
            z, s3 = _next_bit(s3)
            bit = (x & y) ^ ((1 ^ x) & z)
            byte = (byte << 1) | bit  # first generated bit is the MSB
        out[i] = byte
    return bytes(out)