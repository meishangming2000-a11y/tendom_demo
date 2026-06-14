# Stage3.12C Quality-Gated Residual Teacher v0

Generated: `2026-06-13T19:50:52`

## Boundary

- MuJoCo-only bounded residual teacher/search.
- Uses Stage3.12B morphology-quality head as an intervention trigger for tiny residual probes.
- Keeps scripted/event-gated controller and compares against frozen D-I.
- No full-action ACT/DP, hardware runtime, real camera, real tactile, or demo-gallery promotion.

## Failure Window Mining

- Mining variants: `['baseline_di_off', 'lift_ls460_off']`
- Evidence frames: `1105`
- Low-quality frames: `309` (`0.280`)
- Low-quality phases: `{'contact_gate': 224, 'slow_lift': 68, 'post_contact_settle': 17}`
- Low-quality terminal reasons: `{'success_event_contact_gated_true_pinch_release_ball': 221, 'contact_gate_failed': 88}`

## Smoke Ranking

| rank | variant | success | contact | lift | true pinch | release | residual events | hold tip | hold non-tip | reasons | decision |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | `di_qhead_pid_close_s002_w100` | 5 / 8 | 6 | 5 | 5 | 8 | 111 | 0.625 | 0.083 | `{'contact_gate_failed': 2, 'success_event_contact_gated_true_pinch_release_ball': 5, 'lift_gate_failed': 1}` | `tie_diagnostic` |
| 2 | `di_qhead_prelift_xneg_s0003_m0006` | 5 / 8 | 6 | 5 | 5 | 8 | 0 | 0.625 | 0.119 | `{'contact_gate_failed': 2, 'success_event_contact_gated_true_pinch_release_ball': 5, 'lift_gate_failed': 1}` | `tie_diagnostic` |
| 3 | `di_contact_gate300_settle60` | 5 / 8 | 6 | 5 | 5 | 8 | 0 | 0.625 | 0.122 | `{'contact_gate_failed': 2, 'success_event_contact_gated_true_pinch_release_ball': 5, 'lift_gate_failed': 1}` | `tie_diagnostic` |
| 4 | `baseline_di_off` | 5 / 8 | 6 | 5 | 5 | 8 | 0 | 0.625 | 0.131 | `{'contact_gate_failed': 2, 'success_event_contact_gated_true_pinch_release_ball': 5, 'lift_gate_failed': 1}` | `frozen_anchor` |
| 5 | `di_contact_gate260` | 5 / 8 | 6 | 5 | 5 | 8 | 0 | 0.625 | 0.131 | `{'contact_gate_failed': 2, 'success_event_contact_gated_true_pinch_release_ball': 5, 'lift_gate_failed': 1}` | `tie_diagnostic` |
| 6 | `di_contact260_qhead_close_s002_m010` | 5 / 8 | 6 | 5 | 5 | 8 | 20 | 0.625 | 0.131 | `{'contact_gate_failed': 2, 'success_event_contact_gated_true_pinch_release_ball': 5, 'lift_gate_failed': 1}` | `tie_diagnostic` |
| 7 | `di_qhead_close_s002_m010_w100` | 5 / 8 | 6 | 5 | 5 | 8 | 20 | 0.625 | 0.131 | `{'contact_gate_failed': 2, 'success_event_contact_gated_true_pinch_release_ball': 5, 'lift_gate_failed': 1}` | `tie_diagnostic` |
| 8 | `di_qhead_wait_w120` | 5 / 8 | 6 | 5 | 5 | 8 | 24 | 0.625 | 0.131 | `{'contact_gate_failed': 2, 'success_event_contact_gated_true_pinch_release_ball': 5, 'lift_gate_failed': 1}` | `tie_diagnostic` |
| 9 | `di_qhead_close_s003_m012_w120` | 5 / 8 | 6 | 5 | 5 | 8 | 24 | 0.625 | 0.131 | `{'contact_gate_failed': 2, 'success_event_contact_gated_true_pinch_release_ball': 5, 'lift_gate_failed': 1}` | `tie_diagnostic` |
| 10 | `lift_ls460_off` | 5 / 8 | 6 | 5 | 5 | 8 | 0 | 0.625 | 0.147 | `{'contact_gate_failed': 2, 'success_event_contact_gated_true_pinch_release_ball': 5, 'lift_gate_failed': 1}` | `tie_diagnostic` |
| 11 | `ls460_gz0021_off` | 5 / 8 | 6 | 5 | 5 | 8 | 0 | 0.625 | 0.147 | `{'contact_gate_failed': 2, 'success_event_contact_gated_true_pinch_release_ball': 5, 'lift_gate_failed': 1}` | `tie_diagnostic` |
| 12 | `ls460_gz0021_qhead_close_s002_m010` | 5 / 8 | 6 | 5 | 5 | 8 | 20 | 0.625 | 0.147 | `{'contact_gate_failed': 2, 'success_event_contact_gated_true_pinch_release_ball': 5, 'lift_gate_failed': 1}` | `tie_diagnostic` |
| 13 | `ls460_qhead_close_s002_m010_w100` | 5 / 8 | 6 | 5 | 5 | 8 | 20 | 0.625 | 0.147 | `{'contact_gate_failed': 2, 'success_event_contact_gated_true_pinch_release_ball': 5, 'lift_gate_failed': 1}` | `tie_diagnostic` |

## Validation Ranking

| rank | variant | success | contact | lift | true pinch | release | residual events | hold tip | hold non-tip | reasons | decision |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|

## Selected Diagnostic Outcome

- Variant: `di_qhead_pid_close_s002_w100`
- Candidate family: `quality_pid_like`
- Validation success: `5 / 8`
- Contact/lift/true-pinch/release: `6` / `5` / `5` / `8`
- Residual events: `111`
- Terminal reasons: `{'contact_gate_failed': 2, 'success_event_contact_gated_true_pinch_release_ball': 5, 'lift_gate_failed': 1}`

## Decision

Best candidate tied D-I on matched validation. Keep it as diagnostic only; do not promote without a multiseed gain.

## Next

- If validation beats frozen D-I without morphology regression, run the multiseed 150-trial gate.
- If residuals only trade lift/contact/morphology failures, keep D-I frozen and move to contact geometry or richer residual-policy data.
