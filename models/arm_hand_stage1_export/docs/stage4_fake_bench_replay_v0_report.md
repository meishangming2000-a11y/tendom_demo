# Stage4 Fake Bench Replay v0

Generated: `2026-06-13T01:50:16`

## Boundary

- Fake bench/logger replay only.
- Input is F1 MuJoCo force-feedback packet data.
- Output source is `bench_replay`, not real hardware.
- No motor, sensor, or controller hardware runtime is claimed.

## Outputs

- Input JSONL: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage4_force_feedback_packets_v0.jsonl`
- Replay JSONL: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage4_fake_bench_replay_v0.jsonl`
- CSV summary: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage4_fake_bench_replay_v0_summary.csv`
- Metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage4_fake_bench_replay_v0.json`

## Summary

- Source slots: `1200`
- Emitted packets: `1188`
- Sequence range: `0..1199`
- Dropped sequence IDs detected: `12`
- Timestamp monotonic: `True`
- Target / observed sample rate: `200.000` / `200.000 Hz`
- Rate error fraction: `0.000000`
- Fault-active packets: `35`
- Phase counts: `{'approach': 81, 'preshape': 36, 'pinch_close': 67, 'contact_gate': 111, 'post_contact_settle': 15, 'slow_lift': 570, 'hold': 104, 'release_open': 63, 'release_settle': 133, 'final': 8}`
- Schema validation: `schema validation OK`

## Fault Injection

| fault | injected | detected | detection rate |
|---|---:|---:|---:|
| `drop_packet` | 12 | 12 | 1.000 |
| `delay_spike` | 14 | 14 | 1.000 |
| `current_saturation` | 8 | 8 | 1.000 |
| `encoder_freeze` | 6 | 6 | 1.000 |
| `bus_voltage_sag` | 5 | 5 | 1.000 |
| `tension_dropout` | 6 | 6 | 1.000 |
| `driver_fault` | 9 | 9 | 1.000 |
| `e_stop` | 1 | 1 | 1.000 |

## Gate F2

- Packet count >= `1000`: `True`
- Timestamp monotonic: `True`
- Dropped sequence IDs counted correctly: `True`
- Sample-rate median stable: `True`
- Fault detection: `True`

F2 passes only if every item above is `True` and schema validation is OK.

## Next

- F3 signal coverage / calibration matrix.
- Keep residual-policy reopening closed until F0/F1/F2/F3 are all documented.
