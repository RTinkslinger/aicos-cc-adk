---
company: StepSecurity
source: Parallel Deep Research (pro-fast)
date: 2026-03-20
task_group: tgrp_1a4ad04e8a3743e39cef1b5b5c16165b
---

# StepSecurity: Securing the CI/CD Supply Chain – A Deep-Dive into a Fast-Growing US-Founded Play-to-Europe-and-India Market

## Executive Summary
StepSecurity is a rapidly growing cybersecurity startup specializing in CI/CD pipeline protection, specifically targeting GitHub Actions. Despite being headquartered in the United States, the company has strong ties to the Indian tech ecosystem through its founders. The platform currently secures over 18,000,000 CI/CD job runs every week [1] and is utilized by over 8,000 open-source projects, including high-profile repositories from Google, Microsoft, and the Cybersecurity and Infrastructure Security Agency (CISA) [2]. With a recent $3 million seed round [3] and a proven track record of detecting zero-day supply chain attacks [4], StepSecurity represents a critical player in the emerging DevSecOps and AI-agent security landscape.

## 1. Company Snapshot – Who is StepSecurity?
StepSecurity provides a comprehensive security platform designed to detect, prevent, and respond to software supply chain attacks [5]. The company focuses on delivering end-to-end protection for developer machines, npm packages, AI agents, and CI/CD pipelines [5]. Officially filed as a business entity in November 2021, StepSecurity is headquartered in Sammamish, Washington, USA [6] [7]. 

## 2. Founding Team & Leadership
The company is led by a highly technical founding team with deep enterprise software experience:
* **Varun Sharma (Co-founder & CEO):** Based in Redmond, Washington, Sharma is a former Microsoft engineer who brings extensive experience in enterprise cloud security [8].
* **Ashish Kurmi (Co-founder & CTO):** Based in Kirkland, Washington, Kurmi is also a former Microsoft engineer and holds an educational background from Mumbai University, providing the company with strong foundational ties to the Indian engineering talent pool [9].

## 3. Funding History & Capital Structure
StepSecurity is currently in its early venture stages, having successfully raised initial capital to scale its operations.

| Funding Round | Date | Amount Raised | Lead Investor | Key Participants |
|---|---|---|---|---|
| Seed Round | May 2024 | $3 Million | Runtime Ventures | Inner Loop Capital, SaaS Ventures, DeVC, and 15+ industry angels (CISOs from Coinbase, Zscaler, etc.) |

*Takeaway:* The $3 million seed round demonstrates strong early-stage investor confidence, particularly from specialized cybersecurity venture funds and prominent industry practitioners [3] [10]. 

## 4. Product Portfolio & Value Proposition
StepSecurity's core value proposition lies in mitigating the risk of supply chain attacks and helping organizations meet compliance requirements specific to their CI/CD infrastructure [11]. 
* **Harden-Runner:** The flagship product secures CI/CD workflows by controlling network access and monitoring activities on GitHub-hosted and self-hosted runners [4]. It uniquely enforces runner-level network egress controls [2].
* **Developer MDM:** Introduced in early 2026, this product focuses on securing developer machines and AI coding agents, addressing the next frontier of supply chain vulnerabilities [12].

## 5. Market Landscape & Competitive Positioning
The CI/CD security market is highly competitive, with organizations urgently needing to harden environments following high-profile breaches like SolarWinds and XZ Utils [3]. StepSecurity differentiates itself from traditional AppSec vendors by offering specialized, runtime-level enforcement rather than just static analysis.

### 5.1 Competitor Comparison Matrix

| Feature/Capability | StepSecurity | Traditional AppSec Vendors |
|---|---|---|
| Runner-Level Egress Controls | Yes (Harden-Runner) | Limited/None |
| CI/CD Anomaly Detection | Yes (Behavioral monitoring) | Mostly Static Analysis |
| AI Coding Agent Protection | Yes (Developer MDM) | Emerging |
| Open-Source Community Tier | Yes (Free for OS projects) | Varies |

*Takeaway:* StepSecurity's focus on runtime network controls and AI agent security positions it ahead of legacy static analysis tools that fail to catch active pipeline compromises [4] [3].

## 6. Customer Base, Traction & Metrics
StepSecurity has achieved significant bottom-up adoption through its community-led growth strategy.
* **Open-Source Adoption:** Over 8,000 open-source projects use StepSecurity to harden their pipelines, including repositories from CISA, Google, Microsoft, Datadog, Kubernetes, Node, and Ruby [2].
* **Enterprise Traction:** The enterprise tier is actively deployed across customers in the cryptocurrency, healthcare, and cybersecurity industries [2].
* **Scale:** The platform secures more than 18,000,000 CI/CD job runs weekly [1].

