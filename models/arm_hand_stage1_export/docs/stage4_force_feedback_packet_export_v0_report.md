# Stage4 Force-Feedback Packet Export v0

Generated: `2026-06-14T02:28:40`

## Boundary

- MuJoCo-only replay from the frozen Stage3.11D-I demo-quality candidate.
- Exports simulated motor force-feedback into the Stage4 packet contract.
- Does not claim hardware runtime, real tactile sensors, real cameras, or direct force control.

## Outputs

- JSONL packets: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage4_force_feedback_packets_v0.jsonl`
- CSV summary: `D:\tendon_project\simulations\models\arm_hand_stage1_export\data\stage4_force_feedback_packets_v0_summary.csv`
- Metadata: `D:\tendon_project\simulations\models\arm_hand_stage1_export\metadata\stage4_force_feedback_packets_v0.json`
- Schema: `D:\tendon_project\docs\stage4_force_feedback_data_contract_v0.schema.json`

## Summary

- Episodes: `1 / 1` success in this export replay.
- Packets: `148`
- Phase counts: `{'approach': 9, 'preshape': 4, 'pinch_close': 8, 'contact_gate': 14, 'post_contact_settle': 2, 'slow_lift': 72, 'hold': 13, 'release_open': 8, 'release_settle': 17, 'final': 1}`
- Sequence range: `0..147`, dropped IDs `0`
- Timestamp monotonic: `True`
- Active-pair tension mean/max: `14.2661` / `67.7478 N`
- Active-pair balance mean/min: `0.6873` / `0.0000`
- Active-pair max |Iq|: `0.2464 A`
- lift_quality packets: `81`
- adjust_needed packets: `20`
- hold_safe packets: `13`
- abort_required packets: `8`
- fault_active packets: `0`
- Validation: `schema validation OK`

## Gate F1

This run passes Gate F1 when packet count is nonzero, sequence IDs are contiguous, timestamps are monotonic, and schema validation passes.

## Next

- F2: add a fake bench logger/replay that emits the same packets with timing and fault injection.
- Keep residual-policy work closed until F0/F1/F2 are all green.
