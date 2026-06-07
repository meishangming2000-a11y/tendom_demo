# Stage2.5 Gate5 Stage3 Readiness

Generated: 2026-06-03

## Verdict

Gate5 is **PASS** for Stage3 readiness.

Stage2.5 is now ready to start a Stage3 task contract because the project has:

- mature MuJoCo dataset / replay / eval / report templates
- a selected phase-gated / phase-specific control framework
- a reusable failure classification framework
- a concrete synthetic tactile/slip phase map
- a concrete vision abstraction map that replaces perfect MuJoCo state in policy inputs

Stage3 remains a MuJoCo stage. This gate does **not** claim real hardware, real tactile, ultrasound, or camera integration.

## Stage3 Starter Contract

Use this document as the immediate Stage3 contract seed:

```text
models/arm_hand_stage1_export/docs/stage3_task_contract_starter_v0.md
```

Recommended Stage3 anchor task:

```text
approach egg-like object -> gentle grasp -> lift 5 cm -> hold 3 s -> no slip -> no crush
```

## Readiness Checklist

| Required item | Status | Evidence |
|---|---|---|
| mature MuJoCo dataset template | PASS | `collect_arm_hand_stage1_v3_pick_place_dataset_v0_5.py`, v0.9 Gate2 dataset |
| replay QA template | PASS | `replay_arm_hand_stage1_v3_pick_place_dataset.py`, Gate2 replay `79 / 79 PASS` |
| eval template | PASS | hard-gated MoE eval fixed/exact/midpoint reports |
| report template | PASS | Gate2, Gate4, and post-Gate2 workflow reports |
| compact visual QA pattern | PASS | contact sheet + selected MP4, not all-episode video dumping |
| phase-gated control framework | PASS | Gate4 selected phase-gated / phase-specific mainline |
| operational baseline | PASS | Gate2 hard-gated nearest-expert phase MoE |
| trainable template | PASS with boundary | v0.7.3 phase-specific RBF regression retained only as template |
| failure taxonomy | PASS | early push/roll, transport drop, release contact, target miss, closed-loop drift |
| synthetic tactile/slip phase map | PASS | defined below |
| vision abstraction replacement map | PASS | defined below |

## Reusable MuJoCo Run Template

Stage3 should reuse the Stage2.5 run pattern:

```text
run/
  config.lock.yaml
  command.txt
  git_info.txt
  report.md
  datasets/
  eval/
    summary.json
    episodes.jsonl
    *_eval_report.md
    *_summary.json
    *_episodes.csv
  checkpoints/
  visuals/
    contact_sheet.png
    selected_demo.mp4
```

Required evidence remains:

- config lock
- deterministic collection summary
- replay QA
- online eval summary
- compact visual sanity check
- completion report
- handoff update

## Control Framework To Carry Into Stage3

Gate4 selected:

```text
phase-gated / phase-specific control as the mainline
```

Carry this structure into Stage3:

| Phase group | Stage3 default |
|---|---|
| vision acquire / approach / align | phase-gated, conservative |
| gentle close / contact settle | phase-specific, tactile-aware checks |
| grasp secure check | rule/check gate before lift |
| lift / hold | phase-specific; tactile/slip monitoring active |
| slip recovery / abort | explicit state transition |
| release / retreat | explicit until stable |

Do not return to fully live-observation BC for early approach/grasp/lift unless a future noisy/recovery dataset proves it can pass the same gates.

## Failure Classification Framework

Stage3 should start with these buckets:

| Failure bucket | Stage2.5 origin | Stage3 equivalent |
|---|---|---|
| early push/roll | live-observation BC pushed ball before grasp | vision/noisy approach pushes egg before contact plan |
| no secure grasp | timeout / zero useful contact | contact acquisition failure |
| transport/drop | transport floor contact | slip/drop during lift or hold |
| release contact remaining | stable steps reset by hand contact | hand does not clear object after release |
| target miss / drift | placement outside radius | object pose not controlled under noisy estimate |
| closed-loop OOD drift | low offline loss, online failure | sensor-conditioned policy leaves safe manifold |
| excessive penetration | contact gate failure | crush risk |
| unstable hold | not central in pick-place | slip, oscillation, or pose drift during 3s hold |

The first Stage3 contract should log every episode into these buckets.

## Synthetic Tactile / Slip Phase Map

Synthetic tactile/slip should be generated from MuJoCo ground truth contacts, relative motion, and penetration, but exposed to policies as sensor-style abstractions.

