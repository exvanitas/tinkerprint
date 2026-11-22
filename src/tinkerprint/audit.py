"""audit: print every text string the share card on disk holds, before anyone shares it.

It parses card.svg itself with the local expat XML parser, in document order, so the listing always
describes the file that would be shared. Text nodes (CDATA too), comments and every attribute that
is not plain presentation are listed. A file that does not parse is reported and never certified.

card.png holds pixels, not strings, so it is checked two ways: its chunks must be image data only
(no tEXt, iTXt or zTXt, nothing else either), and its pixels must be exactly what the card fields
in sheet.json draw, the same fields that draw card.svg byte for byte. Then the listing above
covers card.png too. portrait.png is checked the same way. portrait.gif must hold image frames
only (no comment, plain-text or other application extension) and be, byte for byte, the loop the
card fields draw.

audit() also says whether every card file is there and certified, for the exit code.
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


def check_portrait_png(data: bytes, card: dict | None, pack=None) -> tuple:
    """(certified, message) for portrait.png: image data only, drawing exactly the card's portrait."""
    try:
        chunks = png_chunks(data)
    except NotPng as e:
        return False, f"portrait.png is not a valid PNG ({e}). It is not certified. Run build again."
    other = sorted({k.decode("latin-1") for k, _ in chunks if k not in IMAGE_CHUNKS})
    if other:
        return False, (f"portrait.png holds chunks that are not image data ({', '.join(other)}). It is not "
                       "certified. Run build again.")
    if not isinstance(card, dict) or not card.get("enabled"):
        return False, ("portrait.png holds image data only, but there are no card fields in sheet.json beside it "
                       "to check its pixels against. It is not certified. Run build again.")
    from .render_card import portrait_png
    try:
        same = png_image(chunks) == png_image(png_chunks(portrait_png(card, pack or _pack())))
    except (KeyError, TypeError, ValueError, AttributeError) as e:
        return False, f"portrait.png could not be checked ({type(e).__name__}). It is not certified. Run build again."
    if not same:
        return False, ("portrait.png does not draw the card's portrait. It is not certified. Run build again, with "
                       "the same --art-pack if you used one.")
    return True, "portrait.png holds image data only, and draws exactly the card's portrait."


class NotGif(ValueError):
    pass


def gif_blocks(data: bytes) -> list:
    """The blocks of a GIF89a in order, as ("image", None), ("extension", label, body) or the
    application's ("application", identifier). The image data itself is skipped, not decoded."""
    if data[:6] != b"GIF89a" or len(data) < 13:
        raise NotGif("no GIF89a header")
    flags = data[10]
    pos = 13 + (3 << ((flags & 7) + 1) if flags & 0x80 else 0)

    def sub_blocks(at):
        body = bytearray()
        while True:
            if at >= len(data):
                raise NotGif("a block is cut short")
            n = data[at]
            at += 1
            if not n:
                return bytes(body), at
            if at + n > len(data):
                raise NotGif("a block is cut short")
            body += data[at:at + n]
            at += n

    out = []
    while True:
        if pos >= len(data):
            raise NotGif("no trailer")
        tag = data[pos]
        if tag == 0x3B:
            if pos + 1 != len(data):
                raise NotGif("bytes after the trailer")
            return out
        if tag == 0x21:
            if pos + 2 > len(data):
                raise NotGif("a block is cut short")
            label = data[pos + 1]
            body, pos = sub_blocks(pos + 2)
            if label == 0xFF:
                out.append(("application", body[:11].decode("latin-1")))
            else:
                out.append(("extension", label, body))
        elif tag == 0x2C:
            if pos + 11 > len(data):
                raise NotGif("an image is cut short")
            local = data[pos + 9]
            pos += 10 + (3 << ((local & 7) + 1) if local & 0x80 else 0) + 1
            _, pos = sub_blocks(pos)
            out.append(("image", None))
        else:
            raise NotGif(f"unknown block 0x{tag:02x}")


GIF_TEXT = {0xFE: "a comment", 0x01: "plain text"}


