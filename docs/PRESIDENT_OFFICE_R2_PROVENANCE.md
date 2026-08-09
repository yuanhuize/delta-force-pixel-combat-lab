# President Office R2 场景来源证据

`combat_lab` 中的 R2 资源是可运行副本，原始场景证据仍保留在工作区 `art_demos` 中，未被移动或替换。

- 六张地图来源：`art_demos/president_office_map_v2/playable_scene/assets/room_maps_r2/`
- 冻结房间拓扑：`art_demos/president_office_map_v2/playable_scene/data/president_office_room_graph_r2.json`
- 障碍物清单：`art_demos/president_office_map_v2/peace_elite_reference/ROOM_OBSTACLE_INVENTORY_R2.md`
- 生成规格：`art_demos/president_office_map_v2/ROOM_MAPS_R2_GENERATION_SPEC.md`
- 对照联系表：`art_demos/president_office_map_v2/playable_scene/assets/room_maps_r2/room_maps_r2_contact_sheet.png`

运行碰撞不是从上述 PNG 的颜色或 alpha 反推出来的。它是依据 Blender/视频场景证据和锁定拓扑独立编辑的矩形数据，位于 `assets/resources/president_office_r2/data/president_office_rooms_r2.json`。

## 威龙 V2.1 角色来源

- 上游批准清单：`art_demos/weilong_elbow_core_run_v2_1/ART_APPROVED_V2_1.md`
- 上游完整哈希清单：`art_demos/weilong_elbow_core_run_v2_1/SHA256SUMS_ART_APPROVED_V2_1.txt`
- combat_lab 运行时批准清单：`assets/resources/weilong_v2_1/ART_APPROVAL_MANIFEST.json`

combat_lab 只复制并加载已批准的肘部身体核心 PNG、肘部挂点 JSON 与 V2.1 spec。`weilong_fullbody_run_8dir_12f_source_v2_1.png` 只用于上游 QA/追溯，没有复制到运行资源，也没有被脚本引用。