Do not expose raw omniscient contact internals as if they were real hardware.

| Phase | Synthetic tactile/slip fields | Purpose |
|---|---|---|
| approach / align | `contact_present=false`, optional proximity diagnostic only | verify no premature contact |
| gentle_close | `contact_present`, `contact_finger_id`, `normal_contact_proxy`, `contact_distribution` | detect first contact and avoid uneven crushing |
| contact_settle | `contact_persistence`, `normal_contact_proxy`, `crush_risk`, `grip_stable` | decide whether grasp is secure before lift |
| lift | `slip_score`, `relative_tangential_motion`, `contact_persistence`, `grip_margin` | detect slip/drop risk as object leaves support |
| hold | `slip_score`, `object_pose_drift`, `contact_persistence`, `crush_risk` | hold for 3s with no slip/no crush |
| transport, if used | same as hold plus `drop_risk` | keep contact stable during motion |
| descend / pre_release | `ground_contact_proxy`, `contact_force_drop`, `slip_score` | distinguish intended support contact from drop |
| release / retreat | `release_contact_clear`, `final_hand_contact_count_proxy` | ensure object is free of hand contact after release |

Suggested field family:

```text
tactile.contact_present
tactile.contact_regions
tactile.normal_contact_proxy
tactile.contact_persistence
tactile.relative_tangential_motion
tactile.slip_score
tactile.grip_stable
tactile.crush_risk
tactile.release_contact_clear
```

Evaluation may still use ground truth MuJoCo metrics, but policy inputs should use the synthetic abstraction fields.

## Vision Abstraction Replacement Map

Current Stage2.5 pick-place observations include perfect MuJoCo target/object information:

```text
target_center_xyz
ball_to_target_xyz
ball_position / velocity inside base observation
```

Stage3 should replace these policy inputs with perception-style fields:

| Perfect MuJoCo state | Stage3 policy input | Notes |
|---|---|---|
| object position | `vision.object_pose_xyz_est` | add noise, latency, confidence |
| object orientation / axis | `vision.object_axis_est` | needed for egg-like object |
| object velocity | `vision.object_pose_delta_est` | estimated from delayed/noisy pose history |
| target center | `vision.goal_pose_xyz_est` or task goal spec | do not use perfect target unless in eval only |
| object-to-goal vector | computed from estimates | not from ground truth |
| object size/shape | `vision.object_shape_params_est` | radius/axis estimate with uncertainty |
| visibility | `vision.visibility`, `vision.occlusion`, `vision.confidence` | policy can abort or slow down |
| initial object position | episode metadata / eval only | not a privileged policy input |

Suggested field family:

```text
vision.object_pose_xyz_est
vision.object_axis_est
vision.object_shape_params_est
vision.goal_pose_xyz_est
vision.object_to_goal_est
vision.confidence
vision.occlusion
vision.latency_steps
vision.noise_std
```

Ground truth object pose remains allowed for:

- success/failure metrics
- replay QA
- supervised label generation
- diagnostic reports

It should not be used as the default learned-policy observation once Stage3 sensor abstraction begins.

## Stage3 Contract Inputs Now Ready

The first Stage3 task contract should include:

- object: egg-like ellipsoid or capsule/ellipsoid approximation
- task: gentle grasp, lift 5 cm, hold 3 s
- phases: vision acquire, approach, gentle close, contact settle, grasp check, lift, hold, recovery/abort, release
- observation: proprioception + phase + noisy vision abstraction + synthetic tactile/slip abstraction
- action: current actuator action schema plus optional phase-specific residuals
- success: stable lift/hold, no slip, no crush, finite state
- failure: crush, slip/drop, premature contact, bad vision confidence, no secure contact, timeout
- reports: same run/report/replay/eval pattern as Stage2.5

## Gate5 Completion Check

- mature dataset/eval/report template exists: **yes**
- phase-gated control framework exists: **yes**
- failure classification framework exists: **yes**
- synthetic tactile/slip phase map exists: **yes**
- vision abstraction replacement map exists: **yes**
- ready to start Stage3 task contract: **yes**

## Next Step

Start Stage3.0 by implementing the task contract and a scripted smoke expert for:

```text
stage3_sensor_aware_gentle_grasp_hold_v0
```

Do not start with RL or hardware. Start with contract, scene/object definition, sensor abstraction fields, scripted expert, replay QA, and numeric eval.
