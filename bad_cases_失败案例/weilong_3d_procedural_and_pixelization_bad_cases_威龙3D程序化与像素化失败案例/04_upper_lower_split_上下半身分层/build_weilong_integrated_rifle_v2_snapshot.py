#!/usr/bin/env python3
"""Build integrated torso+arms+hands+rifle sprites and movement/fire QA."""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


ROOT = Path(__file__).resolve().parent
GEN = ROOT / "generated_sources"
QA = ROOT / "qa_integrated_rifle"
QA.mkdir(exist_ok=True)

CELL = 128
DIRECTIONS = ["Down", "DownRight", "Right", "UpRight", "Up", "UpLeft", "Left", "DownLeft"]
SLUGS = ["down", "downright", "right", "upright", "up", "upleft", "left", "downleft"]
LEG_LENGTH = {"Down": 58, "DownRight": 43, "Right": 42, "UpRight": 46, "Up": 42, "UpLeft": 42, "Left": 42, "DownLeft": 42}
PELVIS_Y = [78, 80, 79, 77, 78, 80, 79, 77]
ART_VECTORS = {
    "Down": (0.60, 0.80),
    "DownRight": (0.707, 0.707),
    "Right": (1.0, 0.0),
    "UpRight": (0.707, -0.707),
    "Up": (0.60, -0.80),
    "UpLeft": (-0.707, -0.707),
    "Left": (-1.0, 0.0),
    "DownLeft": (-0.707, 0.707),
}
SAFE_CELL_OFFSETS = {"UpRight": (0, 4), "Up": (0, 10), "Left": (7, 0)}


def hard_alpha(im: Image.Image) -> Image.Image:
    out = im.convert("RGBA")
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255) if a >= 96 else (0, 0, 0, 0)
    return out


def source_path(slug: str) -> Path:
    if slug == "up":
        return GEN / "rifle_up_3phase_corrected_alpha.png"
    return GEN / f"rifle_{slug}_3phase_alpha.png"


