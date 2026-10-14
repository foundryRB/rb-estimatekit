"""Slidev scaffold — generate slides.md and style.css.

These files form the skeleton of a Slidev presentation project.
They are generated from domain data (project config, branding).
"""

from __future__ import annotations

from pathlib import Path

from engine.domain.model.aggregates.phase import Phase
from engine.domain.model.value_objects.branding import BrandConfig
from engine.domain.model.value_objects.config import ProjectConfig


def _phase_headline(phase: Phase) -> str:
    """The title slide's second line: the phase the deck sells, from its phase-table row."""
    headline = f"{phase.phase_id} Effort Estimate"
    return f"{headline}: {phase.name}" if phase.name else headline


def write_slides_md(
    output_dir: Path, config: ProjectConfig, phase: Phase, page_files: list[str],
) -> None:
    """Generate the main slides.md that imports all page files.

    The title slide carries the project's programme-level description and,
    under it, the phase being sold with its own description, so the cover
    names the phase without the project description having to.
    """
    brand = config.branding
    company = brand.company
    company_brand = company.split("\u2014")[0].strip() if "\u2014" in company else company
    company_suffix = company.split("\u2014")[1].strip() if "\u2014" in company else ""

    lines = [
        "---",
        "theme: default",
        "colorSchema: light",
        f'title: "{config.name}: {phase.phase_id} Effort Estimate"',
        "info: |",
        f"  ## {phase.phase_id} Effort Estimate",
        f"  {config.name}",
        f'titleTemplate: "%s \u2014 {company_brand}"',
        f"author: {config.author or company_brand}",
        "drawings:",
        "  persist: false",
        "transition: slide-left",
        "mdc: true",
        "---",
        "",
        f"# {config.name}",
        f"## {_phase_headline(phase)}",
        "",
        f"{config.description}" if config.description else "",
        "",
        f"{phase.description}" if phase.description else "",
        "",
        '<div class="cf-divider mt-4"></div>',
        "",
        '<div class="cf-footer">',
        f'  <span><span class="cf-brand">{company_brand}</span>'
        f' \u2014 {company_suffix}</span>' if company_suffix else
        f'  <span><span class="cf-brand">{company_brand}</span></span>',
        "</div>",
        "",
    ]
    for page_file in page_files:
        lines.append("---")
        lines.append(f"src: ./pages/{page_file}")
        lines.append("---")
        lines.append("")

    path = output_dir / "slides.md"
    path.write_text("\n".join(lines), encoding="utf-8")


