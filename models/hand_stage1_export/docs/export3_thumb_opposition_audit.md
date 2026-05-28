# Export3 Thumb Opposition Audit

- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_export3.xml`
- Load success: yes
- Ball position: `[0.0, -0.1, 0.21]`
- Old model thumb-ball reference: `0.1549 m`
- Candidate count: 400

## Baseline

- Applied pose: `{'thumb_cmc_abd_joint': 0.0, 'thumb_cmc_flex_joint': 0.0, 'thumb_mcp_joint': 0.0, 'thumb_ip_joint': 0.0}`
- Thumb to ball: 0.170286 m
- Thumb to index: 0.130437 m
- Max penetration: 0.000000 m

## Best Candidates

| Rank | Abd | CMC flex | MCP | IP | Thumb-ball (m) | Thumb-index (m) | Improvement vs old (m) | Penetration (m) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | -0.800 | 0.400 | 0.000 | 1.200 | 0.085822 | 0.053539 | 0.069078 | 0.000000 |
| 2 | -0.800 | 0.400 | 0.000 | 0.800 | 0.087294 | 0.048212 | 0.067606 | 0.000000 |
| 3 | -0.800 | 0.000 | 0.000 | 0.400 | 0.086036 | 0.064447 | 0.068864 | 0.000000 |
| 4 | -0.800 | 0.400 | 0.000 | 0.400 | 0.089716 | 0.049416 | 0.065184 | 0.000000 |
| 5 | -0.800 | 0.800 | 0.000 | 1.200 | 0.092201 | 0.037133 | 0.062699 | 0.000000 |
| 6 | -0.800 | 0.000 | 0.000 | 0.800 | 0.085979 | 0.070289 | 0.068921 | 0.000000 |
| 7 | -0.800 | 0.400 | 0.400 | 1.200 | 0.088641 | 0.057215 | 0.066259 | 0.000000 |
| 8 | -0.800 | 0.000 | 0.000 | 0.000 | 0.087845 | 0.064473 | 0.067055 | 0.000000 |
| 9 | -0.800 | 0.000 | 0.400 | 1.200 | 0.087098 | 0.072517 | 0.067802 | 0.000000 |
| 10 | -0.800 | 0.000 | 0.400 | 0.800 | 0.088371 | 0.068449 | 0.066529 | 0.000000 |
| 11 | -0.800 | 0.000 | 0.000 | 1.200 | 0.087687 | 0.079962 | 0.067213 | 0.000000 |
| 12 | -0.800 | 0.400 | 0.000 | 0.000 | 0.092649 | 0.056572 | 0.062251 | 0.000000 |

## Single Axis Trend

- `thumb_cmc_abd_joint` best applied -0.800: thumb-ball 0.087845 m; worst applied 0.800: 0.230078 m.
- `thumb_cmc_flex_joint` best applied 0.000: thumb-ball 0.170286 m; worst applied 0.800: 0.184931 m.
- `thumb_mcp_joint` best applied 1.200: thumb-ball 0.161682 m; worst applied 0.000: 0.170286 m.
- `thumb_ip_joint` best applied 1.200: thumb-ball 0.164778 m; worst applied 0.000: 0.170286 m.

## Rendered Candidate Views

- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb\baseline_full.png` camera=`full_hand_with_ball` mean_pixel=35.47
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb\baseline_thumb.png` camera=`thumb_root_closeup` mean_pixel=66.05
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb\baseline_palm.png` camera=`palm` mean_pixel=56.08
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb\candidate_01_abd_m0d80_cmcflex_p0d40_mcp_p0d00_ip_p1d20_full.png` camera=`full_hand_with_ball` mean_pixel=35.44
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb\candidate_01_abd_m0d80_cmcflex_p0d40_mcp_p0d00_ip_p1d20_thumb.png` camera=`thumb_root_closeup` mean_pixel=64.09
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb\candidate_01_abd_m0d80_cmcflex_p0d40_mcp_p0d00_ip_p1d20_palm.png` camera=`palm` mean_pixel=57.34
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb\candidate_02_abd_m0d80_cmcflex_p0d40_mcp_p0d00_ip_p0d80_full.png` camera=`full_hand_with_ball` mean_pixel=35.43
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb\candidate_02_abd_m0d80_cmcflex_p0d40_mcp_p0d00_ip_p0d80_thumb.png` camera=`thumb_root_closeup` mean_pixel=64.09
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb\candidate_02_abd_m0d80_cmcflex_p0d40_mcp_p0d00_ip_p0d80_palm.png` camera=`palm` mean_pixel=57.34
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb\candidate_03_abd_m0d80_cmcflex_p0d00_mcp_p0d00_ip_p0d40_full.png` camera=`full_hand_with_ball` mean_pixel=35.43
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb\candidate_03_abd_m0d80_cmcflex_p0d00_mcp_p0d00_ip_p0d40_thumb.png` camera=`thumb_root_closeup` mean_pixel=59.95
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb\candidate_03_abd_m0d80_cmcflex_p0d00_mcp_p0d00_ip_p0d40_palm.png` camera=`palm` mean_pixel=56.08
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb\candidate_04_abd_m0d80_cmcflex_p0d40_mcp_p0d00_ip_p0d40_full.png` camera=`full_hand_with_ball` mean_pixel=35.43
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb\candidate_04_abd_m0d80_cmcflex_p0d40_mcp_p0d00_ip_p0d40_thumb.png` camera=`thumb_root_closeup` mean_pixel=64.09
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb\candidate_04_abd_m0d80_cmcflex_p0d40_mcp_p0d00_ip_p0d40_palm.png` camera=`palm` mean_pixel=57.34
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb\candidate_05_abd_m0d80_cmcflex_p0d80_mcp_p0d00_ip_p1d20_full.png` camera=`full_hand_with_ball` mean_pixel=35.45
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb\candidate_05_abd_m0d80_cmcflex_p0d80_mcp_p0d00_ip_p1d20_thumb.png` camera=`thumb_root_closeup` mean_pixel=63.16
- `D:\tendon_project\simulations\models\hand_stage1_export\docs\visual_checks_export3_thumb\candidate_05_abd_m0d80_cmcflex_p0d80_mcp_p0d00_ip_p1d20_palm.png` camera=`palm` mean_pixel=57.52

## Interpretation

- Best export3 candidate thumb-ball distance is 0.0858 m, compared with old reference 0.1549 m.
- Thumb-to-ball distance improves strongly against the old model reference.
- Metric-wise this is a partial opposition candidate.
- Do not edit axes automatically; use this report to decide what to inspect in SolidWorks.

## Visual Judgment

- Metric candidates visibly move the thumb from the palm side toward the ball compared with baseline.
- The best views are a partial improvement: the thumb is closer to the ball/index side, but it does not yet form a clean Shadow-like opposition clamp around the ball.
- No obvious fly-away or severe visual break is visible in the rendered best candidates.
- Treat export3 thumb as improved enough for scripted smoke tests, not as final opposition kinematics.
- Requested negative `thumb_cmc_flex_joint` values are clamped by the exported joint range; this is recorded in requested/applied pose fields.
