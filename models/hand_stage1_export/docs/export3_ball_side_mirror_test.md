# Export3 Ball Side Mirror Test

Status: four-finger-only ball-side diagnostic. Thumb target tuning is paused.

| Ball position | On inferred palmar side? | Palmar projection (m) | Open contacts | Hold contacts | Max penetration | Mean open tip-ball | Mean hold tip-ball | Visual note |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `[0.0, -0.1, 0.21]` | True | 0.064183 | 0 | 5 | 0.010240 | 0.094482 | 0.033073 | more consistent with palm-side scripted closure |
| `[0.0, 0.1, 0.21]` | False | -0.104727 | 0 | 0 | 0.000000 | 0.163379 | 0.202116 | dorsal side; weak four-finger proximity |
| `[0.0, -0.08, 0.21]` | True | 0.047292 | 0 | 5 | 0.009834 | 0.084298 | 0.039684 | more consistent with palm-side scripted closure |
| `[0.0, 0.08, 0.21]` | False | -0.087836 | 0 | 0 | 0.000000 | 0.145994 | 0.182393 | dorsal side; weak four-finger proximity |

## Interpretation

- Current negative-Y ball is clearly closer to four fingertips after close; ball side may be consistent with scripted closure.
- This test excludes thumb motion; it only checks palm side and long-finger closure.

## Visual Judgment

- Current `[0.0, -0.1, 0.21]` ball placement is the only tested side that the four long fingers can approach in this export3 setup.
- Mirrored `[0.0, 0.1, 0.21]` and `[0.0, 0.08, 0.21]` are visually on the opposite/far side and produce zero hold contacts.
- Therefore, the current odd-looking grasp is not explained by the ball simply being on the wrong Y side.
- Next check should focus on palm CSYS/anatomical side labeling and whether the visible CAD palm/dorsal mesh orientation is flipped relative to the intended robot hand.
