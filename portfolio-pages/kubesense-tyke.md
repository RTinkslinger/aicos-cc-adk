---
company: Kubesense (Tyke)
notion_page_id: 988c9617-6cde-4744-8a0b-b336b9c25830
source: portfolio_db
fetched: 2026-03-20
---

**Table of contents**

---

## Update Checkin: 2025-01-20 

Attendees: @Aakash 

Key is raising capital. Company has limtied runway 

have told them to now raise 1 at 10M post SAFE. Go wide and keep lapping up capital. 

Overall: Tech product is quality, but the poor selling continues to be a hurdle. Should consider a tuck in with one of the Devops cos. Eg Amnic. 

### **Capital Raise Strategy Discussion**

Mon, 20 Jan 25

**Current Traction & Revenue**

- Currently at ~60k ARR

- Recent customer wins:

- Battery Smart (24k ARR)

- Club (15k ARR)

- Climpty (12k ARR)

- All customers are on cloud deployments

**Pipeline Overview**

- Total pipeline of ~400k in active deals including:

- Jupiter Money (converting from Datadog, 2.2M current spend)

- Super Money (100k+ potential, in final stages)

- Chargebee (100k+ potential, POC completed)

- ReliaQuest US (300k potential, currently spending 2.8M on Datadog)

- Other significant opportunities: Airmeet (40k), Credgenics (36k)

**Product & Value Proposition**

- Clear product-market fit emerging for:

- High observability spenders

- Companies requiring private cloud/on-prem solutions

- Financial services and healthcare verticals

- Key differentiators:

- Agent-driven capabilities

- Fast data processing with minimal resources

- Access to 70% of critical data (logs, metrics, traces)

**Fundraising Plans**

- Current runway until March

- Planning $1M raise on SAFE notes

- Target valuation: $10M

- Focus on pre-seed VCs in both US and India

- Previous discussions with Silicon Valley investors (not committed)

**Action Items**

- Send pitch deck to Aakash

- Need introductions to:

- Unicorns

- Specific leadership contacts (details to be shared via WhatsApp)

- Begin fundraising outreach to pre-seed VCs

- Focus on parallel execution of revenue growth and fundraising

---

