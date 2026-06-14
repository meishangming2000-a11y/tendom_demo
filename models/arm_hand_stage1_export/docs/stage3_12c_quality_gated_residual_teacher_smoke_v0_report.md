# Stage3.12C Quality-Gated Residual Teacher v0

Generated: `2026-06-13T19:46:43`

## Boundary

- MuJoCo-only bounded residual teacher/search.
- Uses Stage3.12B morphology-quality head as an intervention trigger for tiny residual probes.
- Keeps scripted/event-gated controller and compares against frozen D-I.
- No full-action ACT/DP, hardware runtime, real camera, real tactile, or demo-gallery promotion.

## Failure Window Mining

- Mining variants: `['baseline_di_off', 'lift_ls460_off']`
- Evidence frames: `552`
- Low-quality frames: `155` (`0.281`)
- Low-quality phases: `{'contact_gate': 112, 'slow_lift': 34, 'post_contact_settle': 9}`
- Low-quality terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 111, 'contact_gate_failed': 44}`

## Smoke Ranking

| rank | variant | success | contact | lift | true pinch | release | residual events | hold tip | hold non-tip | reasons | decision |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | `di_qhead_prelift_xneg_s0003_m0006` | 2 / 4 | 3 | 2 | 2 | 4 | 0 | 0.500 | 0.128 | `{'contact_gate_failed': 1, 'success_event_contact_gated_true_pinch_release_ball': 2, 'lift_gate_failed': 1}` | `tie_diagnostic` |
| 2 | `baseline_di_off` | 2 / 4 | 3 | 2 | 2 | 4 | 0 | 0.500 | 0.141 | `{'contact_gate_failed': 1, 'success_event_contact_gated_true_pinch_release_ball': 2, 'lift_gate_failed': 1}` | `frozen_anchor` |
| 3 | `di_qhead_close_s002_m010_w100` | 2 / 4 | 3 | 2 | 2 | 4 | 20 | 0.500 | 0.141 | `{'contact_gate_failed': 1, 'success_event_contact_gated_true_pinch_release_ball': 2, 'lift_gate_failed': 1}` | `tie_diagnostic` |
| 4 | `di_qhead_wait_w120` | 2 / 4 | 3 | 2 | 2 | 4 | 24 | 0.500 | 0.141 | `{'contact_gate_failed': 1, 'success_event_contact_gated_true_pinch_release_ball': 2, 'lift_gate_failed': 1}` | `tie_diagnostic` |
| 5 | `di_qhead_close_s003_m012_w120` | 2 / 4 | 3 | 2 | 2 | 4 | 24 | 0.500 | 0.141 | `{'contact_gate_failed': 1, 'success_event_contact_gated_true_pinch_release_ball': 2, 'lift_gate_failed': 1}` | `tie_diagnostic` |
| 6 | `lift_ls460_off` | 2 / 4 | 3 | 2 | 2 | 4 | 0 | 0.500 | 0.167 | `{'contact_gate_failed': 1, 'success_event_contact_gated_true_pinch_release_ball': 2, 'lift_gate_failed': 1}` | `tie_diagnostic` |
| 7 | `ls460_qhead_close_s002_m010_w100` | 2 / 4 | 3 | 2 | 2 | 4 | 20 | 0.500 | 0.167 | `{'contact_gate_failed': 1, 'success_event_contact_gated_true_pinch_release_ball': 2, 'lift_gate_failed': 1}` | `tie_diagnostic` |
| 8 | `di_qhead_pid_close_s002_w100` | 2 / 4 | 3 | 2 | 2 | 4 | 51 | 0.500 | 0.167 | `{'contact_gate_failed': 1, 'success_event_contact_gated_true_pinch_release_ball': 2, 'lift_gate_failed': 1}` | `tie_diagnostic` |

## Validation Ranking

| rank | variant | success | contact | lift | true pinch | release | residual events | hold tip | hold non-tip | reasons | decision |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|

## Selected Diagnostic Outcome

- Variant: `di_qhead_prelift_xneg_s0003_m0006`
- Candidate family: `quality_retarget`
- Validation success: `2 / 4`
- Contact/lift/true-pinch/release: `3` / `2` / `2` / `4`
- Residual events: `0`
- Terminal reasons: `{'contact_gate_failed': 1, 'success_event_contact_gated_true_pinch_release_ball': 2, 'lift_gate_failed': 1}`

## Decision

Best candidate tied D-I on matched validation. Keep it as diagnostic only; do not promote without a multiseed gain.

## Next

- If validation beats frozen D-I without morphology regression, run the multiseed 150-trial gate.
- If residuals only trade lift/contact/morphology failures, keep D-I frozen and move to contact geometry or richer residual-policy data.
