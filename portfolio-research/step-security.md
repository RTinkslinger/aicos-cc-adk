# StepSecurity's CI/CD Runtime Edge: EDR for GitHub Actions

## Executive Summary

StepSecurity has established itself as a specialized player in the DevSecOps market by focusing on the "runtime" security of GitHub Actions. While many competitors focus on static analysis (scanning code before it runs), StepSecurity's flagship product, **Harden-Runner**, acts as an Endpoint Detection and Response (EDR) agent for the CI/CD pipeline itself. This approach addresses critical supply chain risks—such as exfiltration of credentials and tampering with build artifacts—that static tools often miss.

**Key Strategic Insights:**
* **Runtime Wedge:** The company has successfully leveraged a "bottoms-up" adoption model via the GitHub Marketplace, securing 976 installs and 967 stars [1] [2]. Its claim of protecting 5,000+ projects, including those from Microsoft and Google, indicates strong product-market fit for high-security engineering teams [2].
* **Pragmatic Remediation:** Beyond detection, StepSecurity actively maintains secure "drop-in replacements" for abandoned or risky third-party actions (e.g., `tj-actions/changed-files`), directly reducing attack surface for its users [3] [4].
* **Enterprise Transition:** The company is moving upmarket with features like the "Unified Network Egress View" and eBPF-based monitoring for self-hosted Kubernetes runners [5] [6]. However, reliance on a closed-source enterprise agent for Windows/macOS creates a diligence requirement for regulated buyers [5].
* **Risk Factors:** A disclosed vulnerability in late 2025 (CVE-2025-32955) regarding a bypass of its `disable-sudo` feature highlights the cat-and-mouse nature of runtime security [7]. Buyers must validate remediation and layer controls.

**Recommendation:** For organizations heavily invested in GitHub Actions, StepSecurity offers high-value, low-friction controls for sensitive release pipelines. A 30-day pilot focused on egress allowlisting for release jobs is the recommended entry point.

---

## Company Snapshot

StepSecurity is a cybersecurity startup purpose-built to secure the CI/CD pipeline "runtime" environment. Unlike broad DevSecOps platforms that scan code for vulnerabilities, StepSecurity focuses on what happens *while* the software is being built and deployed.

### Core Product & Target Market
* **Core Product:** **Harden-Runner**, a security agent that monitors and controls network egress, file integrity, and process activity inside GitHub Actions runners [1]. It functions similarly to an EDR (Endpoint Detection and Response) tool but is optimized for ephemeral CI/CD environments.
* **Service:** **StepSecurity Maintained Actions**, a collection of secure, maintained forks of popular but risky or abandoned open-source GitHub Actions [3].
* **Target Market:** Engineering organizations using GitHub Actions, ranging from open-source maintainers to large enterprises (e.g., Microsoft, Google, Kubernetes) that require defense against supply chain attacks like SolarWinds or Codecov [2].

### Founding Team & Footprint
* **Founders:** The company was founded by **Varun Sharma** and **Ashish Kurmi**, described as cybersecurity leaders [8].
* **Size & Location:** As of early 2026, the company has approximately 21 employees [9]. It operates out of Sammamish, Washington, with a registered headquarters in Dover, Delaware [10] [9].

---

## Product and Technical Approach

StepSecurity's technical strategy relies on an agent-based architecture to enforce "deny-by-default" policies in CI/CD environments. This approach is designed to prevent attackers from exfiltrating credentials or injecting backdoors during the build process.

### Feature-to-Threat Mapping
The platform's controls map directly to high-profile supply chain attack vectors.

| Security Measure | Functionality | Threat Mitigation |
| :--- | :--- | :--- |
| **Network Traffic Control** | Monitors/blocks outbound traffic at DNS, L3/L4, and L7 layers. Creates automated baselines for jobs. | Prevents **Codecov-style** credential exfiltration by blocking connections to unknown C2 servers [1] [11]. |
| **Source Code Integrity** | Detects unauthorized file modifications during the build process. | Mitigates **SolarWinds/XZ Utils** attacks where build artifacts are tampered with before signing [11]. |
| **CI/CD Correlation** | Maps every network call and file operation to the exact step, job, and workflow. | Reduces investigation time by pinpointing exactly which part of the pipeline initiated suspicious activity [1]. |

### Architecture & Implementation
The technical implementation varies by environment, which is a critical detail for security architects.

* **GitHub-Hosted Runners:** The solution installs the **StepSecurity Agent**.
 * **Linux:** The community tier agent is **open-source** (Go-based), providing transparency for OSS projects [5].
 * **Windows/macOS:** The agents for these operating systems are **closed-source** [5].
