# Cybrilla's ONDC-first MF rails: from pilot momentum to scalable distribution advantage

## Executive Summary

Cybrilla has established itself as a critical infrastructure layer for India's mutual fund (MF) ecosystem by combining a SEBI-licensed Registrar and Transfer Agent (RTA) capability with a modern API-first Platform-as-a-Service (PaaS). As of March 2026, the company is capitalizing on the Open Network for Digital Commerce (ONDC) wave, having successfully integrated four marquee Asset Management Companies (AMCs)—DSP, Kotak, Motilal Oswal, and Mirae Asset—onto the network within the last 12 months [1] [2] [3] [4].

The company's strategic value lies in its "Fintech Primitives" API stack, which modularizes complex regulatory and technical workflows (KYC, payments, reporting) into plug-and-play building blocks. This infrastructure is now powering a shift from centralized distribution to decentralized, interoperable networks, validated by a pre-Series A funding round in October 2025 from strategic heavyweights 360 ONE Asset, Peak XV, and Groww [5].

However, while Cybrilla claims over 70 partners and 25+ AMC clients, its revenue scale (approx. ₹2.55 Cr in FY24) and lean team size (~36-46 employees) suggest it is still in the early stages of monetization relative to its enterprise influence [6] [7]. For stakeholders, the immediate opportunity is to leverage Cybrilla's ONDC rails to secure early network advantages, while carefully managing operational risks associated with a single-vendor dependency for critical transaction flows.

## Company Snapshot — Building the backbone for India's MF distribution

Cybrilla positions itself as the "AWS of wealth management," providing the invisible technology backbone that powers mutual fund services for AMCs, fintechs, and wealth managers. By abstracting domain complexity, regulatory rules, and technical architecture into APIs, they enable partners to launch investment products in weeks rather than quarters [8] [9].

### Core Products and Services
The company's offering is structured around three primary pillars:

* **Fintech Primitives (PaaS):** A cloud-based API platform that serves as the core engine for mutual fund transactions. It offers modular APIs for investor onboarding (KYC), order management (lumpsum, SIP), payments (UPI, eNACH), and reporting. It is currently used by over 70 partners to build investment experiences [8] [10] [9].
* **Cybrilla POA (ONDC Gateway):** Acting as a "Seller App" TSP (Technology Service Provider) for AMCs, this gateway enables fund houses to participate in the ONDC network. It handles the translation of ONDC protocols into RTA-compliant transactions, managing asynchronous flows and consent orchestration [11] [12].
* **Wealth OS:** An enterprise-grade platform designed for AMCs to streamline back-end operations, launch new products, and manage distribution channels while ensuring regulatory compliance. This system is reportedly used by over 25 AMCs [5] [13].
* **RTA Services:** Cybrilla holds a permanent SEBI Category I Registrar and Transfer Agent license (INR000004404), valid from March 27, 2024. This license allows them to process reverse feeds and service investors directly, closing the loop on transaction data accuracy [8] [14].

### Target Market
Cybrilla serves a dual-sided market:
1. **Supply Side (AMCs):** Helping asset managers modernize legacy stacks and access new distribution rails like ONDC (e.g., DSP, Motilal Oswal) [2] [4].
2. **Demand Side (Distributors/Fintechs):** Enabling wealthtech startups, robo-advisors, and digital platforms to embed mutual fund investment journeys without building deep domain infrastructure from scratch [8] [9].

## Technology Architecture — API-first, ONDC-compliant, RTA-integrated

Cybrilla's technical approach differentiates itself through a "primitives" philosophy—breaking down complex financial workflows into atomic, reusable API calls. This contrasts with legacy monolithic systems often used by incumbent RTAs.

### Technical Stack and Approach
* **API Design:** The platform exposes RESTful endpoints for critical resources like `MF Investment Accounts`, `Transactions`, and `Payments`. It utilizes webhooks to handle the asynchronous nature of mutual fund processing, pushing status updates (e.g., `under_review` → `submitted` → `successful`) to client applications [15] [11].
* **ONDC Integration:** As a verified BuyerApp TSP, Cybrilla implements the ONDC MF specifications, including complex asynchronous callback sequences (`action` → `ack` → `on_action`). The architecture supports "Basket Orders," allowing multiple scheme purchases to be grouped under a single payment event [11] [12].
* **Developer Ecosystem:** To reduce integration friction, Cybrilla provides an SDK available via npm (`@fintechprimitives/fpapi`) and maintains comprehensive Postman collections for sandbox testing. Their stack includes modern web technologies like ReactJS, NodeJS, and Java, hosted on cloud infrastructure using services like Amazon Route 53 [8] [16] [17].

