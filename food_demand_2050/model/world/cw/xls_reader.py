"""Minimal pure-Python reader for legacy .xls (OLE2 / BIFF8) workbooks.

The SILK model's elasticity/policy/price data ships only as old-format .xls
files, and this environment has neither xlrd nor LibreOffice.  This module
reads just enough of the OLE2 compound-document container and the BIFF8
record stream to recover cell values, exposing a ``Sheet`` whose interface
(``get(row, col)`` 1-indexed, ``cells``, ``max_row``, ``max_col``) matches the
openpyxl-backed ``Sheet`` used by :mod:`silk.gdxxrw`, so the same
``load_symbols`` machinery works on .xls and .xlsx alike.

Supported cell records: NUMBER, RK, MULRK, LABEL, LABELSST, FORMULA
(numeric and cached-string results).  Shared strings (SST) with CONTINUE
spill are handled.  This is not a general xls implementation; it targets the
data tables produced by GDXXRW-style spreadsheets.
"""

from __future__ import annotations

import struct


# --------------------------------------------------------------------------
# OLE2 compound document: extract a single named stream
# --------------------------------------------------------------------------
class _OLE2:
    def __init__(self, data: bytes):
        if data[:8] != b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
            raise ValueError("not an OLE2 file")
        self.data = data
        self.sector_size = 1 << struct.unpack_from("<H", data, 30)[0]
        self.mini_size = 1 << struct.unpack_from("<H", data, 32)[0]
        self.mini_cutoff = struct.unpack_from("<I", data, 56)[0]
        n_fat = struct.unpack_from("<I", data, 44)[0]
        dir_start = struct.unpack_from("<I", data, 48)[0]
        minifat_start = struct.unpack_from("<I", data, 60)[0]
        difat_start = struct.unpack_from("<I", data, 68)[0]
        n_difat = struct.unpack_from("<I", data, 72)[0]

        # DIFAT: first 109 entries in the header, rest chained
        difat = list(struct.unpack_from("<109I", data, 76))
        sect = difat_start
        for _ in range(n_difat):
            base = 512 + sect * self.sector_size
            vals = struct.unpack_from(
                "<%dI" % (self.sector_size // 4), data, base)
            difat.extend(vals[:-1])
            sect = vals[-1]
            if sect >= 0xFFFFFFFE:
                break

        # FAT
        self.fat = []
        for s in difat[:n_fat]:
            if s >= 0xFFFFFFFE:
                continue
            base = 512 + s * self.sector_size
            self.fat.extend(struct.unpack_from(
                "<%dI" % (self.sector_size // 4), data, base))

        # mini-FAT
        self.minifat = []
        s = minifat_start
        while s < 0xFFFFFFFE:
            base = 512 + s * self.sector_size
            self.minifat.extend(struct.unpack_from(
                "<%dI" % (self.sector_size // 4), data, base))
            s = self.fat[s]

        # directory entries
        dir_bytes = self._read_chain(dir_start)
        self.entries = []
        for off in range(0, len(dir_bytes), 128):
            ent = dir_bytes[off:off + 128]
            if len(ent) < 128:
                break
            nlen = struct.unpack_from("<H", ent, 64)[0]
            name = ent[:max(0, nlen - 2)].decode("utf-16-le", "ignore")
            etype = ent[66]
            start = struct.unpack_from("<I", ent, 116)[0]
            size = struct.unpack_from("<I", ent, 120)[0]
            self.entries.append((name, etype, start, size))

        # root entry (type 5) holds the mini-stream container
        root = next(e for e in self.entries if e[1] == 5)
        self.mini_container = self._read_chain(root[2])

    def _read_chain(self, start: int) -> bytes:
        out = []
        s = start
        while s < 0xFFFFFFFE:
            base = 512 + s * self.sector_size
            out.append(self.data[base:base + self.sector_size])
            s = self.fat[s]
        return b"".join(out)

    def _read_mini_chain(self, start: int, size: int) -> bytes:
        out = []
        s = start
        while s < 0xFFFFFFFE:
            base = s * self.mini_size
            out.append(self.mini_container[base:base + self.mini_size])
            s = self.minifat[s]
        return b"".join(out)[:size]

    def stream(self, *names) -> bytes:
        """Return the bytes of the first stream matching any given name."""
        want = {n.lower() for n in names}
        for name, etype, start, size in self.entries:
            if etype == 2 and name.lower() in want:
                if size < self.mini_cutoff:
                    return self._read_mini_chain(start, size)
                return self._read_chain(start)[:size]
        raise KeyError(f"stream not found: {names}")


# --------------------------------------------------------------------------
# BIFF8 record stream
# --------------------------------------------------------------------------
def _rk_to_double(rk: int) -> float:
    """Decode an RK value. ``rk`` is the raw unsigned 32-bit field."""
    rk &= 0xFFFFFFFF
    cents = rk & 1
    is_int = rk & 2
    if is_int:
        v = rk >> 2
        if v & 0x20000000:        # sign-extend 30-bit value
            v -= 0x40000000
        num = float(v)
    else:
        num = struct.unpack("<d", struct.pack("<Q", (rk & 0xFFFFFFFC) << 32))[0]
    if cents:
        num /= 100.0
    return num


def _read_unicode(buf: bytes, pos: int):
    """Read a BIFF8 Unicode string; return (text, new_pos). No CONTINUE here."""
    nchar = struct.unpack_from("<H", buf, pos)[0]
    flags = buf[pos + 2]
    pos += 3
    rich = 0
    ext = 0
    if flags & 0x08:
        rich = struct.unpack_from("<H", buf, pos)[0]
        pos += 2
    if flags & 0x04:
        ext = struct.unpack_from("<I", buf, pos)[0]
        pos += 4
    if flags & 0x01:  # 16-bit
        text = buf[pos:pos + nchar * 2].decode("utf-16-le", "ignore")
        pos += nchar * 2
    else:
        text = buf[pos:pos + nchar].decode("latin-1", "ignore")
        pos += nchar
    pos += rich * 4 + ext
    return text, pos


class _BiffSheet:
    def __init__(self):
        self.cells = {}
        self.max_row = 0
        self.max_col = 0

    def put(self, r, c, v):
        # store 1-indexed to match openpyxl-backed Sheet
        if v is None:
            return
        if isinstance(v, str) and v.strip() == "":
            return
        self.cells[(r + 1, c + 1)] = v
        if r + 1 > self.max_row:
            self.max_row = r + 1
        if c + 1 > self.max_col:
            self.max_col = c + 1

    def get(self, r, c):
        return self.cells.get((r, c))


class _SegReader:
    """Byte reader over a list of SST/CONTINUE segments.

    Each string's character payload may be split across segment boundaries;
    at every boundary the next segment begins with a fresh 1-byte flag that
    re-declares wide/narrow for the remaining characters.
    """

    def __init__(self, segments):
        self.segs = segments
        self.si = 0
        self.pos = 0

    def _cur(self):
        # advance to a segment that still has bytes
        while self.si < len(self.segs) and self.pos >= len(self.segs[self.si]):
            self.si += 1
            self.pos = 0
        return self.segs[self.si] if self.si < len(self.segs) else b""

    def read(self, k):
        out = []
        while k > 0:
            seg = self._cur()
            if not seg:
                break
            take = min(k, len(seg) - self.pos)
            out.append(seg[self.pos:self.pos + take])
            self.pos += take
            k -= take
        return b"".join(out)

    def u16(self):
        return struct.unpack("<H", self.read(2))[0]

    def u32(self):
        return struct.unpack("<I", self.read(4))[0]

    def u8(self):
        return self.read(1)[0]

    def seg_remaining(self):
        seg = self._cur()
        return len(seg) - self.pos if seg else 0

    def at_boundary_flag(self):
        # called when a string continues into a new segment: read its flag
        self._cur()
        return self.u8()


def _parse_sst(segments) -> list:
    """Assemble the shared-string table from SST + CONTINUE segment payloads."""
    rd = _SegReader(segments)
    rd.u32()                       # total occurrences
    unique = rd.u32()
    strings = []
    for _ in range(unique):
        nchar = rd.u16()
        flags = rd.u8()
        rich = rd.u16() if (flags & 0x08) else 0
        ext = rd.u32() if (flags & 0x04) else 0
        wide = flags & 0x01
        chars = []
        need = nchar
        while need > 0:
            avail = rd.seg_remaining()
            if avail <= 0:                      # segment exhausted at header
                wide = rd.at_boundary_flag()
                continue
            if wide & 0x01:
                take = min(need, avail // 2)
                if take == 0:                   # lone trailing byte; cross over
                    wide = rd.at_boundary_flag()
                    continue
                chars.append(rd.read(take * 2).decode("utf-16-le", "ignore"))
            else:
                take = min(need, avail)
                chars.append(rd.read(take).decode("latin-1", "ignore"))
            need -= take
            if need > 0:                         # split mid-string: next flag byte
                wide = rd.at_boundary_flag()
        if rich:
            rd.read(rich * 4)
        if ext:
            rd.read(ext)
        strings.append("".join(chars))
    return strings


def read_xls(path: str) -> dict:
    """Read an .xls workbook; return {sheet_name: _BiffSheet}."""
    with open(path, "rb") as fh:
        raw = fh.read()
    ole = _OLE2(raw)
    stream = ole.stream("Workbook", "Book")

    # First pass: split into records, join CONTINUE for SST.
    pos = 0
    n = len(stream)
    recs = []
    while pos + 4 <= n:
        rectype, length = struct.unpack_from("<HH", stream, pos)
        payload = stream[pos + 4:pos + 4 + length]
        recs.append((rectype, payload))
        pos += 4 + length

    # Build SST (0x00FC) + following CONTINUE (0x003C)
    sst = []
    for i, (rt, pl) in enumerate(recs):
        if rt == 0x00FC:
            segs = [pl]
            j = i + 1
            while j < len(recs) and recs[j][0] == 0x003C:
                segs.append(recs[j][1])
                j += 1
            sst = _parse_sst(segs)
            break

    # BOUNDSHEET (0x0085): sheet directory (name + stream position)
    boundsheets = []  # (bof_pos, name)
    for rt, pl in recs:
        if rt == 0x0085:
            bofpos = struct.unpack_from("<I", pl, 0)[0]
            name, _ = _read_unicode_short(pl, 6)
            boundsheets.append((bofpos, name))

    # Walk records, tracking sheet boundaries via BOF/EOF positions.
    sheets = {}
    order = [b[1] for b in boundsheets]
    cur = None
    sheet_idx = -1
    for rt, pl in recs:
        if rt == 0x0809:  # BOF
            # a BOF starts globals or a worksheet substream
            sheet_idx += 1
            if sheet_idx >= 1 and sheet_idx - 1 < len(order):
                cur = _BiffSheet()
                sheets[order[sheet_idx - 1]] = cur
            else:
                cur = None
            continue
        if cur is None:
            continue
        if rt == 0x0203:  # NUMBER
            r, c = struct.unpack_from("<HH", pl, 0)
            v = struct.unpack_from("<d", pl, 6)[0]
            cur.put(r, c, v)
        elif rt == 0x027E:  # RK
            r, c = struct.unpack_from("<HH", pl, 0)
            rk = struct.unpack_from("<I", pl, 6)[0]
            cur.put(r, c, _rk_to_double(rk))
        elif rt == 0x00BD:  # MULRK
            r, c0 = struct.unpack_from("<HH", pl, 0)
            c1 = struct.unpack_from("<H", pl, len(pl) - 2)[0]
            off = 4
            for c in range(c0, c1 + 1):
                rk = struct.unpack_from("<I", pl, off + 2)[0]
                cur.put(r, c, _rk_to_double(rk))
                off += 6
        elif rt == 0x00FD:  # LABELSST
            r, c, _xf, isst = struct.unpack_from("<HHHI", pl, 0)
            if isst < len(sst):
                cur.put(r, c, sst[isst])
        elif rt == 0x0204:  # LABEL (old inline string)
            r, c = struct.unpack_from("<HH", pl, 0)
            txt, _ = _read_unicode(pl, 6)
            cur.put(r, c, txt)
        elif rt == 0x0006:  # FORMULA
            r, c = struct.unpack_from("<HH", pl, 0)
            res = pl[6:14]
            if res[6] == 0xFF and res[7] == 0xFF:
                # non-numeric: string result comes in following STRING record;
                # bool/error/blank encoded in res[0]/res[2]
                if res[0] == 0:      # string result -> handled by STRING record
                    cur._pending = (r, c)
                elif res[0] == 1:    # boolean
                    cur.put(r, c, bool(res[2]))
                # error / blank: skip
            else:
                cur.put(r, c, struct.unpack("<d", res)[0])
        elif rt == 0x0207:  # STRING (result of preceding FORMULA)
            pend = getattr(cur, "_pending", None)
            if pend is not None:
                txt, _ = _read_unicode(pl, 0)
                cur.put(pend[0], pend[1], txt)
                cur._pending = None
    return sheets


def _read_unicode_short(buf: bytes, pos: int):
    """BOUNDSHEET name: 1-byte length then flag byte."""
    nchar = buf[pos]
    flags = buf[pos + 1]
    pos += 2
    if flags & 0x01:
        text = buf[pos:pos + nchar * 2].decode("utf-16-le", "ignore")
        pos += nchar * 2
    else:
        text = buf[pos:pos + nchar].decode("latin-1", "ignore")
        pos += nchar
    return text, pos
