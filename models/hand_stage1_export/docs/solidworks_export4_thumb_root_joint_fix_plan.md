# SolidWorks Export4 Thumb Root Joint Fix Plan

Status: diagnostic plan after export3 axis/missing-joint audit. Do not treat this as a CAD edit log.

## What Export3 Actually Contains

```text
palm_link
-> thumb_root_connector_fixed_joint [fixed]
-> thumb_root_connector_link
-> thumb_cmc_abd_joint [revolute]
-> thumb_trapezium1_link
-> thumb_cmc_flex_joint [revolute]
-> thumb_metacarpal_link
-> thumb_mcp_joint [revolute]
-> thumb_proximal_link
-> thumb_ip_joint [revolute]
-> thumb_distal_link
```

Export3 active thumb DoF count:

- CMC/root area: 2 active joints
- MCP/IP area: 2 active joints
- Total active thumb joints: 4
- Fixed thumb root connector: 1

## Current Findings

- `thumb_cmc_abd_joint` sign is reversed relative to an intuitive positive-opposition convention.
  - `+0.6 rad` moves thumb farther from the ball/index side.
  - `-0.6 rad` moves thumb closer to the ball/index side.
- `thumb_cmc_flex_joint` also needs SolidWorks sign/axis confirmation.
- The tuned target found a numeric workaround by using negative CMC abd, but this should not be treated as a correct mechanical fix.
- If the thumb root should have one more active opposition/twist joint, it is missing from export3 URDF/MJCF.

## Likely Missing Structure

If the real thumb base needs three root/CMC motions, export4 should add a distinct intermediate link and joint. One possible structure is:

```text
palm_link
-> thumb_root_connector_fixed_joint [fixed]
-> thumb_root_connector_link
-> thumb_cmc_root_joint [revolute, new if physically needed]
-> thumb_cmc_root_link [new massless/dummy or real moving root part]
-> thumb_cmc_abd_joint [revolute]
-> thumb_trapezium1_link
-> thumb_cmc_flex_joint [revolute]
-> thumb_metacarpal_link
-> thumb_mcp_joint [revolute]
-> thumb_proximal_link
-> thumb_ip_joint [revolute]
-> thumb_distal_link
```

Use CAD-native names if you prefer; the names above are only placeholders.

## What To Check In SolidWorks

1. Decide whether the apparent missing root joint is real.
   - If yes, identify the two rigid bodies it connects.
   - If both axes act on the same physical part, add a dummy/intermediate link or reference part so URDF can represent serial joints.

2. Check `thumb_cmc_abd_joint` CSYS/axis.
   - Desired convention: positive angle should move thumb toward palm/index opposition.
   - Current export3 convention: negative angle moves toward opposition.
   - Fix by flipping the SolidWorks axis/CSYS, not by relying on negative controller targets.

3. Check `thumb_cmc_flex_joint` CSYS/axis.
   - Confirm which direction is flexion.
   - Confirm whether negative flex should be allowed.
   - If positive flex visually bends away from opposition, flip the axis or rename semantics before export4.

4. Check `thumb_mcp_joint`.
   - User confirmed the physical axis location is credible.
   - Still confirm sign convention: positive should be thumb MCP flexion if that is the intended controller convention.

5. Check `thumb_ip_joint`.
   - Positive should curl the distal thumb link inward.

## Export4 Requirements

- Do not overwrite export3.
- Export to a new folder, for example:

```text
D:\tendon_project\hardwares\hand\hand_export4
```

- Keep clean per-link STL export.
- Keep `D18d12H4.STEP` and `Trapezium3.STEP` fixed under `thumb_root_connector_link`.
- Keep `Trapezium1.STEP` as the first moving CMC link unless SolidWorks confirms a different moving hierarchy.
- Keep `Os metacarpale I 3.STEP` under `thumb_metacarpal_link`.
- If a new root joint is added, export a real or dummy intermediate link so the URDF tree contains it explicitly.

## Post-Export Verification

After export4:

1. Import export4 into `simulations\models\hand_stage1_export\export4\`.
2. Re-run URDF tree check.
3. Confirm thumb active joint count.
4. Re-run `audit_export3_thumb_missing_joint_and_axis.py` adapted to export4.
5. Re-run thumb opposition audit.
6. Only then update scripted grasp targets.
