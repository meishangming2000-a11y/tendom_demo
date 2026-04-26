# Export Notes

Stage 1 is intentionally conservative:

- visual geometry is placeholder-only and ASCII-safe
- collision remains primitive-first for reliable loading
- body names and actuator names are stable and should be preserved when real meshes arrive

Recommended later export flow:

1. confirm the authoritative CAD assembly revision
2. export per-link visual meshes, not one full assembly mesh
3. keep filenames ASCII-safe when copying into `assets/meshes/visual/`
4. add separate simplified collision assets only after the visual chain is stable
