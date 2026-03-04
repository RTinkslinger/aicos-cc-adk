# Dodo Payments: India-first Merchant-of-Record for Global SaaS Monetization

## Executive Summary

Dodo Payments has emerged as a specialized Merchant of Record (MoR) platform designed to help SaaS and AI companies monetize globally, with a distinct competitive wedge in the Indian and emerging market ecosystems. As of March 2026, the company differentiates itself from incumbents like Paddle and FastSpring by offering native support for Unified Payments Interface (UPI) and other local payment methods critical for capturing revenue in high-growth developing economies.

**Key Strategic Insights:**
* **Emerging Market Wedge:** Dodo is the first MoR to aggressively target the "India-to-Global" and "Global-to-India" corridors, supporting UPI and local wallets alongside standard cards. This addresses a major gap for global SaaS companies struggling to convert Indian customers due to recurring payment mandate failures on traditional card networks.
* **Developer-Centric GTM:** The company is bypassing traditional sales cycles with a heavy focus on developer experience, offering SDKs for modern stacks (Next.js, Rust, Go) and "Sentra," an AI-powered IDE agent that integrates billing directly within code editors.
* **Execution Risks:** While the vision is compelling, the company's product scope is extremely broad for its seed stage—spanning payments, tax, billing, fraud, and distribution. This "mile-wide" approach risks shallow feature depth compared to mature competitors who have spent a decade refining subscription logic and tax compliance.
* **Market Timing:** Dodo is capitalizing on two massive tailwinds: the explosion of Indian SaaS (projected to reach $20-25B by 2030) and the globalization of UPI (projected to handle two-thirds of digital merchant payments in India by 2026).

## Company Snapshot

**Dodo Payments** is a cross-border payments and billing platform operating as a Merchant of Record (MoR). This model means Dodo technically "resells" a software vendor's product to the end customer, thereby taking on the legal liability for sales tax collection, remittance, and compliance in over 200 jurisdictions.

* **Headquarters:** Bengaluru, India
* **Founded:** 2023
* **Core Value Prop:** Enables digital businesses to sell globally without setting up local entities, handling tax/compliance automatically.
* **Key Metrics:** Claims 1,000+ merchants, operations in 30 countries, and >90% transaction success rates.
* **Target Market:** AI-native products, SaaS startups, and digital goods creators, particularly those needing to accept payments from emerging markets like India, Brazil, and Southeast Asia.

## Product and Technology

Dodo Payments offers a "monetization stack" that consolidates payments, billing, and tax compliance. Its architecture is designed to abstract away the complexity of multi-country banking rails.

### Core Capabilities: MoR + Billing + Payments
The platform's primary function is to act as the reseller for digital goods, covering:
* **Global Payment Acceptance:** Supports 25+ local payment methods including UPI (India), Apple Pay, Klarna, Affirm, and Cash App. The platform claims coverage in 220+ countries and territories [1] [2].
* **Flexible Billing Engine:** Supports diverse monetization models including usage-based billing (metering), recurring subscriptions, and one-time payments. This is critical for AI companies that often bill on "tokens" or "compute usage" rather than just flat monthly fees [1].
* **Tax & Compliance:** Automatically calculates, collects, and remits taxes (VAT, GST, Sales Tax) globally. As the MoR, Dodo is the liable party for these taxes, shielding the merchant from regulatory penalties [1].

### Developer Experience & AI Integration
Dodo distinguishes itself with a "developer-first" approach, offering tools that integrate monetization into the software development lifecycle (SDLC):
* **Broad SDK Support:** Provides SDKs for TypeScript, Python, Go, PHP, Java, Kotlin, C#, and Ruby.
* **Framework Adapters:** "Drop-in" adapters for modern web frameworks like Next.js, Nuxt, SvelteKit, Remix, Astro, and Hono, allowing integration in "under 10 lines of code" [1].
* **Sentra (Alpha):** An "agentic stack" and IDE-first assistant that integrates billing and payments directly inside VS Code, Cursor, or Windsurf. This allows developers to "prompt" billing logic into existence rather than writing boilerplate code [1].
* **MCP Server:** A Model Context Protocol (MCP) server that connects AI models directly to Dodo Payments, enabling AI agents to trigger billing actions or retrieve revenue data [1].

### Compliance & Security
* **PCI DSS Compliant:** The platform maintains Level 1 PCI DSS compliance, ensuring secure handling of card data [1].
* **Merchant of Record Liability:** Unlike a standard payment gateway (e.g., Stripe), Dodo takes on the liability for chargebacks and fraud, using AI/ML models for real-time fraud detection and risk management [2] [3].

## Founding Team & Leadership

The company is led by a product-focused founding duo with backgrounds in high-growth tech environments.

* **Rishabh Goel (Co-founder & CEO):** Leads the strategic vision and go-to-market execution.
* **Ayush Agarwal (Co-founder & CPTO):** Oversees the technical architecture and product roadmap. His commentary emphasizes solving the "nuanced challenges of cross-border transactions" and evolving the platform's architecture [2] [3].