def write_style_css(output_dir: Path, brand: BrandConfig) -> None:
    """Generate style.css from branding configuration.

    Produces the proposal's Light reading surface. The project owns its
    primary colour, company and typography; shared document styles live here.
    """
    primary = brand.primary_color
    font_family = brand.font_family or '"Segoe UI", Arial, sans-serif'
    company = brand.company or ""

    font_import = ""
    if brand.font_url:
        font_import = f"@import url('{brand.font_url}');\n\n"

    css = f"""{font_import}:root {{
  --cf-red: {primary};
  --cf-accent-ink: color-mix(in srgb, {primary} 65%, #252321);
  --cf-black: #252321;
  --cf-dark: #252321;
  --cf-dark-grey: #383638;
  --cf-mid-grey: #615B54;
  --cf-light-grey: #CFC5BA;
  --cf-bg-card: #EAE5DC;
  --cf-bg-subtle: #FFFAF5;
  --cf-white: #FFFAF5;
  --cf-blue: #1976D2;
  --cf-alert-bg: #FFF3F3;
  --cf-font: {font_family};
  --cf-company: "{company}";

  --slidev-theme-primary: {primary};
  --slidev-theme-text: #252321;
  --slidev-theme-background: #F5F2ED;
}}

/* ── Global ──────────────────────────────────────── */

.slidev-layout {{
  font-family: var(--cf-font) !important;
  color: var(--cf-dark);
  background: radial-gradient(ellipse at 100% 0%, color-mix(in srgb, var(--cf-red) 9%, transparent), transparent 55%), #F5F2ED;
}}

.slidev-layout h1 {{
  font-family: var(--cf-font) !important;
  font-weight: 700 !important;
  color: var(--cf-black) !important;
  letter-spacing: -0.02em;
}}

.slidev-layout h2,
.slidev-layout h3 {{
  font-family: var(--cf-font) !important;
  font-weight: 600 !important;
  color: var(--cf-dark-grey) !important;
}}

.slidev-layout strong {{ font-weight: 700; }}
.slidev-layout h1 + p {{ opacity: 1; color: var(--cf-mid-grey); }}

.slidev-layout a {{
  color: var(--cf-accent-ink) !important;
  text-decoration: none;
}}
.slidev-layout a:hover {{ text-decoration: underline; }}

/* ── Tables ──────────────────────────────────────── */

.slidev-layout table {{ border-collapse: collapse; }}

.slidev-layout table th {{
  background-color: var(--cf-dark) !important;
  color: var(--cf-white) !important;
  font-weight: 600;
  padding: 0.4rem 0.6rem;
  font-size: 0.8em;
}}

.slidev-layout table td {{
  border-bottom: 1px solid var(--cf-light-grey);
  padding: 0.35rem 0.6rem;
  font-size: 0.8em;
}}

.slidev-layout table tr:hover td {{ background-color: #FAFAFA; }}

/* ── Blockquotes ─────────────────────────────────── */

.slidev-layout blockquote {{
  border-left: 3px solid var(--cf-red) !important;
  background-color: var(--cf-bg-card);
  padding: 0.75rem 1rem;
  margin: 0.5rem 0;
  font-size: 0.9em;
}}

/* ── Divider ─────────────────────────────────────── */

.cf-divider {{
  height: 3px;
  background: var(--cf-red);
  border: none;
  margin: 0.75rem 0;
  width: 60px;
}}

/* ── Footer ──────────────────────────────────────── */

.cf-footer {{
  position: absolute;
  bottom: 1.5rem;
  left: 2rem;
  right: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.65rem;
  color: var(--cf-mid-grey);
  font-family: var(--cf-font);
}}

.cf-footer .cf-brand {{
  font-weight: 700;
  color: var(--cf-accent-ink);
  letter-spacing: 0.05em;
}}

/* ── KPI Stat Cards ──────────────────────────────── */

.cf-stat {{
  background: var(--cf-bg-card);
  border-radius: 4px;
  padding: 0.5rem 0.6rem;
  text-align: center;
}}

.cf-stat-value {{
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--cf-dark);
}}

.cf-stat-label {{
  font-size: 0.7rem;
  color: var(--cf-mid-grey);
}}

.cf-stat--primary .cf-stat-value {{ color: var(--cf-accent-ink); }}
.cf-stat--primary {{ border-left: 3px solid var(--cf-red); }}
.cf-stat--dark .cf-stat-value {{ color: var(--cf-dark); }}
.cf-stat--dark {{ border-left: 3px solid var(--cf-dark-grey); }}
.cf-stat--mid {{ border-left: 3px solid var(--cf-mid-grey); }}

/* ── Category Cards ──────────────────────────────── */

.cf-cat {{
  background: var(--cf-bg-subtle);
  padding: 0.5rem 0.6rem;
  border-radius: 0 4px 4px 0;
}}

.cf-cat-name {{ font-weight: 700; font-size: 0.8rem; }}
.cf-cat-count {{ font-size: 1.5rem; font-weight: 700; color: var(--cf-dark); }}
.cf-cat-desc {{ font-size: 0.65rem; color: var(--cf-mid-grey); }}

.cf-cat--demo {{ border-left: 3px solid var(--cf-blue); }}
.cf-cat--demo .cf-cat-name {{ color: var(--cf-blue); }}
.cf-cat--p1 {{ border-left: 3px solid var(--cf-red); }}
.cf-cat--p1 .cf-cat-name {{ color: var(--cf-accent-ink); }}
.cf-cat--p12 {{ border-left: 3px solid var(--cf-mid-grey); }}
.cf-cat--p12 .cf-cat-name {{ color: var(--cf-mid-grey); }}
.cf-cat--p23 {{ border-left: 3px solid #999; }}
.cf-cat--p23 .cf-cat-name {{ color: #999; }}

/* ── Phase Column Cards ──────────────────────────── */

.cf-phase {{ padding-left: 1rem; }}
.cf-phase--demo {{ border-left: 4px solid var(--cf-blue); }}
.cf-phase--p1 {{ border-left: 4px solid var(--cf-red); }}
.cf-phase--p2 {{ border-left: 4px solid var(--cf-dark-grey); }}
.cf-phase--p3 {{ border-left: 4px solid #999; }}

.cf-phase-tag {{
  font-size: 0.7rem;
  padding: 0.4rem 0.6rem;
  border-radius: 4px;
  background: var(--cf-bg-card);
  margin-top: 0.5rem;
}}

/* ── Risk Map Headers ────────────────────────────── */

.cf-risk-header {{
  padding: 0.4rem 0.6rem;
  font-weight: 700;
  color: var(--cf-white);
  border-radius: 4px 4px 0 0;
  font-size: 0.75rem;
  margin-bottom: 0.25rem;
}}

.cf-risk-header--critical {{ background: #AD2839; }}
.cf-risk-header--monitor  {{ background: var(--cf-mid-grey); }}
.cf-risk-header--accept   {{ background: var(--cf-dark-grey); }}

/* ── Alert Callout ───────────────────────────────── */

.cf-alert {{
  background: var(--cf-alert-bg);
  border-left: 4px solid var(--cf-red);
  border-radius: 4px;
  padding: 0.75rem;
  font-size: 0.85rem;
}}

/* ── Hero Estimate Block ─────────────────────────── */

.cf-hero {{
  background: var(--cf-dark);
  border-top: 3px solid var(--cf-red);
  color: var(--cf-white);
  border-radius: 8px;
  padding: 1.25rem;
  text-align: center;
}}

.cf-hero-value {{ font-size: 2.75rem; font-weight: 700; }}
.cf-hero-label {{ font-size: 0.85rem; margin-top: 0.25rem; }}

/* ── Summary Bar ─────────────────────────────────── */

.cf-summary {{
  background: var(--cf-bg-card);
  border-radius: 4px;
  padding: 0.5rem;
  text-align: center;
  font-size: 0.85rem;
}}

/* ── Legend ───────────────────────────────────────── */

.cf-legend {{ font-size: 0.75rem; color: var(--cf-mid-grey); }}
.cf-legend-dot--demo {{ color: var(--cf-blue); }}
.cf-legend-dot--p1 {{ color: var(--cf-red); }}
.cf-legend-dot--p12 {{ color: var(--cf-mid-grey); }}
.cf-legend-dot--p23 {{ color: #999; }}

/* ── Notes ───────────────────────────────────────── */

.cf-note {{ font-size: 0.75rem; color: var(--cf-mid-grey); }}

/* ── Gantt Chart (Delivery Roadmap) ──────────────── */

.cf-gantt-wrap {{ overflow: hidden; margin-top: 0.5rem; }}

.cf-gantt {{
  width: 100%;
  border-collapse: collapse;
  font-size: 0.65rem;
  font-family: var(--cf-font);
}}

.cf-gantt th,
.cf-gantt td {{
  padding: 3px 5px;
  border: 1px solid var(--cf-light-grey);
  white-space: nowrap;
}}

.cf-gantt .cf-gantt-label {{
  text-align: left;
  font-weight: 600;
  color: var(--cf-dark-grey);
  min-width: 100px;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
}}

.cf-gantt .cf-gantt-effort {{
  text-align: right;
  color: var(--cf-mid-grey);
  min-width: 35px;
}}

.cf-gantt .cf-gantt-month {{
  text-align: center;
  font-weight: 500;
  color: var(--cf-mid-grey);
  min-width: 28px;
}}

.cf-gantt .cf-gantt-phase {{
  text-align: center;
  font-weight: 700;
  font-size: 0.7rem;
  letter-spacing: 0.04em;
  padding: 4px 6px;
}}

.cf-gantt-phase-row th {{
  border-bottom: none !important;
}}

.cf-gantt-header th {{
  background: var(--cf-dark);
  color: var(--cf-white);
  border-bottom: 2px solid var(--cf-light-grey);
}}

.cf-gantt-cell {{
  text-align: center;
  min-width: 28px;
  height: 20px;
}}

.cf-gantt-compact .cf-gantt-cell {{
  height: 14px;
  min-width: 22px;
}}

.cf-gantt-compact th,
.cf-gantt-compact td {{
  padding: 1px 3px;
}}

.cf-gantt-compact .cf-gantt-label {{
  min-width: 80px;
  max-width: 110px;
  font-size: 0.5rem;
}}

.cf-gantt-compact .cf-gantt-stream {{
  min-width: 36px;
  max-width: 50px;
  font-size: 0.45rem;
}}

.cf-gantt-active {{ opacity: 0.85; }}
.cf-gantt-design {{ opacity: 0.45; }}

.cf-gantt-milestone {{
  color: #fff !important;
  font-weight: 700;
  font-size: 0.7rem;
  opacity: 1;
}}

.cf-gantt-legend-active {{
  display: inline-block;
  width: 14px;
  height: 10px;
  border-radius: 2px;
  vertical-align: middle;
}}

.cf-gantt-legend-design {{
  display: inline-block;
  width: 14px;
  height: 10px;
  border-radius: 2px;
  vertical-align: middle;
  opacity: 0.45;
}}

.cf-gantt-legend-milestone {{
  color: var(--cf-accent-ink);
  font-weight: 700;
  font-size: 0.85rem;
  vertical-align: middle;
}}

.cf-gantt .cf-gantt-stream {{
  text-align: left;
  font-weight: 500;
  color: var(--cf-mid-grey);
  font-size: 0.55rem;
  min-width: 50px;
  max-width: 70px;
  overflow: hidden;
  text-overflow: ellipsis;
}}

/* ── Resource Allocation ─────────────────────────── */

.cf-resource-wrap {{ overflow-x: auto; margin-top: 0.35rem; }}

.cf-resource {{
  width: 100%;
  border-collapse: collapse;
  font-size: 0.6rem;
  font-family: var(--cf-font);
}}

.cf-resource th,
.cf-resource td {{
  padding: 2px 5px;
  border: 1px solid var(--cf-light-grey);
  white-space: nowrap;
}}

.cf-resource .cf-resource-stream {{
  text-align: left;
  font-weight: 600;
  color: var(--cf-dark-grey);
  min-width: 70px;
  max-width: 100px;
}}

.cf-resource .cf-resource-total {{
  text-align: right;
  font-weight: 600;
  color: var(--cf-dark-grey);
  min-width: 35px;
}}

.cf-resource .cf-resource-value {{
  text-align: center;
  min-width: 28px;
  color: var(--cf-mid-grey);
}}

.cf-resource .cf-resource-value-high {{
  text-align: center;
  min-width: 28px;
  font-weight: 700;
  color: var(--cf-dark-grey);
}}

.cf-resource-header th {{
  background: var(--cf-dark-grey);
  color: var(--cf-white);
  font-weight: 600;
  text-align: center;
}}

.cf-resource-footer td {{
  background: var(--cf-light-grey);
  font-weight: 700;
  color: var(--cf-dark-grey);
}}

/* ── Legacy Gantt compat ─────────────────────────── */

.gantt-table {{ width: 100%; border-collapse: collapse; font-size: 0.55rem; }}
.gantt-table th {{ background: var(--cf-dark); color: var(--cf-white);
  padding: 2px 4px; text-align: center; font-weight: 600; }}
.gantt-table td {{ padding: 1px 3px; text-align: center; border: 1px solid #eee; }}
.gantt-label {{ text-align: left !important; white-space: nowrap; font-weight: 600; }}
.gantt-effort {{ text-align: right !important; font-size: 0.5rem; color: var(--cf-mid-grey); }}
"""

    path = output_dir / "style.css"
    path.write_text(css, encoding="utf-8")
    chrome = Path(__file__).parent / "templates" / "global-top.vue"
    (output_dir / "global-top.vue").write_text(chrome.read_text(encoding="utf-8"), encoding="utf-8")
