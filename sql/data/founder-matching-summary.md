# Founder Matching Data Summary

**Generated:** 2026-03-20
**Status:** READ-ONLY extraction — no data modified

## Data Sources

| Source | Count | Notes |
|--------|-------|-------|
| Portfolio (Notion export) | 142 companies | People stored as Notion page IDs in relation fields |
| Network DB (Postgres) | 528 people | Names + roles, linked via notion_page_id |
| Companies DB (Postgres) | 545 companies | Links network people to companies |

## Coverage Summary

| Metric | Value |
|--------|-------|
| Total portfolio companies | 142 |
| Companies with any people linked | 131 |
| Companies with resolved people names | 99 |
| Unique people IDs in portfolio relations | 42 |
| Resolved to network names | 35 |
| Unresolved IDs | 7 |

## Key People in Portfolio Relations (Resolved)

These are the 35 network people referenced in portfolio "Led by?", "Sourcing Attribution", "Participation Attribution", or "Venture Partner?" fields:

| Person | Notion Page ID | Companies Referenced In |
|--------|---------------|----------------------|
| Aakrit Vaish  | `28b6b732-70f...` | Boba Bhai, Digital Paani, GoCredit (f.k.a. UniPe), Puch AI (f.k.a. TurboML), Quash Bugs +5 more |
| Abhishek Goyal | `6c22055b-2f5...` | iBind Systems, Mom’s Made, Navo (f.k.a. BizUp), ofScale, OnCare +3 more |
| Alex Peter | `81bd723e-240...` | Seeds Finance |
| Amit Lakhotia | `a20aebfe-38d...` | Coffeee, ElecTrade, HealthCred |
| Amiya Pathak | `12fa0563-116...` | Ananant Systems, Isler, Terafac |
| Anand Lalwani | `22529bcc-b6f...` | Nixo |
| Arjun Rao | `02be8c39-cf7...` | Inspecity, Morphing Machines, Puch AI (f.k.a. TurboML), Uravu Labs, VyomIC (f.k.a. AeroDome) |
| Arvind Parthiban | `81cced8f-8f6...` | ExtraaEdge, Highperformr AI, Mantys |
| Ashish Goel | `a45949ca-f4a...` | CarbonStrong |
| Ashwini Asokan | `92f41ba3-ee0...` | Aurva, Coind, Mantys, Qwik Build (f.k.a Snowmountain) |
| Chakradhar Gade | `6218c280-04e...` | Tractor Factory |
| Chirag Taneja | `24faafdb-023...` | Crest, Kilrr |
| Dhyanesh Shah | `728577ce-38d...` | Prosparity |
| Harshil Mathur | `20f0040a-64d...` | Boba Bhai, Finsire, Multiwoven |
| Jitendra Gupta | `a154cbcb-d12...` | PowerEdge |
| Karthik Ramamoorthy | `12729bcc-b6f...` | Kintsugi |
| Lizzie Chapman | `41a1efe7-79a...` | Unifize |
| Madhusudanan R | `afc7dd34-2d6...` | Riverline (f.k.a Recontact) |
| Miten Sampat | `59f7e10b-1ed...` | Boba Bhai, Digital Paani, GoCredit (f.k.a. UniPe), Puch AI (f.k.a. TurboML), Quash Bugs +5 more |
| Mohit Sadaani | `aef4eb66-f90...` | Bidso, Digital Paani, Felicity, Navo (f.k.a. BizUp), Stupa Sports Analytics |
| Nitin Gupta (Uni) | `f82f042e-be6...` | Ambak, Cybrilla, GoCredit (f.k.a. UniPe), HealthCred, Obvious Finance +2 more |
| Nitin Jain | `6f1cce7b-dd3...` | Tejas (f.k.a Patcorn) |
| Prabhu  | `dd2841c3-1e0...` | Coffeee |
| Prashant Malik | `aee20857-6d6...` | Marrfa, Spheron Network |
| Ramakant Sharma | `0b0a5b0f-133...` | Apptile, BiteSpeed, Eight Networks, GlamPlus, Insta Astro +5 more |
| Revant Bhate | `a8b01e15-01c...` | Bidso, Crest, Hotelzify, Kilrr, Klaar +4 more |
| Rohit MA | `dbdffe0b-bd7...` | Bidso, Fabriclore, Terra |
| Sameer Pittalwala | `03e8eef0-6ed...` | Felicity, Spybird, Ziffi Chess |
| Sanat Rao | `2615d4e0-7b1...` | Qwik Build (f.k.a Snowmountain) |
| Shashank Kumar | `8de32d6a-1d2...` | Boba Bhai, Finsire, Multiwoven |
| Soumitra Sharma | `f413b573-a24...` | Confido Health, Flytbase, NuPort, Revenoid |
| Sri Ganesan  | `3cfe07e8-387...` | Pinegap |
| Suhail Sameer | `21a8c52e-54c...` | Cleevo |
| Vasant Sridhar | `3979f9de-fd8...` | Tejas (f.k.a Patcorn) |
| Vishesh Rajaram | `5d79d566-bd2...` | Inspecity, Morphing Machines, Puch AI (f.k.a. TurboML), Uravu Labs, VyomIC (f.k.a. AeroDome) |

