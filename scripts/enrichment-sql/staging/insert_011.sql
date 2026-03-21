INSERT INTO util.enrichment_staging (company_id, content) VALUES
(124, 'Evaluation Plan + Key Questions to answer: 1. What does the company do? 1. Do we (DeVC/Z47) have a thesis on this space? 1. What are the top 3 questions to diligence? 1. Who has piped this company to us? What are their views? 1. What do refs say about the founder? 1. What''s the DeVC team views? 1. What are the Collective signals? 1. Why is this company likely to be special? 1. Who can help? Experts / Venture Partners? 1. Deal dynamics? Potential deal to do? ---
Deck insights from Notion AI on {use “@now”}: ---
Intro conversation with Founder on {use “@now”}: 
Attendees from DeVC:: 
Notes:: 
Scoring (can be copied for multiple people): Spiky Score [Table] EO/FMF/Thesis/Price Score [Table]
De-brief (if any): ---
Follow-up conversation with Founder on {use “@now”}: 
Attendees from DeVC:: 
Notes:: 
De-brief (if any): ---
Next conversation with Founder on {use “@now”}: 
Attendees from DeVC:: 
Notes:: 
De-brief (if any): ---
Z47 Conversation with Founder on {use “@now”}: 
Attendees:: 
Notes:: '),
(127, 'Prep 2026-03-19T21:50:00.000+05:30: Docura Health — AI-native med-legal platform that automates medical record review, chronologies, and report drafting for workers'' compensation cases Founders: 1. Akhil Sachdev (Founder & CEO) — linkedin.com/in/akhil-sachdev Market: - Market: US workers'' comp = $60B industry; every claim requires multi-thousand-page record review - ICP: IME/QME evaluators, claim adjusters, insurers, legal teams - Product ships: QME, IME, AME, P&S, Supplemental report templates; AMA-compliant impairment ratings (5th & 6th Ed); AI-generated first drafts from uploaded records Prep: - Introduce DeVC & Z47 Healthcare IT portfolio - His prev employment was at Commure - Cash going in view:
Key Qs: - How did you land up at Commure from Siff AI & Rivian? What part of stack at Commure were you working on? - Wedge? - What does this lead to? - Why & when start this company? - Early POCs & proof points - GTM - how? - Onboarding friction - Solution depth - Funding - Comps
Ref on Akhil from Shubhan (Answers AI CoFo) 2026-03-19T23:28:00.000+05:30: 1. I’ve known him since I was a first year student, we lived together for 1.5 years 1. Akhil worked at Salesforce, Athelas and was very passionate about this pain point so he quit Athelas before raising venture and as a solo founder 1. I remember friends telling him that’s a hard move but he backed himself and I’m not sure about his exact numbers but he went at it solo for 6 months until his traction and product was great. He did ...'),
(128, 'RM notes: 1. CoFo Thakur 1. Friday 1. Dad is HAC contractor 1. Built donatioj app for NGO 1. 4th year - dropped out 1. Built AI scraper on Antler 1. No one cares about how SAP configured → Only care about how pocess works 1. Went after companies with COE teams focused on SAP | $50M to $500M 1. Case study: $3bn conglomerate (?) 1. SAP BDP partner - iPAS (?) 1. Top SAP partners 1. SAP AEs are partnering via back door 1. Mark Ken - SAP North America - is his advisor 1. Prev VP of Cloud Implementation at Deloitte - in pipeline (?) 1. Pipeline of $2M 1. Fundraise 1. Pricing 1. Lookin gto get non-YC operators on cap table ||
RM Reflections: Maybe for Collective Top Up | FF, Spiky = 1 | meeting was a downer | believe Collective Top-Up here is the best  approach | Cash is best to comment on founder comp v/s Ressl AI & Sookti AI: ++ Do see strategic thinking here - built advisory network, working on talent pipeline, warming up SAP network for co-branded GTM ++ Seems like a person who will compound fast ++ Has sold micro SaaS products via acquire.com called Friday to Springworks || acqui-hire type scenario ++ Thinking about GTM right way; tagging along with SAP AEs to do co-GTM ++ Certainly outside-in founder || aware of his peers ?? Decided to pursue “boring & unsexy” business ?? Worried that he is an FF who is NOT coachable despite asking for coaching & help ?? Worried that he is the self destruct / creative genius type FF who can implode if things don’t work His demo: [Link: https:/...'),
(130, 'Intro conversation with Founder on {use “@now”}: 
Attendees from DeVC:: 
Notes:: 
Scoring (can be copied for multiple people): Spiky Score [Table] EO/FMF/Thesis/Price Score [Table]
De-brief (if any): ---
Follow-up conversation with Founder on {use “@now”}: 
Attendees from DeVC:: 
Notes:: 
De-brief (if any): ---
Next conversation with Founder on {use “@now”}: 
Attendees from DeVC:: 
Notes:: 
De-brief (if any): ---'),
(131, 'Notes from Z47 Consumer team on 2024-04-17: Views DG: WM; should pass to DeVC EF: 2, FMF: 5, COB: 4, Thesis: 7, TAM: 5, Traction: ?, Pricing: ? + Reasonably outside in and understands the consumer + Decent FMF which shows in thesis + Some product IP edge + Strong thesis with a differentiated GTM ? Limited India B2C TAM ? Did not see any spike to justify US or India B2B sales plan ? Pre-revenue with no proof of product ? IF founder Do believe someone senior will build in this space, hence should follow developments Founder: Abhishek Sahu Background - BE (Information Science) @ BNM Bangalore (2019) - Product manager @Ultrahuman (2,5 years), Software engineer @Zomato (1 year) Personal/professional journey Venture Problem  statement Product - Trackers Competition GTM Learnings from Ultrahuman - Success on crowdfunding platforms like Kickstarter - enables word of mouth - QVC is also a great channel in US TG - 30-50 folks who have problems sleeping and also have the most disposable income Current product stage - Prototype done - and have identified vendors as well Unit economics - 500 dollar discount to 8sleep and hence a $1799 costing Vision - Need nearable tracking and not wearable since you can pack only so many trackers in one ring - Nearables help you surpass that Current product capability - Temperature control though the hub - Can change mattress temperature as well and ambient temperature via smart ACs - Will add air quality, humidification etc - There is some research on n...')
ON CONFLICT (company_id) DO UPDATE SET content = EXCLUDED.content;