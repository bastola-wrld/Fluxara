# Data sources and licences

Every row in `plume_detections` and `satellite_scenes` stores its own
`licence`, `attribution` and, for plumes, `commercial_use_allowed`.
Paid reports must only use rows where `commercial_use_allowed` is true.

| Source | What we take | Licence | Commercial use | Attribution to print |
|---|---|---|---|---|
| NASA EMIT (`EMITL2BCH4PLM` v002, LP DAAC) | Methane plume outlines, peak enhancement, emission rate with uncertainty when NASA provides one | NASA open data policy | Yes | "EMIT L2B Estimated Methane Plume Complexes 60 m V002, NASA LP DAAC, doi:10.5067/EMIT/EMITL2BCH4PLM.002" |
| Copernicus Sentinel 2 L1C | Scene catalogue, bands B11 and B12 for our own retrieval | Copernicus Sentinel data licence | Yes | "Contains modified Copernicus Sentinel data [year]" |
| ERA5 (Copernicus Climate Change Service) | Wind, used later for quantification | CC BY 4.0 | Yes | "Contains modified Copernicus Climate Change Service information [year]" |

## Not used in the paid product

| Source | Why |
|---|---|
| Carbon Mapper | Non commercial licence. A commercial licence can be requested from data@carbonmapper.org. |
| UNEP IMEO Eye on Methane | CC BY NC 4.0, non commercial. |

These two may be used for internal validation and free pilots only. If they
are ever ingested, set `commercial_use_allowed = false` on those rows.

Confirm each licence yourself before your first paid report. Terms change.

## What the instruments can and cannot see

* **EMIT** flies on the International Space Station. It covers about 52 N to
  52 S, at 60 m resolution, and only where the station happens to pass.
  NASA reviews each scene by hand, so plumes appear about two weeks late.
* **EMIT is not fresh.** Checked on 2026-10-06: the V002 catalogue holds 1,686
  plumes in total and the newest was observed on 2025-09-22. Treat EMIT as a
  historical and validation dataset. It cannot drive alerts on new leaks.
  Check again before relying on it:
  `python -m fluxara.ingest.run emit --days 365`
* **Sentinel 2** revisits every 5 days or better at 20 m, but only detects
  large leaks, roughly 500 to 2,000 kg/hr and above, and works best over
  flat, bright, uniform ground such as desert.
* No detection is not proof of no emission.
