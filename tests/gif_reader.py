"""Independent decoder for the global-palette, noninterlaced GIFs in the idle proofs."""
from io import BytesIO
from struct import unpack
from typing import NamedTuple


class Image(NamedTuple):
    rect: tuple
    data: bytes
    delay: int
    dispose: int
    clear: int | None


def sub_blocks(stream):
    parts = []
    while (size := stream.read(1)[0]):
        data = stream.read(size)
        assert len(data) == size
        parts.append(data)
    return b"".join(parts)


def expand(compressed, minimum):
    clear = 1 << minimum
    literal = [bytes([i]) for i in range(clear)]
    output = bytearray()
    window = count = 0
    source = iter(compressed)
    width = minimum+1
    while True:
        while count < width:
            window |= next(source) << count
            count += 8
        code = window & ((1 << width)-1)
        window >>= width
        count -= width
        if code == clear:
            table = literal + [None, None]
            width, last = minimum+1, None
        elif code == clear+1:
            return bytes(output)
        else:
            if code == len(table):
                phrase = last + last[:1]
            else:
                phrase = table[code]
            output.extend(phrase)
            if last is not None and len(table) < 4096:
                table.append(last + phrase[:1])
                if len(table) == 1 << width and width < 12:
                    width += 1
            last = phrase


class Gif:
    def __init__(self, raw):
        s = BytesIO(raw)
        assert s.read(6) == b"GIF89a"
        self.w, self.h, flags, background, _ = unpack("<HHBBB", s.read(7))
        assert flags & 128 and background == 0
        self.palette = ["#"+s.read(3).hex() for _ in range(2 << (flags & 7))]
        self.images = []
        self.loop = None
        while (tag := s.read(1)) != b";":
            if tag == b"!":
                label = s.read(1)
                if label == b"\xff":
                    assert s.read(12) == b"\x0bNETSCAPE2.0"
                    subcode, self.loop = unpack("<BH", sub_blocks(s))
                    assert subcode == 1
                else:
                    assert label == b"\xf9"
                    packed, delay, transparent = unpack("<BHB", sub_blocks(s))
                    clear = transparent if packed & 1 else None
                    disposal = (packed >> 2) & 7
            else:
                assert tag == b","
                x, y, w, h, flags = unpack("<HHHHB", s.read(9))
                assert flags == 0 and w and h and x+w <= self.w and y+h <= self.h
                minimum = s.read(1)[0]
                data = expand(sub_blocks(s), minimum)
                assert len(data) == w*h
                self.images.append(Image((x,y,w,h), data, delay*10, disposal, clear))
        assert not s.read()

    def screens(self, laps=1):
        canvas = bytearray(self.w*self.h)
        for _ in range(laps):
            for im in self.images:
                x, y, w, h = im.rect
                before = bytes(canvas) if im.dispose == 3 else None
                for j in range(h):
                    start = (y+j)*self.w+x
                    for dx, ink in enumerate(im.data[j*w:(j+1)*w]):
                        if ink != im.clear:
                            canvas[start+dx] = ink
                yield bytes(canvas)
                if im.dispose == 2:
                    for j in range(h):
                        start = (y+j)*self.w+x
                        canvas[start:start+w] = bytes(w)
                elif im.dispose == 3:
                    canvas[:] = before
                else:
                    assert im.dispose in (0, 1)

    def indices(self, frame, scale=1):
        indices = {c: i for i, c in reversed(list(enumerate(self.palette))) if i}
        indices[None] = 0
        return b"".join(b"".join(bytes([indices[c]])*scale for c in row)*scale for row in frame.px)