## 7. Business Model, Revenue Signals & Unit Economics
StepSecurity operates on a freemium SaaS model. The "Harden-Runner" community tier is free for open-source projects, which acts as a powerful lead-generation engine [4]. This bottom-up approach helps the company gain internal champions who advocate for the paid enterprise tier within their organizations [3]. 

## 8. Recent Milestones (2024-2026)
* **May 2024:** Announced $3 million seed funding led by Runtime Ventures [3].
* **March 2025:** StepSecurity's Harden-Runner successfully detected a critical supply chain compromise in the popular `tj-actions/changed-files` GitHub Action (CVE-2025-30066) [4]. The company released a free, secure drop-in replacement for the community [4].
* **March 2025:** CISA released an official alert regarding CVE-2025-30066, validating the severity of the threat StepSecurity detected [13].
* **January-March 2026:** Launched "Developer MDM" to secure AI coding agents and published research on autonomous bot attacks targeting CI/CD pipelines [4] [12].

## 9. Indian Market Relevance & Expansion Opportunities
While StepSecurity is a US-based corporation [7], its relevance to the Indian market is substantial. Co-founder Ashish Kurmi's background at Mumbai University [9] provides a natural bridge to India's massive developer ecosystem. As Indian IT services and SaaS startups increasingly adopt GitHub Actions and face stringent global compliance standards, StepSecurity's solutions offer a critical layer of defense against supply chain attacks.

## 10. Risks, Information Gaps & Due-Diligence Checklist
**Information Gaps:** There is limited public information regarding StepSecurity's current Annual Recurring Revenue (ARR), exact employee headcount, and specific enterprise customer names (beyond industry verticals). Furthermore, there is no public disclosure of funding rounds beyond the May 2024 seed round.
**Risks:** The company's heavy reliance on the GitHub Actions ecosystem presents a platform concentration risk. 

## 11. Strategic Recommendations
1. **For Enterprise DevSecOps Teams:** Immediately evaluate StepSecurity's Harden-Runner for any GitHub Actions pipelines handling sensitive data, especially given its proven ability to detect zero-day compromises like CVE-2025-30066 [4].
2. **For Investors:** Monitor StepSecurity for a potential Series A round. Request confidential metrics regarding enterprise conversion rates from their 8,000+ open-source user base [2].
3. **For Indian Tech Companies:** Leverage StepSecurity's free community tier to secure open-source projects and evaluate the enterprise tier to meet emerging global compliance mandates for software supply chain security.

## References

1. *StepSecurity | LinkedIn*. https://www.linkedin.com/company/step-security
2. *Structured Data Results (3 entities)*. https://www.stepsecurity.io
3. *StepSecurity's Big Step: Announcing Our $3M Seed Funding!*. https://www.stepsecurity.io/blog/stepsecurity-seed-funding
4. *Harden-Runner detection: tj-actions/changed-files action is ...*. https://www.stepsecurity.io/blog/harden-runner-detection-tj-actions-changed-files-action-is-compromised
5. *StepSecurity - Detect, Prevent, and Respond to Software Supply ...*. https://www.stepsecurity.io/
6. *StepSecurity - Crunchbase Company Profile & Funding*. https://www.crunchbase.com/organization/step-security
7. *Step Security, Inc. Sammamish, WA - filing information*. https://www.bizprofile.net/wa/sammamish/step-security-inc
8. *Varun Sharma - Co-founder & CEO, StepSecurity (ex- ...*. https://www.linkedin.com/in/varunsharma07
9. *Ashish Kurmi - StepSecurity - LinkedIn*. https://www.linkedin.com/in/ashish-kurmi-3428aa24
10. *Step Security $3 Million seed 2024-05-01 - Fundz*. https://www.fundz.net/fundings/step-security-funding-round-seed-56c2f3
11. *StepSecurity: Protecting CI/CD Runners from Supply Chain Attacks*. https://runs-on.com/integrations/stepsecurity/
12. *StepSecurity Developer MDM: Securing Dev Machines & AI Coding ...*. https://www.linkedin.com/posts/ashish-kurmi-3428aa24_introducingstepsecuritydeveloper-mdm-activity-7416904382891372545-u14o
13. *Supply Chain Compromise of Third-Party tj-actions ...*. https://www.cisa.gov/news-events/alerts/2025/03/18/supply-chain-compromise-third-party-github-action-cve-2025-30066
