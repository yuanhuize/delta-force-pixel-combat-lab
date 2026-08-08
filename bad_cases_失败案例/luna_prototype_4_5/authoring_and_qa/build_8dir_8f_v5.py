from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

if __name__ == "__main__":
    raise SystemExit(
        "REJECTED_BAD_CASE: Luna Prototype 5 composited an identity-locked "
        "upper body with separately generated lower-body motion. Rebuilding "
        "or reusing it is forbidden."
    )

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent.parent
COCOS_ROOT = WORKSPACE / "combat_lab" / "assets" / "resources" / "luna"
SOURCE_ROOT = ROOT / "v5_8frame_sources"
QA_ROOT = ROOT / "v5_8frame_qa"
V3_BUILDER = ROOT / "build_minimal_v3_revision.py"

CELL = 128
FOOT_Y = 116
CLEAR_GENERATED_ABOVE_Y = 80
ORIGINAL_UPPER_CROP_Y = 88
DIRECTIONS = ("Down", "DownRight", "Right", "UpRight", "Up", "UpLeft", "Left", "DownLeft")
PHASES = ("CONTACT_A", "DOWN_A", "PASS_A", "UP_A", "CONTACT_B", "DOWN_B", "PASS_B", "UP_B")
BOB_Y = (0, 1, 0, -1, 0, 1, 0, -1)

V4_BODY = COCOS_ROOT / "luna_body_run_8dir_4f_v4.png"
BODY_NAME = "luna_body_run_8dir_8f_v5.png"
TRIGGER_NAME = "luna_rifle_trigger_arm_hand_8dir_8walk_3phase_v5.png"
SUPPORT_NAME = "luna_rifle_support_arm_hand_8dir_8walk_3phase_v5.png"
SPEC_NAME = "luna_run_8dir_8f_v5_spec.json"

SOURCE_STRIPS = (
    SOURCE_ROOT / "down_8f_alpha.png",
    SOURCE_ROOT / "downright_8f_alpha.png",
    SOURCE_ROOT / "right_8f_alpha.png",
    SOURCE_ROOT / "upright_8f_alpha.png",
    SOURCE_ROOT / "up_8f_alpha.png",
    SOURCE_ROOT / "upleft_8f_alpha.png",
    SOURCE_ROOT / "left_8f_alpha.png",
    SOURCE_ROOT / "downleft_8f_alpha.png",
)


