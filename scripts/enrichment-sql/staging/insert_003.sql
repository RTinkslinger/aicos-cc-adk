INSERT INTO util.enrichment_staging (company_id, content) VALUES
(54, 'Notes from ICICI Bank Event: 1. Founder: 1. Investors: 1. Funding history 1. $2M round - just started the fundraise 1. Credgencies - Collections, Backspace - Payments disputes 1. MENA has 15 in pipeline 1. Live with ICICI bank as a customer 1. Cofo in this business is an eng from Cognizant who worked on similar custom tech for banks 1. The ICICI Bank contract itself can be $1M 1. Possible to charge both the issuer and the acquiring Bank for the same service 1. Dispute resolution module for each card network and each payment type can be charged as a separate product 1. Possible to build a network for payment dispute reso
Notes from convo with Praveen 2024-09-23: Attendees: @Rahul Mathur and @Aakash 1. Post GFF 1. Journey 1. Swan De-watering systems 1. Inspiration 1. Backspace 1. Incorporated in 2020 1. Traction & pipeline 1. ICICI learnings 1. Team 1. Funding 1. Action items'),
(55, 'Intro conversation with Founder on {use “@now”}: 
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
(59, 'Notes:: BillMe acquisition • BillMe serves as a product hook o Price point is not a factor o Net revenue isn''t the focus here • Current acquisition rate: 2K stores monthly o 80% from new enterprise sales (not MSMEs) o 99% through cross-selling by other teams • Acquisition completed in September 2023 o Initially structured as Cash + Equity o Converted to all-cash deal due to FOCC restrictions • Targets by Sept 2025 o 10x growth in stores and transactions o Systems implementation complete New venture (initial concept) • Consumer focus o Premium artisanal cookie QSR o High-end positioning o Social media-driven marketing o Aiming to be India''s Krumble o Future expansion into other products • Break-even at 40 orders daily o No on-site cooking required • Store network collaboration • BillMe integration advantages o Access to target group data and locations o Cookie data cross-selling potential with McD • Target audience: Social media-savvy women (Instagram-focused) • Financial metrics o INR 350 Average Order Value o INR 200 Average Selling Price • Product specifications o Premium quality cookies o Dense, cheesecake-like texture o 2-3 day shelf life • Launch location: Bangalore o Tech-savvy population o Affordable rent (INR 250/sqft) o Mumbai launch later when brand is established • Projected financials o Monthly revenue: INR 8-12L o Daily target: 100 orders × INR 350 = INR 10L monthly
Deck insights from Notion AI on {use “@now”}: ---'),
(60, 'Evaluation Plan + Key Questions to answer: 1. What does the company do? 1. Do we (DeVC/Z47) have a thesis on this space? 1. What are the top 3 questions to diligence? 1. Who has piped this company to us? What are their views? 1. What do refs say about the founder? 1. What''s the DeVC team views? 1. What are the Collective signals? 1. Why is this company likely to be special? 1. Who can help? Experts / Venture Partners? 1. Deal dynamics? Potential deal to do? ---
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
(61, 'Notes from convo with @Anonymous, @Anonymous + Z47 Consumer: My take on him - spikey 0.5-1 on hustle and picking business getting to some answers that work - ⁠however very low on consumer insights - ⁠has very low commercial depth. He had thought through most of our questions things at a high level but lacked depth in almost everything. - ⁠maybe+ overall as a guy to back but we will need to fund his journey to maturity and depth. Will burn through a lot of money - Family background - Business model and thinking has evolved a lot Mohit: Spikey 1 + Spike is clarity of thought CV: Spikey 1 + Had a lot of depth for a guy not from the industry ? Will blow through money because he''s naïve DC ? Doubts on his execution skills Kishan: Spikey 0.5 -1 DG: Maybe +/SM for DeVC | Maybe - for Z47 (want to track for next round)Spikey 0.5 (tending to 1) + Very first principled and strategic - one of the sharpest articulation on vertical QC + High IQ guy with a clear chip on the shoulder + Entrepreneurial - has had a history of always wanting to start up + Real H&H - very rare to find entrepreneurs this young doing this grit (likely well off also - so pure ambition) + Structured - everything had an excel/notion + analytical + ballsy guy - openly asked if we are just collecting data ? What is the execution spike - a lot of it is just thought right now - why hasn’t he added more brands? ? Does he run from trend to trend? Started from Blue-collar to Bookmarks to QC ? No history of achievement - if ...')
ON CONFLICT (company_id) DO UPDATE SET content = EXCLUDED.content;