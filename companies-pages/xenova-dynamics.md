# Xenova Dynamics

**Table of contents (click to navigate)**
---
## Inbound via Ankit Sanghvi (Riverline AI) - 2026-02-25
Source: Warm intro from Ankit Sanghvi (ankit@riverline.ai) on Feb 18, 2026


Ankit's intro context: "Gurasees is a student at IITM, founding a company in drone-detection tech."

### Xenova Dynamics — deck summary (Counter-UAV)
<!-- file block -->
**What they do:** Xenova is building an integrated counter‑UAV system focused on *detecting and managing drone swarms*, with a software “command OS” layer on top of sensor/radar hardware.
### Problem
- Drone detection is hard.
- Handling *hundreds of drones (swarms)* is harder, especially in cluttered airspace.

### Solution (two-part)
- **Detect:** AI-powered, multi-sensor, drone-focused radar system to spot, track, and manage swarms.
- **Analyze / Command OS:** “Drone traffic OS” that:
  - Analyzes swarm dynamics plus terrain, elevation, and wind.
  - Suggests operator decision plans (Operator AI).
  - Aggregates multiple information sources and produces summaries/findings (AI analyst).

### Product / system architecture (as presented)
- **Separate transmitter and receivers** in a multi-radar setup.
- Claims **~10 km** coverage for critical infrastructure surveillance.
- Positioned as a *swarm-native* detection + sensor fusion + decision/orchestration layer.

### Market (their numbers)
- **TAM:** $30B
- **SAM (30%):** $9.2B
- **SOM (10% of SAM):** $1B
- **27% CAGR** (stated)

### “Why now”
- Counter‑UAV becoming a regulatory/operational need (airports).
- Low-cost drones create disruption, surveillance, and payload threats.
- Critical infrastructure (oil, nuclear, strategic facilities) exposed to sabotage/espionage and coordinated incursions.

### Competition (their framing)
They mention players focused on:
- **Hard kill interceptors** (e.g., Perseus, Jatayu).
- **OS / soft kill (jamming) + interceptors** (e.g., Armory, Prandtl).
- **Integrated domes / capture drones / interceptor agility** (e.g., Indrajaal, Aerix).
**Gap they claim:** no unified, swarm-native command software combining drone-focused detection, sensor fusion, swarm analysis, and engagement orchestration with strong operator usability.

### Progress & roadmap
- **Operator OS:** “largely complete,” AI analysis/decision modules built; end-to-end integration underway.
- **Interceptor prototypes:** in field deployment testing.
- Next steps:
  - **Next 3 months:** field trials with sensors + integrated software.
  - **Next 9 months:** start AI-driven drone-focused radar design; upgrade OS; deliver MVP and start contracts.
### Use cases / GTM
- **Government tenders** (indigenous anti-drone systems for defense).
- **Partnerships** with larger primes/integrators.
- **Subsystem sales** (radar modules, tracking turrets, guidance units, sensor fusion engines).
- **Civil infrastructure** adaptation for security agencies and critical assets.
- Active engagement with airport/airspace authorities, MoD + allied ministries, primes/integrators, and academic mentors.
### Team / advisors (highlighted)
They cite engagement with defense and academic experts, including an IIT Madras professor mentor and retired IAF personnel in product/validation conversations.


## Meeting 2026-02-26T11:10:00.000+05:30 


### RM reflections - WM given this is a college project right now
++ Outside-In | Have studied comps to their best ability
++ Resourceful - mentors | cold calls etc
+? Some IP via IIT Madras | Professor isn’t actively involved though
?? Too young to sell
?? Not convinced about this team being the one to build the Software SI for A&D in India



### RM notes
Founder:
  1. Is there conclusive evidence of founder slope / achievement in life?
  1. How has the founder demonstrated high agency?
  1. Does the founder have critical thinking skills?
  1. Quality of team or L1s assembled by the founder?
  1. What is the founder’s clear spike (business building skill)?

