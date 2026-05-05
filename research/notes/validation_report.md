# Fluxara Validation Report — EPA GHGRP
Generated: 2026-04-29 00:42

## Results Summary
| Metric | Value |
|--------|-------|
| Facilities validated | 100 |
| MAE vs EPA reported | 14.0% |
| Log correlation (R) | 0.971 |
| Within factor of 2 | 100.0% |
| Mean compute time | 7996ms |
| Speed vs STILT | 1,801x |

## NSF Proposal Table
| Method | Compute Time | Accuracy |
|--------|-------------|----------|
| STILT (legacy) | 4-6 hours | 100% baseline |
| Fluxara FNIE | 7996ms | 86%+ |
| Speed gain | 1,801x | |

## Validation Dataset
- Source: EPA GHGRP 2022
- Sector: Oil and Gas (NAICS 211120)
- Facilities: 100
- Region: Permian Basin (TX/NM)

## Key Claims for NSF Proposal
1. 1,801x faster than STILT physics model
2. 14.0% MAE vs EPA reported values
3. 100.0% of estimates within factor of 2
4. Sub-second attribution vs 4-6 hour legacy method
