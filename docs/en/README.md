# PyroLens Documentation — Index

All project documentation, by category. **Convention D1 (validated 2026-10-21)**:
the single source of published figures is `baselines/summary.csv` (and its
timestamped derivatives) — no phase 1 values are republished.

> **Languages**: the two flagship documents are available in English under
> [`../`](../) — [`../PROJECT_OVERVIEW.md`](../PROJECT_OVERVIEW.md) and
> [`../FIRE_RISK_PREDICTION.md`](../FIRE_RISK_PREDICTION.md). All other
> documents are in French (team working language).

---

## 1. Scientific (how figures are produced and what they are worth)

| Document | Content |
|---|---|
| [`../methodology.md`](../methodology.md) | research question, non-objectives, set keys (cell/window), filters, metrics, interpretation prohibitions |
| [`../phase2/data_validation.md`](../phase2/data_validation.md) | report A: row accounting, anomalies, quantitative reference figures (summarized from `summary.csv`), verification of phase 1 announcements (§7) |
| [`../phase2/scientific_method.md`](../phase2/scientific_method.md) | H1-H6 statuses, distinction "executed" ≠ "validated", citation rules |
| [`../phase2/validation_plan.md`](../phase2/validation_plan.md) | verification plans: figures, screens, regression, publication |
| [`../data_inventory.md`](../data_inventory.md) | real inventory of sources (CMR, FIRMS, Earthdata), acquisition state |
| [`../references.md`](../references.md) | scientific references and HTTP status of consulted APIs |
| [`../limitations.md`](../limitations.md) | assumed limits: scientific, data, API, frontend, and what to do if one blocks |

## 2. Technical (build, deploy, operate)

| Document | Content |
|---|---|
| [`../technical.md`](../technical.md) | architecture (pipeline → artifacts → front + API), installation, Freebuff deployment, errors/logs, security |
| [`../api.md`](../api.md) | API v1 contract: envelopes, error codes, each endpoint with curl examples, auth, OpenAPI export |
| [`../openapi.json`](../openapi.json) | machine specification exported from `/api/v1/openapi.json` (regenerated after each route change) |
| [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) | contributor setup, checks, editorial rules, PR checklist |
| [`../../env.example`](../../env.example) | environment variable template (pipeline + API), no secrets |

## 3. Phase 2 — Product Scoping (`phase2/`)

| Document | Content |
|---|---|
| [`../phase2/mvp_scope.md`](../phase2/mvp_scope.md) | MVP scope, user stories, acceptance criteria |
| [`../phase2/implementation_plan.md`](../phase2/implementation_plan.md) | lots S0-S4, progress state |
| [`../phase2/decisions_to_validate.md`](../phase2/decisions_to_validate.md) | decisions D1-D8 (D1 **validated**: only `summary.csv`) |
| [`../phase2/backend_architecture.md`](../phase2/backend_architecture.md) | static vs API options, sources of truth |
| [`../phase2/api_contract.md`](../phase2/api_contract.md) | v1 contract for artifact data (shared front/API fields) |
| [`../phase2/frontend_handoff.md`](../phase2/frontend_handoff.md) | technical handoff of existing front (structure, theme, procedures) |
| [`../phase2/data_validation.md`](../phase2/data_validation.md) | see §1 (report A) |
| [`../phase2/scientific_method.md`](../phase2/scientific_method.md) / [`../phase2/validation_plan.md`](../phase2/validation_plan.md) | see §1 |

## 4. Other Entries

- Root: [`../../README.md`](../../README.md) (**English** — installation, commands, execution state), [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) (D1 rules), [`../../LICENSE`](../../LICENSE) (MIT).
- [`../NASA_SUBMISSION_AUDIT.md`](../NASA_SUBMISSION_AUDIT.md) — NASA submission audit (ready-to-use, validated sections).
- Scoping documents moved to docs root: `AUREL_SPECS_REVIEW.md`,
  `Pyrolens_Specification_Frontend.md`, `FRONTEND_IMPLEMENTATION_REPORT.md`,
  `PROMPT_MODEL_CHAT_IMPROVEMENT.md`.
- Original HTML prototypes: [`../../prototypes/`](../../prototypes/) (design reference, unmaintained).
- Detailed UI handoff (screens, design system, flows, mockups):
  [`../../frontend-handoff/`](../../frontend-handoff/README.md).
- Published artifacts (source of truth for figures):
  `../../web/public/artifacts/` and `../../baselines/summary.csv`.

---

**Non-negotiable reminders**: never claim fire absence; provenance
(`data_origin`, `generated_at`) visible everywhere; Jaccard = set overlap,
not an accuracy; no client-side secrets nor in artifacts.
