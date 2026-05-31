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
- V3 pick-place status: task scaffold and one scripted pure-physics same-platform demo pass; no pick-place dataset/checkpoint is promoted yet.

Guardrails:

- Do not modify CAD/STL.
- Do not overwrite the Stage1 baseline unless explicitly promoted.
- Do not promote BC/RL training yet.
- Do not add tendon routing yet.
- Treat collision proxy v2 as smoke-test geometry, not final physics.
- Treat the current BC checkpoints as experimental smoke only; they are not maintained baselines.
- Treat v3 pick-place as a scripted smoke scaffold only until dataset v0.5 replay QA and online eval exist.
- Keep RL blocked until broader reset coverage and reward QA are accepted.

Recommended Stage2 continuation:

1. inspect the v0.4 long-hold and holdout demo videos plus the updated hold-validation report;
2. inspect the v3 pick-place contact sheet/video and task contract;
3. run a small scripted pick-place sweep around the current target (`target radius 0.035 m`) before collecting dataset v0.5;
4. collect pick-place dataset v0.5 only from scripted episodes that pass replay QA;
5. train a first `obs_phase_target` BC policy after dataset v0.5 replay QA passes;
6. keep Shadow/video comparison as regression;
7. keep RL blocked until broader holdout coverage and reward QA are accepted.