Specific:
  1. **How did he meet Advisors? (ALL COLD)**
    1. *Dr. Manoj Kumar, retired wing commander, IAF*
    1. *Rahul Arora, guided missiles inspector, IAF.*
    1. *Prof K Giridhar - Mentor w/o equity*
  1. Who were juniors and seniors in Aero Club, IITM?
  1. Where did the interest in aerospace come about? 
    1. *Gurasees - NCC Air Force Wing - Pilot demo*
    1. *Zaid is from *[*Abhiyaan team*](https://www.teamabhiyaan.com/)* at IIT Madras*

Comps:
  1. Which comps are studied?
    1. *Jatayu & Indrajaal has  a 1 km detection range*
    1. *Big Bang Boom Solutions (Anti-Drone Guns) *
    1. *Armory etc is working on counter drones*
  1. Which RFPs / Tenders will you go after?
    1. *Not starting out with Defense - couldn’t get traction*
  1. What are they offering?
    1. *Interoperable OS which combines data about capability, swarm analysis*
    1. *Focusing on Dual Use*
    1. *Start w/ Delhi Airport, Oil Rigs and other sites vulnerable to drone attacks*




### AI notes

<!-- transcription block -->

    ### Action Items
    - [ ] @Rahul Mathur to follow up with founders within a day with feedback and potential introductions 
    - [ ] @Rahul Mathur to connect Gurashish and Zaid with other investors and experts better informed about commercial airport procurement 
    - [ ] Founders to consider alternative business approaches given procurement challenges 
    ### Founders' Backgrounds
    - **Gurashish** is from Chandigarh studying at IIT Madras, developed passion for aerospace through NCC Air Force training where they first piloted a plane in 10th class  
    - Part of Team Abhiyaan (IIT Madras International Rocketry Team) for 3 years, won innovation award at International Rocket Engineering Challenge in Texas for Asia's largest hybrid engine 
    - **Zaid** is from Hyderabad, runs a cooking YouTube channel with 200k subscribers that started during lockdown  
    - Both are chemical engineering students at IIT Madras who met in second year through mentorship programs and Inter-IIT competitions  
    ### Zenova's Product & Technology
    - Building multistatic radar systems for drone detection with multiple transceivers over a perimeter to localize drones and swarms  
    - Advised by Professor Giridhar from IIT Madras who has done groundbreaking research on the data fusion problem for multistatic systems  
    - Developing an interoperable software platform that integrates all sensor data, environment information, defender capabilities, and swarm analysis to provide automated course of action recommendations  
    - System aims to address limitations of legacy radars which have 4-6 meter inaccuracies - too imprecise for small drone detection  
    ### Competitive Landscape & Differentiation
    - Current players include Indrajal, Zentech, Big Bang Boom Solutions, and Jatayu focusing primarily on interception rather than detection  
    - Most solutions require manual operator control which cannot scale for fast-moving drone swarms  
    - No Indian player has built unified software architecture for automated decision-making - only Anduril's Lattice OS internationally, but unlikely to be procured by Indian defense 
    - Existing systems lack interoperability between different vendor solutions 
    ### Go-to-Market Strategy Shift
    - Started in July 2023 initially focused on building complete anti-drone interception systems for defense 
    - Pivoted away from defense procurement after realizing they lack necessary connections and it would be "probability based" without insider relationships  
    - Now targeting commercial facilities (airports, critical infrastructure) to gain traction before attempting defense contracts  
    - Strategy is to start with software integration as operating system, then potentially expand to include multistatic radar hardware  
    ### Current Customer Engagements
    - **Delhi Airport**: In discussions through GMI Group's startup program to understand current detection gaps and explore pilot deployment  
    - Airport currently has digital twin simulation but no dedicated drone detection data layer 
    - **Saudi Arabia**: In talks for pilot program, positioning as cost-effective alternative to $2-5M US/European systems  
    - Middle East market opportunity exists because they want platform solutions like US provides, not just point products 
    ### Fundraising
    - Seeking $200k seed round to build radar systems and integrate software with hardware toward MVP 
    - Have not yet applied to Campus Fund, Antler India, or Entrepreneur First accelerators  
    - Took break from fundraising after defense pivot, this is first attempt with commercial focus 
    ### Investor Concerns Raised
    - **Procurement challenges**: 12-18 month sales cycles per customer, painful systems integration work 
    - **Pricing risk**: Concern founders will accept low-ball offers (e.g. $60k/year) without understanding value-based pricing, limiting to 20-30 airport customers  
    - **Product vs services**: Risk of becoming services shop doing custom integration rather than building scalable product platform, which eliminates enterprise value   
    - **Market positioning**: Most large venture investors have already backed competing systems integrators, making fundraising difficult 
    - **Defense quality**: Even if successful in defense, it's a poor business with 270-day net working capital cycles, buyer concentration risk, and limited export potential 
    - **Round size**: $200k is at lower end for DeVC given deep tech typically takes longer and costs more than planned  
    ### Advisor Network
    - Connected with Dr. Manoj Kumar (Head of Product at HAL), Rahul Arora, and Dr. Giridhar through cold LinkedIn outreach  
    - Discussions focused on technical validation and business guidance for defense entry 
    - Advisors helped validate shift toward detection rather than interception focus 



    Where are you from? What was family like? What got you interested in Aero and I think Gurashish you have done like Aero club as well like a bunch of other people so I just love to get the story why did you and Zaid decide to partner and Zaid your version of it as well if you don't agree with Gurashish.
    Yeah, you go first.
    So, I hail from Chandigarh.
    My whole family is, my mom's a lawyer and my dad's a government engineer. So they're the typical family of get government job, get college and go through all of that stuff. And success for them is just getting a government job and getting married and having a settled life. That's-The family I hail from, of course, I am very lucky to be here. And I have had this passion for aerospace and rockets and anything indie, anything that's life to be honest.
    Just like my childhood. That has been inculcating in me since like my 10th class when I was in LCC Air Force Cadet. They took me to fly an actual plane. My first time sitting in a plane was actually when I got piloted in a training program at NCC Air Force. And that sort of got me into like Like, yes, I want to do this for my life. This is it. And that led to me getting here and here I found out about this club, this bomb team and so much stuff that goes on here.
    I got interested by of course the Aero Club and more importantly Team Abhiya Zeh which is the IIT Madras International Rocketry Team. They create rockets and go to international competitions and compete with other colleges. I've been part of that team for 3 years now. I joined them in my first year. I also did Eritrean Cup. Bye. Hello, I am represented Abhyudaya at International Rocket Engineering Challenge that was held in Texas last year June and there I won an innovation award for Asia's largest hybrid engine and also the India's first hybrid that we built as a student team.
    So that is something I'm really proud of. India in a I have been more working on drones and planes and sort of treating it as my area of my makers Just sort of explore what allWhat is going on in the domain right now, I see what I can contribute to it. I've worked on I've worked on PX4 and combat and I've been to a few, solved a few inter-IT problems statements as well. And that is sort of how me and Jay got to Nice Would you just want to continue from there?
    Yeah, sure. Give you an introduction? Yeah, sure.
    So I come from Hyderabad and So yeah, after that in my 8th and 9th class I was just interested in softwares and stuff. I used to build apps. sort of android apps, this and stuff. And then when I joined engineering, I joined a team I called up Yann, which is basicallyOkay, before that, I think you skipped a big part.
    There is something he doesn't like talking about. He in a rich class, 10. During lockdown, Oh wow, what's the channel name, sorry? It's a cooking channel. It's a cooking channel.
    The cooking channel?
    Yeah, yeah. So these guys found... I love talking about it because he is just too humble of a person.
    Got two relevance items.
    It is, it is relevance. Very nice. So, basically, These guys found a really super cool Hyderabadi food niche and just sort of built on that during the lockdown period and built up the channel to what it is today Now it's in autopilot mode and pilot is in red.
    Wow, very nice man. That is cool. I think you should tell people about that. Yeah, even though it's not. Exactly. Not company relevant but it's still nice dude. I feel it's good to have an interest like this. I cannot cook to save my ass. I am very well known to burn pizzas that you put in the oven as well right when they come straight out of the cold storage at Tesco. But very cool man and To be sure, I don't cook as well.
    I just use the kitchen to bake. That's what I used to do. My mom used to cook the whole thing and I just edit those videos and just post it on YouTube and do the stuff. Nice. Perfect. Okay. And are you all, are you all like dorm mates, roommates in college or are you all one? So I am a chemical engineer studying chemical engineering at IIT Madras and I'll just say I joined the Aapyaan team. It was a team of...
    No, no, you didn't answer the question.
    Okay, I'm answering. I'll go on to that. So I... Yeah, we basically We used to build our autonomous vehicles. Correct. After that, We went to inter-IIT, we had a problem statement related to robotics and Gurasees had something related to drones. Yeah, yeah, yeah. And also, before that, we also had like a junior's We used to mentor juniors in a way and that's how I met Gurasi. We didn't actually meet in first year, we just met in second year which is funny, we didn't even know in first year that well.
    And we just hit it off. I also love talking about rockets and and we just met up and in Inter-IT we just, okay, yeah, in Inter-IT, Hearing that, in the bus, in the bus, Grouchy proposed to me this. Okay, I'm building something. I'm building a modular rocket engine. Would you be part of this? I was like sure why not that seems cool and so We just started talking about this rocket engine, what we are doing.
    What are we going to do and this so can you mention about the yeah?
    I just like to answer your question. I felt like he didn't even answer. He lives in Chennai now like his whole family is here. He lives off campus very near to the campus. He doesn't have a hospital I live here in a hospital, I'm home with a two-part. Yeah.
    Cannot remember the top of my head and I'll it's just running in the background but very cool stuff so Let's dive into what you guys are trying to do at Zenova, right? There is a lot of activity in drones, counter drones. You saw the Adani guys being called out as a vendor for those drones that did the kamikaze strikes during Operation Sindur as well. So there's a lot of stuff that's going on. And, you know, given the fact that you're at a college which is as close to the action as possible, there are advisors, there are mentors, there are people who can tell you what's the lay of the land.
    Just talk to me a little bit about... What have you all decided to pursue with Zenova? Where do you think the opportunity is to wedge into procurement and in that process maybe tell me a bit about what you have started to build?
    Yeah, right. I'll just share the... Sure, we'll just go over the relevant slide and I think it'll be better to just have a visual. Yeah? Absolutely. I'll go over your questions one by one. Yeah. uh... They have never been so easily available. And so never anyone thought of detecting drones would be such a big issue. And basically what we are trying to do is introduce a new kind of tech into the space and along with that come in as an integrator of all the sensors specializing for drones.
    The tech that we are trying to introduce is multistatic radars. -Essentially, you have multiple transceivers over a perimeter which help in localization of one particular drone and This can be extrapolated to a swarm of drones. yeah The data problem essentially, you have all of this data from each of the trunk tables, but how do you put it together So that you find that oneYeah. Here in ITMarshanath there is a professor from KGD there and he has been working in this So he is kind of our mentor Particularly for Oostip, just this problem, and he has been dealing in the data problem and actually dealing with data, how do you the data to actually localize all the drones.
    And they have done some groundbreaking research in the field. We are very clear with them about our motive and they are also perfectly supportive.
    And Professor Giridhar is advising you guys, will you be taking some IP from him, what is the relationship with him?
    Makes sense.
    Very interesting. Okay, so that is Professor Giridhar. If I had to just jump in here for a minute, on this entire drone detection and maybe hard kill, soft kill, there are a bunch of players, right? There is Gren with Indrajal, there's Zentech. There is Jatayu and their Perseus platform that you had actually mentioned. There are a few other companies. Just if you can... Double click on where today's solutions are where the competitors might lag and i know you may not have 100 info on them for whatever reason but based on whatever you know where do you think the gap is for you to wedge in because this is a single customer to procure yes you can procure this at a brigadier level that's going to give you a crore of revenue you will probably make one crore in your third year of employment at a software company somewhere in the west right you need to get that 200 crore central which needs top down, top down means you need to wedge somewhere into defense procurement.
    How will you guys be able to get in with all these players today trying to do 10 different things?
    Okay, so I would like to answer a question in two parts. Yeah. Number one, How are we differentiating? And number two, the defense part. I would like to talk about that more. Sure. Okay the to do anything about it. That is basically what we are trying to bet on and why we are trying to increase our range is again multi-stack radar and would you like toSure, sure, Danielle.
    There's also one more company that is working on anti-drone systems called VBSM, Big Bang Boom Solutions. They make anti-drone guns. I had a meeting with them And talk about this very thing, the detection part. What they're doing currently is they have a legacy radar ASAA radar, which is the most advanced radar in missiles, detecting missiles, etc. And they're trying to tweak that to detect drones.
    Now they mention that this type of legacy radar that they are using currently, that they are deploying, It has huge inaccuracies up to 4 to 5 meters or 6 meters. When you have small drones, that inaccuracy is very fatal. Yeah. The detection part, okay, most of the companies, Zen Technologies, Indrajal, Armory, so many companies are working more on the... The intersection part, making your own drones to capture them, like Indrajal made their own nets to capture other drones.
    But I think the most important thing is how do you even detect them? That is one part, detection. The second part is, okay, you did detect it, but then how do you analyze them? Let us not talk about that bit. Because, okay, you have, let's say, you have 100 drones, you have 50 drones, something. But then they have, you know the drones that are coming now, they have swarms that are coming now, they are forming multiple formations.
    Some of them have payloads, some of them have, You know the mother drone, slave drone setup. There's multiple tactics, plays, etc. There's no unifying architecture. There's no interoperable software as well, apart from architecture. There's no interoperable software that combines all of this information together. It combines the information of the environment, it combines the information of what you have as defender capability analysis, the swarm analysis, all sorts of things.
    There's no such software that can predict all of this and also give you what to do next. Because, for example, right now, in the Indian defense context, most of the anti-drone counting US systems, they have an operator sitting in some bunk or something, Can man please try to... Intercept drones. For example, they send their own drones. They manually operate their own drones or they manually operate some sort of a gun system, etc.
    Automation in... Because these drones fly at fast speeds and they have low altitudes. They can occur anytime. They just detect all of a sudden and you don't have time. Especially when you have 20 drones, 30 drones, you can't manually have an operator operate on these systems. The course of action should not be... In a manual hands, so there should be automation here and that is what we think that is one of the biggest things.
    Okay, detection part is one. The second part is how do you manage to plan all of this together? And we don't think that any of the players right now in India is working on this. There is again, Anduril. Anduril has their own Lattice OS which they are working on. But again, it's not very specific to counter US space. But India, there's no... And Lattice will never be procured by the Indian defense. Very clear that they'll procure weapon systems from overseas, but we want to do logic and decision making software domestically.
    Right. I think that that is the insight I also received from someone decently senior in the armed forces. So this makes sense. Now, question to ask you guys is. There are lots of drone OEMs that are also coming out with their systems and whatever else. Is the, and I'm asking this question because I'm trying to fit this in a mental model, Today if I was a Brigadier, would I be, is the bigger picture to allow me to use Zenova as an operating system that is then integrated with all these other providers that may be deployed at different places to pull this into a single dashboard.
    So are you doing a software systems integration job or do you also want to then do the counter defense systems, so the counter drone systems?
    Yeah, I just I just wanted to clarify on how we want to start off with and before I answer your question I just want to say that getting into defense what we saw needed a lot of contacts, a lot of people you already know in the defense. Okay We don't because we tried doing that and we have found that out to be a bit difficult at the stage we are at. So to start up and get some traction and maybe even pilot our program, we want to go into the commercial phase where we want to essentially set up our Radars and integrated are an operating system.
    and eventually create better for facilities which are already highly prone to drone attacks.
    Very good.
    Yeah CorrectCorrect. We are currently in talks with someone in the Arab regarding Saudi Arabia. essentially run a pilot program but my what I The point that I'm trying to emphasize is We tried getting into defense right now and it's essentially We are way too inexperienced with defense. And we don't know anything. Yeah. Yeah, perfect soYeah. Peace? God. Okay, now to actually answer your question, are we Setting up our own radar, I'll be doing the operation.
    system. and essentially We want to start off with the operating system because how we look at it, current forces and the current authorities might not realize the need for a multistatic system, but the multistatic The operating system is a big More far into the future where the need might not be recognized right now. But right now, yes. For defense,It was specifically different. You would like to come in as an integrator of all the sensors and essentially provide an interface between the operator and the defender.
    Is that fine, sir? Yeah.
    Zed, sorry you were saying something Yeah, please.
    Uh, yeah.
    To answer your question again, As Gurasi has already mentioned that we are trying to make this ...operable software to integrate all of the things together. That's what we are talking about. Again, when Russ has talked about defense... Defense again, it's not like we are... Behind in the different space, but then it's very... So for example there are multiple drones Each drone company has their own software.
    Yes. Yeah. Yeah, absolutely. The defense forces have taken into account the multistatic setup but in a passive sense. So there's something called passive radars that are not active and they have been talking about this as well. But it's not just at that level that we can directly go in. Yeah. No, this makes sense and in fact Let me actually Okay, let as we go through this, let me also go find the name of some companies that I've heard doing exactly this operating system or software system integration task.
    30th January, OkinawaOkay. Hmm.
    Got it. So let me build a new... Yeah, so this is the one that I thought was decently interesting in the Indian context. But I completely agree with you. There is this... Opportunity to build a single software layer that it brings together all of this feed which was actually the initial promise of of Andrew right and then they went into towers and whatever else and use you use lattice which is the right That's their product brand.
    Tell me a little bit more about this engagement with Delhi airport and other places. How did this come about? Where are you in the... in their procurement cycle like do they have alternatives do they already have a solution is it a rip and replace there just some more info about this About the commercial side of the business?
    Yeah Yeah, GMI group which operates multiple airports including the D-Lane International Airport and they essentially run a program where startups can pitch in and they can implement their solutions Yeah We build that pipeline and we talk to them about what currently is deployed at Delhi airport, what do they actually need at the airport and where we could fit in. And currently they do have a digital film simulation.
    So they have essentially a simulated model of the airport but they don't currentlyDo you have any data deployed Specifically for These kind of drones and these kind of micro-EMVs And we essentially couldn't pitch in there because They directly take up contract They don't have any speed people basically to early say for them. I would be Wipe me. Die, boys. We could set up a small pilot maybe like one or two days sort of see the whole ecosystem of frags that any of us would Try to integrate those and use them with the radar.
    and essentially see how all of that goes Just to add to Guru Asi's, just to add.
    So the airports currently, they have a digital twin simulation that they claim they have. But again, the problem is that we are not competing with that type of solution. We are integrating their software because Cables will have their own software when it comes to air traffic control etc. What we can do as a platform when you talk about this operating system, if we can integrate that to speed up the process.
    specifically counter drones and then integrate with their software that's what we can pitch in as well and that's what we are in talks with them as well so we are not like directly competing with those software we can just have a integrated platform interoperable platform makes sense The Saudi guy and The Gulf market is essentially that most of the defensive systems, most of these counter-EUV solutions, they either get it from the US, the other dominant suppliers, or they get it from Europe.
    But again the problem is these systems cost a huge lot of money. For example the setup. single defense system cost them some sort of range between 2 to 5 million dollars but then the problem is when you have a facility that is you want to guard this facility you need to have multiple defensive systems but you cannot take these 5 million dollar systems 5 million 5 million 5 million you cannot take there is no economic freedom as much when it comes to these solutions but again why is USA the dominant supplier because USA does not sell us single part single counter UAV solution Yeah We presented the platform and the radar systems.
    It's quite interesting and we can have a discussion about this later. Yeah. Makes sense man. See it's a painful procurement process. That's the only thing which I will tell you because it becomes sort of systems integration work. You know, just I had one or two questions that were up here. You know, you had Dr. Manoj Kumar, Rahul Arora, etc. How did you guys get connected to them from the IAF? Are they were they helping you in any way to break into defense procurement?
    Just give me a sense of what the journey has been so far. So we're meeting today. When did you start working? When did you all try defense procurement? When do you decide to go away from defense procurement towards commercial procurement?
    Right, so we started up last year July, right? So last year July and at that time we were trying to essentially create a whole anti-nones system, create missiles to take down nodes and whatnot. And essentially through that process, talking to people and essentially trying to validate our idea, we got to know that, oh, it's not the interception part, it's the detection part that is actually hard. and Talking to a bit more people and all of these people are just cold contacts.
    Like go to LinkedIn, DM people, hey I have this idea, can I get some of your time and all of these were just cold contacts. And through that process we came across a few people, for example, I'll be pointing out to Manoj Kumar, he is The head of product loan forms in IS And he found an ideaAnd he, we basically, ...fix your idea to us and we were like, "Okay, this is what we're trying to do. What do you think about it?
    How can we get this in contact? What can we do?" And essentially, their take on this was, Correct because yeah that's it and doctor uh they are essentially a systems evaluator for short range surfaceand that was essentially what we were trying to createUh, do you want? I need But I justThe discussions with them were not Okay. for Interceptor and a lot of technical discussions with Rahul Arun and nothing too business oriented and the business oriented part was more towards Dr.
    Manoj Kumar and essentially In the end, what we set up for was that OkayWe want to get to a level as fast as possible where we can get those 100 CR, 200 CR contracts from defense. And to actually get to that level, we need to go into the commercial space. That's what we thought, that we should go into the commercial space to actually get some traction, get some validation that, okay, we can actually get stuff done.
    And going into that part has been like the last A month or so I would say. That's when we... Okay, more than a month. And that's when we reached out to people and sort of getting their views on reaching out to our potential customers to essentially sort of understand what they need and is this something that they would actually pay for? And so that has been mostly what we have been doing And what if we even-Makes sense.
    Commercial effect mode.
    Because she, mainly because we don't know anyone in defense, we don't have anyone who can tell us I'll keep you take us to the different forces and be like okay guysin the Paragon pool Let's talk about that. Another thing that sort ofThe main point was that-Ready? Uh, it'd be a little bit of a lot. probability based if you don't have Yeah Makes sense Yeah?
    Yeah, yeah, I know look I'd agree with you man, I I I actually messaged Ankit as well on WhatsApp where I said that unless one of you, one of the two of you has a parent who is far up that military value chain, I don't think it's worth it. I'm glad you guys are doing this. dual use and quite frankly you'll probably end up doing better just not doing defense Because quality of business you build in defense is garbage.
    It's a 270 day networking capital cycle, buyer concentration risk, limited export potential. And that's why, you know, the... The typical defense listed prime in the country is like 400-500 million valuation, right? Exactly. And despite having burned through a lot of money on the way up, lot of political connects, etc. So it doesn't excite most people at the early stage. When you guys are thinking through And presumably we are now thinking about capital, what What sort of raise do you need to put together?
    Where does this get you? How would you plan to use money that you've raised?
    First of it, and essentially mostly it's going to be building the radar and essentially integrating all the software with the new hardware that comes along and more of just building towards the MVP. I'm not sure how to answer your question but... Yeah. I hope I did a good job. But yeah Let me think about it. Do you wanna add something?
    Will you just be normal man? making those radar systems and not just making those radar systems and actually having the software like gluing together perfectly with the different Hardware bot. Yeah. Makes sense. Awesome, man. No, I think this is a good starting point for us in the conversation. 200k is actually a bit at the lower end of what Funds like us would do round size guys, like the smallest rounds we have ever participated in as a fund.
    Just, and I'll be very honest with you, given the fact that in deep tech, forget defense, Things always take longer than planned. They're more expensive than planned and therefore typically a company needs a lot more capital cushion. Have you guys tried the incubators like sorry incubator accelerators like the antler India campus fund etc.
    Wait, Antler India and Campus Fund are two different things.
    Correct, correct. So there's Antler, there's Campus Fund, there's Entrepreneur First. Have you applied for any of these?
    Yeah, so campus fund we didn't apply to and at that point we had like the defense only sort of mindset which kind of turned off campus fund and yeah so that's the deal with campus fund. Other than that we mostly have been, our last contact with any venture capital or any accelerator was when we were doing defense. Yeah. We sort of took a break from trying to raise money because we sort of figured out that when you say defense people just get knocked off and it's just not it for us and we kind of took our time to actually formulate a plan into the commercial space and this is essentially our first time coming back trying to raise money with I'll part straight.
    I think the The really tough one for me to get over the hoop over here is This is going to be one absolutely painful procurement process for you. and There is going to be 12-18 months per company. I have not studied anything on the commercial side with this type of product. So I will need to go in my network and come back to you. It's tough dude. You all have picked a tough problem but There is no other alternative right?
    Defense is a no go in my opinion. Yeah. How do you guys feel about this? Is there anything else? So if I had to almost flip this around, Sometimes as an entrepreneur you are at right place, right time, you may not be right person because this industry relies on insider, on bribing, on who knows who. Is there something else that you would build that is not dependent on a procurement cycle like this?
    I don't think I have an answer for that.
    Yeah, no, no, I'll just leave you with this question, right? Because fundamentally for me, the decision to sell the company, not continue running it, whatever, when I was an entrepreneur, Was just based on the fact that I said wow okay this is like turning out to be one catalyzmic slog that is leading to nothing right I mean of course we were profitable growing and whatever else because insurance gives you revenue every day.
    Every month but Yeah, this is This is a tough one. Let me sit back over this and come back to you guys. And I'll also suggest a few people who I'm happy to connect you guys to. Yeah. But very good stuff man. I think given yalla what 21, 20, 22? 19. 19. Okay, wow. Very good. Yeah, this is good. Very good progress. And... How long have you guys been working on this?
    Year, almost a year ago.
    Yeah, early days man. So I'm not, you guys still have what, two years in college left? One and a half. Yeah, so there is ample time for you guys to also move through this. Yeah Yeah, it's a tricky one dude. The other issue also is almost every large venture investor in this country has already taken a bet on a systems integrator that they want to build out all this software right because it's a little bit of a king making play And I know you're not doing defense, but then the same guy doing defense also does commercial, right?
    Because for all the logical reasons you listed, So it's going to be a tough one to even see who else is open in this space. What up? This is me telling you what's going on in my mind.
    question if you don't have one. Yeah. So when you say it's going to be a tough procurement, I just want a bit more context in that.
    So, so look, I think what I'm very worried about is because you guys are young and not naive, but because you're young, you probably don't have a sense of what value based pricing and pricing methodologies are. You will get low balled into, let's say, a Delhi airport offering you $60,000 a year for this product And you will jump and say wow 60k USD is great. But... I don't know how you will get connected to someone who runs Adani, who's at Mumbai, knows actually what the ability to pay is.
    And I sense you will get stuck in this 100k ACV zone where you will only get 20 to 30 airports that would purchase the product and you would stagnate. And the tough part about the procurement now is how do you go back negotiate a 100k to 500k or to something else. But if you guys can crack that, then you're home, right? I also don't know how long it's going to take to deploy at one of these airports.
    I don't know what is the state of their tech stack. I don't know what software vendor they are using to build out their tech. Therefore, I don't know how much of product based work you can do versus how much of pure play services or systems integration work you have to do.
    That makes sense.
    And you can use cloud code and all that's fine, but then you're not going to get a enterprise valuation, right? You're just a services shop, which is nil enterprise value. If you think about this from the lens of an investor, as a founder, services business is also great, right? My mom has sold a services business, she's made money, but no one who would have invested in that would have ever made money.
    And I sense the issue with all of aerospace, aerospace is broadly or airports are aerospace and defense. Is it so hard to build the product or the platform which gives you your enterprise value? Otherwise, everything else is custom integration and services. But you'll have to go through this journey to see what can be productized and what is What cannot be productized?
    Yeah, and look sometimes you have to have your founder conviction as well.
    It is not. It's not that you listen to one random uncle walking on a treadmill and you feel you got like a lightbulb from Zeus or something. But good stuff. I think you've done really good work for your age and the resources that are available and don't be disheartened by what's happened in defense. And I'll come back to you in about a day or so. But whatever the outcome is, I will also make a couple of introductions so that you can speak to other people who are better informed than I am.
    No, that's awesome. Thank you so much.
    Awesome. Thank you so much. Nice to meet you, Guruji. Best of luck and speak soon.
    Thank you so much. Awesome.
    Take care. See you. Bye bye. Take care. See you. Bye bye.
