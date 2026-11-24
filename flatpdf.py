import math
import re
import subprocess
from pypdf import PdfReader, PdfWriter
from pypdf.generic import FloatObject, NameObject, ArrayObject

INPUT     = "input.pdf"
OUTPUT    = "output.pdf"
OPACITY   = 0.30
PAD_THICK = 1   # extra on each side, perpendicular to the stroke (pt)
PAD_LEN   = 4   # extra at each end of the stroke (pt)

r = PdfReader(INPUT)
w = PdfWriter()
w.append(r)

num = rb"([-\d.]+)"

for page in w.pages:
    for a in page.get("/Annots", []):
        a = a.get_object()
        if a.get("/Subtype") != "/Ink":
            continue

        ap = a["/AP"]["/N"].get_object()
        data = ap.get_data()

        width = float(re.search(num + rb" w", data).group(1))
        (x1, y1), (x2, y2) = [
            (float(p), float(q))
            for p, q in re.findall(num + rb" " + num + rb" [ml]\b", data)
        ]

        # extend both ends along the stroke direction
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        ux, uy = (dx / L, dy / L) if L else (1.0, 0.0)
        x1 -= ux * PAD_LEN; y1 -= uy * PAD_LEN
        x2 += ux * PAD_LEN; y2 += uy * PAD_LEN
        width += 2 * PAD_THICK

        cr, cg, cb = [float(v) for v in a["/C"]]
        new = (
            f"/GS gs\nq\n{cr} {cg} {cb} RG\n{width} w\n2 J\n0 j\n"
            f"{x1} {y1} m\n{x2} {y2} l\nS\nQ\n"
        ).encode()
        ap.set_data(new)

        # opacity + multiply blend
        gs = ap["/Resources"]["/ExtGState"]["/GS"].get_object()
        gs[NameObject("/CA")] = FloatObject(OPACITY)
        gs[NameObject("/ca")] = FloatObject(OPACITY)
        gs[NameObject("/BM")] = NameObject("/Multiply")
        a[NameObject("/CA")] = FloatObject(OPACITY)

        # grow Rect/BBox so nothing gets clipped
        m = PAD_THICK + PAD_LEN
        rx1, ry1, rx2, ry2 = [float(v) for v in a["/Rect"]]
        box = ArrayObject([FloatObject(v) for v in
                           (rx1 - m, ry1 - m, rx2 + m, ry2 + m)])
        a[NameObject("/Rect")] = box
        ap[NameObject("/BBox")] = ArrayObject(box)

        # keep the annotation's own data consistent
        a[NameObject("/Border")] = ArrayObject(
            [FloatObject(0), FloatObject(0), FloatObject(width)])
        a[NameObject("/InkList")] = ArrayObject([ArrayObject(
            [FloatObject(v) for v in (x1, y1, x2, y2)])])

w.write("fixed.pdf")

# subprocess.run(
#     ["qpdf", "--flatten-annotations=all", "fixed.pdf", "flat.pdf"],
#     check=True,
# )
subprocess.run(
    ["pdftocairo", "-pdf", "fixed.pdf", OUTPUT],
    check=True,
)
print("Done:", OUTPUT)