Chat with meeting transcript: [https://notes.granola.ai/p/40e2de9d-b402-4612-bdda-d3b35f4d163e](https://notes.granola.ai/p/40e2de9d-b402-4612-bdda-d3b35f4d163e)



## Update Checkin: 2024-05-07 

### Attendees: @Aakash 

- Good progress on the pivot to ebpf based observability play 

- Product has taken good shape for kubernetes (now also shipping docker) 

- Early customer traction seems to be there (should validate pull and do customer chats in June) 

- Need to help him with GTM : Kuldeep, Arvind, Aswini, Soumitra (?) 

- Didn’t capture burn and runway. Need to 

- Have teed up with him that we should be running GTM review and analysis at monthly cadence. Let’s get that setup. cc: @Anonymous @Rahul Mathur 



**Notes** 

**Chargebee**

Deployment in UAT

Gets in to paid contract

Want to replace datadog first

That’s the target to replace

Splunk later

Splunk is on Prem : yearly licensed .. 300K + 80-100K on infra

Datadog spending 650K last year .. brought it down to 200K

We quoted 120K (10K p.m.) ..that’s the target the Devops has

- Long term we price by number of nodes



<< Cred has 700K on data dog and 700K on coralogix >> 



We can ingest 10K TPS now. Less than 16GB RAM >> Did this for juspay deployment

We got rid of kafka and built internal queues

Even as request RPS goes up our resource requirement doesn’t go up

Logs and metrics custoemrs are getting from other sources, we were working on traces only

But juspay came back and said do logs and metrics too

Currently product support Kubernetes | Now gonna build for docker

Agent is already compatible with docker

Instrumentation is simple and quick.

Support all sorts of DBs and protocols

Have done load test with one billion records per day

JusPay

Should be deploying this week

They are on old contract which was $12K per year would have to be redone

---



## Update Checkin : 2024-07-23 

### Attendees : @Aakash 



5 Customers in UAT | 2 go in to prod soon 

Clickhouse DB + Victoria metrics for time series data

Airtel evaluating dynatrace (traditional agents not ebpf) vs Kubesense 

M2P been in production for 2 weeks. But they haven’t signed contracts. They made a proposal to even acquire and build this product internally and market the product as M2P product 

Cloud version comes out in September 

Chargebee is waiting for AWS fargate support 

12 months runway 

Untill next july 

cash in bank :  200K in + 100K yet to receive 

18K monthly cost base + 4-5 K it goes up 





---

## Update Checkin : 2024-11-06 

### Attendees : @Aakash & @Anonymous 



We are doing a lot of demos but many of these are not Kubernetes but on EC2 

M2P was in production but then we stopped; they wanted to acquire us

Devrev and Crayon data were also offering to acquire us.

Thought we should generate some meaningful revenue before taking these conversations to detail 



Citymall is moving and Chargebee is moving along; Chargebee’s infra guy was a blocker → they have themselves reduce 650K costs to 200K and hence cost of the product was not a driver



Chargebee wanted us to build observability on a customer level so that they can identify that amongst all the errors which are ones to focus on. This problem seems relevant for all other customers as well

CB wants to expose this to CX success teams; so far they can only wait customer to come back

This product will be ready by Nov end 



Speaking to a couple of fintechs and AZ teams to meet their customers

Citymall is currently 2K per month; they spend 50K on AWS and any such product for them will be $20K


3-6 month priority 

- 500K by April 

- dont have any marketing support right now

- We need to be at a point that we have a 50-60K ARR and a path to 500K



I have runway till 4 months and we have 2 angels coming in helping us stretch to 6 months 

Burn > 20K per month



- [x] Connects needed from us when EC2 is ready @Anonymous Divyanshi 2024-12-03T09:00:00.000+05:30 



![](https://prod-files-secure.s3.us-west-2.amazonaws.com/b21975bb-aebf-48e3-8c44-1573c4404129/26fc6201-d26f-4732-a639-49ccce1c2df8/Screenshot_2024-11-06_at_5.23.21_PM.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4665AGVSXLC%2F20260320%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260320T102120Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEGgaCXVzLXdlc3QtMiJIMEYCIQC8AZnQL3iRO%2BURNF4gW2nCPk%2FhcQVsiEyIr%2FdCi3citwIhAK6r%2FeSsEY8mvupNT10JfwRPj%2F71baGli5e5Zc2IoGGqKv8DCDEQABoMNjM3NDIzMTgzODA1IgzLx9cC1QoUIiPvmHUq3AOXtsnzxX1y5N4DBQcpAJTtOnO2lVfU4Yb5n1y3muhRs2dnCeMo3E9rEIu%2F7PMbyJR6O%2BsrwPyGpEsGFZ8LvPqaigpx157mCGujwW7R2BkatNfAjRDvsqFgwU2CHt98Z4p85CD0C2rU04GJKK7kK0VAc8B0NtcMU202kVSgxjK%2FdHeAsbfYCiXGekluNEvln29SsB%2F5vQOYxBY1zxNjRSY5pUcjJmxJlrfhcC6mtx6GRbiN8d9GMzOjqIOGAfYQ7TFtpFUAa%2BKY9pGx5AwjMXyV%2BMmVddu1nubeJINnZunsxDhzJZPMLd9Ba5dSdti4k9ntaTmNUu1JfSmqjeS7Bw2EUxLIA7SjStejCyFxJieLcrjAU241Hs84DVz12ZZT23ifz9JfFLuGsNnSeozQee%2BUGuayzkl9pceH8VFlpMFIPbwUJ%2B0jsqSSeb05deiQAOuMw%2BmzZwZjHIM4Q4Wp%2FKzp4VNxEH0wflbTmUoHultDViNmT%2BSEVcWzurTvv%2Bu%2BNcr93lJMHPdvnKNK8etPvwHFyFa5C5hCHnwvuHwnJaBa42S3xXnYiYoIqajlOjGLhUMQTPkHiUORQb9SzBD1LIBLFsGhTF7ykxN8mn6y9AG%2B%2FkLU2Y9%2BedMWujkutTDD%2F%2FPNBjqkAdFA8p0wqU2IcMO8VWXwlZQy%2ByK7JtOrh4zKV0NtkSxYyxPQRgHHUwV9ABWqjYlgSV9GjzB8wWnvD7dv8a2NCYr3OaV5lZErZSQCUWUnx5X2en98T4954EPVY%2Bev0e%2BIO5sFHbz9fKHDWDMrzpB0rugJwSCJBnN06NRPtBKDsn6dKpgslbn3Lgal%2Fl0PKrbnrguxaid9oMXPegriR3obrBYA18BB&X-Amz-Signature=6485aded4a727a90abc15e097cfc9a3d382404e5347e4053633cc5c6839292f1&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

---

## Update shared 2025-03-26 



Dear Friends & Supporters,

Two weeks ago, one of the potential acquirers (whom we declined) asked me a pointed question:*“In such a crowded space, why do you believe you can win? Why not join forces with a bigger player and collectively aim for leadership position?”*
My response was just three words: **“Hunger to win.”**
Yes, *hunger to win*—because everything else follows.
We are a small but intensely driven team. What we have built in just 14 months would have taken most companies 4-5 years and 50x more capital. Few SaaS startups have the courage to aim for $100K accounts within their first few months. We are on track to reach $500K ARR with less than $300K in burn—a rare thing where 5x burn for the first million is the norm.
[KubeSense](https://kubesense.ai/) is redefining what it means to build and sell enterprise software from India to the world. And our hunger? It’s limitless—truly limitless. We’re not here for small wins; **we’re here for a billion-dollar revenue journey**. That’s the benchmark. That’s the mission.
This is not a typical investor update. Today, for the first time, I am sharing my vision with absolute clarity—our ambition to make this a reality in the coming years.
When I decided to shut down our previous product, [tyke.ai](http://tyke.ai/), it wasn’t because we failed—it was because we weren’t thinking big enough. We weren’t building something that could generate a billion dollars in revenue. That product had no clear path to scaling beyond $5-10M in revenue, and reaching a billion-dollar milestone was impossible. So, we made the hard decision to move on.

Letting go of something we had built for over 18 months and starting from scratch was brutal. But we had to do it—and we had to do it even faster this time. And we did.
We never compromised for short-term convenience. We pushed ourselves into uncharted territory—mastering eBPF, our own ClickHouse variant, Rust, and deep telemetry expertise—all to lay the right foundation for a petabyte-scale product that guarantees enterprise-grade performance, security and reliability.
None of this would have been possible without your constant support and belief in us. Many of you have provided invaluable guidance on the tech and product side, and for that, I am truly grateful. 
Below are the detailed updates. Please feel free to ask me anything—anytime. Thank you for being part of this journey.

### Product Update:

We’re happy to announce that KubeSense is now generally available!

Unlike traditional SaaS products, KubeSense is an observability platform designed for large-scale enterprises, focusing on $100K+ deals from day one. This meant we had to support massive scale from the start and ensure that at least 90% of the most critical features—compared to competitors like Datadog and New Relic—were available from launch. And we made sure KubeSense had all those features. Find the attached feature comparison document for more details.

What we’ve built in just 14 months with a nine-member team would have taken years for others. Even our competitors acknowledge this. The result? Four acquisition offers—all of which we politely declined. Why? Because our ambitions are far bigger than a $5M or $10M exit.

Here’s a [**short product demo**](https://www.youtube.com/watch?v=o_XTV4qab5U&t=1s)—check it out and help us spread the word!

We’re also [available on the Amazon Marketplace](https://aws.amazon.com/marketplace/pp/prodview-zardfty4p7axw?sr=0-1&ref_=beagle&applicationId=AWSMPContessa) and in the process of listing on GCP and Azure.

### **Business Update**

First and most importantly, we are on track to reach profitability by May/June and plan to operate at break-even for a couple of quarters before accelerating growth.

Currently, five customers are in production, each generating over 1.5TB of telemetry data per day—a strong testament to our product’s maturity and the team’s capabilities.

On the revenue front, we are currently under $100K ARR, with multiple high-value deals (Jupiter, Chargebee, Credgenics) in the procurement and contracting stage. We expect to reach $500K ARR by May/June 2025.

Additionally, we are gearing up to start PoCs with several large prospects, including Macy’s, T-Mobile, Informatica, Super Money and HighRadius.

### **Team Update**

We are still a nine-member team, and while we’re facing challenges in supporting new customers, we are not in a rush to hire for the sake of it. Instead, we are carefully scouting for ten hungry, ambitious young individuals to join us over the next two quarters—before transitioning to a more traditional hiring approach.

### **Funding & Runway Update**

We are default alive and not dependent on external funding for survival. However, we may consider raising a large round in Q3 (July–Sep) once we hit $1M ARR, to fuel our next phase of growth.

### **Rejected Acquisition Offers**

Finally, on the acquisition offers—we’ve received interest from four companies: DevRev, M2P Fintech, Crayon Data, and Grafana. I didn’t even take the time to assess their seriousness or explore the discussions in detail because the answer was clear: we are here to build something massive.

We’re not just in observability anymore—the opportunity ahead is far bigger when combined with the potential of AgentSRE. Our strategy to become the system of record for telemetry and capture the traditional telemetry market will position us perfectly to lead the AgentSRE evolution.

Unlike incumbents, our tech stack is already built to support AgentSRE use cases. Additionally, our role as the system of record (SOR) for telemetry gives us a distinct advantage over pure AgentSRE startups that rely on external integrations to process terabytes of telemetry data—a limitation we do not have.

### **Finally**

The **TAM is projected to reach $150B by 2035**, and we are laser-focused on building a **$1B revenue company** at the intersection of Observability and AgentSRE.

Thank you for your continued belief and support. This is just the beginning. **Onward and upward!**

---



## Update call 2025-06-13 

 

### Current Revenue & Customer Status

- Chargebee status:

- Initial contract signed for $2,500/month ($30k annual)

- Expected to expand to $12,500/month ($150k annual) by year-end/October

- Currently running parallel with Datadog due to technical dependencies

- Won due to B2B monitoring capabilities for prioritizing high-paying customers

### Major Pipeline Opportunities

- Informatica:

- Signed $10k/month contract for next 5 months starting July

- Potential to expand to $100k+ next year

- Currently starting with one team, gradual rollout planned

- Automation Anywhere:

- $25k contract for 4 months

- Partnership includes building database monitoring feature

- Looking to replace Datadog completely

- High Radius:

- POC completed

- $50k contract pending procurement call

### Key Challenges & Learnings

- Jupiter Money deal challenges:

- Price war with Corologix led to reducing quote from $120k to $75k

- Lost deal due to leadership turnover (4 decision makers left)

- Learning: Need stronger differentiation beyond pricing

- Technical challenges with Chargebee:

- Sampling issues with current solution

- Need to build function profiling feature

- Running parallel systems increasing costs temporarily



### Data shared on WA

KubeSense: Next-Gen Observability with AgentSRE


A high-performance, AI-powered observability platform that unifies APM, Logging, Infra Monitoring, and AgentSRE capabilities, delivering 10x more value at one-third the cost of legacy solutions.

Built for petabyte-scale, KubeSense has been replacing Datadog, New Relic, and Splunk for large startups and enterprises like Chargebee, Emeritus, Informatica, Automation Anywhere and more.



Here’s a quick demo video: [https://youtu.be/o_XTV4qab5U](https://youtu.be/o_XTV4qab5U)



Relevant Differentiators

Price Capping and Free Usage in Lower Environments – We guarantee approximately 70% savings on your current observability spend, along with free usage for lower environments. For enterprise contracts, we offer price capping, ensuring that your telemetry costs will not exceed the capped prices for the next 5 years.

Performance Efficiency – Zero-code instrumentation, 5x higher compression, 40x faster queries, with 3x lower infra footprint.



Seller, Merchant or Product-Level Monitoring – Provides merchant-specific or product-specific insights with performance metrics and error analytics.

Advanced Stack and AgentSRE – Built on the most advanced tech stack in the market, capable of supporting AgentSRE use cases, and includes built-in AgentSRE features such as AI RCA, natural language querying over telemetry, and more.



---



### Update 2025-12-17 

Has hit 250K ARR
11 people team (all engg)
Running purely from cash flows
Will get to 1M ARR over next 7-8 months
ACVs are in 30K range, will go up to 60-70K. Confident that will sign a few 100K contracts by Feb
Resilient guy and has just kept things going
Product is not a step jump on alternates and mostly sells on being cheaper
Have guided him to keep compounding
Told him unless step jump product, GTM won’t accelerate.
He’ll focus on India market and get to 2-2.5 M ARR by end of 26
Nothing for us to do here
