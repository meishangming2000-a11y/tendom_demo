# Next Stage Handoff Prompt

Continue `tendon_project` from the closed Stage1 arm-hand virtual prototype baseline.

Current baseline:

- Model: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\arm_hand_export4_collision_proxy_v2.xml`
- Lift scene: `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_lift_ball_demo.xml`
- Closeout report: `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\stage1_virtual_prototype_closeout.md`
- Baseline manifest: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\current_baseline_manifest.json`
- Default-posture lift demo:
  `python D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_lift_ball_from_default.py`

Latest known result:

- default-posture lift demo status: `PASS`
- pure physics final lift: about `0.158 m`
- ball-hand contacts: `7`
- max penetration: about `0.0034 m`

Stage2 kickoff status:

- Task API: `D:\tendon_project\simulations\models\arm_hand_stage1_export\arm_hand_stage1_task_api.py`
- Task API report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_task_api_report.md`
- Task API default scene: collision proxy v2 with ball
- Action dim: `26`
- Observation dim: `124`
- Ball-pose sweep script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_v2_ball_pose_sweep.py`
- Ball-pose sweep report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_ball_pose_sweep_report.md`
- Default sweep: x/y offsets `[-0.015, 0.0, 0.015]`, z offset `[0.0]`
- Default sweep result: `9 / 9` PASS
- Task contract script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\write_arm_hand_stage1_v2_task_contract.py`
- Task contract report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_task_contract.md`
- Task contract version: `stage2_lift_ball_v0_1`
- Observation/action/reward/done status: frozen for dataset-v0 collection
- Dataset v0:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0.npz`
- Dataset v0 collection script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\collect_arm_hand_stage1_v2_dataset_v0.py`
- Dataset v0 report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_report.md`
- Dataset v0 replay QA script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\replay_arm_hand_stage1_v2_dataset_v0.py`
- Dataset v0 replay QA report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_replay_report.md`
- Dataset v0 result: `9 episodes / 9067 rows`, `9 / 9` success, replay QA `PASS`
- Training readiness review:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_training_readiness_report.md`
- BC smoke training script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\train_arm_hand_stage1_v2_bc_smoke.py`
- BC smoke checkpoint:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_smoke.pth`
- BC smoke train report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_smoke_train_report.md`
- BC smoke eval script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\eval_arm_hand_stage1_v2_bc_smoke.py`
- BC smoke eval report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_smoke_eval_report.md`
- BC smoke demo script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_stage1_v2_bc_smoke.py`
- BC smoke demo video:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_smoke\bc_smoke_policy_demo.mp4`
- Latest BC smoke result: readiness `PASS`; phase-only schedule-conditioned BC train final val MSE about `5.43e-7`; online eval `9 / 9` success; demo episode 4 success.
- Repair note: the first obs+phase BC attempt fit offline but failed online rollout (`0 / 9` success), so the retained smoke checkpoint uses `phase_only` features. This is a schedule-conditioned smoke artifact, not a robust closed-loop policy.
- Dataset v0.1:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz`
- Dataset v0.1 collection script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\collect_arm_hand_stage1_v2_dataset_v0_1.py`
- Dataset v0.1 report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_1_report.md`
- Dataset v0.1 replay QA:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_1_replay_report.md`
- Dataset v0.1 result: `75 episodes / 77154 rows`, behavior success `68 / 75`, replay QA `PASS`.
- Dataset v0.1 action semantics: `actions` are applied behavior actions for replay; `expert_actions` are BC labels.
- V0.1 obs+phase selected checkpoint:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_1_obs_phase_strongreg.pth`
- V0.1 obs+phase repair report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_1_obs_phase_repair_report.md`
- V0.1 obs+phase selected eval:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_1_obs_phase_strongreg_smooth_eval_report.md`
- V0.1 obs+phase demo video:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_1_obs_phase\obs_phase_strongreg_policy_demo.mp4`
- Latest v0.1 obs+phase result: raw obs+phase `18 / 75`, regularized `51 / 75`, strong regularization plus smoothing `69 / 75`, matching the phase-only reference on the same v0.1 resets.
- V0.1 failure analysis:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_v0_1_failure_analysis_report.md`
- V0.1 failure diagnosis: the retained obs+phase failures clustered on right-edge offsets and ended as timeout with near-zero lift and zero ball-hand contacts.
- Dataset v0.2:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\arm_hand_stage1_v2_lift_ball_dataset_v0_2.npz`
- Dataset v0.2 collection script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\collect_arm_hand_stage1_v2_dataset_v0_2.py`
- Dataset v0.2 report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_2_report.md`
- Dataset v0.2 replay QA:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_dataset_v0_2_replay_report.md`
- Dataset v0.2 result: `87 episodes / 87773 rows`, behavior success `87 / 87`, replay QA `PASS`.
- Dataset v0.2 recovery modes: `nominal=63`, `right_edge_mid_y=15`, `right_edge_high_y=6`, `right_edge_upper_y=3`.
- V0.2 obs+phase selected checkpoint:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_moderatereg.pth`
- V0.2 obs+phase repair report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_2_obs_phase_repair_report.md`
- V0.2 obs+phase selected eval:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_2_obs_phase_moderatereg_smooth040_eval_report.md`
- V0.2 obs+phase selected eval on v0.1 resets:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_2_obs_phase_moderatereg_on_v0_1_smooth040_eval_report.md`
- V0.2 obs+phase recovered demo video:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_2_obs_phase\obs_phase_moderatereg_recovered_ep09_demo.mp4`
- Latest v0.2 obs+phase result: selected moderate-regularized obs+phase policy reaches `81 / 87` on v0.2 recovery resets and improves the old v0.1 reset score from `69 / 75` to `72 / 75`.
- Remaining v0.2 blocker: the upper-right offset cluster `[0.02, 0.02, 0.0]` and `[0.02, 0.025, 0.0]` still times out with zero ball-hand contacts.
- V0.3 obs+phase training report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_3_obs_phase_training_report.md`
- V0.3 obs+phase selected checkpoint:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright.pth`
- V0.3 obs+phase selected eval:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_3_obs_phase_weighted_upperright_on_v0_2_smooth050_eval_report.md`
- V0.3 obs+phase selected eval on v0.1 resets:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_3_obs_phase_weighted_upperright_on_v0_1_smooth050_eval_report.md`
- V0.3 obs+phase recovered demo:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_3_obs_phase\obs_phase_weighted_upperright_recovered_ep24_demo.mp4`
- Latest v0.3 obs+phase result: weighted upper-right sampling improves the v0.2 recovery-set score from `81 / 87` to `84 / 87` while preserving the old v0.1 reset score at `72 / 75`.
- Remaining v0.3 blocker: with selected smoothing `0.5`, `[0.01, 0.01, 0.0]` still times out with zero ball-hand contacts across profiles.
- V0.4 obs+phase training report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_4_obs_phase_training_report.md`
- V0.4 obs+phase selected checkpoint:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\checkpoints\bc_arm_hand_stage1_v2_lift_ball_dataset_v0_2_obs_phase_weighted_upperright_transition.pth`
- V0.4 obs+phase selected eval:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_4_obs_phase_weighted_upperright_transition_on_v0_2_smooth050_eval_report.md`
- V0.4 obs+phase selected eval on v0.1 resets:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_4_obs_phase_weighted_upperright_transition_on_v0_1_smooth050_eval_report.md`
- V0.4 obs+phase recovered demo:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_4_obs_phase\obs_phase_weighted_transition_recovered_ep18_demo.mp4`
- Latest v0.4 obs+phase result: weighted upper-right plus transition-band sampling reaches `87 / 87` on v0.2 recovery resets and `75 / 75` on old v0.1 resets.
- V0.4 long-hold validation:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_4_hold_validation_report.md`
- V0.4 long-hold eval on v0.2:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_4_freeze_settle180_hold900_min070_recover_on_v0_2_eval_report.md`
- V0.4 long-hold eval on v0.1:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_4_freeze_settle180_hold900_min070_recover_on_v0_1_eval_report.md`
- V0.4 long-hold result: with action smoothing `0.5`, `180` post-success settle steps, freeze-best-settle action, and `900` required hold steps, v0.4 reaches `87 / 87` on v0.2 recovery resets and `75 / 75` on old v0.1 resets.
- V0.4 long-hold demo:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_4_hold\obs_phase_weighted_transition_ep25_freeze_settle180_hold900_demo.mp4`
- V0.4 long-hold demo result: episode `25`, terminal reason `success_lift_hold`, final lift `0.079840 m`, ball-floor contacts after lift `0`, frames `537`.
- V0.4 unseen holdout sweep script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\eval_arm_hand_stage1_v2_bc_holdout_sweep.py`
- V0.4 unseen holdout diagnostic with original smoothing `0.5`:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_4_holdout_sweep_report.md`
- V0.4 unseen holdout diagnostic result: `11 / 12`; failure was `[0.0175, 0.0075, 0.0]` with no-lift timeout.
- V0.4 unseen holdout selected report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v2_bc_v0_4_holdout_sweep_smooth020_report.md`
- V0.4 unseen holdout selected result: with action smoothing `0.2`, `12 / 12` pass, terminal reason `success_lift_hold`, final lift range `0.075788 m` to `0.092617 m`.
- V0.4 unseen holdout demo:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v2_bc_v0_4_holdout\holdout_offset_0175_0075_smooth020_demo.mp4`
- V0.4 unseen holdout demo result: offset `[0.0175, 0.0075, 0.0]`, terminal reason `success_lift_hold`, final lift `0.078270 m`, ball-floor contacts after lift `0`, frames `537`.
- Remaining v0.4 blocker: none on the accepted reset sets or first unseen midpoint holdout; next gate is broader holdout plus reward/termination QA before promotion or RL warm-start.
- V3 pick-place scene:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_pick_place_demo.xml`
- V3 pick-place task contract script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\arm_hand_stage1_v3_pick_place_task_api.py`
- V3 pick-place task contract:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_v3_pick_place_task_contract.md`
- V3 same-platform scripted pick-place demo:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_stage1_v3_pick_place_scripted.py`
- V3 same-platform scripted pick-place demo result: `PASS`, terminal reason `success_pick_place_ball`, final target XY distance `0.003190 m`, stable target steps `1169`, transport floor contacts before release `0`, final ball-hand contacts `0`.
- V3 same-platform scripted pick-place video:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\visual_checks_arm_hand_stage1_v3_pick_place\pick_place_same_platform_scripted_demo.mp4`
- V3 pick-place target sweep script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\run_arm_hand_stage1_v3_pick_place_sweep.py`
- V3 pick-place target-neighborhood sweep result: `25 / 25` PASS for target offsets `[-0.02, -0.01, 0, 0.01, 0.02]` on x/y; max target XY miss `0.031068 m`, stable target steps minimum `545`, transport floor contacts total `0`.
- V3 pick-place wider margin sweep result: `37 / 49` on target offsets `[-0.03..0.03]` x/y; outer-rim failures are `target_miss=9` and `placement_not_stable=3`.
- V3 pick-place status: task scaffold, one scripted pure-physics same-platform demo, and target-label tolerance sweeps are in place; no pick-place dataset/checkpoint is promoted yet.
- Standardized Stage2 run scaffold:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\init_arm_hand_stage1_run.py`
- Stage2 training/run standard:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\arm_hand_stage1_training_run_standard.md`
- V3 pick-place dataset v0.5 run:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_5\20260601_004101_seed000`
- V3 pick-place dataset v0.5:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_5\20260601_004101_seed000\datasets\arm_hand_stage1_v3_pick_place_dataset_v0_5.npz`
- V3 pick-place dataset v0.5 collection result: `3 / 3` success, `10423` rows, obs shape `[10423, 130]`, base obs shape `[10423, 124]`, action shape `[10423, 26]`, fixed target only, profiles `clean_nominal`, `timing_fast_clean`, and `timing_slow_clean`.
- V3 pick-place dataset v0.5 replay QA:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_5\20260601_004101_seed000\eval\replay_qa_report.md`
- V3 pick-place dataset v0.5 replay QA result: `PASS`, shape check `PASS`, replay status `PASS`, dataset gate `PASS`, max obs/next_obs/reward error `0`, success count `3 / 3`, transport floor contacts `0`, final hand contacts `0`, final target XY distances `0.005215 m` to `0.013411 m`.
- V3 pick-place dataset v0.5 self-check: do not collect v0.6 immediately; v0.5 is replay-clean for fixed-target pick-place, so train/eval the first BC policy first and let online policy failures decide the v0.6 content.
- V3 pick-place first BC attempt, `obs_phase_target`:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_5\20260601_004101_seed000\checkpoints\bc_arm_hand_stage1_v3_pick_place_dataset_v0_5_obs_phase_target.pth`
- V3 pick-place `obs_phase_target` offline result: final train MSE `8.01e-6`, final val MSE `5.31e-5`, val action RMSE `0.002244`; online fixed-target eval `FAIL`, terminal reason `timeout`, final target XY distance `12.262183 m`. Diagnosis: low offline loss was not enough; the obs-conditioned policy entered closed-loop OOD and pushed/rolled the ball far away. Keep this as failure evidence, not a selected checkpoint.
- V3 pick-place repaired BC smoke, `phase_only`:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_5\20260601_004101_seed000\checkpoints\bc_arm_hand_stage1_v3_pick_place_dataset_v0_5_phase_only.pth`
- V3 pick-place `phase_only` offline result: final train MSE `2.08e-4`, final val MSE `2.77e-5`, val action RMSE `0.001986`.
- V3 pick-place `phase_only` fixed-target online eval:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_5\20260601_004101_seed000\eval\fixed_target_phase_only_eval_report.md`
- V3 pick-place `phase_only` fixed-target result: `1 / 1 PASS`, terminal reason `success_pick_place_ball`, final target XY distance `0.022262 m`, stable target steps `240`, transport floor contacts `0`, final hand contacts `0`.
- V3 pick-place `phase_only` narrow target-label sweep:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_5\20260601_004101_seed000\eval\narrow_sweep_phase_only_eval_report.md`
- V3 pick-place `phase_only` narrow sweep result: `25 / 25 PASS` for target offsets `[-0.02, -0.01, 0, 0.01, 0.02]` on x/y; target XY distance range `0.003819 m` to `0.030615 m`, mean `0.022446 m`, stable target steps `240` for every episode, transport floor contacts total `0`, final hand contacts max `0`.
- Interpretation: `phase_only` is the selected first pick-place BC smoke checkpoint because it completes fixed-target online pick-place. The narrow sweep is target-label tolerance only; it is not evidence of true target-conditioned transport because v0.5 contains fixed-target data and the selected model does not use dynamic observation or target features.
- V3 pick-place v0.6 repair run:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_6_repair\20260601_011726_seed061`
- V3 pick-place v0.6 repair report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_6_repair\20260601_011726_seed061\eval\final_v0_6_repair_report.md`
- V3 pick-place v0.6 dataset:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_6_repair\20260601_011726_seed061\datasets\arm_hand_stage1_v3_pick_place_dataset_v0_6.npz`
- V3 pick-place v0.6 repair content: added `close_hold=180`, increased lift hold to `220`, increased transport to `960`, added `transport_hold=300`, increased descend to `620`, pre-release settle to `300`, release to `760`, retreat to `380`, and settle to `720`.
- V3 pick-place v0.6 dataset/replay result: collection `3 / 3`, replay QA `PASS`, replay success `3 / 3`, transport floor contacts `0`, final hand contacts `0`.
- V3 pick-place v0.6 selected checkpoint:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_6_repair\20260601_011726_seed061\checkpoints\bc_arm_hand_stage1_v3_pick_place_dataset_v0_6_phase_only.pth`
- V3 pick-place v0.6 `phase_only` training result: final train MSE `2.03e-4`, final val MSE `2.04e-4`, val action RMSE `0.005587`.
- V3 pick-place v0.6 fixed-target final demo:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_6_repair\20260601_011726_seed061\visuals\final_demo_v0_6_phase_only_policy_demo.mp4`
- V3 pick-place v0.6 fixed-target result: with action smoothing `0.2`, `1 / 1 PASS`, terminal reason `success_pick_place_ball`, steps `4392`, final target XY distance `0.030539 m`, stable target steps `240`, transport floor contacts `0`, final hand contacts `0`.
- V3 pick-place v0.6 narrow sweep result: with action smoothing `0.2`, `12 / 25 PARTIAL` on the same 5x5 target-label grid; failures are timeouts/target misses, target XY mean `0.041180 m`, max `0.073649 m`, transport floor contacts total `0`, final hand contacts max `0`.
- V3 pick-place v0.6 diagnosis: the repair solved the fixed-target grasp/transport/release stability symptoms but reduced target-label tolerance compared with v0.5 (`25 / 25`). Do not promote v0.6 as target-general. The next useful repair is target-conditioned transport/descend collection rather than more hold length.
- V3 pick-place 50cm target probe scene:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_pick_place_50cm_probe.xml`
- V3 pick-place 50cm target probe run:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_50cm_probe\20260601_014936_seed062`
- V3 pick-place 50cm target probe report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_50cm_probe\20260601_014936_seed062\eval\target_50cm_probe_report.md`
- V3 pick-place 50cm target probe geometry: initial ball `[0.19022382, 0.187702, -0.06538044]`; target `[-0.06586616075, 0.61714107805, -0.06538044]`; initial XY distance `0.500000 m`. The target pad and target site were both moved in MJCF, so this is a real visual/metric far-target probe.
- V3 pick-place 50cm scripted probe result: existing scripted trajectory `PARTIAL / target_miss`, final target XY `0.448500 m`, transport floor contacts `0`, final hand contacts `0`.
- V3 pick-place 50cm BC probe result: v0.6 `phase_only` checkpoint `FAIL / timeout`, final target XY `0.437410 m`, stable target steps `0`, transport floor contacts `0`, final hand contacts `0`.
- V3 pick-place 50cm visual artifact:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_50cm_probe\20260601_014936_seed062\visuals\bc_v0_6_phase_only_50cm_probe_rendered_policy_demo.mp4`
- V3 pick-place 50cm diagnosis: failure is long-distance placement/path planning, not grasp/drop/release. Do not train BC on this failing far-target rollout. Next step is v0.7 target-conditioned scripted expert with transport/descend arm targets parameterized by `target_center`.
- V3 pick-place v0.7 target-conditioned scene:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\mjcf\scene_arm_hand_export4_pick_place_50cm_v0_7.xml`
- V3 pick-place v0.7 target-conditioned scripted expert:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\demo_arm_hand_stage1_v3_pick_place_target_conditioned.py`
- V3 pick-place v0.7 run:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_7_target_conditioned\20260601_021319_seed063`
- V3 pick-place v0.7 final report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_7_target_conditioned\20260601_021319_seed063\eval\final_v0_7_target_conditioned_report.md`
- V3 pick-place v0.7 target geometry: initial ball `[0.19022382, 0.187702, -0.06538044]`; target `[-0.16332957059327374, -0.16585139059327378, -0.06538044]`; initial-to-target XY distance `0.500000 m`. This target is 50cm away in a reachable `-135 deg` direction.
- V3 pick-place v0.7 scripted result: `PASS`, final target XY `0.022320 m`, stable target steps `1865`, transport floor contacts `0`, final hand contacts `0`.
- V3 pick-place v0.7 dataset:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_7_target_conditioned\20260601_021319_seed063\datasets\arm_hand_stage1_v3_pick_place_dataset_v0_7.npz`
- V3 pick-place v0.7 dataset/replay result: collection `3 / 3`, `17536` rows, replay QA `PASS`, replay success `3 / 3`.
- V3 pick-place v0.7 first BC attempt, `phase_only`:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_7_target_conditioned\20260601_021319_seed063\checkpoints\bc_arm_hand_stage1_v3_pick_place_dataset_v0_7_phase_only.pth`
- V3 pick-place v0.7 first BC result: fixed-target eval `FAIL / timeout`, final target XY `0.328093 m`; diagnosis was release sensitivity after the ball reached the target neighborhood.
- V3 pick-place v0.7 selected BC, `phase_only_trainall`:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_7_target_conditioned\20260601_021319_seed063\checkpoints\bc_arm_hand_stage1_v3_pick_place_dataset_v0_7_phase_only_trainall.pth`
- V3 pick-place v0.7 selected BC result: fixed 50cm target `1 / 1 PASS`, terminal reason `success_pick_place_ball`, steps `6430`, final target XY `0.029014 m`, stable target steps `240`, transport floor contacts `0`, final hand contacts `0`.
- V3 pick-place v0.7 selected BC demo:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_7_target_conditioned\20260601_021319_seed063\visuals\final_demo_v0_7_phase_only_trainall_50cm_policy_demo.mp4`
- V3 pick-place v0.7 status: fixed reachable 50cm target smoke pass achieved for scripted expert and train-all phase-only BC. Do not promote as target-general; next useful step is v0.7.1 multi-direction reachable 50cm data and `obs_phase_target`.
- V3 pick-place v0.7.1 multi-direction train-ready run:
  `D:\tendon_project\simulations\runs\stage2_pick_place_v0_7_1_multidir\20260602_000000_seed064`
