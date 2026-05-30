# Arm-Hand Stage1 V2 BC Smoke Eval Report

Generated: 2026-05-31T01:09:21

- Status: **PASS**
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth`
- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Episodes: `75`
- Success count: `75 / 75`
- Terminal reasons: `{'success_lift_hold': 75}`
- Hold enabled: `True`
- Hold pass count: `75 / 75`
- Hold reasons: `{'passed': 75}`
- Lift range: `0.077501 m` to `0.093798 m`
- Mean lift: `0.086455 m`
- Max steps: `3000`
- Action clipping: `True`
- Action smoothing: `0.5`
- Training ready: **No, experimental BC smoke only**

## Episode Results

| ep | status | reason | steps | lift m | hold | hold steps | hold min m | reward | hand contacts | floor contacts | max pen m | action L2 | delta L2 |
|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | success | success_lift_hold | 2141 | 0.079812 | passed | 900 | 0.072270 | 1.767404 | 7 | 0 | 0.002203 | 4.048648 | 0.003754 |
| 1 | success | success_lift_hold | 2141 | 0.079786 | passed | 900 | 0.072860 | 1.767147 | 7 | 0 | 0.002203 | 4.047129 | 0.003733 |
| 2 | success | success_lift_hold | 2139 | 0.079839 | passed | 900 | 0.073620 | 1.767672 | 7 | 0 | 0.002204 | 4.043685 | 0.003711 |
| 3 | success | success_lift_hold | 2139 | 0.079215 | passed | 900 | 0.069554 | 1.761433 | 7 | 0 | 0.002202 | 4.050186 | 0.003770 |
| 4 | success | success_lift_hold | 2153 | 0.081725 | passed | 900 | 0.048049 | 11.786540 | 7 | 0 | 0.002202 | 4.051550 | 0.003821 |
| 5 | success | success_lift_hold | 2133 | 0.084822 | passed | 900 | 0.081085 | 11.813995 | 6 | 0 | 0.003099 | 4.058729 | 0.003689 |
| 6 | success | success_lift_hold | 2124 | 0.085821 | passed | 900 | 0.080979 | 11.823872 | 6 | 0 | 0.003136 | 4.045986 | 0.003652 |
| 7 | success | success_lift_hold | 2124 | 0.091229 | passed | 900 | 0.081713 | 11.870652 | 7 | 0 | 0.003416 | 4.050410 | 0.003700 |
| 8 | success | success_lift_hold | 2130 | 0.086801 | passed | 900 | 0.079272 | 11.833924 | 6 | 0 | 0.003049 | 4.036952 | 0.003694 |
| 9 | success | success_lift_hold | 2137 | 0.079646 | passed | 900 | 0.059780 | 1.765741 | 7 | 0 | 0.002203 | 4.037934 | 0.003802 |
| 10 | success | success_lift_hold | 2133 | 0.084582 | passed | 900 | 0.079579 | 11.811593 | 6 | 0 | 0.003102 | 4.057349 | 0.003669 |
| 11 | success | success_lift_hold | 2129 | 0.089140 | passed | 900 | 0.079895 | 11.849764 | 7 | 0 | 0.003416 | 4.057440 | 0.003616 |
| 12 | success | success_lift_hold | 2129 | 0.089943 | passed | 900 | 0.081246 | 11.857792 | 7 | 0 | 0.003416 | 4.054111 | 0.003814 |
| 13 | success | success_lift_hold | 2125 | 0.092562 | passed | 900 | 0.081135 | 11.883975 | 7 | 0 | 0.003416 | 4.034745 | 0.003698 |
| 14 | success | success_lift_hold | 2136 | 0.079337 | passed | 900 | 0.071627 | 1.762651 | 7 | 0 | 0.002203 | 4.033968 | 0.003653 |
| 15 | success | success_lift_hold | 2129 | 0.089770 | passed | 900 | 0.081629 | 11.856065 | 7 | 0 | 0.003416 | 4.055504 | 0.003681 |
| 16 | success | success_lift_hold | 2129 | 0.089426 | passed | 900 | 0.081441 | 11.852623 | 7 | 0 | 0.003416 | 4.054418 | 0.003670 |
| 17 | success | success_lift_hold | 2129 | 0.089728 | passed | 900 | 0.081248 | 11.855636 | 7 | 0 | 0.003416 | 4.053363 | 0.003673 |
| 18 | success | success_lift_hold | 2124 | 0.093441 | passed | 900 | 0.081626 | 11.892769 | 7 | 0 | 0.003416 | 4.030117 | 0.003718 |
| 19 | success | success_lift_hold | 2128 | 0.084259 | passed | 900 | 0.071151 | 11.808384 | 6 | 0 | 0.003096 | 4.093676 | 0.003879 |
| 20 | success | success_lift_hold | 2126 | 0.093798 | passed | 900 | 0.081976 | 11.896335 | 7 | 0 | 0.003416 | 4.039120 | 0.003656 |
| 21 | success | success_lift_hold | 2125 | 0.093406 | passed | 900 | 0.081322 | 11.892416 | 7 | 0 | 0.003416 | 4.039408 | 0.003672 |
| 22 | success | success_lift_hold | 2125 | 0.092899 | passed | 900 | 0.081491 | 11.887346 | 7 | 0 | 0.003416 | 4.038637 | 0.003717 |
| 23 | success | success_lift_hold | 2124 | 0.092891 | passed | 900 | 0.081080 | 11.887268 | 7 | 0 | 0.003416 | 4.037040 | 0.003761 |
| 24 | success | success_lift_hold | 2144 | 0.077501 | passed | 900 | 0.061273 | 1.740924 | 6 | 0 | 0.003051 | 4.128221 | 0.003652 |
| 25 | success | success_lift_hold | 2141 | 0.079812 | passed | 900 | 0.072270 | 1.767404 | 7 | 0 | 0.002203 | 4.048648 | 0.003754 |
| 26 | success | success_lift_hold | 2141 | 0.079786 | passed | 900 | 0.072860 | 1.767147 | 7 | 0 | 0.002203 | 4.047129 | 0.003733 |
| 27 | success | success_lift_hold | 2139 | 0.079839 | passed | 900 | 0.073620 | 1.767672 | 7 | 0 | 0.002204 | 4.043685 | 0.003711 |
| 28 | success | success_lift_hold | 2139 | 0.079215 | passed | 900 | 0.069554 | 1.761433 | 7 | 0 | 0.002202 | 4.050186 | 0.003770 |
| 29 | success | success_lift_hold | 2153 | 0.081725 | passed | 900 | 0.048049 | 11.786540 | 7 | 0 | 0.002202 | 4.051550 | 0.003821 |
| 30 | success | success_lift_hold | 2133 | 0.084822 | passed | 900 | 0.081085 | 11.813995 | 6 | 0 | 0.003099 | 4.058729 | 0.003689 |
| 31 | success | success_lift_hold | 2124 | 0.085821 | passed | 900 | 0.080979 | 11.823872 | 6 | 0 | 0.003136 | 4.045986 | 0.003652 |
| 32 | success | success_lift_hold | 2124 | 0.091229 | passed | 900 | 0.081713 | 11.870652 | 7 | 0 | 0.003416 | 4.050410 | 0.003700 |
| 33 | success | success_lift_hold | 2130 | 0.086801 | passed | 900 | 0.079272 | 11.833924 | 6 | 0 | 0.003049 | 4.036952 | 0.003694 |
| 34 | success | success_lift_hold | 2137 | 0.079646 | passed | 900 | 0.059780 | 1.765741 | 7 | 0 | 0.002203 | 4.037934 | 0.003802 |
| 35 | success | success_lift_hold | 2133 | 0.084582 | passed | 900 | 0.079579 | 11.811593 | 6 | 0 | 0.003102 | 4.057349 | 0.003669 |
| 36 | success | success_lift_hold | 2129 | 0.089140 | passed | 900 | 0.079895 | 11.849764 | 7 | 0 | 0.003416 | 4.057440 | 0.003616 |
| 37 | success | success_lift_hold | 2129 | 0.089943 | passed | 900 | 0.081246 | 11.857792 | 7 | 0 | 0.003416 | 4.054111 | 0.003814 |
| 38 | success | success_lift_hold | 2125 | 0.092562 | passed | 900 | 0.081135 | 11.883975 | 7 | 0 | 0.003416 | 4.034745 | 0.003698 |
| 39 | success | success_lift_hold | 2136 | 0.079337 | passed | 900 | 0.071627 | 1.762651 | 7 | 0 | 0.002203 | 4.033968 | 0.003653 |
| 40 | success | success_lift_hold | 2129 | 0.089770 | passed | 900 | 0.081629 | 11.856065 | 7 | 0 | 0.003416 | 4.055504 | 0.003681 |
| 41 | success | success_lift_hold | 2129 | 0.089426 | passed | 900 | 0.081441 | 11.852623 | 7 | 0 | 0.003416 | 4.054418 | 0.003670 |
| 42 | success | success_lift_hold | 2129 | 0.089728 | passed | 900 | 0.081248 | 11.855636 | 7 | 0 | 0.003416 | 4.053363 | 0.003673 |
| 43 | success | success_lift_hold | 2124 | 0.093441 | passed | 900 | 0.081626 | 11.892769 | 7 | 0 | 0.003416 | 4.030117 | 0.003718 |
| 44 | success | success_lift_hold | 2128 | 0.084259 | passed | 900 | 0.071151 | 11.808384 | 6 | 0 | 0.003096 | 4.093676 | 0.003879 |
| 45 | success | success_lift_hold | 2126 | 0.093798 | passed | 900 | 0.081976 | 11.896335 | 7 | 0 | 0.003416 | 4.039120 | 0.003656 |
| 46 | success | success_lift_hold | 2125 | 0.093406 | passed | 900 | 0.081322 | 11.892416 | 7 | 0 | 0.003416 | 4.039408 | 0.003672 |
| 47 | success | success_lift_hold | 2125 | 0.092899 | passed | 900 | 0.081491 | 11.887346 | 7 | 0 | 0.003416 | 4.038637 | 0.003717 |
| 48 | success | success_lift_hold | 2124 | 0.092891 | passed | 900 | 0.081080 | 11.887268 | 7 | 0 | 0.003416 | 4.037040 | 0.003761 |
| 49 | success | success_lift_hold | 2144 | 0.077501 | passed | 900 | 0.061273 | 1.740924 | 6 | 0 | 0.003051 | 4.128221 | 0.003652 |
| 50 | success | success_lift_hold | 2141 | 0.079812 | passed | 900 | 0.072270 | 1.767404 | 7 | 0 | 0.002203 | 4.048648 | 0.003754 |
| 51 | success | success_lift_hold | 2141 | 0.079786 | passed | 900 | 0.072860 | 1.767147 | 7 | 0 | 0.002203 | 4.047129 | 0.003733 |
| 52 | success | success_lift_hold | 2139 | 0.079839 | passed | 900 | 0.073620 | 1.767672 | 7 | 0 | 0.002204 | 4.043685 | 0.003711 |
| 53 | success | success_lift_hold | 2139 | 0.079215 | passed | 900 | 0.069554 | 1.761433 | 7 | 0 | 0.002202 | 4.050186 | 0.003770 |
| 54 | success | success_lift_hold | 2153 | 0.081725 | passed | 900 | 0.048049 | 11.786540 | 7 | 0 | 0.002202 | 4.051550 | 0.003821 |
| 55 | success | success_lift_hold | 2133 | 0.084822 | passed | 900 | 0.081085 | 11.813995 | 6 | 0 | 0.003099 | 4.058729 | 0.003689 |
| 56 | success | success_lift_hold | 2124 | 0.085821 | passed | 900 | 0.080979 | 11.823872 | 6 | 0 | 0.003136 | 4.045986 | 0.003652 |
| 57 | success | success_lift_hold | 2124 | 0.091229 | passed | 900 | 0.081713 | 11.870652 | 7 | 0 | 0.003416 | 4.050410 | 0.003700 |
| 58 | success | success_lift_hold | 2130 | 0.086801 | passed | 900 | 0.079272 | 11.833924 | 6 | 0 | 0.003049 | 4.036952 | 0.003694 |
| 59 | success | success_lift_hold | 2137 | 0.079646 | passed | 900 | 0.059780 | 1.765741 | 7 | 0 | 0.002203 | 4.037934 | 0.003802 |
| 60 | success | success_lift_hold | 2133 | 0.084582 | passed | 900 | 0.079579 | 11.811593 | 6 | 0 | 0.003102 | 4.057349 | 0.003669 |
| 61 | success | success_lift_hold | 2129 | 0.089140 | passed | 900 | 0.079895 | 11.849764 | 7 | 0 | 0.003416 | 4.057440 | 0.003616 |
| 62 | success | success_lift_hold | 2129 | 0.089943 | passed | 900 | 0.081246 | 11.857792 | 7 | 0 | 0.003416 | 4.054111 | 0.003814 |
| 63 | success | success_lift_hold | 2125 | 0.092562 | passed | 900 | 0.081135 | 11.883975 | 7 | 0 | 0.003416 | 4.034745 | 0.003698 |
| 64 | success | success_lift_hold | 2136 | 0.079337 | passed | 900 | 0.071627 | 1.762651 | 7 | 0 | 0.002203 | 4.033968 | 0.003653 |
| 65 | success | success_lift_hold | 2129 | 0.089770 | passed | 900 | 0.081629 | 11.856065 | 7 | 0 | 0.003416 | 4.055504 | 0.003681 |
| 66 | success | success_lift_hold | 2129 | 0.089426 | passed | 900 | 0.081441 | 11.852623 | 7 | 0 | 0.003416 | 4.054418 | 0.003670 |
| 67 | success | success_lift_hold | 2129 | 0.089728 | passed | 900 | 0.081248 | 11.855636 | 7 | 0 | 0.003416 | 4.053363 | 0.003673 |
| 68 | success | success_lift_hold | 2124 | 0.093441 | passed | 900 | 0.081626 | 11.892769 | 7 | 0 | 0.003416 | 4.030117 | 0.003718 |
| 69 | success | success_lift_hold | 2128 | 0.084259 | passed | 900 | 0.071151 | 11.808384 | 6 | 0 | 0.003096 | 4.093676 | 0.003879 |
| 70 | success | success_lift_hold | 2126 | 0.093798 | passed | 900 | 0.081976 | 11.896335 | 7 | 0 | 0.003416 | 4.039120 | 0.003656 |
| 71 | success | success_lift_hold | 2125 | 0.093406 | passed | 900 | 0.081322 | 11.892416 | 7 | 0 | 0.003416 | 4.039408 | 0.003672 |
| 72 | success | success_lift_hold | 2125 | 0.092899 | passed | 900 | 0.081491 | 11.887346 | 7 | 0 | 0.003416 | 4.038637 | 0.003717 |
| 73 | success | success_lift_hold | 2124 | 0.092891 | passed | 900 | 0.081080 | 11.887268 | 7 | 0 | 0.003416 | 4.037040 | 0.003761 |
| 74 | success | success_lift_hold | 2144 | 0.077501 | passed | 900 | 0.061273 | 1.740924 | 6 | 0 | 0.003051 | 4.128221 | 0.003652 |

## Interpretation

- This is the online rollout gate for the first BC smoke checkpoint.
- PASS/PARTIAL here still does not promote the model to the maintained project baseline.
- If this report is FAIL, inspect action scaling, phase features, and dataset coverage before collecting larger data.
