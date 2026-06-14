# Stage3.11D Motor Force Feedback Simulation v0

Generated: `2026-06-11`

## Boundary

- Stage3 remains MuJoCo-only.
- This is a simulated motor-driver signal surface, not real hardware data.
- No real motor, encoder, current shunt, torque sensor, tactile sensor, or
  ultrasound data are integrated.
- The current implementation is for future control design and diagnostics; it
  is not a promoted controller baseline.

## What Motor Force Feedback Usually Means

For our tendon hand, the useful motor-side feedback signals are:

- `phase_current` / `iq_current`: motor current. In FOC, the q-axis current is
  the torque-producing current.
- `torque_estimate`: usually calculated from current and motor torque constant,
  not directly measured by a torque sensor.
- `encoder_position` and `encoder_velocity`: shaft or joint state, needed to
  distinguish load from motion.
- `dc_bus_voltage` and `dc_bus_current`: supply-side health and power-limit
  signals.
- `current_limit`, `saturation`, and `fault flags`: over-current, over-voltage,
  under-voltage, following error, thermal derating, and driver shutdown states.
- Optional future signals: inline tendon load cell, joint torque sensor, motor
  temperature, driver temperature, and calibrated gearbox/spool compliance.

Source notes:

- ODrive exposes torque control in Nm and uses a `torque_constant` to convert
  torque/current at the controller level:
  https://docs.odriverobotics.com/v/latest/manual/control.html
- ODrive API documents `Iq_measured` as the q-axis torque-generating current,
  with motor torque approximately `torque_constant * Iq_measured`:
  https://docs.odriverobotics.com/v/latest/fibre_types/com_odriverobotics_ODrive.html
- maxon states that motor torque is proportional to current through the torque
  constant:
  https://support.maxongroup.com/hc/en-us/articles/360013761160-Motor-data-and-simulation
- maxon EPOS/IDX torque actual values are calculated from measured current and
  torque constant; there is no direct torque measuring device in that drive
  object:
  https://support.maxongroup.com/hc/en-us/articles/360011690019-EPOS4-IDX-Object-Torque-actual-value
- TI's FOC material describes adjusting q-axis current to generate commanded
  torque:
  https://www.ti.com/lit/an/sprabz0/sprabz0.pdf
- ODrive hardware configuration also treats DC bus voltage/current as monitored
  protection signals:
  https://docs.odriverobotics.com/v/latest/manual/hardware-config.html

## Simulation Model

The new MuJoCo proxy is:

```text
simulations/models/arm_hand_stage1_export/external_sensors/mujoco_motor_force_feedback_sensor.py
```

It maps MuJoCo actuator load into driver-like signals:

```text
output_torque_nm ~= data.actuator_force[actuator_id]
motor_torque_nm = output_torque_nm / (gear_ratio * gear_efficiency)
iq_cmd_a = motor_torque_nm / torque_constant_nm_per_a
iq_measured_a = clamp(iq_cmd_a, current_limit_a) + sensor_noise
tendon_tension_n = abs(output_torque_nm) / spool_radius_m
encoder_position_rad = joint_position_rad * gear_ratio
encoder_velocity_rad_s = joint_velocity_rad_s * gear_ratio
```

Default assumptions:

- `torque_constant_nm_per_a = 0.035`
- `gear_ratio = 30`
- `gear_efficiency = 0.72`
- `spool_radius_m = 0.008`
- `current_limit_a = 4.0`
- `bus_voltage_v = 24.0`

These are explicit placeholders. They should be replaced by measured motor,
gearbox, spool, and driver values during Stage4 hardware work.

## Current Probe

The randomized event-gated robustness runner can enable this signal surface:

```powershell
python .\simulations\models\arm_hand_stage1_export\run_stage3_11d_b_event_contact_gated_robustness_v0.py --trials 24
```

Current result with motor feedback enabled:

- Randomized success: `13 / 24`
- Contact-gate success: `24 / 24`
- Lift gate success: `13 / 24`
- Release success: `24 / 24`
- Max simulated `|Iq|`: `3.0775 A`
- Max simulated tendon tension proxy: `287.1294 N`
- Max hand-side simulated `|Iq|`: `0.2097 A`
- Max hand-side tendon tension proxy: `19.3552 N`
- Current saturation trial fraction: `0.000`

Interpretation:

- The object contact event is robust in this small perturbation set.
- Failures are lift-window failures, not release failures.
- Global motor feedback is dominated by arm joint load, so controller logic must
  use hand/finger-side metrics for grasp control.
- Phase-wise hand-side tension separates the failure mode better than the
  contact event alone:
  - Contact gate mean hand tension: success `7.93 N`, failure `10.28 N`.
  - Slow-lift mean hand tension: success `1.95 N`, failure `1.30 N`.
  - Hold mean hand tension: success `1.14 N`, failure `0.58 N`.
- Force feedback should first be used as a lift permission / lift-continuation
  signal: do not trust the contact event alone; require thumb+middle morphology
  plus sustained hand-side tension during slow lift.
- Because current saturation stayed zero in this run, the next controller
  experiment should not increase current blindly. It should use current/tension
  balance to decide whether to preload, wait, micro-adjust pose, or abort lift.

## Next Control Direction

Update after the force-feedback/offset expansion pass:

- Active-pair force summaries are now implemented for thumb + active finger.
- The preload-style force gate was tested and regressed from `13 / 24` to
  `9 / 24`; it raised pair tension but disturbed the two-tip geometry.
- The conservative wait-only gate held `13 / 24`; it avoided regression but did
  not rescue lift failures.
- A small geometry correction, `--base-grasp-offset-x-delta -0.0008`, improved
  the 50-trial randomized probe from `29 / 50` to `34 / 50`.
- Therefore, force feedback should be treated as observation, quality gate, and
  future residual-controller input first. It should not yet be used as a direct
  "close harder" controller.
- Stage3.11D-C then selected the `gx=-0.0008 m, gz=0.0020 m,
  tip_pair_separation=0.060 m` geometry center and reached `43 / 50`
  randomized full true-pinch-release success. The selected run had mean
  slow-lift active-pair tension `7.8862 N`, mean hold active-pair tension
  `4.3746 N`, and saturation trial fraction `0.000`.

Current closeout:

```text
simulations/models/arm_hand_stage1_export/docs/stage3_11d_b_force_feedback_offset_expansion_v0_closeout.md
```

Stage3.11D-C closeout:

```text
simulations/models/arm_hand_stage1_export/docs/stage3_11d_c_geometry_force_refine_v0_closeout.md
```

1. Use `gx -0.0008 m` as the next local-search center, not as a promoted
   baseline.
2. Refine geometry with coupled variables:
   `grasp_offset_x`, `grasp_offset_z`, `tip_pair_separation_target`, thumb
   abduction/MCP, and active-finger abduction/PIP.
3. Keep force feedback in the observation/gate surface:
   active-pair hold tension, active-pair balance, hand-side current margin, and
   saturation flags.
4. Design a residual micro-adjust phase:
   use force feedback to choose small pose/closure corrections, not blind
   preload.
5. Validate against MuJoCo contact truth:
   compare motor-current proxy with actual contact morphology, penetration,
   lift success, release success, and close-up visual evidence.

## If Successful

Use the force-feedback proxy as a core Stage3.11E input for constrained
residual/full-action experiments.

## If Failed

Do not relax success thresholds. First calibrate the simulated motor constants,
spool radius, gear ratio, fingertip proxy geometry, and contact material model.
