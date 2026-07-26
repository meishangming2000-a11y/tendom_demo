# Motor Bay Preflight: Parent Link Candidates

Generated: 2026-06-25

Scene inspected:

`simulations/models/hand_stage1_export/mjcf/scene_export4_connected_to_body_corrected_v10.xml`

All poses below are MuJoCo world poses at the default/zero state.

| candidate_parent_link | exists | body path | world pose | reason_for_candidate | risk | recommended_or_not |
|---|---:|---|---|---|---|---|
| `rough_body_support_link` | true | `/world/rough_body_support_link` | pos `[0.0, 0.0, 0.18]`, quat `[1.0, 0.0, 0.0, 0.0]` | Body/root support link. Best candidate if motor bay is fixed to the body/support frame. | Wrong if the motor bay actually moves with an arm/forearm segment. Body model is still PARTIAL / needs final CAD confirmation. | provisional recommended for body-fixed motor bay |
| `base_link` | true | `/world/rough_body_support_link/base_link` | pos `[0.0, 0.0, 0.18]`, quat `[0.5, 0.5, -0.5, 0.5]` | Arm root. Candidate if motor bay is fixed to the arm root after the body mount. | May make body-mounted geometry move with the arm root semantics; parent choice must be confirmed by CAD. | conditional, not default |
| `link_1` | true | `/world/rough_body_support_link/base_link/link_1` | pos `[0.0, 0.0, 0.18]`, quat `[0.5, 0.5, -0.5, 0.5]` | First actuated arm link. Candidate only if the motor bay is physically mounted on link_1. | Would move with joint `j1`; likely wrong for a body-side fixed motor bay. | not recommended unless CAD says link_1 |
| `link_2` | true | `/world/rough_body_support_link/base_link/link_1/link_2` | pos `[-0.014755, -0.133, 0.143629]`, quat `[0.6940200699, 0.1354100136, 0.1354120136, 0.6940200699]` | Moving arm segment candidate. | Would move with upstream joints; high risk unless motor bay is physically on link_2. | not recommended unless CAD says link_2 |
| `link_3` | true | `/world/rough_body_support_link/base_link/link_1/link_2/link_3` | pos `[0.0061697879, -0.2638298946, 0.1775061959]`, quat `[0.4929366242, -0.5069475003, 0.4831598263, 0.5163083368]` | Moving distal arm segment candidate. | Would move with upstream joints; high risk unless motor bay is physically on link_3. | not recommended unless CAD says link_3 |
| `ee_mount` | true | `/world/rough_body_support_link/base_link/link_1/link_2/link_3/ee_mount` | pos `[0.0084844505, -0.4093065967, 0.1198449446]`, quat `[0.706231354, 0.0349275511, 0.0241971882, 0.706704915]` | Existing arm/hand mounting body. Candidate if motor bay is actually the distal forearm/wrist-side housing between arm and hand. | Could crowd or obscure wrist/hand mount; must preserve existing `hand_base_link` and active joint tree. | conditional recommended for wrist-side motor bay only |
| `ee_tool_frame` | true | `/world/rough_body_support_link/base_link/link_1/link_2/link_3/ee_mount/ee_tool_frame` | pos `[-0.006282642, -0.3884405437, 0.1781650142]`, quat `[0.6819651818, -0.2538650332, -0.6275246381, 0.2769275435]` | Existing tool/reference frame. Useful as a reference frame for measurement. | This is not the preferred load-bearing parent; using it as parent may create confusing frame semantics. | not recommended as parent |
| `hand_base_link` | true | `/world/rough_body_support_link/base_link/link_1/link_2/link_3/ee_mount/hand_base_link` | pos `[-0.0110737006, -0.431056569, 0.1764019929]`, quat `[0.652955336, 0.6321888304, -0.2713901172, -0.3167554516]` | Hand root. Candidate only if motor bay is physically part of the hand base. | Would couple motor bay to hand root and may confuse future hand-only assumptions. | not recommended |
| `wrist_middle_link` | true | `/world/rough_body_support_link/base_link/link_1/link_2/link_3/ee_mount/hand_base_link/wrist_middle_link` | pos `[-0.0223973471, -0.4408613722, 0.1772025335]`, quat `[-0.4213059235, 0.002360024, -0.0303124941, -0.906408794]` | Wrist link. Candidate only for wrist-local visual references. | Moves with `wrist_1_joint`; not appropriate for a fixed motor bay housing. | not recommended |
| `palm_link` | true | `/world/rough_body_support_link/base_link/link_1/link_2/link_3/ee_mount/hand_base_link/wrist_middle_link/palm_link` | pos `[-0.0373757354, -0.4545451699, 0.1776009112]`, quat `[-0.2599184543, -0.611635522, 0.3331546314, -0.6688440602]` | Palm link. Useful only as a hand-side reference. | Moves with wrist joints; would alter hand-local geometry semantics. | not recommended |

## Current Recommendation

Do not decide the parent from file names alone.

Provisional recommendation:

- Use `rough_body_support_link` if `motor_bay_fixed_v0` is fixed to the
  body/support structure.
- Use `ee_mount` only if hardware confirms that the motor bay is a distal
  forearm/wrist-side housing that should move with the arm end while preserving
  the existing hand mount.

Final parent link is `UNKNOWN` until the SolidWorks export or user note states
the intended parent.