def load_v3_builder():
    spec = importlib.util.spec_from_file_location("luna_v3_builder", V3_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to import v3 builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v3 = load_v3_builder()


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise RuntimeError("Empty sprite frame")
    return bbox


def remove_green_fringe(image: Image.Image) -> Image.Image:
    output = image.convert("RGBA")
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


def split_4x2(path: Path) -> list[Image.Image]:
    image = remove_green_fringe(Image.open(path))
    width, height = image.size
    xs = [round(index * width / 4) for index in range(5)]
    ys = [round(index * height / 2) for index in range(3)]
    frames = []
    for row in range(2):
        for column in range(4):
            frames.append(image.crop((xs[column], ys[row], xs[column + 1], ys[row + 1])))
    return frames


def crop_atlas(image: Image.Image, columns: int, rows: int) -> list[list[Image.Image]]:
    if image.size != (columns * CELL, rows * CELL):
        raise RuntimeError(f"Unexpected atlas size: {image.size}")
    return [
        [image.crop((column * CELL, row * CELL, (column + 1) * CELL, (row + 1) * CELL)) for column in range(columns)]
        for row in range(rows)
    ]


def centroid_x(image: Image.Image, y0: int, y1: int) -> float:
    alpha = image.getchannel("A")
    points = [x for y in range(max(0, y0), min(image.height, y1)) for x in range(image.width) if alpha.getpixel((x, y)) >= 128]
    if not points:
        raise RuntimeError("Unable to measure sprite centroid")
    return sum(points) / len(points)


def normalize_generated(source: Image.Image, target_height: int, target_head_x: float) -> Image.Image:
    bbox = alpha_bbox(source)
    subject = source.crop(bbox)
    scale = target_height / subject.height
    scaled = subject.resize((max(1, round(subject.width * scale)), target_height), Image.Resampling.NEAREST)
    head_x = centroid_x(scaled, 0, min(32, scaled.height))
    x = round(target_head_x - head_x)
    y = FOOT_Y + 1 - target_height
    output = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    output.alpha_composite(scaled, (x, y))
    return output


def hard_alpha(image: Image.Image) -> Image.Image:
    output = image.convert("RGBA")
    output.putalpha(output.getchannel("A").point(lambda value: 255 if value >= 128 else 0))
    return output


def compose_identity_locked_frame(generated: Image.Image, upper_source: Image.Image, bob_y: int) -> Image.Image:
    output = generated.copy()
    output.paste((0, 0, 0, 0), (0, 0, CELL, CLEAR_GENERATED_ABOVE_Y))
    upper = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    upper.alpha_composite(upper_source.crop((0, 0, CELL, ORIGINAL_UPPER_CROP_Y)), (0, bob_y))
    output.alpha_composite(upper)
    return hard_alpha(output)


def build_body() -> tuple[list[list[Image.Image]], dict[str, object]]:
    source_v4 = Image.open(V4_BODY).convert("RGBA")
    v4_frames = crop_atlas(source_v4, 4, 8)
    atlas = Image.new("RGBA", (CELL * 8, CELL * 8), (0, 0, 0, 0))
    frames: list[list[Image.Image]] = []
    report: dict[str, object] = {}

    for direction, strip_path in enumerate(SOURCE_STRIPS):
        generated = split_4x2(strip_path)
        upper_source = v4_frames[direction][0]
        upper_bbox = alpha_bbox(upper_source)
        target_height = upper_bbox[3] - upper_bbox[1]
        target_head_x = centroid_x(upper_source, upper_bbox[1], min(upper_bbox[1] + 32, upper_bbox[3]))
        direction_frames = []
        contact_counts = []
        hashes = []
        for phase, source in enumerate(generated):
            normalized = normalize_generated(source, target_height, target_head_x)
            frame = compose_identity_locked_frame(normalized, upper_source, BOB_Y[phase])
            bbox = alpha_bbox(frame)
            if bbox[3] - 1 != FOOT_Y:
                raise AssertionError(f"{DIRECTIONS[direction]} {PHASES[phase]} foot line = {bbox[3] - 1}")
            contact_count = sum(1 for x in range(CELL) if frame.getpixel((x, FOOT_Y))[3] == 255)
            if contact_count < 2:
                raise AssertionError(f"{DIRECTIONS[direction]} {PHASES[phase]} has no ground contact")
            contact_counts.append(contact_count)
            hashes.append(hashlib.sha256(frame.tobytes()).hexdigest())
            direction_frames.append(frame)
            atlas.alpha_composite(frame, (phase * CELL, direction * CELL))
        if len(set(hashes)) != 8:
            raise AssertionError(f"{DIRECTIONS[direction]} contains duplicate frames")
        frames.append(direction_frames)
        report[DIRECTIONS[direction]] = {
            "source": str(strip_path),
            "targetHeight": target_height,
            "groundContactPixelCounts": contact_counts,
            "uniqueFrames": len(set(hashes)),
            "upperIdentitySource": f"v4 direction {direction} frame 0",
        }

    atlas.save(COCOS_ROOT / BODY_NAME)
    atlas.save(QA_ROOT / BODY_NAME)
    return frames, report


def build_arms(body_frames: list[list[Image.Image]]) -> tuple[dict[str, list[list[Image.Image]]], dict[str, object]]:
    columns = 8 * 3
    trigger_atlas = Image.new("RGBA", (CELL * columns, CELL * 8), (0, 0, 0, 0))
    support_atlas = Image.new("RGBA", (CELL * columns, CELL * 8), (0, 0, 0, 0))
    trigger_grid = [[Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0)) for _ in range(columns)] for _ in range(8)]
    support_grid = [[Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0)) for _ in range(columns)] for _ in range(8)]
    anchors: dict[str, object] = {}

    for direction, direction_name in enumerate(DIRECTIONS):
        direction_anchors = []
        for walk_frame in range(8):
            chest_x, chest_y = v3.opaque_centroid(body_frames[direction][walk_frame], 50, 78)
            offsets = v3.SHOULDER_OFFSETS[direction_name]
            trigger_start = (round(chest_x + offsets["trigger"][0]), round(chest_y + offsets["trigger"][1]))
            support_start = (round(chest_x + offsets["support"][0]), round(chest_y + offsets["support"][1]))
            for phase in range(3):
                column = walk_frame * 3 + phase
                geometry = v3.rifle_geometry(direction, phase)
                aim = geometry["aim"]
                facing_sign = 1 if aim[0] >= 0 else -1
                trigger = v3.draw_arm_hand(trigger_start, geometry["triggerGrip"], aim, facing_sign)
                support = v3.draw_arm_hand(support_start, geometry["supportGrip"], aim, -facing_sign)
                trigger_grid[direction][column] = trigger
                support_grid[direction][column] = support
                trigger_atlas.alpha_composite(trigger, (column * CELL, direction * CELL))
                support_atlas.alpha_composite(support, (column * CELL, direction * CELL))
            direction_anchors.append({"walkFrame": walk_frame, "triggerShoulder": list(trigger_start), "supportShoulder": list(support_start)})
        anchors[direction_name] = direction_anchors

    trigger_atlas.save(COCOS_ROOT / TRIGGER_NAME)
    support_atlas.save(COCOS_ROOT / SUPPORT_NAME)
    trigger_atlas.save(QA_ROOT / TRIGGER_NAME)
    support_atlas.save(QA_ROOT / SUPPORT_NAME)
    return {"trigger": trigger_grid, "support": support_grid}, {"columns": columns, "anchors": anchors}


