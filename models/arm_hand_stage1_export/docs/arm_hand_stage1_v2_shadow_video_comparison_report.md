# Arm+Hand Stage1 v2 vs Shadow Video Comparison

Generated: 2026-05-28 02:13:28

## Scope

This diagnostic maps the same recorded open/close video features to Shadow Hand and to the current arm+hand export4 v2 assembly. The ball is removed; the purpose is to check whether both hands can replay closure-like motion and produce comparable geometry metrics. No training, tendon routing, CAD edit, STL edit, joint-tree edit, or joint-name edit was performed.

## Inputs

- Manifest: `D:\tendon_project\artifacts\vision_real_hand\open_close_v1\open_close_manifest.json`
- Shadow scene: `D:\tendon_project\simulations\models\shadow_hand\scene_right_no_object_compare.xml`
- Arm+hand scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_collision_proxy_v2.xml`
- Visual output: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_shadow_video_compare`

## Aggregate

- Videos processed: `12` / `12`
- Shadow failures: `0`
- Arm+hand failures: `0`
- Shadow mean closure score: `0.3136`
- Arm+hand v2 mean closure score: `0.2202`
- Score correlation: `0.8646130677077688`

## Model Summary

- Shadow: `26` bodies, `24` joints, `24` actuators, `63` geoms, `1` sites.
- Arm+hand v2: `31` bodies, `26` joints, `26` actuators, `66` geoms, `14` sites.

## Per-Video Results

| video | frames | curl range | Shadow score | Arm+hand v2 score | Shadow tip delta | Arm+hand tip delta | Arm+hand thumb-index close | sheet |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 3b8df50c5b | 871 | 0.116 | 0.074 | 0.054 | 0.0047 | 0.0007 | 0.1142 | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_shadow_video_compare\3b8df50c5b02578840f6780eb1af3864\shadow_arm_hand_v2_keyframe_comparison.png` |
| 5526d4a4db | 686 | 0.408 | 0.297 | 0.242 | 0.0288 | 0.0111 | 0.0669 | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_shadow_video_compare\5526d4a4dbfa60def9174c1cbc2b337f\shadow_arm_hand_v2_keyframe_comparison.png` |
| 5f8921b82b | 1941 | 0.415 | 0.383 | 0.212 | 0.0330 | 0.0094 | 0.0757 | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_shadow_video_compare\5f8921b82b99d271f2447342503491f1\shadow_arm_hand_v2_keyframe_comparison.png` |
| 7435f48581 | 1431 | 0.432 | 0.380 | 0.238 | 0.0410 | 0.0120 | 0.0693 | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_shadow_video_compare\7435f48581dd15b87bd8e414102889a9\shadow_arm_hand_v2_keyframe_comparison.png` |
| 75591dc2dd | 881 | 0.236 | 0.158 | 0.110 | 0.0211 | 0.0026 | 0.1000 | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_shadow_video_compare\75591dc2dd31629fae53e43a1ef42869\shadow_arm_hand_v2_keyframe_comparison.png` |
| 82a39952e2 | 2766 | 0.602 | 0.321 | 0.300 | 0.0212 | 0.0171 | 0.0554 | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_shadow_video_compare\82a39952e2c714b2b7dd1a0652dbfd14\shadow_arm_hand_v2_keyframe_comparison.png` |
| 8bb172ba1f | 1026 | 0.426 | 0.383 | 0.241 | 0.0396 | 0.0114 | 0.0676 | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_shadow_video_compare\8bb172ba1face74ebdf65f7963919284\shadow_arm_hand_v2_keyframe_comparison.png` |
| c244bd77cb | 1241 | 0.537 | 0.418 | 0.293 | 0.0386 | 0.0157 | 0.0573 | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_shadow_video_compare\c244bd77cb952f142ee158d5ee4b8183\shadow_arm_hand_v2_keyframe_comparison.png` |
| dcd8d76b78 | 2806 | 0.422 | 0.393 | 0.215 | 0.0376 | 0.0095 | 0.0764 | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_shadow_video_compare\dcd8d76b7832ddba4ada715d0131df12\shadow_arm_hand_v2_keyframe_comparison.png` |
| e756f557a5 | 1611 | 0.332 | 0.205 | 0.118 | 0.0280 | 0.0065 | 0.1062 | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_shadow_video_compare\e756f557a531f0f65cef54a4e2522e7c\shadow_arm_hand_v2_keyframe_comparison.png` |
| f1003df868 | 1716 | 0.548 | 0.368 | 0.301 | 0.0325 | 0.0165 | 0.0558 | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_shadow_video_compare\f1003df86868f1e9c45236a4576a3bfc\shadow_arm_hand_v2_keyframe_comparison.png` |
| fd33c34413 | 1811 | 0.582 | 0.383 | 0.318 | 0.0413 | 0.0192 | 0.0481 | `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_shadow_video_compare\fd33c3441391718965fe6718dd8b9aef\shadow_arm_hand_v2_keyframe_comparison.png` |

## Interpretation

- Passing here means the video-to-control pathway can drive both the Shadow reference model and our arm+hand stage1 model through a comparable open/close motion.
- This does not prove stable object grasp, because the ball is intentionally removed from this comparison.
- The arm+hand model now includes the mechanical arm context; arm actuators are held at zero during this hand-closure diagnostic.
- Current collision v2 is useful for smoke tests, but collision fidelity is still not training-ready.

Machine-readable summary: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\arm_hand_stage1_v2_shadow_video_comparison.json`
