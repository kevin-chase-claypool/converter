# Documentation Map

Use this page to find the shortest authoritative path for a task. Do not read
the entire documentation tree before working.

For a visual overview of this process, open
[`codex-documentation-flow.html`](codex-documentation-flow.html).

## Start by task

| Task | Read first | Current source of truth |
|---|---|---|
| Windows converter UI or behavior | [`../software/README.md`](../software/README.md) | Code under `software/`; behavior in `software/README.md` |
| Converter algorithms or historical tradeoffs | [`HANDOFF.md`](HANDOFF.md) relevant section only | Code under `software/converter_core/`; deep rationale in `HANDOFF.md` |
| RP23CNC/grblHAL work | [`../firmware/README.md`](../firmware/README.md) | Relevant file under `firmware/grblhal/` |
| Pen-pressure firmware | [`../firmware/pen_pressure/README.md`](../firmware/pen_pressure/README.md) | `firmware/pen_pressure/` |
| Wiring or pin assignment | [`hardware/WIRING_TABLE.md`](hardware/WIRING_TABLE.md) | `hardware/WIRING_TABLE.md` |
| Part selection or electrical rating | [`hardware/BOM.md`](hardware/BOM.md) | `hardware/BOM.md` |
| Subsystem interface or units | [`integration/INTERFACES.md`](integration/INTERFACES.md) | `integration/INTERFACES.md` |
| Current priorities | [`project/ROADMAP.md`](project/ROADMAP.md) | `project/ROADMAP.md` |
| Test or bench work | [`testing/TEST_PLAN.md`](testing/TEST_PLAN.md) | Test plan plus `report/lab-notes/` evidence |
| Why a lasting decision was made | [`decisions/`](decisions/) | Applicable ADR |
| What changed recently | [`changes/INDEX.md`](changes/INDEX.md) | Categorized change note |
| Chronological successes and failures | [`project/ENGINEERING_LOG.md`](project/ENGINEERING_LOG.md) | Engineering log |

## Document roles

Each type has one job:

- **Current-state documents** describe how the project works now.
- **Change notes** explain one meaningful change, its verification, and risks.
- **Engineering log** records milestones, failures, measurements, and decisions
  in chronological order. Its generated topic index links to those same entries
  without copying their bodies.
- **Roadmap** tracks incomplete and completed project work.
- **ADRs** preserve decisions with lasting architectural consequences.
- **Lab notes** contain raw physical-test evidence.
- **Git history** remains the record for incidental edits and mechanical
  cleanup that do not warrant a separate narrative.

Avoid copying the same detailed explanation into multiple documents. Put the
full detail in the authoritative document and link to it elsewhere.

## Large reference documents

[`HANDOFF.md`](HANDOFF.md) is a deep technical reference and historical design
record. Search it by topic; it is not required front-to-back reading.

[`project/ENGINEERING_LOG.md`](project/ENGINEERING_LOG.md) is intentionally
append-only and will grow. Search by component, test ID, status, or error text.

## Validation

After documentation changes:

```powershell
python tools\docs_index.py --write
python tools\docs_index.py --check
```

The first command rebuilds change indexes from note metadata. The second checks
generated indexes, note metadata, duplicate IDs, and local Markdown links.
