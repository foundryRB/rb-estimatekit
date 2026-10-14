"""Domain constants — single source of truth for shared identifiers.

These constants are part of the Ubiquitous Language and may be used by
both domain logic and adapters.  **No duplication allowed** — every
file name, column name, or color token must be defined here exactly once.

Sub-modules:
  - ``scheduling`` — scheduling parameters
  - ``colors``     — phase colour palettes
  - ``columns``    — TSV column name constants
  - ``files``      — file naming conventions and helpers
      - ``files.inputs``    — source / input TSV file constants
      - ``files.outputs``   — generated Excel workbook constants
      - ``files.templates`` — Excel template file constants
      - ``files.roadmaps``  — roadmap output file helpers
"""