## Unresolved People IDs (7)

These IDs appear in portfolio relations but do not match any network DB entry:

- `12029bcc-b6fc-80a5-b895-ca7f92f67f4c` — referenced by: Kubesense (Tyke)
- `12229bcc-b6fc-8063-ade5-e9a8fa24b2c4` — referenced by: Crackle
- `12629bcc-b6fc-80e1-b7e1-f3e6a1326b24` — referenced by: Boost Robotics
- `17529bcc-b6fc-8001-9480-ed5a5634dce9` — referenced by: Ballisto AgriTech (f.k.a. Orbit Farming)
- `2d7e074a-5166-4ae5-80cf-7a8dddb0d6ca` — referenced by: Ballisto AgriTech (f.k.a. Orbit Farming), DreamSleep, Flytbase, HealthCred, Terafac, Turnover
- `60a061e2-3f9f-4862-a6fa-94f92a0a1c74` — referenced by: Felicity, Ziffi Chess
- `f7a625c0-a21c-4b2f-a02d-d1e4a3e300b5` — referenced by: Lucio AI

## Per-Company People Summary

### Alter AI (2 people)
- Kevan Dodhia (Co-founder) <companies_db>
- Srikar Dandamuraju <companies_db>

### Ambak (4 people)
- Nitin Gupta (Uni) (Co-Founder CEO) [led_by, sourcing] <portfolio>
- Raghuveer Malik (Co-Founder CEO) <companies_db>
- Rameshwar Gupta (Co-Founder CTO) <companies_db>
- Rashi Garg (Co-Founder COO) <companies_db>

### Ananant Systems (1 people)
- Amiya Pathak (Co-Founder CEO) [led_by, sourcing] <portfolio>

### Answers.ai (4 people)
- Brianna Wilburn <companies_db>
- Mamoun Debbagh <companies_db>
- Shubhan Dua (Co-Founder CTO) <companies_db>
- Siddhant Satapath <companies_db>

### Apptile (1 people)
- Ramakant Sharma (Co-Founder CEO) [led_by, sourcing, venture_partner] <portfolio>

### AskMyGuru (2 people)
- Krishna Vedula (Co-Founder CEO) <companies_db>
- Vivek Sadamate (Co-Founder CEO) <companies_db>

### Atica (no linked people)

### AuraML (no linked people)

### Aurva (3 people)
- Apurv Garg (Co-Founder CEO) <companies_db>
- Ashwini Asokan (Founder) [led_by, sourcing] <portfolio>
- Krishna Bagadia (Co-Founder CTO) <companies_db>

### Autosana (2 people)
- Jason Steinberg (Co-founder) <companies_db>
- Yuvan Sundrani (Co-founder) <companies_db>

### Ballisto AgriTech (f.k.a. Orbit Farming) (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### BetterPlace fka Mindforest (1 people)
- [unresolved] <companies_db>

### Bidso (3 people)
- Mohit Sadaani (VC Partner) [led_by, participation] <portfolio>
- Revant Bhate (Co-Founder CEO) [led_by, participation] <portfolio>
- Rohit MA (VC Partner) [venture_partner] <portfolio>

### BiteSpeed (1 people)
- Ramakant Sharma (Co-Founder CEO) [led_by, sourcing, venture_partner] <portfolio>

### Blockfenders (2 people)
- Niranjan Ingale <companies_db>
- Viraj Phanse (Co-Founder CEO) <companies_db>