- V3 pick-place v0.7.1 config:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\configs\stage2_pick_place_v0_7_1_multidir_train_ready.yaml`
- V3 pick-place v0.7.1 dataset:
  `D:\tendon_project\simulations\runs\stage2_pick_place_v0_7_1_multidir\20260602_000000_seed064\datasets\arm_hand_stage1_v3_pick_place_dataset_v0_7_1.npz`
- V3 pick-place v0.7.1 collection result: `12 / 12` success, `74125` rows, obs shape `[74125, 130]`, base obs shape `[74125, 124]`, action shape `[74125, 26]`, four 50cm target directions (`-180`, `-150`, `-135`, `-90`) and three timing profiles per target.
- V3 pick-place v0.7.1 replay QA:
  `D:\tendon_project\simulations\runs\stage2_pick_place_v0_7_1_multidir\20260602_000000_seed064\eval\replay_qa_report.md`
- V3 pick-place v0.7.1 replay QA result: `PASS`, replay success `12 / 12`, max obs/next_obs/reward error `0`, final target XY range `0.008571 m` to `0.028386 m`, transport floor contacts `0`, final hand contacts `0`.
- V3 pick-place v0.7.1 train readiness report:
  `D:\tendon_project\simulations\runs\stage2_pick_place_v0_7_1_multidir\20260602_000000_seed064\eval\train_readiness_report.md`
- V3 pick-place v0.7.1 BC training/eval report:
  `D:\tendon_project\simulations\runs\stage2_pick_place_v0_7_1_multidir\20260602_000000_seed064\eval\final_v0_7_1_bc_training_report.md`
- V3 pick-place v0.7.1 `obs_phase_target` result: standard split and train-all both fit offline but fail online fixed-angle eval (`0 / 4` PASS). Diagnosis: live observation feedback drives early closed-loop OOD, pushing/rolling the ball before a secure grasp.
- V3 pick-place v0.7.1 `phase_target_static` repair result: train-all static target/phase policy reaches `2 / 4` fixed 50cm targets (`-150`, `-90`) with clean learned pick-place, but fails `-180` and `-135`; do **not** promote as target-general baseline.
- V3 pick-place v0.7.1 learned success demo:
  `D:\tendon_project\simulations\runs\stage2_pick_place_v0_7_1_multidir\20260602_000000_seed064\visuals\v0_7_1_static_success_demo_m150_policy_demo.mp4`
- V3 pick-place v0.7.1 current status: dataset/replay are good and one learned 50cm direction demo is achieved, but the policy gate is **PARTIAL**. Next step is v0.7.2 with phase-gated/static-target control and more directional coverage, not RL.
- V3 pick-place v0.7.2 phase-table policy script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\eval_arm_hand_stage1_v3_pick_place_phase_table_policy.py`
- V3 pick-place v0.7.2 phase-table policy artifact:
  `D:\tendon_project\simulations\runs\stage2_pick_place_v0_7_1_multidir\20260602_000000_seed064\checkpoints\phase_table_policy_v0_7_2_clean_actions.npz`
