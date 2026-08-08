from __future__ import annotations

import json
import statistics
from pathlib import Path

if __name__ == "__main__":
    raise SystemExit(
        "REJECTED_BAD_CASE: Luna Prototype 4 preserved an upper body while "
        "replacing lower-body motion. Rebuilding or reusing it is forbidden."
    )

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent.parent
COCOS_ROOT = WORKSPACE / "combat_lab" / "assets" / "resources" / "luna"
SOURCE_ROOT = ROOT / "v4_leg_revision_sources"
QA_ROOT = ROOT / "v4_leg_revision_qa"

CELL = 128
FOOT_Y = 116
CUT_Y = 84
DIRECTIONS = ("Down", "DownRight", "Right", "UpRight", "Up", "UpLeft", "Left", "DownLeft")
SOURCE_BODY = COCOS_ROOT / "luna_body_run_8dir_4f_v3.png"
OUTPUT_NAME = "luna_body_run_8dir_4f_v4.png"
SPEC_NAME = "luna_left_gait_v4_spec.json"

REPLACEMENTS = {
    5: SOURCE_ROOT / "upleft_4f_alpha.png",
    6: SOURCE_ROOT / "left_4f_alpha.png",
    7: SOURCE_ROOT / "downleft_4f_alpha.png",
}


def crop_grid(image: Image.Image, columns: int, rows: int) -> list[list[Image.Image]]:
    if image.size != (columns * CELL, rows * CELL):
        raise RuntimeError(f"Unexpected atlas size: {image.size}")
    return [
        [image.crop((column * CELL, row * CELL, (column + 1) * CELL, (row + 1) * CELL)) for column in range(columns)]
        for row in range(rows)
    ]


def split_strip(path: Path) -> list[Image.Image]:
    image = remove_green_fringe(Image.open(path).convert("RGBA"))
    width, height = image.size
    xs = [round(index * width / 4) for index in range(5)]
    return [image.crop((xs[index], 0, xs[index + 1], height)) for index in range(4)]


