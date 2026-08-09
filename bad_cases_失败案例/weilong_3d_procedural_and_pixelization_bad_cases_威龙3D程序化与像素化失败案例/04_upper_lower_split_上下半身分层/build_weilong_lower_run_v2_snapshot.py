#!/usr/bin/env python3
"""Build Weilong's 8-direction, 8-frame lower-body run atlas and QA.

Each input strip was redrawn as a complete running character.  This builder
restores the fixed 4x pixel grid, registers the pelvis using integer shifts,
and then extracts the lower-body layer.  It never creates animation by attaching
new legs to the approved static body.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


ROOT = Path(__file__).resolve().parent
V1 = ROOT.parent / "weilong_pixel_art_v1"
GEN = ROOT / "generated_sources"
QA = ROOT / "qa"
QA.mkdir(exist_ok=True)

CELL = 128
FRAMES = 8
DIRECTIONS = [
    "Down",
    "DownRight",
    "Right",
    "UpRight",
    "Up",
    "UpLeft",
    "Left",
    "DownLeft",
]
SLUGS = ["down", "downright", "right", "upright", "up", "upleft", "left", "downleft"]
PELVIS_Y = [78, 80, 79, 77, 78, 80, 79, 77]


def hard_alpha(im: Image.Image) -> Image.Image:
    rgba = im.convert("RGBA")
    px = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255) if a >= 96 else (0, 0, 0, 0)
    return rgba


def split_source_4x(source: Image.Image) -> list[Image.Image]:
    """Split the 4x2 layout first, then restore every cell at fixed 1/4 scale."""
    w, h = source.size
    cells: list[Image.Image] = []
    for row in range(2):
        y0 = round(row * h / 2)
        y1 = round((row + 1) * h / 2)
        for col in range(4):
            x0 = round(col * w / 4)
            x1 = round((col + 1) * w / 4)
            cell = source.crop((x0, y0, x1, y1))
            pw = math.ceil(cell.width / 4) * 4
            ph = math.ceil(cell.height / 4) * 4
            padded = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
            padded.alpha_composite(cell)
            cells.append(hard_alpha(padded.resize((pw // 4, ph // 4), Image.Resampling.NEAREST)))
    return cells


def estimate_pelvis(cell: Image.Image) -> tuple[int, int, tuple[int, int, int, int]]:
    bbox = cell.getchannel("A").getbbox()
    if bbox is None:
        raise RuntimeError("Empty run frame")
    left, top, right, bottom = bbox
    height = bottom - top
    band_top = top + round(height * 0.42)
    band_bottom = top + round(height * 0.60)
    alpha = cell.getchannel("A")
    xs: list[int] = []
    for y in range(band_top, min(band_bottom, cell.height)):
        for x in range(max(0, left), min(right, cell.width)):
            if alpha.getpixel((x, y)):
                xs.append(x)
    cx = round(sum(xs) / len(xs)) if xs else (left + right - 1) // 2
    py = top + round(height * 0.55)
    return cx, py, bbox


def register(cell: Image.Image, frame: int) -> tuple[Image.Image, dict]:
    px, py, bbox = estimate_pelvis(cell)
    dx = 64 - px
    dy = PELVIS_Y[frame] - py
    out = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    out.alpha_composite(cell, (dx, dy))
    final_bbox = out.getchannel("A").getbbox()
    if final_bbox is None:
        raise RuntimeError("Registered frame is empty")
    return out, {
        "source_bbox": list(bbox),
        "estimated_source_pelvis": [px, py],
        "target_pelvis": [64, PELVIS_Y[frame]],
        "integer_translation": [dx, dy],
        "registered_bbox": list(final_bbox),
        "registered_visual_height": final_bbox[3] - final_bbox[1],
    }


def extract_lower(full: Image.Image, frame: int) -> Image.Image:
    py = PELVIS_Y[frame]
    mask = Image.new("L", (CELL, CELL), 0)
    d = ImageDraw.Draw(mask)
    # Narrow pelvis cap excludes hands at waist level; below the hip crease the
    # whole canvas is retained so extended run legs are never clipped.
    d.polygon([(45, py - 7), (83, py - 7), (88, py + 5), (40, py + 5)], fill=255)
    d.rectangle((0, py + 4, CELL - 1, CELL - 1), fill=255)
    alpha = ImageChops.multiply(full.getchannel("A"), mask)
    out = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    out.paste(full, (0, 0), alpha)
    return out


def load_v1_upper() -> list[Image.Image]:
    atlas = Image.open(V1 / "weilong_body_upper_idle_8dir_v1.png").convert("RGBA")
    return [atlas.crop((0, i * CELL, CELL, (i + 1) * CELL)) for i in range(8)]


def make_atlas(rows: list[list[Image.Image]]) -> Image.Image:
    atlas = Image.new("RGBA", (CELL * FRAMES, CELL * len(rows)), (0, 0, 0, 0))
    for r, frames in enumerate(rows):
        for f, cell in enumerate(frames):
            atlas.alpha_composite(cell, (f * CELL, r * CELL))
    return atlas


def checker(cell: Image.Image) -> Image.Image:
    out = Image.new("RGBA", cell.size, (22, 28, 34, 255))
    d = ImageDraw.Draw(out)
    for y in range(0, CELL, 8):
        for x in range(0, CELL, 8):
            if (x // 8 + y // 8) % 2:
                d.rectangle((x, y, x + 7, y + 7), fill=(29, 36, 43, 255))
    out.alpha_composite(cell)
    return out


def composite_run(lower: Image.Image, upper: Image.Image, frame: int) -> Image.Image:
    composed = lower.copy()
    bob = PELVIS_Y[frame] - 78
    moved_upper = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    moved_upper.alpha_composite(upper, (0, bob))
    composed.alpha_composite(moved_upper)
    return composed


def save_gifs(lower_rows: list[list[Image.Image]], upper: list[Image.Image]) -> list[str]:
    files: list[str] = []
    for r, direction in enumerate(DIRECTIONS):
        composite = [composite_run(lower_rows[r][f], upper[r], f) for f in range(FRAMES)]
        frames = [checker(c).resize((512, 512), Image.Resampling.NEAREST) for c in composite]
        name = f"weilong_run_loop_{r + 1}_{direction.lower()}_8f_v2.gif"
        frames[0].save(QA / name, save_all=True, append_images=frames[1:], duration=95, loop=0, disposal=2)
        files.append(name)
    return files


def qa_contact(full_rows: list[list[Image.Image]], lower_rows: list[list[Image.Image]], upper: list[Image.Image]) -> None:
    # Each direction occupies two rows: complete redrawn action, then runtime
    # lower + approved V1 upper composite.
    native = Image.new("RGBA", (CELL * FRAMES, CELL * 16), (18, 23, 28, 255))
    for d in range(8):
        for f in range(8):
            native.alpha_composite(checker(full_rows[d][f]), (f * CELL, d * CELL * 2))
            combo = composite_run(lower_rows[d][f], upper[d], f)
            native.alpha_composite(checker(combo), (f * CELL, d * CELL * 2 + CELL))
    native.save(QA / "weilong_run_full_vs_layered_contact_v2.png")


def main() -> None:
    full_rows: list[list[Image.Image]] = []
    lower_rows: list[list[Image.Image]] = []
    measurements: dict[str, list[dict]] = {}

    for direction, slug in zip(DIRECTIONS, SLUGS):
        source = Image.open(GEN / f"run_{slug}_8f_alpha.png").convert("RGBA")
        registered: list[Image.Image] = []
        lower: list[Image.Image] = []
        data: list[dict] = []
        for frame, source_cell in enumerate(split_source_4x(source)):
            full, m = register(source_cell, frame)
            registered.append(full)
            lower.append(extract_lower(full, frame))
            data.append(m)
        full_rows.append(registered)
        lower_rows.append(lower)
        measurements[direction] = data

    full_atlas = make_atlas(full_rows)
    lower_atlas = make_atlas(lower_rows)
    full_atlas.save(ROOT / "weilong_body_full_run_source_8dir_8f_v2.png")
    lower_atlas.save(ROOT / "weilong_body_lower_run_8dir_8f_v2.png")

    upper = load_v1_upper()
    composite_rows = [[composite_run(lower_rows[d][f], upper[d], f) for f in range(8)] for d in range(8)]
    composite_atlas = make_atlas(composite_rows)
    composite_atlas.save(ROOT / "weilong_runtime_run_composite_8dir_8f_v2.png")
    gif_files = save_gifs(lower_rows, upper)
    qa_contact(full_rows, lower_rows, upper)

    alpha_values = sorted(set(lower_atlas.getchannel("A").getdata()))
    if alpha_values != [0, 255]:
        raise AssertionError(f"Lower atlas is not hard-alpha: {alpha_values}")

    manifest = {
        "version": "weilong_pixel_actions_v2",
        "directions": DIRECTIONS,
        "frame_phases": [
            "left_contact",
            "left_recoil_down",
            "passing_a",
            "up_a",
            "right_contact",
            "right_recoil_down",
            "passing_b",
            "up_b_to_loop",
        ],
        "atlas": {"columns": 8, "rows": 8, "cell": [128, 128], "column": "runFrame"},
        "pelvis_target_y_by_frame": PELVIS_Y,
        "source_scale_restore": "fixed 4x to 1x NEAREST per source cell; no fit-to-height and no per-frame scale",
        "construction": "complete full-body run redrawn first, lower layer extracted second",
        "hard_alpha": alpha_values,
        "qa_gifs": gif_files,
        "runtime_composite_visual_heights": {
            DIRECTIONS[d]: [
                (composite_rows[d][f].getchannel("A").getbbox()[3] - composite_rows[d][f].getchannel("A").getbbox()[1])
                for f in range(8)
            ]
            for d in range(8)
        },
        "measurements": measurements,
    }
    (ROOT / "weilong_lower_run_v2_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("built", len(DIRECTIONS), "directions x", FRAMES, "frames")
    print("alpha", alpha_values)


if __name__ == "__main__":
    main()