def check_portrait_gif(data: bytes, card: dict | None, pack=None) -> tuple:
    """(certified, message) for portrait.gif: frames only, and byte for byte the card's idle loop."""
    try:
        blocks = gif_blocks(data)
    except NotGif as e:
        return False, f"portrait.gif is not a valid GIF ({e}). It is not certified. Run build again."
    text = sorted({GIF_TEXT.get(b[1], f"extension 0x{b[1]:02x}") for b in blocks
                   if b[0] == "extension" and b[1] != 0xF9})
    apps = sorted({b[1] for b in blocks if b[0] == "application" and b[1] != "NETSCAPE2.0"})
    if text or apps:
        what = ", ".join(text + [f"application {a!r}" for a in apps])
        return False, f"portrait.gif holds more than image frames ({what}). It is not certified. Run build again."
    if not isinstance(card, dict) or not card.get("enabled"):
        return False, ("portrait.gif holds image frames only, but there are no card fields in sheet.json beside it "
                       "to check it against. It is not certified. Run build again.")
    from .render_card import portrait_gif
    try:
        same = portrait_gif(card, pack or _pack()) == data
    except (KeyError, TypeError, ValueError, AttributeError) as e:
        return False, f"portrait.gif could not be checked ({type(e).__name__}). It is not certified. Run build again."
    if not same:
        return False, ("portrait.gif is not the loop the card's fields draw. It is not certified. Run build again, "
                       "with the same --art-pack if you used one.")
    return True, "portrait.gif holds image frames only, no comment or text, and is exactly the card's idle loop."


def _pack():
    from .art import default_pack
    return default_pack()


def _sheet_card(out_dir: str):
    try:
        with open(os.path.join(out_dir, "sheet.json"), encoding="utf-8") as f:
            return json.load(f).get("card")
    except (OSError, ValueError, AttributeError):
        return None


def portrait_line(card: dict) -> str:
    """The card fields the portrait's pixels come from, besides the set, class and shares."""
    from .look import of_card
    try:
        look = of_card(card)
    except (TypeError, ValueError, AttributeError):
        return "The portrait's look tokens in sheet.json could not be read."
    words = [f"presentation {look['presentation']}", f"skin {look['skin'] or 'from the art pack'}",
             f"hair {look['hair']}", f"eyes {look['eyes']}", f"expression {look['expression']}"]
    return "The portrait is drawn from the card's name and these look tokens: " + ", ".join(words) + "."


def audit(out_dir: str, profile=None, pack=None) -> tuple:
    """(lines, clean). clean is True only when every card file is there, parses, and is certified."""
    path = os.path.join(out_dir, "card.svg")
    png = os.path.join(out_dir, "card.png")
    if not os.path.isfile(path):
        lines = [f"No card.svg in {out_dir}. There is no card to share."]
        for name in ("card.png", "portrait.png", "portrait.gif"):
            if os.path.isfile(os.path.join(out_dir, name)):
                lines.append(f"{os.path.join(out_dir, name)} is there without card.svg, so it is not certified. "
                             "Run build again.")
        return lines, False
    with open(path, "rb") as f:
        data = f.read()
    try:
        strings = svg_strings(data.decode("utf-8"))
    except (NotSvg, UnicodeDecodeError) as e:
        return [f"{path} is not valid SVG ({e}). It is not certified. Run build again."], False
    lines = [f"{path} holds these {len(strings)} strings and nothing else:"]
    lines += [f"  {s}" for s in strings]
    card = _sheet_card(out_dir)
    if isinstance(card, dict) and card.get("enabled"):
        lines.append(portrait_line(card))
    clean = True
    for name, check in (("card.png", lambda b: check_png(b, card, data, pack)),
                        ("portrait.png", lambda b: check_portrait_png(b, card, pack)),
                        ("portrait.gif", lambda b: check_portrait_gif(b, card, pack))):
        where = os.path.join(out_dir, name)
        if os.path.isfile(where):
            with open(where, "rb") as f:
                ok, message = check(f.read())
        else:
            ok, message = False, f"No {name} in {out_dir}. Run build again to make one."
        clean = clean and ok
        lines.append(message)
    if profile is not None and not profile.card_enabled:
        lines.append("Warning: the profile no longer allows a card, but the card files are still there. Run build again.")
        clean = False
    return lines, clean


def audit_card(out_dir: str, profile=None, pack=None) -> list:
    """The listing alone. See audit() for the verdict."""
    return audit(out_dir, profile, pack)[0]
