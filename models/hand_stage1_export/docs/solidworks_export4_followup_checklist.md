# SolidWorks Export4 Follow-Up Checklist

Generated: 2026-05-25 14:57:12

This checklist lists unresolved or human-confirmation items after MuJoCo current-baseline audits.

| severity | item | observed issue | SolidWorks check |
|---|---|---|---|
| MAJOR | `thumb_cmc_abd_joint / thumb_cmc_joint` | Current scripted thumb works for smoke tests but CMC mechanical semantics are not finally signed off. | Confirm each CMC axis passes through the intended rotation center and that positive/negative directions match intended abd/flex. |
| MINOR | `index/middle/ring/little_mcp_flex_joint` | MCP-flex joints are audit-only because they may be lateral/spread joints in the current naming convention. | Confirm whether each MCP flex csys actually represents spread/side motion or flexion; do not rename unless SolidWorks semantics are final. |
| MJCF | `collision_proxy` | Collision proxy audit found tuning issues. | This is MJCF-side proxy tuning, not necessarily SolidWorks. Check only if proxy mismatch reflects wrong body/link geometry. |
