---
company: "Alter AI"
notion_page_id: "22529bcc-b6fc-8190-b4d5-e1fb8a87239f"
fetched: "2026-03-20"
content_type: "rich"
---

## Alter AI integration for dev's security gateway 2025-07-09

### Attendees: Cash & Krish

### Product Overview
- Alter is building a security gateway for AI agents and knowledge bases
- Recently accepted to YC (batch started 1.5 weeks ago)
- Founded by ex-Goldman Sachs employee
- Focus on regulated industries, particularly finance

### Technical Details
- Gateway routes all agent calls through centralized security infrastructure
- Features: Protection against SQL/prompt injections, RBAC, OAuth token management, fine-grained logging, identity management, ability to host on customer infrastructure (AWS)

### Use Cases & Differentiation
- Built specifically for regulated financial institutions
- Handles both structured and unstructured data access
- Dev-first approach rather than SaaS solution

---

## Views:

### Aakash (Maybe):
- Good pedigree and smart guy
- Depth is there but limited. Has faced AI in enterprise problem at Goldman
- Super early
- Single interaction would place him in middle 50 of YC (intuition), could be top quartile

### Krish:
+ Proactively setting meetings with everyone on the waitlist (customer backward)
+ Company's idea came up from an actual issue he faced at GS
+ Open Sourcing it
+ Hosted on own infra
(-) Shipping velocity is really poor
(-) Seem to be distracted with a ton of things going on
(-) Overcommited with features
(+) Always been customer centric

---

## Heads up note 2025-08-19

DeVC is investing $100K as part of a YC SAFE round - Community Top Up with Anand Lalwani (US Collective Member | CoFo of Cardinal Robotics)

**Founders**
1. Srikar D - 4 YOE @ Goldman Sachs (Marcus), UT Austin CS 2018. Instrumental in developing infra to launch the Goldman Sachs Card w/ Apple
2. Kevan D - CMU CS 2019, Ex CoFo & CTO @ Compute AI (acquired by Terizza Inc). Built compute engine 5x faster than EMR Spark

**Round details**
- Uncapped YC SAFE note
- Anand Lalwani angel: $20,000
- YC S25 fund: $375K
- Standard YC terms (MFN clause, 0% discount, Uncapped)
- Previous round: $125K for 7% from YC

**Investment risks**
1. PLG approach may not work for sensitive RBAC use cases in enterprise
2. Crowded market with OSS players (Casbin, Oso, Permify) and incumbents (WorkOS, Okta)
3. Shipping velocity flagged

---

## Conversation 2025-09-03

### VV reflections
++ ScaleKit is light years behind
?? Krish is right - shipping velocity is slow
?? Would be very surprised

### Notes
- Srikar worked on Marcus Card at GS
- They will Open Source - TBD on when & what
- Similar to Okta, WorkOS does it for old SaaS paradigm
- Enterprise conversations with JPMorgan, BNY for on-premises deployment
- Policy is deterministic > code | Binary > Y || N
- Policy in natural language is the next step of agent automation
- Biggest gap: Policy as code right now
