#!/bin/zsh

cd '/Users/yuanhuize/codex work/三角洲行动-像素版/generated/combat_lab/build/web-desktop' || exit 1
python3 -m http.server 8468 --bind 127.0.0.1 &
rig_server_pid=$!
trap 'kill ${rig_server_pid} 2>/dev/null' EXIT INT TERM
sleep 0.5
open 'http://127.0.0.1:8468'
wait ${rig_server_pid}