def split_three_fixed_4x(im: Image.Image) -> list[Image.Image]:
    w, h = im.size
    result: list[Image.Image] = []
    for col in range(3):
        x0 = round(col * w / 3)
        x1 = round((col + 1) * w / 3)
        cell = im.crop((x0, 0, x1, h))
        pw = math.ceil(cell.width / 4) * 4
        ph = math.ceil(cell.height / 4) * 4
        padded = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        padded.alpha_composite(cell)
        result.append(hard_alpha(padded.resize((pw // 4, ph // 4), Image.Resampling.NEAREST)))
    return result


def register(cell: Image.Image, direction: str) -> tuple[Image.Image, dict]:
    bbox = cell.getchannel("A").getbbox()
    if bbox is None:
        raise RuntimeError("Empty integrated rifle frame")
    left, top, right, bottom = bbox
    source_pelvis_y = bottom - LEG_LENGTH[direction]
    alpha = cell.getchannel("A")
    xs: list[int] = []
    for y in range(max(top, source_pelvis_y - 4), min(bottom, source_pelvis_y + 18)):
        for x in range(left, right):
            if alpha.getpixel((x, y)):
                xs.append(x)
    source_pelvis_x = round(sum(xs) / len(xs)) if xs else (left + right - 1) // 2
    dx = 64 - source_pelvis_x
    dy = 78 - source_pelvis_y
    safe_dx, safe_dy = SAFE_CELL_OFFSETS.get(direction, (0, 0))
    dx += safe_dx
    dy += safe_dy

    out = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    source_count = sum(1 for a in alpha.getdata() if a)
    out.alpha_composite(cell, (dx, dy))
    final_count = sum(1 for a in out.getchannel("A").getdata() if a)
    final_bbox = out.getchannel("A").getbbox()
    return out, {
        "source_bbox": list(bbox),
        "estimated_source_pelvis": [source_pelvis_x, source_pelvis_y],
        "integer_translation": [dx, dy],
        "registered_bbox": list(final_bbox) if final_bbox else None,
        "clipped_opaque_pixels": source_count - final_count,
    }


def extract_upper_complete(full: Image.Image, direction: str) -> Image.Image:
    # The generated full-body source guarantees coherent anatomy.  Runtime upper
    # keeps the complete torso/arms/hands/weapon and a five-pixel belt overlap;
    # all pants, coat tails and legs below the overlap are removed together.
    keep = Image.new("L", (CELL, CELL), 0)
    seam_bottom = 94 if direction == "Up" else (88 if direction == "UpRight" else 84)
    ImageDraw.Draw(keep).rectangle((0, 0, CELL - 1, seam_bottom), fill=255)
    alpha = ImageChops.multiply(full.getchannel("A"), keep)
    out = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    out.paste(full, (0, 0), alpha)
    return out


def make_atlas(rows: list[list[Image.Image]]) -> Image.Image:
    atlas = Image.new("RGBA", (CELL * 3, CELL * 8), (0, 0, 0, 0))
    for d, phases in enumerate(rows):
        for p, cell in enumerate(phases):
            atlas.alpha_composite(cell, (p * CELL, d * CELL))
    return atlas


def load_lower() -> list[list[Image.Image]]:
    atlas = Image.open(ROOT / "weilong_body_lower_run_8dir_8f_v2.png").convert("RGBA")
    return [[atlas.crop((f * CELL, d * CELL, (f + 1) * CELL, (d + 1) * CELL)) for f in range(8)] for d in range(8)]


def checker(cell: Image.Image) -> Image.Image:
    bg = Image.new("RGBA", (CELL, CELL), (22, 28, 34, 255))
    draw = ImageDraw.Draw(bg)
    for y in range(0, CELL, 8):
        for x in range(0, CELL, 8):
            if (x // 8 + y // 8) % 2:
                draw.rectangle((x, y, x + 7, y + 7), fill=(29, 36, 43, 255))
    bg.alpha_composite(cell)
    return bg


def shifted_upper(upper: Image.Image, walk_frame: int) -> Image.Image:
    out = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    out.alpha_composite(upper, (0, PELVIS_Y[walk_frame] - 78))
    return out


def muzzle_point(upper: Image.Image, direction: str) -> tuple[int, int]:
    vx, vy = ART_VECTORS[direction]
    alpha = upper.getchannel("A")
    pts: list[tuple[float, int, int]] = []
    for y in range(CELL):
        for x in range(CELL):
            if alpha.getpixel((x, y)):
                pts.append(((x - 64) * vx + (y - 60) * vy, x, y))
    if not pts:
        return (64, 64)
    _, x, y = max(pts)
    return x, y


def add_muzzle_fx(frame: Image.Image, point: tuple[int, int], direction: str) -> Image.Image:
    out = frame.copy()
    vx, vy = ART_VECTORS[direction]
    x = round(point[0] + vx * 3)
    y = round(point[1] + vy * 3)
    d = ImageDraw.Draw(out)
    gold = (255, 174, 32, 255)
    pale = (255, 236, 124, 255)
    d.point((x, y), fill=pale)
    for k in (1, 2, 3):
        d.point((round(x + vx * k), round(y + vy * k)), fill=gold)
    d.point((x + round(-vy * 2), y + round(vx * 2)), fill=gold)
    d.point((x + round(vy * 2), y + round(-vx * 2)), fill=gold)
    return out


def save_qa(upper_rows: list[list[Image.Image]]) -> list[str]:
    lower = load_lower()
    files: list[str] = []
    action_phase_by_walk = [0, 0, 1, 2, 0, 0, 1, 2]
    for d, direction in enumerate(DIRECTIONS):
        frames: list[Image.Image] = []
        for walk in range(8):
            phase = action_phase_by_walk[walk]
            combo = lower[d][walk].copy()
            u = shifted_upper(upper_rows[d][phase], walk)
            combo.alpha_composite(u)
            if phase == 1:
                combo = add_muzzle_fx(combo, muzzle_point(u, direction), direction)
            frames.append(checker(combo).resize((512, 512), Image.Resampling.NEAREST))
        name = f"weilong_move_fire_integrated_{d + 1}_{direction.lower()}_v2.gif"
        frames[0].save(QA / name, save_all=True, append_images=frames[1:], duration=105, loop=0, disposal=2)
        files.append(name)

    turntable: list[Image.Image] = []
    for d, direction in enumerate(DIRECTIONS):
        for phase in range(3):
            frame = checker(upper_rows[d][phase])
            if phase == 1:
                frame = add_muzzle_fx(frame, muzzle_point(upper_rows[d][phase], direction), direction)
            turntable.append(frame.resize((512, 512), Image.Resampling.NEAREST))
    turntable[0].save(QA / "weilong_upper_complete_rifle_8dir_3phase_turntable_v2.gif", save_all=True, append_images=turntable[1:], duration=145, loop=0, disposal=2)
    files.append("weilong_upper_complete_rifle_8dir_3phase_turntable_v2.gif")

    contact = Image.new("RGBA", (CELL * 3, CELL * 8), (18, 23, 28, 255))
    for d in range(8):
        for p in range(3):
            contact.alpha_composite(checker(upper_rows[d][p]), (p * CELL, d * CELL))
    contact.resize((CELL * 6, CELL * 16), Image.Resampling.NEAREST).save(QA / "weilong_upper_complete_rifle_contact_v2.png")
    return files


def save_runtime_composite(upper_rows: list[list[Image.Image]]) -> dict[str, list[list[int]]]:
    lower = load_lower()
    action_phase_by_walk = [0, 0, 1, 2, 0, 0, 1, 2]
    rows: list[list[Image.Image]] = []
    bboxes: dict[str, list[list[int]]] = {}
    for d, direction in enumerate(DIRECTIONS):
        frames: list[Image.Image] = []
        dir_boxes: list[list[int]] = []
        for walk in range(8):
            phase = action_phase_by_walk[walk]
            combo = lower[d][walk].copy()
            combo.alpha_composite(shifted_upper(upper_rows[d][phase], walk))
            frames.append(combo)
            bbox = combo.getchannel("A").getbbox()
            dir_boxes.append(list(bbox) if bbox else [0, 0, 0, 0])
        rows.append(frames)
        bboxes[direction] = dir_boxes
    atlas = Image.new("RGBA", (CELL * 8, CELL * 8), (0, 0, 0, 0))
    for d in range(8):
        for f in range(8):
            atlas.alpha_composite(rows[d][f], (f * CELL, d * CELL))
    atlas.save(ROOT / "weilong_runtime_move_fire_integrated_8dir_8f_v2.png")
    return bboxes


def main() -> None:
    full_rows: list[list[Image.Image]] = []
    upper_rows: list[list[Image.Image]] = []
    measurements: dict[str, list[dict]] = {}
    for direction, slug in zip(DIRECTIONS, SLUGS):
        source = Image.open(source_path(slug)).convert("RGBA")
        full_phases: list[Image.Image] = []
        upper_phases: list[Image.Image] = []
        data: list[dict] = []
        for cell in split_three_fixed_4x(source):
            full, m = register(cell, direction)
            full_phases.append(full)
            upper_phases.append(extract_upper_complete(full, direction))
            data.append(m)
        full_rows.append(full_phases)
        upper_rows.append(upper_phases)
        measurements[direction] = data

    make_atlas(full_rows).save(ROOT / "weilong_body_full_rifle_8dir_3phase_source_v2.png")
    upper_atlas = make_atlas(upper_rows)
    upper_atlas.save(ROOT / "weilong_upper_complete_rifle_8dir_3phase_v2.png")
    qa_files = save_qa(upper_rows)
    runtime_bboxes = save_runtime_composite(upper_rows)
    alpha_values = sorted(set(upper_atlas.getchannel("A").getdata()))
    manifest = {
        "version": "weilong_integrated_rifle_v2",
        "directions": DIRECTIONS,
        "phases": ["AIM", "FIRE", "RECOVER"],
        "runtime_unit": "head + torso + complete arms + complete hands + current rifle",
        "hands_cut": False,
        "atlas": {"columns": 3, "rows": 8, "cell": [128, 128]},
        "logical_vectors": {"Down": [0, 1], "Up": [0, -1]},
        "art_vectors": {k: list(v) for k, v in ART_VECTORS.items()},
        "safe_cell_offsets": {k: list(v) for k, v in SAFE_CELL_OFFSETS.items()},
        "up_art_vector_reason": "logical Up remains strict; art uses 0.60,-0.80 to avoid a vertical line and cell clipping",
        "alpha_values": alpha_values,
        "qa": qa_files,
        "runtime_composite_bboxes": runtime_bboxes,
        "measurements": measurements,
    }
    (ROOT / "weilong_integrated_rifle_v2_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("built integrated rifle", alpha_values)
    print("clipped", {d: [x["clipped_opaque_pixels"] for x in m] for d, m in measurements.items()})


if __name__ == "__main__":
    main()