* **Self-Hosted Runners (ARC):** For Kubernetes-based Action Runner Controllers (ARC), StepSecurity uses a **DaemonSet** that leverages **eBPF** (Extended Berkeley Packet Filter) for deep visibility and enforcement. This component is **not open-source** [5].
* **Egress Blocking Mechanism:**
 * **IP Layer:** Uses `iptables` rules to block unauthorized IP addresses [7].
 * **DNS Layer:** Uses a custom DNS proxy. The agent stops `systemd-resolved`, rewrites `/etc/resolv.conf` to point to its local proxy, and then restarts the service to intercept and filter DNS queries [7].

### Tier Comparison
Buyers should select a tier based on their OS requirements and need for centralized management.

| Feature | Community Tier | Enterprise Tier |
| :--- | :--- | :--- |
| **Cost** | Free | Paid |
| **OS Support** | Linux only | Linux, Windows, macOS |
| **Agent Source** | Open Source | Closed Source |
| **Management** | Per-repo config | Centralized "Unified Network Egress View" [6] |
| **Self-Hosted** | Limited | Full ARC (eBPF) support |

---

## Traction and Adoption Signals

StepSecurity has demonstrated significant traction within the GitHub ecosystem, validating the demand for runtime security.

* **Community Engagement:** The `harden-runner` repository has **967 stars** and **83 forks** on GitHub [1].
* **Marketplace Presence:** The StepSecurity app has **976 installs** on the GitHub Marketplace [2].
* **Enterprise Validation:** The company claims its solution protects over **5,000** open-source projects and enterprises, explicitly naming industry giants like **Microsoft, Google, and Kubernetes** as users [2].
* **Maintained Actions:** The company's secure replacement for `tj-actions/changed-files` has garnered **79 stars**, indicating active migration by users seeking safer alternatives [4].

---

## Funding and Runway

StepSecurity is an early-stage, venture-backed startup. Its funding history reflects strong support from specialized security investors and industry practitioners.

**Funding Summary:**
* **Total Raised:** **$3 Million** [9] [12].
* **Latest Round:** **Seed Round**, closed/announced around **March 25 - May 1, 2024** [9] [8].
* **Lead Investor:** **Runtime Ventures** [12].
* **Participating Investors:** Inner Loop Capital, SaaS Ventures, DeVC [12].
* **Notable Angel Investors:** The round included a roster of high-profile security executives, including CISOs and founders from **Coinbase, Zscaler, GreyNoise, Bill.com, and Alteryx** [12].

**Strategic Implication:** The heavy involvement of CISOs as angel investors suggests the product solves a genuine pain point experienced by security leaders, but the relatively small capital raise ($3M) implies the company is still in a lean, early-growth phase.

---

## Competitive Landscape

StepSecurity occupies a specific niche—**CI/CD Runtime Security**—which differentiates it from broader AppSec vendors.

| Competitor Type | Key Players | Comparison to StepSecurity |
| :--- | :--- | :--- |
| **Direct Competitors (CI/CD Security)** | **Aikido Security, Cycode, Legit Security** | These platforms often focus on *governance* (misconfigurations, secrets scanning) and pipeline posture. StepSecurity differentiates by sitting *inside* the runner to block threats in real-time [10]. |
| **Code Quality & SAST** | **Sonar, Snyk** | Focus on finding vulnerabilities in source code *before* build. They do not prevent a compromised build tool from exfiltrating credentials during execution [10]. |
| **Cloud Security (CNAPP)** | **Wiz, Prisma Cloud** | Excellent for securing the cloud infrastructure *after* deployment. StepSecurity protects the *process* of deployment itself. |
| **Dynamic Testing (DAST)** | **StackHawk** | Focuses on testing running applications for vulnerabilities, not securing the build pipeline infrastructure [10]. |

**Verdict:** StepSecurity is best viewed as a complementary control. It does not replace SAST/DAST tools but fills the "runtime gap" that those tools leave open.

---

## Recent News and Developments (Last 12 Months)

* **Security Vulnerability Disclosure (Dec 2025):** Sysdig researchers disclosed **CVE-2025-32955**, a vulnerability in the community tier of Harden-Runner. The issue allowed attackers to bypass the `disable-sudo` feature. The research noted that while IP blocking used `iptables`, the DNS interception relied on rewriting `/etc/resolv.conf`, which could be manipulated [7].
* **Maintained Actions Expansion (2025-2026):** StepSecurity has aggressively expanded its "Maintained Actions" program. As of February 2026, they offer secure replacements for actions like `ssh-agent`, `paths-filter`, and `s3-actions-cache`. These replacements are actively updated (last updates in Feb 2026) to fix security debts like persistent credentials [3] [4].
* **Unified Network Egress View:** The company launched a centralized view for enterprise customers to aggregate and analyze network destinations across all their GitHub Actions workflows, facilitating easier policy creation [6].