### Product-to-Process Mapping
| Module | Function | Business Value |
| :--- | :--- | :--- |
| **Identity & KYC** | Digital KYC checks via KRA integrations (e.g., CVL) | Reduces drop-offs during onboarding; ensures compliance [11] |
| **Order Management** | Lumpsum, SIP, Redemption, Switch APIs | Enables flexible product structuring (e.g., daily SIPs, micro-investments) [18] |
| **Payments** | UPI, UPI Autopay, eNACH, Netbanking integration | Increases SIP success rates; supports recurring mandates [18] |
| **Reporting** | CAS parsing, capital gains reports, portfolio summary | Provides investors with real-time visibility into performance [18] |

## Leadership and Organization

Cybrilla is led by a founder-operator team with over 15 years of experience in the domain, transitioning from a service-based model to a product-led infrastructure play.

* **Satish Perala (Co-founder & CEO):** An IIT Kharagpur alumnus, Perala has steered the company since its inception in 2010. His focus has been on solving "Digital Public Infrastructure" challenges for wealth-techs [8] [6] [19].
* **Anchal Jajodia (Co-founder):** Jajodia leads the strategic vision for ONDC integration and industry partnerships. He actively advocates for the democratization of wealth creation through open networks [8] [20].
* **Key Executives:** The leadership team includes Sudheendra Kothapalle (Program Manager, Founders' Office) and Tamilarasi Krishnasamy (Head of Fintech Applications), indicating a lean structure focused on product delivery [6] [21].

**Organizational Scale:**
Despite its long operating history, the team remains relatively small, with employee counts estimated between 36 and 46 as of late 2025. This lean headcount suggests a high degree of automation in their operations but also highlights potential capacity constraints for enterprise support [6] [7].

## Funding History and Investor Signals

Cybrilla has attracted strategic capital from key ecosystem players, validating its utility to both asset managers and distribution platforms. While exact valuation figures remain undisclosed in public reports, the caliber of investors signals strong industry endorsement.

### Investment Rounds
| Date | Round | Amount | Investors | Strategic Signal |
| :--- | :--- | :--- | :--- | :--- |
| **Oct 28, 2025** | Pre-Series A | Undisclosed | **360 ONE Asset** (Lead), **Peak XV**, **Groww** | Backing from a major wealth manager (360 ONE) and a unicorn fintech (Groww) suggests direct product-market fit validation [5] [22]. |
| **Sep 25, 2025** | Accelerator | Undisclosed | **Surge (Peak XV)** | Participation in a top-tier accelerator program often precedes scaling [7]. |
| **Dec 21, 2022** | Seed | ₹20 Cr (~$2.44M) | **Florintree Advisors**, Angel Investors | Led by Mathew Cyriac (ex-Blackstone), focused on building the initial product suite and RTA capabilities [23] [7]. |
| **Aug 29, 2015** | Angel | ~$7.7K | Individual Angels | Early operational capital [7]. |

**Note:** Total funding estimates vary by source, with Tracxn citing ~$7.28M and PitchBook reporting ~$2.44M in disclosed amounts. The 2025 round was explicitly strategic, aimed at expanding the product roadmap and AMC integrations [6] [7].

## Go-to-Market and Partnerships — ONDC-first AMC rollouts

In the last 12 months, Cybrilla has aggressively positioned itself as the primary enabler for AMCs joining the ONDC network. This "ONDC-first" strategy has yielded a rapid succession of high-profile partnerships.

### Key Partnerships (Last 12 Months)
| Partner | Date | Scope & Impact |
| :--- | :--- | :--- |
| **Mirae Asset MF** | Feb 02, 2026 | Integrated subscription, redemption, switch, and SIP flows on ONDC. Aimed at platform-agnostic distribution [1]. |
| **Motilal Oswal AMC** | Aug 14, 2025 | Appointed Cybrilla as the backend service provider for ONDC to bridge distribution gaps and reach grassroots investors [4]. |
| **Kotak Mutual Fund** | Jul 24, 2025 | Partnered to leverage ONDC's decentralized infrastructure for reaching Tier 2/3 cities and lowering distribution costs [3]. |
| **DSP Asset Managers** | Jul 14, 2025 | One of the first AMCs to go live on ONDC via Cybrilla. Focus on enabling micro-SIPs and daily SIPs for first-time investors [2]. |

**Milestone:** Cybrilla processed its first live mutual fund order via ONDC on May 23, 2025, marking the transition from pilot to production [24].

## Market Landscape and TAM

Cybrilla operates within a rapidly expanding Indian mutual fund market, where regulatory pushes for digitization and financial inclusion are creating strong tailwinds for infrastructure providers.

* **Market Size:** The Indian mutual fund industry's Average Assets Under Management (AAUM) hit **₹82.01 Lakh Crore** (approx. $1 Trillion) in January 2026, a 6-fold increase over 10 years [25].
* **Growth Trajectory:** The market is forecast to reach **$1.27 Trillion by 2031**, growing at a CAGR of ~6.86% [26].
* **Retail Participation:** Monthly SIP inflows reached a record **₹31,002 Crore** in January 2026, with total SIP accounts standing at 10.29 Crore. This surge in high-volume, low-ticket transactions necessitates automated, low-cost infrastructure like Cybrilla's [27] [28].
* **Regulatory Catalysts:** SEBI's new regulations effective April 1, 2026, aim to lower expense ratios, putting pressure on AMCs to reduce operational costs—a direct value proposition for Cybrilla's automated "Wealth OS" [26].

## Competitive Landscape

Cybrilla competes in a nuanced landscape involving incumbent giants, horizontal fintech infrastructure players, and specialized wealthtech platforms.

| Competitor Type | Key Players | Cybrilla's Position & Differentiator |
| :--- | :--- | :--- |
| **Incumbent RTAs** | **CAMS**, **KFintech** | These duopoly players hold the vast majority of AUM data. Cybrilla differentiates by offering a modern, API-first layer on top of (or as an alternative to) legacy RTA pipes, specifically for ONDC [6]. |
| **Horizontal Infra** | **Setu**, **Decentro**, **M2P** | These firms offer broad fintech APIs (payments, banking). Cybrilla specializes deeply in the *mutual fund* domain with specific RTA licensing and ONDC MF protocols, creating a vertical moat [6]. |
| **Wealthtech Platforms** | **Investwell**, **REDVision**, **Finbingo** | Primarily serve distributors with CRM and front-end tools. Cybrilla focuses on the *backend infrastructure* and connectivity layer, often powering the platforms that distributors use [6]. |

## Risks and Red Flags

While Cybrilla's strategic positioning is strong, potential clients and investors should weigh specific risks:

* **Scale vs. Ambition Mismatch:** With FY24 revenue at ~₹2.55 Cr and a team of under 50, the company is punching above its weight. Supporting mission-critical infrastructure for Tier-1 AMCs requires robust SRE (Site Reliability Engineering) and support capabilities that may be stretched [6] [7].
* **Revenue Disclosure Gaps:** The lack of disclosed funding amounts for the 2025 rounds and discrepancies in total funding data (ranging from $2.4M to $7.3M) obscure the company's true financial runway [6] [7].
* **Ecosystem Volatility:** The mutual fund ecosystem is sensitive to regulatory shifts. For instance, AMFI's directive in Sep 2025 to halt data sharing with third-party apps (MF Central case) highlights the fragility of data access. Cybrilla's RTA license mitigates this but doesn't eliminate ecosystem risk [26].
* **Adoption Risk:** While ONDC momentum is high, it is still in the early adoption phase. If ONDC fails to gain critical mass among retail investors, Cybrilla's heavy bet on this rail could yield lower-than-expected returns.

## Strategic Outlook

Cybrilla has successfully transitioned from a "building phase" to a "deployment phase," securing critical wins with major AMCs and validating its ONDC stack. The immediate future will likely see them focusing on:
1. **Deepening ONDC Utility:** Moving beyond simple orders to complex workflows like switch, STP, and basket orders to reach parity with traditional channels.
2. **Monetization:** Converting pilot ONDC volumes into significant recurring revenue to justify its valuation and support operational scaling.
3. **Operational Resilience:** Proving that a lean team can support enterprise-grade SLAs as transaction volumes from partners like Groww and Kotak scale up.

For ecosystem participants, Cybrilla represents the most "ready-to-use" gateway to the future of decentralized mutual fund distribution, provided they are comfortable with the counterparty risks of an early-stage infrastructure partner.

## References

1. *Mirae Asset Mutual Fund partners with Cybrilla to simplify ...*. https://m.economictimes.com/mf/mf-news/mirae-asset-mutual-fund-partners-with-cybrilla-to-simplify-investing-through-ondc-network/articleshow/127858543.cms
2. *Fetched web page*. https://economictimes.indiatimes.com/mf/mf-news/dsp-asset-managers-partners-with-cybrilla-to-bring-mutual-funds-live-on-ondc-network/articleshow/122434608.cms
3. *Fetched web page*. https://economictimes.indiatimes.com/mf/mf-news/kotak-mutual-fund-announces-ondc-integration-in-collaboration-with-cybrilla/articleshow/122878129.cms
4. *Fetched web page*. https://economictimes.indiatimes.com/mf/mf-news/motilal-oswal-mutual-fund-joins-ondc-appoints-cybrilla-as-service-provide/articleshow/123298644.cms
5. *Cybrilla Secures Pre-Series A Funding Led by 360 ONE Asset | Entrepreneur*. https://www.entrepreneur.com/en-in/news-and-trends/cybrilla-secures-pre-series-a-funding-led-by-360-one-asset/498814
6. *Cybrilla - 2026 Company Profile, Team, Funding, Competitors & Financials - Tracxn*. https://tracxn.com/d/companies/cybrilla/__R5Ck4QMLguhsQuqOR-MPHcuq59NZKt7mjVSv8oaqv_o
7. *Cybrilla 2026 Company Profile: Valuation, Funding & Investors | PitchBook*. https://pitchbook.com/profiles/company/83348-74
8. *Cybrilla | LinkedIn*. https://in.linkedin.com/company/cybrilla
9. *APIs for fintech use cases | Wealth Management*. https://fintechprimitives.com/
10. *Cybrilla Technologies*. https://cybrilla.com/
11. *FP-CybrillaPOA gateway - Introduction*. https://docs.fintechprimitives.com/fp-cybrillapoa-gateway/overview/
12. *Cybrilla – ONDC Route | MFStack*. https://mfstack.com/solutions/cybrilla-ondc-route
13. *Cybrilla secures strategic funding to expand wealth management infrastructure - The Wealth Mosaic*. https://www.thewealthmosaic.com/vendors/wealthtech-strategy-partners/blogs/cybrilla-secures-strategic-funding-to-expand-wealt/
14. *Contact us*. https://cybrilla.com/contact
15. *Introduction – API Reference*. https://fintechprimitives.com/docs/api/
16. *Cybrilla Technologies - Crunchbase Company Profile & Funding*. https://www.crunchbase.com/organization/cybrilla-technologies
17. *Best Practices Guide - Integrate FP APIs into your applications*. https://docs.fintechprimitives.com/general-topics/best-practices-guide/
18. *Introduction - Fintech Primitives*. https://docs.fintechprimitives.com/
19. *Satish Perala - Cybrilla | LinkedIn*. https://in.linkedin.com/in/satishperala
20. *Anchal Jajodia - Cybrilla Technologies | LinkedIn*. https://in.linkedin.com/in/anchaljajodia
21. *Cybrilla Technologies: Founder, Leadership & Team*. https://wellfound.com/company/cybrilla-technologies/people
22. * 360 ONE Asset invests in Cybrilla's pre-Series A round*. https://entrackr.com/snippets/360-one-asset-invests-in-cybrillas-pre-series-a-round-10600054
23. *Florintree Advisors buys stake in Cybrilla | Company Business News*. https://www.livemint.com/companies/start-ups/florintree-advisors-buys-stake-in-cybrilla-11671643863739.html
24. *ONDC x Fintech Primitives: First Live Transaction Successfully Processed*. https://cybrilla.com/blogs/ondc-fintech-primitives
25. *Indian Mutual Fund Industry's Average Assets Under ...*. https://www.amfiindia.com/articles/indian-mutual
26. *India Mutual Fund Market Size, Trends, Share & Competitive Landscape 2031*. https://www.mordorintelligence.com/industry-reports/india-mutual-fund-industry
27. *India's MF industry profile: Rs 81.01 lakh crore AUM in January, up 20.5% - The Times of India*. https://timesofindia.indiatimes.com/business/india-business/indias-mf-industry-profile-rs-81-01-lakh-crore-aum-in-january-up-20-5/articleshow/128458274.cms
28. *As mutual fund industry reaches Rs. 82 lakh crore, 2025 ...*. https://cafemutual.com/news/industry/36699-as-mutual-fund-industry-reaches-rs-82-lakh-crore-2025-ends-with-highest-ever-sip-inflows