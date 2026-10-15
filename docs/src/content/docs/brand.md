---
title: Visual identity
id: DOC-BRAND-001
type: Reference
status: Active
updated: "2026-09-13"
summary: The application's identity and the defaults a new project starts from.
---

EstimateKit's application wears the RB Software Engineering identity; a new project starts from the issuing company's defaults (RB). Existing projects own their explicit branding in `project.yaml`.

## Source ownership

| Surface | Source |
| --- | --- |
| Application palette, spacing and motion | `web/src/index.css`, `web/tailwind.config.js` |
| Lockup (the one mark) | `web/src/components/Lockup.tsx`, mounted by the home page, the toolbar and `web/src/views/atoms/Logo.tsx` |
| Decorative side fields and particles | `web/src/views/atoms/AmbientField.tsx` |
| Reading preference | `web/src/viewmodels/useThemeViewModel.tsx` |
| New-project identity | `templates/project.yaml`, `engine/domain/model/value_objects/branding.py` |
| Default output accent | `engine/domain/constants/colors.py` |
| Proposal reading surfaces | `engine/adapters/outbound/slidev/scaffold.py` |
| Proposal ambient contours | `engine/adapters/outbound/slidev/templates/global-top.vue` |
| Shared workbook appearance | `engine/adapters/outbound/excel/branding.py` |

The application uses a near-black stage in dark and paper in light, the brand's green as the primary and the field's colour, and system fonts for text. Continuous side fields and sparse rising particles animate in both appearances, pause on hidden pages and stop for reduced motion. The editing workspace uses opaque working surfaces. Mobile layouts retain access to the project gallery.

New projects use RB, its green (`#00a86b`) and Segoe UI. Output adapters consume the project's branding for its proposal, roadmap and presentation; an explicitly branded customer project retains its own values. Generated data, calculations and estimation semantics belong to the existing engine.

Proposals use Light reading surfaces with dark table headers, accessible accent text, edge contours and sparse embers. Motion pauses on hidden pages, stops for reduced motion and is absent from print. Generated workbooks use the shared reading palette and Segoe UI. Semantic risk/category colours remain tied to data. Issued files retain their appearance until regenerated.