def remove_green_fringe(image: Image.Image) -> Image.Image:
    """Remove residual generated chroma pixels before nearest-neighbor scaling."""
    output = image.copy()
    pixels = output.load()
    for y in range(output.height):
        for x in range(output.width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                continue
            if green > 70 and green > red + 22 and green > blue + 22:
                pixels[x, y] = (0, 0, 0, 0)
            elif green > max(red, blue) + 8:
                pixels[x, y] = (red, max(red, blue) + 8, blue, alpha)
    return output


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise RuntimeError("Empty generated gait frame")
    return bbox


def alpha_centroid_x(image: Image.Image, y0: int, y1: int) -> float:
    alpha = image.getchannel("A")
    points = [x for y in range(max(0, y0), min(image.height, y1)) for x in range(image.width) if alpha.getpixel((x, y)) >= 128]
    if not points:
        raise RuntimeError("Unable to locate head centroid")
    return sum(points) / len(points)


def original_head_x(frames: list[Image.Image]) -> float:
    values = []
    for frame in frames:
        bbox = alpha_bbox(frame)
        values.append(alpha_centroid_x(frame, bbox[1], min(bbox[1] + 30, bbox[3])))
    return statistics.median(values)


def normalize_generated(source: Image.Image, target_height: int, target_head_x: float) -> Image.Image:
    bbox = alpha_bbox(source)
    subject = source.crop(bbox)
    scale = target_height / subject.height
    scaled = subject.resize((max(1, round(subject.width * scale)), target_height), Image.Resampling.NEAREST)
    head_x = alpha_centroid_x(scaled, 0, min(30, scaled.height))
    x = round(target_head_x - head_x)
    y = FOOT_Y + 1 - target_height
    output = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    output.alpha_composite(scaled, (x, y))
    return output


def preserve_original_upper(generated: Image.Image, original: Image.Image) -> Image.Image:
    output = generated.copy()
    # The generated art is used only as the lower-body motion source. Keeping
    # the original pixels above the pelvis prevents identity/scale flicker and
    # keeps the v3 arm sockets aligned with the torso.
    output.paste((0, 0, 0, 0), (0, 0, CELL, CUT_Y))
    output.alpha_composite(original.crop((0, 0, CELL, CUT_Y)), (0, 0))
    return output


def hard_alpha(image: Image.Image) -> Image.Image:
    output = image.convert("RGBA")
    alpha = output.getchannel("A").point(lambda value: 255 if value >= 128 else 0)
    output.putalpha(alpha)
    return output


def make_loop_gif(frames: list[Image.Image], direction_name: str) -> str:
    rendered = []
    for frame in frames:
        canvas = Image.new("RGBA", (CELL, CELL), (8, 14, 18, 255))
        draw = ImageDraw.Draw(canvas)
        for line in range(0, CELL, 8):
            draw.line((line, 0, line, CELL), fill=(20, 36, 40, 255))
            draw.line((0, line, CELL, line), fill=(20, 36, 40, 255))
        draw.ellipse((40, 111, 88, 121), fill=(3, 7, 9, 175))
        canvas.alpha_composite(frame)
        rendered.append(canvas.resize((CELL * 4, CELL * 4), Image.Resampling.NEAREST))
    path = QA_ROOT / f"luna_run_loop_{direction_name.lower()}_v4.gif"
    rendered[0].save(path, save_all=True, append_images=rendered[1:], duration=[115] * 4, loop=0, disposal=2, optimize=False)
    return str(path)


def build() -> tuple[Image.Image, dict[str, object]]:
    QA_ROOT.mkdir(parents=True, exist_ok=True)
    source_atlas = Image.open(SOURCE_BODY).convert("RGBA")
    source_frames = crop_grid(source_atlas, 4, 8)
    output_atlas = source_atlas.copy()
    report: dict[str, object] = {"directions": {}, "unchangedRows": list(DIRECTIONS[:5])}

    for direction, strip_path in REPLACEMENTS.items():
        generated_frames = split_strip(strip_path)
        original_frames = source_frames[direction]
        heights = [alpha_bbox(frame)[3] - alpha_bbox(frame)[1] for frame in original_frames]
        target_height = round(statistics.median(heights))
        target_head_x = original_head_x(original_frames)
        rebuilt = []
        contacts = []
        for phase, (generated, original) in enumerate(zip(generated_frames, original_frames)):
            normalized = normalize_generated(generated, target_height, target_head_x)
            frame = hard_alpha(preserve_original_upper(normalized, original))
            bbox = alpha_bbox(frame)
            if bbox[3] - 1 != FOOT_Y:
                raise AssertionError(f"{DIRECTIONS[direction]} phase {phase}: foot line is {bbox[3] - 1}")
            bottom_contact = sum(1 for x in range(CELL) if frame.getpixel((x, FOOT_Y))[3] == 255)
            if bottom_contact < 2:
                raise AssertionError(f"{DIRECTIONS[direction]} phase {phase}: no stable ground contact")
            contacts.append(bottom_contact)
            rebuilt.append(frame)
            output_atlas.paste((0, 0, 0, 0), (phase * CELL, direction * CELL, (phase + 1) * CELL, (direction + 1) * CELL))
            output_atlas.alpha_composite(frame, (phase * CELL, direction * CELL))

        report["directions"][DIRECTIONS[direction]] = {
            "source": str(strip_path),
            "phaseOrder": ["LEFT_CONTACT", "RIGHT_PASS", "RIGHT_CONTACT", "LEFT_PASS"],
            "targetHeight": target_height,
            "upperBodyPreservedThroughY": CUT_Y - 1,
            "groundContactPixelCounts": contacts,
            "qa": make_loop_gif(rebuilt, DIRECTIONS[direction]),
        }

    # Rows not requested by the user are strict byte copies.
    rebuilt_grid = crop_grid(output_atlas, 4, 8)
    for direction in range(5):
        for phase in range(4):
            if rebuilt_grid[direction][phase].tobytes() != source_frames[direction][phase].tobytes():
                raise AssertionError(f"Unexpected edit in {DIRECTIONS[direction]} phase {phase}")

    output_path = COCOS_ROOT / OUTPUT_NAME
    output_atlas.save(output_path)
    output_atlas.save(QA_ROOT / OUTPUT_NAME)
    report.update({
        "version": "prototype-4-left-gait-redraw",
        "sourceBody": str(SOURCE_BODY),
        "outputBody": str(output_path),
        "cellSize": [CELL, CELL],
        "footLineY": FOOT_Y,
        "runtimeInputLogicChanged": False,
    })
    (COCOS_ROOT / SPEC_NAME).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (QA_ROOT / SPEC_NAME).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_atlas, report


def main() -> None:
    _, report = build()
    print(json.dumps({"output": report["outputBody"], "directions": report["directions"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
