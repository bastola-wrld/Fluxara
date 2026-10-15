# Fluxara — Intellectual Property and Defensibility Assessment

> **Document 7 of 8 · Fluxara Documentation Suite**
> Prepared June 2026 · Status: Production-ready

Real-time satellite methane attribution · 8-second inference · 86% accuracy · 1,801× faster than STILT · Zero marginal data cost

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [What Fluxara Owns: IP Inventory](#what-fluxara-owns-ip-inventory)
- [What Is Potentially Patentable](#what-is-potentially-patentable)
  - [Claim Set 1 — The Neural Atmospheric Inversion Method](#claim-set-1--the-neural-atmospheric-inversion-method)
  - [Claim Set 2 — The Real-Time Attribution Pipeline](#claim-set-2--the-real-time-attribution-pipeline)
  - [Claim Set 3 — Bayesian Uncertainty Output for Regulatory MRV](#claim-set-3--bayesian-uncertainty-output-for-regulatory-mrv)
  - [Patentability Assessment Summary](#patentability-assessment-summary)
- [Existing Patent Landscape: Prior Art and Freedom to Operate](#existing-patent-landscape-prior-art-and-freedom-to-operate)
  - [GHGSat — Patented Interferometer Technology](#ghgsat--patented-interferometer-technology)
  - [International Patent Application WO 2022/008681 A1](#international-patent-application-wo-20220086811-a1)
  - [Academic Prior Art: FootNet, GATES, and the ML Surrogate Literature](#academic-prior-art-footnet-gates-and-the-ml-surrogate-literature)
  - [Freedom to Operate Assessment](#freedom-to-operate-assessment)
- [Trade Secret Strategy](#trade-secret-strategy)
  - [What to Protect as Trade Secrets](#what-to-protect-as-trade-secrets)
  - [Trade Secret Implementation Protocol](#trade-secret-implementation-protocol)
- [Open Source Licensing Considerations](#open-source-licensing-considerations)
  - [Inbound Licences: Dependencies Fluxara Uses](#inbound-licences-dependencies-fluxara-uses)
  - [Open Data Licences: Satellite and Meteorological Data](#open-data-licences-satellite-and-meteorological-data)
  - [Outbound Licence: What Fluxara Ships](#outbound-licence-what-fluxara-ships)
  - [The AGPL Risk: The Critical Licence to Audit](#the-agpl-risk-the-critical-licence-to-audit)
- [Copyright Protection](#copyright-protection)
- [Recommended IP Strategy](#recommended-ip-strategy)
  - [Phase 1 — Immediate Actions (Pre-Funding, 0–3 Months)](#phase-1--immediate-actions-pre-funding-03-months)
  - [Phase 2 — Post-Grant Award (Months 3–12)](#phase-2--post-grant-award-months-312)
  - [Phase 3 — Post-Series A (Months 12–36)](#phase-3--post-series-a-months-1236)
- [IP as a Fundraising Asset](#ip-as-a-fundraising-asset)
- [Risk Register](#risk-register)

---

## Executive Summary

Fluxara's intellectual property position is best understood through the lens of four overlapping protection layers: trade secrets (the trained model weights and the proprietary training dataset), patents (the specific pipeline combining neural atmospheric inversion with regulatory MRV output), copyright (the software implementation and report templates), and data moat (the accumulating attribution time series that no competitor can reproduce retroactively).

No directly blocking patents have been identified in the atmospheric inversion or satellite methane attribution space. GHGSat holds patents on its physical interferometer instrument — hardware that Fluxara does not build or use. The relevant academic prior art (FootNet, GATES, and the U-Net plume detection literature) establishes the general concept of machine learning for atmospheric transport, but does not anticipate Fluxara's specific architecture: a Bayesian U-Net trained directly on TROPOMI plus ERA5 inputs to produce facility-level emission attribution with calibrated uncertainty bounds formatted for regulatory submission.

The recommended IP strategy for a pre-revenue deep tech startup with no legal budget is: (1) protect the trained model weights as a trade secret immediately and at zero cost; (2) file a provisional patent application on the core pipeline method within 90 days of completing the first working model, using Innovate UK grant IP funding (typically £7,500 allocated for IP in Innovate UK awards) to cover the filing cost; (3) convert the provisional to a PCT international application at 12 months to preserve global filing options; and (4) never disclose the specific architecture, training data composition, or hyperparameter configuration to any party without a signed NDA.

---

## What Fluxara Owns: IP Inventory

The following constitutes Fluxara's current IP estate at the pre-implementation architecture stage:

| Asset | Type | Protection Mechanism | Status |
|---|---|---|---|
| Bayesian U-Net neural atmospheric inversion architecture | Invention | Trade secret + potential patent | Documented in Doc 3; not yet filed |
| Real-time TROPOMI → ERA5 → attribution pipeline | Invention | Trade secret + potential patent | Documented in Doc 3; not yet filed |
| MC Dropout regulatory uncertainty output format | Invention | Trade secret + potential patent | Documented in Doc 3; not yet filed |
| Physics-informed loss function (L_physics) | Invention | Trade secret | Documented in Doc 3; not yet filed |
| Gaussian plume training label generation methodology | Invention | Trade secret | Documented in Doc 3; not yet filed |
| Training dataset (synthetic plumes + TROPOMI backgrounds) | Compilation | Trade secret + copyright | To be created during prototype phase |
| Trained model weights (v1.x) | Artefact | Trade secret | To be created during prototype phase |
| Attribution time series database | Database | Database right (UK/EU) + trade secret | Accumulated post-deployment |
| Regulatory report templates (Jinja2/HTML/PDF) | Creative work | Copyright | To be created during development |
| API schema and endpoint design | Creative work | Copyright | Documented in Doc 3 |
| Fluxara brand and logo | Brand | Trademark | To be registered |
| This documentation suite (Docs 1–8) | Literary works | Copyright | Created; automatic protection |

---

## What Is Potentially Patentable

### Claim Set 1 — The Neural Atmospheric Inversion Method

**What it covers:** A computer-implemented method for attributing greenhouse gas emission rates to specific industrial facilities, comprising:

- receiving, as input, a multi-channel tensor comprising satellite-observed column-averaged methane enhancement fields from TROPOMI at 5.5 × 7 km resolution, atmospheric wind fields from ERA5 reanalysis data, and a facility density map derived from a regulatory facility database;
- processing said input through an encoder-decoder convolutional neural network with skip connections and spatial dropout layers active during inference;
- generating, as output, a per-facility emission rate vector in kg/hr;
- computing, via N stochastic forward passes with dropout active, a mean emission rate and associated uncertainty estimate per facility;
- completing said processing in less than 10 seconds on a single GPU.

**Novelty argument:** No existing patent or published patent application describes the specific combination of TROPOMI satellite inputs, ERA5 meteorological inputs, and a U-Net architecture with MC Dropout producing facility-level emission rate attributions with calibrated uncertainty bounds. FootNet (He, Dadheech & Turner, 2025) describes an ML surrogate for STILT footprint generation — a different technical step (footprint generation, not attribution) and a different architecture (CNN footprint emulator, not direct emission attribution with uncertainty). GATES (preprint, 2025) uses a graph neural network for footprint emulation at continental scale — again, footprint emulation, not direct attribution. Neither FootNet nor GATES produces regulatory-format uncertainty output.

**Claim strength:** Medium-high. The general concept of ML for atmospheric transport is in the prior art literature. However, the specific claim — the complete pipeline from TROPOMI + ERA5 inputs through a Bayesian U-Net to per-facility attribution with uncertainty quantification — is sufficiently specific to be patentable in the UK (Patents Act 1977, novelty + inventive step requirements) and likely in the US (35 U.S.C. § 101 software patent considerations apply but the technical character and specific hardware implementation (GPU inference, specific sensor inputs) strengthen patentability post-Alice).

---

### Claim Set 2 — The Real-Time Attribution Pipeline

**What it covers:** A system for real-time greenhouse gas attribution comprising:

- an automated data ingest module configured to retrieve TROPOMI L2 NetCDF4 products from the Copernicus Data Space Ecosystem API and ERA5 hourly reanalysis from the ECMWF CDS API;
- a background removal module computing XCH4 enhancement using a sliding 200 km percentile window;
- a facility alignment module mapping GHGRP or E-PRTR facility coordinates to TROPOMI pixel resolution using a spatial index;
- a neural inference module executing a trained Bayesian U-Net on assembled input tensors;
- a report generation module producing structured MRV reports formatted for compliance with named regulatory frameworks;
- end-to-end processing time not exceeding 8 seconds from assembled input tensor to emission rate output.

**Novelty argument:** The combination of free open-access satellite data, automated regulatory database alignment, neural inference, and regulatory-format output generation in a single integrated pipeline is not anticipated by any identified prior art.

**Claim strength:** Medium. The individual components (TROPOMI ingest, ERA5 ingest, facility database lookup, neural inference) are individually known. The patent claim rests on the specific combination and integration in a real-time pipeline — a systems-level claim that is harder to obtain but provides broad protection if granted.

---

### Claim Set 3 — Bayesian Uncertainty Output for Regulatory MRV

**What it covers:** A method of generating calibrated uncertainty estimates for satellite-derived greenhouse gas emission attributions suitable for submission to regulatory authorities, comprising:

- executing N stochastic forward passes through a neural network with dropout active at inference time;
- computing mean emission rate, standard deviation, and percentile confidence intervals across said N passes;
- combining epistemic model uncertainty from MC Dropout with aleatoric measurement uncertainty from satellite retrieval precision;
- classifying each attribution as LOW, MEDIUM, or HIGH uncertainty based on coefficient of variation thresholds;
- including said uncertainty classification and confidence interval bounds in a structured output formatted for a named regulatory reporting framework.

**Novelty argument:** No existing satellite methane product provides Bayesian uncertainty quantification alongside emission rate attribution for regulatory MRV purposes. GHGSat provides point estimates without calibrated uncertainty. Kayrros provides monitoring intelligence without uncertainty-classified regulatory output. The integration of MC Dropout with a regulatory-format output standard is a specific and novel combination.

**Claim strength:** Medium. MC Dropout as a Bayesian approximation is well-established in the ML literature (Gal & Ghahramani, 2016). The specific application to satellite methane attribution with regulatory-format uncertainty classification may be patentable as an applied method claim.

---

### Patentability Assessment Summary

| Claim Set | Novelty | Inventive Step | Recommended Action |
|---|---|---|---|
| Neural atmospheric inversion method | High | Medium-high | File provisional within 90 days of first working model |
| Real-time attribution pipeline | Medium | Medium | Include as dependent claims in same provisional |
| Bayesian uncertainty for regulatory MRV | Medium-high | Medium | Include as separate independent claim |

**Cost estimate:** UK provisional patent application prepared by a patent attorney: £2,000–£5,000. Full UK national phase or PCT filing: £8,000–£15,000. Innovate UK grants typically allocate £7,500 for IP costs — sufficient for a provisional filing and partial PCT cost coverage. High-quality patent drafting by an experienced attorney can easily exceed £10,000 per application. Grants can help offset these costs, often providing limited budgets for IP work, commonly around £7,500 for Innovate UK grants. 

**Critical timing warning:** Pitching publicly before filing can destroy patent rights.  Every investor pitch, conference presentation, or published document describing the specific architecture, training methodology, or pipeline in enabling detail constitutes prior art disclosure. In the UK (and EU), there is a 12-month grace period for the inventor's own disclosures, but no such grace period exists in most other jurisdictions. File the provisional application before making any public technical disclosure beyond what is already in this documentation suite.

---

## Existing Patent Landscape: Prior Art and Freedom to Operate

### GHGSat — Patented Interferometer Technology

GHGSat's remote sensing technology is changing the way the world measures methane emissions. The company's patented interferometer capability provides the opportunity to observe emissions by merging multiple sources of light to create an interference pattern, enabling measurement and pinpointing of methane leaks from individual sites. 

GHGSat's patents cover its proprietary Wide-Angle Fabry-Pérot (WAF-P) interferometer — a physical optical instrument used aboard its satellites. This patent covers hardware that Fluxara does not build, use, or replicate. Fluxara uses TROPOMI (an ESA instrument using a different spectroscopic principle — grating spectrometer). GHGSat's patents present zero freedom-to-operate risk for Fluxara.

---

### International Patent Application WO 2022/008681 A1

Title: "Automated detection and quantification of gas emissions"
Applicant: Kayrros / Machover, Facciolo, Morel, de Franchis, Ehret
Filed: January 2022

This patent application covers automated methods for detecting and quantifying gas emission plumes from satellite imagery using image processing techniques. The core claims relate to: (a) automated plume detection in multispectral satellite imagery; (b) emission rate quantification from detected plumes using mass balance or Gaussian methods.

**Freedom to operate assessment:** Fluxara's method differs from WO 2022/008681 in the following material respects: (1) Fluxara uses a trained neural network for attribution rather than the image processing pipeline described in the Kayrros application; (2) Fluxara's primary task is facility-level attribution from a pre-identified facility database, not open-scene plume detection; (3) Fluxara produces regulatory-format MRV output with calibrated uncertainty, which is not described in WO 2022/008681. The risk of infringement is low but a formal freedom-to-operate opinion from a patent attorney should be obtained before commercial launch, specifically reviewing the granted claims (the published application may have narrowed during examination).

---

### Academic Prior Art: FootNet, GATES, and the ML Surrogate Literature

The following published academic works constitute the most relevant prior art for Fluxara's neural inversion method. They do not block Fluxara's patent claims but must be disclosed in any patent application and set the inventive step bar:

**FootNet v1.0** (He, Dadheech & Turner, 2025, *Geoscientific Model Development*): Machine learning emulator of STILT atmospheric transport. Uses a CNN to predict STILT footprints rather than directly attributing emissions. Input: meteorological fields. Output: spatial footprint functions. This is a surrogate for one step (footprint generation) of the two-step inversion process. Fluxara's architecture replaces the entire two-step process (footprint + optimisation) in a single forward pass.

**High-resolution GHG flux inversions using ML surrogate** (Dadheech, He & Turner, 2025, *Atmospheric Chemistry and Physics*): Applies FootNet footprints to a full GHG flux inversion in the San Francisco Bay Area. Demonstrates 650× speedup. Uses HRRR meteorological fields (not ERA5). Target application is urban CO₂ flux, not oil and gas methane attribution. No facility-level attribution, no regulatory output, no uncertainty quantification for MRV.

**GATES** (preprint, July 2025, *EGUSphere*): Graph-Neural-Network Atmospheric Transport Emulation System (GATES) — a data-driven LPDM emulator outputting source-receptor relationships using only meteorology and surface data as inputs, approximately 1,000× faster than an LPDM, demonstrated over South America using GOSAT observations.  Uses graph neural network architecture (not U-Net). Targets continental-scale footprint emulation (not facility-level attribution). No regulatory output. No Bayesian uncertainty.

**U-Plume and CH4Net**: U-Plume (Bruno et al., 2023) and CH4Net (Vaughan et al., 2024) have demonstrated potential of U-Net architectures for plume detection and masking using GHGSat and Sentinel-2 observations.  These cover plume detection (binary mask) and emission quantification from GHGSat high-resolution imagery — not TROPOMI-resolution basin-scale attribution with facility database alignment.

**Machover et al. WO 2022/008681 A1**: Kayrros patent application on automated plume detection from satellite imagery. Discussed above.

**Summary:** The prior art establishes that ML for atmospheric transport emulation is a known concept. Fluxara's patent claims must be drafted to emphasise the specific combination elements: TROPOMI + ERA5 multi-channel input, Bayesian U-Net architecture with MC Dropout active at inference, facility database alignment for attribution (not open-scene detection), and regulatory-format output with calibrated uncertainty classification. This combination is not anticipated by any identified prior art.

---

### Freedom to Operate Assessment

A formal freedom-to-operate (FTO) opinion from a qualified patent attorney is required before commercial launch. Based on the landscape analysis above, the preliminary FTO assessment is:

| Risk Area | Risk Level | Basis |
|---|---|---|
| GHGSat interferometer patents | **None** | Hardware instrument; Fluxara uses no interferometer |
| Kayrros WO 2022/008681 A1 | **Low** | Different method (image processing vs neural inversion); different output (plume detection vs facility attribution) |
| FootNet / GATES academic prior art | **None** (not patents) | Academic publications; create prior art affecting Fluxara's own patentability, not FTO risk |
| General ML / deep learning patents | **Low-medium** | Review granted claims from IBM, Google, Microsoft ML patent portfolios; unlikely to cover specific atmospheric inversion application |
| TROPOMI data use | **None** | Free and open Copernicus licence expressly permits commercial use |
| ERA5 data use | **None** | Copernicus licence permits commercial use |
| PyTorch (BSD 3-Clause) | **None** | Permissive commercial use |
| FastAPI (MIT) | **None** | Permissive commercial use |
| PostgreSQL (PostgreSQL Licence) | **None** | Permissive commercial use |

---

## Trade Secret Strategy

### What to Protect as Trade Secrets

Trade secret protection is the highest-priority IP action for Fluxara at the pre-revenue stage. Unlike patents (which require public disclosure), trade secrets provide indefinite protection as long as the information remains confidential and reasonable steps are taken to protect it.

The following constitute Fluxara's core trade secrets:

**1. Trained model weights (highest priority)**
The trained Bayesian U-Net weights — approximately 120 MB of floating-point parameters — represent the cumulative result of the training dataset, architecture design, loss function choices, and hyperparameter tuning. A competitor given the architecture specification (Document 3) but not the weights would need to replicate the entire training pipeline from scratch, at a cost of GPU compute time (approximately 43 hours on 4× A100 GPUs, approximately $500–$1,000 at spot pricing) plus the dataset construction time (months). The weights are a classic trade secret: valuable, not generally known, and not inferable from the product outputs.

Protection method: Store weights in encrypted object storage (AWS S3 with server-side encryption, or GCS with CMEK). Restrict access to named employees and contractors under NDA. Never include weights in public GitHub repository. Never share weights with customers (customers access the API, not the weights).

**2. Training dataset composition**
The specific set of TROPOMI orbits, GHGRP facility pairings, and synthetic plume generation parameters used to create the 50,000+ training examples is not publicly known or inferable. The dataset composition determines what the model learns and therefore directly affects performance. Protect as trade secret through access controls and NDA requirements on all team members with dataset access.

**3. Hyperparameter configuration**
Specific learning rate schedule, dropout rates, loss function weights (w1 = 0.8, w2 = 0.2), batch size, and augmentation parameters are not disclosed in marketing materials or academic publications. These are documented in Document 3 for internal use but should be treated as confidential.

**4. Background removal algorithm parameters**
The specific percentile threshold (15th percentile), sliding window radius (200 km), and facility exclusion zone (20 km) used in background XCH4 removal are not disclosed in prior art and represent calibrated choices that affect attribution accuracy.

**5. Uncertainty threshold calibration**
The specific coefficient of variation thresholds (LOW < 0.15, MEDIUM 0.15–0.40, HIGH ≥ 0.40) are calibrated against the GHGRP validation set. Their empirical calibration represents valuable know-how.

---

### Trade Secret Implementation Protocol

The following operational measures constitute "reasonable steps" to maintain trade secret status under UK law (Trade Secrets (Enforcement, etc.) Regulations 2018, implementing EU Directive 2016/943) and US law (Defend Trade Secrets Act 2016):

**Employee and contractor NDAs:** All team members, contractors, and advisors must sign NDAs before receiving access to any trade secret material. NDAs should specify: (a) the categories of protected information; (b) the obligation to maintain confidentiality survives employment termination for a minimum of 5 years; (c) the obligation to return or destroy all confidential material upon request.

**Access controls:** Role-based access control on all systems containing trade secret material. The trained model weights, training dataset, and configuration files are accessible only to engineers with a documented business need. Access logs maintained and reviewed quarterly.

**Code repository hygiene:** Public GitHub repository (if used for portfolio) contains only architecture documentation and public-facing API specifications. Never commit model weights, training data, or full configuration files to any public repository.

**Customer agreements:** API terms of service prohibit reverse engineering, model extraction, or systematic querying to infer model architecture. Include specific prohibition on using Fluxara outputs to train a competing model.

**Partner and investor disclosure:** When sharing technical details with prospective investors or partners, share Document 3 (Technical Specification) but redact specific hyperparameter values and training data composition details. Always obtain NDA signature before sharing any technical documentation beyond the public executive summary.

---

## Open Source Licensing Considerations

### Inbound Licences: Dependencies Fluxara Uses

All of Fluxara's primary software dependencies carry permissive open-source licences with no restrictions on commercial use:

| Dependency | Licence | Commercial Use | Copyleft Risk |
|---|---|---|---|
| PyTorch 2.3.0 | BSD 3-Clause | ✅ Unrestricted | None |
| NumPy 1.26 | BSD 3-Clause | ✅ Unrestricted | None |
| SciPy 1.13 | BSD 3-Clause | ✅ Unrestricted | None |
| xarray | Apache 2.0 | ✅ Unrestricted | None |
| FastAPI | MIT | ✅ Unrestricted | None |
| PostgreSQL | PostgreSQL Licence | ✅ Unrestricted | None |
| rasterio | BSD 3-Clause | ✅ Unrestricted | None |
| pyresample | LGPL 3.0 | ✅ Permitted (dynamic linking) | Low — LGPL modifications must be open-sourced; use as library without modification is safe |
| shapely | BSD 3-Clause | ✅ Unrestricted | None |
| WeasyPrint | BSD 3-Clause | ✅ Unrestricted | None |
| Jinja2 | BSD 3-Clause | ✅ Unrestricted | None |
| SQLAlchemy | MIT | ✅ Unrestricted | None |
| Matplotlib | PSF (BSD-compatible) | ✅ Unrestricted | None |
| Cartopy | BSD 3-Clause | ✅ Unrestricted | None |
| h5netcdf | BSD 3-Clause | ✅ Unrestricted | None |

The MIT Licence's permissive terms and minimal restrictions remain highly attractive for projects ranging from personal open-source repositories to large-scale commercial products. The Apache Licence 2.0's strong patent grant and clear terms for contributions make it a preferred choice for many enterprise and cloud-native projects. 

**Critical finding:** Fluxara's entire dependency stack is permissively licenced. There is no GPL or AGPL dependency that would require Fluxara to open-source its own code under copyleft obligations.

---

### Open Data Licences: Satellite and Meteorological Data

| Data Source | Licence | Commercial Use | Attribution Required |
|---|---|---|---|
| TROPOMI L2 CH4 (Copernicus) | Copernicus Open Licence | ✅ Yes | Yes — "Contains modified Copernicus Sentinel data [year]" |
| ERA5 (ECMWF CDS) | Copernicus Licence to use Products | ✅ Yes | Yes — acknowledge ECMWF and Copernicus Climate Change Service |
| EPA GHGRP facility data | US Government public domain | ✅ Yes | No requirement |
| EU E-PRTR / EEA Industrial Emissions | EEA standard re-use policy | ✅ Yes | Yes — acknowledge EEA |

Fluxara must include appropriate data attribution notices in its MRV reports and API documentation. The required Copernicus attribution for TROPOMI data is: *"Contains modified Copernicus Sentinel data [year], processed by Fluxara."* This is a purely administrative requirement with no commercial restriction.

**Important:** The Copernicus licences do not restrict commercial use of derived products (Fluxara's attribution outputs are derived products, not raw satellite data redistribution). Fluxara is not redistributing the raw TROPOMI NetCDF4 files; it is selling derived emission attribution — a distinct product category fully permitted under the Copernicus licence.

---

### Outbound Licence: What Fluxara Ships

Fluxara does not ship open-source software. Its product is a commercial SaaS API and report generation service. The following outbound licence structure is recommended:

**Fluxara API Terms of Service (proprietary):** All rights reserved in the software, model, and API. Customers receive a limited, non-exclusive, non-transferable licence to access the API and use outputs for their own internal compliance purposes. No right to redistribute, sublicence, reverse engineer, or use outputs to train competing models.

**Fluxara MRV Report Licence:** Reports generated by Fluxara are licensed for the customer's internal use and regulatory submission only. Reports may be shared with regulators, auditors, and assurance providers as required for compliance purposes. Reports may not be redistributed commercially.

**Public GitHub repository (optional, for recruitment and credibility):** Fluxara may choose to open-source non-core components (e.g., a lightweight TROPOMI data visualisation tool, a public dataset of background XCH4 fields) under MIT licence as a developer relations and recruitment strategy. This must never include model weights, training data, or the core inference pipeline.

---

### The AGPL Risk: The Critical Licence to Audit

The GNU Affero General Public Licence (AGPL) is the most dangerous open-source licence for a SaaS company. Copyleft licences (GPL, AGPL): Commercial use is allowed, but source code disclosure is required when distributing. Unlike the GPL, the AGPL's copyleft triggers for network use — meaning if Fluxara uses AGPL-licenced code to provide a web service, it may be required to release its entire codebase under AGPL. 

Before deployment, Fluxara must audit its full dependency tree for any AGPL-licenced packages. The current identified stack contains no AGPL dependencies. This audit must be repeated whenever a new dependency is added.

---

## Copyright Protection

Copyright arises automatically upon creation in the UK (Copyright, Designs and Patents Act 1988) and in all Berne Convention countries (including the US, EU, and Australia). No registration is required.

The following Fluxara works are automatically copyright-protected upon creation:

- All source code written by Fluxara employees or contractors (under work-for-hire or IP assignment agreements)
- The neural network architecture specification (this documentation)
- MRV report templates (HTML/Jinja2)
- API documentation and specifications
- Training data pipeline code
- This documentation suite (Documents 1–8)

**Critical action:** All IP assignment agreements with employees, contractors, and consultants must include an explicit clause assigning all work product (including software, models, datasets, and documentation created during the engagement) to Fluxara. Without this clause, in the UK, independent contractors retain copyright in their work product by default. All engagement contracts and employment agreements must include this assignment.

**Database rights:** The Fluxara attribution database (the accumulated time series of facility-level emission attributions) qualifies as a database in which Fluxara has invested substantially. Under the UK Database Regulations 1997 (implementing EU Database Directive 96/9/EC), Fluxara holds a 15-year sui generis database right preventing extraction or reutilisation of substantial parts of the database without consent. This right renews automatically each time a substantial investment is made in updating the database.

---

## Recommended IP Strategy

The following strategy is calibrated for a pre-revenue deep tech startup with no legal budget, prioritising zero-cost immediate protection followed by targeted investment aligned with grant funding milestones.

### Phase 1 — Immediate Actions (Pre-Funding, 0–3 Months)

**Cost: £0–£500**

1. **Establish trade secret protocol today.** Draft a one-page internal confidentiality policy identifying the categories of protected information and access control requirements. Have all current team members (including advisors) sign NDAs immediately. Cost: £0 (template NDAs available from UKIPO website).

2. **Register Fluxara as a trademark.** File a UK trademark application for "Fluxara" in Class 42 (scientific and technological services; software as a service; environmental monitoring services) and Class 35 (data analysis services; regulatory reporting services) at the UKIPO (gov.uk/apply-for-a-trademark). Cost: £170 for one class, £50 per additional class = approximately £220 for two classes.

3. **Create an IP register.** Document every piece of IP created by date, author, and description. This creates an evidence record for priority disputes and investor due diligence. Cost: £0 (use a spreadsheet).

4. **Audit all dependency licences.** Review every library in the technology stack for AGPL exposure before writing the first line of code. Cost: £0.

5. **Establish public GitHub hygiene.** If using a public repository for portfolio purposes, establish a clear policy: only non-core components go public. Model weights, training data, and inference code are internal only. Cost: £0.

---

### Phase 2 — Post-Grant Award (Months 3–12)

**Cost: £5,000–£10,000 (fundable from Innovate UK grant IP allocation)**

1. **File provisional patent application** on the core neural atmospheric inversion method (Claim Set 1) and include Claim Sets 2 and 3 as additional claims. Use grant IP funding. Timeline: file before any public conference presentation or academic paper submission describing the enabling technical detail. A provisional application is often compared to planting a flag in the ground. It can be prepared relatively quickly, entails less formality, and requires far less expense.  Cost: approximately £2,000–£4,000 with UK patent attorney.

2. **Obtain formal FTO opinion** on WO 2022/008681 A1 (Kayrros patent application) from a UK patent attorney, reviewing granted claims. Cost: approximately £2,000–£3,000.

3. **Implement employee IP assignment agreements** with all hires and contractors from day one. Cost: legal review of standard template approximately £500–£1,000.

4. **Register copyright in key works** (optional but provides additional evidentiary benefit in the US — the US Copyright Office registration enables statutory damages). UK copyright registration is not available; registration is optional in the US. Cost: approximately $55 per work in the US.

---

### Phase 3 — Post-Series A (Months 12–36)

**Cost: £30,000–£80,000 (from Series A funding)**

1. **Convert provisional to PCT application** at 12 months from provisional filing, preserving the option to enter national phase in US, EU, Canada, Norway, and Australia — Fluxara's target commercial geographies. US-first → PCT at 12 months → National phase at 30/31 months is the standard simplified filing path.  Cost: PCT filing approximately £10,000–£15,000.

2. **File divisional applications** covering the real-time pipeline architecture (Claim Set 2) and the Bayesian uncertainty regulatory output (Claim Set 3) as separate applications, creating a patent family with broader collective coverage. Cost: £4,000–£8,000 per application.

3. **Enter national phase in priority markets** at 30–31 months: US (USPTO), European Patent Office (covering all 38 EPC states including UK, Germany, France, Netherlands, Norway), Canada (CIPO). Cost: £5,000–£10,000 per jurisdiction.

4. **Commission a comprehensive patent landscape analysis** using a patent analytics firm to identify emerging competitor filings and potential infringement risks ahead of commercial launch. Cost: £5,000–£15,000.

---

## IP as a Fundraising Asset

VC-backed startups with strong IP raise more, scale faster, and exit stronger. A structured patent portfolio signals discipline and credibility to investors. A mix of pending and granted applications, mapped to the product roadmap, signals growth and defence readiness. 

For Fluxara's investor presentations, the IP narrative should be structured as follows:

**At pre-seed / ESA BIC stage:**
*"Our IP strategy prioritises trade secrets over patents at this stage. The trained model weights are our primary proprietary asset — analogous to a pharmaceutical compound. They are stored with access controls, protected by NDA with all team members, and are not inferable from our product outputs. We will file a provisional patent application upon completing our first working model, funded through our Innovate UK grant IP allocation."*

**At seed stage (post-prototype):**
*"We have filed a provisional UK patent application [number] covering our neural atmospheric inversion method, real-time attribution pipeline, and Bayesian uncertainty output format for regulatory MRV. We have identified no blocking patents in the atmospheric inversion space. Our freedom-to-operate opinion confirms no infringement risk from the Kayrros WO 2022/008681 A1 application. Our trained model weights are protected as trade secrets. Our attribution database constitutes a sui generis database right under UK law."*

**At Series A:**
*"We have a PCT application in national phase across the US, EU, Canada, and Norway. Our patent family covers the core method, pipeline, and uncertainty quantification output. Our competitive moat is reinforced by a [X]-month historical attribution database covering [Y] facilities — a dataset that no competitor can reproduce retroactively and which improves with every day of additional TROPOMI data ingested."*

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Kayrros / Energy Aspects files patent application covering neural inversion from TROPOMI data | Medium | High | File Fluxara provisional immediately; ensure priority date predates any Kayrros application |
| FootNet or GATES authors spin out a commercial venture | Medium | Medium | Fluxara's patent and trade secret protection; our attribution database moat; regulatory output format differentiation |
| A well-funded competitor (Google, Microsoft, IBM) files a broad ML atmospheric inversion patent | Low | High | Monitor USPTO/EPO filings; ensure Fluxara's provisional establishes prior date; design around broad claims in product architecture |
| Model weights leaked via insider or security breach | Low | Very High | Encryption at rest and in transit; role-based access; NDA with all team members; incident response plan |
| AGPL-licenced dependency discovered in stack post-launch | Low | High | Full licence audit before first line of code; repeat audit on every dependency addition |
| Copernicus data licence terms change | Very Low | Medium | Monitor ESA/ECMWF licence terms annually; Copernicus commercial use has been policy-stable since 2014 |
| Customer reverse-engineers model from API outputs | Low | Medium | Rate limiting; API ToS prohibition; technical obfuscation of output precision beyond regulatory requirement |

---

*End of Document 7 — IP and Defensibility Assessment*

*All patent law references are to UK law (Patents Act 1977, Trade Secrets Regulations 2018, Copyright, Designs and Patents Act 1988) with US equivalents noted where material. This document does not constitute legal advice. Engage a qualified UK and US patent attorney before filing any patent application or making public technical disclosures.*

---

**Fluxara Documentation Suite**
`DOC-01` Scientific Validation · `DOC-02` Regulatory Landscape · `DOC-03` Technical Specification · `DOC-04` Grant Research · `DOC-05` Market Analysis · `DOC-06` Business Plan · `DOC-07` IP Assessment · `DOC-08` Executive Summary
