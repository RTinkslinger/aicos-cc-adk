INSERT INTO util.enrichment_staging (company_id, content) VALUES
(147, 'Deck insights from Notion AI on {use “@now”}: ---
Intro conversation with Founder on {use “@now”}: 
Attendees from DeVC:: 
Notes:: 
Scoring (can be copied for multiple people): Spiky Score [Table] EO/FMF/Thesis/Price Score ---
De-brief (if any): 
Follow-up conversation with Founder on {use “@now”}: 
Attendees from DeVC:: 
Notes:: 
De-brief (if any): ---
De-brief (if any): 
Next conversation with Founder on {use “@now”}: ---
Attendees from DeVC:: 
Z47 Conversation with Founder on {use “@now”}: 
Notes:: 
Attendees:: [Table]
Notes:: '),
(148, 'Evaluation Plan + Key Questions to answer: 1. What does the company do? 1. Do we (DeVC/Z47) have a thesis on this space? 1. What are the top 3 questions to diligence? 1. Who has piped this company to us? What are their views? 1. What do refs say about the founder? 1. What''s the DeVC team views? 1. What are the Collective signals? 1. Why is this company likely to be special? 1. Who can help? Experts / Venture Partners? 1. Deal dynamics? Potential deal to do? ---
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
(149, 'About the Company: - ExtraaEdge provides a full-stack marketing and sales SaaS platform for the education industry, leveraging predictive analytics, automation, and AI-driven tools to improve student acquisition and recruitment processes. - They are targeting educational institutions such as universities, test prep organizations, overseas study consultants, and coaching centers. - Annual Recurring Revenue (ARR): $2M (2023-24) and has grown 3.2x ARR since 2022. - They have 276 global education brands, including universities and mid-market players with the following split - Enterprise (23%), Mid-Market (15%), SMB (62%). - The core offerings are 1) predictive enrolment engine with 83% accuracy using proprietary LLMs and ML models, 2) automated CRM, lead nurturing, ROI trackers, and centralized communication tools, 3) GenAI-powered co-pilots for sales teams and prospective students to enhance conversion rates - They are well reviewed and testimonials indicate improved application rates by 22% and increased conversions for remote counseling teams by 18%, making it a trusted partner in education recruitment. - They are currently selling in MENA, UK, Europe and India Founders - Abhishek Ballabh (CEO) - Data Science and B2B SaaS expert with a background in AI and ML. - ExtraaEdge – ’18 - now - OnDeck – Founder Fellowship ’22 - SaaSBoomi – SGx W20 - Instructional Design Head – MindTickle ’13-15 - Software Architech – HSBC ‘09-13 - Sushil Mundada (COO) - 15+ years in product engineerin...'),
(151, 'AI notes:: Anirudh, founder of Faff, presented their personal assistant service to potential investors from DVC. Faff aims to democratize access to personal assistants through a combination of human operators and AI automation. Founder Background - Anirudh graduated from IIT Bombay in 2022 (Chemical Engineering) - Worked at Facebook AI Research (FAIR) in London on reducing AI hallucinations - Met co-founder Het Patel at an Entrepreneur First hackathon - Raised $125K from Entrepreneur First in December Business Model & Metrics - Personal assistant service targeting tasks not covered by specialized apps - Users send requests via WhatsApp to a Relationship Manager who assigns tasks to "Faffers" - 182 current users paying ₹2,000/month - Top users average 5 tasks per week - Target demographic: 25-35 year olds with ~₹40 LPA income - Most common tasks: digital tasks (web check-ins, Uber booking), finding local services, and sourcing local products Operations & Economics - Relationship Manager assigns tasks to Faffers (task executors) - Currently paying Faffers ₹50K/month, planning to reduce to ₹30K with better SOPs - Each Faffer currently handles ~12 tasks/day - Negative unit economics with ₹2K gross margin burn per customer - Payments handled through user wallet or direct payment by users Automation Strategy - 6140% of voice workflow already automated (restaurant reservations, pharmacy calls) -  4114/*-92w34r5t678Goal to increase Faffer productivity from 12 to 50+ tasks per day - C...'),
(153, 'AI notes: Jigar, a former Goldman Sachs risk analyst, presented his startup which is building an AI-powered analytics platform for asset managers. The meeting covered product strategy, market positioning, and fundraising plans. Background and Experience - Worked at Goldman Sachs (2016-2020) in Risk Informatics team - Used machine learning and AI for firm-wide risk management - Developed systems to analyze 50 scenarios across 2 million positions - Previously worked in market risk for Asia Special Situations Group - Focused on ensuring no FX or interest rate risk in emerging markets deals Product Vision - Creating AI-powered risk and factor analysis for fundamental equity investors - Key workflow integration: morning portfolio review meetings - Generates reports analyzing what moved the portfolio yesterday - Creates customized factor models with real-world explanations - Not positioning as "selling alpha generation" (strategic approach) - Integrating with data sources including Polymarket, Google News, and Alpha Vantage Target Market - Fundamental asset managers with under $100B AUM - Focus on firms without large quant teams (80% of market currently underserved) - Initial beachhead: firms with 2-3 quant people who need supplemental capabilities - Already working with design partners like Marcellus, Arga, GCM, and Grosvenor Business Potential - Current market: similar services generate $800M revenue with only 10% AUM penetration - Aladdin (competitor) generates $1B in revenue wi...')
ON CONFLICT (company_id) DO UPDATE SET content = EXCLUDED.content;