"""Lay out a batch CSV's QR codes on cut-ready sheets (see docs/CODES.md).

Usage::

    uv run python -m scripts.qr_sheets --csv var/redemption-codes/tokyo-run1.csv \\
        --paper A4 --per-page 50 --qr-mm 20 \\
        --output var/redemption-codes/tokyo-run1.pdf

This is for test prints and planning, not for printing the drink caps
themselves (the factory prints from the CSV directly, per CODES.md section
1). The output PDF is a plaintext artifact of the codes, same as the CSV:
treat it the same way (encrypt before it leaves this machine, confirm
receipt, then delete it).

The layout maths (how many columns and rows fit a page at a given QR size)
are pure and raise ``ValueError`` before any drawing happens if the
requested QR size will not fit; nothing is ever silently shrunk below the
size the factory needs to test-scan it.
"""

from __future__ import annotations

import argparse
import csv
import io
import math
import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import segno
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

CSV_HEADER = ["batch_id", "city", "printed_code", "code", "qr_url"]

# Portrait, millimetres (width, height).
PAPER_SIZES_MM: dict[str, tuple[float, float]] = {
    "A4": (210.0, 297.0),
    "A3": (297.0, 420.0),
}

# Space the layout reserves beyond the QR itself: a blank edge so cutting
# does not clip a QR's quiet zone, and a line under it for the printed code
# (the manual-entry fallback if a scan fails).
DEFAULT_MARGIN_MM = 8.0
DEFAULT_GUTTER_MM = 1.5
DEFAULT_CODE_LINE_MM = 5.0

# QR error-correction level M (docs/CODES.md section 1).
QR_ERROR_LEVEL = "M"


class LayoutError(ValueError):
    """A sheet cannot be laid out: too many codes, or the QR size doesn't fit."""


@dataclass(frozen=True, slots=True)
class CsvRow:
    batch_id: str
    city: str
    printed_code: str
    code: str
    qr_url: str


@dataclass(frozen=True, slots=True)
class GridPlan:
    """How one page's codes are arranged: a ``columns`` x ``rows`` grid."""

    paper: str
    columns: int
    rows: int
    per_page: int
    page_width_mm: float
    page_height_mm: float
    margin_mm: float
    cell_width_mm: float
    cell_height_mm: float
    qr_mm: float


def read_csv_rows(path: Path) -> list[CsvRow]:
    """Read a batch CSV written by ``scripts.generate_codes``."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or list(reader.fieldnames) != CSV_HEADER:
            raise LayoutError(f"{path} does not have the expected header {CSV_HEADER}")
        return [
            CsvRow(
                batch_id=row["batch_id"],
                city=row["city"],
                printed_code=row["printed_code"],
                code=row["code"],
                qr_url=row["qr_url"],
            )
            for row in reader
        ]


def plan_grid(
    paper: str,
    per_page: int,
    qr_mm: float,
    *,
    margin_mm: float = DEFAULT_MARGIN_MM,
    gutter_mm: float = DEFAULT_GUTTER_MM,
    code_line_mm: float = DEFAULT_CODE_LINE_MM,
) -> GridPlan:
    """Choose a columns x rows grid for ``per_page`` codes on ``paper``.

    Picks the grid, among every ``(columns, rows)`` with
    ``columns * rows >= per_page``, that wastes the fewest cells and whose
    shape is closest to the page's own aspect ratio (so a portrait page
    gets more rows than columns, not a single wide strip). Raises
    :class:`LayoutError` if no grid lets a cell hold ``qr_mm`` plus the
    code line and a gutter around it -- callers should shrink ``qr_mm`` or
    ``per_page``, not expect a silently smaller QR than they asked for.
    """
    if per_page < 1:
        raise LayoutError("per_page must be at least 1")
    if qr_mm <= 0:
        raise LayoutError("qr_mm must be positive")
    try:
        width_mm, height_mm = PAPER_SIZES_MM[paper]
    except KeyError:
        raise LayoutError(
            f"unknown paper {paper!r}; choose one of {sorted(PAPER_SIZES_MM)}"
        ) from None

    printable_width = width_mm - 2 * margin_mm
    printable_height = height_mm - 2 * margin_mm
    page_aspect = printable_width / printable_height
    min_cell_width = qr_mm + gutter_mm
    min_cell_height = qr_mm + code_line_mm + gutter_mm

    best: tuple[tuple[int, float], int, int, float, float] | None = None
    for columns in range(1, per_page + 1):
        rows = math.ceil(per_page / columns)
        cell_width = printable_width / columns
        cell_height = printable_height / rows
        if cell_width < min_cell_width or cell_height < min_cell_height:
            continue
        waste = columns * rows - per_page
        aspect_gap = abs((columns / rows) - page_aspect)
        key = (waste, aspect_gap)
        if best is None or key < best[0]:
            best = (key, columns, rows, cell_width, cell_height)

    if best is None:
        raise LayoutError(
            f"a {qr_mm}mm QR (plus the code line and gutter) does not fit "
            f"{per_page} per {paper} page; shrink qr_mm or per_page"
        )
    _, columns, rows, cell_width, cell_height = best
    return GridPlan(
        paper=paper,
        columns=columns,
        rows=rows,
        per_page=per_page,
        page_width_mm=width_mm,
        page_height_mm=height_mm,
        margin_mm=margin_mm,
        cell_width_mm=cell_width,
        cell_height_mm=cell_height,
        qr_mm=qr_mm,
    )


def paginate(rows: list[CsvRow], per_page: int) -> list[list[CsvRow]]:
    """Split ``rows`` into pages of at most ``per_page`` codes each."""
    if per_page < 1:
        raise LayoutError("per_page must be at least 1")
    return [rows[i : i + per_page] for i in range(0, len(rows), per_page)]


def page_count(total_rows: int, per_page: int) -> int:
    if per_page < 1:
        raise LayoutError("per_page must be at least 1")
    return math.ceil(total_rows / per_page) if total_rows else 0


def _qr_image(payload: str, *, scale: int = 5, border: int = 2) -> ImageReader:
    """A :class:`QRCode` for ``payload``, rendered as a PNG reportlab can draw."""
    qr = segno.make(payload, error=QR_ERROR_LEVEL)
    buffer = io.BytesIO()
    qr.save(buffer, kind="png", scale=scale, border=border)
    buffer.seek(0)
    return ImageReader(buffer)


def _cell_positions(plan: GridPlan) -> Iterator[tuple[float, float]]:
    """Bottom-left (x, y) in mm of every cell, left-to-right, top-to-bottom."""
    for row in range(plan.rows):
        for column in range(plan.columns):
            x = plan.margin_mm + column * plan.cell_width_mm
            # PDF y grows upward; row 0 is the top row of the page.
            y = plan.page_height_mm - plan.margin_mm - (row + 1) * plan.cell_height_mm
            yield x, y


def _draw_crop_marks(
    pdf: canvas.Canvas, x: float, y: float, width: float, height: float
) -> None:
    """Short ticks at a cell's corners, extending past it (cut lines)."""
    tick = 2.5 * mm
    pdf.setLineWidth(0.2)
    for corner_x, corner_y, dx, dy in (
        (x, y, -tick, -tick),
        (x + width, y, tick, -tick),
        (x, y + height, -tick, tick),
        (x + width, y + height, tick, tick),
    ):
        pdf.line(corner_x, corner_y, corner_x + dx, corner_y)
        pdf.line(corner_x, corner_y, corner_x, corner_y + dy)


