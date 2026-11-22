#!/usr/bin/env python3
"""Minimal BPS patch creator/applier (SourceRead + TargetRead + SourceCopy for moved data is not used).
usage: mkbps.py make src tgt out.bps [metadata] | mkbps.py apply src patch out"""
import sys, zlib

def enc(n):
    out = bytearray()
    while True:
        x = n & 0x7f; n >>= 7
        if n == 0: out.append(0x80 | x); return out
        out.append(x); n -= 1

def dec(b, i):
    data, shift = 0, 1
    while True:
        x = b[i]; i += 1
        data += (x & 0x7f) * shift
        if x & 0x80: return data, i
        shift <<= 7; data += shift

def make(src, tgt, meta=b''):
    p = bytearray(b'BPS1') + enc(len(src)) + enc(len(tgt)) + enc(len(meta)) + meta
    i, n = 0, len(tgt)
    while i < n:
        if i < len(src) and src[i] == tgt[i]:
            j = i
            while j < n and j < len(src) and src[j] == tgt[j]: j += 1
            p += enc(((j - i - 1) << 2) | 0); i = j          # SourceRead
        else:
            j = i
            # stop the literal run when >=4 matching bytes resume
            while j < n and not (j + 3 < min(n, len(src)) and src[j:j+4] == tgt[j:j+4]): j += 1
            p += enc(((j - i - 1) << 2) | 1) + tgt[i:j]; i = j  # TargetRead
    for c in (zlib.crc32(src), zlib.crc32(tgt)): p += c.to_bytes(4, 'little')
    p += zlib.crc32(p).to_bytes(4, 'little')
    return bytes(p)

def apply(src, p):
    assert p[:4] == b'BPS1'
    assert zlib.crc32(p[:-4]) == int.from_bytes(p[-4:], 'little'), 'patch crc'
    assert zlib.crc32(src) == int.from_bytes(p[-12:-8], 'little'), 'source crc mismatch'
    i = 4; ss, i = dec(p, i); ts, i = dec(p, i); ms, i = dec(p, i); i += ms
    out = bytearray(); so = to = 0
    while i < len(p) - 12:
        d, i = dec(p, i); cmd, ln = d & 3, (d >> 2) + 1
        if cmd == 0: out += src[len(out):len(out) + ln]
        elif cmd == 1: out += p[i:i+ln]; i += ln
        elif cmd == 2:
            d, i = dec(p, i); so += (-1 if d & 1 else 1) * (d >> 1); out += src[so:so+ln]; so += ln
        else:
            d, i = dec(p, i); to += (-1 if d & 1 else 1) * (d >> 1)
            for _ in range(ln): out.append(out[to]); to += 1
    assert len(out) == ts and zlib.crc32(out) == int.from_bytes(p[-8:-4], 'little'), 'target crc'
    return bytes(out)

if __name__ == '__main__':
    if sys.argv[1] == 'make':
        s = open(sys.argv[2], 'rb').read(); t = open(sys.argv[3], 'rb').read()
        meta = sys.argv[5].encode() if len(sys.argv) > 5 else b''
        p = make(s, t, meta); open(sys.argv[4], 'wb').write(p)
        assert apply(s, p) == t; print('ok', len(p), 'bytes, verified')
    else:
        s = open(sys.argv[2], 'rb').read(); p = open(sys.argv[3], 'rb').read()
        open(sys.argv[4], 'wb').write(apply(s, p)); print('applied')
