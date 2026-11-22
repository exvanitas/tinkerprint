"""audit: print every text string the share card on disk holds, before anyone shares it.

It parses card.svg itself with the local expat XML parser, in document order, so the listing always
describes the file that would be shared. Text nodes (CDATA too), comments and every attribute that
is not plain presentation are listed. A file that does not parse is reported and never certified.

card.png holds pixels, not strings, so it is checked two ways: its chunks must be image data only
(no tEXt, iTXt or zTXt, nothing else either), and its pixels must be exactly what the card fields
in sheet.json draw, the same fields that draw card.svg byte for byte. Then the listing above
covers card.png too.
"""
from __future__ import annotations

import json
import os
import struct
import zlib

import pyexpat

# Attributes that only place or paint things. Every other attribute value counts as text.
PRESENTATION = {
    "xmlns", "viewBox", "width", "height", "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry",
    "fill", "stroke", "stroke-width", "stroke-linejoin", "stroke-linecap", "fill-opacity", "stroke-opacity",
    "opacity", "font-family", "font-size", "font-weight", "text-anchor", "letter-spacing", "points", "d",
    "transform", "role", "version", "preserveAspectRatio", "dominant-baseline", "shape-rendering",
}


class NotSvg(ValueError):
    pass


def svg_strings(svg: str) -> list:
    """Every text node, comment and text-bearing attribute in an SVG, in document order."""
    p = pyexpat.ParserCreate()
    p.ordered_attributes = True
    out: list = []
    buf: list = []

    def flush():
        t = "".join(buf).strip()
        if t:
            out.append(t)
        buf.clear()

    def start(name, attrs):
        flush()
        for k, v in zip(attrs[::2], attrs[1::2]):
            if k not in PRESENTATION and v.strip():
                out.append(v.strip())

    def refuse(*_):
        raise NotSvg("declarations and entities are not allowed in a card")

    p.StartElementHandler = start
    p.EndElementHandler = lambda name: flush()
    p.CharacterDataHandler = buf.append
    p.CommentHandler = lambda data: (flush(), out.append(data.strip()) if data.strip() else None)
    p.StartDoctypeDeclHandler = refuse
    p.EntityDeclHandler = refuse
    p.ProcessingInstructionHandler = lambda target, data: (flush(), out.append(f"{target} {data}".strip()))
    try:
        p.Parse(svg, True)
    except pyexpat.ExpatError as e:
        raise NotSvg(str(e)) from None
    flush()
    return out


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
IMAGE_CHUNKS = (b"IHDR", b"PLTE", b"tRNS", b"IDAT", b"IEND")
TEXT_CHUNKS = (b"tEXt", b"iTXt", b"zTXt")


class NotPng(ValueError):
    pass


def png_chunks(data: bytes) -> list:
    """Every chunk of a PNG as (type, body), after checking the signature, lengths and CRCs."""
    if data[:8] != PNG_SIGNATURE:
        raise NotPng("no PNG signature")
    out, pos = [], 8
    while pos < len(data):
        if pos + 12 > len(data):
            raise NotPng("a chunk is cut short")
        n, = struct.unpack(">I", data[pos:pos + 4])
        kind, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + n]
        if len(body) != n or pos + 12 + n > len(data):
            raise NotPng("a chunk is cut short")
        crc, = struct.unpack(">I", data[pos + 8 + n:pos + 12 + n])
        if zlib.crc32(kind + body) & 0xFFFFFFFF != crc:
            raise NotPng(f"bad CRC in {kind.decode('latin-1')!r}")
        out.append((kind, body))
        pos += 12 + n
        if kind == b"IEND":
            break
    if pos != len(data):
        raise NotPng("bytes after the end of the image")
    if not out or out[0][0] != b"IHDR" or out[-1][0] != b"IEND":
        raise NotPng("it does not start with IHDR and end with IEND")
    return out