### Boba Bhai (5 people)
- Aakrit Vaish  (Co-Founder CEO) [participation] <portfolio>
- Dhruv Kohli (Co-Founder CEO) <companies_db>
- Harshil Mathur (Co-Founder CEO) [led_by, sourcing] <portfolio>
- Miten Sampat (CXO) [participation] <portfolio>
- Shashank Kumar (Co-Founder CTO) [led_by, sourcing] <portfolio>

### Boost Robotics (2 people)
- Hans Kumar (Co-Founder CTO) <companies_db>
- Hardik Singh (Co-Founder CEO) <companies_db>

### Boxpay (2 people)
- Puneet Singh (Co-Founder CEO) <companies_db>
- Shobhit Mehra (Co-Founder COO) <companies_db>

### Caddy (2 people)
- Connor Waslo (Founder) <companies_db>
- Rajiv Sancheti (Founder) <companies_db>

### CarbonStrong (3 people)
- Ashish Goel (Co-Founder CEO) [led_by, sourcing] <portfolio>
- Harsh Jain (Carbonstrong) (Co-Founder CEO) <companies_db>
- Vikramaditya Singh (Co-Founder COO) <companies_db>

### Cleevo (3 people)
- Karan Shah (Co-Founder COO) <companies_db>
- Mayank Jain (Co-Founder CEO) <companies_db>
- Suhail Sameer [led_by, sourcing] <portfolio>

### CodeAnt (no linked people)

### Coffeee (2 people)
- Amit Lakhotia (Founder) [led_by, sourcing] <portfolio>
- Prabhu  (Co-Founder CTO) [participation] <portfolio>

### Coind (1 people)
- Ashwini Asokan (Founder) [led_by, sourcing] <portfolio>

### Confido Health (1 people)
- Soumitra Sharma (VC Partner) [led_by, sourcing] <portfolio>

### Crackle (3 people)
- Harsh Mittal (Co-Founder CEO) <companies_db>
- Jaivir Nagi (Co-Founder CEO) <companies_db>
- Shashank Dudeja (Co-Founder CTO) <companies_db>

### Crest (3 people)
- Chirag Taneja (Co-Founder CEO) [led_by, sourcing] <portfolio>
- Revant Bhate (Co-Founder CEO) [participation] <portfolio>
- Zuhaib Khan (Co-Founder CEO) <companies_db>

### Cybrilla (3 people)
- Anchal Jajodia (Co-Founder CEO) <companies_db>
- Nitin Gupta (Uni) (Co-Founder CEO) [led_by, participation] <portfolio>
- Satish Perala (Co-Founder CTO) <companies_db>

### Digital Paani (3 people)
- Aakrit Vaish  (Co-Founder CEO) [led_by, participation] <portfolio>
- Miten Sampat (CXO) [led_by, participation] <portfolio>
- Mohit Sadaani (VC Partner) [led_by, participation] <portfolio>

### Dodo Payments (no linked people)

### DreamSleep (1 people)
- Abhishek Sahu (Co-Founder CEO) <companies_db>

### Eight Networks (1 people)
- Ramakant Sharma (Co-Founder CEO) [led_by, participation] <portfolio>

### ElecTrade (3 people)
- Amit Lakhotia (Founder) [led_by, sourcing] <portfolio>
- Milind Srivastava (Co-Founder CTO) <companies_db>
- Rishikesh Ranjan (Co-Founder CEO) <companies_db>

### Emomee (2 people)
- Pooja Jauhari (Co-Founder COO) <companies_db>
- Varun Duggirala (Co-Founder CEO) <companies_db>

### ExtraaEdge (3 people)
- Abhishek Ballabh (Co-Founder CEO) <companies_db>
- Arvind Parthiban (Co-Founder CEO) [sourcing] <portfolio>
- Sushil Mundada (Co-Founder COO) <companies_db>

### Fabriclore (3 people)
- Anupam Arya (Co-Founder COO) <companies_db>
- Rohit MA (VC Partner) [led_by, sourcing] <portfolio>
- Vijay Sharma (Co-Founder CEO) <companies_db>

### Felicity (3 people)
- Anurag Choudhary <companies_db>
- Mohit Sadaani (VC Partner) [participation] <portfolio>
- Sameer Pittalwala (CXO) [led_by, participation] <portfolio>

### Finsire (2 people)
- Harshil Mathur (Co-Founder CEO) [led_by, sourcing] <portfolio>
- Shashank Kumar (Co-Founder CTO) [led_by, sourcing] <portfolio>

