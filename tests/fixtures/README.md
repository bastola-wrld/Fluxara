# Test fixtures

* `emit_cmr_granules.json` and `sentinel2_stac_search.json` are real API
  responses recorded on 2026-10-06 (trimmed to one record each).
* `emit_plume_metadata_*.json` are **hand written**. They use the property
  names NASA's delivery code writes
  (github.com/emit-sds/emit-sds-tgp, `src/annotate/plume_io.py`), but the
  numbers are test values, not measurements. The real files need an Earthdata
  login to download. Replace these with a real file once you have a token.
