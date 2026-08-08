from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
from statistics import median

if __name__ == "__main__":
    raise SystemExit(
        "REJECTED_BAD_CASE: rebuilding or reusing weilong-prototype-1 is forbidden; "
        "restart from a complete character and complete skeleton."
    )

from PIL import Image, ImageChops, ImageDraw


# REJECTED_BAD_CASE: retained only for forensic review. This builder used an
# upper-body identity lock combined with separately authored lower-body motion,
# which is permanently forbidden by ART_ASSET_GENERATION_STANDARD.md.
REBUILD_BLOCKED = True
REJECTION_STATUS = "REJECTED_BAD_CASE"
REJECTION_REASON = "upper-body identity lock combined with separately generated lower-body motion"


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent.parent
COCOS_ROOT = WORKSPACE / "combat_lab" / "assets" / "resources" / "weilong"
SOURCE_ROOT = ROOT / "generated_sources"
QA_ROOT = ROOT / "qa"

LUNA_ROOT = WORKSPACE / "combat_lab" / "assets" / "resources" / "luna"
LUNA_V3_BUILDER = WORKSPACE / "art_demos" / "luna_cocos_prototype" / "build_minimal_v3_revision.py"
LUNA_V2_BUILDER = WORKSPACE / "art_demos" / "luna_cocos_prototype" / "build_cocos_prototype_assets.py"
BASE_ATLAS = (
    WORKSPACE
    / "art_demos"
    / "character_batch_v1"
    / "body_core_v4_3d_ref"
    / "atlas"
    / "operator_weilong_lingxiao_3dref_elbow_core_8dir_128.png"
)
HIGH_PRECISION_3D_ROOT = WORKSPACE / "art_demos" / "weilong_3d_pipeline"
HIGH_PRECISION_MASTER = HIGH_PRECISION_3D_ROOT / "weilong_8dir_master_preview.png"
HIGH_PRECISION_DIRECTIONS = HIGH_PRECISION_3D_ROOT / "turnaround_master"
HIGH_PRECISION_TURNAROUND_BLEND = HIGH_PRECISION_3D_ROOT / "weilong_turnaround_source_packed.blend"
HIGH_PRECISION_ACTION_BLEND = HIGH_PRECISION_3D_ROOT / "weilong_action_source_packed.blend"

CELL = 128
FOOT = (64, 116)
WALK_FPS = 12
DIRECTIONS = ("Down", "DownRight", "Right", "UpRight", "Up", "UpLeft", "Left", "DownLeft")
DIR_SLUGS = ("down", "down_right", "right", "up_right", "up", "up_left", "left", "down_left")
WALK_PHASES = ("CONTACT_A", "DOWN_A", "PASS_A", "UP_A", "CONTACT_B", "DOWN_B", "PASS_B", "UP_B")
ACTION_PHASES = ("AIM", "FIRE", "RECOVER")
RELOAD_PHASES = ("AIM", "GRAB_MAG", "PULL", "OUT", "PUSH", "INSERT", "REGRIP")
RELOAD_DATA = (
    ("AIM", 0, False),
    ("GRAB_MAG", 0, True),
    ("PULL", 5, True),
    ("OUT", 11, True),
    ("PUSH", 5, True),
    ("INSERT", 0, True),
    ("REGRIP", 0, False),
)

BOB_Y = (0, 1, 0, -1, 0, 1, 0, -1)
CLEAR_GENERATED_ABOVE_Y = 75
ORIGINAL_UPPER_CROP_Y = 86

VERSION = "weilong-prototype-1-eight-direction-eight-frame-run-rifle"

NAMES = {
    "body": "weilong_body_run_8dir_8f_v1.png",
    "weaponBack": "weilong_rifle_weapon_back_8dir_3phase_v1.png",
    "weaponFront": "weilong_rifle_weapon_front_8dir_3phase_v1.png",
    "trigger": "weilong_rifle_trigger_arm_hand_8dir_8walk_3phase_v1.png",
    "support": "weilong_rifle_support_arm_hand_8dir_8walk_3phase_v1.png",
    "magazine": "weilong_rifle_magazine_8dir_3phase_v1.png",
    "muzzle": "weilong_rifle_muzzle_8dir_3phase_v1.png",
    "reloadWeaponBack": "weilong_rifle_weapon_back_reload_8dir_7f_v1.png",
    "reloadWeaponFront": "weilong_rifle_weapon_front_reload_8dir_7f_v1.png",
    "reloadTrigger": "weilong_rifle_reload_trigger_8dir_7f_v1.png",
    "reloadSupport": "weilong_rifle_reload_support_8dir_7f_v1.png",
    "reloadMagazine": "weilong_rifle_reload_magazine_8dir_7f_v1.png",
    "spec": "weilong_run_rifle_v1_spec.json",
}

# Screen-space elbow socket centres in the approved 128px base atlas. The body
# layer already contains shoulder, upper arm and elbow armour; independent arm
# layers begin here and contain only forearm, wrist and hand.
ELBOW_BASE = {
    "Down": {"trigger": (94, 71), "support": (47, 71)},
    "DownRight": {"trigger": (94, 71), "support": (49, 72)},
    "Right": {"trigger": (65, 74), "support": (51, 73)},
    "UpRight": {"trigger": (79, 73), "support": (31, 73)},
    "Up": {"trigger": (95, 72), "support": (47, 72)},
    "UpLeft": {"trigger": (47, 72), "support": (95, 72)},
    "Left": {"trigger": (62, 74), "support": (72, 73)},
    "DownLeft": {"trigger": (48, 70), "support": (95, 71)},
}

