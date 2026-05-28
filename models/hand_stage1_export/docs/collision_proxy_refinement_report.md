# Collision Proxy Refinement Report

## Scope

- Model: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_visual_clean_collision_proxy.xml`
- Scene: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_visual_clean_collision_proxy.xml`
- Clean STL meshes are visual-only.
- Collision uses simplified primitive proxy geoms.
- No CAD/STL/joint-tree/joint-name changes were made for this report.

## Current Proxy Inventory

- Hand collision proxy geoms: 28
- Scene collision geoms including ball and ground: 30
- Hand proxy mask: `contype=1`, `conaffinity=2`
- Ball mask: `contype=2`, `conaffinity=1`
- Ground mask: `contype=1`, `conaffinity=3`
- Result: hand-ball and hand-ground contacts are enabled; hand-hand self-collision is disabled for this smoke-test stage.

Main proxy types:

- `hand_base_link`: box
- `wrist_middle_link`: capsule
- `palm_link`: ellipsoid
- palm-to-finger/root spokes: capsules
- long finger links: capsules
- thumb links: capsules

## Sweep Evidence

The four-finger sweep used the current collision proxy with the thumb held open.

- Sweep positions: 27
- PASS: 15
- PARTIAL: 10
- FAIL: 2
- Worst open-hand ball contact count: 0
- Best ball position: `[0.0, -0.1, 0.21]`
- Best hold contacts: 3
- Best hold max penetration: `0.006741 m`
- Best hold mean four-fingertip distance: `0.035715 m`
- Max hold penetration in sweep: `0.022373 m`

The default low-overlap region is still credible. At `[0.0, -0.1, 0.195]`, open-hand contact is 0 and the four-finger hold remains close to the earlier position-control smoke test.

## Findings

### Palm Proxy

Status: usable, needs later tuning.

- The current palm ellipsoid does not create open-hand contact for any of the 27 swept ball positions.
- This means the earlier ball overlap issue was mainly ball placement plus early proxy/mask behavior, not a persistent palm proxy blocker.
- TODO: visually tune the palm ellipsoid after thumb opposition is repaired, because a real free-ball grasp will need palm support rather than only finger distal contact.

Severity: MINOR for current smoke test, MAJOR for future physical grasp.

### Finger Proxies

Status: usable for four-finger smoke testing.

- Distal and intermediate finger capsules produce contacts near the ball during hold.
- Best and default positions show mean four-fingertip distance around `0.034-0.036 m`, which is appropriate for a ball radius of `0.025 m` in a scripted smoke test.
- Some positions show high penetration despite good fingertip distances, especially:
  - `[0.02, -0.1, 0.195]`: max penetration `0.022373 m`
  - `[0.0, -0.12, 0.21]`: max penetration `0.018485 m`
- These high penetration cases suggest the proxy capsules are a little coarse for side-biased or farther ball placements.

Severity: MINOR for current pinned-ball smoke test, MAJOR before free-ball physical validation.

### Fingertip Proxy

Status: incomplete.

- Fingertip sites exist: `index_tip_site`, `middle_tip_site`, `ring_tip_site`, `little_tip_site`, `thumb_tip_site`.
- Dedicated fingertip collision spheres are not yet modeled as separate contact geoms.
- Distal capsule proxies currently act as fingertip contact approximations.
- TODO: add small fingertip sphere/capsule-end proxy geoms after link axes are confirmed.

Severity: MAJOR for stable free-object grasp and contact analysis.

### Thumb Proxy

Status: not the current root cause; thumb mechanics remain the blocker.

- Thumb collision capsules exist for `thumb_root_connector_link`, `thumb_metacarpal_link`, `thumb_proximal_link`, and `thumb_distal_link`.
- Thumb-to-ball distance remains large because the thumb kinematic sweep does not produce useful opposition.
- Do not tune thumb proxy shape to hide a kinematic/axis issue.
- TODO: revisit thumb proxy only after `thumb_cmc_joint`, `thumb_mcp_joint`, `thumb_ip_joint` axes and body frames are checked in SolidWorks.

Severity: MAJOR, but blocked by thumb axis/csys semantics rather than proxy geometry alone.

## Recommendations

1. Keep current proxy model for four-finger scripted smoke tests.
2. Keep clean STL visual-only; do not switch STL meshes to collision.
3. Do not tune thumb collision until thumb mechanical semantics are confirmed.
4. Next collision changes should be small and explicit:
   - add distal fingertip sphere geoms;
   - slightly reduce side-case distal/intermediate capsule radii if penetration remains above `0.01 m`;
   - add a palm support proxy only after the ball free-body controller and thumb opposition improve.
5. Continue using pinned-ball and zero-gravity tests as smoke tests only; do not treat them as stable grasp proof.

## Tomorrow's Proxy TODO

- Inspect side-biased ball position `[0.02, -0.1, 0.195]` visually before shrinking any capsules.
- Inspect farther ball position `[0.0, -0.12, 0.21]` visually before changing palm/finger proxy positions.
- Add fingertip collision spheres once thumb and long-finger axes are considered mechanically credible.
- Re-run `sweep_four_finger_grasp_ball.py` after every proxy size change.
