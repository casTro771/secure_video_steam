(function exposeCipher(root) {
  "use strict";
  const LFSR_PERIOD_BITS = 0xffff;
 
  function nextBit(state) {
    // Output is the least significant bit; taps are bits 0, 2, 3, 5;
    // the register shifts right and the feedback bit enters bit 15.
    const output = state & 1;
    const feedback = (state ^ (state >>> 2) ^ (state >>> 3) ^ (state >>> 5)) & 1;
    const nextState = ((state >>> 1) | (feedback << 15)) & 0xffff;
    return [output, nextState];
  }
 
  function keystream(length, seed, offset = 0) {
    if (!Number.isInteger(seed) || seed < 1 || seed > 0xffff) throw new RangeError("invalid seed");
    if (!Number.isInteger(length) || length < 0 || !Number.isInteger(offset) || offset < 0) {
      throw new RangeError("invalid length or offset");
    }
    let state = seed;
    // Same rule as Python: skip offset * 8 bits, reduced modulo the period.
    const skip = (offset * 8) % LFSR_PERIOD_BITS;
    for (let i = 0; i < skip; i++) state = nextBit(state)[1];
 
    const out = new Uint8Array(length);
    for (let i = 0; i < length; i++) {
      let byte = 0;
      for (let j = 0; j < 8; j++) {
        const [bit, next] = nextBit(state);
        state = next;
        byte = (byte << 1) | bit; // first generated bit is the MSB
      }
      out[i] = byte;
    }
    return out;
  }
 
  function xorBytes(data, seed, offset = 0) {
    const bytes = data instanceof Uint8Array ? data : new Uint8Array(data);
    const stream = keystream(bytes.length, seed, offset);
    const out = new Uint8Array(bytes.length);
    for (let i = 0; i < bytes.length; i++) out[i] = bytes[i] ^ stream[i];
    return out;
  }
 
  const cipher = { keystream, xorBytes };
  root.LfsrCipher = cipher;
  if (typeof module !== "undefined") module.exports = cipher;
}(typeof self !== "undefined" ? self : globalThis));
