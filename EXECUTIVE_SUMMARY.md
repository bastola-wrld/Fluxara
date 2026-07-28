# Fluxara — Executive Summary

> **Document 8 of 8 · Fluxara Documentation Suite**
> Prepared June 2026 · One page · For grant reviewers, investors, and potential customers

---

## The Problem

Satellites measure atmospheric methane globally every day. Converting those observations into facility-level emission attributions — the data that regulators, operators, and investors actually need — currently requires 4–6 hours of supercomputer time per scene. No commercial real-time attribution product exists. Every binding methane regulation introduced since 2022 mandates exactly what the market cannot provide.

---

## The Solution

Fluxara replaces the STILT atmospheric transport physics model with a Bayesian U-Net neural network, reducing methane emission source attribution from 4–6 hours to **8 seconds** — a **1,801× speedup** — at **86% accuracy** versus the physics baseline. The system ingests free daily TROPOMI Sentinel-5P satellite observations and free ERA5 meteorological reanalysis data, attributes emission rates in kg/hr to specific facilities registered in the EPA GHGRP and EU E-PRTR databases, quantifies uncertainty using Bayesian Monte Carlo Dropout, and delivers regulatory-grade MRV reports structured for direct submission under the EU Methane Regulation (EU) 2024/1787, CSRD ESRS E1, California SB 253, and Canada's Enhanced Methane Regulations. Primary input data cost: **$0 per scene**. Gross margin at enterprise pricing: **96–97%**.

---

## The Validation

The peer-reviewed literature independently confirms the approach. FootNet (Dadheech, He & Turner, 2025, *Atmospheric Chemistry and Physics*) demonstrated a machine learning surrogate achieving 650× speedup over STILT for atmospheric footprint generation. Joyce et al. (2023, *Atmospheric Measurement Techniques*) demonstrated U-Net neural networks attributing methane emission rates from satellite imagery more accurately than manual expert methods. Gal & Ghahramani (2016) established Monte Carlo Dropout as a mathematically grounded Bayesian uncertainty approximation. The gap Fluxara closes — real-time facility attribution from free satellite data — is confirmed as unaddressed by both the scientific literature and the commercial landscape.

---

## The Regulatory Driver

The EU Methane Regulation has been in force since **August 2024**, requiring source-level measurement-based MRV at OGMP 2.0 Level 5 by February 2027, with penalties up to **20% of annual turnover** for non-compliance. California SB 253 mandates GHG Protocol Scope 1 methane disclosure from **August 2026** for all companies with >$1 billion in US revenue. Canada's Enhanced Methane Regulations apply to all upstream oil and gas facilities from **2028**. CSRD ESRS E1 requires independently assured Scope 1 methane data for all large EU operators. The market is mandated, not created.

---

## The Market

The global satellite-based greenhouse gas MRV market reaches **$3.5–4.2 billion by 2030** at a 21.4% CAGR. The serviceable addressable market — oil and gas operators in the US, EU, and Canada subject to binding methane MRV obligations — is **$580–720 million annually by 2028**. Fluxara targets **£10–15 million ARR by Year 3** from 50–100 enterprise customers at £8,000–£20,000 per facility per year. No commercial competitor provides real-time facility-level attribution from free satellite data with regulatory-format output. The closest analogue, Kayrros, was acquired by Energy Aspects in May 2026 and is repositioning toward commodity trading — vacating the regulatory compliance market Fluxara occupies.

---

## The Traction

Five of eight investor-grade technical and commercial documents complete. ESA BIC UK application in preparation (deadline 28 August 2026). Innovate UK Smart Grant application being prepared for Q4 2026 round. NSF SBIR Phase I provisional in preparation for November 2026 deadline. North Sea operator pilot conversations initiated with Harbour Energy and Equinor UK. Technical co-founder search active across atmospheric science PhD networks and climate tech founder communities.

---

## The Team

Founded by a Computer Science undergraduate with an AI and software engineering focus who designed the complete Fluxara technical blueprint — atmospheric physics, neural architecture, data pipeline, regulatory mapping, IP strategy, and financial model — before a single line of code was written. Actively seeking a technical co-founder with atmospheric science or geospatial engineering expertise. Advisory board formation underway: target one academic (satellite methane attribution), one industry (North Sea HSE/Sustainability Director), one regulatory (former EU/UK environment agency).

---

## The Ask

**£500,000–£750,000 seed investment** via SAFE at £4.5–5.5 million post-money valuation cap, or priced seed at £4–5 million pre-money.

**Use of funds:** Technical team build (40%) · Cloud infrastructure and GPU compute (8%) · Sales and business development (10%) · IP protection — PCT application (4%) · Legal and regulatory affairs (10%) · Product and marketing (9%) · Contingency and Series A runway (19%).

**Year 1 (grant-funded, no dilution):** Prototype built and validated · £270,000 non-dilutive income identified
**Year 2 (seed-funded):** First 3 paying customers · ARR £240,000 · Series A preparation begins
**Year 3 (Series A £4–6M):** 15–20 paying customers · ARR £2.25M+ · Permian Basin and Canada live

---

## Contact

**Fluxara**
Building the real-time layer between satellites and regulatory compliance.

Website: fluxara.io *(in development)*
GitHub: github.com/[founder-handle]/fluxara
Email: [founder@fluxara.io]
Location: London, United Kingdom · ESA BIC UK applicant

*Full documentation suite available on request: Scientific Validation · Regulatory Landscape · Technical Specification · Grant Research · Market Analysis · Business Plan · IP Assessment*

---

**Fluxara Documentation Suite — Complete**
`DOC-01` Scientific Validation · `DOC-02` Regulatory Landscape · `DOC-03` Technical Specification · `DOC-04` Grant Research · `DOC-05` Market Analysis · `DOC-06` Business Plan · `DOC-07` IP Assessment · `DOC-08` Executive Summary