def render_sheets(
    rows: list[CsvRow],
    plan: GridPlan,
    output: Path,
    *,
    batch_id: str = "",
) -> int:
    """Write the cut-ready PDF; return the number of pages written.

    Every page carries the batch id and ``sheet n/N`` in the header margin,
    every cell gets its QR, the human-readable code under it, and crop
    marks at its corners. The PDF's page size is set in exact millimetres so
    printing at 100% scale ("actual size", no "fit to page") reproduces
    ``plan.qr_mm`` physically.
    """
    pages = paginate(rows, plan.per_page)
    total = len(pages)
    label = batch_id or (rows[0].batch_id if rows else "")

    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        pdf = canvas.Canvas(
            handle, pagesize=(plan.page_width_mm * mm, plan.page_height_mm * mm)
        )
        for page_number, page_rows in enumerate(pages, start=1):
            pdf.setFont("Helvetica", 7)
            pdf.drawString(
                plan.margin_mm * mm,
                (plan.page_height_mm - plan.margin_mm / 2) * mm,
                f"{label}    sheet {page_number}/{total}",
            )
            positions = _cell_positions(plan)
            for row, (x_mm, y_mm) in zip(page_rows, positions, strict=False):
                x, y = x_mm * mm, y_mm * mm
                qr_x = x + (plan.cell_width_mm * mm - plan.qr_mm * mm) / 2
                pdf.drawImage(
                    _qr_image(row.qr_url),
                    qr_x,
                    y + (plan.cell_height_mm * mm - plan.qr_mm * mm),
                    width=plan.qr_mm * mm,
                    height=plan.qr_mm * mm,
                )
                pdf.setFont("Courier", 7)
                pdf.drawCentredString(
                    x + (plan.cell_width_mm * mm) / 2,
                    y + 1 * mm,
                    row.printed_code,
                )
                _draw_crop_marks(
                    pdf, x, y, plan.cell_width_mm * mm, plan.cell_height_mm * mm
                )
            pdf.showPage()
        pdf.save()
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--paper", choices=sorted(PAPER_SIZES_MM), default="A4")
    parser.add_argument("--per-page", type=int, required=True)
    parser.add_argument("--qr-mm", type=float, default=20.0)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()

    rows = read_csv_rows(arguments.csv)
    plan = plan_grid(arguments.paper, arguments.per_page, arguments.qr_mm)
    pages = render_sheets(rows, plan, arguments.output)
    print(
        f"{arguments.output}: {len(rows)} codes, {pages} pages, "
        f"{plan.columns}x{plan.rows} per sheet, "
        f"{plan.cell_width_mm:.1f}x{plan.cell_height_mm:.1f}mm cells"
    )


if __name__ == "__main__":
    main()
