#!/usr/bin/env python3
"""Build the scale-stable integrated rifle upper from one unified 8-dir master."""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "generated_sources" / "rifle_aim_8dir_unified_alpha.png"
EXPERIMENTAL = ROOT / "weilong_upper_complete_rifle_8dir_3phase_v2.png"
LOWER = ROOT / "weilong_body_lower_run_8dir_8f_v2.png"
QA = ROOT / "qa_stable_master"
QA.mkdir(exist_ok=True)

CELL = 128
DIRECTIONS = ["Down", "DownRight", "Right", "UpRight", "Up", "UpLeft", "Left", "DownLeft"]
VECTORS = [(0.60, 0.80), (0.707, 0.707), (1, 0), (0.707, -0.707), (0.60, -0.80), (-0.707, -0.707), (-1, 0), (-0.707, 0.707)]
PELVIS_BOB = [0, 2, 1, -1, 0, 2, 1, -1]


def hard(im: Image.Image) -> Image.Image:
    out = im.convert("RGBA")
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255) if a >= 96 else (0, 0, 0, 0)
    return out


def native_cells() -> list[Image.Image]:
    im = Image.open(SOURCE).convert("RGBA")
    w, h = im.size
    cells: list[Image.Image] = []
    for row in range(2):
        y0, y1 = round(row * h / 2), round((row + 1) * h / 2)
        for col in range(4):
            x0, x1 = round(col * w / 4), round((col + 1) * w / 4)
            c = im.crop((x0, y0, x1, y1))
            pw, ph = math.ceil(c.width / 4) * 4, math.ceil(c.height / 4) * 4
            pad = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); pad.alpha_composite(c)
            cells.append(hard(pad.resize((pw // 4, ph // 4), Image.Resampling.NEAREST)))
    return cells


def align_full(cell: Image.Image) -> Image.Image:
    bbox = cell.getchannel("A").getbbox()
    if bbox is None:
        raise RuntimeError("empty unified aim cell")
    l, t, r, b = bbox
    alpha = cell.getchannel("A")
    xs = [x for y in range(max(t, b - 5), b) for x in range(l, r) if alpha.getpixel((x, y))]
    foot_x = round(sum(xs) / len(xs)) if xs else (l + r - 1) // 2
    out = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    out.alpha_composite(cell, (64 - foot_x, 116 - (b - 1)))
    return out


def upper_from_full(full: Image.Image) -> Image.Image:
    out = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    out.alpha_composite(full.crop((0, 0, CELL, 86)), (0, 0))
    return out


def corrected_up() -> Image.Image:
    atlas = Image.open(EXPERIMENTAL).convert("RGBA")
    src = atlas.crop((0, 4 * CELL, CELL, 5 * CELL))
    bbox = src.getchannel("A").getbbox()
    if bbox is None:
        raise RuntimeError("missing corrected Up source")
    crop = src.crop(bbox)
    scaled = crop.resize((max(1, round(crop.width * 0.72)), max(1, round(crop.height * 0.72))), Image.Resampling.NEAREST)
    out = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    out.alpha_composite(scaled, (64 - scaled.width // 2, 85 - scaled.height))
    return out


def shift(im: Image.Image, dx: int, dy: int) -> Image.Image:
    out = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0)); out.alpha_composite(im, (dx, dy)); return out


def build_phases(aim: Image.Image, vector: tuple[float, float]) -> list[Image.Image]:
    vx, vy = vector
    fire = shift(aim, -round(vx * 2), -round(vy * 2))
    recover = shift(aim, -round(vx), -round(vy))
    return [aim, fire, recover]


def atlas(rows: list[list[Image.Image]], cols: int) -> Image.Image:
    out = Image.new("RGBA", (CELL * cols, CELL * len(rows)), (0, 0, 0, 0))
    for r, cells in enumerate(rows):
        for c, im in enumerate(cells): out.alpha_composite(im, (c * CELL, r * CELL))
    return out


def lower_rows() -> list[list[Image.Image]]:
    im = Image.open(LOWER).convert("RGBA")
    return [[im.crop((f * CELL, d * CELL, (f + 1) * CELL, (d + 1) * CELL)) for f in range(8)] for d in range(8)]


def checker(im: Image.Image) -> Image.Image:
    bg = Image.new("RGBA", (CELL, CELL), (22, 28, 34, 255)); d = ImageDraw.Draw(bg)
    for y in range(0, CELL, 8):
        for x in range(0, CELL, 8):
            if (x // 8 + y // 8) % 2: d.rectangle((x, y, x + 7, y + 7), fill=(29, 36, 43, 255))
    bg.alpha_composite(im); return bg


def muzzle(upper: Image.Image, vector: tuple[float, float]) -> tuple[int, int]:
    vx, vy = vector; a = upper.getchannel("A")
    pts = [((x - 64) * vx + (y - 60) * vy, x, y) for y in range(CELL) for x in range(CELL) if a.getpixel((x, y))]
    _, x, y = max(pts); return x, y


def flash(im: Image.Image, point: tuple[int, int], vector: tuple[float, float]) -> Image.Image:
    out = im.copy(); d = ImageDraw.Draw(out); vx, vy = vector
    x, y = round(point[0] + vx * 3), round(point[1] + vy * 3)
    d.point((x, y), fill=(255, 242, 136, 255))
    for k in (1, 2, 3): d.point((round(x + vx * k), round(y + vy * k)), fill=(255, 164, 28, 255))
    return out


def main() -> None:
    aims = [upper_from_full(align_full(c)) for c in native_cells()]
    aims[4] = corrected_up()
    phases = [build_phases(aims[d], VECTORS[d]) for d in range(8)]
    aim_atlas = atlas([[x] for x in aims], 1)
    phase_atlas = atlas(phases, 3)
    aim_atlas.save(ROOT / "weilong_upper_complete_rifle_aim_8dir_stable_v2.png")
    phase_atlas.save(ROOT / "weilong_upper_complete_rifle_8dir_3phase_stable_v2.png")

    contact = Image.new("RGBA", (CELL * 4, CELL * 2), (18, 23, 28, 255))
    for d, im in enumerate(aims): contact.alpha_composite(checker(im), ((d % 4) * CELL, (d // 4) * CELL))
    contact.resize((1536, 768), Image.Resampling.NEAREST).save(QA / "weilong_upper_complete_rifle_8dir_stable_contact_v2.png")

    lower = lower_rows(); phase_by_walk = [0, 0, 1, 2, 0, 0, 1, 2]
    runtime_rows: list[list[Image.Image]] = []
    gif_names: list[str] = []
    for d, direction in enumerate(DIRECTIONS):
        frames: list[Image.Image] = []
        gif_frames: list[Image.Image] = []
        for walk in range(8):
            p = phase_by_walk[walk]
            combo = lower[d][walk].copy(); u = shift(phases[d][p], 0, PELVIS_BOB[walk]); combo.alpha_composite(u)
            frames.append(combo)
            display = flash(combo, muzzle(u, VECTORS[d]), VECTORS[d]) if p == 1 else combo
            gif_frames.append(checker(display).resize((512, 512), Image.Resampling.NEAREST))
        runtime_rows.append(frames)
        name = f"weilong_move_fire_stable_{d + 1}_{direction.lower()}_v2.gif"
        gif_frames[0].save(QA / name, save_all=True, append_images=gif_frames[1:], duration=105, loop=0, disposal=2)
        gif_names.append(name)
    atlas(runtime_rows, 8).save(ROOT / "weilong_runtime_move_fire_8dir_8f_stable_v2.png")

    turn: list[Image.Image] = []
    for d in range(8):
        for p in range(3):
            im = flash(phases[d][p], muzzle(phases[d][p], VECTORS[d]), VECTORS[d]) if p == 1 else phases[d][p]
            turn.append(checker(im).resize((512, 512), Image.Resampling.NEAREST))
    turn[0].save(QA / "weilong_upper_complete_rifle_8dir_turntable_stable_v2.gif", save_all=True, append_images=turn[1:], duration=145, loop=0, disposal=2)

    data = {
        "version": "stable_unified_master_v2",
        "directions": DIRECTIONS,
        "runtime_unit": "torso + complete arms + complete hands + rifle",
        "hands_cut": False,
        "phases": ["AIM", "FIRE", "RECOVER"],
        "phase_build": "AIM is unified redrawn master; FIRE/RECOVER use whole-unit integer recoil so hands cannot detach",
        "up_override": "corrected slanted integrated Up source, globally nearest-scaled to match the unified master",
        "alpha_values": sorted(set(phase_atlas.getchannel("A").getdata())),
        "qa_gifs": gif_names + ["weilong_upper_complete_rifle_8dir_turntable_stable_v2.gif"],
        "upper_bboxes": {DIRECTIONS[d]: list(aims[d].getchannel("A").getbbox()) for d in range(8)},
    }
    (ROOT / "weilong_upper_complete_stable_v2_manifest.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(data["upper_bboxes"], ensure_ascii=False))


if __name__ == "__main__": main()
