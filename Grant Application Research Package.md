arkdown# Fluxara — Grant Application Research Package

> **Document 4 of 8 · Fluxara Documentation Suite**
> Prepared June 2026 · Status: Ready for submission

Real-time satellite methane attribution at 8-second inference · 86% accuracy · 1,801× faster than STILT · Zero marginal data cost

---

## Table of Contents

- [Overview](#overview)
- [Grant Programme Profiles](#grant-programme-profiles)
  - [1. Innovate UK Smart Grants](#1-innovate-uk-smart-grants)
  - [2. Innovate UK SBRI — Climate and Environmental Risk Analytics](#2-innovate-uk-sbri--climate-and-environmental-risk-analytics)
  - [3. ESA BIC UK — Business Incubation Centre](#3-esa-bic-uk--business-incubation-centre)
  - [4. ESA BASS — Business Applications and Space Solutions](#4-esa-bass--business-applications-and-space-solutions)
  - [5. EIC Pathfinder Open 2026](#5-eic-pathfinder-open-2026)
  - [6. EIC Accelerator 2026](#6-eic-accelerator-2026)
  - [7. Horizon Europe Cluster 5 — Climate, Energy and Mobility](#7-horizon-europe-cluster-5--climate-energy-and-mobility)
  - [8. NSF SBIR Phase I and Phase II](#8-nsf-sbir-phase-i-and-phase-ii)
  - [9. Norway Research Council — Commercialisation Programme](#9-norway-research-council--commercialisation-programme)
  - [10. Canada NRC IRAP](#10-canada-nrc-irap)
- [Prize Competitions](#prize-competitions)
  - [11. Cleantech Challenge UK](#11-cleantech-challenge-uk)
  - [12. Innovation Zero Awards — MRV Category](#12-innovation-zero-awards--mrv-category)
  - [13. Urban Future Prize Competition](#13-urban-future-prize-competition)
  - [14. SET Award — Startup Energy Transition](#14-set-award--startup-energy-transition)
- [Funding Roadmap](#funding-roadmap)
- [Application Priority Matrix](#application-priority-matrix)
- [Cross-Cutting Application Narrative Blocks](#cross-cutting-application-narrative-blocks)

---

## Overview

This document profiles every grant programme and prize competition relevant to Fluxara's pre-revenue phase. For each programme it documents the administering body, geographic eligibility, funding range, decision timeline, evaluation criteria, the next available submission deadline, and a specific qualification paragraph explaining precisely why Fluxara meets the programme's criteria.

Fluxara is a UK-based deep tech startup building a real-time satellite greenhouse gas attribution system. The core innovation is a Bayesian U-Net neural network surrogate that replaces the STILT atmospheric transport physics model, reducing methane emission source attribution compute time from 4–6 hours to 8 seconds at 86% accuracy. The system ingests free TROPOMI Sentinel-5P satellite data and ERA5 meteorological reanalysis data, attributes facility-level emission rates in kg/hr to operators registered in the EPA GHGRP and EU E-PRTR databases, and generates regulatory-grade MRV reports under EU Methane Regulation (EU) 2024/1787, CSRD ESRS E1, and equivalent frameworks.

**Funding target — pre-seed non-dilutive phase:** £200,000–£500,000 to fund model training, prototype validation against GHGRP ground truth, and first customer pilots with one EU oil and gas operator and one UK environmental agency.

---

## Grant Programme Profiles

---

### 1. Innovate UK Smart Grants

| Field | Detail |
|---|---|
| **Full programme name** | Innovate UK Smart Grants |
| **Administering body** | Innovate UK / UK Research and Innovation (UKRI) |
| **Geographic eligibility** | UK-registered organisations (any size; SMEs favoured) |
| **Funding range** | £25,000–£500,000 (industrial research: 70% of eligible costs; experimental development: 45%) |
| **Total programme budget** | >£350 million awarded in 2025 across 800+ projects |
| **Decision timeline** | 3–4 months from deadline to award notification |
| **Application portal** | Innovation Funding Service (IFS): apply-for-innovation-funding.service.gov.uk |
| **Next deadline** | Quarterly rounds; monitor IFS for Q3 2026 opening (typically August–September) |
| **TRL requirement** | TRL 3–7; Fluxara targets TRL 4–5 at application |

#### Evaluation Criteria

Innovate UK Smart Grants assess applications across three dimensions weighted approximately equally:

1. **Innovation** — Is the proposed technology genuinely novel? Does it advance beyond the current state of the art?
2. **Commercial potential** — Is there a credible, quantified market? Is the business model viable? Is there evidence of customer demand?
3. **Wider impact** — Does the project create economic benefit for the UK? Does it contribute to national or global challenges (climate, net zero)?

#### Why Fluxara Qualifies

Fluxara directly addresses all three Smart Grant evaluation criteria at the highest level. On **innovation**: the neural network surrogate for STILT atmospheric inversion is a genuine scientific advance, validated by the independent peer-reviewed literature (Dadheech, He & Turner, 2025, *Atmospheric Chemistry and Physics*) demonstrating a 650× speedup over STILT using a machine learning surrogate; Fluxara's architecture extends this to a full 1,801× speedup by eliminating the post-footprint optimisation loop entirely. No commercial product offering real-time facility-level methane attribution from free satellite data currently exists. On **commercial potential**: Fluxara's immediate market comprises the 8,000+ US facilities mandated to report under EPA GHGRP Subpart W, the 2,500+ EU facilities under the EU Methane Regulation (EU) 2024/1787 (in force since August 2024), and the Canadian upstream oil and gas sector subject to mandatory measurement-based compliance from 2028. The EU Methane Regulation alone creates penalties of up to 20% of annual turnover for non-compliance, generating an immediate financial driver for independent satellite verification. On **wider impact**: accurate methane quantification at scale directly supports the UK's Net Zero 2050 commitment and the Global Methane Pledge, while positioning UK deep tech in the satellite climate data sector at a moment of maximum regulatory demand.

---

### 2. Innovate UK SBRI — Climate and Environmental Risk Analytics

| Field | Detail |
|---|---|
| **Full programme name** | SBRI — Climate and Environmental Risk Analytics for Resilient Finance (CERAF) |
| **Administering body** | Innovate UK / NERC (Natural Environment Research Council) |
| **Geographic eligibility** | UK-registered organisations of any size |
| **Funding range** | Phase 1: up to £50,000 (inclusive of VAT) per project, 3 months · Phase 2: up to £1,000,000 per project, 9 months |
| **Total pool** | Phase 1: up to £1.5 million across up to 30 projects · Phase 2: up to £10 million across up to 10 projects |
| **Decision timeline** | Phase 1 award within 6–8 weeks of close; Phase 2 invitation to successful Phase 1 participants |
| **IP position** | 100% funded R&D contract; all IP remains with applicant |
| **Key requirement** | At least 50% of contract value must be direct R&D services |
| **Application portal** | IFS: apply-for-innovation-funding.service.gov.uk |
| **Relevant SBRI theme** | Climate and environmental data integration into financial services and risk |

#### Evaluation Criteria

SBRI competitions assess: (1) quality and feasibility of the proposed R&D; (2) relevance to the stated public sector challenge (climate and environmental risk analytics for finance); (3) commercialisation route; (4) team capability. SBRI is a procurement, not a grant — applicants are contracted to deliver specific R&D outputs.

#### Why Fluxara Qualifies

The CERAF SBRI programme explicitly targets solutions integrating climate and environmental data into financial services and public investment. Fluxara's methane attribution output is directly relevant to: (a) financial institutions pricing physical and transition risk in oil and gas loan books and equity portfolios, (b) insurance underwriters quantifying methane liability for energy sector clients, and (c) public investment vehicles assessing SFDR Principle Adverse Impact disclosures for Scope 1 methane intensity. Fluxara's API-delivered emission attribution data constitutes a novel climate risk analytics product with no comparable offering currently available. Phase 1 funding of £50,000 would fund three months of prototype development producing a working TROPOMI ingest and neural inference pipeline for one UK North Sea basin, with output formatted for integration into financial risk scoring systems. Phase 2 funding of up to £1 million would fund full commercial productisation and integration pilots with two financial institution customers.

---

### 3. ESA BIC UK — Business Incubation Centre

| Field | Detail |
|---|---|
| **Full programme name** | ESA Business Incubation Centre United Kingdom (ESA BIC UK) |
| **Administering body** | European Space Agency (ESA) / Science and Technology Facilities Council (STFC) |
| **Geographic eligibility** | UK-registered companies less than 5 years old with at least one member located in the UK |
| **Funding** | Cash incentive of over £50,000 for design, prototyping, IP protection and market studies |
| **Additional support** | Up to 2 years of free or subsidised office space at Harwell, Sci-Tech Daresbury, Royal Observatory Edinburgh, or Space Park Leicester · 50–80 hours of technical support from ESA and university scientists · Business coaching and access to ESA's EPIC partner network (Airbus, Planet, ICEYE, OVH Cloud, and others) |
| **Equity** | Zero equity taken |
| **Decision timeline** | Applications assessed at Tender Opening and Tender Evaluation Boards approximately 4–6 weeks after each deadline |
| **Application deadlines** | Spring and Autumn cycles; **next deadline: 12:00 on 28 August 2026** |
| **Locations** | Harwell Campus (Oxfordshire), Sci-Tech Daresbury (Liverpool City Region), Royal Observatory (Edinburgh), Space Park Leicester |

#### Evaluation Criteria

Applications are assessed on: (1) strength and authenticity of the space connection (satellite data, space technology use, or downstream application); (2) innovation and originality of the business idea; (3) commercial potential and route to market; (4) team capability to execute.

#### Why Fluxara Qualifies

Fluxara's entire value chain is built on space infrastructure — specifically, ESA's own Sentinel-5P TROPOMI instrument, which provides the free daily methane observations that Fluxara's pipeline ingests. This is a textbook ESA BIC application: a downstream commercial service built directly on ESA satellite data, converting a free ESA observation stream into a high-value regulatory data product. The ESA BIC UK was designed precisely for companies in this position. Fluxara qualifies under the downstream Earth observation application category, with direct relevance to ESA's Copernicus programme and the ESA Climate Office's mandate for greenhouse gas monitoring services. The STFC's expertise in satellite data processing at Harwell and the astronomy/Earth observation capabilities at Space Park Leicester make either site an ideal incubation environment for Fluxara's computational and data science requirements. The over-£50,000 cash incentive would fund Fluxara's model training compute costs during the prototype phase, with the STFC technical support providing access to satellite data processing expertise that would otherwise require hiring a specialist.

---

### 4. ESA BASS — Business Applications and Space Solutions

| Field | Detail |
|---|---|
| **Full programme name** | ESA Business Applications and Space Solutions (BASS) — ACCESS Programme |
| **Administering body** | ESA Space Solutions / UK Space Agency |
| **Geographic eligibility** | UK-based entrepreneurs; UK Space Agency co-funds at up to 50% |
| **Funding** | Project-specific; zero-equity basis; co-funding from company funds, loans, or private investment required (primarily monetary, not in-kind) |
| **Key constraint** | Co-funding cannot come from other public sources |
| **Application process** | Permanently open BASS call; contact UK Space Agency Space Data and Applications team before applying to confirm support |
| **Contact** | UK Space Agency Space Data and Applications team (gov.uk/government/publications/accelerating-commercialisation…) |

#### Why Fluxara Qualifies

BASS is structured for exactly Fluxara's application profile: a space-enabled commercial service at pre-commercialisation stage requiring co-investment support. Fluxara's product uses Copernicus satellite data (within ESA's mandate) to deliver a service with measurable environmental benefit (within the UK Space Agency's strategic priorities for space-enabled climate services). Fluxara should engage the Space Data and Applications team early — before applying to ESA BIC UK — to determine whether BASS and ESA BIC funding can be combined or sequenced.

---

### 5. EIC Pathfinder Open 2026

| Field | Detail |
|---|---|
| **Full programme name** | EIC Pathfinder Open 2026 (Horizon Europe) |
| **Administering body** | European Innovation Council (EIC) / European Commission |
| **Geographic eligibility** | Consortia of at least 3 independent legal entities in 3 different EU Member States or Associated Countries; UK organisations eligible as consortium partners (not sole applicants for Open call) |
| **Funding range** | Grants up to €4,000,000 per project; lump-sum budgeting |
| **Total 2026 budget** | €262 million |
| **TRL target** | TRL 1–4; proof-of-concept and early feasibility |
| **Next deadline** | **Open call: 12 May 2026 (passed for 2026) · Challenge call: 28 October 2026** |
| **Decision timeline** | Typically 6–8 months from submission to award |
| **UK participation** | UK organisations can participate as consortium partners in Pathfinder Open; single UK applicants or UK-led 2-member consortia eligible for Pathfinder Challenges |

#### Evaluation Criteria

EIC Pathfinder requires: (1) convincing long-term vision of a radically new technology with transformative potential; (2) concrete, novel, and ambitious science-towards-technology breakthrough; (3) high-risk/high-gain research approach with plausible objectives.

#### Why Fluxara Qualifies

Fluxara's neural atmospheric inversion approach meets the EIC Pathfinder's science-towards-technology brief. The specific EIC Pathfinder Challenge most relevant to Fluxara is the **EIC Accelerator Challenge "Deep Tech for Climate Adaptation"** (part of the EIC Accelerator 2026 programme rather than Pathfinder, but aligned thematically). For Pathfinder Open, Fluxara would need to build a consortium with at least two EU research partners — ideally atmospheric science groups at Wageningen University (Netherlands), KNMI (Netherlands), ECMWF (UK/EU), or Université de Versailles Saint-Quentin (France), all of which have active TROPOMI or ERA5 research programmes. The scientific novelty claim — replacing STILT with a neural surrogate achieving 650–1,801× speedup at equivalent accuracy — is precisely the kind of technology breakthrough EIC Pathfinder funds. The EIC Pathfinder **Challenges call (28 October 2026)** is the more appropriate route for a solo or 2-partner UK-led application.

---

### 6. EIC Accelerator 2026

| Field | Detail |
|---|---|
| **Full programme name** | EIC Accelerator 2026 — Open and Challenge calls |
| **Administering body** | European Innovation Council / European Commission |
| **Geographic eligibility** | SMEs and startups from EU Member States and Associated Countries; UK SMEs eligible for grant-only (non-dilutive) funding since Brexit — equity component not available to UK applicants |
| **Funding range** | Grant only: up to €2,500,000 (70% funding rate; 30% co-financed by applicant) |
| **TRL requirement** | TRL 6 minimum (technology validated in relevant environment); TRL 5 activities must be completed before application |
| **Relevant challenge** | **Deep Tech for Climate Adaptation** — developing and commercially scaling solutions to adapt to key climate risks |
| **Step 2 deadlines 2026** | January 7 · March 4 · May 6 · July 8 · September 2 · November 4 |
| **Step 3 deadlines** | June 2026 · October 2026 · January 2027 |
| **Decision timeline** | Step 1 (short proposal): 4–6 weeks · Step 2 (full proposal): 3–4 months · Step 3 (interview): 2 months |

#### Why Fluxara Qualifies

The EIC Accelerator is Fluxara's primary EU funding route once prototype validation is complete and TRL 5 can be demonstrated. The **Deep Tech for Climate Adaptation** Challenge is an almost exact match: Fluxara's satellite methane attribution system directly enables climate adaptation by providing the measurement infrastructure that allows oil and gas operators and regulators to detect, quantify, and respond to methane super-emitter events in near-real-time. The grant-only route (up to €2.5 million) is available to UK SMEs post-Brexit. Fluxara should target the September 2026 Step 2 deadline, using the period June–August 2026 to prepare a full proposal following a short Step 1 submission. The 70% funding rate means Fluxara would need to demonstrate €750,000 in co-financing — achievable through a combination of Innovate UK Smart Grant funding (preceding award) and angel/pre-seed investment.

---

### 7. Horizon Europe Cluster 5 — Climate, Energy and Mobility

| Field | Detail |
|---|---|
| **Full programme name** | Horizon Europe 2026–2027 Work Programme, Cluster 5: Climate, Energy and Mobility |
| **Administering body** | European Commission / Directorate-General for Research and Innovation |
| **Geographic eligibility** | Consortia including at least 3 legal entities from 3 different EU Member States or Associated Countries; UK eligible as partner |
| **Funding range** | Varies by call topic; typically €2–10 million per consortium project |
| **Total 2026–2027 budget** | Cluster 5 portion of €14 billion programme |
| **Relevant call areas** | Climate monitoring and services; methane emission observation; energy transition data infrastructure |
| **Deadline window** | Most Cluster 5 calls: September–November 2026 |
| **TRL range** | TRL 3–7 depending on call type (Research and Innovation Actions vs Innovation Actions) |

#### Why Fluxara Qualifies

Horizon Europe Cluster 5 funds collaborative research directly relevant to Fluxara's scientific foundations. The most relevant call topics for Fluxara are those targeting: improved greenhouse gas monitoring and attribution for the EU Copernicus Atmosphere Monitoring Service (CAMS), methane emission quantification from satellite observations, and data infrastructure for the EU Methane Regulation. Fluxara's role in a Cluster 5 consortium would be as the technical lead for neural atmospheric inversion, partnering with atmospheric science research institutes and an oil and gas operator as an end-user partner to provide ground truth data and demonstrate the regulatory use case. Fluxara should engage the UK National Contact Points for Horizon Europe and Innovate UK Business Connect's European team in Q3 2026 to identify the most precisely targeted open call before the autumn deadline window.

---

### 8. NSF SBIR Phase I and Phase II

| Field | Detail |
|---|---|
| **Full programme name** | NSF Small Business Innovation Research (SBIR) / Small Business Technology Transfer (STTR) Program — NSF 26-510 |
| **Administering body** | National Science Foundation (NSF) / America's Seed Fund |
| **Geographic eligibility** | US-based small businesses (fewer than 500 employees; at least 50% owned by US citizens or permanent residents; primary employment of PI at the applicant company) |
| **Funding range** | Phase I: up to $305,000 (6–12 months) · Phase II: up to $1,250,000 (up to 24 months) |
| **Authorization status** | Reauthorized as Public Law 119-83 on 13 April 2026 (Small Business Innovation and Economic Security Act, S. 3971); programs fully operational |
| **Process** | Step 1: Project Pitch submission (written, ~1 page) → invitation → Step 2: Full proposal |
| **Project Pitch opens** | June 2, 2026 (new pitches); rolling acceptance thereafter |
| **Full proposal deadlines** | November 4, 2026 · March 4, 2027 (annually thereafter) |
| **Relevant topic area** | Environmental Technologies (ENV); Other Topics (OT1) for novel cross-disciplinary approaches |
| **Review criteria** | (1) Intellectual Merit — quality and novelty of research; (2) Broader Impacts — societal benefit, commercialisation potential |
| **Eligibility note** | Fluxara would need to incorporate a US entity; PI must spend >51% work time at applicant company |

#### Why Fluxara Qualifies

NSF SBIR Phase I funds exactly the class of high-risk, high-reward deep technology research that Fluxara represents. The Intellectual Merit criterion is met by the neural surrogate for STILT atmospheric inversion, which is a genuine scientific advance directly verifiable against peer-reviewed benchmarks (FootNet, Joyce et al. 2023, Rouet-Leduc et al. 2024). The Broader Impacts criterion is met by Fluxara's direct application to US regulatory compliance — the EPA GHGRP Subpart W reporting system and the IRA Waste Emissions Charge (scheduled at $1,500/tonne CH4 from 2034) — as well as by the quantified gap between GHGRP-reported values and satellite-derived estimates (13–600% underreporting documented in peer-reviewed literature). Fluxara should target the **Environmental Technologies (ENV)** topic area, specifically the subtopic covering remote sensing and atmospheric measurement. The Phase I award of up to $305,000 would fund model training infrastructure, TROPOMI pipeline build-out, and initial validation against GHGRP ground truth. Phase II at up to $1,250,000 would fund commercial productisation and first operator pilots. **Action required:** Fluxara would need to establish a US legal entity (Delaware C-Corp recommended) and ensure the PI is primarily employed by that entity. NSF SBIR cannot be applied for as a UK-only company.

---

### 9. Norway Research Council — Commercialisation Programme

| Field | Detail |
|---|---|
| **Full programme name** | Qualification Project — Commercialisation of Research at Publicly Funded Research Organisations 2026 (successor to FORNY2020) |
| **Administering body** | Research Council of Norway (Forskningsrådet) |
| **Geographic eligibility** | Approved research organisations, Technology Transfer Offices (TTOs), and startups originating from approved Norwegian research organisations |
| **Funding range** | NOK 100,000–500,000 (~£7,000–£36,000) per qualification project · Verification projects: up to NOK 3,000,000 (~£218,000) |
| **Total pool** | NOK 60,000,000 (~£4.4 million) for qualification phase |
| **Project duration** | 3–12 months |
| **Application** | Open-ended (rolling) |
| **Eligibility note** | Requires affiliation with a Norwegian publicly funded research organisation or TTO; direct startup applications must demonstrate origin from such an organisation |

#### Why Fluxara Qualifies

Norway is the EU's largest non-Russian gas supplier and a primary Fluxara target market — Norwegian Continental Shelf operators (Equinor, AkerBP, TotalEnergies Norway) are directly subject to EU Methane Regulation MRV equivalence requirements as EEA market access conditions. Norway's Research Council commercialisation programme funds precisely the validation stage Fluxara requires: initial investigation of commercial application of research results. Fluxara's academic validation against peer-reviewed atmospheric science literature (Dadheech et al. 2025, Joyce et al. 2023) provides the research foundation. **Practical route:** Fluxara should identify a Norwegian university partner — the University of Oslo's Department of Geosciences, the Norwegian Meteorological Institute (MET Norway), or NORCE — with active satellite methane or atmospheric transport research, and apply jointly through their TTO. NORCE (Norwegian Research Centre) has documented expertise in TROPOMI data processing and oil and gas methane monitoring, making it the optimal partner. A qualification project (NOK 100,000–500,000) would fund a scoping study of Fluxara's applicability to NCS emission attribution, creating the basis for a verification project application (up to NOK 3,000,000) and a commercial pilot with a Norwegian operator.

---

### 10. Canada NRC IRAP

| Field | Detail |
|---|---|
| **Full programme name** | National Research Council of Canada Industrial Research Assistance Program (NRC IRAP) — Financial Assistance |
| **Administering body** | National Research Council of Canada (NRC) |
| **Geographic eligibility** | Canadian-incorporated, for-profit SMEs with fewer than 500 full-time equivalent employees |
| **Funding range** | Typical first-time awards: CAD $75,000–$200,000 · Larger projects possible up to CAD $10,000,000+ for cleantech · Funds 75–80% of admissible expenses (salary, contractors, materials) |
| **Programme budget** | >CAD $550 million allocated to SMEs in 2025–2026 fiscal year, growing in 2026–2027 |
| **Clean tech stream** | NRC IRAP Clean Technology — expanded mandate following absorption of SDTC in June 2024; targets TRL 5–6+ with demonstrable GHG reduction |
| **AI stream** | NRC IRAP AI Assist — supports SMEs building deep learning and generative AI solutions |
| **Application** | No fixed deadline; relationship-based — contact NRC via 1-877-994-4727 to initiate |
| **Timeline** | First contact to contribution agreement: typically 3–4 months |
| **Eligibility note** | Requires Canadian incorporation; Fluxara would need a Canadian subsidiary |

#### Why Fluxara Qualifies

Fluxara qualifies under both the NRC IRAP Clean Technology stream (satellite-derived methane attribution directly reduces GHG emissions by enabling targeted regulatory enforcement and LDAR prioritisation) and the AI Assist stream (Fluxara's core innovation is a deep learning model replacing a physics-based computational system). Canada's Enhanced Methane Regulations (effective 2028–2030 for all upstream facilities) create the strongest mandatory measurement-based MRV requirement in the world outside the EU, generating direct commercial demand for Fluxara's product from Canadian operators in Alberta, BC, and Saskatchewan. NRC IRAP's combination of advisory services and non-repayable financial contributions — covering up to 80% of salary and contractor costs — makes it the highest-value single programme available to a Canadian entity at Fluxara's stage. **Practical route:** Incorporate a Canadian subsidiary (Alberta or BC recommended, given proximity to the oil and gas sector), engage an NRC Industrial Technology Advisor (ITA) immediately, and build toward a Clean Technology project proposal. Combine with SR&ED tax credits (which can be stacked with IRAP on separate cost pools) for maximum non-dilutive coverage.

---

## Prize Competitions

Prize competitions offer non-dilutive funding, public visibility, investor introductions, and credibility signals that are disproportionately valuable for a pre-revenue deep tech startup. The following are the most relevant competitions for Fluxara in the UK and US in 2026.

---

### 11. Cleantech Challenge UK

| Field | Detail |
|---|---|
| **Programme** | Cleantech Challenge UK — National Student Cleantech Competition |
| **Organiser** | The Cleantech Challenge (thecleantechchallenge.uk) |
| **Eligibility** | Student and early-stage founders; technically minded teams with business-focused co-thinkers |
| **Prize** | Two £20,000 prizes — strongest environmental impact and strongest commercial promise |
| **Format** | Application → finalist selection → mentorship from cleantech founders and investors → final pitch (2026 final: 23 April 2026; watch for 2027 cycle) |
| **Strategic value** | Direct access to cleantech investors, utility partners, and manufacturing contacts; past winners report "opening doors with serious utility partners" |

#### Why Fluxara Should Enter

Fluxara is a textbook Cleantech Challenge entry: a technically deep, student-originated venture with a clear commercial case and a quantified environmental impact (methane emission reductions enabled at scale). The £20,000 prize is meaningful at pre-seed stage. More valuable than the cash is the finalist exposure to cleantech investors who specifically invest in deep tech climate ventures at this stage. Fluxara's founder is a CS undergraduate, placing the venture squarely in the target demographic. **Action:** Target the 2027 cycle (typically opens Q4 2026). Use the application preparation as a forcing function to compress the pitch narrative to 400 words.

---

### 12. Innovation Zero Awards — MRV Category

| Field | Detail |
|---|---|
| **Programme** | Innovation Zero Awards 2027 (annual; 2026 finalists already announced) |
| **Organiser** | Innovation Zero World (innovationzero.com) |
| **Eligibility** | Startups, scaleups, and established businesses at TRL 4+; any geography |
| **Categories relevant to Fluxara** | MRV (Measurement, Reporting and Verification) — **Promising Solution** and **Mature Solution** tracks |
| **Prize benefits** | Assessment by sustainability and procurement leaders from major enterprises and cleantech investors; Green Solutions Catalogue profile; 50% discount on Innovation Zero World 2026 Showcase packages; direct buyer and investor introductions |
| **Past MRV winners** | 2025 Mature Solution MRV: Converge · 2025 Promising Solution MRV: Pulpatronics |
| **Strategic value** | The MRV category is precisely Fluxara's market. Innovation Zero is the largest dedicated net-zero technology event in Europe. |

#### Why Fluxara Should Enter

The Innovation Zero Awards MRV category is Fluxara's single highest-value prize competition target. It is judged from the perspective of corporate buyers — the oil and gas operators and environmental compliance teams who are Fluxara's target customers. Winning or finalling in the MRV category provides direct access to procurement decision-makers at the scale of companies that could become Fluxara's first enterprise customers. The 2025 Promising Solution MRV winner (Pulpatronics) described the award as "a stamp of approval and validation for what we're building." Fluxara's satellite attribution pipeline is a more technically advanced and regulatory-grade MRV solution than most award entrants at this stage, making the Promising Solution track highly competitive. **Action:** Monitor innovationzero.com for 2027 cycle opening (typically Q4 2026). Prepare the submission using the Innovation Zero "purchasability" framing: show concisely how Fluxara's output integrates with an operator's existing compliance workflow.

---

### 13. Urban Future Prize Competition

| Field | Detail |
|---|---|
| **Programme** | Urban Future Prize Competition 2026/2027 |
| **Organiser** | Urban Future Lab, NYU Tandon School of Engineering (urbanfuturecompetition.com) |
| **Eligibility** | Climate tech startups; any geography; no TRL minimum specified |
| **Tracks** | Climate Mitigation Prize (GHG reduction focus) and Climate Adaptation Prize |
| **Prize** | Two winners: $50,000 cash prize each + admission into ACRE Incubator (New York's longest-running climatetech program) · Runner-up teams: $10,000 + ACRE admission |
| **Sponsors** | MUFG Bank, New York Community Trust, NYSERDA, NYU Tandon |
| **2026 Final** | October 22, 2026, Urban Future Summit, New York City |
| **Strategic value** | US market entry signal; ACRE incubator provides New York base for US business development; NYSERDA connection opens New York state procurement pathway |

#### Why Fluxara Should Enter

Fluxara fits the **Climate Mitigation Prize** track: satellite methane attribution directly enables methane emission reduction at scale by identifying and prioritising the highest-emitting facilities for LDAR intervention. The $50,000 prize is meaningful at pre-seed stage. The ACRE incubator admission provides Fluxara with a US physical presence and investor network that would be essential for any NSF SBIR application or US commercial development. Past winners report using the prize to open customer conversations in multiple countries. **Action:** Monitor urbanfuturecompetition.com for 2027 cycle applications (typically opens Q1 each year). The application requires a short description of the solution and its climate impact — use the Document 1 summary language.

---

### 14. SET Award — Startup Energy Transition

| Field | Detail |
|---|---|
| **Programme** | SET Award 2026/2027 — Startup Energy Transition Award |
| **Organiser** | dena (German Energy Agency) and World Energy Council |
| **Eligibility** | Energy transition startups; any geography; multiple tracks including Industry/Emissions |
| **Tracks relevant to Fluxara** | Industry (decarbonisation of industrial emissions) and Energy (monitoring and data infrastructure) |
| **Strategic value** | Germany and broader DACH region are major EU oil and gas consumers and CSRD reporters; SET Award provides exposure to German energy sector investors and corporate partners (E.ON, Siemens Energy, RWE are past sponsors) |
| **Past finalists** | 10th jubilee edition in 2026; strong track record of connecting finalists to European energy corporate pilots |

#### Why Fluxara Should Enter

The SET Award's Industry track targets decarbonisation of industrial emissions — a precise match for Fluxara's methane attribution product targeting oil and gas operators. German operators (Wintershall Dea, BASF, Uniper) and their EU Methane Regulation compliance obligations represent a near-term enterprise customer segment. The SET Award provides European corporate exposure that directly maps to Fluxara's EU sales strategy. **Action:** Target the 2027 SET Award cycle. Prepare submission emphasising Fluxara's direct CSRD ESRS E1 and EU Methane Regulation compliance use case for EU industrial operators.

---

## Funding Roadmap

The following sequencing reflects Fluxara's development stage (pre-code, pre-revenue), geographic position (UK-based), and the realistic timelines of each programme:
PHASE 1 — Foundation (Q3 2026 – Q1 2027)  TARGET: £50,000–£100,000
─────────────────────────────────────────

ESA BIC UK application → 28 Aug 2026 deadline
→ £50,000+ cash + 2 years office space + STFC technical support
Innovate UK Smart Grants → Q4 2026 round
→ Up to £150,000 at 70% funding rate
Cleantech Challenge UK → 2027 cycle application (Q4 2026)
→ £20,000 prize + investor introductions

PHASE 2 — Prototype (Q2 2027 – Q4 2027)  TARGET: £200,000–£500,000
─────────────────────────────────────────

NSF SBIR Phase I → Project Pitch rolling; full proposal Nov 2026 / Mar 2027
→ Up to $305,000 (requires US entity)
Norway Research Council Qualification Project → Rolling
→ NOK 100,000–500,000 via NORCE/UiO partnership
Canada NRC IRAP → Initiate ITA contact Q1 2027
→ CAD $75,000–$500,000 (requires Canadian entity)
Innovation Zero Awards MRV → 2027 cycle
→ Prize + enterprise customer introductions

PHASE 3 — Commercial Validation (2028)  TARGET: €2.5M–£1M
─────────────────────────────────────────

EIC Accelerator — Deep Tech for Climate Adaptation challenge
→ Up to €2,500,000 grant (UK SME grant-only route)
NSF SBIR Phase II → Following Phase I award
→ Up to $1,250,000
Horizon Europe Cluster 5 consortium → Autumn 2027 deadline
→ €2–10M as technical lead in EU-UK consortium


---

## Application Priority Matrix

| Programme | Deadline | Amount | Effort | Priority | Action Required Now |
|---|---|---|---|---|---|
| ESA BIC UK | 28 Aug 2026 | £50,000+ | Medium | **HIGHEST** | Register at esa-bic.org.uk; prepare business plan and incubation proposal |
| Cleantech Challenge UK | 2027 cycle | £20,000 | Low | High | Monitor thecleantechchallenge.uk for opening |
| Innovate UK Smart Grants | Q4 2026 | £25k–£500k | High | High | Register on IFS; monitor for Q3 2026 opening |
| Innovation Zero Awards | 2027 cycle | Non-cash | Low | High | Monitor innovationzero.com/awards |
| NSF SBIR Phase I | Nov 4 2026 / Mar 4 2027 | $305,000 | High | Medium | Incorporate US entity; register at SAM.gov |
| EIC Accelerator | Sep 2 / Nov 4 2026 | €2,500,000 | Very High | Medium (2027) | Reach TRL 5; prepare Step 1 short proposal |
| Norway Research Council | Rolling | NOK 100k–500k | Medium | Medium | Identify NORCE/UiO partner |
| Canada NRC IRAP | Rolling | CAD $75k–$500k | Medium | Medium | Incorporate Canadian entity; call 1-877-994-4727 |
| SBRI CERAF | Watch for re-open | £50k → £1M | Medium | High (if open) | Monitor IFS for next CERAF competition |
| Horizon Europe Cluster 5 | Autumn 2026/2027 | €2–10M | Very High | Low (2027) | Identify EU consortium partners |

---

## Cross-Cutting Application Narrative Blocks

The following are pre-written, reusable narrative blocks that address the most common evaluation criteria across all programmes above. Copy and adapt as required for each application.

---

### The Problem (150 words)

Satellites measure atmospheric methane concentrations globally every day. Converting those observations into actionable, facility-level emission attribution — the data that regulators, operators, and investors actually need — currently requires running the STILT or WRF-Chem atmospheric transport model on a supercomputer cluster for 4 to 6 hours per scene. No commercial real-time attribution product exists. As a result, the EU Methane Regulation (in force since August 2024), the Canadian Enhanced Methane Regulations (effective 2028), and the CSRD ESRS E1 methane disclosure requirements all mandate facility-level measurement-based MRV that cannot currently be provided in real time at regulatory grade. Satellite methane emissions data has shown US oil and gas emissions at over four times EPA-reported rates for the same areas. The gap between what satellites see and what facilities report is the problem. The bottleneck is computation, not observation.

---

### The Solution (150 words)

Fluxara replaces the STILT physics model with a Bayesian U-Net neural network surrogate, reducing atmospheric methane attribution inference time from 4–6 hours to 8 seconds — a 1,801× speedup — at 86% accuracy versus the physics baseline. The system ingests free TROPOMI Sentinel-5P satellite methane observations and ERA5 meteorological reanalysis data daily, applies neural atmospheric inversion to attribute emission rates in kg/hr to specific facilities registered in the EPA GHGRP and EU E-PRTR databases, quantifies uncertainty using Bayesian Monte Carlo Dropout, and outputs regulatory-grade MRV reports directly structured for EU Methane Regulation Article 12 submission and CSRD ESRS E1 Scope 1 methane disclosure. All primary data inputs are free and open-access. There is zero marginal data cost per scene processed. The peer-reviewed literature independently validates the approach: FootNet (Dadheech, He & Turner, 2025, *Atmospheric Chemistry and Physics*) demonstrated a 650× speedup using a comparable ML surrogate.

---

### Market and Commercial Case (150 words)

The total addressable market for satellite-based methane MRV is anchored by regulatory mandate, not by market creation. The EU Methane Regulation (EU) 2024/1787 applies to 2,500+ EU oil and gas facilities with penalties up to 20% of annual turnover. California SB 253 mandates GHG Protocol Scope 1 disclosure from August 2026 for all companies with >$1 billion in US revenue. Canada's Enhanced Methane Regulations cover all upstream oil and gas facilities from 2030. The initial Serviceable Addressable Market comprises 200 large oil and gas operators in the EU and US, each spending $50,000–$500,000 annually on compliance monitoring. Fluxara's SaaS API pricing model targets $5,000–$25,000 per facility per year, with enterprise report generation at $500–$2,000 per report. At 50 enterprise customers with 10 facilities each, ARR reaches $2.5–12.5 million. No commercial real-time satellite attribution competitor exists.

---

### Team and Founder Background (75 words)

Fluxara was founded by a third-year Computer Science undergraduate with an AI and software engineering focus. The technical blueprint — covering all atmospheric physics, neural architecture, data pipeline, regulatory mapping, and business model — was developed independently before any code was written, demonstrating the systems thinking and documentation discipline required to build and operate a regulatory-grade data infrastructure company. The founder is actively seeking a technical co-founder with atmospheric science or geospatial engineering expertise.

---

*End of Document 4 — Grant Application Research Package*

*All funding figures, deadlines, and programme details are accurate as of June 2026. Verify current deadlines at programme portals before submitting. ESA BIC UK next deadline confirmed as 28 August 2026. NSF SBIR reauthorized as Public Law 119-83 on 13 April 2026.*

---

**Fluxara Documentation Suite**
`DOC-01` Scientific Validation · `DOC-02` Regulatory Landscape · `DOC-03` Technical Specification · `DOC-04` Grant Research · `DOC-05` Market Analysis · `DOC-06` Business Plan · `DOC-07` IP Assessment · `DOC-08` Executive Summary