def load_layer(name: str, columns: int) -> list[list[Image.Image]]:
    return crop_atlas(Image.open(COCOS_ROOT / name).convert("RGBA"), columns, 8)


def compose_rifle(body: Image.Image, direction: int, walk_frame: int, arms: dict[str, list[list[Image.Image]]]) -> Image.Image:
    phase = 0
    column = walk_frame * 3 + phase
    weapon_back = load_layer("luna_rifle_weapon_back_8dir_3phase_v3.png", 3)[direction][phase]
    weapon_front = load_layer("luna_rifle_weapon_front_8dir_3phase_v3.png", 3)[direction][phase]
    magazine = load_layer("luna_rifle_magazine_8dir_3phase_v3.png", 3)[direction][phase]
    output = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    if direction in (3, 4, 5):
        layers = (weapon_back, weapon_front, magazine, arms["support"][direction][column], body, arms["trigger"][direction][column])
    else:
        layers = (weapon_back, body, arms["trigger"][direction][column], arms["support"][direction][column], weapon_front, magazine)
    for layer in layers:
        output.alpha_composite(layer)
    return output


def render_cell(frame: Image.Image, scale: int = 3) -> Image.Image:
    canvas = Image.new("RGBA", (CELL, CELL), (8, 14, 18, 255))
    draw = ImageDraw.Draw(canvas)
    for line in range(0, CELL, 8):
        draw.line((line, 0, line, CELL), fill=(20, 36, 40, 255))
        draw.line((0, line, CELL, line), fill=(20, 36, 40, 255))
    draw.ellipse((40, 111, 88, 121), fill=(3, 7, 9, 175))
    canvas.alpha_composite(frame)
    return canvas.resize((CELL * scale, CELL * scale), Image.Resampling.NEAREST)


def make_qa(body_frames: list[list[Image.Image]], arms: dict[str, list[list[Image.Image]]]) -> list[str]:
    outputs = []
    for direction, direction_name in enumerate(DIRECTIONS):
        frames = [render_cell(compose_rifle(body_frames[direction][phase], direction, phase, arms), 4) for phase in range(8)]
        path = QA_ROOT / f"luna_run_loop_{direction + 1}_{direction_name.lower()}_8f_v5.gif"
        frames[0].save(path, save_all=True, append_images=frames[1:], duration=[83] * 8, loop=0, disposal=2, optimize=False)
        outputs.append(str(path))

    combined = []
    for phase in range(8):
        sheet = Image.new("RGBA", (CELL * 4, CELL * 2), (8, 14, 18, 255))
        for direction in range(8):
            frame = compose_rifle(body_frames[direction][phase], direction, phase, arms)
            sheet.alpha_composite(frame, ((direction % 4) * CELL, (direction // 4) * CELL))
        combined.append(sheet.resize((CELL * 8, CELL * 4), Image.Resampling.NEAREST))
    combined_path = QA_ROOT / "luna_run_all_8dir_8f_v5.gif"
    combined[0].save(combined_path, save_all=True, append_images=combined[1:], duration=[83] * 8, loop=0, disposal=2, optimize=False)
    outputs.append(str(combined_path))
    return outputs


def main() -> None:
    QA_ROOT.mkdir(parents=True, exist_ok=True)
    body_frames, body_report = build_body()
    arms, arm_report = build_arms(body_frames)
    qa_files = make_qa(body_frames, arms)
    report = {
        "version": "prototype-5-eight-direction-eight-frame-run",
        "directionOrder": list(DIRECTIONS),
        "phaseOrder": list(PHASES),
        "cellSize": [CELL, CELL],
        "bodyAtlas": {"file": BODY_NAME, "columns": 8, "rows": 8},
        "armAtlases": {"trigger": TRIGGER_NAME, "support": SUPPORT_NAME, "columns": 24, "rows": 8, "columnFormula": "walkFrame * 3 + actionPhase"},
        "footLineY": FOOT_Y,
        "walkFps": 12,
        "body": body_report,
        "arms": arm_report,
        "qa": qa_files,
        "runtimeInputLogicChanged": False,
    }
    (COCOS_ROOT / SPEC_NAME).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (QA_ROOT / SPEC_NAME).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"body": str(COCOS_ROOT / BODY_NAME), "qa": qa_files}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
