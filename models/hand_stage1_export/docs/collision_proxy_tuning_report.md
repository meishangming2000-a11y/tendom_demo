# Collision Proxy Tuning Report

Generated: 2026-05-26T02:09:10

## Scope

This summarizes the experimental export4 wrist2/collision-proxy branch. Only collision proxy sizes/visual debug branch files were changed; CAD, STL, joint tree, joint names, and current-baseline files were not overwritten.

## What Changed In The Experimental MJCF

- `wrist_2_joint` is verified as a hinge/revolute joint in the experimental branch.
- Conservative collision proxy sizes were applied to palm, long-finger capsules, and thumb capsules.
- Clean STL remains visual-only; STL mesh geoms are not used as collision geoms.

## Static Penetration Result

| case | max penetration | contacts | ball-hand contacts | status |
|---|---:|---:|---:|---|
| tuned open, default `[0.0, -0.1, 0.21]` | 0.000000 | 0 | 0 | PASS_UNDER_5MM |
| tuned close, default `[0.0, -0.1, 0.21]` | 0.000000 | 0 | 0 | no static penetration, but no ball contact |
| tuned close, mirror `[0.0, 0.1, 0.21]` | 0.000000 | 0 | 0 | visually closer, still no contact |

## Grasp-Side Finding

- Default `-Y` grasp demo status: **FAIL_GRASP_SIDE_OR_TARGET_NEEDS_REVIEW**.
- Mirror `+Y` grasp demo status: **PARTIAL_NO_CONTACT_BUT_VISUALLY_CLOSE**.
- Visual screenshots and fingertip distances both show the mirror `+Y` ball is closer to the closed fingers and thumb than the default `-Y` ball.
- I did not inflate the collision proxy to force contact across a large air gap. That would hide the palm-side / target-side issue.

## Recommendation

1. Keep the conservative proxy branch because open-hand static penetration is now zero in the tested poses.
2. Treat the default `-Y` ball side as unresolved for grasp smoke. Use the mirror-side diagnostics to decide the canonical palmar side before training or dataset expansion.
3. After the canonical ball side is fixed, add small distal fingertip collision spheres/capsule-end tuning if contact remains slightly short.

## Issue Severity

- BLOCKER: none for model loading or wrist_2 verification.
- MAJOR: default grasp side / target side does not produce contact.
- MINOR: collision proxy is conservative and will need final fingertip-radius tuning.