### Fliq (f.k.a. EthosX) (2 people)
- Deepanshu (Co-Founder CEO) <companies_db>
- Smit Patoliya (Co-Founder CTO) <companies_db>

### Flytbase (1 people)
- Soumitra Sharma (VC Partner) [led_by, sourcing] <portfolio>

### Fondant (2 people)
- Jehoshaph Akshay Chandran (Co-Founder CEO) <companies_db>
- Parav Nagarsheth <companies_db>

### Frizzle (2 people)
- Abhay Gupta (Co-Founder CEO) <companies_db>
- Shyam Sai (Co-Founder CTO) <companies_db>

### GameRamp (2 people)
- Sashank Vandrangi (Co-Founder CEO) <companies_db>
- Vivek Ramachandran (Co-Founder CEO) <companies_db>

### Gimi Michi (2 people)
- Akhil Kumar (Co-founder) <companies_db>
- Nishank Goyal (Co-founder) <companies_db>

### GlamPlus (1 people)
- Ramakant Sharma (Co-Founder CEO) [led_by, sourcing] <portfolio>

### Gloroots (3 people)
- Abhirup Nath (Co-Founder CEO) <companies_db>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### GoCredit (f.k.a. UniPe) (5 people)
- Aakrit Vaish  (Co-Founder CEO) [led_by, participation] <portfolio>
- Abhijit Verma (Co-Founder CEO) <companies_db>
- Anupam Acharya <companies_db>
- Miten Sampat (CXO) [led_by, sourcing, participation] <portfolio>
- Nitin Gupta (Uni) (Co-Founder CEO) [led_by, participation] <portfolio>

### Grexa (2 people)
- Ashutosh Kumar (Founder) <companies_db>
- Ayush Varshney (Founder) <companies_db>

### Grvt (3 people)
- Aaron Ong (Co-Founder CTO) <companies_db>
- Hong Gyu Yea (Co-Founder CEO) <companies_db>
- Matthew Quek (Co-Founder COO) <companies_db>

### HealthCred (4 people)
- Amit Lakhotia (Founder) [participation] <portfolio>
- Arpit Jangir (Co-Founder COO) <companies_db>
- Nitin Gupta (Uni) (Co-Founder CEO) [led_by, sourcing] <portfolio>
- Shrey Jain (Co-Founder CEO) <companies_db>

### Hexo AI (3 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Highperformr AI (3 people)
- Arvind Parthiban (Co-Founder CEO) [led_by, sourcing, venture_partner] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Hotelzify (3 people)
- Revant Bhate (Co-Founder CEO) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Inspecity (4 people)
- Arjun Rao (VC Partner) [led_by, sourcing] <portfolio>
- Vishesh Rajaram (VC Partner) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Insta Astro (2 people)
- Ramakant Sharma (Co-Founder CEO) [led_by, sourcing, venture_partner] <portfolio>
- [unresolved] <companies_db>

### Intract (no linked people)

### Isler (2 people)
- Amiya Pathak (Co-Founder CEO) [participation] <portfolio>
- Ramakant Sharma (Co-Founder CEO) [led_by, sourcing] <portfolio>

### Kairos Computer (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Kavana AI (Two Four Labs) (3 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Kilrr (3 people)
- Chirag Taneja (Co-Founder CEO) [led_by, sourcing] <portfolio>
- Revant Bhate (Co-Founder CEO) [led_by, sourcing, venture_partner] <portfolio>
- [unresolved] <companies_db>

### Kintsugi (3 people)
- Karthik Ramamoorthy (Senior Vice President) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Klaar (1 people)
- Revant Bhate (Co-Founder CEO) [led_by, participation] <portfolio>

### Klaire (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Kreo (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Kubesense (Tyke) (no linked people)

### Lane (1 people)
- [unresolved] <companies_db>