SHOULDER_BASE = {
    "Down": {"trigger": (85, 56), "support": (55, 56)},
    "DownRight": {"trigger": (86, 57), "support": (57, 57)},
    "Right": {"trigger": (64, 58), "support": (56, 59)},
    "UpRight": {"trigger": (74, 57), "support": (39, 57)},
    "Up": {"trigger": (86, 56), "support": (56, 56)},
    "UpLeft": {"trigger": (56, 56), "support": (87, 57)},
    "Left": {"trigger": (64, 58), "support": (70, 59)},
    "DownLeft": {"trigger": (57, 56), "support": (87, 56)},
}

COLORS = {
    "outline": (6, 8, 10, 255),
    "sleeve": (72, 75, 80, 255),
    "sleeve_light": (166, 169, 171, 255),
    "cuff": (109, 43, 37, 255),
    "glove": (34, 36, 40, 255),
    "glove_light": (112, 116, 121, 255),
    "accent": (214, 82, 48, 255),
}

EXTRA_PALETTE_COLORS = (
    COLORS["outline"][:3],
    COLORS["sleeve"][:3],
    COLORS["sleeve_light"][:3],
    COLORS["cuff"][:3],
    COLORS["glove"][:3],
    COLORS["accent"][:3],
    (255, 134, 28),
    (255, 249, 181),
)

_LIMITED_PALETTE: Image.Image | None = None


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


luna_v3 = load_module(LUNA_V3_BUILDER, "luna_v3_for_weilong")
luna_v2 = load_module(LUNA_V2_BUILDER, "luna_v2_for_weilong")
rig = luna_v2.rig


def transparent() -> Image.Image:
    return Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))


def hard_alpha(image: Image.Image) -> Image.Image:
    output = image.convert("RGBA")
    output.putalpha(output.getchannel("A").point(lambda value: 255 if value >= 128 else 0))
    return output


