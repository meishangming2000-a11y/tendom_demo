# Arm-Hand Stage1 V2 BC Smoke Eval Report

Generated: 2026-05-30T20:56:13

- Status: **PASS**
- Checkpoint: `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth`
- Dataset: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz`
- Scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Episodes: `75`
- Success count: `75 / 75`
- Terminal reasons: `{'success_lift_ball': 75}`
- Lift range: `0.080064 m` to `0.080977 m`
- Mean lift: `0.080432 m`
- Max steps: `1300`
- Action clipping: `True`
- Action smoothing: `0.5`
- Training ready: **No, experimental BC smoke only**

## Episode Results

| ep | status | reason | steps | lift m | reward | hand contacts | floor contacts | max pen m | action L2 | delta L2 |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | success | success_lift_ball | 1061 | 0.080533 | 11.773449 | 5 | 0 | 0.002423 | 3.430824 | 0.007489 |
| 1 | success | success_lift_ball | 1061 | 0.080425 | 11.772294 | 6 | 0 | 0.002369 | 3.430088 | 0.007472 |
| 2 | success | success_lift_ball | 1059 | 0.080431 | 11.771815 | 5 | 0 | 0.002531 | 3.423097 | 0.007457 |
| 3 | success | success_lift_ball | 1059 | 0.080273 | 11.770409 | 5 | 0 | 0.002624 | 3.425811 | 0.007466 |
| 4 | success | success_lift_ball | 1073 | 0.080553 | 11.774285 | 9 | 0 | 0.002294 | 3.431153 | 0.007259 |
| 5 | success | success_lift_ball | 1053 | 0.080410 | 11.768330 | 7 | 0 | 0.003152 | 3.427396 | 0.007269 |
| 6 | success | success_lift_ball | 1044 | 0.080085 | 11.763905 | 6 | 0 | 0.003292 | 3.412567 | 0.007343 |
| 7 | success | success_lift_ball | 1044 | 0.080672 | 11.764625 | 7 | 0 | 0.003452 | 3.412420 | 0.007398 |
| 8 | success | success_lift_ball | 1050 | 0.080783 | 11.772867 | 6 | 0 | 0.003201 | 3.398058 | 0.007400 |
| 9 | success | success_lift_ball | 1057 | 0.080164 | 11.768757 | 5 | 0 | 0.002706 | 3.402741 | 0.007319 |
| 10 | success | success_lift_ball | 1053 | 0.080232 | 11.766531 | 7 | 0 | 0.003134 | 3.422885 | 0.007253 |
| 11 | success | success_lift_ball | 1049 | 0.080577 | 11.763850 | 7 | 0 | 0.003447 | 3.417532 | 0.007280 |
| 12 | success | success_lift_ball | 1049 | 0.080353 | 11.761585 | 7 | 0 | 0.003449 | 3.414909 | 0.007553 |
| 13 | success | success_lift_ball | 1045 | 0.080120 | 11.759069 | 7 | 0 | 0.003443 | 3.390825 | 0.007429 |
| 14 | success | success_lift_ball | 1056 | 0.080082 | 11.767821 | 5 | 0 | 0.002829 | 3.399516 | 0.007309 |
| 15 | success | success_lift_ball | 1049 | 0.080726 | 11.765337 | 7 | 0 | 0.003449 | 3.416232 | 0.007280 |
| 16 | success | success_lift_ball | 1049 | 0.080568 | 11.763859 | 7 | 0 | 0.003441 | 3.414789 | 0.007269 |
| 17 | success | success_lift_ball | 1049 | 0.080349 | 11.761565 | 7 | 0 | 0.003450 | 3.414031 | 0.007272 |
| 18 | success | success_lift_ball | 1044 | 0.080641 | 11.764304 | 7 | 0 | 0.003442 | 3.384130 | 0.007448 |
| 19 | success | success_lift_ball | 1048 | 0.080319 | 11.767560 | 7 | 0 | 0.003065 | 3.425825 | 0.007796 |
| 20 | success | success_lift_ball | 1046 | 0.080977 | 11.768784 | 7 | 0 | 0.003489 | 3.403069 | 0.007347 |
| 21 | success | success_lift_ball | 1045 | 0.080305 | 11.761103 | 7 | 0 | 0.003438 | 3.400649 | 0.007393 |
| 22 | success | success_lift_ball | 1045 | 0.080482 | 11.762730 | 7 | 0 | 0.003441 | 3.398033 | 0.007489 |
| 23 | success | success_lift_ball | 1044 | 0.080064 | 11.758509 | 7 | 0 | 0.003439 | 3.396289 | 0.007545 |
| 24 | success | success_lift_ball | 1064 | 0.080676 | 11.771868 | 7 | 0 | 0.003178 | 3.496977 | 0.007296 |
| 25 | success | success_lift_ball | 1061 | 0.080533 | 11.773449 | 5 | 0 | 0.002423 | 3.430824 | 0.007489 |
| 26 | success | success_lift_ball | 1061 | 0.080425 | 11.772294 | 6 | 0 | 0.002369 | 3.430088 | 0.007472 |
| 27 | success | success_lift_ball | 1059 | 0.080431 | 11.771815 | 5 | 0 | 0.002531 | 3.423097 | 0.007457 |
| 28 | success | success_lift_ball | 1059 | 0.080273 | 11.770409 | 5 | 0 | 0.002624 | 3.425811 | 0.007466 |
| 29 | success | success_lift_ball | 1073 | 0.080553 | 11.774285 | 9 | 0 | 0.002294 | 3.431153 | 0.007259 |
| 30 | success | success_lift_ball | 1053 | 0.080410 | 11.768330 | 7 | 0 | 0.003152 | 3.427396 | 0.007269 |
| 31 | success | success_lift_ball | 1044 | 0.080085 | 11.763905 | 6 | 0 | 0.003292 | 3.412567 | 0.007343 |
| 32 | success | success_lift_ball | 1044 | 0.080672 | 11.764625 | 7 | 0 | 0.003452 | 3.412420 | 0.007398 |
| 33 | success | success_lift_ball | 1050 | 0.080783 | 11.772867 | 6 | 0 | 0.003201 | 3.398058 | 0.007400 |
| 34 | success | success_lift_ball | 1057 | 0.080164 | 11.768757 | 5 | 0 | 0.002706 | 3.402741 | 0.007319 |
| 35 | success | success_lift_ball | 1053 | 0.080232 | 11.766531 | 7 | 0 | 0.003134 | 3.422885 | 0.007253 |
| 36 | success | success_lift_ball | 1049 | 0.080577 | 11.763850 | 7 | 0 | 0.003447 | 3.417532 | 0.007280 |
| 37 | success | success_lift_ball | 1049 | 0.080353 | 11.761585 | 7 | 0 | 0.003449 | 3.414909 | 0.007553 |
| 38 | success | success_lift_ball | 1045 | 0.080120 | 11.759069 | 7 | 0 | 0.003443 | 3.390825 | 0.007429 |
| 39 | success | success_lift_ball | 1056 | 0.080082 | 11.767821 | 5 | 0 | 0.002829 | 3.399516 | 0.007309 |
| 40 | success | success_lift_ball | 1049 | 0.080726 | 11.765337 | 7 | 0 | 0.003449 | 3.416232 | 0.007280 |
| 41 | success | success_lift_ball | 1049 | 0.080568 | 11.763859 | 7 | 0 | 0.003441 | 3.414789 | 0.007269 |
| 42 | success | success_lift_ball | 1049 | 0.080349 | 11.761565 | 7 | 0 | 0.003450 | 3.414031 | 0.007272 |
| 43 | success | success_lift_ball | 1044 | 0.080641 | 11.764304 | 7 | 0 | 0.003442 | 3.384130 | 0.007448 |
| 44 | success | success_lift_ball | 1048 | 0.080319 | 11.767560 | 7 | 0 | 0.003065 | 3.425825 | 0.007796 |
| 45 | success | success_lift_ball | 1046 | 0.080977 | 11.768784 | 7 | 0 | 0.003489 | 3.403069 | 0.007347 |
| 46 | success | success_lift_ball | 1045 | 0.080305 | 11.761103 | 7 | 0 | 0.003438 | 3.400649 | 0.007393 |
| 47 | success | success_lift_ball | 1045 | 0.080482 | 11.762730 | 7 | 0 | 0.003441 | 3.398033 | 0.007489 |
| 48 | success | success_lift_ball | 1044 | 0.080064 | 11.758509 | 7 | 0 | 0.003439 | 3.396289 | 0.007545 |
| 49 | success | success_lift_ball | 1064 | 0.080676 | 11.771868 | 7 | 0 | 0.003178 | 3.496977 | 0.007296 |
| 50 | success | success_lift_ball | 1061 | 0.080533 | 11.773449 | 5 | 0 | 0.002423 | 3.430824 | 0.007489 |
| 51 | success | success_lift_ball | 1061 | 0.080425 | 11.772294 | 6 | 0 | 0.002369 | 3.430088 | 0.007472 |
| 52 | success | success_lift_ball | 1059 | 0.080431 | 11.771815 | 5 | 0 | 0.002531 | 3.423097 | 0.007457 |
| 53 | success | success_lift_ball | 1059 | 0.080273 | 11.770409 | 5 | 0 | 0.002624 | 3.425811 | 0.007466 |
| 54 | success | success_lift_ball | 1073 | 0.080553 | 11.774285 | 9 | 0 | 0.002294 | 3.431153 | 0.007259 |
| 55 | success | success_lift_ball | 1053 | 0.080410 | 11.768330 | 7 | 0 | 0.003152 | 3.427396 | 0.007269 |
| 56 | success | success_lift_ball | 1044 | 0.080085 | 11.763905 | 6 | 0 | 0.003292 | 3.412567 | 0.007343 |
| 57 | success | success_lift_ball | 1044 | 0.080672 | 11.764625 | 7 | 0 | 0.003452 | 3.412420 | 0.007398 |
| 58 | success | success_lift_ball | 1050 | 0.080783 | 11.772867 | 6 | 0 | 0.003201 | 3.398058 | 0.007400 |
| 59 | success | success_lift_ball | 1057 | 0.080164 | 11.768757 | 5 | 0 | 0.002706 | 3.402741 | 0.007319 |
| 60 | success | success_lift_ball | 1053 | 0.080232 | 11.766531 | 7 | 0 | 0.003134 | 3.422885 | 0.007253 |
| 61 | success | success_lift_ball | 1049 | 0.080577 | 11.763850 | 7 | 0 | 0.003447 | 3.417532 | 0.007280 |
| 62 | success | success_lift_ball | 1049 | 0.080353 | 11.761585 | 7 | 0 | 0.003449 | 3.414909 | 0.007553 |
| 63 | success | success_lift_ball | 1045 | 0.080120 | 11.759069 | 7 | 0 | 0.003443 | 3.390825 | 0.007429 |
| 64 | success | success_lift_ball | 1056 | 0.080082 | 11.767821 | 5 | 0 | 0.002829 | 3.399516 | 0.007309 |
| 65 | success | success_lift_ball | 1049 | 0.080726 | 11.765337 | 7 | 0 | 0.003449 | 3.416232 | 0.007280 |
| 66 | success | success_lift_ball | 1049 | 0.080568 | 11.763859 | 7 | 0 | 0.003441 | 3.414789 | 0.007269 |
| 67 | success | success_lift_ball | 1049 | 0.080349 | 11.761565 | 7 | 0 | 0.003450 | 3.414031 | 0.007272 |
| 68 | success | success_lift_ball | 1044 | 0.080641 | 11.764304 | 7 | 0 | 0.003442 | 3.384130 | 0.007448 |
| 69 | success | success_lift_ball | 1048 | 0.080319 | 11.767560 | 7 | 0 | 0.003065 | 3.425825 | 0.007796 |
| 70 | success | success_lift_ball | 1046 | 0.080977 | 11.768784 | 7 | 0 | 0.003489 | 3.403069 | 0.007347 |
| 71 | success | success_lift_ball | 1045 | 0.080305 | 11.761103 | 7 | 0 | 0.003438 | 3.400649 | 0.007393 |
| 72 | success | success_lift_ball | 1045 | 0.080482 | 11.762730 | 7 | 0 | 0.003441 | 3.398033 | 0.007489 |
| 73 | success | success_lift_ball | 1044 | 0.080064 | 11.758509 | 7 | 0 | 0.003439 | 3.396289 | 0.007545 |
| 74 | success | success_lift_ball | 1064 | 0.080676 | 11.771868 | 7 | 0 | 0.003178 | 3.496977 | 0.007296 |

## Interpretation

- This is the online rollout gate for the first BC smoke checkpoint.
- PASS/PARTIAL here still does not promote the model to the maintained project baseline.
- If this report is FAIL, inspect action scaling, phase features, and dataset coverage before collecting larger data.
