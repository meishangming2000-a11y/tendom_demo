# Export2 Collision And Ball Position Retry Report

## What Changed

- Kept the export2 joint tree, joint names, and clean STL mesh mapping unchanged.
- Kept `hand_stage1_clean_mesh_export2_draft.xml` as the clean mesh source.
- Added retry scene: `mjcf/scene_ball_clean_mesh_export2_retry.xml`.
- Added retry scripts:
  - `scripts/run_export2_ballpos_retry.py`
  - `scripts/demo_grasp_ball_export2_retry.py`

## Collision Diagnosis

The clean STL visual geoms are intentionally visual-only:

- `contype="0"`
- `conaffinity="0"`
- `group="2"`

So the clean CAD mesh itself does not collide with the ball yet. Ball contacts currently happen against the primitive collision geoms that remain in the model.

The scripted demo also directly writes hand joint `qpos` and ball freejoint `qpos`; it is not a force/actuator/controller grasp. Because of that, MuJoCo contacts do not automatically push the ball out of the hand during the scripted pose sequence.

## Old Ball Position Problem

Old ball position:

- `[0.01, -0.045, 0.215]`

Measured ball contacts:

| Stage | Ball contacts | Min contact dist |
|---|---:|---:|
| open_hand | 4 | -0.012230 m |
| hold | 6 | -0.022275 m |

Conclusion: the old default ball position started inside the hand/primitive collision shell. This explains the visible hand-ball overlap.

## Retry Ball Position

Selected conservative retry position:

- `[0.0, -0.1, 0.195]`

Measured ball contacts:

| Stage | Ball contacts | Max penetration | Mean 4-fingertip distance |
|---|---:|---:|---:|
| open_hand | 0 | 0.000000 m | 0.105781 m |
| hold | 2 | 0.005000 m | 0.034357 m |

Visual screenshots:

- `docs/visual_checks_export2_retry/low_penetration/open_hand.png`
- `docs/visual_checks_export2_retry/low_penetration/hold.png`
- `docs/visual_checks_export2_retry/low_penetration/hold_top.png`
- `docs/visual_checks_export2_retry/low_penetration/hold_side.png`
- `docs/visual_checks_export2_retry/live_demo/open_hand.png`
- `docs/visual_checks_export2_retry/live_demo/hold.png`

Visual conclusion:

- The ball no longer starts merged into the hand.
- Four long fingers now close toward the ball and visually wrap it.
- Hold-stage penetration is much smaller and comes from the scripted qpos pose pressing primitive collision geoms into the sphere.
- The thumb still does not oppose the ball correctly.

## Direction Check

An all-flexion-axis flip was tested separately in `hand_stage1_clean_mesh_export2_graspfix.xml`.

Result:

- Original export2 axes hold-stage mean 4-fingertip distance: about `0.0613 m` at the old ball position.
- All-axis-flipped version hold-stage mean 4-fingertip distance: about `0.0947 m`.

Conclusion: globally flipping the closing axes made the grasp worse, so it was not promoted.

Thumb-specific axis flips were also checked in memory. Flipping only `thumb_cmc_joint`, `thumb_mcp_joint`, and/or `thumb_ip_joint` did not bring the thumb tip across to the ball. The thumb remains a TODO for CAD/URDF axis and joint-frame confirmation.

## Current Recommendation

Use the conservative retry script for visual continuation:

```powershell
python D:\tendon_project\simulations\models\hand_stage1_export\scripts\demo_grasp_ball_export2_retry.py --viewer
```

Optional ball overrides:

```powershell
python D:\tendon_project\simulations\models\hand_stage1_export\scripts\demo_grasp_ball_export2_retry.py --viewer --ball-x 0.0 --ball-y -0.1 --ball-z 0.195
```

Do not promote this as final physical grasp yet. It is a clean-mesh visual and kinematic smoke test.

## TODO

- Confirm thumb CMC/MCP/IP joint frames and axes in SolidWorks/URDF.
- Decide whether clean CAD mesh should get simplified collision capsules/boxes or convex collision proxies.
- Replace direct qpos teleporting with a simple position actuator/controller when moving from visual demo to physics demo.
- Keep `mcp_flex` / `mcp_abd` names unchanged until the real motion semantics are confirmed.
