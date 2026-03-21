INSERT INTO util.enrichment_staging (company_id, content) VALUES
(261, 'Conversation 2024-09-14T20:30:00.000+05:30 with @Rahul Mathur: Attendees: @Rahul Mathur 1. Progress - Product 1. Has worked with Vivek to now make the product OS agnostic 1. And, the product is now cloud vendor agnostic 1. Still not ready for MM deployment 1. Progress - Business 1. Is going to start pilots with: 1. Avey TV 1. Unfiltered podcast —> found out about them them from RM’s LinkedIn post 1. About Avey TV 1. Has a full time resource who sets up all the equipment 1. Paying ~₹5L per month for the same 1. Have ~100 editors in the Avey TV business and ~30 in the YAS (YouTube As a Service) business 1. ICP 1. Might be agencies which do gaming, video editing or designing 1. The Buyer at the agency is the Producer / right hand person of the creator 1. Looking to charge ₹5K to ₹10K per seat therefore this becomes a MM Sales motion 1. Progress - Team & Talent 1. Vivek has come onboard full time to work as an engineer 1. Is going to get ~5% equity which vests over 4 year with 1 year cliff 1. Taking home ~₹50K per month 1. Has taken most of the technical burden off Advait 1. Working with the founder of Fold Money & a friend on design aspect 1. Progress - Supply 1. Has realized that cannot work with GCP, Azure etc since they are too large 1. Working with an Indore based cloud provider called Neev Cloud 1. Promoter of the business is “paying it forward” — connected via LinkedIn 1. Have met in-person 1. Also got Shashank from MagicAPI to meet the NeevCloud owner 1. Qs which he asked...'),
(263, '**Founder Backgrounds**: - **Mohan (CTO)**: IIT Guwahati CSE grad (2018-2022), worked at Sprinklr for 2.5 years with quick promotions. Enjoyed lab courses in college. Built a YouTube channel with 21K subscribers. - **Sudhanshu (CEO)**: IIT Guwahati CSE & Maths grad. Worked at Jupiter on ODS (on-demand salary product), Kirana Club, and Amex. Won internal Amex Shark Tank competition (₹1L prize). Enjoyed topology and probability courses. - **Sushant (Designer)**: From North Karnataka, IIT Guwahati grad. Mental math champion from 4th standard. Chess player (peak 1400-1500 rating). Previously at Flipkart where he designed home services and built chatbots that impressed Kalyan Krishnamurthy. **Matiks Journey** - Started as a side project while founders were employed elsewhere - Initially created a web-based platform where users could generate links to play math games with friends - Acquired 1.5K users in first week through link sharing on WhatsApp - Started GTM through LinkedIn, later expanded to Twitter with good results - Signed term sheet with InfoEdge in September 2024 (₹3 crore on ₹17 crore post) - Currently have 5 full-time team members plus 5-6 interns **Product & Metrics** - **User Flow**: Onboarding → score setting (45% completion) → game formats - **Most Popular Format**: Online duels (60% of activity) - **Other Formats**: Fastest finger first (20%), daily puzzles, KenKen puzzles - **Engagement**: KenKen puzzles average 5 mins on weekdays, 50 mins on weekends - **Referral...'),
(264, 'Scoring (can be copied for multiple people): **Spiky Score** **EO/FMF/Thesis/Price Score**
Intro conversation with Founder on {use “@now”}: 
Attendees from DeVC:: 
Notes:: 
De-brief (if any): ---
Follow-up conversation with Founder on {use “@now”}: 
Attendees from DeVC:: 
Notes:: 
De-brief (if any): ---
Next conversation with Founder on {use “@now”}: 
Attendees from DeVC:: 
Notes:: 
De-brief (if any): ---'),
(265, 'Evaluation Plan + Key Questions to answer: 1. **What does the company do?** 1. 1. **Do we (DeVC/Z47) have a thesis on this space?** 1. 1. **What are the top 3 questions to diligence?** 1. 1. **Who has piped this company to us? What are their views?** 1. 1. **What do refs say about the founder?** 1. 1. **What''s the DeVC team views?** 1. 1. **What are the Collective signals?** 1. 1. **Why is this company likely to be special?** 1. 1. **Who can help? Experts / Venture Partners?** 1. 1. **Deal dynamics? Potential deal to do?** 1. ---
Scoring (can be copied for multiple people): **Spiky Score** **EO/FMF/Thesis/Price Score**
Deck insights from Notion AI on {use “@now”}: ---
Intro conversation with Founder on {use “@now”}: 
Attendees from DeVC:: 
Notes:: 
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
Notes:: 
De-brief (if any): '),
(266, 'Scoring (can be copied for multiple people): **Spiky Score** **EO/FMF/Thesis/Price Score**
Intro conversation with Founder on {use “@now”}: 
Attendees from DeVC:: 
Notes:: 
De-brief (if any): ---
Follow-up conversation with Founder on {use “@now”}: 
Attendees from DeVC:: 
Notes:: 
De-brief (if any): ---
Next conversation with Founder on {use “@now”}: 
Attendees from DeVC:: 
Notes:: 
De-brief (if any): ---')
ON CONFLICT (company_id) DO UPDATE SET content = EXCLUDED.content;