---

## Risks and Red Flags

* **Bypass Vulnerabilities:** The disclosure of CVE-2025-32955 [7] proves that the agent is not invincible. Sophisticated attackers with code execution rights inside a runner may find ways to disable the agent.
 * *Mitigation:* Use StepSecurity as part of a defense-in-depth strategy, not a silver bullet.
* **Closed-Source Components:** The enterprise agents (Windows/macOS) and the ARC eBPF daemonset are closed-source [5]. This limits the community's ability to audit the code for bugs or backdoors, a standard concern for security tools.
* **Platform Dependency:** The company is heavily tethered to the **GitHub Actions** ecosystem. While this provides focus, it creates platform risk if GitHub introduces native runtime security features that commoditize StepSecurity's offering.
* **Early Stage Viability:** With only ~$3M in disclosed funding and ~21 employees [9], the company is small. Enterprise buyers should consider the risk of acquisition or pivot when signing long-term contracts.

---

## Market Size and Growth Trajectory

The market for DevSecOps and Application Security provides a strong tailwind for StepSecurity's growth.

* **DevSecOps Market:**
 * **Grand View Research:** Estimates the market at **$8.84 billion in 2024**, growing to **$20.24 billion by 2030** (CAGR of 13.2%) [13].
 * **Technavio:** Forecasts even faster growth, predicting an increase of **$14 billion** between 2024-2028 at a **CAGR of 37.12%** [14].
* **Application Security Market:** MarketsandMarkets projects the broader application security sector to reach **$55 billion by 2029**, growing at a CAGR of 10.3% [15].

**Insight:** The discrepancy in growth rates (13% vs 37%) suggests a volatile but rapidly expanding sector. StepSecurity's niche (runtime protection) is likely to grow faster than the average as attackers shift focus from code vulnerabilities to pipeline compromise.

## References

1. *GitHub - step-security/harden-runner: Harden-Runner is a CI/CD security agent that works like an EDR for GitHub Actions runners. It monitors network egress, file integrity, and process activity on those runners, detecting threats in real-time.*. https://github.com/step-security/harden-runner
2. *StepSecurity Actions Security · GitHub Marketplace · GitHub*. https://github.com/marketplace/harden-runner-app
3. *StepSecurity Maintained Actions | StepSecurity*. https://docs.stepsecurity.io/actions/stepsecurity-maintained-actions
4. *step-security-maintained-actions · GitHub Topics · GitHub*. https://github.com/topics/step-security-maintained-actions
5. *harden-runner/docs/how-it-works.md at main · step-security/harden-runner · GitHub*. https://github.com/step-security/harden-runner/blob/main/docs/how-it-works.md
6. *Unified Network Egress View: Centralize GitHub Actions ...*. https://www.stepsecurity.io/blog/unified-network-egress-view-centralize-github-actions-network-destinations-for-your-enterprise
7. *CVE-2025-32955: Security mechanism bypass in Harden-Runner Github Action | Sysdig*. https://www.sysdig.com/blog/security-mechanism-bypass-in-harden-runner-github-action
8. *StepSecurity Secures $3 Million Seed Funding to Protect CI/CD Pipelines*. https://www.prnewswire.com/news-releases/stepsecurity-secures-3-million-seed-funding-to-protect-cicd-pipelines-302132073.html
9. *StepSecurity 2026 Company Profile: Valuation, Funding & Investors | PitchBook*. https://pitchbook.com/profiles/company/499906-18
10. *StepSecurity - Crunchbase Company Profile & Funding*. https://www.crunchbase.com/organization/step-security
11. *Harden-Runner | StepSecurity*. https://docs.stepsecurity.io/harden-runner
12. *StepSecurity's Big Step: Announcing Our $3M Seed Funding! - StepSecurity*. https://www.stepsecurity.io/blog/stepsecurity-seed-funding
13. *DevSecOps Market Size And Share | Industry Report, 2030*. https://www.grandviewresearch.com/industry-analysis/development-security-operation-market-report
14. * Global Devsecops Market Growth Analysis - Size and Forecast 2024 - 2028  | Technavio *. https://www.technavio.com/report/devsecops-market-analysis
15. *Application Security Market Share, Forecast | Growth Analysis and Trends Report [2032]*. https://www.marketsandmarkets.com/Market-Reports/application-security-market-110170194.html
