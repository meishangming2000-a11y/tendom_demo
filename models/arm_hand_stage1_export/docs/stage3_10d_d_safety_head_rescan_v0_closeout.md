# Stage3.10D-D Safety Head Rescan v0 Closeout

- 生成时间：`2026-06-09T03:09:46`
- 状态：`PASS`
- D-B v1 rescan：`PASS`
- 新增 stress pass：`12 / 12`
- 边界：仍是 MuJoCo scripted arm/wrist + learned hand/fingers + safety/fallback；不是 full-action ACT/DP，也不是硬件。

## 做了什么

D-D 把 D-C 的 safety head 用回 D-B v1，并补了两个新压力点：初始 `depth_noise_5mm` 与最终 `false_positive_blob`。同时保留 `combined_hard` 作为失败边界，用来确认视觉系统在过强初始污染下会拒绝，而不是盲目抓取。

## D-B v1 复扫

- records：`100`
- mean evaluable F1：`1.000000`
- false failure on hold-safe：`0`
- missed failure/blocker：`0`

## 新增 stress cases

| case | 含义 | 状态 | 成功 | safety-head 结果 |
| --- | --- | --- | ---: | --- |
| `initial_depthnoise5_pose005` | 新增：初始 depth noise 5mm + 5mm 位姿噪声 | `PASS` | `6 / 6` | `missed_failure=0, unsafe_hold_safe=0, false_failure=0` |
| `final_falseblob_occlusionaware_pose005` | 新增：最终 false-positive blob + occlusion-aware 验收 | `PASS` | `6 / 6` | `missed_failure=0, unsafe_hold_safe=0, false_failure=0` |
| `initial_combinedhard_pose003_boundary` | 失败边界：初始 combined_hard + 3mm 位姿噪声 | `PARTIAL` | `1 / 2` | `missed_failure=0, unsafe_hold_safe=0, false_failure=0` |

## 判断

- `stage3_10d_d_ready_for_e`：`True`
- `depth_noise_5mm` 之前会让捏持初始视觉失败；修补 noisy estimator 的 median-depth fallback 后，小基准通过。
- `false_positive_blob` 最终视觉会被 strict confidence 拒绝，但 occlusion-aware 视觉/触觉融合能正确接住。
- `combined_hard` 初始视觉仍失败，这是合理边界：mask retention 约半数、false positive 与深度噪声同时存在时，系统宁可拒绝，不应放宽阈值硬抓。

## 如果成功

进入 Stage3.10E：整理 Stage3.10 的最终边界、可复现命令、demo/report 索引和下一阶段计划。

## 如果失败

如果后续要攻克 `combined_hard`，不要放宽抓取成功阈值；应另开更强视觉路线，例如多相机一致性、时序滤波、显式背景/false-positive 分割或训练式 pose estimator。
