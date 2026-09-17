"""Tiny dependency-free PDF writer: pages, vector paths, base-14 text."""

import zlib


def _esc(s):
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _latin(s):
    return str(s).encode("latin-1", "replace").decode("latin-1")


class PDF:
    A4 = (595, 842)

    def __init__(self, w=A4[0], h=A4[1], compress=True):
        self.w, self.h = w, h
        self.pages = []
        self.cur = None
        self.compress = compress

    def add_page(self):
        self.cur = []
        self.pages.append(self.cur)
        return self.cur

    def _c(self, c):
        return "%s %s %s" % tuple("%.3f" % (v / 255.0) for v in c)

    def _paint(self, fill, stroke, sw):
        if fill:
            self.cur.append(self._c(fill) + " rg")
        if stroke:
            self.cur.append("%s RG %s w" % (self._c(stroke), sw))

    @staticmethod
    def _mode(fill, stroke):
        return " f" if fill and not stroke else " S" if not fill else " B"

    def poly(self, pts, fill=None, stroke=None, sw=1.0):
        d = "%.2f %.2f m " % (pts[0][0], self.h - pts[0][1])
        for p in pts[1:]:
            d += "%.2f %.2f l " % (p[0], self.h - p[1])
        self._paint(fill, stroke, sw)
        self.cur.append(d + "h" + self._mode(fill, stroke))

    def line(self, x1, y1, x2, y2, color=(0, 0, 0), sw=1.0):
        self.cur.append("%s RG %.2f w" % (self._c(color), sw))
        self.cur.append("%.2f %.2f m %.2f %.2f l S" %
                        (x1, self.h - y1, x2, self.h - y2))

    def rect(self, x, y, w, h, rx=0, fill=None, stroke=None, sw=1.0):
        self._paint(fill, stroke, sw)
        self.cur.append("%.2f %.2f %.2f %.2f re%s" %
                        (x, self.h - y - h, w, h, self._mode(fill, stroke)))

    def circle(self, cx, cy, r, fill=None, stroke=None, sw=1.0, alpha=1.0,
               paper=(255, 255, 255)):
        if alpha < 0.999 and fill:
            fill = tuple(round(p + (f - p) * alpha) for p, f in zip(paper, fill))
        k = 0.5523 * r
        X, Y = cx, self.h - cy
        pts = [(X + r, Y), (X + r, Y + k), (X + k, Y + r), (X, Y + r),
               (X - k, Y + r), (X - r, Y + k), (X - r, Y),
               (X - r, Y - k), (X - k, Y - r), (X, Y - r),
               (X + k, Y - r), (X + r, Y - k), (X + r, Y)]
        d = "%.2f %.2f m " % pts[0]
        for i in range(1, len(pts), 3):
            d += "%.2f %.2f %.2f %.2f %.2f %.2f c " % (pts[i] + pts[i + 1] + pts[i + 2])
        self._paint(fill, stroke, sw)
        self.cur.append(d + "h" + self._mode(fill, stroke))

    def ellipse(self, cx, cy, rx, ry, fill=None, stroke=None, sw=1.0, alpha=1.0,
                paper=(255, 255, 255)):
        if alpha < 0.999 and fill:
            fill = tuple(round(p + (f - p) * alpha) for p, f in zip(paper, fill))
        kx, ky = 0.5523 * rx, 0.5523 * ry
        X, Y = cx, self.h - cy
        pts = [(X + rx, Y), (X + rx, Y + ky), (X + kx, Y + ry), (X, Y + ry),
               (X - kx, Y + ry), (X - rx, Y + ky), (X - rx, Y),
               (X - rx, Y - ky), (X - kx, Y - ry), (X, Y - ry),
               (X + kx, Y - ry), (X + rx, Y - ky), (X + rx, Y)]
        d = "%.2f %.2f m " % pts[0]
        for i in range(1, len(pts), 3):
            d += "%.2f %.2f %.2f %.2f %.2f %.2f c " % (pts[i] + pts[i + 1] + pts[i + 2])
        self._paint(fill, stroke, sw)
        self.cur.append(d + "h" + self._mode(fill, stroke))

    def art(self, shapes, ox, oy_top, scale, paper=(255, 255, 255)):
        import charart
        self.cur.extend(charart.pdf_ops(shapes, ox, oy_top, scale, paper))

    def text(self, x, y, size, s, bold=False, color=(0, 0, 0)):
        font = "/F2" if bold else "/F1"
        self.cur.append("%s rg" % self._c(color))
        self.cur.append("BT %s %s Tf 1 0 0 1 %.2f %.2f Tm (%s) Tj ET" %
                        (font, size, x, self.h - y, _esc(_latin(s))))

    def bar(self, x, y, w, h, frac, back=(225, 228, 235), fill=(60, 90, 200)):
        self.rect(x, y, w, h, fill=back)
        if frac > 0:
            self.rect(x, y, max(2, w * min(frac, 1.0)), h, fill=fill)

    def out(self):
        objs = {}
        n_pages = len(self.pages)
        first_page_obj = 5

        page_obj = lambda i: first_page_obj + i * 2
        content_obj = lambda i: first_page_obj + i * 2 + 1

        kids = " ".join("%d 0 R" % page_obj(i) for i in range(n_pages))
        objs[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
        objs[2] = ("<< /Type /Pages /Kids [%s] /Count %d >>" %
                   (kids, n_pages)).encode()
        objs[3] = (b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
                   b"/Encoding /WinAnsiEncoding >>")
        objs[4] = (b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold "
                   b"/Encoding /WinAnsiEncoding >>")
        for i, ops in enumerate(self.pages):
            stream = "\n".join(ops).encode("latin-1", "replace")
            if self.compress and len(stream) > 200:
                stream = zlib.compress(stream)
                filt = " /Filter /FlateDecode"
            else:
                filt = ""
            objs[page_obj(i)] = (
                "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %d %d] "
                "/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
                "/Contents %d 0 R >>" % (self.w, self.h, content_obj(i))).encode()
            objs[content_obj(i)] = (
                ("<< /Length %d%s >>\nstream\n" % (len(stream), filt)).encode()
                + stream + b"\nendstream")

        buf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = {1: len(buf)}
        for num in sorted(objs):
            offsets.setdefault(num, len(buf))
            buf += ("%d 0 obj\n" % num).encode() + objs[num] + b"\nendobj\n"
        maxobj = max(objs)
        xref_at = len(buf)
        buf += ("xref\n0 %d\n" % (maxobj + 1)).encode()
        buf += b"0000000000 65535 f \n"
        for num in range(1, maxobj + 1):
            buf += ("%010d 00000 n \n" % offsets.get(num, 0)).encode()
        buf += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" %
                (maxobj + 1, xref_at)).encode()
        return bytes(buf)