def png_image(chunks: list) -> tuple:
    """What a PNG draws: its header, palette, transparency and the decompressed image rows.
    Two files with equal images draw the same pixels, whatever their compression."""
    head = b"".join(b for k, b in chunks if k == b"IHDR")
    plte = b"".join(b for k, b in chunks if k == b"PLTE")
    trns = b"".join(b for k, b in chunks if k == b"tRNS")
    try:
        rows = zlib.decompress(b"".join(b for k, b in chunks if k == b"IDAT"))
    except zlib.error as e:
        raise NotPng(f"image data does not decompress ({e})") from None
    return head, plte, trns, rows


def check_png(data: bytes, card: dict | None, svg: bytes | None, pack=None) -> tuple:
    """(certified, message) for card.png. card is the card fields from sheet.json, svg the
    card.svg bytes on disk."""
    try:
        chunks = png_chunks(data)
    except NotPng as e:
        return False, f"card.png is not a valid PNG ({e}). It is not certified. Run build again."
    kinds = [k.decode("latin-1") for k, _ in chunks]
    text = sorted({k for k in kinds if k.encode("latin-1") in TEXT_CHUNKS})
    if text:
        return False, f"card.png holds text chunks ({', '.join(text)}). It is not certified. Run build again."
    other = sorted({k for k in kinds if k.encode("latin-1") not in IMAGE_CHUNKS})
    if other:
        return False, (f"card.png holds chunks that are not image data ({', '.join(other)}). It is not certified. "
                       "Run build again.")
    if not isinstance(card, dict) or not card.get("enabled"):
        return False, ("card.png holds image data only, but there are no card fields in sheet.json beside it to "
                       "check its pixels against. It is not certified. Run build again.")
    from .render_card import render_card
    from .render_card_png import render_card_png
    try:
        same_svg = svg is not None and render_card(card, pack).encode("utf-8") == svg
        same_png = same_svg and png_image(chunks) == png_image(png_chunks(render_card_png(card, pack)))
    except (KeyError, TypeError, ValueError, AttributeError) as e:
        return False, f"card.png could not be checked ({type(e).__name__}). It is not certified. Run build again."
    if not same_svg:
        return False, ("card.svg is not what the card fields in sheet.json draw, so card.png cannot be matched to "
                       "it. card.png is not certified. Run build again, with the same --art-pack if you used one.")
    if not same_png:
        return False, ("card.png does not draw the card fields that card.svg draws. It is not certified. Run build "
                       "again, with the same --art-pack if you used one.")
    return True, "card.png holds image data only, and draws exactly the fields card.svg draws."


def _sheet_card(out_dir: str):
    try:
        with open(os.path.join(out_dir, "sheet.json"), encoding="utf-8") as f:
            return json.load(f).get("card")
    except (OSError, ValueError, AttributeError):
        return None


def audit_card(out_dir: str, profile=None, pack=None) -> list:
    path = os.path.join(out_dir, "card.svg")
    png = os.path.join(out_dir, "card.png")
    if not os.path.isfile(path):
        lines = [f"No card.svg in {out_dir}. There is no card to share."]
        if os.path.isfile(png):
            lines.append(f"{png} is there without card.svg, so it is not certified. Run build again.")
        return lines
    with open(path, "rb") as f:
        data = f.read()
    try:
        strings = svg_strings(data.decode("utf-8"))
    except (NotSvg, UnicodeDecodeError) as e:
        return [f"{path} is not valid SVG ({e}). It is not certified. Run build again."]
    lines = [f"{path} holds these {len(strings)} strings and nothing else:"]
    lines += [f"  {s}" for s in strings]
    if os.path.isfile(png):
        with open(png, "rb") as f:
            _, message = check_png(f.read(), _sheet_card(out_dir), data, pack)
        lines.append(message)
    else:
        lines.append(f"No card.png in {out_dir}. Run build again to make one.")
    if profile is not None and not profile.card_enabled:
        lines.append("Warning: the profile no longer allows a card, but the card files are still there. Run build again.")
    return lines