The leadership team includes experience from major tech and fintech players, with angel investors and advisors hailing from **Uni Cards, Oyo, Flipkart, and a16z** [2].

## Funding History & Runway

Dodo Payments is currently in the **Pre-Seed** stage, having raised capital to validate its thesis and build initial infrastructure.

| Date | Round | Amount | Lead Investors | Notable Angel Investors | Use of Funds |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Mar 2025** | Pre-Seed | **$1.1 Million** | Antler, 9Unicorns (now 100Unicorns), Venture Catalysts | Nitin Gupta (Uni Cards), Maninder Gulati (ex-Oyo), Preethi Kasireddy (ex-a16z), Raymond Russell (ex-Boom Supersonic) | • Enhance tech infra (billing, fraud modules)<br>• Establish local payment rails in 30+ countries (EU, UK, SEA, Brazil)<br>• Expand team |

[2] [3] [4]

**Strategic Implication:** A $1.1M pre-seed is relatively small for a company attempting to build a global financial infrastructure and distribution network. This suggests the company will need to raise a larger Seed or Series A round within 12-18 months (by mid-to-late 2026) to sustain its ambitious roadmap of local entity setup in 30 countries.

## Target Market & Tailwinds

Dodo is positioning itself at the intersection of two massive growth trends: the rise of Indian SaaS and the globalization of instant payment rails.

### 1. The Indian SaaS Explosion
The Indian SaaS ecosystem is maturing rapidly, with revenue projected to reach **$20–$25 billion by 2030** [5]. Companies like Zoho, Freshworks, and Postman have paved the way, but a new wave of AI-native startups is launching "global-from-day-one." These companies need an MoR that understands their specific context (e.g., RBI regulations) while enabling global sales.

