"""Production-oriented Weilong full-character 3D -> 2D pixel pipeline.

This rebuild intentionally uses the supplied full-body and AirCannon PSA tracks
instead of the rejected procedural A/B placeholder actions.  Body, face, jet,
watch and weapon are evaluated at one scene time and rendered by one camera.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector


ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = Path("/Users/yuanhuize/Downloads/三角洲项目文件/威龙_凌霄")
BODY_PSA = SOURCE_ROOT / "角色模型/人物动作/M_Dragon_Outers_1u_S_Show_06_Body.psa"
FACE_PSA = SOURCE_ROOT / "角色模型/人物动作/M_Dragon_Outers_1u_S_Show_06_Face_HD.psa"
GUN_PSA = SOURCE_ROOT / "角色模型/人物动作/M_Dragon_Outers_1u_S_Show_06_Gun.psa"

BODY = "M_Dragon_Outers_1u_S_Body_UI_HD"
FACE = "M_Dragon_Outers_1u_S_Face_UI_HD"
JET = "Assault_C302_JetSystem_Outers_1u_UI"
WATCH = "Watch_Dragon_Outers_1u_A_UI"
GUN = "Assault_C302_AirCannon_Outers_1u_UI_V1"

BODY_ACTION = "M_Dragon_Outers_1u_S_Show_06_Body"
FACE_ACTION = "M_Dragon_Outers_1u_S_Show_06_Face_HD"
GUN_ACTION = "M_Dragon_Outers_1u_S_Show_06_Gun"
PROBE_FRAMES = (1, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1147)


def cli() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("probe", "render-probe", "render-turntable", "render-motion", "render-stylecard", "render-run", "render-q-static"), default="probe")
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return p.parse_args(argv)


def import_psa(path: Path, target: bpy.types.Object) -> bpy.types.Action:
    before = set(bpy.data.actions)
    bpy.ops.object.select_all(action="DESELECT")
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    result = bpy.ops.psa.import_all(
        filepath=str(path),
        fps_source="SEQUENCE",
        should_use_fake_user=True,
        should_write_keyframes=True,
        should_write_metadata=True,
        should_write_scale_keys=True,
        should_overwrite=True,
        should_stash=False,
        translation_scale=1.0,
    )
    if "FINISHED" not in result:
        raise RuntimeError(f"PSA import failed: {path}: {result}")
    preferred = path.stem
    action = bpy.data.actions.get(preferred)
    if action is None:
        created = sorted(set(bpy.data.actions) - before)
        if not created:
            raise RuntimeError(f"PSA import created no Action: {path}")
        action = bpy.data.actions[created[-1]]
    target.animation_data_create()
    target.animation_data.action = action
    return action


def assign_action(target: bpy.types.Object, action: bpy.types.Action) -> None:
    target.animation_data_create()
    target.animation_data.action = action


def prepare_animation() -> tuple[bpy.types.Action, bpy.types.Action, bpy.types.Action]:
    body = bpy.data.objects[BODY]
    face = bpy.data.objects[FACE]
    jet = bpy.data.objects[JET]
    gun = bpy.data.objects[GUN]
    body_action = import_psa(BODY_PSA, body)
    face_action = import_psa(FACE_PSA, face)
    gun_action = import_psa(GUN_PSA, gun)
    # The face has a dedicated synchronized track.  The jet rig shares the
    # supplied Root/Hips/Spine naming and follows the same full-body Action time.
    assign_action(jet, body_action)
    # Source .blend lays the UI weapon beside the character for inspection. Its
    # PSA animates internal weapon bones while the full-body hand joint supplies
    # the weapon's world transform at exactly the same scene time.
    gun.location = (0.0, 0.0, 0.0)
    gun.rotation_euler = (0.0, 0.0, 0.0)
    gun.scale = (1.0, 1.0, 1.0)
    for constraint in list(gun.constraints):
        gun.constraints.remove(constraint)
    follow = gun.constraints.new("COPY_TRANSFORMS")
    follow.name = "WL2D_FollowRightHandWeaponJoint"
    follow.target = body
    follow.subtarget = "Weapon_RightHand_Joint"
    follow.target_space = "WORLD"
    follow.owner_space = "WORLD"

    # Preserve the supplied watch's rest registration and make it follow the
    # left forearm as one rigid accessory; never render it as a separate pose.
    watch = bpy.data.objects.get(WATCH)
    if watch is not None:
        world = watch.matrix_world.copy()
        watch.parent = body
        watch.parent_type = "BONE"
        watch.parent_bone = "LeftForeArm"
        watch.matrix_world = world
    return body_action, face_action, gun_action


def visible_contract() -> None:
    prefixes = (BODY, FACE, JET, WATCH, GUN, "WL2D_")
    for obj in bpy.data.objects:
        keep = obj.name.startswith(prefixes)
        obj.hide_render = not keep
        obj.hide_viewport = not keep


def evaluated_bbox() -> list[list[float]]:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    points: list[Vector] = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.hide_render:
            continue
        evaluated = obj.evaluated_get(depsgraph)
        for corner in evaluated.bound_box:
            points.append(evaluated.matrix_world @ Vector(corner))
    if not points:
        return [[0, 0, 0], [0, 0, 0]]
    return [
        [min(p[i] for p in points) for i in range(3)],
        [max(p[i] for p in points) for i in range(3)],
    ]


def bone_point(armature: bpy.types.Object, bone_name: str) -> list[float]:
    bone = armature.pose.bones.get(bone_name)
    if bone is None:
        return []
    p = armature.matrix_world @ bone.head
    return [round(v, 4) for v in p]


def scene_probe() -> dict:
    scene = bpy.context.scene
    body = bpy.data.objects[BODY]
    gun = bpy.data.objects[GUN]
    rows = []
    for frame in PROBE_FRAMES:
        scene.frame_set(frame)
        rows.append(
            {
                "frame": frame,
                "bbox": evaluated_bbox(),
                "rightHand": bone_point(body, "RightHand"),
                "leftHand": bone_point(body, "LeftHand"),
                "weaponRoot": bone_point(gun, "AirCannon"),
            }
        )
    return {"bodyAction": BODY_ACTION, "faceAction": FACE_ACTION, "gunAction": GUN_ACTION, "frames": rows}


def point_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_render() -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = True
    scene.render.filter_size = 0.01
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.8
    world = scene.world or bpy.data.worlds.new("WL2D_World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.035, 0.04, 0.055, 1.0)
    bg.inputs["Strength"].default_value = 0.85

    for obj in list(bpy.data.objects):
        if obj.name.startswith("WL2D_"):
            bpy.data.objects.remove(obj, do_unlink=True)

    target = Vector((0.0, 0.0, 92.0))
    cam_data = bpy.data.cameras.new("WL2D_Camera")
    cam = bpy.data.objects.new("WL2D_Camera", cam_data)
    scene.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 210.0
    cam.location = (0.0, -420.0, 250.0)
    point_at(cam, target)
    scene.camera = cam

    for name, loc, energy, color in (
        ("WL2D_Key", (-180, -240, 320), 3.8, (1.0, 0.92, 0.80)),
        ("WL2D_Fill", (190, -120, 210), 2.3, (0.55, 0.72, 1.0)),
        ("WL2D_Rim", (40, 220, 300), 3.2, (0.75, 0.87, 1.0)),
    ):
        data = bpy.data.lights.new(name, "SUN")
        data.energy = energy
        data.color = color
        light = bpy.data.objects.new(name, data)
        scene.collection.objects.link(light)
        light.location = loc
        point_at(light, target)


def render_probe() -> None:
    setup_render()
    out = ROOT / "probe_highres"
    out.mkdir(parents=True, exist_ok=True)
    for frame in PROBE_FRAMES:
        bpy.context.scene.frame_set(frame)
        bpy.context.scene.render.filepath = str(out / f"show06_f{frame:04d}.png")
        bpy.ops.render.render(write_still=True)
        print("WL2D_RENDER", frame, bpy.context.scene.render.filepath)


def render_turntable() -> None:
    setup_render()
    scene = bpy.context.scene
    scene.frame_set(700)
    root = bpy.data.objects.new("WL2D_Turntable", None)
    scene.collection.objects.link(root)
    for name in (BODY, FACE, JET):
        obj = bpy.data.objects[name]
        world = obj.matrix_world.copy()
        obj.parent = root
        obj.matrix_world = world
    out = ROOT / "aim_16dir_highres"
    out.mkdir(parents=True, exist_ok=True)
    for direction in range(16):
        root.rotation_euler[2] = math.radians(-direction * 22.5)
        scene.frame_set(700)
        scene.render.filepath = str(out / f"aim_d{direction:02d}.png")
        bpy.ops.render.render(write_still=True)
        print("WL2D_TURNTABLE", direction, scene.render.filepath)


def render_motion() -> None:
    setup_render()
    scene = bpy.context.scene
    out = ROOT / "aim_motion_highres"
    out.mkdir(parents=True, exist_ok=True)
    # Twelve equally spaced source samples from the supplied synchronized full-
    # character cinematic.  This is an animation proof, not yet the run cycle.
    frames = tuple(676 + i * 4 for i in range(12))
    for index, frame in enumerate(frames):
        scene.frame_set(frame)
        scene.render.filepath = str(out / f"aim_f{index:02d}_src{frame:04d}.png")
        bpy.ops.render.render(write_still=True)
        print("WL2D_MOTION", index, frame, scene.render.filepath)


def scale_pose_bone(armature: bpy.types.Object, name: str, scale: tuple[float, float, float]) -> None:
    bone = armature.pose.bones.get(name)
    if bone is not None:
        bone.scale = scale
        # The imported PSA contains scale channels.  Persist the Q proxy value
        # at the style-card time so render evaluation cannot restore the source
        # scale immediately before drawing.
        bone.keyframe_insert("scale", frame=bpy.context.scene.frame_current, group=bone.name)


def apply_q_proportions() -> None:
    """Create a non-destructive Q-style pose proxy on the full evaluated rigs."""
    body = bpy.data.objects[BODY]
    face = bpy.data.objects[FACE]
    gun = bpy.data.objects[GUN]
    # Bone local Y is the longitudinal axis in the supplied UE skeleton.
    for name in ("LeftUpLeg", "RightUpLeg"):
        scale_pose_bone(body, name, (1.12, 0.58, 1.12))
    for name in ("LeftLeg", "RightLeg"):
        scale_pose_bone(body, name, (1.14, 0.62, 1.14))
    for name in ("Spine", "Spine1", "Spine2"):
        scale_pose_bone(body, name, (1.14, 0.78, 1.14))
    for name in ("LeftShoulder", "RightShoulder"):
        scale_pose_bone(body, name, (1.08, 1.10, 1.08))
    for name in ("LeftHand", "RightHand"):
        scale_pose_bone(body, name, (1.20, 1.20, 1.20))
    for name in ("LeftFoot", "RightFoot"):
        scale_pose_bone(body, name, (1.16, 1.16, 1.16))
    scale_pose_bone(body, "Head", (1.42, 1.42, 1.42))
    scale_pose_bone(body, "Head_Joint", (1.36, 1.36, 1.36))
    scale_pose_bone(face, "Head", (1.60, 1.60, 1.60))
    scale_pose_bone(gun, "AirCannon", (1.14, 1.14, 1.14))
    bpy.context.view_layer.update()


def apply_q_lattice() -> None:
    """Apply one shared world-space Q deformation to every visible mesh.

    The cage shortens the whole figure and expands the head zone without
    separating, replacing or compositing body regions.
    """
    data = bpy.data.lattices.new("WL2D_QCageData")
    data.points_u = 2
    data.points_v = 2
    data.points_w = 6
    cage = bpy.data.objects.new("WL2D_QCage", data)
    bpy.context.scene.collection.objects.link(cage)
    cage.location = (0.0, 0.0, 100.0)
    cage.dimensions = (210.0, 180.0, 220.0)
    # Desired normalized vertical distribution: aggressively shorten legs,
    # retain the chest block, then reserve space for a larger helmet mass.
    target_z = (-1.75, -1.25, -0.70, -0.05, 0.75, 1.75)
    width_scale = (1.12, 1.02, 1.00, 1.05, 1.14, 1.42)
    uv_count = data.points_u * data.points_v
    for w in range(data.points_w):
        for v in range(data.points_v):
            for u in range(data.points_u):
                point = data.points[u + v * data.points_u + w * uv_count]
                point.co_deform.x *= width_scale[w]
                point.co_deform.y *= width_scale[w]
                point.co_deform.z = target_z[w]
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.hide_render:
            continue
        modifier = obj.modifiers.new("WL2D_QFullCharacterCage", "LATTICE")
        modifier.object = cage
    bpy.context.view_layer.update()


def apply_q_lattice_v2() -> None:
    """Continuous whole-character deformation for the four-head proxy.

    Unlike the rejected cage, control points stay inside the lattice's native
    -0.5..0.5 space. Every visible mesh receives the same modifier, so the
    character is never divided into independently transformed body sections.
    """
    data = bpy.data.lattices.new("WL2D_QCageV2Data")
    data.points_u = 2
    data.points_v = 2
    data.points_w = 6
    cage = bpy.data.objects.new("WL2D_QCageV2", data)
    bpy.context.scene.collection.objects.link(cage)
    cage.location = (0.0, 0.0, 100.0)
    cage.dimensions = (210.0, 180.0, 220.0)
    # With six W points Blender's native lattice Z coordinates are
    # -2.5,-1.5,-0.5,0.5,1.5,2.5. Keep the full cage height while moving the
    # hip region downward to shorten both complete leg chains continuously.
    target_z = (-2.50, -2.10, -1.40, -0.30, 1.00, 2.50)
    width_scale = (1.20, 1.18, 1.15, 1.18, 1.25, 1.45)
    uv_count = data.points_u * data.points_v
    for w in range(data.points_w):
        for v in range(data.points_v):
            for u in range(data.points_u):
                point = data.points[u + v * data.points_u + w * uv_count]
                point.co_deform.x *= width_scale[w]
                point.co_deform.y *= width_scale[w]
                point.co_deform.z = target_z[w]
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.hide_render:
            continue
        modifier = obj.modifiers.new("WL2D_QFullCharacterCageV2", "LATTICE")
        modifier.object = cage
    cage.hide_render = True
    bpy.context.view_layer.update()


def render_stylecard() -> None:
    setup_render()
    scene = bpy.context.scene
    scene.frame_set(700)
    apply_q_lattice()
    scene.camera.data.ortho_scale = 190.0
    scene.view_settings.exposure = 0.35
    out = ROOT / "q_stylecard_highres"
    out.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(out / "weilong_q_front.png")
    bpy.ops.render.render(write_still=True)
    print("WL2D_STYLECARD", scene.render.filepath)


def freeze_pose(armature: bpy.types.Object) -> None:
    matrices = {bone.name: bone.matrix_basis.copy() for bone in armature.pose.bones}
    if armature.animation_data:
        armature.animation_data.action = None
    for bone in armature.pose.bones:
        bone.matrix_basis = matrices[bone.name]


def add_local_rotation(armature: bpy.types.Object, bone_name: str, axis: tuple[float, float, float], degrees: float) -> None:
    bone = armature.pose.bones.get(bone_name)
    if bone is None:
        return
    bone.rotation_mode = "QUATERNION"
    bone.rotation_quaternion = bone.rotation_quaternion @ Quaternion(axis, math.radians(degrees))


def key_complete_pose(armature: bpy.types.Object, frame: int) -> None:
    for bone in armature.pose.bones:
        bone.rotation_mode = "QUATERNION"
        bone.keyframe_insert("location", frame=frame, group=bone.name)
        bone.keyframe_insert("rotation_quaternion", frame=frame, group=bone.name)
        bone.keyframe_insert("scale", frame=frame, group=bone.name)


def build_fullbody_run() -> bpy.types.Action:
    """Build one full-skeleton in-place run while preserving the source grip pose."""
    scene = bpy.context.scene
    body = bpy.data.objects[BODY]
    scene.frame_set(700)
    # Apply proportions after the source frame evaluation. Calling this before
    # frame_set would let the imported PSA scale channels restore 1.0.
    apply_run_chibi_proportions()
    baseline = {bone.name: bone.matrix_basis.copy() for bone in body.pose.bones}
    action = bpy.data.actions.get("WL2D_run_forward_fullbody") or bpy.data.actions.new("WL2D_run_forward_fullbody")
    body.animation_data_create()
    body.animation_data.action = action
    keys = (1, 6, 11, 16, 21)
    phases = (0.0, 0.5 * math.pi, math.pi, 1.5 * math.pi, 2.0 * math.pi)
    for frame, phase in zip(keys, phases):
        for bone in body.pose.bones:
            bone.matrix_basis = baseline[bone.name]
        swing = math.cos(phase)
        cross = math.sin(phase)
        bounce = 2.8 * (1.0 - abs(swing))
        hips = body.pose.bones.get("Hips")
        if hips:
            hips.location.z += bounce
        # One complete pose: pelvis, spine and both legs are authored together.
        add_local_rotation(body, "Hips", (0, 0, 1), 3.0 * cross)
        add_local_rotation(body, "Spine", (1, 0, 0), 7.0)
        add_local_rotation(body, "Spine1", (0, 0, 1), -3.0 * cross)
        add_local_rotation(body, "Spine2", (0, 1, 0), 2.0 * cross)
        add_local_rotation(body, "LeftUpLeg", (1, 0, 0), 34.0 * swing)
        add_local_rotation(body, "RightUpLeg", (1, 0, 0), -34.0 * swing)
        left_knee = 10.0 + 30.0 * max(0.0, -swing) + 14.0 * abs(cross)
        right_knee = 10.0 + 30.0 * max(0.0, swing) + 14.0 * abs(cross)
        add_local_rotation(body, "LeftLeg", (1, 0, 0), -left_knee)
        add_local_rotation(body, "RightLeg", (1, 0, 0), -right_knee)
        add_local_rotation(body, "LeftFoot", (1, 0, 0), -12.0 * swing + left_knee * 0.36)
        add_local_rotation(body, "RightFoot", (1, 0, 0), 12.0 * swing + right_knee * 0.36)
        # The upper body remains a single source-authored two-hand weapon pose;
        # only a small common torso counter-motion is added.
        add_local_rotation(body, "LeftShoulder", (0, 0, 1), 1.5 * cross)
        add_local_rotation(body, "RightShoulder", (0, 0, 1), -1.5 * cross)
        key_complete_pose(body, frame)
    scene.frame_start = 1
    scene.frame_end = 20
    return action


def apply_run_chibi_proportions() -> None:
    """Adjust the complete 3D rigs toward the approved stocky pixel silhouette.

    This is evaluated before the run Action is baked.  It never divides the
    raster image or replaces a body region: every visible mesh is still drawn
    together from the same camera at the same Action time.
    """
    body = bpy.data.objects[BODY]
    face = bpy.data.objects[FACE]

    def multiply_scale(armature: bpy.types.Object, bone_name: str, xyz: tuple[float, float, float]) -> None:
        bone = armature.pose.bones.get(bone_name)
        if bone is None:
            return
        bone.scale = tuple(bone.scale[i] * xyz[i] for i in range(3))

    def compress_leg_chain(side: str, factor: float) -> None:
        """Move knee/ankle joints, instead of merely squashing leg skin."""
        hip = body.pose.bones.get(f"{side}UpLeg")
        knee = body.pose.bones.get(f"{side}Leg")
        ankle = body.pose.bones.get(f"{side}Foot")
        if hip is None or knee is None or ankle is None:
            return
        hip_pos = hip.matrix.translation.copy()
        knee_old = knee.matrix.translation.copy()
        ankle_old = ankle.matrix.translation.copy()
        knee_new = hip_pos + (knee_old - hip_pos) * factor
        ankle_new = knee_new + (ankle_old - knee_old) * factor
        knee_matrix = knee.matrix.copy()
        ankle_matrix = ankle.matrix.copy()
        knee_matrix.translation = knee_new
        knee.matrix = knee_matrix
        bpy.context.view_layer.update()
        ankle_matrix.translation = ankle_new
        ankle.matrix = ankle_matrix

    # The target is an actual four-head game silhouette, not an adult figure
    # scaled to 128 px.  Both joints and their complete skinned meshes move.
    for name in ("LeftFoot", "RightFoot"):
        multiply_scale(body, name, (1.22, 1.22, 1.22))
    for name in ("Spine", "Spine1"):
        multiply_scale(body, name, (1.18, 1.06, 1.18))
    # Enlarge the full head/helmet rig.  Arms are deliberately untouched so the
    # source-authored two-hand grip remains registered to the weapon.
    multiply_scale(body, "Head", (1.38, 1.38, 1.38))
    multiply_scale(body, "Head_Joint", (1.24, 1.24, 1.24))
    multiply_scale(face, "Head", (1.42, 1.42, 1.42))
    compress_leg_chain("Left", 0.62)
    compress_leg_chain("Right", 0.62)
    bpy.context.view_layer.update()


def reduce_texture_microdetail(max_size: int = 64) -> None:
    """Reduce source texture frequency before rendering, never after per-frame.

    This keeps armour identity blocks but stops 2K/4K fabric noise becoming
    random one-pixel confetti in a 128 px sprite.
    """
    for image in bpy.data.images:
        if image.type != "IMAGE" or image.size[0] <= 0 or image.size[1] <= 0:
            continue
        width, height = int(image.size[0]), int(image.size[1])
        longest = max(width, height)
        if longest <= max_size:
            continue
        ratio = max_size / float(longest)
        image.scale(max(1, int(round(width * ratio))), max(1, int(round(height * ratio))))
    for material in bpy.data.materials:
        if not material.use_nodes or material.node_tree is None:
            continue
        for node in material.node_tree.nodes:
            if node.type == "TEX_IMAGE":
                node.interpolation = "Closest"


def base_color_image(material: bpy.types.Material):
    if not material.use_nodes or material.node_tree is None:
        return None
    candidates = []
    for node in material.node_tree.nodes:
        if node.type != "TEX_IMAGE" or node.image is None:
            continue
        name = node.image.name.lower()
        score = 0
        if "basecolor" in name or "albedo" in name or "_bc" in name: score += 20
        if "_c." in name or name.endswith("_c.png"): score += 18
        if "idra" in name: score += 8
        if any(token in name for token in ("nrm", "_n.", "normal", "mro", "mra", "mask", "height")): score -= 30
        candidates.append((score, node.image))
    return max(candidates, key=lambda row: row[0])[1] if candidates else None


def simplify_materials_for_pixel() -> None:
    for material in bpy.data.materials:
        image = base_color_image(material)
        fallback = tuple(material.diffuse_color[:3]) if hasattr(material, "diffuse_color") else (0.28, 0.31, 0.34)
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        nodes.clear()
        output = nodes.new("ShaderNodeOutputMaterial")
        diffuse = nodes.new("ShaderNodeBsdfDiffuse")
        diffuse.inputs["Color"].default_value = (*fallback, 1.0)
        diffuse.inputs["Roughness"].default_value = 1.0
        links.new(diffuse.outputs["BSDF"], output.inputs["Surface"])
        if image is not None:
            try:
                image.colorspace_settings.name = "sRGB"
            except Exception:
                pass
            texture = nodes.new("ShaderNodeTexImage")
            texture.image = image
            texture.interpolation = "Closest"
            links.new(texture.outputs["Color"], diffuse.inputs["Color"])


def render_run() -> None:
    scene = bpy.context.scene
    body = bpy.data.objects[BODY]
    face = bpy.data.objects[FACE]
    jet = bpy.data.objects[JET]
    gun = bpy.data.objects[GUN]
    scene.frame_set(700)
    # Freeze synchronized source face/jet/weapon at the accepted grip pose.
    freeze_pose(face)
    freeze_pose(jet)
    freeze_pose(gun)
    # The face and jet are rigidly registered to the animated full-body bones;
    # no raster layer or body section is created.
    for accessory, bone_name in ((face, "Head"), (jet, "Spine2")):
        world = accessory.matrix_world.copy()
        accessory.parent = body
        accessory.parent_type = "BONE"
        accessory.parent_bone = bone_name
        accessory.matrix_world = world
    build_fullbody_run()
    setup_render()
    reduce_texture_microdetail()
    scene = bpy.context.scene
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    # One fixed safety margin for the enlarged Q helmet/feet across the entire
    # cycle.  The camera never changes between sampled frames.
    scene.camera.data.ortho_scale = 235.0
    scene.view_settings.look = "AgX - Medium High Contrast"
    # Keep the supplied PBR material graph intact.  Flattening it into a single
    # diffuse texture destroyed the armour value separation and produced a dark
    # silhouette.  Pixel colour reduction happens once, after this full-frame
    # render, so every output pixel still comes from the same evaluated body.
    scene.view_settings.exposure = 0.8
    if hasattr(scene.render, "use_freestyle"):
        # A deterministic one-pixel silhouette is generated from the final
        # whole-character alpha.  Freestyle's sub-pixel line sampling is too
        # unstable for a 128 px sprite and can sparkle between frames.
        scene.render.use_freestyle = False
    out = ROOT / "run_q_v2_highres"
    out.mkdir(parents=True, exist_ok=True)
    for index in range(12):
        source_frame = 1.0 + index * 20.0 / 12.0
        whole = int(math.floor(source_frame))
        scene.frame_set(whole, subframe=source_frame - whole)
        scene.render.filepath = str(out / f"run_f{index:02d}.png")
        bpy.ops.render.render(write_still=True)
        print("WL2D_RUN", index, source_frame, scene.render.filepath)


def render_q_static() -> None:
    """Render one direct-low-resolution Q proxy frame for visual approval."""
    scene = bpy.context.scene
    # Frame 500 has a readable near-front full-character source pose with both
    # arms and the weapon evaluated at the same official animation time.
    scene.frame_set(500)
    setup_render()
    reduce_texture_microdetail(max_size=64)
    scene = bpy.context.scene
    scene.frame_set(500)
    apply_q_lattice_v2()
    scene.render.resolution_x = 128
    scene.render.resolution_y = 128
    scene.render.resolution_percentage = 100
    scene.render.filter_size = 0.01
    scene.camera.data.ortho_scale = 180.0
    scene.camera.location = (0.0, -420.0, 200.0)
    point_at(scene.camera, Vector((0.0, 0.0, 88.0)))
    if hasattr(scene.render, "use_freestyle"):
        scene.render.use_freestyle = False
    out = ROOT / "q_static_dead_cells_pipeline"
    out.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(out / "weilong_q_front_raw_128.png")
    bpy.ops.render.render(write_still=True)
    print("WL2D_Q_STATIC", scene.render.filepath)


def main() -> None:
    args = cli()
    ROOT.mkdir(parents=True, exist_ok=True)
    visible_contract()
    prepare_animation()
    visible_contract()
    probe = scene_probe()
    (ROOT / "animation_probe.json").write_text(json.dumps(probe, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.mode == "render-probe":
        render_probe()
    elif args.mode == "render-turntable":
        render_turntable()
    elif args.mode == "render-motion":
        render_motion()
    elif args.mode == "render-stylecard":
        render_stylecard()
    elif args.mode == "render-run":
        render_run()
    elif args.mode == "render-q-static":
        render_q_static()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "weilong_fullbody_source_actions.blend"))
    print(json.dumps({"status": "OK", "mode": args.mode, "output": str(ROOT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
