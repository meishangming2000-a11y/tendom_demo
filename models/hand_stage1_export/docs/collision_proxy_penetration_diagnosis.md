# Collision Proxy Penetration Diagnosis

Generated: 2026-05-26T02:09:10

## Scope

Static open/close pose diagnosis for current baseline and wrist2/collision-tuned experimental scene. No CAD, STL, joint tree, or joint names were modified by this diagnostic script.

## Ball Positions

- `[0.0, -0.1, 0.21]`: default
- `[0.0, -0.08, 0.21]`: variant
- `[0.0, -0.1, 0.195]`: variant
- `[0.0, 0.1, 0.21]`: mirror-side diagnostic

## Summary Table

| scene | ball | stage | contacts | max pen (m) | ball-hand contacts | ball-hand max pen (m) | source counts |
|---|---|---|---:|---:|---:|---:|---|
| current_baseline | `[0.0, -0.1, 0.21]` | open_hand | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| current_baseline | `[0.0, -0.1, 0.21]` | preshape | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| current_baseline | `[0.0, -0.1, 0.21]` | close_four_fingers | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| current_baseline | `[0.0, -0.1, 0.21]` | close_thumb | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| current_baseline | `[0.0, -0.08, 0.21]` | open_hand | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| current_baseline | `[0.0, -0.08, 0.21]` | preshape | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| current_baseline | `[0.0, -0.08, 0.21]` | close_four_fingers | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| current_baseline | `[0.0, -0.08, 0.21]` | close_thumb | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| current_baseline | `[0.0, -0.1, 0.195]` | open_hand | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| current_baseline | `[0.0, -0.1, 0.195]` | preshape | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| current_baseline | `[0.0, -0.1, 0.195]` | close_four_fingers | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| current_baseline | `[0.0, -0.1, 0.195]` | close_thumb | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| current_baseline | `[0.0, 0.1, 0.21]` | open_hand | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| current_baseline | `[0.0, 0.1, 0.21]` | preshape | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| current_baseline | `[0.0, 0.1, 0.21]` | close_four_fingers | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| current_baseline | `[0.0, 0.1, 0.21]` | close_thumb | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| wrist2_collision_tuned | `[0.0, -0.1, 0.21]` | open_hand | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| wrist2_collision_tuned | `[0.0, -0.1, 0.21]` | preshape | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| wrist2_collision_tuned | `[0.0, -0.1, 0.21]` | close_four_fingers | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| wrist2_collision_tuned | `[0.0, -0.1, 0.21]` | close_thumb | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| wrist2_collision_tuned | `[0.0, -0.08, 0.21]` | open_hand | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| wrist2_collision_tuned | `[0.0, -0.08, 0.21]` | preshape | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| wrist2_collision_tuned | `[0.0, -0.08, 0.21]` | close_four_fingers | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| wrist2_collision_tuned | `[0.0, -0.08, 0.21]` | close_thumb | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| wrist2_collision_tuned | `[0.0, -0.1, 0.195]` | open_hand | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| wrist2_collision_tuned | `[0.0, -0.1, 0.195]` | preshape | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| wrist2_collision_tuned | `[0.0, -0.1, 0.195]` | close_four_fingers | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| wrist2_collision_tuned | `[0.0, -0.1, 0.195]` | close_thumb | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| wrist2_collision_tuned | `[0.0, 0.1, 0.21]` | open_hand | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| wrist2_collision_tuned | `[0.0, 0.1, 0.21]` | preshape | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| wrist2_collision_tuned | `[0.0, 0.1, 0.21]` | close_four_fingers | 0 | 0.000000 | 0 | 0.000000 | `{}` |
| wrist2_collision_tuned | `[0.0, 0.1, 0.21]` | close_thumb | 0 | 0.000000 | 0 | 0.000000 | `{}` |

## Deepest Contacts By Case

### current_baseline

### wrist2_collision_tuned

## Diagnosis

- Tuned default open-hand max penetration: `0.000000` m.
- Tuned default close-thumb max penetration: `0.000000` m.
- If default-side ball contact remains poor while mirror-side contact is natural, treat it as a grasp-side placement issue rather than a collision-proxy issue.
- The four-finger `*_mcp_flex_joint` names are retained, but their current mechanical role is lateral spread / abduction-adduction.