def limited_palette() -> Image.Image:
    global _LIMITED_PALETTE
    if _LIMITED_PALETTE is not None:
        return _LIMITED_PALETTE
    base = Image.open(BASE_ATLAS).convert("RGBA")
    opaque = [(red, green, blue) for red, green, blue, alpha in base.getdata() if alpha >= 128]
    sample = Image.new("RGB", (len(opaque) + len(EXTRA_PALETTE_COLORS) * 96, 1))
    sample.putdata(opaque + list(EXTRA_PALETTE_COLORS) * 96)
    quantized = sample.quantize(colors=32, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    raw_palette = quantized.getpalette()
    used_indices = sorted(index for _, index in quantized.getcolors() or [])
    colors = [tuple(raw_palette[index * 3:index * 3 + 3]) for index in used_indices]
    for color in EXTRA_PALETTE_COLORS:
        if color not in colors:
            colors.append(color)
    colors = colors[:32]
    palette_bytes = [component for color in colors for component in color]
    palette_bytes.extend([0] * (768 - len(palette_bytes)))
    palette = Image.new("P", (1, 1))
    palette.putpalette(palette_bytes)
    _LIMITED_PALETTE = palette
    return palette


def apply_limited_palette(image: Image.Image) -> Image.Image:
    source = hard_alpha(image)
    alpha = source.getchannel("A")
    reduced = source.convert("RGB").quantize(
        palette=limited_palette(),
        dither=Image.Dither.NONE,
    ).convert("RGBA")
    reduced.putalpha(alpha)
    return hard_alpha(reduced)


def scrub_green(image: Image.Image) -> Image.Image:
    output = image.convert("RGBA")
    pixels = output.load()
    for y in range(output.height):
        for x in range(output.width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                continue
            if green > 72 and green > red + 22 and green > blue + 22:
                pixels[x, y] = (0, 0, 0, 0)
            elif green > max(red, blue) + 8:
                pixels[x, y] = (red, max(red, blue) + 8, blue, alpha)
    return hard_alpha(output)


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise RuntimeError("Empty frame")
    return bbox


def split_4x2(path: Path) -> list[Image.Image]:
    image = scrub_green(Image.open(path))
    width, height = image.size
    xs = [round(index * width / 4) for index in range(5)]
    ys = [round(index * height / 2) for index in range(3)]
    return [
        image.crop((xs[column], ys[row], xs[column + 1], ys[row + 1]))
        for row in range(2)
        for column in range(4)
    ]


def crop_grid(image: Image.Image, columns: int, rows: int) -> list[list[Image.Image]]:
    expected = (columns * CELL, rows * CELL)
    if image.size != expected:
        raise RuntimeError(f"Unexpected atlas size {image.size}, expected {expected}")
    return [
        [image.crop((column * CELL, row * CELL, (column + 1) * CELL, (row + 1) * CELL)) for column in range(columns)]
        for row in range(rows)
    ]


def centroid_x(image: Image.Image, y0: int, y1: int) -> float:
    alpha = image.getchannel("A")
    points = [
        x
        for y in range(max(0, y0), min(image.height, y1))
        for x in range(image.width)
        if alpha.getpixel((x, y)) == 255
    ]
    if not points:
        bbox = alpha_bbox(image)
        return (bbox[0] + bbox[2] - 1) / 2
    return sum(points) / len(points)


def save_asset(image: Image.Image, name: str) -> None:
    COCOS_ROOT.mkdir(parents=True, exist_ok=True)
    QA_ROOT.mkdir(parents=True, exist_ok=True)
    image = apply_limited_palette(image)
    image.save(COCOS_ROOT / name)
    image.save(QA_ROOT / name)


def normalize_generated(source: Image.Image, scale: float, target_head_x: float) -> Image.Image:
    subject = source.crop(alpha_bbox(source))
    scaled = subject.resize(
        (max(1, round(subject.width * scale)), max(1, round(subject.height * scale))),
        Image.Resampling.NEAREST,
    )
    head_band = max(10, min(32, round(scaled.height * 0.32)))
    source_head_x = centroid_x(scaled, 0, head_band)
    x = round(target_head_x - source_head_x)
    y = FOOT[1] + 1 - scaled.height
    output = transparent()
    output.alpha_composite(scaled, (x, y))
    return output


def compose_identity_locked_frame(generated: Image.Image, upper_source: Image.Image, bob_y: int) -> Image.Image:
    output = generated.copy()
    output.paste((0, 0, 0, 0), (0, 0, CELL, CLEAR_GENERATED_ABOVE_Y))
    upper = transparent()
    upper.alpha_composite(upper_source.crop((0, 0, CELL, ORIGINAL_UPPER_CROP_Y)), (0, bob_y))
    output.alpha_composite(upper)
    return hard_alpha(output)


def build_body() -> tuple[list[list[Image.Image]], dict[str, object]]:
    base_grid = crop_grid(Image.open(BASE_ATLAS).convert("RGBA"), 4, 2)
    base_frames = [base_grid[row][column] for row in range(2) for column in range(4)]
    sources = [split_4x2(SOURCE_ROOT / f"weilong_run_{slug}_8f_alpha.png") for slug in DIR_SLUGS]
    source_heights = [alpha_bbox(frame)[3] - alpha_bbox(frame)[1] for direction in sources for frame in direction]
    target_height = median(alpha_bbox(frame)[3] - alpha_bbox(frame)[1] for frame in base_frames)
    uniform_scale = target_height / median(source_heights)

    atlas = Image.new("RGBA", (CELL * 8, CELL * 8), (0, 0, 0, 0))
    body_frames: list[list[Image.Image]] = []
    report: dict[str, object] = {}

    for direction, direction_name in enumerate(DIRECTIONS):
        base = base_frames[direction]
        base_bbox = alpha_bbox(base)
        target_head_x = centroid_x(base, base_bbox[1], min(base_bbox[1] + 30, base_bbox[3]))
        row: list[Image.Image] = []
        hashes: list[str] = []
        frame_metrics = []
        for walk_frame, source in enumerate(sources[direction]):
            normalized = normalize_generated(source, uniform_scale, target_head_x)
            frame = apply_limited_palette(compose_identity_locked_frame(normalized, base, BOB_Y[walk_frame]))
            bbox = alpha_bbox(frame)
            if bbox[3] - 1 != FOOT[1]:
                raise AssertionError(f"{direction_name} {WALK_PHASES[walk_frame]} footY={bbox[3] - 1}")
            digest = hashlib.sha256(frame.tobytes()).hexdigest()
            hashes.append(digest)
            row.append(frame)
            atlas.alpha_composite(frame, (walk_frame * CELL, direction * CELL))
            frame_metrics.append({
                "phase": WALK_PHASES[walk_frame],
                "bbox": list(bbox),
                "lastOpaqueY": bbox[3] - 1,
                "hash": digest,
            })
        if len(set(hashes)) != 8:
            raise AssertionError(f"{direction_name} does not have 8 unique frames")
        body_frames.append(row)
        report[direction_name] = {
            "source": str(SOURCE_ROOT / f"weilong_run_{DIR_SLUGS[direction]}_8f_alpha.png"),
            "uniqueFrames": len(set(hashes)),
            "identityUpper": str(BASE_ATLAS),
            "frames": frame_metrics,
        }

    save_asset(atlas, NAMES["body"])
    report["uniformNearestScale"] = round(uniform_scale, 8)
    report["targetMedianVisualHeight"] = target_height
    report["upperIdentityLock"] = {
        "clearGeneratedAboveY": CLEAR_GENERATED_ABOVE_Y,
        "approvedUpperCropY": ORIGINAL_UPPER_CROP_Y,
        "bobY": list(BOB_Y),
    }
    return body_frames, report


def recolor_rifle(image: Image.Image) -> Image.Image:
    output = image.convert("RGBA")
    pixels = output.load()
    for y in range(output.height):
        for x in range(output.width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                continue
            if green > red + 18 and blue > red + 22 and max(green, blue) > 90:
                luminance = max(green, blue)
                pixels[x, y] = (
                    min(230, round(luminance * 1.08)),
                    min(125, round(luminance * 0.48)),
                    min(90, round(luminance * 0.32)),
                    alpha,
                )
    return hard_alpha(output)


def copy_rifle_layers() -> dict[str, list[list[Image.Image]]]:
    source_names = {
        "weaponBack": "luna_rifle_weapon_back_8dir_3phase_v3.png",
        "weaponFront": "luna_rifle_weapon_front_8dir_3phase_v3.png",
        "magazine": "luna_rifle_magazine_8dir_3phase_v3.png",
        "muzzle": "luna_rifle_muzzle_8dir_3phase_v3.png",
    }
    grids = {}
    for key, source_name in source_names.items():
        image = Image.open(LUNA_ROOT / source_name).convert("RGBA")
        if key != "muzzle":
            image = recolor_rifle(image)
        image = apply_limited_palette(image)
        save_asset(image, NAMES[key])
        grids[key] = crop_grid(image, 3, 8)
    return grids


def vector_polygon(center, along, normal, half_length: float, half_width: float):
    return [
        tuple(map(round, rig.add(rig.add(center, rig.mul(along, half_length)), rig.mul(normal, half_width)))),
        tuple(map(round, rig.add(rig.add(center, rig.mul(along, half_length)), rig.mul(normal, -half_width)))),
        tuple(map(round, rig.add(rig.add(center, rig.mul(along, -half_length)), rig.mul(normal, -half_width)))),
        tuple(map(round, rig.add(rig.add(center, rig.mul(along, -half_length)), rig.mul(normal, half_width)))),
    ]


def draw_forearm_hand(
    start: tuple[int, int],
    target: tuple[float, float],
    aim: tuple[float, float],
    bend_sign: int,
) -> Image.Image:
    layer = transparent()
    draw = ImageDraw.Draw(layer)
    normal = (-aim[1], aim[0])
    wrist = rig.add(target, rig.mul(aim, -3.0))
    midpoint = ((start[0] + wrist[0]) * 0.5, (start[1] + wrist[1]) * 0.5)
    bend = 4.0 if math.dist(start, wrist) < 24 else 5.0
    inner_elbow = rig.add(midpoint, rig.mul(normal, bend * bend_sign))
    points = [tuple(map(round, start)), tuple(map(round, inner_elbow)), tuple(map(round, wrist))]

    draw.line(points, fill=COLORS["outline"], width=8, joint="curve")
    draw.line(points, fill=COLORS["sleeve"], width=5, joint="curve")
    draw.line((points[0], points[1]), fill=COLORS["sleeve_light"], width=1)
    sx, sy = points[0]
    draw.ellipse((sx - 3, sy - 3, sx + 3, sy + 3), fill=COLORS["outline"])
    draw.ellipse((sx - 2, sy - 2, sx + 2, sy + 2), fill=COLORS["cuff"])

    draw.polygon(vector_polygon(target, aim, normal, 4.0, 4.0), fill=COLORS["outline"])
    draw.polygon(vector_polygon(target, aim, normal, 3.0, 2.5), fill=COLORS["glove"])
    finger_a = rig.add(target, rig.mul(normal, 2.0))
    finger_b = rig.add(target, rig.mul(normal, -2.0))
    draw.point(tuple(map(round, finger_a)), fill=COLORS["glove_light"])
    draw.point(tuple(map(round, finger_b)), fill=COLORS["glove_light"])
    return apply_limited_palette(layer)


def rifle_muzzle_point(direction: int, phase: int) -> tuple[float, float]:
    geometry = luna_v3.rifle_geometry(direction, phase)
    aim = geometry["aim"]
    width_factor = 0.48 + 0.52 * abs(aim[0])
    return rig.add(geometry["weaponShoulder"], rig.mul(aim, 44 * width_factor))


def build_rifle_arms(body_frames: list[list[Image.Image]]) -> tuple[dict[str, list[list[Image.Image]]], dict[str, object]]:
    columns = 24
    trigger_atlas = Image.new("RGBA", (columns * CELL, 8 * CELL), (0, 0, 0, 0))
    support_atlas = Image.new("RGBA", (columns * CELL, 8 * CELL), (0, 0, 0, 0))
    trigger_grid = [[transparent() for _ in range(columns)] for _ in range(8)]
    support_grid = [[transparent() for _ in range(columns)] for _ in range(8)]
    report: dict[str, object] = {}

    for direction, direction_name in enumerate(DIRECTIONS):
        walks = []
        for walk_frame in range(8):
            bob = BOB_Y[walk_frame]
            trigger_start = (ELBOW_BASE[direction_name]["trigger"][0], ELBOW_BASE[direction_name]["trigger"][1] + bob)
            support_start = (ELBOW_BASE[direction_name]["support"][0], ELBOW_BASE[direction_name]["support"][1] + bob)
            walk_item = {
                "walkFrame": walk_frame,
                "phase": WALK_PHASES[walk_frame],
                "triggerElbow": list(trigger_start),
                "supportElbow": list(support_start),
                "phases": [],
            }
            for phase, phase_name in enumerate(ACTION_PHASES):
                column = walk_frame * 3 + phase
                geometry = luna_v3.rifle_geometry(direction, phase)
                aim = geometry["aim"]
                facing_sign = 1 if aim[0] >= 0 else -1
                trigger = draw_forearm_hand(trigger_start, geometry["triggerGrip"], aim, facing_sign)
                support = draw_forearm_hand(support_start, geometry["supportGrip"], aim, -facing_sign)
                trigger_grid[direction][column] = trigger
                support_grid[direction][column] = support
                trigger_atlas.alpha_composite(trigger, (column * CELL, direction * CELL))
                support_atlas.alpha_composite(support, (column * CELL, direction * CELL))
                muzzle = rifle_muzzle_point(direction, phase)
                walk_item["phases"].append({
                    "actionPhase": phase_name,
                    "column": column,
                    "triggerGrip": [round(value, 2) for value in geometry["triggerGrip"]],
                    "supportGrip": [round(value, 2) for value in geometry["supportGrip"]],
                    "weaponShoulder": [round(value, 2) for value in geometry["weaponShoulder"]],
                    "muzzle": [round(value, 2) for value in muzzle],
                })
            walks.append(walk_item)
        report[direction_name] = walks

    save_asset(trigger_atlas, NAMES["trigger"])
    save_asset(support_atlas, NAMES["support"])
    return {"trigger": trigger_grid, "support": support_grid}, report


def reload_aim(direction: int) -> tuple[float, float]:
    if direction == 0:
        raw = (0.34, 0.94)
    elif direction == 4:
        raw = (0.34, -0.94)
    else:
        return rig.direction_vector(direction)
    length = math.hypot(*raw)
    return raw[0] / length, raw[1] / length


def reload_geometry(direction: int, detach: float, support_on_mag: bool) -> dict[str, tuple[float, float]]:
    aim = reload_aim(direction)
    side_factor = abs(aim[0])
    if direction == 0:
        weapon_shoulder = (72.0, 78.0)
    elif direction == 4:
        weapon_shoulder = (85.0, 77.0)
    else:
        weapon_shoulder = (69.0, 77.0) if side_factor < 0.25 else (64.0 + aim[0] * 2.0, 78.0)
    down = rig.normal_for_weapon(aim)
    trigger = rig.add(rig.add(weapon_shoulder, rig.mul(aim, 8)), rig.mul(down, 2))
    foregrip = rig.add(rig.add(weapon_shoulder, rig.mul(aim, 24)), rig.mul(down, 1))
    magwell = rig.add(rig.add(weapon_shoulder, rig.mul(aim, 16)), rig.mul(down, 3))
    _, mag_top = rig.magazine_layer(magwell, down, detach)
    support = rig.add(mag_top, rig.mul(down, 7)) if support_on_mag else foregrip
    return {
        "aim": aim,
        "weaponShoulder": weapon_shoulder,
        "triggerGrip": trigger,
        "supportGrip": support,
        "magwell": magwell,
    }


def build_reload() -> tuple[dict[str, list[list[Image.Image]]], dict[str, object]]:
    source_names = {
        "reloadWeaponBack": "luna_rifle_weapon_back_reload_8dir_7f_v2.png",
        "reloadWeaponFront": "luna_rifle_weapon_front_reload_8dir_7f_v2.png",
        "reloadMagazine": "luna_rifle_reload_magazine_8dir_7f.png",
    }
    grids: dict[str, list[list[Image.Image]]] = {}
    for key, source_name in source_names.items():
        image = apply_limited_palette(recolor_rifle(Image.open(LUNA_ROOT / source_name).convert("RGBA")))
        save_asset(image, NAMES[key])
        grids[key] = crop_grid(image, 7, 8)

    trigger_atlas = Image.new("RGBA", (7 * CELL, 8 * CELL), (0, 0, 0, 0))
    support_atlas = Image.new("RGBA", (7 * CELL, 8 * CELL), (0, 0, 0, 0))
    trigger_grid = [[transparent() for _ in range(7)] for _ in range(8)]
    support_grid = [[transparent() for _ in range(7)] for _ in range(8)]
    report: dict[str, object] = {}

    for direction, direction_name in enumerate(DIRECTIONS):
        phases = []
        trigger_start = ELBOW_BASE[direction_name]["trigger"]
        support_start = ELBOW_BASE[direction_name]["support"]
        for phase, (phase_name, detach, support_on_mag) in enumerate(RELOAD_DATA):
            geometry = reload_geometry(direction, detach, support_on_mag)
            aim = geometry["aim"]
            facing_sign = 1 if aim[0] >= 0 else -1
            trigger = draw_forearm_hand(trigger_start, geometry["triggerGrip"], aim, facing_sign)
            support = draw_forearm_hand(support_start, geometry["supportGrip"], aim, -facing_sign)
            trigger_grid[direction][phase] = trigger
            support_grid[direction][phase] = support
            trigger_atlas.alpha_composite(trigger, (phase * CELL, direction * CELL))
            support_atlas.alpha_composite(support, (phase * CELL, direction * CELL))
            phases.append({
                "phase": phase_name,
                "magazineDetachPx": detach,
                "triggerGrip": [round(value, 2) for value in geometry["triggerGrip"]],
                "supportGrip": [round(value, 2) for value in geometry["supportGrip"]],
                "magwell": [round(value, 2) for value in geometry["magwell"]],
            })
        report[direction_name] = phases

    save_asset(trigger_atlas, NAMES["reloadTrigger"])
    save_asset(support_atlas, NAMES["reloadSupport"])
    grids["reloadTrigger"] = trigger_grid
    grids["reloadSupport"] = support_grid
    return grids, report


def compose_rifle(
    body: Image.Image,
    direction: int,
    walk_frame: int,
    phase: int,
    gun: dict[str, list[list[Image.Image]]],
    arms: dict[str, list[list[Image.Image]]],
) -> Image.Image:
    column = walk_frame * 3 + phase
    output = transparent()
    if direction in (3, 4, 5):
        layers = (
            gun["weaponBack"][direction][phase],
            gun["weaponFront"][direction][phase],
            gun["magazine"][direction][phase],
            arms["support"][direction][column],
            body,
            arms["trigger"][direction][column],
            gun["muzzle"][direction][phase],
        )
    else:
        layers = (
            gun["weaponBack"][direction][phase],
            body,
            arms["trigger"][direction][column],
            arms["support"][direction][column],
            gun["weaponFront"][direction][phase],
            gun["magazine"][direction][phase],
            gun["muzzle"][direction][phase],
        )
    for layer in layers:
        output.alpha_composite(layer)
    return hard_alpha(output)


def compose_reload(
    body: Image.Image,
    direction: int,
    phase: int,
    reload: dict[str, list[list[Image.Image]]],
) -> Image.Image:
    output = transparent()
    if direction in (3, 4, 5):
        layers = (
            reload["reloadWeaponBack"][direction][phase],
            reload["reloadWeaponFront"][direction][phase],
            reload["reloadMagazine"][direction][phase],
            reload["reloadSupport"][direction][phase],
            body,
            reload["reloadTrigger"][direction][phase],
        )
    else:
        layers = (
            reload["reloadWeaponBack"][direction][phase],
            body,
            reload["reloadTrigger"][direction][phase],
            reload["reloadSupport"][direction][phase],
            reload["reloadWeaponFront"][direction][phase],
            reload["reloadMagazine"][direction][phase],
        )
    for layer in layers:
        output.alpha_composite(layer)
    return hard_alpha(output)


def qa_canvas(frame: Image.Image, scale: int = 4) -> Image.Image:
    canvas = Image.new("RGBA", (CELL, CELL), (8, 14, 18, 255))
    draw = ImageDraw.Draw(canvas)
    for y in range(0, CELL, 8):
        for x in range(0, CELL, 8):
            fill = (13, 24, 28, 255) if (x // 8 + y // 8) % 2 == 0 else (10, 19, 23, 255)
            draw.rectangle((x, y, x + 7, y + 7), fill=fill)
    draw.line((0, FOOT[1], CELL - 1, FOOT[1]), fill=(50, 116, 112, 255), width=1)
    draw.ellipse((40, 111, 88, 121), fill=(3, 7, 9, 175))
    canvas.alpha_composite(frame)
    return canvas.resize((CELL * scale, CELL * scale), Image.Resampling.NEAREST)


def make_qa(
    body_frames: list[list[Image.Image]],
    gun: dict[str, list[list[Image.Image]]],
    arms: dict[str, list[list[Image.Image]]],
    reload: dict[str, list[list[Image.Image]]],
) -> list[str]:
    QA_ROOT.mkdir(parents=True, exist_ok=True)
    outputs = []
    for direction, slug in enumerate(DIR_SLUGS):
        frames = [qa_canvas(body_frames[direction][walk_frame]) for walk_frame in range(8)]
        path = QA_ROOT / f"weilong_run_loop_{direction + 1}_{slug}_8f_v1.gif"
        frames[0].save(path, save_all=True, append_images=frames[1:], duration=[83] * 8, loop=0, disposal=2, optimize=False)
        outputs.append(str(path))

    action_by_walk = (0, 0, 1, 2, 0, 1, 2, 0)
    overview_frames = []
    for walk_frame in range(8):
        sheet = Image.new("RGBA", (CELL * 4, CELL * 2), (8, 14, 18, 255))
        for direction in range(8):
            phase = action_by_walk[walk_frame]
            combined = compose_rifle(body_frames[direction][walk_frame], direction, walk_frame, phase, gun, arms)
            cell = qa_canvas(combined, 1)
            sheet.alpha_composite(cell, ((direction % 4) * CELL, (direction // 4) * CELL))
        overview_frames.append(sheet.resize((CELL * 8, CELL * 4), Image.Resampling.NEAREST))
    overview_path = QA_ROOT / "weilong_run_rifle_fire_overview_v1.gif"
    overview_frames[0].save(
        overview_path,
        save_all=True,
        append_images=overview_frames[1:],
        duration=[83] * 8,
        loop=0,
        disposal=2,
        optimize=False,
    )
    outputs.append(str(overview_path))

    reload_frames = []
    for phase in range(7):
        sheet = Image.new("RGBA", (CELL * 4, CELL * 2), (8, 14, 18, 255))
        for direction in range(8):
            combined = compose_reload(body_frames[direction][phase % 8], direction, phase, reload)
            sheet.alpha_composite(qa_canvas(combined, 1), ((direction % 4) * CELL, (direction // 4) * CELL))
        reload_frames.append(sheet.resize((CELL * 8, CELL * 4), Image.Resampling.NEAREST))
    reload_path = QA_ROOT / "weilong_reload_all_8dir_7f_v1.gif"
    reload_frames[0].save(
        reload_path,
        save_all=True,
        append_images=reload_frames[1:],
        duration=[130] * 7,
        loop=0,
        disposal=2,
        optimize=False,
    )
    outputs.append(str(reload_path))

    identity_audit = Image.new("RGBA", (CELL * 8, CELL * 2), (8, 14, 18, 255))
    for direction, slug in enumerate(DIR_SLUGS):
        master = Image.open(HIGH_PRECISION_DIRECTIONS / f"weilong_{slug}.png").convert("RGBA")
        master_bbox = alpha_bbox(master)
        subject = master.crop(master_bbox)
        scale = 106 / max(subject.width, subject.height)
        subject = subject.resize(
            (max(1, round(subject.width * scale)), max(1, round(subject.height * scale))),
            Image.Resampling.LANCZOS,
        )
        master_cell = Image.new("RGBA", (CELL, CELL), (8, 14, 18, 255))
        master_cell.alpha_composite(subject, ((CELL - subject.width) // 2, FOOT[1] + 1 - subject.height))
        identity_audit.alpha_composite(master_cell, (direction * CELL, 0))
        identity_audit.alpha_composite(qa_canvas(body_frames[direction][0], 1), (direction * CELL, CELL))
    audit_path = QA_ROOT / "weilong_identity_3d_vs_pixel_audit_v1.png"
    identity_audit.save(audit_path)
    outputs.append(str(audit_path))
    return outputs


def count_diff(a: Image.Image, b: Image.Image) -> int:
    difference = ImageChops.difference(a.convert("RGBA"), b.convert("RGBA"))
    return sum(1 for pixel in difference.getdata() if pixel != (0, 0, 0, 0))


def green_like_count(image: Image.Image) -> int:
    return sum(
        1
        for red, green, blue, alpha in image.convert("RGBA").getdata()
        if alpha == 255 and green > 90 and green > red + 28 and green > blue + 28
    )


def validate(body_frames: list[list[Image.Image]]) -> dict[str, object]:
    expected = {
        NAMES["body"]: (1024, 1024),
        NAMES["weaponBack"]: (384, 1024),
        NAMES["weaponFront"]: (384, 1024),
        NAMES["trigger"]: (3072, 1024),
        NAMES["support"]: (3072, 1024),
        NAMES["magazine"]: (384, 1024),
        NAMES["muzzle"]: (384, 1024),
        NAMES["reloadWeaponBack"]: (896, 1024),
        NAMES["reloadWeaponFront"]: (896, 1024),
        NAMES["reloadTrigger"]: (896, 1024),
        NAMES["reloadSupport"]: (896, 1024),
        NAMES["reloadMagazine"]: (896, 1024),
    }
    asset_report = {}
    for name, size in expected.items():
        path = COCOS_ROOT / name
        image = Image.open(path).convert("RGBA")
        if image.size != size:
            raise AssertionError(f"{name}: {image.size} != {size}")
        alpha_values = set(image.getchannel("A").getdata())
        if not alpha_values.issubset({0, 255}):
            raise AssertionError(f"{name}: non-hard alpha")
        green = green_like_count(image)
        if green:
            raise AssertionError(f"{name}: {green} green-like opaque pixels")
        opaque_colors = {
            (red, green, blue)
            for red, green, blue, alpha in image.getdata()
            if alpha == 255
        }
        if len(opaque_colors) > 32:
            raise AssertionError(f"{name}: {len(opaque_colors)} opaque colors > 32")
        asset_report[name] = {
            "size": list(size),
            "hardAlpha": True,
            "greenLikeOpaquePixels": green,
            "opaqueColorCount": len(opaque_colors),
            "fixedPaletteLimit": 32,
        }

    direction_report = {}
    for direction, direction_name in enumerate(DIRECTIONS):
        frames = body_frames[direction]
        hashes = [hashlib.sha256(frame.tobytes()).hexdigest() for frame in frames]
        if len(set(hashes)) != 8:
            raise AssertionError(f"{direction_name}: uniqueFrames != 8")
        foot_lines = [alpha_bbox(frame)[3] - 1 for frame in frames]
        if set(foot_lines) != {FOOT[1]}:
            raise AssertionError(f"{direction_name}: foot lines {foot_lines}")
        adjacent = [count_diff(frames[index], frames[(index + 1) % 8]) for index in range(8)]
        closure = adjacent[-1]
        internal = adjacent[:-1]
        closure_limit = max(internal) * 1.35
        if closure > closure_limit:
            raise AssertionError(f"{direction_name}: closure {closure} > {closure_limit:.1f}")
        upper_hashes = []
        for walk_frame, frame in enumerate(frames):
            normalized = transparent()
            normalized.alpha_composite(frame, (0, -BOB_Y[walk_frame]))
            upper_hashes.append(hashlib.sha256(normalized.crop((0, 0, CELL, CLEAR_GENERATED_ABOVE_Y - 1)).tobytes()).hexdigest())
        if len(set(upper_hashes)) != 1:
            raise AssertionError(f"{direction_name}: upper identity changed across walk frames")
        direction_report[direction_name] = {
            "uniqueFrames": 8,
            "footLastOpaqueY": foot_lines,
            "adjacentChangedPixels": adjacent,
            "frame7To0ChangedPixels": closure,
            "closureLimit": round(closure_limit, 2),
            "closedLoop": True,
            "upperIdentityStableAfterBobNormalization": True,
        }

    return {
        "assetSizes": asset_report,
        "directions": direction_report,
        "hardAlpha": True,
        "noGreenFringe": True,
        "footAnchorVerified": list(FOOT),
    }


def atlas_specs() -> dict[str, object]:
    return {
        "bodyRun": {"file": NAMES["body"], "columns": 8, "rows": 8, "size": [1024, 1024]},
        "rifleWeaponBack": {"file": NAMES["weaponBack"], "columns": 3, "rows": 8, "size": [384, 1024]},
        "rifleWeaponFront": {"file": NAMES["weaponFront"], "columns": 3, "rows": 8, "size": [384, 1024]},
        "rifleTriggerArmHand": {"file": NAMES["trigger"], "columns": 24, "rows": 8, "size": [3072, 1024]},
        "rifleSupportArmHand": {"file": NAMES["support"], "columns": 24, "rows": 8, "size": [3072, 1024]},
        "rifleMagazine": {"file": NAMES["magazine"], "columns": 3, "rows": 8, "size": [384, 1024]},
        "rifleMuzzle": {"file": NAMES["muzzle"], "columns": 3, "rows": 8, "size": [384, 1024]},
        "reloadWeaponBack": {"file": NAMES["reloadWeaponBack"], "columns": 7, "rows": 8, "size": [896, 1024]},
        "reloadWeaponFront": {"file": NAMES["reloadWeaponFront"], "columns": 7, "rows": 8, "size": [896, 1024]},
        "reloadTrigger": {"file": NAMES["reloadTrigger"], "columns": 7, "rows": 8, "size": [896, 1024]},
        "reloadSupport": {"file": NAMES["reloadSupport"], "columns": 7, "rows": 8, "size": [896, 1024]},
        "reloadMagazine": {"file": NAMES["reloadMagazine"], "columns": 7, "rows": 8, "size": [896, 1024]},
    }


def main() -> None:
    if REBUILD_BLOCKED:
        raise RuntimeError(
            "REJECTED_BAD_CASE: rebuilding or reusing weilong-prototype-1 is forbidden; "
            "restart from a complete character and complete skeleton."
        )

    COCOS_ROOT.mkdir(parents=True, exist_ok=True)
    QA_ROOT.mkdir(parents=True, exist_ok=True)
    body_frames, body_report = build_body()
    gun = copy_rifle_layers()
    arms, arm_report = build_rifle_arms(body_frames)
    reload, reload_report = build_reload()
    qa_files = make_qa(body_frames, gun, arms, reload)
    validation = validate(body_frames)

    anchors = {}
    for direction_name in DIRECTIONS:
        anchors[direction_name] = {
            "triggerShoulder": list(SHOULDER_BASE[direction_name]["trigger"]),
            "supportShoulder": list(SHOULDER_BASE[direction_name]["support"]),
            "triggerElbow": list(ELBOW_BASE[direction_name]["trigger"]),
            "supportElbow": list(ELBOW_BASE[direction_name]["support"]),
            "rifleByWalkFrame": arm_report[direction_name],
            "reloadPhases": reload_report[direction_name],
        }

    payload = {
        "version": VERSION,
        "assetStatus": REJECTION_STATUS,
        "rejectionReason": REJECTION_REASON,
        "allowedUse": ["forensic_bad_case_review_only"],
        "forbiddenAsGenerationInput": True,
        "scope": "威龙·凌霄戍卫 Prototype 1 action art; no Luna files modified",
        "identityReferences": [
            str(HIGH_PRECISION_MASTER),
            str(HIGH_PRECISION_DIRECTIONS),
            str(HIGH_PRECISION_TURNAROUND_BLEND),
            str(HIGH_PRECISION_ACTION_BLEND),
            str(WORKSPACE / "art_demos/reference_skins/3d_weilong_lingxiao/weilong_lingxiao_3d_8dir_reference.png"),
            str(WORKSPACE / "art_demos/reference_skins/3d_weilong_lingxiao/renders"),
            str(BASE_ATLAS),
        ],
        "excludedAsFormalPixelSource": [
            str(HIGH_PRECISION_3D_ROOT / "weilong_8dir_game_pixel_preview.png"),
            str(HIGH_PRECISION_3D_ROOT / "weilong_8dir_game_128_atlas.png"),
        ],
        "cellSize": [CELL, CELL],
        "footAnchor": list(FOOT),
        "directionOrder": list(DIRECTIONS),
        "phaseOrder": list(WALK_PHASES),
        "actionPhaseOrder": list(ACTION_PHASES),
        "reloadPhaseOrder": list(RELOAD_PHASES),
        "walkFps": WALK_FPS,
        "reloadSecondsPerFrame": 0.13,
        "atlases": atlas_specs(),
        "armColumnFormula": "walkFrame * 3 + actionPhase",
        "zOrder": {
            "frontFacing": ["weaponBack", "body", "triggerArmHand", "supportArmHand", "weaponFront", "magazine", "muzzle"],
            "rearFacing": ["weaponBack", "weaponFront", "magazine", "supportArmHand", "body", "triggerArmHand", "muzzle"],
            "rearDirectionIndices": [3, 4, 5],
        },
        "downDirection": {
            "logicalBallisticVectorAssetYDown": [0.0, 1.0],
            "artVectorAssetYDown": [0.6, 0.8],
            "artAngleFromVerticalDegrees": 36.87,
        },
        "anchors": anchors,
        "bodyBuild": body_report,
        "qaFiles": qa_files,
        "validation": validation,
        "status": {
            "bodyRun": REJECTION_STATUS,
            "rifleFireLayers": REJECTION_STATUS,
            "reloadLayers": REJECTION_STATUS,
            "cocosRuntimeBinding": "FORBIDDEN",
        },
        "pixelArtContract": {
            "style": "Luna Prototype 5 chibi pixel language",
            "palette": "one fixed <=32-color palette shared by all formal layers",
            "dither": False,
            "alpha": "hard 0/255",
            "scaling": "nearest-neighbor only",
            "threeLevelShadingIntent": True,
            "realisticDownsampleUsedAsFormalArt": False,
        },
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    (COCOS_ROOT / NAMES["spec"]).write_text(text, encoding="utf-8")
    (QA_ROOT / NAMES["spec"]).write_text(text, encoding="utf-8")
    (QA_ROOT / "weilong_run_rifle_v1_qa_report.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({
        "version": VERSION,
        "output": str(COCOS_ROOT),
        "spec": str(COCOS_ROOT / NAMES["spec"]),
        "qa": qa_files,
        "validation": validation,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
