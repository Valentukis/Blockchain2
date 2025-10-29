import struct

# --- rotate left for 64-bit integers ---
def rotl64(x: int, r: int) -> int:
    return ((x << r) | (x >> (64 - r))) & 0xFFFFFFFFFFFFFFFF


# --- constants (same as in C++) ---
ROUND_CONSTS = [
    0x243F6A8885A308D3, 0x13198A2E03707344,
    0xA4093822299F31D0, 0x082EFA98EC4E6C89,
    0x452821E638D01377, 0xBE5466CF34E90C6C,
    0xC0AC29B7C97C50DD, 0x3F84D5B5B5470917,
    0x9216D5D98979FB1B, 0xD1310BA698DFB5AC,
    0x2FFD72DBD01ADFB7, 0xB8E1AFED6A267E96
]


# --- permutation / mixing ---
def permute_state(state, block_words):
    for r in range(12):
        for i in range(4):
            state[i] ^= ROUND_CONSTS[r]

        a, b, c, d = state

        a = rotl64((a + (block_words[(r + 0) % 8] ^ b)) & 0xFFFFFFFFFFFFFFFF, (7 + r) % 64)
        b = rotl64((b ^ (c + block_words[(r + 1) % 8])) & 0xFFFFFFFFFFFFFFFF, (13 + r) % 64)
        c = rotl64((c + (d ^ block_words[(r + 2) % 8])) & 0xFFFFFFFFFFFFFFFF, (17 + r) % 64)
        d = rotl64((d ^ (a + block_words[(r + 3) % 8])) & 0xFFFFFFFFFFFFFFFF, (23 + r) % 64)

        state[0] = (a + b) & 0xFFFFFFFFFFFFFFFF
        state[1] = b ^ c
        state[2] = (c + d) & 0xFFFFFFFFFFFFFFFF
        state[3] = d ^ a

        state[0] ^= rotl64(state[1], 11)
        state[2] ^= rotl64(state[3], 19)


# --- padding function ---
def pad_message(msg_bytes: bytes) -> bytes:
    bit_len_low = len(msg_bytes) * 8
    bit_len_high = 0

    out = bytearray(msg_bytes)
    out.append(0x80)
    while (len(out) + 16) % 64 != 0:
        out.append(0x00)

    out += bit_len_high.to_bytes(8, 'big')
    out += bit_len_low.to_bytes(8, 'big')
    return bytes(out)


# --- block to words ---
def block_to_words(block: bytes) -> list[int]:
    words = [0] * 8
    for i in range(min(len(block), 64)):
        word_idx = i // 8
        words[word_idx] = ((words[word_idx] << 8) | block[i]) & 0xFFFFFFFFFFFFFFFF

    last_word_bytes = len(block) % 8
    if last_word_bytes != 0:
        idx = (len(block) - 1) // 8
        words[idx] = (words[idx] << (8 * (8 - last_word_bytes))) & 0xFFFFFFFFFFFFFFFF
    return words


# --- to hex string (256-bit) ---
def to_hex256(state):
    return ''.join(f"{x:016x}" for x in state)


# --- main custom hash function ---
def custom_hash256(data: str) -> str:
    state = [
        0x6A09E667F3BCC908,
        0xBB67AE8584CAA73B,
        0x3C6EF372FE94F82B,
        0xA54FF53A5F1D36F1,
    ]

    msg_bytes = data.encode('utf-8')
    padded = pad_message(msg_bytes)

    for pos in range(0, len(padded), 64):
        block = padded[pos:pos + 64]
        words = block_to_words(block)

        # XOR block into state
        for i in range(4):
            state[i] ^= words[i % 8]

        permute_state(state, words)

    # finalization: diffusion rounds
    zero_block = [0] * 8
    for i in range(4):
        state[i] ^= 0x0123456789ABCDEF ^ state[(i + 1) % 4]
    permute_state(state, zero_block)
    permute_state(state, zero_block)

    return to_hex256(state)
