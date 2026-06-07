# Stage3 ACT-lite Chunk Policy v0 闭环评估报告

- 生成时间：`2026-06-07T12:12:57`
- 状态：`PARTIAL`
- checkpoint：`D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\stage3_act_lite_chunk_policy_v1_pinch30.pth`
- 执行模式：`scripted_arm_predicted_hand`
- chunk 重规划间隔：`16`
- 成功数：`84 / 100`
- 训练状态：`stage3_act_lite_chunk_policy_v0_trained_offline_not_closed_loop_promoted`
- 边界：这是 MuJoCo 仿真闭环评估，不是硬件集成。

## 技能汇总

| 技能 | 成功 | 终止原因 | 失败项 | 风险标记 |
| --- | ---: | --- | --- | --- |
| `full_hand_gentle_grasp` | 48 / 50 | `{'success_gentle_grasp_hold': 48, 'insufficient_lift_height': 2}` | `{'insufficient_lift_height': 2, 'unstable_hold_tactile': 2, 'egg_on_floor_after_hold': 2}` | `{'early_contact_in_approach': 50, 'transient_or_hold_slip': 47}` |
| `thumb_index_middle_pinch` | 36 / 50 | `{'success_vision_confirmed_pinch_lift_hold': 36, 'vision_lift_too_small': 7, 'hold_slip_score_high': 2, 'final_vision_failed_or_occluded': 5}` | `{'vision_lift_too_small': 7, 'true_lift_too_small': 12, 'no_thumb_finger_pinch_before_lift': 8, 'pinch_not_maintained_in_hold': 9, 'hold_tactile_unstable': 10, 'egg_still_touching_floor': 12, 'hold_slip_score_high': 6, 'final_vision_failed_or_occluded': 5}` | `{'early_contact_in_approach': 50, 'transient_slip_high': 50, 'low_pinch_purity': 13, 'final_vision_occluded_or_low_confidence': 5}` |

## 单次结果