- V3 pick-place v0.7.2 final report:
  `D:\tendon_project\simulations\runs\stage2_pick_place_v0_7_1_multidir\20260602_000000_seed064\eval\final_v0_7_2_phase_table_report.md`
- V3 pick-place v0.7.2 fixed 50cm target result: **4 / 4 PASS** on exact dataset directions (`-180`, `-150`, `-135`, `-90`), final target XY range `0.008620 m` to `0.018237 m`, stable target steps `240` for every target, transport floor contacts `0`, final hand contacts max `0`.
- V3 pick-place v0.7.2 local tolerance result: `-150 deg` 5x5 narrow sweep is `24 / 25 PASS`; the only miss is `0.035461 m`, just outside the `0.035 m` radius.
- V3 pick-place v0.7.2 success demo:
  `D:\tendon_project\simulations\runs\stage2_pick_place_v0_7_1_multidir\20260602_000000_seed064\visuals\v0_7_2_phase_table_success_demo_m135_policy_demo.mp4`
- V3 pick-place v0.7.2 status: fixed-known-target diagnostic baseline is **PASS**, but it is nearest-target action-table playback, not a smooth target-general policy. Next step is v0.7.3 trainable phase-specific or mixture-of-experts policy using v0.7.2 as the control baseline.
- V3 pick-place v0.7.3 phase-specific run:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_7_3_phase_specific\20260602_010000_seed068`
- V3 pick-place v0.7.3 config:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\configs\stage2_pick_place_v0_7_3_phase_specific.yaml`
- V3 pick-place v0.7.3 final report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_7_3_phase_specific\20260602_010000_seed068\eval\final_v0_7_3_phase_regression_report.md`
- V3 pick-place v0.7.3 release-repair dataset:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_7_3_phase_specific\20260602_010000_seed068\datasets\arm_hand_stage1_v3_pick_place_dataset_v0_7_3_release_repair.npz`
- V3 pick-place v0.7.3 dataset/replay result: initial 7-direction collection was `12 / 21` because `-165`, `-120`, and `-105` kept hand contact after release; per-target `pre_release_z_drop` repair produced `21 / 21` collection success and replay QA `PASS`.
- V3 pick-place v0.7.3 selected trainable policy:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_7_3_phase_specific\20260602_010000_seed068\checkpoints\phase_regression_policy_v0_7_3_release_repair_clean_actions_rbf.npz`
- V3 pick-place v0.7.3 fixed 50cm target result: **7 / 7 PASS** on exact dataset directions (`-180`, `-165`, `-150`, `-135`, `-120`, `-105`, `-90`), final target XY range `0.008620 m` to `0.018237 m`, stable target steps `240` for every target, transport floor contacts `0`, final hand contacts max `0`.
- V3 pick-place v0.7.3 demo:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_7_3_phase_specific\20260602_010000_seed068\visuals\v0_7_3_phase_regression_rbf_success_demo_m165_policy_demo.mp4`
- V3 pick-place v0.7.3 `-165 deg` narrow sweep:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_7_3_phase_specific\20260602_010000_seed068\eval\v0_7_3_phase_regression_rbf_m165_narrow_sweep_eval_report.md`
- V3 pick-place v0.7.3 `-165 deg` narrow sweep result: **15 / 25 PARTIAL** on 5x5 offsets `[-0.02, -0.01, 0.0, 0.01, 0.02]`; failures are timeout/target miss on some outer offsets, with transport floor contacts `0` and final hand contacts max `0`.
- V3 pick-place v0.7.3 status: fixed-known-target trainable phase-specific baseline is **PASS**, but local target generality is **PARTIAL**. Do not overclaim target generality; the selected policy uses target RBF centers at the seven known directions. Next gate is interpolation-focused repair around `-165`, then narrow sweeps around `-135` and `-105`.
- V3 pick-place v0.8 Gate1 run:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_8_gate1_target_generalization\20260603_000000_seed071`
- V3 pick-place v0.8 Gate1 config:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\configs\stage2_pick_place_v0_8_gate1_target_generalization.yaml`
- V3 pick-place v0.8 Gate1 report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_8_gate1_target_generalization\20260603_000000_seed071\eval\gate1_v0_8_target_generalization_report.md`
- V3 pick-place v0.8 Gate1 dataset:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_8_gate1_target_generalization\20260603_000000_seed071\datasets\arm_hand_stage1_v3_pick_place_dataset_v0_8_gate1_m165_local_repair.npz`
- V3 pick-place v0.8 Gate1 dataset/replay result: collection **31 / 31 PASS** and replay QA **31 / 31 PASS**. The dataset includes original fixed 7 targets plus 24 local repair centers around `-165 deg`, using `clean_nominal`.
- V3 pick-place v0.8 Gate1 trainable RBF phase-regression result: **NOT PASS** for local target generality. Best fixed-target candidate used `rbf_sigma=0.075`, `ridge=1e-3`, recovered fixed 7 targets to **7 / 7 PASS**, but the `-165 deg` 5x5 sweep was only **8 / 25 PARTIAL** with timeout and transport-drop failures. Diagnosis: current RBF phase regressor breaks transport/transport_hold/descend trajectory representation.
- V3 pick-place v0.8 Gate1 phase-table bridge result: **PASS** as a diagnostic/staged-control bridge, not a smooth learned target-general policy. Fixed 7 targets: **7 / 7 PASS**; `-165 deg` exact 5x5 sweep: **25 / 25 PASS**; `-165 deg` held-out midpoint sweep with offsets `[-0.015, -0.005, 0.005, 0.015]`: **16 / 16 PASS**; transport floor contacts `0`; final hand contacts max `0`.
- V3 pick-place v0.8 Gate1 demo:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_8_gate1_target_generalization\20260603_000000_seed071\visuals\v0_8_gate1_phase_table_midpoint_success_demo_policy_demo.mp4`
- V3 pick-place v0.8 Gate1 hard-gated MoE script:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\eval_arm_hand_stage1_v3_pick_place_phase_moe_policy.py`
- V3 pick-place v0.8 Gate1 hard-gated MoE policy:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_8_gate1_target_generalization\20260603_000000_seed071\checkpoints\phase_moe_policy_v0_8_gate1_top1_sigma0p0.npz`
- V3 pick-place v0.8 Gate1 hard-gated MoE completion report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_8_gate1_target_generalization\20260603_000000_seed071\eval\gate1_v0_8_hard_moe_completion_report.md`
- V3 pick-place v0.8 Gate1 hard-gated MoE result: **PASS**. Fixed 7 targets: **7 / 7 PASS**; `-165 deg` exact 5x5: **25 / 25 PASS**; `-165 deg` held-out midpoint 4x4: **16 / 16 PASS**; transport floor contacts `0`; final hand contacts max `0`.
- V3 pick-place v0.8 Gate1 hard-gated MoE demo:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_8_gate1_target_generalization\20260603_000000_seed071\visuals\v0_8_gate1_hard_moe_midpoint_success_demo_policy_demo.mp4`
- V3 pick-place v0.8 Gate1 status: record Gate1 as achieved for hard-gated MoE / nearest-target staged-control. Do **not** claim smooth continuous target interpolation: dense RBF phase regression, soft action MoE, and phase-keypoint regression were tried and rejected because they caused transport drops, timeout, or release instability. Next step is to repeat the hard-gated MoE process around `-135` and `-105`.
- V3 pick-place v0.9 Gate2 run:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_9_gate2_multiregion_hard_moe\20260603_020000_seed072`
- V3 pick-place v0.9 Gate2 config:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\configs\stage2_pick_place_v0_9_gate2_multiregion_hard_moe.yaml`
- V3 pick-place v0.9 Gate2 completion report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_9_gate2_multiregion_hard_moe\20260603_020000_seed072\eval\gate2_v0_9_hard_moe_completion_report.md`
- V3 pick-place v0.9 Gate2 dataset:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_9_gate2_multiregion_hard_moe\20260603_020000_seed072\datasets\arm_hand_stage1_v3_pick_place_dataset_v0_9_gate2_multiregion_hard_moe.npz`
- V3 pick-place v0.9 Gate2 policy:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_9_gate2_multiregion_hard_moe\20260603_020000_seed072\checkpoints\phase_moe_policy_v0_9_gate2_top1_sigma0p0.npz`
- V3 pick-place v0.9 Gate2 result: **PASS**. Dataset collection **79 / 79 PASS** and replay QA **79 / 79 PASS**. Fixed 7 targets: **7 / 7 PASS**. Local exact 5x5 around `-165`, `-135`, and `-105`: **25 / 25 PASS** for each region. Held-out midpoint 4x4 around `-165`, `-135`, and `-105`: **16 / 16 PASS** for each region. All passing evals had transport floor contacts `0` and final hand contacts max `0`.
- V3 pick-place v0.9 Gate2 repair memory: first collection was **64 / 79 PASS**. `-135` failures were residual hand-contact timeouts; global `post_release_clear_steps=700` fixed them. `-105` also needed `pre_release_z_drop=0.012` and `hover_z_lift=0.012` to avoid descend-phase floor contact and release drift. Higher hover lift values were harmful in the sweep.
- V3 pick-place v0.9 Gate2 demo:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\runs\stage2_pick_place_v0_9_gate2_multiregion_hard_moe\20260603_020000_seed072\visuals\v0_9_gate2_hard_moe_m105_midpoint_success_demo_policy_demo.mp4`
- V3 pick-place v0.9 Gate2 status: record Gate2 as achieved for hard-gated MoE / nearest-target staged-control across three local regions. Do **not** claim smooth continuous target interpolation. Next step is Gate3 inter-region holdout and robustness, not more exact local-cell collection by default.
- Stage2.5 Gate4 policy-structure maturity report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\stage2_5_gate4_policy_structure_maturity.md`
- Stage2.5 Gate4 status: **PASS**. Keep `phase-gated / phase-specific control` as the mainline. The selected operational baseline is Gate2 v0.9 hard-gated nearest-expert phase MoE. Retain v0.7.3 phase-specific RBF regression only as a trainable template, not as the promoted local-general baseline.
- Stage2.5 Gate4 policy boundary: early approach/grasp/lift should not use fully live-observation BC. Transport, descend, and release may use learned phase-specific modules or residuals later, but only if they match or beat Gate2 hard-gated MoE on the same fixed/exact/held-out/contact gates.
- Stage2.5 Gate5 Stage3 readiness report:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\stage2_5_gate5_stage3_readiness.md`
- Stage3 task contract starter:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\stage3_task_contract_starter_v0.md`
- Stage2.5 Gate5 status: **PASS**. Stage2.5 now has mature MuJoCo dataset/replay/eval/report templates, the phase-gated control framework, a failure taxonomy, a synthetic tactile/slip phase map, and a vision abstraction map replacing perfect MuJoCo object/target state for policy inputs.
- Stage3.0 recommended start: implement `stage3_sensor_aware_gentle_grasp_hold_v0` with an egg-like object, noisy vision abstraction, synthetic tactile/slip fields, conservative phase-gated scripted expert, replay QA, numeric eval, and compact visual report.
- Stage2.5 closure summary:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\stage2_5_closure_summary_before_stage3.md`
- Stage2.5 closure status: close Stage2.5 for the purpose of starting Stage3. Inter-region pick-place robustness remains useful optional backlog, but it is not blocking for Stage3.0.
- Stage2 pick-place sim-to-real strategy memory:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\sim_to_real_strategy_stage2_pick_place.md`
- Stage3 sensor-aware MuJoCo manipulation outline:
  `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\stage3_sensor_aware_mujoco_manipulation_outline.md`
- Strategic reminder: 50cm pick-place is a sim-to-real scaffold for staged, measurable manipulation. Use it to expose gates, failure modes, tactile/slip needs, and hardware-safe control architecture; do not let the work drift into endless single-demo optimization or premature end-to-end BC/RL claims.

Stage roadmap:

- Stage2.5: MuJoCo training maturity. Keep current pick-place work inside MuJoCo until local target interpolation, held-out target eval, perturbation robustness, and standardized dataset/replay/train/eval/demo/report loops are stronger.
- Stage3: Sensor-aware MuJoCo manipulation. Hardware is still unavailable, so Stage3 stays in MuJoCo and adds simulated vision, synthetic tactile/slip, fragile egg-like object grasp/lift/hold, crush/slip metrics, and recovery logic.
- Stage4: Hardware interface. Stage4 owns motor command interface, real sensor data interface, camera calibration, tactile/ultrasound integration when available, and staged real-hand tests.
- Do not describe Stage3 as hardware integration. Stage4 is the hardware-interface stage.

Guardrails:

- Do not modify CAD/STL.
- Do not overwrite the Stage1 baseline unless explicitly promoted.
- Do not promote BC/RL training yet.
- Do not add tendon routing yet.
- Treat collision proxy v2 as smoke-test geometry, not final physics.
- Treat the current BC checkpoints as experimental smoke only; they are not maintained baselines.
- Treat v3 pick-place as a scripted smoke scaffold only until dataset v0.5 replay QA and online eval exist.
- Keep RL blocked until broader reset coverage and reward QA are accepted.
- Do not claim tactile/ultrasound integration exists in the hand runtime; Stage3 may only use synthetic tactile/slip abstractions until sensors are integrated.

Recommended continuation for the next conversation:

1. start Stage3.0 from:
   `D:\tendon_project\simulations\models\arm_hand_stage1_export\docs\stage3_task_contract_starter_v0.md`;
2. implement `stage3_sensor_aware_gentle_grasp_hold_v0`;
3. add an egg-like MuJoCo object scene;
4. add noisy vision abstraction fields that replace perfect object/target state in policy inputs;
5. add synthetic tactile/slip fields from MuJoCo contact, penetration, and relative-motion proxies;
6. create a conservative phase-gated scripted smoke expert;
7. collect the first fixed-pose Stage3 dataset and run replay QA;
8. run numeric eval plus contact-sheet visual QA;
9. keep Stage2.5 inter-region pick-place robustness as optional regression/backlog, not the next mainline;
10. keep RL and hardware integration blocked until Stage3 contract, replay QA, reward/termination QA, and sensor-abstraction eval pass.
