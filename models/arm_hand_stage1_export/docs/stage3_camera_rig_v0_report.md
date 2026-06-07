# Stage3 Camera Rig V0 Report

Generated: 2026-06-03

## Purpose

Define the default visual convention for Stage3 demos.

Future Stage3 demos should render both named MuJoCo cameras:

- `stage3_egg_overview`
- `stage3_egg_closeup`

## Camera Roles

| Camera | Role | Intended use |
|---|---|---|
| `stage3_egg_overview` | Whole-task overview | Check arm/hand trajectory, object location, and gross scene framing |
| `stage3_egg_closeup` | Object/contact closeup | Check approach, contact acquisition, gentle close, slip/drop symptoms, and hold stability |

## Current Visual Check

Current contact sheet:

```text
docs/visual_checks_stage3_camera_rig_v0/stage3_camera_rig_contact_sheet_updated.png
```

Rendered frames:

```text
docs/visual_checks_stage3_camera_rig_v0/stage3_egg_overview_updated.png
docs/visual_checks_stage3_camera_rig_v0/stage3_egg_closeup_updated.png
```

## Verdict

Use these two camera views as the default Stage3 demo output.

The closeup camera was adjusted to keep the egg-like object unobstructed while
leaving the hand visible in the background. The same camera name is preserved so
future scripts can render by name without special-case camera parameters.

## Demo Output Rule

Every Stage3 demo should emit at least:

- one overview render or video from `stage3_egg_overview`
- one closeup render or video from `stage3_egg_closeup`
- one contact sheet combining both views
- a JSON summary listing camera names and output paths

This is a visual QA convention only. It does not change task success criteria or
claim real camera integration.
