# Export3 Thumb Limit Tuning Audit

Status: experimental thumb-limit grid search. No CAD/STL/tree/name changes.

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3_thumb_limit_tuned.xml`
- Ball position: `[0.0, -0.1, 0.21]`
- Candidate count: 2430
- Old export3 best thumb-ball reference: `0.0858 m`
- Context: four long fingers held at scripted close pose while scanning thumb pose.

## Best By Score

| Rank | Abd | CMC flex | MCP | IP | Score | Thumb-ball | Thumb-index | Thumb-middle | Contacts | Penetration | Penalty |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | -1.200 | 0.600 | -0.200 | 1.200 | 0.177961 | 0.034260 | 0.028973 | 0.045357 | 4 | 0.017894 | 0.000000 |
| 2 | -1.200 | 0.600 | -0.200 | 0.800 | 0.182124 | 0.036814 | 0.031999 | 0.045742 | 4 | 0.017894 | 0.000000 |
| 3 | -1.200 | 0.600 | 0.000 | 1.200 | 0.184691 | 0.037415 | 0.034897 | 0.047812 | 4 | 0.017894 | 0.000000 |
| 4 | -1.200 | 0.300 | -0.200 | 0.800 | 0.186268 | 0.037468 | 0.036312 | 0.051079 | 4 | 0.017894 | 0.000000 |
| 5 | -1.200 | 0.300 | -0.200 | 0.400 | 0.186567 | 0.037667 | 0.037022 | 0.050058 | 4 | 0.017894 | 0.000000 |
| 6 | -1.200 | 0.900 | -0.200 | 1.200 | 0.188823 | 0.041597 | 0.035279 | 0.046850 | 4 | 0.017894 | 0.000000 |
| 7 | -1.200 | 0.300 | 0.000 | 0.800 | 0.189790 | 0.039088 | 0.039677 | 0.051956 | 4 | 0.017894 | 0.000000 |
| 8 | -1.200 | 0.300 | 0.000 | 1.200 | 0.192132 | 0.040127 | 0.041082 | 0.054358 | 4 | 0.017894 | 0.000000 |
| 9 | -1.200 | 0.600 | -0.200 | 0.400 | 0.193427 | 0.042756 | 0.040408 | 0.050372 | 4 | 0.017894 | 0.000000 |
| 10 | -1.200 | 0.600 | 0.000 | 0.800 | 0.194222 | 0.042793 | 0.041474 | 0.051269 | 4 | 0.017894 | 0.000000 |
| 11 | -1.200 | 0.300 | -0.200 | 1.200 | 0.195220 | 0.042087 | 0.042243 | 0.056548 | 4 | 0.017894 | 0.000000 |
| 12 | -1.200 | 0.300 | -0.200 | 0.000 | 0.195916 | 0.042589 | 0.043960 | 0.053890 | 4 | 0.017894 | 0.000000 |
| 13 | -1.200 | 0.300 | 0.000 | 0.400 | 0.197192 | 0.043211 | 0.044918 | 0.054590 | 4 | 0.017894 | 0.000000 |
| 14 | -1.200 | 0.900 | 0.000 | 1.200 | 0.200409 | 0.047183 | 0.044351 | 0.052702 | 4 | 0.017894 | 0.000000 |
| 15 | -1.200 | 0.000 | -0.200 | 0.000 | 0.201434 | 0.044660 | 0.048321 | 0.058957 | 4 | 0.017894 | 0.000000 |
| 16 | -1.200 | 0.000 | -0.200 | 0.400 | 0.201766 | 0.044971 | 0.047873 | 0.059939 | 4 | 0.017894 | 0.000000 |
| 17 | -1.200 | 0.900 | -0.200 | 0.800 | 0.202570 | 0.048990 | 0.044926 | 0.052971 | 4 | 0.017894 | 0.000000 |
| 18 | -1.200 | 0.000 | 0.000 | 0.400 | 0.202609 | 0.045262 | 0.049168 | 0.059550 | 4 | 0.017894 | 0.000000 |
| 19 | -1.200 | 0.300 | -0.200 | -0.200 | 0.202794 | 0.046222 | 0.048783 | 0.057224 | 4 | 0.017894 | 0.000000 |
| 20 | -1.200 | 0.300 | 0.400 | 1.200 | 0.204674 | 0.046663 | 0.050577 | 0.059391 | 4 | 0.017894 | 0.000000 |

## Best By Thumb-Ball Distance

| Rank | Abd | CMC flex | MCP | IP | Thumb-ball | Thumb-index | Thumb-middle | Score | Contacts | Penetration |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | -1.200 | 0.600 | -0.200 | 1.200 | 0.034260 | 0.028973 | 0.045357 | 0.177961 | 4 | 0.017894 |
| 2 | -1.200 | 0.600 | -0.200 | 0.800 | 0.036814 | 0.031999 | 0.045742 | 0.182124 | 4 | 0.017894 |
| 3 | -1.200 | 0.600 | 0.000 | 1.200 | 0.037415 | 0.034897 | 0.047812 | 0.184691 | 4 | 0.017894 |
| 4 | -1.200 | 0.300 | -0.200 | 0.800 | 0.037468 | 0.036312 | 0.051079 | 0.186268 | 4 | 0.017894 |
| 5 | -1.200 | 0.300 | -0.200 | 0.400 | 0.037667 | 0.037022 | 0.050058 | 0.186567 | 4 | 0.017894 |
| 6 | -1.200 | 0.300 | 0.000 | 0.800 | 0.039088 | 0.039677 | 0.051956 | 0.189790 | 4 | 0.017894 |
| 7 | -1.200 | 0.300 | 0.000 | 1.200 | 0.040127 | 0.041082 | 0.054358 | 0.192132 | 4 | 0.017894 |
| 8 | -1.200 | 0.900 | -0.200 | 1.200 | 0.041597 | 0.035279 | 0.046850 | 0.188823 | 4 | 0.017894 |
| 9 | -1.200 | 0.300 | -0.200 | 1.200 | 0.042087 | 0.042243 | 0.056548 | 0.195220 | 4 | 0.017894 |
| 10 | -1.200 | 0.300 | -0.200 | 0.000 | 0.042589 | 0.043960 | 0.053890 | 0.195916 | 4 | 0.017894 |
| 11 | -1.200 | 0.600 | -0.200 | 0.400 | 0.042756 | 0.040408 | 0.050372 | 0.193427 | 4 | 0.017894 |
| 12 | -1.200 | 0.600 | 0.000 | 0.800 | 0.042793 | 0.041474 | 0.051269 | 0.194222 | 4 | 0.017894 |
| 13 | -1.200 | 0.300 | 0.000 | 0.400 | 0.043211 | 0.044918 | 0.054590 | 0.197192 | 4 | 0.017894 |
| 14 | -1.200 | 0.000 | -0.200 | 0.000 | 0.044660 | 0.048321 | 0.058957 | 0.201434 | 4 | 0.017894 |
| 15 | -1.200 | 0.000 | -0.200 | 0.400 | 0.044971 | 0.047873 | 0.059939 | 0.201766 | 4 | 0.017894 |
| 16 | -1.200 | 0.000 | 0.000 | 0.400 | 0.045262 | 0.049168 | 0.059550 | 0.202609 | 4 | 0.017894 |
| 17 | -1.200 | 0.300 | -0.200 | -0.200 | 0.046222 | 0.048783 | 0.057224 | 0.202794 | 4 | 0.017894 |
| 18 | -1.200 | 0.000 | -0.200 | -0.200 | 0.046576 | 0.050927 | 0.060435 | 0.205022 | 4 | 0.017894 |
| 19 | -1.200 | 0.300 | 0.400 | 1.200 | 0.046663 | 0.050577 | 0.059391 | 0.204674 | 4 | 0.017894 |
| 20 | -1.200 | 0.000 | 0.000 | 0.800 | 0.046878 | 0.050630 | 0.061979 | 0.205562 | 4 | 0.017894 |

## Single Axis Trend

- `thumb_cmc_abd_joint` best -1.200: thumb-ball 0.049145 m; worst 1.200: 0.247319 m.
- `thumb_cmc_flex_joint` best -1.200: thumb-ball 0.148043 m; worst 1.200: 0.188892 m.
- `thumb_mcp_joint` best 1.400: thumb-ball 0.159324 m; worst -0.200: 0.170332 m.
- `thumb_ip_joint` best 1.200: thumb-ball 0.164778 m; worst 0.000: 0.170286 m.

## Renders

- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\baseline_full.png` camera=`full_hand_with_ball` mean_pixel=33.54
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\baseline_thumb.png` camera=`thumb_root_closeup` mean_pixel=65.89
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\baseline_palm.png` camera=`palm` mean_pixel=58.42
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_01_abd_m1d20_cmcflex_p0d60_mcp_m0d20_ip_p1d20_full.png` camera=`full_hand_with_ball` mean_pixel=33.32
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_01_abd_m1d20_cmcflex_p0d60_mcp_m0d20_ip_p1d20_thumb.png` camera=`thumb_root_closeup` mean_pixel=62.37
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_01_abd_m1d20_cmcflex_p0d60_mcp_m0d20_ip_p1d20_palm.png` camera=`palm` mean_pixel=59.84
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_02_abd_m1d20_cmcflex_p0d60_mcp_m0d20_ip_p0d80_full.png` camera=`full_hand_with_ball` mean_pixel=33.33
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_02_abd_m1d20_cmcflex_p0d60_mcp_m0d20_ip_p0d80_thumb.png` camera=`thumb_root_closeup` mean_pixel=62.37
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_02_abd_m1d20_cmcflex_p0d60_mcp_m0d20_ip_p0d80_palm.png` camera=`palm` mean_pixel=59.84
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_03_abd_m1d20_cmcflex_p0d60_mcp_p0d00_ip_p1d20_full.png` camera=`full_hand_with_ball` mean_pixel=33.33
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_03_abd_m1d20_cmcflex_p0d60_mcp_p0d00_ip_p1d20_thumb.png` camera=`thumb_root_closeup` mean_pixel=62.37
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_03_abd_m1d20_cmcflex_p0d60_mcp_p0d00_ip_p1d20_palm.png` camera=`palm` mean_pixel=59.84
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_04_abd_m1d20_cmcflex_p0d30_mcp_m0d20_ip_p0d80_full.png` camera=`full_hand_with_ball` mean_pixel=33.33
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_04_abd_m1d20_cmcflex_p0d30_mcp_m0d20_ip_p0d80_thumb.png` camera=`thumb_root_closeup` mean_pixel=60.26
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_04_abd_m1d20_cmcflex_p0d30_mcp_m0d20_ip_p0d80_palm.png` camera=`palm` mean_pixel=58.48
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_05_abd_m1d20_cmcflex_p0d30_mcp_m0d20_ip_p0d40_full.png` camera=`full_hand_with_ball` mean_pixel=33.33
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_05_abd_m1d20_cmcflex_p0d30_mcp_m0d20_ip_p0d40_thumb.png` camera=`thumb_root_closeup` mean_pixel=60.26
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_05_abd_m1d20_cmcflex_p0d30_mcp_m0d20_ip_p0d40_palm.png` camera=`palm` mean_pixel=58.48
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_06_abd_m1d20_cmcflex_p0d90_mcp_m0d20_ip_p1d20_full.png` camera=`full_hand_with_ball` mean_pixel=33.50
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_06_abd_m1d20_cmcflex_p0d90_mcp_m0d20_ip_p1d20_thumb.png` camera=`thumb_root_closeup` mean_pixel=61.42
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_06_abd_m1d20_cmcflex_p0d90_mcp_m0d20_ip_p1d20_palm.png` camera=`palm` mean_pixel=60.58
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_07_abd_m1d20_cmcflex_p0d30_mcp_p0d00_ip_p0d80_full.png` camera=`full_hand_with_ball` mean_pixel=33.33
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_07_abd_m1d20_cmcflex_p0d30_mcp_p0d00_ip_p0d80_thumb.png` camera=`thumb_root_closeup` mean_pixel=60.73
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_07_abd_m1d20_cmcflex_p0d30_mcp_p0d00_ip_p0d80_palm.png` camera=`palm` mean_pixel=58.52
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_08_abd_m1d20_cmcflex_p0d30_mcp_p0d00_ip_p1d20_full.png` camera=`full_hand_with_ball` mean_pixel=33.33
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_08_abd_m1d20_cmcflex_p0d30_mcp_p0d00_ip_p1d20_thumb.png` camera=`thumb_root_closeup` mean_pixel=60.73
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_08_abd_m1d20_cmcflex_p0d30_mcp_p0d00_ip_p1d20_palm.png` camera=`palm` mean_pixel=58.52
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_09_abd_m1d20_cmcflex_p0d60_mcp_m0d20_ip_p0d40_full.png` camera=`full_hand_with_ball` mean_pixel=33.35
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_09_abd_m1d20_cmcflex_p0d60_mcp_m0d20_ip_p0d40_thumb.png` camera=`thumb_root_closeup` mean_pixel=62.37
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_09_abd_m1d20_cmcflex_p0d60_mcp_m0d20_ip_p0d40_palm.png` camera=`palm` mean_pixel=59.84
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_10_abd_m1d20_cmcflex_p0d60_mcp_p0d00_ip_p0d80_full.png` camera=`full_hand_with_ball` mean_pixel=33.34
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_10_abd_m1d20_cmcflex_p0d60_mcp_p0d00_ip_p0d80_thumb.png` camera=`thumb_root_closeup` mean_pixel=62.37
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb_limit_tuning\candidate_10_abd_m1d20_cmcflex_p0d60_mcp_p0d00_ip_p0d80_palm.png` camera=`palm` mean_pixel=59.84

