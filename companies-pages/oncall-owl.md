# OnCall Owl

**Table of contents (click to navigate)**

---

## Sujoy <> Aakash 2025-09-23 
### Aakash’s India Travel & VC Activity
- Now spending 3 weeks every quarter in India
- Significant shift: Portfolio founders building from India day zero vs. previous 9-18 month transitions
- ~40 DVC portfolio companies now based in SF, New York, Seattle
- Plans to be in India again in November - potential meetup opportunity
### AI Squared Update - Sujoy’s Current Role
- Nearly 2 years at AI Squared post-Multiwoven acquisition
- Entire original team intact and grown, with Bangalore as engineering hub
- Nag remains CTO, now also in Mountain View office
- Sujoy managing:
  - All post-sales operations
  - Customer success
  - New partnerships and alliances mandate
- Team size: 45 people across Bay Area and Bangalore
### AI Squared’s Product & Market Position
- Solving “last mile of AI” - getting models from shelf to end users
- Founded by Ben (ex-DOD chief of data science, early Databricks)
- Target: Regulated industries (financial services, federal government, DOD, supply chain)
- Problem: 6-9 month integration cycles reduced to under 30 days
- Reverse ETL for AI/ML vs. Multiwoven’s data movement focus
- Series B targeting mid-next year
### Federal Government Business
- Strong DOD presence through Advana platform (Chief Data & Analytics Office)
- Marketplace model within defense ecosystem
- Customer segments:
  - DOD (Army, Navy, Air Force)
  - Intelligence agencies (NSA, NGA)
  - Civilian federal (Agriculture, Energy) - laggards compared to DOD
- Requires both technical integration and internal BD/sales work
### Next Venture Exploration
- Sujoy and Nag exploring new ideas in BI/insights space
- Focus: Legacy enterprise software with static dashboards
- Target customers: Users of Tableau, Cognos, Click with hundreds of thousands of installations
- Problem validation already done through AI Squared customer exposure
- Opportunity: Transform rigid, old-school tools where insights live outside the software
### Next Steps
- November meetup when Aakash visits India (early second week through Thanksgiving)
- Aakash to confirm dates and coordinate meeting
[https://notes.granola.ai/d/4C4DBEBD-2253-40D7-B3B3-40A89F59F589](https://notes.granola.ai/d/4C4DBEBD-2253-40D7-B3B3-40A89F59F589)
---


## Update 2026-02-24 

<!-- file block -->
### OnCall Owl — summary (from the 2‑pager)
- **What it is:** An **autonomous AI “on-call engineer”** that can **detect, diagnose, mitigate, verify, and document** production incidents without paging a human.
- **Problem:** Modern distributed systems still rely on humans for on-call. The deck claims **60–80% of incidents are repetitive/deterministic**, while **SRE cost is high** (e.g., $180K+ senior SRE salary; **$5M–$15M annual SRE spend** at ~$500M ARR SaaS).
- **How it works (capabilities):**
  - **Detects** anomalies from observability tools (Datadog, CloudWatch, Prometheus, Grafana)
  - **Diagnoses** via correlating deploy history, metrics, traces, config changes
  - **Mitigates** via actions like rollback, scale, restart, feature flag, traffic shift, failover, within guardrails
  - **Verifies** recovery before closing incident
  - **Learns** by drafting RCA, updating runbooks, creating follow-up tickets
  - Safety model: customers define **safety zones + approval thresholds**, with a **copilot → autonomy** progression.
- **Why it matters / positioning:** Framed as **headcount replacement (labor leverage)** rather than incremental tooling. Target is to reduce L1/L2 on-call burden and MTTR, and be **infra-agnostic** across clouds/Kubernetes and the observability stack (not vendor-locked).
- **Business model (deck numbers):**
  - “Free to start” (connect stack, observe first shift)
  - Pricing shown as **$500/shift/month** (also mentions **$99/mo/shift** earlier) plus **consumption/credit packs** for scale
  - Go-to-market: **PLG**, “discovered during an incident,” bottom-up adoption.
- **Why now:** **Opsgenie end-of-sale (June 2025) and shutdown (April 2027)** creates a rebuild window; plus claim that **AI agents are now reliable enough** for multi-step remediation.
- **Team:**
  - Sujoy Golan (ex Multiwoven cofounder; dev tools / AI platform GTM)
  - Nagendra “Nag” Dhanakeerthi (2x founder; distributed systems + AI/ML at Razorpay; Techstars; Bay Area)
  - Sharath Keshava (founding member; CEO [Sanas.ai](http://sanas.ai/); ex [Observe.ai](http://observe.ai/); described as former cofounder/COO)
- **Fundraise:** **$4M seed**, **$2M open**. Goals: prove MTTR/labor leverage, reach **1000 deployed “AI engineers” in 12 months**, then Series A in ~12 months.
