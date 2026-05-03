# custom_tendon_hand_template

Template for the future custom tendon-hand MuJoCo import.

This directory is intentionally metadata-first. Do not put generated CAD export
output here until the custom hand model is ready to be checked in under a real
model directory such as `models/custom_tendon_hand/`.

## Expected First Import

The first custom hand import should be minimal and runnable:

- one root body
- one mount site
- one palm reference site
- named joints with limits
- named actuators with control ranges
- conservative collision for palm and fingertips
- metadata for tendon, motor, and joint ownership

The recommended model filename for the first real import is:

`models/custom_tendon_hand/robot.xml`

The recommended combo wrapper after standalone compile is:

`models/arm_stage1_custom_hand_combo/scene.xml`

## Validation Command

From `simulations/`, after the real model exists:

```bash
python scripts/diagnostics/check_mujoco_model.py --model models/custom_tendon_hand/robot.xml --require-body custom_hand_root --require-site custom_hand_mount_site --require-site custom_palm_site
```
