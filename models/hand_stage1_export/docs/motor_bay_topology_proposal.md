# Motor Bay Preflight: Topology Proposal

Generated: 2026-06-25

Scope: proposal only. No final motor bay scene is written here.

## Assumptions From User

- `motor_bay_link` is a rigid body.
- It does not add an active joint.
- It does not replace the hand.
- It does not require re-exporting the full model.
- Existing arm/wrist/hand joints must be preserved.
- `action_dim` and adapter mapping should stay unchanged.

## Direct Answers

1. Suggested parent link for this round:
   UNKNOWN final. Provisional recommendation is:
   - `rough_body_support_link` if the motor bay is body/support-fixed.
   - `ee_mount` if the motor bay is a distal forearm/wrist-side housing between
     the arm and hand.

   Do not finalize this choice until the user provides the intended parent link
   or the SolidWorks mount CSYS relationship.

2. Fixed to parent or static worldbody visual:
   Use a fixed child body under the confirmed parent link for the formal
   integration. A static `worldbody` visual is acceptable only as a one-off
   visual placement diagnostic, not as the final topology, because it loses the
   rigid-body parent semantics.

3. If parent cannot be judged:
   User must provide:
   - intended parent link name from the current scene;
   - `motor_bay_mount_csys` pose relative to that parent;
   - a screenshot or CAD note showing the motor bay attached to that parent.

4. Is a wrist-side reference frame needed:
   Optional for a pure body-fixed motor bay. Recommended if the motor bay
   interfaces with the wrist/hand side, cable exits, tendon routing, or future
   insertion between `ee_mount` and `hand_base_link`. Name it
   `motor_bay_wrist_mount_csys` if provided.

5. Will this change the existing hand/arm joint tree:
   It should not. The intended integration is a fixed child body with no active
   joint and no changes to `j1`-`j4`, `wrist_1_joint`, `wrist_2_joint`, or finger
   joints.

6. Will this affect `action_dim` / adapter mapping:
   No, if implemented as fixed visual/collision geometry only. Expected action
   dimension remains `26`.

## Proposed Topology

```text
rough_body_support_link
  base_link
    link_1
      link_2
        link_3
          ee_mount
            hand_base_link
              ...
```

For a body-fixed motor bay:

```text
rough_body_support_link
  motor_bay_link   # fixed child, no joint, no actuators
  base_link
    ...
```

For a wrist-side forearm housing:

```text
ee_mount
  motor_bay_link   # fixed child, no active joint
  hand_base_link   # existing child preserved
    ...
```

The second topology should be used only if CAD confirms that the motor bay
belongs at the distal arm/wrist interface.

## Do Not Do In This Round

- Do not add active joints.
- Do not insert a new joint between arm and hand.
- Do not change actuator order.
- Do not replace `hand_base_link`.
- Do not re-run training.
- Do not overwrite `scene_export4_connected_to_body_corrected_v10.xml`.