### 2. Cross-Border Payment Complexity
Cross-border B2B e-commerce exports from Asia reached **$1.8 trillion in 2025** [6]. However, payment failures remain a critical bottleneck. Traditional card networks often have high decline rates for cross-border transactions from emerging markets due to strict 2FA mandates (like India's AFA). By offering local rails like UPI, Dodo addresses a specific pain point where "Indian exporters linked to unified payment interface portals cut receipt times from 14 days to 36 hours" [6].

### 3. The Rise of UPI
UPI is expected to account for **two out of three digital merchant payments in India by 2026** [5]. Dodo's support for UPI allows global merchants to sell *into* India effectively, a market many Western SaaS companies struggle to monetize due to card friction.

## Competitive Landscape

Dodo competes in a crowded market of Merchant of Record providers, but differentiates through its emerging market focus.

### MoR Competitors

| Competitor | Primary Focus | Key Strengths | Weaknesses vs. Dodo |
| :--- | :--- | :--- | :--- |
| **Paddle** | SaaS & Software | Market leader, deep subscription logic, robust tax compliance [7] [8]. | Can be expensive; less focus on emerging market local rails like UPI. |
| **FastSpring** | B2B Software | Legacy player, strong enterprise support, flexible contract terms [9] [10]. | Older tech stack; perceived as less "developer-native." |
| **Lemon Squeezy** | Creators & Indie | Excellent UI/UX, easy setup for digital products [10]. | Lacks depth for complex B2B SaaS billing; primarily for smaller creators. |
| **PayPro Global** | SaaS & Software | Strong global tax handling, 24/7 support, hybrid pricing models [11]. | Brand awareness lower in developer communities compared to Stripe/Paddle. |

### The "DIY" Alternative
Many startups choose to build their own stack using **Stripe** (Payment Processor) + **Sphere/Anrok** (Tax Automation).
* **Pros:** Lower fees (~3% + flat tax fee vs. 5-8% for MoR), more control over checkout [10].
* **Cons:** Merchant retains liability for tax and fraud; requires maintaining local entities or registrations in every jurisdiction.

**Dodo's Wedge:** Dodo is the "Paddle for India/Emerging Markets." While Paddle and Stripe dominate the US/EU corridors, Dodo wins where local payment methods (UPI, Pix, local wallets) are the difference between a sale and a decline.

## Traction & Performance

As of March 2026, Dodo Payments has reported early but significant traction metrics:

* **Merchant Count:** Onboarded **1,000+ merchants** across 30 countries [2] [3].
* **Growth Targets:** Aims to scale to **10,000+ merchants** globally by the end of 2025 [2].
* **Transaction Success:** Claims success rates exceeding **90%**, significantly higher than the industry average for cross-border transactions involving emerging markets [2].
* **Global Reach:** Supports customers in **30 countries** with plans to establish local payment rails in key regions including the EU, UK, Southeast Asia, Middle East, Brazil, and Australia [2].

## Recent News & Launches (Last 12 Months)

* **March 2025:** Raised **$1.1M Pre-Seed funding** led by Antler, 100Unicorns, and Venture Catalysts [4] [2].
* **Product Launch:** Introduced **Sentra**, an AI agent for billing integration, and an **MCP Server** for connecting AI models to payment infrastructure [1].
* **Expansion:** Announced plans to support **100+ currencies and 300+ local payment methods** in the coming year [3].

## Regulatory & Execution Risks

While the opportunity is large, the risks are significant for a pre-seed fintech company.

### 1. Compliance Complexity
Acting as an MoR requires flawless execution on tax remittance. If Dodo fails to remit VAT correctly in a jurisdiction like the EU or UK, the liability falls on them, but the reputational damage hits the merchant.
* **Risk:** Managing tax rules for 200+ jurisdictions with a small team is an immense operational challenge.
* **Diligence Item:** Customers should verify Dodo's tax registration certificates in key markets (e.g., OSS registration in EU).

### 2. "Mile Wide, Inch Deep" Product
Dodo's website advertises a massive surface area: payments, billing, tax, fraud, *and* distribution (storefronts, affiliate programs) [1].
* **Risk:** Legacy MoRs like Digital River failed partly because they became "bloated" and inflexible [12]. Dodo risks spreading its engineering resources too thin, resulting in shallow features (e.g., basic subscription logic that can't handle complex enterprise upgrades/downgrades).

### 3. Counterparty Risk
As an MoR, Dodo holds merchant funds before payout.
* **Risk:** For a pre-seed startup, financial stability is critical. If the company faces liquidity issues or banking partner shutdowns, merchant funds could be frozen.
* **Mitigation:** Merchants should demand clear payout SLAs (e.g., T+2 or T+7) and understand the underlying banking partners.

## Technology Stack Deep Dive

Dodo's technical approach is modern and API-first, designed to abstract the complexity of underlying financial rails.

* **Integration:** Offers "adapters" that wrap the SDK initialization, allowing integration in minimal lines of code for frameworks like Next.js and Remix [1].
* **AI/ML Layer:** Uses machine learning for fraud detection and merchant underwriting [3]. The "Sentra" agent suggests a move toward "infrastructure-as-code" where billing logic is generated rather than manually implemented.
* **Mobile:** Provides React Native SDKs optimized for iOS and Android, enabling in-app payment experiences [1].
* **Frontend:** Offers a "Billing SDK" with pre-built components (pricing cards, subscription dashboards) built for React and ShadCN, reducing frontend development time [1].

## Recommendations

### For Prospective Customers (SaaS/AI Startups)
* **Pilot for Emerging Markets:** If you are a US/EU company seeing high decline rates from India/SEA, use Dodo as a secondary gateway/MoR specifically for those regions to test uplift.
* **Verify Payouts:** Start with small volumes to verify payout reliability and timing before migrating 100% of traffic.
* **Check Feature Depth:** Ensure their subscription logic handles your specific edge cases (proration, grandfathering, usage-based overages) which are often missing in early-stage platforms.

### For Investors
* **Thesis Validation:** The "India-first MoR" is a defensible wedge given the complexity of RBI regulations and UPI integration.
* **Milestone Tracking:** Key metrics to watch are the successful setup of local entities in the target 30 countries (proving operational competence) and the "Net Revenue Retention" of early cohorts to ensure the platform scales with merchants.

### For Partners
* **Integration:** Dev shops and agencies building for Indian SaaS founders should evaluate Dodo as a default stack component, replacing the complex "Stripe + Atlas + Tax Tool" setup.

## References

1. *Fetched web page*. https://dodopayments.com/
2. *Fetched web page*. https://economictimes.indiatimes.com/tech/funding/cross-border-payments-startup-dodo-payments-raises-1-1-million-pre-seed-funding/articleshow/118551842.cms?from=mdr
3. *Dodo Payments Raises $1.1M to Expand Cross-Border Payment Solutions | Financial IT*. https://financialit.net/news/fundraising-news/dodo-payments-raises-11m-expand-cross-border-payment-solutions
4. *Dodo Digest: We raised $1.1M from Top Global Investors! | Dodo Payments*. https://dodopayments.com/blogs/newsletter-march3rd
5. *The Rise of SaaS in India 2023 - Bessemer Venture Partners*. https://www.bvp.com/atlas/rise-of-saas-in-india-2023
6. *Cross Border Payments Market Size, Competitive Landscape, Trends 2031*. https://www.mordorintelligence.com/industry-reports/cross-border-payments-market
7. *The world needs MoR | Paddle*. https://mor.paddle.com/
8. *Paddle MoR: Everything you need to know*. https://www.paddle.com/paddle-101
9. *Merchant of Record - FastSpring  *. https://fastspring.com/merchant-of-record/
10. *Merchant of Record: Pros, Cons, Options*. https://www.getsphere.com/blog/merchant-of-record
11. *Merchant of Record (MOR) Solution for SaaS and Software*. https://payproglobal.com/products/merchant-of-record/
12. *Why the Old Merchant of Record Model No Longer Works*. https://medium.com/@WithReach/the-end-of-an-era-why-the-old-merchant-of-record-model-no-longer-works-a75ff85420d3