## Interpretation

- Best score pose thumb-ball is 0.0343 m and thumb-index is 0.0290 m.
- Best pure thumb-ball pose reaches 0.0343 m, compared with old export3 reference 0.0858 m.
- The expanded limits found poses inside the 0.06 m thumb-ball target.
- Thumb-ball distance improves materially against the old export3 best.
- This is scripted pose search only; no learning or model-structure change was used.

## Visual Judgment

- Rendered full/top/palm views show a clear improvement over the old export3 thumb pose: the thumb tip moves to the opposite side of the ball and forms a visible pinch/wrap with index and middle fingers.
- The best scored pose enters the 0.06 m thumb-ball target region; thumb-ball is about 0.0343 m and thumb-index is about 0.0290 m in the static audit.
- The best pose uses the expanded bounds at thumb_cmc_abd=-1.2, thumb_mcp=-0.2, and thumb_ip=1.2, so these should remain experimental until SolidWorks confirms the extreme positions are mechanically acceptable.
- Static audit penetration is dominated by four-finger proxy contacts with the ball rather than direct thumb collision; the dynamic position-control grasp run reduced hold penetration to about 0.0066 m.
- No obvious thumb fly-away, mirrored motion, or severe visual flip was visible in the saved candidate screenshots.
- Recommendation: use this pose for scripted Shadow-style smoke tests, but do not promote it to training or final mechanical limits yet.