### Legend of Toys (3 people)
- Ramakant Sharma (Co-Founder CEO) [led_by, sourcing, venture_partner] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Lucio AI (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Mantys (3 people)
- Arvind Parthiban (Co-Founder CEO) [led_by, sourcing, venture_partner] <portfolio>
- Ashwini Asokan (Founder) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>

### Manufacture AI (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Marrfa (1 people)
- Prashant Malik (VC Partner) [led_by, participation] <portfolio>

### Material Depot (3 people)
- Ramakant Sharma (Co-Founder CEO) [led_by, participation] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Measure AI (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Mello (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### MiniMines (no linked people)

### Modus Secure (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Mom’s Made (2 people)
- Abhishek Goyal (Co-Founder CEO) [led_by] <portfolio>
- [unresolved] <companies_db>

### Morphing Machines (5 people)
- Arjun Rao (VC Partner) [led_by, sourcing] <portfolio>
- Vishesh Rajaram (VC Partner) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Multiwoven (5 people)
- Harshil Mathur (Co-Founder CEO) [led_by, sourcing] <portfolio>
- Nagendra Dhanakeerthi (CXO) <companies_db>
- Shashank Kumar (Co-Founder CTO) [led_by, sourcing] <portfolio>
- Sujoy Golan (CXO) <companies_db>
- [unresolved] <companies_db>

### Navo (f.k.a. BizUp) (2 people)
- Abhishek Goyal (Co-Founder CEO) [led_by, participation] <portfolio>
- Mohit Sadaani (VC Partner) [led_by, participation] <portfolio>

### Nimo Planet (1 people)
- [unresolved] <companies_db>

### Nixo (3 people)
- Anand Lalwani (Co-founder) [led_by, sourcing, participation] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### NuPort (3 people)
- Soumitra Sharma (VC Partner) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Obvious Finance (4 people)
- Nitin Gupta (Uni) (Co-Founder CEO) [participation] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Offline (1 people)
- Revant Bhate (Co-Founder CEO) [led_by] <portfolio>

### OhSoGo (3 people)
- Aashish Benjamin (Co-Founder CEO) <companies_db>
- Revant Bhate (Co-Founder CEO) [led_by, sourcing, venture_partner] <portfolio>
- [unresolved] <companies_db>

### OnCare (3 people)
- Abhishek Goyal (Co-Founder CEO) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### One Impression (no linked people)

### Orange Slice (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Pinegap (3 people)
- Sri Ganesan  [led_by, participation] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Polytrade (1 people)
- Revant Bhate (Co-Founder CEO) [participation] <portfolio>

### Potpie (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### PowerEdge (4 people)
- Abhishek Gupta (Co-Founder CEO) <companies_db>
- Jitendra Gupta (Co-Founder CEO) [led_by, sourcing] <portfolio>
- Nitin Gupta (Uni) (Co-Founder CEO) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>

### PowerUp (2 people)
- Nitin Gupta (Uni) (Co-Founder CEO) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>

### Prosparity (4 people)
- Abhishek Goyal (Co-Founder CEO) [participation] <portfolio>
- Dhyanesh Shah (Co-Founder COO) [led_by, participation] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Puch AI (f.k.a. TurboML) (6 people)
- Aakrit Vaish  (Co-Founder CEO) [led_by, sourcing] <portfolio>
- Arjun Rao (VC Partner) [led_by, sourcing] <portfolio>
- Miten Sampat (CXO) [led_by, sourcing] <portfolio>
- Vishesh Rajaram (VC Partner) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Quash Bugs (6 people)
- Aakrit Vaish  (Co-Founder CEO) [led_by, sourcing, venture_partner] <portfolio>
- Abhishek Goyal (Co-Founder CEO) [participation] <portfolio>
- Miten Sampat (CXO) [led_by, sourcing, venture_partner] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Quivly (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Qwik Build (f.k.a Snowmountain) (2 people)
- Ashwini Asokan (Founder) [venture_partner] <portfolio>
- Sanat Rao [participation] <portfolio>

### Rakshan AI (3 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### RapidClaims (5 people)
- Aakrit Vaish  (Co-Founder CEO) [led_by, sourcing] <portfolio>
- Abhinay Vyas (Co-Founder COO) <companies_db>
- Miten Sampat (CXO) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Realfast (no linked people)

### Renderwolf (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### ReplyAll (f.k.a. PRBT) (1 people)
- [unresolved] <companies_db>

### Revenoid (2 people)
- Soumitra Sharma (VC Partner) [sourcing, participation] <portfolio>
- [unresolved] <companies_db>

### Revspot (6 people)
- Aakrit Vaish  (Co-Founder CEO) [participation] <portfolio>
- Miten Sampat (CXO) [participation] <portfolio>
- Ramakant Sharma (Co-Founder CEO) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Rhym (no linked people)

### Riverline (f.k.a Recontact) (4 people)
- Abhishek Gupta (Co-Founder COO) <companies_db>
- Madhusudanan R (Co-Founder CEO) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### SalesChat (4 people)
- Aakrit Vaish  (Co-Founder CEO) [led_by, sourcing] <portfolio>
- Miten Sampat (CXO) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Seeds Finance (1 people)
- Alex Peter (Co-Founder CEO) [led_by, sourcing] <portfolio>

### Skydda (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Smallest AI (2 people)
- Aakrit Vaish  (Co-Founder CEO) [participation] <portfolio>
- Miten Sampat (CXO) [participation] <portfolio>

### Solar Ladder (3 people)
- Abhishek Pillai (Co-Founder COO) <companies_db>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Soulside (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Spheron Network (1 people)
- Prashant Malik (VC Partner) [participation] <portfolio>

### Spybird (3 people)
- Abhishek Kamdar (Co-Founder CEO) <companies_db>
- Sameer Pittalwala (CXO) [sourcing] <portfolio>
- [unresolved] <companies_db>

### Spydra (3 people)
- Ramakant Sharma (Co-Founder CEO) [sourcing, venture_partner] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Stance Health (f.k.a HealthFlex) (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Stellon Labs (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Step Security (no linked people)

### Stupa Sports Analytics (1 people)
- Mohit Sadaani (VC Partner) [led_by, sourcing] <portfolio>

### Supernova (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### SuprSend (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Tejas (f.k.a Patcorn) (5 people)
- Nitin Jain (Co-Founder COO) [participation] <portfolio>
- Vasant Sridhar (Co-Founder CEO) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Terafac (2 people)
- Amiya Pathak (Co-Founder CEO) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>

### Terra (4 people)
- Rohit MA (VC Partner) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Terractive (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Tesora AI (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Tractor Factory (2 people)
- Chakradhar Gade (Co-Founder CEO) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>

### Turnover (no linked people)

### UGX (3 people)
- Abhishek Kumar (Co-Founder CEO) <companies_db>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### Unifize (1 people)
- Lizzie Chapman (Co-Founder CEO) [led_by] <portfolio>

### Uravu Labs (5 people)
- Arjun Rao (VC Partner) [led_by, sourcing] <portfolio>
- Vishesh Rajaram (VC Partner) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### VoiceBit (3 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### VyomIC (f.k.a. AeroDome) (5 people)
- Anurag Patil (Co-Founder CTO) <companies_db>
- Arjun Rao (VC Partner) [sourcing] <portfolio>
- Lokesh Kabdal (Co-Founder CEO) <companies_db>
- Vibhor Jain (Co-founder) <companies_db>
- Vishesh Rajaram (VC Partner) [sourcing] <portfolio>

### Workatoms (2 people)
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### YOYO AI (fka Trimpixel) (no linked people)

### Ziffi Chess (4 people)
- Abhishek Goyal (Co-Founder CEO) [participation] <portfolio>
- Sameer Pittalwala (CXO) [participation] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### ZuAI (4 people)
- Aakrit Vaish  (Co-Founder CEO) [led_by, sourcing] <portfolio>
- Miten Sampat (CXO) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### cocreate (2 people)
- Archish Arun (Co-founder) <companies_db>
- Tamish Pulappadi (Co-founder) <companies_db>

### iBind Systems (3 people)
- Abhishek Goyal (Co-Founder CEO) [participation] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>

### ofScale (5 people)
- Abhishek Goyal (Co-Founder CEO) [led_by, sourcing] <portfolio>
- Revant Bhate (Co-Founder CEO) [led_by, sourcing] <portfolio>
- [unresolved] <companies_db>
- [unresolved] <companies_db>
- [unresolved] <companies_db>


## Data Architecture Notes

1. **Portfolio DB** stores people as Notion page IDs in relation fields (`Led by?`, `Sourcing Attribution`, etc.)
   - These IDs point to Network DB pages
   - Only 10 rows synced to Postgres; full data from Notion export (142 entries)

2. **Companies DB** links people via `network_ids` and `current_people_ids` arrays
   - Many network IDs here are unresolved (people not yet in network table)
   - This is the primary path for founder<->company matching

3. **Network DB** has 528 people with names, roles, and company links
   - `current_company_ids` field links back to companies

4. **Matching approach:** Two paths to find people for a portfolio company:
   - Path A: Portfolio → `Led by?`/`Sourcing Attribution` → Network DB (35 resolved / 7 unresolved)
   - Path B: Portfolio → `Company Name` → Companies DB → `network_ids`/`current_people_ids` → Network DB
   
5. **Gap:** Many companies in Companies DB have network_ids that don't resolve to network table entries
