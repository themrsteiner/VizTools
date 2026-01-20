# Changelog

All notable changes to VizTools will be documented in this file.

## v0.1 — 2026-01-20

### Added
- Streamlit app template for interactive CSV/Excel visualization.
- File upload support for CSV and Excel (with sheet selection for multi-sheet workbooks).
- Interactive Plotly scatter plot with column mapping:
  - X (numeric), Y (numeric)
  - Color (categorical)
  - Symbol (categorical)
  - Optional Size (numeric)
  - Custom tooltip fields
- Export options:
  - Download interactive HTML
  - Download PNG (server-side)
  - Plotly toolbar PNG export (client-side)

### Changed
- Updated layout calls to use `width="stretch"` where applicable (Streamlit deprecation readiness).
- Pinned Plotly/Kaleido versions to stabilize server-side PNG export.

### Notes
- Toolbar PNG export may visually match the on-screen theme more closely than server-side PNG export; both are accurate.