| ep | 技能 | 场景 | 状态 | 原因 | 抬升 | hold 稳定度 | hold 滑移 | 最大滑移 | 失败项 |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 0 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.0994 | 1.000 | 0.155 | 0.495 | `[]` |
| 1 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1109 | 1.000 | 0.168 | 1.000 | `[]` |
| 2 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0938 | 1.000 | 0.199 | 0.382 | `[]` |
| 3 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1103 | 1.000 | 0.297 | 0.826 | `[]` |
| 4 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.1013 | 1.000 | 0.160 | 0.569 | `[]` |
| 5 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0858 | 1.000 | 0.137 | 0.483 | `[]` |
| 6 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1199 | 1.000 | 0.185 | 0.377 | `[]` |
| 7 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.1016 | 1.000 | 0.189 | 0.563 | `[]` |
| 8 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1118 | 1.000 | 0.217 | 0.625 | `[]` |
| 9 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1145 | 1.000 | 0.175 | 0.395 | `[]` |
| 10 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.0974 | 1.000 | 0.166 | 0.460 | `[]` |
| 11 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1027 | 1.000 | 0.116 | 0.334 | `[]` |
| 12 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0945 | 1.000 | 0.182 | 0.407 | `[]` |
| 13 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1091 | 1.000 | 0.183 | 0.788 | `[]` |
| 14 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.1005 | 1.000 | 0.147 | 0.511 | `[]` |
| 15 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0848 | 1.000 | 0.230 | 0.706 | `[]` |
| 16 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1162 | 1.000 | 0.170 | 0.610 | `[]` |
| 17 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.1014 | 1.000 | 0.155 | 0.526 | `[]` |
| 18 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1118 | 1.000 | 0.223 | 0.488 | `[]` |
| 19 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1119 | 1.000 | 0.210 | 0.942 | `[]` |
| 20 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.1008 | 1.000 | 0.163 | 0.517 | `[]` |
| 21 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1051 | 1.000 | 0.102 | 0.644 | `[]` |
| 22 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0959 | 1.000 | 0.178 | 0.391 | `[]` |
| 23 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1095 | 1.000 | 0.150 | 0.328 | `[]` |
| 24 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.0999 | 1.000 | 0.147 | 0.514 | `[]` |
| 25 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0863 | 1.000 | 0.147 | 0.947 | `[]` |
| 26 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1225 | 1.000 | 0.247 | 0.538 | `[]` |
| 27 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.0990 | 1.000 | 0.183 | 0.573 | `[]` |
| 28 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1114 | 1.000 | 0.228 | 0.611 | `[]` |
| 29 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1116 | 1.000 | 0.167 | 1.000 | `[]` |
| 30 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.1006 | 1.000 | 0.160 | 0.328 | `[]` |
| 31 | `full_hand_gentle_grasp` | `left_low_nominal` | PASS | `success_gentle_grasp_hold` | 0.1032 | 1.000 | 0.194 | 0.407 | `[]` |
| 32 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0950 | 1.000 | 0.189 | 0.392 | `[]` |
| 33 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1096 | 1.000 | 0.156 | 0.367 | `[]` |
| 34 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.0977 | 1.000 | 0.138 | 0.556 | `[]` |
| 35 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0860 | 1.000 | 0.148 | 0.359 | `[]` |
| 36 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1200 | 1.000 | 0.188 | 0.383 | `[]` |
| 37 | `full_hand_gentle_grasp` | `lifted_center` | FAIL | `insufficient_lift_height` | -0.0192 | 0.000 | 0.000 | 1.000 | `['insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 38 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1114 | 1.000 | 0.216 | 0.625 | `[]` |
| 39 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1141 | 1.000 | 0.184 | 0.461 | `[]` |
| 40 | `full_hand_gentle_grasp` | `center_nominal` | PASS | `success_gentle_grasp_hold` | 0.0979 | 1.000 | 0.148 | 0.519 | `[]` |
| 41 | `full_hand_gentle_grasp` | `left_low_nominal` | FAIL | `insufficient_lift_height` | -0.0161 | 0.000 | 0.000 | 1.000 | `['insufficient_lift_height', 'unstable_hold_tactile', 'egg_on_floor_after_hold']` |
| 42 | `full_hand_gentle_grasp` | `right_high_nominal` | PASS | `success_gentle_grasp_hold` | 0.0938 | 1.000 | 0.181 | 0.397 | `[]` |
| 43 | `full_hand_gentle_grasp` | `left_high_zplus` | PASS | `success_gentle_grasp_hold` | 0.1081 | 1.000 | 0.161 | 1.000 | `[]` |
| 44 | `full_hand_gentle_grasp` | `right_low_zminus` | PASS | `success_gentle_grasp_hold` | 0.1008 | 1.000 | 0.148 | 0.520 | `[]` |
| 45 | `full_hand_gentle_grasp` | `front_small_lift` | PASS | `success_gentle_grasp_hold` | 0.0846 | 1.000 | 0.134 | 0.472 | `[]` |
| 46 | `full_hand_gentle_grasp` | `back_large_lift` | PASS | `success_gentle_grasp_hold` | 0.1203 | 1.000 | 0.170 | 0.511 | `[]` |
| 47 | `full_hand_gentle_grasp` | `lifted_center` | PASS | `success_gentle_grasp_hold` | 0.1010 | 1.000 | 0.172 | 0.519 | `[]` |
| 48 | `full_hand_gentle_grasp` | `lifted_diag` | PASS | `success_gentle_grasp_hold` | 0.1113 | 1.000 | 0.199 | 0.495 | `[]` |
| 49 | `full_hand_gentle_grasp` | `wide_diag` | PASS | `success_gentle_grasp_hold` | 0.1142 | 1.000 | 0.179 | 0.383 | `[]` |
| 50 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1001 | 1.000 | 0.167 | 1.000 | `[]` |
| 51 | `thumb_index_middle_pinch` | `left_low_nominal` | FAIL | `vision_lift_too_small` | -0.0145 | 0.000 | 0.000 | 1.000 | `['vision_lift_too_small', 'true_lift_too_small', 'no_thumb_finger_pinch_before_lift', 'pinch_not_maintained_in_hold', 'hold_tactile_unstable', 'egg_still_touching_floor']` |
| 52 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0935 | 1.000 | 0.245 | 1.000 | `[]` |
| 53 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1106 | 1.000 | 0.168 | 1.000 | `[]` |
| 54 | `thumb_index_middle_pinch` | `right_low_zminus` | FAIL | `hold_slip_score_high` | 0.0603 | 0.757 | 1.000 | 1.000 | `['hold_slip_score_high']` |
| 55 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0757 | 1.000 | 0.255 | 1.000 | `[]` |
| 56 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1159 | 1.000 | 0.254 | 1.000 | `[]` |
| 57 | `thumb_index_middle_pinch` | `lifted_center` | FAIL | `final_vision_failed_or_occluded` | -0.0170 | 0.000 | 0.000 | 1.000 | `['final_vision_failed_or_occluded', 'true_lift_too_small', 'no_thumb_finger_pinch_before_lift', 'pinch_not_maintained_in_hold', 'hold_tactile_unstable', 'egg_still_touching_floor']` |
| 58 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1131 | 1.000 | 0.205 | 0.645 | `[]` |
| 59 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1148 | 1.000 | 0.194 | 1.000 | `[]` |
| 60 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0984 | 1.000 | 0.177 | 0.925 | `[]` |
| 61 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1047 | 1.000 | 0.122 | 0.851 | `[]` |
| 62 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0960 | 1.000 | 0.217 | 1.000 | `[]` |
| 63 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1117 | 1.000 | 0.148 | 0.898 | `[]` |
| 64 | `thumb_index_middle_pinch` | `right_low_zminus` | FAIL | `vision_lift_too_small` | -0.0080 | 0.701 | 1.000 | 1.000 | `['vision_lift_too_small', 'true_lift_too_small', 'hold_slip_score_high', 'egg_still_touching_floor']` |
| 65 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0890 | 1.000 | 0.121 | 1.000 | `[]` |
| 66 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1204 | 1.000 | 0.174 | 0.815 | `[]` |
| 67 | `thumb_index_middle_pinch` | `lifted_center` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1005 | 1.000 | 0.249 | 0.893 | `[]` |
| 68 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1128 | 1.000 | 0.217 | 0.888 | `[]` |
| 69 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1141 | 1.000 | 0.181 | 1.000 | `[]` |
| 70 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1000 | 1.000 | 0.121 | 0.886 | `[]` |
| 71 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1049 | 1.000 | 0.145 | 1.000 | `[]` |
| 72 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1000 | 1.000 | 0.168 | 1.000 | `[]` |
| 73 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1114 | 1.000 | 0.156 | 1.000 | `[]` |
| 74 | `thumb_index_middle_pinch` | `right_low_zminus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1013 | 1.000 | 0.207 | 1.000 | `[]` |
| 75 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0885 | 1.000 | 0.129 | 1.000 | `[]` |
| 76 | `thumb_index_middle_pinch` | `back_large_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1221 | 1.000 | 0.179 | 1.000 | `[]` |
| 77 | `thumb_index_middle_pinch` | `lifted_center` | FAIL | `final_vision_failed_or_occluded` | -0.0223 | 0.000 | 0.000 | 1.000 | `['final_vision_failed_or_occluded', 'true_lift_too_small', 'no_thumb_finger_pinch_before_lift', 'pinch_not_maintained_in_hold', 'hold_tactile_unstable', 'egg_still_touching_floor']` |
| 78 | `thumb_index_middle_pinch` | `lifted_diag` | FAIL | `final_vision_failed_or_occluded` | -0.0163 | 0.000 | 0.000 | 1.000 | `['final_vision_failed_or_occluded', 'true_lift_too_small', 'no_thumb_finger_pinch_before_lift', 'pinch_not_maintained_in_hold', 'hold_tactile_unstable', 'egg_still_touching_floor']` |
| 79 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1138 | 1.000 | 0.179 | 1.000 | `[]` |
| 80 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1029 | 1.000 | 0.258 | 0.791 | `[]` |
| 81 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1034 | 1.000 | 0.338 | 1.000 | `[]` |
| 82 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1003 | 1.000 | 0.155 | 1.000 | `[]` |
| 83 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1100 | 1.000 | 0.147 | 1.000 | `[]` |
| 84 | `thumb_index_middle_pinch` | `right_low_zminus` | FAIL | `vision_lift_too_small` | -0.0034 | 0.516 | 1.000 | 1.000 | `['vision_lift_too_small', 'true_lift_too_small', 'hold_tactile_unstable', 'hold_slip_score_high', 'egg_still_touching_floor']` |
| 85 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0879 | 1.000 | 0.129 | 1.000 | `[]` |
| 86 | `thumb_index_middle_pinch` | `back_large_lift` | FAIL | `hold_slip_score_high` | 0.0941 | 0.876 | 1.000 | 1.000 | `['hold_slip_score_high']` |
| 87 | `thumb_index_middle_pinch` | `lifted_center` | FAIL | `final_vision_failed_or_occluded` | -0.0187 | 0.000 | 0.000 | 1.000 | `['final_vision_failed_or_occluded', 'true_lift_too_small', 'no_thumb_finger_pinch_before_lift', 'pinch_not_maintained_in_hold', 'hold_tactile_unstable', 'egg_still_touching_floor']` |
| 88 | `thumb_index_middle_pinch` | `lifted_diag` | FAIL | `vision_lift_too_small` | -0.0139 | 0.000 | 0.000 | 1.000 | `['vision_lift_too_small', 'true_lift_too_small', 'no_thumb_finger_pinch_before_lift', 'pinch_not_maintained_in_hold', 'hold_tactile_unstable', 'egg_still_touching_floor']` |
| 89 | `thumb_index_middle_pinch` | `wide_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1160 | 1.000 | 0.235 | 0.814 | `[]` |
| 90 | `thumb_index_middle_pinch` | `center_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1005 | 1.000 | 0.123 | 0.908 | `[]` |
| 91 | `thumb_index_middle_pinch` | `left_low_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1039 | 1.000 | 0.126 | 0.882 | `[]` |
| 92 | `thumb_index_middle_pinch` | `right_high_nominal` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0937 | 1.000 | 0.239 | 1.000 | `[]` |
| 93 | `thumb_index_middle_pinch` | `left_high_zplus` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1105 | 1.000 | 0.156 | 1.000 | `[]` |
| 94 | `thumb_index_middle_pinch` | `right_low_zminus` | FAIL | `final_vision_failed_or_occluded` | -0.0102 | 0.600 | 1.000 | 1.000 | `['final_vision_failed_or_occluded', 'true_lift_too_small', 'hold_slip_score_high', 'egg_still_touching_floor']` |
| 95 | `thumb_index_middle_pinch` | `front_small_lift` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.0881 | 1.000 | 0.157 | 1.000 | `[]` |
| 96 | `thumb_index_middle_pinch` | `back_large_lift` | FAIL | `vision_lift_too_small` | -0.0153 | 0.359 | 1.000 | 1.000 | `['vision_lift_too_small', 'true_lift_too_small', 'pinch_not_maintained_in_hold', 'hold_tactile_unstable', 'hold_slip_score_high', 'egg_still_touching_floor']` |
| 97 | `thumb_index_middle_pinch` | `lifted_center` | FAIL | `vision_lift_too_small` | -0.0200 | 0.000 | 0.000 | 1.000 | `['vision_lift_too_small', 'true_lift_too_small', 'no_thumb_finger_pinch_before_lift', 'pinch_not_maintained_in_hold', 'hold_tactile_unstable', 'egg_still_touching_floor']` |
| 98 | `thumb_index_middle_pinch` | `lifted_diag` | PASS | `success_vision_confirmed_pinch_lift_hold` | 0.1132 | 1.000 | 0.203 | 0.638 | `[]` |
| 99 | `thumb_index_middle_pinch` | `wide_diag` | FAIL | `vision_lift_too_small` | -0.0184 | 0.000 | 0.000 | 1.000 | `['vision_lift_too_small', 'true_lift_too_small', 'no_thumb_finger_pinch_before_lift', 'pinch_not_maintained_in_hold', 'hold_tactile_unstable', 'egg_still_touching_floor']` |

## 解释

- `full_action` 表示模型直接控制 26 个 actuator，是更难也更容易失稳的模式。
- `scripted_arm_predicted_hand` 表示手臂/手腕仍由视觉引导脚本控制，ACT-lite 只控制手指闭合和保持，这是目前更合理的第一道闭环门槛。
- 只有在成功率、滑移、挤压、穿透、落地接触都能接近或超过脚本 SkillZoo baseline 后，才适合继续提升为正式策略。

## 如果成功

下一步扩大随机姿态和场景数量，并和 Stage3.7D 全手、Stage3.8B 捏持脚本 baseline 做同条件对比。

## 如果失败

先按失败来源拆开：视觉/接近、接触建立、手指闭合、抬升保持、最终视觉确认。不要立刻扩大模型；优先调整 chunk 执行间隔、分技能头或 phase-specific head。
