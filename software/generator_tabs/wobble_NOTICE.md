# Wobble tab - third-party notice

The Wobble tab ports the Unlicense-licensed cadin/line-wobbler
(https://github.com/cadin/line-wobbler). Its parameters map directly:
`frequency` (subpoint spacing), `amplitude` (perpendicular deviation),
`frequencyJitter` (parallel deviation as a percentage of the frequency), and
the two endpoint-wobble toggles, plus a seed for reproducibility.

The upstream class draws into a Processing canvas; this tab applies the same
subdivision and offset math to the current preview contours, so it runs as a
post-process after any tool has produced a preview.
