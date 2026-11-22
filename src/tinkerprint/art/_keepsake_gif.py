"""Lossless GIF89a for small pixel-art loops. Index zero is clear."""
from struct import pack


def _lzw(pixels, minimum):
    """Pack variable-width LZW codes least-significant bit first."""
    clear = 1 << minimum
    end = clear + 1
    width, next_code = minimum+1, end+1
    table = {}
    data = bytearray()
    bits = count = 0

    def emit(code):
        nonlocal bits, count
        bits |= code << count
        count += width
        while count >= 8:
            data.append(bits & 255)
            bits >>= 8
            count -= 8

    emit(clear)
    prefix = pixels[0]
    for symbol in pixels[1:]:
        pair = (prefix, symbol)
        match = table.get(pair)
        if match is not None:
            prefix = match
            continue
        emit(prefix)
        # The decoder installs each phrase one code later than the encoder.
        if next_code == 4096:
            emit(clear)
            table.clear()
            width, next_code = minimum+1, end+1
        else:
            if next_code == 1 << width:
                width += 1
            table[pair] = next_code
            next_code += 1
        prefix = symbol
    emit(prefix)
    if next_code == 1 << width and width < 12:
        width += 1
    emit(end)
    if count:
        data.append(bits)
    return b"".join(bytes([len(block)]) + block for block in
                    (data[i:i+255] for i in range(0, len(data), 255))) + b"\0"


def _patch(base, frame, following, w, h, scale, restore):
    """Plan what to paint now and what must clear before the next frame."""
    left, top, right, bottom = w, h, -1, -1
    erase = False
    for i, (old, ink, after) in enumerate(zip(base, frame, following)):
        retiring = not restore and ink and not after
        if old == ink and not retiring:
            continue
        x, y = i % w, i // w
        left, right = min(left, x), max(right, x)
        top, bottom = min(top, y), max(bottom, y)
        erase |= bool(retiring)
    if right < 0:
        left = top = right = bottom = 0  # a timed hold
    width = right-left+1
    next_base = bytearray(frame) if erase else frame
    block = bytearray()
    for y in range(top, bottom+1):
        start = y*w+left
        row = bytes(c if c != base[i] else 0
                    for i, c in enumerate(frame[start:start+width], start))
        if scale != 1:
            row = b"".join(bytes([c])*scale for c in row)
        block.extend(row*scale)
        if erase:
            next_base[start:start+width] = bytes(width)
    rect = (left*scale, top*scale, width*scale, (bottom-top+1)*scale)
    if restore:
        return rect, block, 3, base
    return rect, block, (2 if erase else 1), next_base


def _images(indexed, delays_ms, w, h, scale, minimum, anchor=False):
    out = bytearray()
    base = bytes(w*h)
    for i, frame in enumerate(indexed):
        following = indexed[(i+1) % len(indexed)]
        rect, pixels, disposal, base = _patch(base, frame, following, w, h,
                                              scale, restore=anchor and i > 0)
        out += b"\x21\xf9\x04" + pack("<BHBB", disposal*4+1, delays_ms[i]//10, 0, 0)
        out += b"\x2c" + pack("<HHHHBB", *rect, 0, minimum) + _lzw(pixels, minimum)
    return out


def encode(frames, delays_ms, scale=1):
    """Encode equal-sized Canvases with exact centisecond timing, looping forever.

    Up to 255 distinct opaque RGB colors are available across the whole loop.
    Compute disposal and differences on the native grid, then enlarge losslessly.
    """
    frames, delays_ms = tuple(frames), tuple(delays_ms)
    if not frames or len(frames) != len(delays_ms):
        raise ValueError("supply one delay per frame")
    w, h = frames[0].w, frames[0].h
    if (not isinstance(scale, int) or scale < 1 or
            not (0 < w*scale < 65536 and 0 < h*scale < 65536)):
        raise ValueError("invalid scaled GIF dimensions")
    if any((f.w, f.h) != (w, h) for f in frames):
        raise ValueError("GIF frame sizes differ")
    if any(not isinstance(t, int) or t % 10 or not 10 <= t <= 655350 for t in delays_ms):
        raise ValueError("GIF delays must be positive whole centiseconds")
    colors = sorted({ink for frame in frames for ink in frame.colors()})
    if len(colors) > 255:
        raise ValueError("GIF needs at most 255 opaque colors plus transparency")
    depth = max(1, len(colors).bit_length())
    minimum = max(2, depth)
    palette = b"\0\0\0" + b"".join(bytes.fromhex(c[1:]) for c in colors)
    index = {c: i for i, c in enumerate(colors, 1)}
    index[None] = 0
    indexed = [bytes(index[c] for row in frame.px for c in row) for frame in frames]
    out = bytearray(b"GIF89a" + pack("<HHBBB", w*scale, h*scale, 0xf0 | (depth-1), 0, 0))
    out += palette.ljust(3 << depth, b"\0")
    out += b"\x21\xff\x0bNETSCAPE2.0\x03\x01\0\0\0"
    images = _images(indexed, delays_ms, w, h, scale, minimum)
    # A resting silhouette often fits inside every later pose. Try keeping
    # it on the screen and restoring it after each overlay. This can avoid
    # redrawing an entire lineup when just two distant shoulders fall.
    first = indexed[0]
    if 0 in first and all(not any(a and not b for a,b in zip(first, frame))
                          for frame in indexed[1:]):
        overlays = _images(indexed, delays_ms, w, h, scale, minimum, anchor=True)
        if len(overlays) < len(images):
            images = overlays
    return bytes(out + images + b"\x3b")
