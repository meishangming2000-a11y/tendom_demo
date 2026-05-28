# Thumb Opposition Audit

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_visual_clean_collision_proxy.xml`
- Load success: yes
- Ball position: `[0.0, -0.1, 0.195]`

## Baseline

- Pose: `{'thumb_cmc_joint': 0.0, 'thumb_mcp_joint': 0.0, 'thumb_ip_joint': 0.0}`
- Thumb to ball: 0.170603 m
- Thumb to index: 0.130438 m

## Single Axis Sweep

### thumb_cmc_joint

| Value | Thumb to ball (m) | Thumb to index (m) |
|---:|---:|---:|
| -0.800 | 0.168268 | 0.157645 |
| -0.400 | 0.168938 | 0.137992 |
| 0.000 | 0.170603 | 0.130438 |
| 0.400 | 0.172976 | 0.138163 |
| 0.800 | 0.175663 | 0.157921 |

### thumb_mcp_joint

| Value | Thumb to ball (m) | Thumb to index (m) |
|---:|---:|---:|
| 0.000 | 0.170603 | 0.130438 |
| 0.400 | 0.168786 | 0.132974 |
| 0.800 | 0.164720 | 0.139608 |
| 1.200 | 0.158907 | 0.148840 |

### thumb_ip_joint

| Value | Thumb to ball (m) | Thumb to index (m) |
|---:|---:|---:|
| 0.000 | 0.170603 | 0.130438 |
| 0.400 | 0.170196 | 0.130907 |
| 0.800 | 0.167867 | 0.132434 |
| 1.200 | 0.163914 | 0.134749 |

## Best Combined Candidates

| Rank | CMC | MCP | IP | Thumb-ball (m) | Thumb-index (m) | Score |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | -0.800 | 1.200 | 0.000 | 0.154947 | 0.135203 | 0.188748 |
| 2 | -0.400 | 1.200 | 0.000 | 0.156733 | 0.136815 | 0.190937 |
| 3 | -0.800 | 1.200 | 0.400 | 0.157542 | 0.135582 | 0.191438 |
| 4 | -0.400 | 1.200 | 0.400 | 0.159250 | 0.133970 | 0.192742 |
| 5 | -0.400 | 1.200 | 1.200 | 0.159722 | 0.132859 | 0.192937 |
| 6 | -0.800 | 1.200 | 0.800 | 0.158755 | 0.137940 | 0.193240 |
| 7 | -0.400 | 1.200 | 0.800 | 0.160292 | 0.132561 | 0.193432 |
| 8 | -0.800 | 1.200 | 1.200 | 0.158426 | 0.141819 | 0.193880 |
| 9 | -0.800 | 0.800 | 0.000 | 0.160917 | 0.137407 | 0.195269 |
| 10 | -0.400 | 0.800 | 0.000 | 0.162507 | 0.131899 | 0.195482 |
| 11 | 0.000 | 1.200 | 1.200 | 0.161719 | 0.136398 | 0.195819 |
| 12 | 0.000 | 1.200 | 0.000 | 0.158907 | 0.148840 | 0.196117 |

## Rendered Candidate Views

- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_thumb_opposition\baseline_full.png` camera=`full_hand_with_ball` mean_pixel=32.25
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_thumb_opposition\baseline_thumb.png` camera=`thumb_root_closeup` mean_pixel=75.47
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_thumb_opposition\candidate_01_cmc_m0d80_mcp_p1d20_ip_p0d00_full.png` camera=`full_hand_with_ball` mean_pixel=32.24
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_thumb_opposition\candidate_01_cmc_m0d80_mcp_p1d20_ip_p0d00_thumb.png` camera=`thumb_root_closeup` mean_pixel=76.75
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_thumb_opposition\candidate_02_cmc_m0d40_mcp_p1d20_ip_p0d00_full.png` camera=`full_hand_with_ball` mean_pixel=32.25
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_thumb_opposition\candidate_02_cmc_m0d40_mcp_p1d20_ip_p0d00_thumb.png` camera=`thumb_root_closeup` mean_pixel=75.66
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_thumb_opposition\candidate_03_cmc_m0d80_mcp_p1d20_ip_p0d40_full.png` camera=`full_hand_with_ball` mean_pixel=32.24
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_thumb_opposition\candidate_03_cmc_m0d80_mcp_p1d20_ip_p0d40_thumb.png` camera=`thumb_root_closeup` mean_pixel=76.75
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_thumb_opposition\candidate_04_cmc_m0d40_mcp_p1d20_ip_p0d40_full.png` camera=`full_hand_with_ball` mean_pixel=32.24
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_thumb_opposition\candidate_04_cmc_m0d40_mcp_p1d20_ip_p0d40_thumb.png` camera=`thumb_root_closeup` mean_pixel=75.66
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_thumb_opposition\candidate_05_cmc_m0d40_mcp_p1d20_ip_p1d20_full.png` camera=`full_hand_with_ball` mean_pixel=32.24
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_thumb_opposition\candidate_05_cmc_m0d40_mcp_p1d20_ip_p1d20_thumb.png` camera=`thumb_root_closeup` mean_pixel=75.66
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_thumb_opposition\candidate_06_cmc_m0d80_mcp_p1d20_ip_p0d80_full.png` camera=`full_hand_with_ball` mean_pixel=32.24
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_thumb_opposition\candidate_06_cmc_m0d80_mcp_p1d20_ip_p0d80_thumb.png` camera=`thumb_root_closeup` mean_pixel=76.75
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_thumb_opposition\candidate_07_cmc_m0d40_mcp_p1d20_ip_p0d80_full.png` camera=`full_hand_with_ball` mean_pixel=32.25
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_thumb_opposition\candidate_07_cmc_m0d40_mcp_p1d20_ip_p0d80_thumb.png` camera=`thumb_root_closeup` mean_pixel=75.66
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_thumb_opposition\candidate_08_cmc_m0d80_mcp_p1d20_ip_p1d20_full.png` camera=`full_hand_with_ball` mean_pixel=32.27
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_thumb_opposition\candidate_08_cmc_m0d80_mcp_p1d20_ip_p1d20_thumb.png` camera=`thumb_root_closeup` mean_pixel=76.75

## Interpretation

- Best scanned thumb pose reduces thumb-to-ball distance from 0.1706 m to 0.1549 m.
- thumb_cmc_joint: best single-axis value -0.800 gives thumb-to-ball 0.1683 m; worst value 0.800 gives 0.1757 m.
- thumb_mcp_joint: best single-axis value 1.200 gives thumb-to-ball 0.1589 m; worst value 0.000 gives 0.1706 m.
- thumb_ip_joint: best single-axis value 1.200 gives thumb-to-ball 0.1639 m; worst value 0.000 gives 0.1706 m.
- Even the best scanned pose leaves the thumb tip far from the ball; thumb opposition is not solved in the current joint frame/axis setup.
- Recommendation: manually inspect thumb_cmc_axis, thumb_mcp_axis, and thumb_ip_axis in SolidWorks/URDF before changing MJCF axes.

## Notes

- This is a static kinematic audit using direct qpos only for measurement; it does not edit joint axes or names.
- Four long fingers are held open to isolate thumb CMC/MCP/IP motion.
- A small thumb-to-ball improvement without crossing the palm is not sufficient evidence to change axes automatically.
