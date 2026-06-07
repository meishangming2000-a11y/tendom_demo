# Stage2.5 Gate4 Policy Structure Maturity

Generated: 2026-06-03

## Verdict

Gate4 is **PASS** for policy-structure maturity.

The selected Stage2.5 structure is:

```text
phase-gated / phase-specific control as the mainline
```

The promoted operational baseline is:

```text
Gate2 v0.9 hard-gated nearest-expert phase MoE
```

The retained trainable template is:

```text
v0.7.3 phase-specific RBF regression
```

The trainable template is useful, but it is **not** promoted as the current local-generalization baseline because its `-165` local narrow sweep was only `15 / 25 PARTIAL`.

## Selected Baseline

### Operational Baseline To Keep

- Name: Gate2 v0.9 hard-gated nearest-expert phase MoE
- Policy file:
  `models/arm_hand_stage1_export/runs/stage2_pick_place_v0_9_gate2_multiregion_hard_moe/20260603_020000_seed072/checkpoints/phase_moe_policy_v0_9_gate2_top1_sigma0p0.npz`
- Report:
  `models/arm_hand_stage1_export/runs/stage2_pick_place_v0_9_gate2_multiregion_hard_moe/20260603_020000_seed072/eval/gate2_v0_9_hard_moe_completion_report.md`
- Structure:
  - phase schedule is explicit
  - target selects nearest successful expert
  - `top_k=1`
  - `rbf_sigma=0.0`
  - no fully live-observation BC during early grasp/lift

Gate evidence:

| Gate item | Result |
|---|---:|
| collection | 79 / 79 PASS |
| replay QA | 79 / 79 PASS |
| fixed 7 targets | 7 / 7 PASS |
| -165 exact 5x5 | 25 / 25 PASS |
| -135 exact 5x5 | 25 / 25 PASS |
| -105 exact 5x5 | 25 / 25 PASS |
| -165 held-out midpoint 4x4 | 16 / 16 PASS |
| -135 held-out midpoint 4x4 | 16 / 16 PASS |
| -105 held-out midpoint 4x4 | 16 / 16 PASS |
| transport floor contacts | 0 |
| final hand contacts max | 0 |

### Trainable Template To Keep

- Name: v0.7.3 phase-specific RBF regression
- Report:
  `models/arm_hand_stage1_export/runs/stage2_pick_place_v0_7_3_phase_specific/20260602_010000_seed068/eval/final_v0_7_3_phase_regression_report.md`
- Fixed known targets: `7 / 7 PASS`
- Local sweep: `15 / 25 PARTIAL` around `-165`

Use it as the template for future learned modules because it is phase-specific and avoids fully live observation feedback. Do not promote it as the main Gate4 baseline until it beats hard-gated MoE on the same local and held-out gates.

## Phase Scope

| Phase group | Gate4 decision | Allowed policy structure |
|---|---|---|
| approach / preshape / close | keep conservative | scripted or phase-only/static target; no fully live-observation BC |
| lift / hold_lift | keep conservative | scripted, phase-specific, or hard-gated expert schedule |
| transport | learnable later | phase-specific learned module or residual may be tested after hard-gated baseline |
| transport_hold | learnable later | phase-specific residual allowed if contact/stability gates pass |
| descend_to_target | learnable later with care | phase-specific learned module or residual, but must preserve no pre-release floor contact |
| pre_release_settle / release | learnable later with strict gates | phase-specific residual allowed only if final hand contact remains 0 |
| post_release_clear / retreat | mostly rule-based for now | keep explicit until release/contact behavior is robust |

## What Not To Keep As Mainline

### Fully Live-Observation BC For Early Grasp/Lift

Evidence:

- v0.7.1 `obs_phase_target` split policy had low offline loss but fixed-angle online eval was `0 / 4 PASS`.
- v0.7.1 `obs_phase_target_trainall` also had very good offline fit but fixed-angle online eval was `0 / 4 PASS`.
- Failure diagnosis: live ball/hand observations made early rollout drift self-amplifying; the policy nudged or rolled the ball before secure grasp, then could not recover.

Conclusion:

Do not use a fully live-observation BC policy for approach, closure, or early lift unless a future dataset includes recovery/noise coverage and passes the same gates.

### Smooth Low-Level Action Interpolation

Evidence:

- Gate1 dense RBF phase regression recovered fixed targets but failed local `-165` exact 5x5 with only `8 / 25 PASS`.
- Soft action MoE on held-out midpoint variants produced transport drops and timeouts, including a `13 / 16 PARTIAL` case with transport floor contacts `2` and final hand contacts max `7`.
- Phase-keypoint policy on `-165` midpoint produced only `5 / 16 PASS`, with timeout, transport-drop, large target misses, and final hand contacts up to `7`.

Conclusion:

Do not promote smooth low-level action blending yet. For this contact-rich task, low-level interpolation can break transport, descent, and release timing.

## Where Learned Modules Are Allowed

Gate4 does not ban learning. It restricts where learning is allowed first.

Allowed next experiments:

- phase-specific learned residual for `transport`
- phase-specific learned residual for `descend_to_target`
- phase-specific release correction after `pre_release_settle`
- target-conditioned high-level/keypoint proposal, followed by explicit phase execution

Required promotion gates:

- must beat or match Gate2 hard-gated MoE on fixed/exact/held-out target gates
- transport floor contacts must remain `0`
- final hand contacts max must remain `0`
- no overclaim of smooth continuous target interpolation unless held-out inter-region eval passes

## Failure Analysis Supporting The Choice

| Candidate | Outcome | Failure support |
|---|---|---|
| v0.7.1 live obs+phase+target BC | rejected | `0 / 4 PASS`; early closed-loop OOD drift, ball push/roll before secure grasp |
| v0.7.1 phase_target_static BC | diagnostic only | improved to `2 / 4 PASS`, proving less live observation is better, but not enough coverage |
| v0.7.2 phase-table | diagnostic pass | `4 / 4 PASS`, local `24 / 25`, but nearest table playback and not smooth target-general |
| v0.7.3 phase-specific RBF | retained template | fixed `7 / 7 PASS`, but local `15 / 25 PARTIAL`; not promoted to local-general baseline |
| v0.8 smooth/RBF/soft/keypoint variants | rejected for now | timeout, transport drop, release instability, residual hand contact |
| v0.9 Gate2 hard-gated MoE | selected baseline | fixed, exact-local, and held-out midpoint gates all PASS across three local regions |

## Gate4 Completion Check

- selected phase-specific baseline exists: **yes**, Gate2 v0.9 hard-gated nearest-expert phase MoE
- usage scope is explicit: **yes**, see Phase Scope
- overclaim boundaries are explicit: **yes**, no smooth interpolation, no hardware-ready claim, no fully live-observation early grasp/lift claim
- failure analysis supports the choice: **yes**, v0.7.1, v0.7.3, v0.8, and Gate2 evidence are listed

## Next Work

Gate5 should evaluate robustness and inter-region generality:

- inter-region targets around `-150`, `-120`, and possibly `-97.5`
- small initial ball and target perturbations
- compare hard-gated MoE against phase-specific learned residuals only on the same gates
- keep early grasp/lift conservative until recovery/noise data proves live observation can be trusted
