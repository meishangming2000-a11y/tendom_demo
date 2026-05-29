# Arm-Hand Stage1 V2 Dataset V0.1 Report

Generated: 2026-05-30T00:36:33

- Task: `arm_hand_stage1_lift_ball`
- Contract: `stage2_lift_ball_v0_1`
- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz`
- Episodes: `75`
- Total rows: `77154`
- obs shape: `[77154, 124]`
- behavior actions shape: `[77154, 26]`
- expert actions shape: `[77154, 26]`
- Success count: `68 / 75`
- Terminal reasons: `{'success_lift_ball': 68, 'timeout': 7}`
- Profile counts: `{'clean_nominal': 25, 'mild_fast_jitter': 25, 'mild_slow_jitter': 25}`
- BC target field: `expert_actions`
- Training ready: **No, experimental BC smoke only**

## Episode Summary

| ep | profile | offset xyz | rows | terminal phase | status | reason | lift m | hand contacts | max pen m |
|---:|---|---|---:|---|---|---|---:|---:|---:|
| 0 | clean_nominal | `[-0.02, -0.02, 0.0]` | 1009 | lift | success | success_lift_ball | 0.0804 | 7 | 0.003148 |
| 1 | clean_nominal | `[-0.01, -0.02, 0.0]` | 1009 | lift | success | success_lift_ball | 0.0804 | 7 | 0.003149 |
| 2 | clean_nominal | `[0.0, -0.02, 0.0]` | 1009 | lift | success | success_lift_ball | 0.0805 | 7 | 0.003129 |
| 3 | clean_nominal | `[0.01, -0.02, 0.0]` | 1009 | lift | success | success_lift_ball | 0.0804 | 7 | 0.003133 |
| 4 | clean_nominal | `[0.02, -0.02, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003447 |
| 5 | clean_nominal | `[-0.02, -0.01, 0.0]` | 1014 | lift | success | success_lift_ball | 0.0802 | 4 | 0.002825 |
| 6 | clean_nominal | `[-0.01, -0.01, 0.0]` | 1009 | lift | success | success_lift_ball | 0.0801 | 7 | 0.003188 |
| 7 | clean_nominal | `[0.0, -0.01, 0.0]` | 1009 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003131 |
| 8 | clean_nominal | `[0.01, -0.01, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003446 |
| 9 | clean_nominal | `[0.02, -0.01, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0805 | 7 | 0.003447 |
| 10 | clean_nominal | `[-0.02, 0.0, 0.0]` | 1008 | lift | success | success_lift_ball | 0.0807 | 6 | 0.003241 |
| 11 | clean_nominal | `[-0.01, 0.0, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0803 | 8 | 0.003372 |
| 12 | clean_nominal | `[0.0, 0.0, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0807 | 7 | 0.003449 |
| 13 | clean_nominal | `[0.01, 0.0, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003450 |
| 14 | clean_nominal | `[0.02, 0.0, 0.0]` | 1230 | hold_lift | failure | timeout | -0.0002 | 0 | 0.000184 |
| 15 | clean_nominal | `[-0.02, 0.01, 0.0]` | 1008 | lift | success | success_lift_ball | 0.0804 | 6 | 0.003195 |
| 16 | clean_nominal | `[-0.01, 0.01, 0.0]` | 1007 | lift | success | success_lift_ball | 0.0808 | 6 | 0.003386 |
| 17 | clean_nominal | `[0.0, 0.01, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0807 | 7 | 0.003450 |
| 18 | clean_nominal | `[0.01, 0.01, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0803 | 7 | 0.003452 |
| 19 | clean_nominal | `[0.02, 0.01, 0.0]` | 1007 | lift | success | success_lift_ball | 0.0807 | 7 | 0.003432 |
| 20 | clean_nominal | `[-0.02, 0.02, 0.0]` | 1010 | lift | success | success_lift_ball | 0.0805 | 7 | 0.003146 |
| 21 | clean_nominal | `[-0.01, 0.02, 0.0]` | 1008 | lift | success | success_lift_ball | 0.0805 | 6 | 0.003209 |
| 22 | clean_nominal | `[0.0, 0.02, 0.0]` | 1006 | lift | success | success_lift_ball | 0.0807 | 7 | 0.003449 |
| 23 | clean_nominal | `[0.01, 0.02, 0.0]` | 1007 | lift | success | success_lift_ball | 0.0805 | 7 | 0.003414 |
| 24 | clean_nominal | `[0.02, 0.02, 0.0]` | 1230 | hold_lift | failure | timeout | -0.0002 | 0 | 0.000184 |
| 25 | mild_fast_jitter | `[-0.02, -0.02, 0.0]` | 971 | lift | success | success_lift_ball | 0.0805 | 4 | 0.002840 |
| 26 | mild_fast_jitter | `[-0.01, -0.02, 0.0]` | 968 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003204 |
| 27 | mild_fast_jitter | `[0.0, -0.02, 0.0]` | 968 | lift | success | success_lift_ball | 0.0800 | 7 | 0.003149 |
| 28 | mild_fast_jitter | `[0.01, -0.02, 0.0]` | 968 | lift | success | success_lift_ball | 0.0800 | 7 | 0.003165 |
| 29 | mild_fast_jitter | `[0.02, -0.02, 0.0]` | 965 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003451 |
| 30 | mild_fast_jitter | `[-0.02, -0.01, 0.0]` | 967 | lift | success | success_lift_ball | 0.0802 | 7 | 0.003189 |
| 31 | mild_fast_jitter | `[-0.01, -0.01, 0.0]` | 968 | lift | success | success_lift_ball | 0.0801 | 7 | 0.003120 |
| 32 | mild_fast_jitter | `[0.0, -0.01, 0.0]` | 968 | lift | success | success_lift_ball | 0.0804 | 7 | 0.003100 |
| 33 | mild_fast_jitter | `[0.01, -0.01, 0.0]` | 965 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003468 |
| 34 | mild_fast_jitter | `[0.02, -0.01, 0.0]` | 966 | lift | success | success_lift_ball | 0.0808 | 7 | 0.003420 |
| 35 | mild_fast_jitter | `[-0.02, 0.0, 0.0]` | 968 | lift | success | success_lift_ball | 0.0805 | 7 | 0.003104 |
| 36 | mild_fast_jitter | `[-0.01, 0.0, 0.0]` | 965 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003427 |
| 37 | mild_fast_jitter | `[0.0, 0.0, 0.0]` | 965 | lift | success | success_lift_ball | 0.0800 | 7 | 0.003467 |
| 38 | mild_fast_jitter | `[0.01, 0.0, 0.0]` | 1180 | hold_lift | failure | timeout | -0.0002 | 0 | 0.000184 |
| 39 | mild_fast_jitter | `[0.02, 0.0, 0.0]` | 1180 | hold_lift | failure | timeout | -0.0002 | 0 | 0.000184 |
| 40 | mild_fast_jitter | `[-0.02, 0.01, 0.0]` | 968 | lift | success | success_lift_ball | 0.0808 | 6 | 0.003136 |
| 41 | mild_fast_jitter | `[-0.01, 0.01, 0.0]` | 965 | lift | success | success_lift_ball | 0.0807 | 7 | 0.003451 |
| 42 | mild_fast_jitter | `[0.0, 0.01, 0.0]` | 966 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003441 |
| 43 | mild_fast_jitter | `[0.01, 0.01, 0.0]` | 967 | lift | success | success_lift_ball | 0.0810 | 7 | 0.003404 |
| 44 | mild_fast_jitter | `[0.02, 0.01, 0.0]` | 1180 | hold_lift | failure | timeout | -0.0002 | 0 | 0.000184 |
| 45 | mild_fast_jitter | `[-0.02, 0.02, 0.0]` | 969 | lift | success | success_lift_ball | 0.0808 | 7 | 0.003177 |
| 46 | mild_fast_jitter | `[-0.01, 0.02, 0.0]` | 967 | lift | success | success_lift_ball | 0.0805 | 5 | 0.003383 |
| 47 | mild_fast_jitter | `[0.0, 0.02, 0.0]` | 966 | lift | success | success_lift_ball | 0.0808 | 7 | 0.003471 |
| 48 | mild_fast_jitter | `[0.01, 0.02, 0.0]` | 999 | lift | success | success_lift_ball | 0.0807 | 4 | 0.000739 |
| 49 | mild_fast_jitter | `[0.02, 0.02, 0.0]` | 1180 | hold_lift | failure | timeout | -0.0002 | 0 | 0.000184 |
| 50 | mild_slow_jitter | `[-0.02, -0.02, 0.0]` | 1053 | lift | success | success_lift_ball | 0.0801 | 7 | 0.003177 |
| 51 | mild_slow_jitter | `[-0.01, -0.02, 0.0]` | 1053 | lift | success | success_lift_ball | 0.0803 | 7 | 0.003151 |
| 52 | mild_slow_jitter | `[0.0, -0.02, 0.0]` | 1050 | lift | success | success_lift_ball | 0.0802 | 7 | 0.003100 |
| 53 | mild_slow_jitter | `[0.01, -0.02, 0.0]` | 1050 | lift | success | success_lift_ball | 0.0802 | 6 | 0.003244 |
| 54 | mild_slow_jitter | `[0.02, -0.02, 0.0]` | 1045 | lift | success | success_lift_ball | 0.0803 | 7 | 0.003423 |
| 55 | mild_slow_jitter | `[-0.02, -0.01, 0.0]` | 1051 | lift | success | success_lift_ball | 0.0803 | 7 | 0.003118 |
| 56 | mild_slow_jitter | `[-0.01, -0.01, 0.0]` | 1053 | lift | success | success_lift_ball | 0.0802 | 5 | 0.002946 |
| 57 | mild_slow_jitter | `[0.0, -0.01, 0.0]` | 1046 | lift | success | success_lift_ball | 0.0808 | 7 | 0.003468 |
| 58 | mild_slow_jitter | `[0.01, -0.01, 0.0]` | 1049 | lift | success | success_lift_ball | 0.0804 | 7 | 0.003444 |
| 59 | mild_slow_jitter | `[0.02, -0.01, 0.0]` | 1280 | hold_lift | failure | timeout | -0.0002 | 0 | 0.000184 |
| 60 | mild_slow_jitter | `[-0.02, 0.0, 0.0]` | 1052 | lift | success | success_lift_ball | 0.0804 | 7 | 0.003115 |
| 61 | mild_slow_jitter | `[-0.01, 0.0, 0.0]` | 1050 | lift | success | success_lift_ball | 0.0801 | 6 | 0.003267 |
| 62 | mild_slow_jitter | `[0.0, 0.0, 0.0]` | 1046 | lift | success | success_lift_ball | 0.0803 | 7 | 0.003454 |
| 63 | mild_slow_jitter | `[0.01, 0.0, 0.0]` | 1046 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003464 |
| 64 | mild_slow_jitter | `[0.02, 0.0, 0.0]` | 1046 | lift | success | success_lift_ball | 0.0803 | 7 | 0.003396 |
| 65 | mild_slow_jitter | `[-0.02, 0.01, 0.0]` | 1052 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003125 |
| 66 | mild_slow_jitter | `[-0.01, 0.01, 0.0]` | 1046 | lift | success | success_lift_ball | 0.0806 | 8 | 0.003457 |
| 67 | mild_slow_jitter | `[0.0, 0.01, 0.0]` | 1047 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003457 |
| 68 | mild_slow_jitter | `[0.01, 0.01, 0.0]` | 1049 | lift | success | success_lift_ball | 0.0808 | 6 | 0.003306 |
| 69 | mild_slow_jitter | `[0.02, 0.01, 0.0]` | 1048 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003427 |
| 70 | mild_slow_jitter | `[-0.02, 0.02, 0.0]` | 1050 | lift | success | success_lift_ball | 0.0800 | 7 | 0.003155 |
| 71 | mild_slow_jitter | `[-0.01, 0.02, 0.0]` | 1055 | lift | success | success_lift_ball | 0.0805 | 5 | 0.002756 |
| 72 | mild_slow_jitter | `[0.0, 0.02, 0.0]` | 1048 | lift | success | success_lift_ball | 0.0806 | 7 | 0.003435 |
| 73 | mild_slow_jitter | `[0.01, 0.02, 0.0]` | 1048 | lift | success | success_lift_ball | 0.0800 | 7 | 0.003465 |
| 74 | mild_slow_jitter | `[0.02, 0.02, 0.0]` | 1045 | lift | success | success_lift_ball | 0.0803 | 7 | 0.003413 |

## Interpretation

- Replay should validate against `actions`, because those were applied in MuJoCo.
- BC should train against `expert_actions`, because those are the scripted recovery targets.
- The perturbations are intentionally mild and are meant to reduce closed-loop covariate shift for obs+phase BC.
