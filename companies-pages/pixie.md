# Pixie

**Table of contents (click to navigate)**
---

## Meeting 2026-02-24T10:08:00.000+05:30 


### RM reflections - SM on Shiv as a Founder
++ Tech spike of CTO CoFo Rahul comes out;  5 mins story generated in 15s v/s 60s earlier; very good system prompt - Granny v/s Nani, Language, Customs, Pronunciation, Music in stories etc
++ Customer backwards: Re-listening content insight on children’s behavior, screen lock,  custom voices; family & grandparents mentioned in stories
++ Opinionated UI & product development: Guided UI to help parent tune various story components
++ Commercial instinct of Shiv - Freemium tier w/ contextual Ads - Flavour Labs
?? NOT Consumer Tech native founders - Need to be coached on Retention, Loops etc BUT very good Product builders
?? Don’t see GTM spike which was clear in EMoMee’s case
?? Analytical skills seem a bit deficient for a ex PE guy - didn’t have a good answer

What would change my mind:
- 2PE which suggests Customer Backwards / Tech Spike is not clear


### RM notes

- Cousins
  - From Siliguri West Bengal
- Rahul
  - IIT Hyderabad
  - Software @ Alexa
  - Alexa voice actions
- Hardware journey
  - ₹5K ASP hardware won’t work
- Problem
  - Parental controls - age wise
  - UI not suitable
- 3-6 yrs
  - 3 hrs per day video content consumption
  - parents want screen light & educational
- Idea started w/ nephew in USA
  - Used LLMs to create a story & then spread amongst his family members w/ kids
- Tech stack
  - LLM Orchestrator
  - System prompt
  - Scoring of story
- Cost
  - ₹1 per piece of content
  - 50 stories per month - Power User


### AI notes

<!-- transcription block -->

    ### Action Items
    - [ ] Rahul to schedule call with DeVC partners (Rajat and Aakash) and consumer team members (Kishan and CV) 
    - [ ] Rahul to connect Pixie team with [Answers.ai](http://answers.ai/) (Shubhan) for US GTM learnings and influencer ecosystem playbook 
    - [ ] Rahul to introduce Pixie to Supernova and imo me for insights 
    - [ ] Rahul to send list of recommended investors for double opt-in introductions 
    - [ ] Shiv to meet with imo me during Mumbai visit (Jan 26 - Feb 2)  
    - [ ] Pixie team to focus on scaling user acquisition through Instagram and mom influencers  
    - [ ] Pixie team to continue reducing content generation latency (current: 15-16 seconds, target: under 5 seconds) 
    ### Meeting Overview
    First in-person meeting between DeVC investor Rahul and Pixie co-founders Shiv and Rahul (cousins from Siliguri). DeVC is a three-person fund ($40M Fund I, focused on pre-seed/seed with 140 companies at 1-2% entry ownership) that invests across deep tech, software, consumer brands, and financial services.   The fund has significant experience in the kids/education space with portfolio companies including Toddle, Supernova, Zoo AI (now Professor Curious), and Frizzle.  
    ### Pixie Product Overview
    Pixie is an AI-powered audio storytelling app for children aged 3-6 that creates personalized, educational content to reduce screen time.   The app addresses three key gaps in existing AI tools: safety for kids, child-friendly UI, and age-appropriate features. 
    **Core Features:**
    - **Custom Story Creation**: Parents input 5-6 parameters (child's age, name, loved ones, educational lesson, story type, character preferences) and generate personalized 4-5 minute audio stories  
    - **One-Tap Pre-Generated Content**: Repository of stories across themes that instantly personalize with child's name  
    - **Screen Lock Mode**: Stories continue playing with screen locked, similar to Spotify, dramatically increasing listening time  
    - **Sleep Timer**: Automatically stops playback after set duration, addressing parent feedback 
    - **Personal Library**: Dedicated space for children to re-listen to favorite stories independently  
    - **Voice Cloning**: Parents can record their own voice or choose from narrator voices  
    - **Alexa Integration**: Available as Alexa skill for hands-free access 
    **Key Insight**: Initial hardware approach (remote control device to reduce screen time) pivoted to software-only when beta app showed strong engagement, particularly for voice features.  
    ### Technical Architecture
    **Content Generation Pipeline**:  
    1. User input feeds into LLM orchestration model that selects appropriate models based on genre, language, and other parameters
    1. Story generation with extensive prompt engineering informed by hours of content feedback
    1. Quality control agent checks multiple parameters:
    1. Stories below quality threshold are regenerated automatically 
    1. Text-to-speech API with language, accent, and regional customization  
    **Key Technical Innovation**: Custom pronunciation engine that learns correct phonetic pronunciations from user inputs and suggests them to future users with same names, building a pronunciation data mine   This is particularly important for Indian names where transcription accuracy is challenging. 
    **Performance Metrics**: Content generation latency reduced from 70 seconds to 15-16 seconds (P99), with goal of under 5 seconds.    One-tap content costs ₹1-2 per story through pre-generation optimization. 
    ### Traction & User Behavior
    **Current Metrics:**
    - 650 active users with strong engagement from both India and US markets 
    - Surprising finding: Significant US traction without UI changes, contrary to initial assumptions  
    - Power users generate ~30 custom stories per month, average users create at least one per day  
    **User Insights:**
    - Most frequently added characters in India: mother, father, and friends (male and female friends rank equally with father) 
    - In US: grandparents rank higher due to geographic separation 
    - Children aged 7-8 are "hacking" the app to learn about scientific concepts (thunder, rainbows) beyond original 3-6 age target  
    - Re-listening behavior is extremely strong - children love replaying favorite stories 
    - Screen lock feature reduced session time but increased listening time significantly 
    **Origin Story**: Product concept emerged when Shiv created personalized stories using LLMs for 4-year-old nephew Rio (sister works at Meta), who preferred these AI-generated stories over his mother's storytelling.   Early validation came from sharing stories via WhatsApp with parents who provided 5 parameters about their children. 
    ### Business Model & Monetization
    **Subscription Tiers** (pending Apple payment approval): 
    - Free tier: 8 stories to test engagement
    - Basic plan: ₹199/month (India), $4.99/month (US, planning to increase to $8.99)   
    - Premium plan: ₹299/month (India), $6.99/month (US)  
    **Advertising Revenue**: Contextual brand integration for free users 
    - Example: Oral-B integration in teeth brushing lesson stories  
    - Brand collaborations with Gladful, SlurpFirm, and Flavor Lab creating themed story series   
    - QR codes on partner products (like Gladful orders) that generate instant branded stories  
    **Unit Economics**: Cost structure is sustainable with ₹1-2 per one-tap story and power users averaging 30 stories/month.   Costs have decreased significantly due to volume (previously ₹7-8 per story at low credit levels from 11 Labs). 
    ### Go-to-Market Strategy
    **Current Distribution** (primarily offline for early validation): 
    - Live storytelling events with 200+ kids, then pitching Pixie to parents 
    - Student fest partnership with Kukuduku (2,000+ participants) 
    - School partnerships: 2 schools providing Pixie access to all parents (400 users total) 
    - In-classroom usage: Teachers use Pixie for mandatory story time, letting children choose characters as rewards 
    **Future Scaling Plans**:
    - Instagram mom influencer ecosystem (primary channel)  
    - Brand partnerships with kid-focused companies for co-marketing 
    - Pediatricians and speech therapists recommending as screen time alternative 
    - Organic word-of-mouth through parent WhatsApp groups (every parent is in 10+ groups)  
    **Recent Growth Spike**: US downloads surged when one parent shared in school WhatsApp group, leading to immediate viral adoption. 
    ### Key Challenges
    **Product Challenge**: Balancing two stakeholder needs  
    - **Children** want unrestricted entertainment, relatable stories where they're the hero, fun with friends
    - **Parents** want screen-free, educational content that teaches vocabulary, concepts, and values (like using Hindi to teach Gujarati kids)
    - Current balance works well for ages 3-6, but 8-9 year olds want more interactivity while parents still want minimal screen time  
    **Technical Challenges**:
    - Finding optimal balance between personalization/control and ease of use  
    - Latency remains concern despite 78% reduction (70s to 15-16s)  
    **Business Model Consideration**: Age-related churn limits LTV compared to products like Spotify, though early acquisition (age 3-6) and graduation strategy (expanding to older age groups with science education, etc.) can extend lifetime value.   
    ### Fundraising Details
    **Previous Round**: ₹50 lakhs from 4 investors including former Google Assistant director and his partners (50k total).  
    **Current Round**: Raising $1M to reach 50K-100K users by December.   Efficient burn rate with sustainable unit economics positions company well for growth.
    **Competitive Landscape**: Limited direct competition. Bunny Labs (SPC, Indian founders, US incorporated) was developing similar hardware + software play but returned capital and abandoned the opportunity.     imo me focuses on video content and physical toy sets, not audio-first approach.   US founders currently focused on B2B AI rather than consumer applications, leaving consumer AI for kids largely untapped. 
    ### Next Steps
    DeVC will coordinate follow-up meeting with partners Rajat (led Razorpay investment) and Aakash (8th Housing co-founder, early Hotstar employee), plus consumer team specialists Kishan and CV who have evaluated 60+ companies in AI kids space.  Focus will be on US GTM strategy learnings from portfolio companies and potential syndicate partners for the $1M round.  Immediate priority is scaling user acquisition through online channels, particularly Instagram mom influencer ecosystem. 



    from overseas, which if you ask me is the real market, right? They see parents don't really have the money with no disrespect meant to them. Yeah, yeah.
    Very nice. Most of the people I think, the thought has been that we would want to, It's easy to get access to Indian parents out here. And a lot of networks that I personally had was able to leverage that. But surprising that US parents, we thought that we'd have to change the UI a little bit. Yeah, very nice.
    And what I'll do is first give intro about me. First time actually we are meeting. I briefly spoke to Shiv when you were doing the thing to reduce screen time for children.
    We were doing a hardware play. Correct.
    And I remember you had also done like Zepto 1.0 version over COVID. Yes. Yeah, makes sense. In fact, Adit was in my batch and I remember. I did YC winter 21 and I remember the Batch consensus was these guys are clowns. Is it? And obviously history is such that they are like 99% of the market cap of the batch. Disruptors are that way.
    Yeah, yeah. People think they are clowns before they actually do the disruptions.
    Yeah, yeah.
    It's very amazing how YC backed them at that time when they were only focused on SaaS, tech play, and this was not primarily a tech play, right? And more operational heavy.
    Yeah, they even went and backed another company after Zepto called Build ASAP, which is a cross between Udaan and Zepto for Southeast Asia. But again, like... Very weird things happen. So yeah, I was a founder like you guys, YC winter '21, I raised capital from Sequoia, sold the company at the top of the bull run. In 2022, so I take zero credit for it. Whatever money I made from it, I went and gave back to my mom and I said, you enjoy life.
    She doesn't enjoy life. She's still running a company. That is Varad, right?
    Yeah. I got...
    somewhere in that 1 million dollar range out from the company which is a very good outcome in the Indian context. Today of course people make way more but whatever. I'm not too stressed out. So at DVC I do everything from deep tech to software to consumer brands to financial services. We're a three person team, two partners plus me. Rajat led the investment in Razorpay. Akash built and sold housing.
    He was the eighth co-founder who didn't get fired. He was at Hotstar early as employee number 15 or 20 and sat there post the Disney exit as well. So at least two of us have been in the trenches as operators or founders. Rajat obviously continues to operate his family's manufacturing business on the side. So he's also quite used to Bamboo Master, which is what you need to build and scale any business.
    And philosophy at DVC is to come in early, even if there's no round, you commit the capital, we look to take 1-2% of the company at entry. If there is no lead investor, we bank the round, we help you figure out how to syndicate the We've done this at about 10, 15 companies. Fund one, which we're almost done deploying, fund two starts later this year. Fund one has 140 companies, 1% to 2% at entry. In maybe 12 to 13 of those we've already built up to 6-7% ownership with the idea that If you're on track with plan, you're executing well, there's no reason why we shouldn't come in and add more capital.
    In almost all of the 12 cases, we have preempted, offered a term sheet on uncapped or capped with MFN and that's what's driven the top up rounds that are happening. Slightly different way of investing. It's wide aperture at entry and really concentrate at the seed and series A.
    And other LPs dedicated for DVC or is it Z47 LPs?
    It's the same set of LPs that carve out similar to how the Sequoia vehicles you can allocate. It's the same structure. Okay, but you have a dedicated fund for DVC. In fact, even your cap table as well, if it's a US entity, it's a DVC Global LLC one.
    Okay, how big was the first fund?
    Thank you. 40 million for the follow up. Yeah, and then after this we'll probably close to double it and so on. But see if you're doing precedence seed you cannot have more than 100 million dollars, how do you deploy it? Exactly. If you're putting 200k approximately into a company at entry, then you have to double down a lot later on. So that has worked for us. And in a three member team. Three member team.
    We used to be a five member team, now it is three plus one engineer plus AI. And he does A lot. Yeah, like eight, nine people.
    It easily serves more than one person's job. Yeah, absolutely. Accordingly, we have four engineers in our house.
    Maybe more.
    Yeah. Some working full-time, some working part-time.
    Yeah, so that's sort of us in a nutshell. In the... Toys space we've had quite a bit going on over the years toys and kids I'll split it down first hardware then go software hardware out we had invested into legend of toys which is an RC control company you may have seen it on quick commerce platforms we had invested into that SPC bunny labs but they have returned capital because they're not doing the they were looking to do a remote control with similar to what you're trying to build Hardware comes software dedicated for children safe AI.
    They're not doing that but we had actually committed to invest there and they are not pursuing that opportunity.
    Indian company? No, US.
    Indian founders SPC India but US incorporation. We've done a lot in the kids space now when it comes to the world of software. So Supernova, which is English education, Zoo AI, which is exam prep. It's called Professor Curious now, but it was Zoo AI when we had invested. Frizzle in the US, but that's more teacher SaaS. That is not...
    Teacher marking.
    Almost like teacher enablement or scoring enablement. So we are quite excited about everything kids related. In fact, Rajat's top performing SaaS portfolio company Toddle is in education.
    Oh, Toddle is a fabulous company.
    Yeah, so he's very excited.
    I met the director of Toddle in one of the, so her child goes to this Deke Centre in Bangalore, Papagoya. So I met her, we were just doing a conversation with the founder of Papagoya and that's when I met Toddle's director and I had a chat on how they are growing. They're doing a fabulous job in the US.
    Yeah, yeah, yeah. It's old school SaaS but it works.
    And Rajat had invested through DVC or Z47?
    Z47. So Rajat has just moved into DVC last year.
    Okay, so he's dedicated to DBC.
    But typically partners invest across both funds. So really the only full-time person on the fund is me. Got it. Very cool, man. And AI, which is now quite big. But no, that's us in a nutshell. So very excited about everything AI for kids. We have not taken any investment from fund one as of now. There's nothing even in the venture portfolio either. I'll hand over to you guys. First time we're meeting.
    Quick intro. It is the interest confirm how do the two of you meet as well. And then I'll jump into specific questions.
    So, we have both grown up in Siliguri, which is in West Bengal. Cousins, by the way. Okay, very nice. Played multiple GTA Vice City games when we were kids. Nice. And I moved to SRCC for my undergrad. Yeah. Was in Delhi for three years, then moved to Bangalore for international. And you were Yashi's batchmate. Yashi was junior to me. Okay, got it.
    I think two batches junior to me. Got it. So, you are like 25, 26.
    No, no. Yashi was... I'm twenty eighteen batch. You're twenty eighteen. No I say age wise you're twenty. Achhaan age wise I'm thirty right now. Oh and Yash was only two batches junior to you? Yeah I think two or three. Approximately.
    Actually possible makes sense.
    Okay, so you were SRCC 2018 got it and move to investment banking Okay, what for two and a half years in spark capital? Yeah The consumer deals there. Yeah, then COVID happened moved back to my hometown. That's where I started delivery Okay, did that for six seven months and then wanted to learn a little bit more about brand building and then I joined a lighthouse Okay, we have a good fund.
    Yeah, Bangalore consumer deals. Correct.
    Bikaji, Kama Ayurveda, Nica And now I've taken the plunge to start Pixie.
    Makes sense. Awesome.
    It's all right.
    I'm here only, don't worry. So I'm just, I'm Rahul. Yeah, I switched sides with cousins and we've grown up together in Silivri. As a kid, I was really fond of puzzles and that got me into programming and stuff, right? I've always been interested in programming that way. Took computer science in IT Hyderabad, graduated 2019. Went to Japan to work there, couple of years. Came back home during COVID and joined Amazon in Alexa team.
    So I was working there for three years. That's when we got in touch again and she was saying she's building something and wanted some guidance and that guidance turned into a full-time work there itself. Makes sense.
    Pressured him to help me out from his Alexa time.
    And in Alexa you were working on software, hardware, models? I was mostly working on the software part, backend part and then with the transition of coming into LLMs we started building into conversational AI products that enabled argument matchingAll the voice transactions, a lot of folks now, if you've seen Alexa Plus, they've started taking in bookings and other aspects of a lot of your assistant related tasks that's being done by Alexa natively through voice.
    And that's the system we're building there. Let's say booking a plumber or booking a restaurant, making a reservation on flight tickets or anything, we're enabling that system there. Very nice. So effectively voice commands leading to some transaction or action. Very cool. Very cool. We invested in this company called Caddy that is trying to do this and now Whisperflow is doing exactly that. So it's very interesting.
    Awesome. VoiceAid is going to be the deal in the future. I've met so many people who've, developers who've stopped typing.
    I don't type. I'm only typing today in a meeting because I can't talk while you guys are talking. It's awkward. That's what we were discussing.
    What are the use cases where people will type versus people who will use voice? Yeah. And one of the use cases was when you're in public settings.
    Yeah, public settings. privacy astrotalk for example still gets most of his business through text because people in a household are embarrassed to speak Productivity will increase greatly with voice. You are able to do multifunctional tasks with that. You don't have to rely on something on body or anything. Yeah, I did half my office work walking in here itself. I was on WhatsApp with our agent saying do this, do this, do this, do this, do this, this format, etc.
    At the end of today's call, I'll go back and check. What has it been? It's decently good. I saw some parts of it. But very cool. So, y'all decided to partner even when What was the hardware device?
    pilots that that is not something which can scale because a parent paying 5000 bucks for a hardware piece which they don't know whether their kids will use after a month or not is not something a lot of parents would want to take on, right? And that time we had launched a beta version of our app. That was getting a very good response. Then we thought that let's just focus on the app because that can really have the potential of scaling globally.
    That's the rule that we took then. Makes sense. I realized people are just downloading the app and they were using it for the voice with the kids.
    So let me give you a little bit of understanding of what the app does. So the overall thought Rahul is that AI right now, AI tools that exist is not safe for kids. So parents don't want their kids to be on charge GPT. And second, it's not... friendly in terms of the UI so the child can easily go and navigate through it. And third, they don't have deep features built for age appropriate use case of the child.
    Yeah. Right? Yeah. So because of these reasons, we thought we are trying to build a AI that your child meets and grows up with. Yeah. Since we are building for the early age group, 3 to 6 is the focus right now. In that, each group content consumption is very high. Okay. Right, on an average, three hours per day is what these kids watch televisions or media, YouTube and other platforms, right? Yeah.
    Parents want something which is screen light. and something that teaches their kid as well.
    Yeah, makes sense.
    The moment you do something, you move away from video, video has a lot of exciting images, a lot of changing scenes, bright colors, which kind of hooks the kid. How do you bring that kind of engagement with audio? Because if kids don't enjoy it, parents won't buy it. Yeah. Right? That's when we started experimenting. So this started with when I was in the US. And I I have a nephew who's four years old back then, his name is Rio.
    and he used to be glued to screens And the only time he used to take his eyes off screen is when my sister used to tell him stories. Yeah. But she's a PM at Meta, so she was very caught up a lot of times. And then one day she told me that Shiv, you're the one who's going to be in charge of this. And I went blank. I'm like, which concept do I tell him story on and how do I stitch it around? That's when I used different LLMs and different text-to-speech models to craft a story for him.
    And I created it to him. And he loved it. Next day when my sister sat down with him for story time and he was asking mom, I want to listen to mom's story. Nice. So that's when I thought that okay, if kids are enjoying this, so maybe personalization is the hook which can drive the kid towards audio. Yeah. So that's when I started reaching out to my sister's friends, a few of my friends back in India.
    And I used to ask them five things about their child. Their kid's age, gender, name. Which loved one do their kids have? Mother's name, father's name, and the character that they've given to him. Yeah. And I used to stitch together an audio story and share it to them on WhatsApp. Yeah. Right? And that's when I saw that, OK, engagement is coming. Let me show you a video of an early user, a very early user.
    Who used the access?
    You guys should be if you want to screen share up there should be possible. Otherwise I can do we connected itWe had connected, but I think there's an issue.
    Can you just-Thank you. It's already in Apple TV mode, can you cut this?
    This screen is an enigma to me. I have never been able to make sense of it unless it's a zoom call. Nice. So the parent feedback unlisted video I watched, which is what you shared this morning. Yes. Which was very, very nice to see.
    So this is how the first child's reaction was. This is a child whose name is Vedi. Yeah.
    and while this comes up below the hood you guys are using a mixture of open source Close source LLMs, there is a system prompt in place, anything else beyond the usual wizardry?
    There is a complete pipeline. Okay. That we have built. Can I get this?
    Yeah, go for it.
    So it starts with user input.
    Which is those five, six questions that they are answering for you? Correct. All right.
    That feeds into Uh, An LLM orchestration model that you have made. Okay, yeah, makes sense. Right? Because there are different genres, there are different languages, so different elements perform differently based on those inputs. So you select the different models, and it generates the output. This is 2D output. Got it. This is where our prompt engineering has come. Yeah. We've given a lot of prompts in terms of what is the story that a child likes.
    Yeah. It's improving because we have hours and hours of content that has been generated and it is giving feedback whether this is good or not. Correct. It's bad for what reason. Correct. Right? So here there's an agent which we're developing which checks The story on different parameters. Okay. Like... Woke up. As a child's age Right, it should be, so there's something about three letter word, there's an exact score that comes.
    As per the child's age, the lexite score should match. The lexite score is basically... The length and the complexity of the words in the story. This profanity check that happens. Yeah. By chance, parent or someone has written something weird. Or the LLM hallucinates and gives something. Nice. Which the child should not listen to, right? Yeah. So, I mean, there are other parameters. Once... This gives the output, it gives us code based on these parameters.
    If it does not cross a particular threshold, it again generates. Yeah. Once it gives the story which clears the scores, then it goes into Text to speech. Uh... API call, right?
    Yeah. So we keep testing. And then this will handle the voice, the tone, the Western, if it's a kid in America you want American voice, Indian you want whatever voice.
    So they are, as per the language, Then there is accent.
    Yeah language accent.
    Language is English is the language.
    And then the story that is also some educational goal always.
    So that comes into the user input.
    So right now just to take one step back I am the parent my kid is here. I have pixie downloaded on my phone or maybe a phone that I give my child. I give it some input saying do a story that teaches them about.
    So you don't give a long input. Thought is that parents hate typing. They don't have time to type anything. Yeah. So it has to be very and they don't have time to think as well. Yeah. It has to be very easy for them. Yeah. This is how it works for them. Let me show you quick demo On the Pixy app, parents and kids can do two things. First, they can create custom content on characters and concepts they want.
    And second, explore one-tap content across different themes and ideas. First, let's create a custom story for my 4 year old nephew, Leo. Let's make a bedtime story in English. You can also opt for Chinese or Spanish during onboarding. Let's feature his favorite friends, Kiara and Ethan. So you can either tap from any of those options or you can type, you can create a character that your child wants.
    Yesterday he got very angry when his friend broke his crayon. So here we are giving the user as per the age of the child. What should be the lesson that your child should learn right now? Very nice. And you see those waves? Those waves are telling you that your child has already learned about teamwork a little bit. Maybe try something different. So as and when you keep using teamwork,Fact. the height of the wave will keep increasing.
    Yeah. Right? So you can also, let's say you came across a very different topic that you want to teach your child, you can just type it out there and take the input.
    Let's make it a funny story.
    Everything looks good. Very nice, makes sense.
    So this makes sense. I can completely see typical parent does not have the brains to think through all of these parameters. You are pretty much doing You are pretty much surfacing what an LLM would ask you as questions via UI. So thisClicks makes perfect sense. Okay, so this is what the parent goes through.
    Right, now the audio is generated. No, sorry, the text is generated.
    My own voice is saving.
    The two voices that we have. We plan to add other voices like a voice calling will come into picture out here. You can also have like a grandparents voice that we want to add later on. Very nice.
    So we've incorporated a lot of speed control, narration, abilities, custom voices, custom pronunciations, and all of those are tuned into the final output and it will be present.
    Kids go mad if their name is not pronounced rightly.
    Especially for Indian voices, that has been a challenge. Yeah.
    We built our custom pronunciation engines to handle that.
    And the custom pronunciation engine is-piece of IP that you have or you've again done?
    Yeah, so on our app, This is the data mine that we're trying to create, wherein we are letting the user decide what is the correct phonetic pronunciation of their child. And so let's say tomorrow you select that your name should be pronounced as Ruhal, for example. The next time a child comes with the same name, it would suggest that, hey, Is this one of your pronunciations? Nice. We're collecting not based on only one user, but we're creating a pyramid and as per the highest used pronunciation, it will recommend that pronunciation to that child.
    Yeah Within seconds, Pixie generates the audio story.
    Sounds like Desi Aunty. Indian, Indian English. Very nice. So if you pause here for a second, Can I also add things like my kid has two or three friends and you want to include the friends in the story?
    That's the primary thing that here you add You select a loved one.
    How do I-so fine. So that is all. Okay, very nice.
    You can select a wide range of relations, parents, aunt, uncle, friends, pets, teachers, grandparents, anything.
    One thing, Rahul, funny thing, so when we developed this, right, what are the four highest added people that you think must be there?
    Oh wow Best friend maybe from school could be one. If they go to school, Maybe a grandparent who doesn't visit them often, who's probably away in a different city. If a parent is away from the city, maybe the parent, that's what I can think of.
    Yeah, so you're very bang on, right? Our hypothesis was that it might be father, mother, grandmother, grandfather. Right when you started off. Yeah. Right now on the platform in India, the top ones are mother, father, and equivalent to a father is a female friend. I'm a male friend. Friends are something that kids love adding into their stories. Interesting. And in the US, you have grandparents coming up because parents are not there in the same city, right?
    So got it. So effectively by doing Divya, mom, Rohit, papa, you are effectively nudging your... your story generated that although the person is saying the parent is saying Rohit you have to refer to them as Papa.
    No, it's your call. So if you just mention maternal grandmother and you just mention the name we have made it in a way that it will identify in India maternal grandmother is called Nani. So it should call Nani. But in UK it's called Granny. So it should call it Granny.
    Context is provided with this but what it will be calling it is automatically tuned accordingly there. based on region, based on what is their customs and how they call it. People might be calling their, in US they might not be referring to their parents by name or they might be calling them dad versus papa or something like that. So it automatically chooses the appropriate word for that relation and uses that in the story, not necessarily using the name or something.
    Yeah, because a lot of, we have a lot of users who just put akka, So you should be able to understand that okay Akka is what the child refers to the grandmother. The child might not even know the real name of Akka. Yeah, absolutely. Absolutely. You are right.
    Very cool. So this is how we generate the story. Story can either be mimicking my own voice. It gets how I get my pronunciation correct. Very interesting.
    So there are two things that you can do in the app.
    And one tap content is pre-generated from your end.
    So one important thing in this is--Lock the screen.
    Parents want the kids to listen. So this is something that it reduced our session time significantly, but increased our listening time-Through the roof.
    So effectively the screen locks and just like how Spotify continues to play in the background, Pixy plays in the background. The child can pause it but in most cases the child will just listen And in this screen lock instance, yes, you cannot track whether they are listening or not, but anecdotally you are hearing They are listening to the end.
    Yeah, so we have a sleep timer as well. A lot of parents, what used to happen is that they used to put it on during their bedtime and when they used to get up, the story is still playing. Right, because the parent and the child listened to the stories, they both dozed off. Interesting. Right? Yeah. Then they requested at shift, can you please give us a? Sleep timer. Hmm. So that's why we introduced sleep timer.
    that you know that your child I just had a stop timer, lock the screen, and just listen with him. And because children love to re-listen to their favorite stories, every creation is given its own language where they can come. This is a very important aspect wherein kids love re-listening to the content that they like. So you need a platform, you need a dedicated library where now this is where the child takes over.
    Parents role stops when they are creating a story with their child. Once it's created, during the day when the mom does not have time or the dad does not have time, they give over the phone. The kid wants to listen to whatever is being told. Listen it from your creations or listen it from one tap content. It's your choice. Very nice. A dedicated library is super important for them. Perfect, no, this also makes sense.
    Based on the themes and characters parents are creating most, we are building a growing repository of one-tap content.
    George Washington's breakthrough. Hi Rio.
    Use the child's name. With one tap, the audio story instantly personalizes with the child's name. And because we control this content clear, we can add music, sound effects, and many other things to enhance the listening experience.
    George gave his father a tight hug and sang a song.
    nice very nice generating music also ♪ Who's to say ♪ Very nice man because your car dash would or simply by saying, Alexa, open Face-C.
    The origin of the name is not known.
    Very nice. Very cool. Okay, this is very nice and you played to Alexa relationship by getting this added as a skill also.
    So we were facing a lot of bugs. He called up his team in the Alexa office and was like, can you see the logs? That was amazing.
    No, this is very cool. So product wise, very clear. I think that a roadmap will emerge here. When you think about The business that you need to build around Pixie You are the investor, where does the profit pool come from here? How do you intend to monetize this? Let's go to that.
    Two things, right? In short term, there are two main things that we're planning for monetization. One is subscription So it will be a premium plan wherein you use the app, maybe generate eight content for free so that your child understands and you can see how much money he's having. And then there's a basic plan and there's a super plan. Yeah, right. So that's one. Second thing which we're exploring is ad revenue here.
    So for the free users who are there on the app, you saw the place where you can add a lesson. So let's say there is a parent who's added brush well as a lesson. And we have collaborated with Oral-B for Brushwell. Every time a parent creates a story with Brushwell, Within the story, Oral-B will be contextually placed. For example, I'm a mother in the story.
    "Rahul, where is your Oral-B toothbrush?
    Go bring it." So the brand will be on a per click or per listen basis. Very cool. Similarly, we can do that for one tap stories as well. So we are working with Gladful and SlurpFirm to bring in those aspects wherein-so for example, we did this with a company called Flavor Lab. I'll show you the content that we made with them. So... So we made the three series story. on food.
    And this was with Gladful.
    This was with Playworld app. They provide workshop on food to kids.
    Very nice, very cool, awesome. So there is this angle as well. And you'll price this India versus US separately, which is perfectly fine. How much are you guys burning today with this, in total across all these 600 odd, 650 active users? 650 active users. How much are you, like what is the... Just to understand the pricing, for one of these power users, how much are you spending on inference for them and therefore how much do you need to price this at?
    So each content that is one tap content that is being generated, it is costing us around 1 to 2 rupees. What user? Okay? So let's say you opened a new content, it cost us one rupees. Okay. Because you've made it in a way that a lot of is pre-generated, but the parts where your child's name is being taken, that are the aspects which we are generating.
    So Rs.1 per piece of content, typical parent does how many pieces of content a day at the absolute power user tier?
    at least one per day is a general average.
    So we were just trying to compute that yesterday, the exact numbers. Very nice. For your creations, right? which is the story that you're creating Customs that you're creating. Our power user is generating 30 stories.
    in a month. Perfect, pricing makes sense. So we can move on. You have found the right number, 199 and 299 is Spotify as well. So it makes sense and the US will scale it up accordingly.
    499, 699 is what we want to start with and then move it to 899. 4.9 US.
    Yes. Okay, makes sense. Okay, so this is, so therefore your costs are in control. This is not a lopsided gross consumer AI business. And I presume the LLM Orchestrator is something that really along with the structure of the story really compresses down the generation cost which is nice. Okay, this is very good. And when you think about distribution backwards, Yeah.
    So the product has been evolving and so has the distribution, right? Multiple channels of distribution.. First one-so when we started, the thought was to get users offline so that we can speak to them. And there's a relationship that is established. They'll come on a call and have an interaction with us. So far right now distribution has been mostly offline Which is you going to what schools?
    Schools?
    I am a story teller as well, so storytelling events. Where I host events for kids, 200 kids sitting, I tell them a story, then I plug in Vixie to their parents and then they download the app. And We did an event with this company called Kukuduku It's a very famous student fest event. They have more than 2,000 participants coming into it. Got it. Um... But now going forward, what would be the plan, right?
    Because this was not meant for scale. Um, First will be schools. We are already working with two schools wherein they provided access to Pixy to all their parents. So immediately we got 200 users from each. Yeah. And since it's coming from school, there's a lot of trust that is built into it. Correct. And few of these schools are also using this inside their classroom. Yeah. Every school, especially preschool, mandatory needs to have a story time class.
    in the week. So what they do is and that their teachers are not trained into storytelling. They're more trained into handling kids, changing the diapers, teaching them ABCD. Correct. What they do is to maintain the excitement, they reward the child. You are, you did a good job today. Tell me which character do you want to listen to the story about? We will be on you. Entire class is feeling that, "Acha, aita Rahul ka story sun rahe hai, hamla sab ko bhai" Correct That's how they're using this in schools.
    Makes sense. So that would be one aspect. Second is mostly Instagram. Influencers.
    Yeah, you will have to do the whole mom influencer ecosystem because that's how you get the product through. So I will do a double opt-in with Mohith from MomsCo. He had done a lot of mom-led influencer and then probably use him as a way to understand Who are the right influencers? Which even an agency will tell you but at least he'll share his learnings from having done it. So yeah, so there's influencer.
    Then there are brand collaborations. For example, let's say we collaborated with Gladful for that matter. Gladful will inform their parents that hey, you want to hear a story about why you should eat nutrition, go listen it on Pixi. And there's also a plugin of Gladful inside the story. Second thing that we're doing is, one is them marketing On social media? Second thing is that we are exploring a way in which all the orders that they send off will have a card on which Pixie's QR code is there.
    And a customer of Gladful can just scan that QR code, enter the child's name, it's a web app that will open up, enter the child's name, and instantly a story gets generated which will have Gladful in it, why you should eat this nutrition mix that they're trying to sell, and a beautiful story that the child will be happy with. Then there will be a button to download Pixi. Right?
    Makes sense.
    Then there are other ways, obviously, like we are speaking with a few pediatricians, Speech Therapist who would want their kids-the parents reach out to these child psychologists saying that, hey, my child is addicted to screens. What can I do? Correct. There's no solution at the--Therapists can order, offer. Yeah. But now there is.
    Makes sense. Okay, this is good. So you're clear that you'll ultimately have to do scalable online GTM. Offline will obviously work. But typically offline is a follow up to online. Yeah. Blow the lid off Instagram with the mom influencers itself and then that will seep into offline discussions and whatever else.
    And the fun part with parents is that it's a very close-knit community. Yes. Every parent is on 10 WhatsApp groups with other parents.
    That is the whole mom-influencer shenanigan, right?
    So if you like something for your child, you share it in your parent's group that, hey, came across this. That's how we got into, we saw spike two weeks back in the US. A parent who used our app shared a story in their school group. Another parent downloaded it instantly and started using it. Yeah.
    Very nice.
    So word of mouth spreading with these groups is very cool. Very strong, absolutely. And the counterbalance to this since you're an investor is there is age related churn. So you don't have to pay as high a CAC because you acquire them through this word of mouth, through parents and offline communities. But it's also not unlimited LTV, right? Like Spotify can project out LTV for 69 years. You will have to think about how the graduation dynamic plays out.
    But that's not a seed story, that's a series A story.
    So since I've been an investor, LD has been a thought right? Yeah. So hence we were very clear that we want to acquire kids as early as possible. So that we are now their habit and then we can grow with the child. Yeah. For example, a six to, a three to six year age child is listening to lessons. And sharing five magical words like saying thank you, saying sorry. But we are seeing users who are seven to eight year old adding concepts in the lesson section.
    What is thunder? What is rainbow? So one of the eight-year-old child's favorite story on our app is where a unicorn takes the child down on top of a rainbow and explains how this rainbow is formed. scientific reason why how this range was formed.
    Absolutely. Absolutely. You can-So they're hacking into the app and trying to use it beyond their use cases? Yeah. And that's what we're trying to-And this is the kid herself, or this is the parent of the child? Kid herself. Kid herself doing this. Yeah. Perfect. So look, makes perfect sense. You can also ride some part of graduation. What concerns you about the business?
    I think So one thing that concerns us is So we're trying to balance two stakeholders, right? On one side you have parents who are the payers of the app. On the other side you have students or kids who are the users of the app. Now a student or a child enjoys the app because They can relate to him, relate to the stories. Yeah. They are the hero. Yeah. They are having fun with friends. Yeah. And unrestricted Entertainment.
    Yeah. Because parents are like, "I'm watching TV for an hour a day." PIXI that you are letting to offer, Yeah? Right? So it's unrestricted entertainment. I don't have any issues. This is audio, right? Yeah. Hey, what do you have, parents? For parents, this is good because it's grain free. Yeah. It's teaching vocab. Concepts. Language, we have few Gujarati users. who are using this app to teach Hindi to their child.
    Yeah.
    Yeah. Yeah. Yes. Emomi is a DVC fund one portfolio, but that is completely different right their end goal is to buildThey're trying to build Disney-like kingdoms. Ha ha, like EQ skills for children, which is a combination of content plus a Physical toys universe.
    Yeah, they're making those kids.
    Yeah, full kids. Correct.
    So now this is-Why both the stakeholders? Happy. Now as you move forward to bigger age group kids, Whether we'll be able to maintain this balance or not. Because these kids would want a little more engagement on the app. more interactive. But then we might-the parents might be like, nahi yaar, I don't want my kids to be looking at the screen. Yeah. We are facing that right now. We have 8-year-old, 9-year-old kids using this app and parents are happy because they compare it to over stimulating video content on YouTube.
    That's the battery. So that's something that we will have to figure out.
    So this is on the product side, anything on tech that gets you worried.
    So currently it's mostly like The general idea about audio not sticking out. We've tried our best, but at many levels, the customizations, it's just like, so there's two ends, right? One is how much personalization you want, how much control you want, versus how much ease you want. We need the right balance out there. So we're getting a lot of requests from parents that we want more customizations while we're also seeing a growing use case of one-tap stories.
    Finding the right balance for all the age groups is where we're trying to make the best use case of it. Yeah.
    I think one challenge that I think that one challenge that we've been facing is latency. Because the content that we're generating is four minute, five minute stories. and the parents can't wait. They can't wait for a story which is loading, loading, loading. So we have brought that down from, I think what?
    It is 70 seconds before. We brought it down to 50 seconds, and then now we're currently at 15 to 16 seconds. Wow. The end goal is to bring it down to 5 seconds and lesser. We're still working on that part. I'm hopeful that we'll be able to achieve single-digit success at least.
    So he's built this fun thing. Let's just create a random story. So you can skip wait as well and it triggers the smaller model and generates it quickly. Now this is generated, right? I press listen and it's generating. This time that is there, It is right now around 17 seconds, P99 I think. Right, so this was earlier 70 seconds approximately. So now it's live, so as it is generating it is being streamed to the user.
    This is a test flight version. No, no, absolutely. Very cool. That is something that we're trying to work on.
    Yeah. Let's see. Good stuff man. So next steps from my end is I'll figure out how to line up a call with the partners. I may rope in couple of people from our consumer team there because they look at the AI kids space extensively. Kishan and CV must have met 60 companies. You can ask them questions. So they have a little bit of domain depth. What questions can I answer for you guys?
    I'm trying to-so-For us, Rahul, the next step, since we are right now raising the round primarily to scale adoption, right, in India as well as in the US. I wanted to understand which all your companies are primarily focused in the US market and how have you been able to help them with the USGDTM?
    Yeah, so half our portfolio is in the US. We haven't done too much of US consumer focused But I can introduce you to our portfolio company Answers.ai. Which is... Math. It's more... It's more like... 18 to 21 range solving tuition, solving college exam prep. So they have nailed the creator and influencer ecosystem there using in-house creators. Shubhan is like very high NPS founder so he'll if you land up in the US and in LA or SF you should meet him in person he'll give you the full playbook So he's definitely, Ansar's AI is one you should meet.
    Supernova you should meet in India. Actually more than Supernova, MO me. I think something will pull out the action items but imo me I will figure out the connect Answers AI for the US is one. What else can we do for you in the US consumer landscape? No Indian VC can help you. Exactly right. But But we know enough US VCs who we've co-invested with in the Indian Indian companies going there were mainly an enterprise software investor in the US where I can figure out people.
    Like I know Shyamal who used to run the OpenAI startup program. Uh... few people like that who might be able to nudge you in the right direction. But remember that the US approach to AI is very different from the India approach. In India because we have seen Seco and a few other companies really ride, we are very excited to back consumer AI. The West is more focused on build the next foundation model company, build the next ServiceNow replacement.
    Their interest in consumer is not as much as our interest.
    You know, and surprisingly that's what our realisation was when we were trying to understand that someone must be doing this in the US. It's such a big use case. But all the founders in the US is only focused on B2B right now, which is definitely a very good thing as well. But that leaves a big market for us, which is untapped out there. Yeah, absolutely.
    Absolutely.
    Well, flavor of the valley right now is to do AI research, right? Flavor of the valley is not to do functional AI, which is what you guys are doing. And that will change in two, three years when they realize most of this AI research is... Please just speak. Bakwas only. At a certain point doesn't make a damn difference to shit works Get the transcript out one way, any fucking AI tool will tell me what the action items are.
    That is true. Not that fucking hard. Very true.
    You have a little too much strength. Smallness daily. Yes. Maybe in the future we also like in the roadmap there is a thing that we want to train a voice model which is suitable for kids because when for kids to have an interaction with kid Voice modulations become very important. Stressing on certain words like the cloud fell down, thum, right? Yeah.
    This you've not been able to tune 11 labs output.
    So we have. So that's how the-so we have generated a--Cloned voice out there. Hence, you see a very good voice modulation that is coming in.
    Let me check. Video entertainment. He's not doing audio. I know the guy at Lightspeed who's made the Seiko investment but he's also Interesting character. I can chat with someone and come back to you. But... Rich thoughts first grow like just blast the tofu right because once tofu blasts all your downstream problems become apparent you can stack rank and prioritize them like don't try premature anything in fact even if you are close to break even on GM I would have said no problem because economies of scale kicks in yeah right tokens are a little bit like construction material the bigger your fucking project the We have seen that, right?
    For this, which is costing one rupee to us, earlier when we were on very low credit requirements from 11 Labs, it's costing us around seven to eight rupees. Yeah, absolutely.
    Perfect. So I'm clear on my next steps. Uh... I'll also maybe send you a list of people who I'm happy to double opt in, introduce you guys to their sensible people for lack of words versus most other investors in the ecosystem. The idea is if we take 1-2%, you still need someone to add maybe the next 7-800k. So I'll give you a few suggestions. And the round is 2 mil, 3 mil, 1 mil, 1 on? Or you still don't know?
    The valuation? Yeah, have you already? Okay.
    We did a previous round.
    That was with the Misho engineering guy? Yes. Okay. How do you know him?
    So my sister in the US and he was also in the Bay Area back then. So he was a director of Google Assistant back then. Correct. And he's put what, 50K in? No, so they have to get, so they are, he and his brother and one more person, there are four of them. Okay. We've raised a 50 lakh round.
    50 lakhs. 50K. Very efficient. Very efficient. Very nice. And you're doing a one mil round, makes perfect sense. What does a one mil get you? Uh...
    So that's the focus. We plan to reach approximately 50K to 100K users. by this December. But we really don't know what is the potential here, right? You don't know how you get viral instantly. Yeah, no, fair.
    Okay, I know one minute is a good starting point. Uh... Y'all will just need to... On that Instagram thing I will connect you to... What is Moed Sadani?
    Moed Sadani? Imomi Answers Moed Sadani.
    So I am going to Mumbai on 26th and there till 2nd, if you have any connects that I should speak to in Mumbai.
    Investors are here, I am from Mumbai, I am also here because everyone is here. But you could meet Emo me. You could walk into the Amome studio and see what they're doing just to get Do you think it's a competition?
    Because I saw their Shark Tank pitch, they are focusing on video on YouTube, they're focusing on their sets, the kids set.
    No, no, no. So look, the honest answer in consumer is you don't know who's your competition. Everyone will get into everyone's ass crack at some point. I'd be honest with you, I have no clue what the f**k Imomi does. I'm an investor in the company, they send in... They don't send in MIS. They don't even send the lead investor in MIS. Clueless. I discovered yesterday when our partner went to visit them in Mumbai that, "Oh, they are not selling SKUs, therefore the MIS looked so bad." They are focusing on content like you said.
    It's not competition. Bunny would have been competition. But it's returned capital. Got it. Yes, I know the guy who was doing engineering at Bunny. I can connect you with him if you want to speak to him. I'll follow up on this. Perfect. It was good chatting with you guys. Very interesting. Good early traction that you all are on. You all are not monetizing right now. You all will now start charging.
    It will be a fun journey for you all.
    So this is what we were just experimenting with. We have already applied for approvals to come in and Apple is taking a lot of time for payment approvals. So in the meanwhile we are trying to, we have few power users, we are trying to target them and ask them to pay up. This is the test flight. This is what Subscriptions will deflate.
    Yeah, I like the-I presume this is all AI generated UI. Oh, no.
    So we are working with Andre. OK. So Andre is someone who's been with us since day one. He sits out of Berlin and he's the lead designer on our team.
    How did you find him?
    So that's Andre. How did I find him? So he was working with Google. And my sister in the US, she was working with Google. He was doing the design team of that vertical back then. and now he's in Doordash. So my sister connected to him. We were looking for UI designers. Yeah. So she connected me to him saying for if he can give us some other designers contact. Nice. But he was at Doordash and he was like Shiv, bohot boring kaam hai yaar pe.
    It's a company which is established, I need some creative gateway. Yeah. So I would love to do this for you guys.
    Yeah, no, makes sense. So good team also that's coming together. Oh. Perfect. So I'll ping you on WhatsApp or on email to figure out next steps. I'll try to get both Rajat and Akash to join that. And I'll also aim to get a Kishan or a CV who looks at consumer from our ventures team because they are very excited. And as the boomer fund in the country, we haven't pulled the trigger on anything. in this space even at the larger fund.
    Here we've obviously done a lot. Very good man, good stuff. It was great chatting with you. Likewise. Yeah, you all have done Very good stuff for the limited resources and this is about a year and a half in for you. Year.



## Investor material 2026-02-24T13:39:00.000+05:30 

<!-- file block -->


Customer chats
1. One video of multiple user interviews- [Link](https://youtu.be/zHbUB4aWwAY)
1. One video of multiple kids using Pixie- [Link](https://www.youtube.com/shorts/4q6xuXh2IBU)
1. For further details:
  - Playlist of individual user interviews- [Link](https://www.youtube.com/playlist?list=PLVFl2MGAs8dVeFtGHeEnbBvLTdkSJiOAK)
  - Playlist of kids using Pixie: [Link](https://www.youtube.com/playlist?list=PLVFl2MGAs8dVpqgyHQGbBo1O-7_PMjr2z)
  - Raw recordings of 20+ user interviews- [Link](https://drive.google.com/drive/folders/1UTVZpS6z6Zoo9qfE0mj54wyrgemfO8DZ?usp=drive_link)


## Reference checks
### Yashi (Z47) - College Alum Reference - 2026-02-11
**Context:** Yashi reached out in April 2025 about Shiv as a college alum building in AI x Toys space. At the time, Shiv was building in stealth and not looking for institutional investors - just wanted early stage gyaan on fund constructs at pre-seed, angel networks etc.
**What Shiv shared (April 2025):**
- Building something to make screen-free time more exciting for kids
- Audio-only format: 4-12 years
- Early level traction, few POCs
- App + hardware, app goes live soon
- Co-founder is from Amazon Alexa
### **Reference from Musthaqheem Ahamed** - Chief of Staff @Powerplay, ex DB, Bain, SRCC'20
- *How he knows Shiv:* Was a year junior to Shiv in college, worked closely with him at Enactus
**Reference Views:**
- **Intellect & Hustle:** Very sharp, smart, and has the hustle. Strong with numbers.
- **Founder Potential:** A good founder - takes initiative and executes well.
- **Leadership & Experience:** Led multiple initiatives at Enactus, actively involved in campaigns. In college, successfully closed a [XX] drive, collecting warm clothes from everyone.
- **Rank & Performance:** Likely top 5%, but unsure if he's top decile (top 10%). Was among the top 25 or top 50 - need more clarity.
- **Personal Assessment:** Worked with him at Enactus (as his senior) across multiple projects. Had a 15-minute conversation but couldn't fully gauge his caliber.
**Note:** At the time (April 2025), Shiv was raising pre-seed and not looking for institutional investors. Yashi was going to connect him with Rahul over WhatsApp. Kishan was CC'd as they were actively tracking AI x Toys space.


### Ref from [Divyesh Shah](https://www.linkedin.com/in/divyeshps/) (VP Engineering at Meesho; Angel in company; ex Dr. of Engineering @ Google Assistant in Bay Area) 2026-02-24T14:03:00.000+05:30 

Context: Divyesh is an Angel in the company; along with F&F - he has contributed to the ₹50L Angel round

++ Problem statement validation - his child likes the product; has used alts like Toniebox but none have been able to hold the 
++ Good product hooks - likes the concept of story recommendations | This brings him (as a parent user) back to the product
+? Bet on Shiv - has seen him ask for help & grow || Albeit nephew of a college from Meta hence some bias 
+? Mixed review on the underlying Tech - believes TTS has a way to go & pronunciation is still quite Westernized (”South Indian lady from South California”)

Notes:
- He has a kid who grew up in US (2.5 yrs) and now in India (5 yrs of age)
- Resonates with the problem of making up stories each night
- He has tried products like Toniebox
  - Non-personalized
- Betting on Shiv
  - Reaches out for help continuously 
  - Shiv’s aunt has worked with Divyesh at Meta in US
- Has spent time w/ Rahul (CTO) - not an insane hacker but met the technical bar
- Believes they will need to go to USA
- TTS model is still quite raw - pronunciation 
- Good product hooks - story recommendations

<!-- transcription block -->

    ### Action Items
    - [ ] Keep Divyash updated on investment progress 
    ### Investment Rationale
    - Divyash invested based on personal experience with their child using storytelling products for solo play and learning 
    - Found value in using stories to teach behavioral lessons instead of direct instruction - for example, addressing sharing, co-play, and other developmental challenges through narrative 
    - Investment thesis: expects the product to evolve significantly from its current form, values the founder's ability to iterate rather than seeking perfection upfront  
    ### Founder Assessment - Shiv
    - Primary bet is on Shiv as the entrepreneur 
    - Key strengths identified:
    - Has deep understanding of existing user base including retention metrics and user behavior patterns 
    - While not the absolute best hacker Divyash has seen, has solid technical execution capability and good judgment 
    ### Co-Founder - Rahul
    - Spent four years at Amazon Alexa team, specifically working on voice commands for transactions  
    - Divyash validated Rahul's depth of understanding of the voice assistant ecosystem 
    - Strong technical contributor but Divyash would bet on Shiv over Rahul as the primary driver 
    ### Product & Technology
    - Cost structure: Story creation costs 1-2 rupees, making unit economics viable at 299 rupees per month price point 
    - Cost seems reasonable and achievable given current AI/TTS technology landscape  
    - Product successfully drives parent engagement through recommended stories and timely content (e.g., holiday-themed stories delivered proactively before festivals like Holi)  
    ### Current Challenges
    - Text-to-speech (TTS) model struggles with Indian names and accents 
    - Model appears trained primarily on US content and US NRI content, resulting in voices that sound like "South Indian women living in California or New York"  
    - These pronunciation issues are expected to improve with scale 
    ### Recommendations for Growth
    - Divyash suggests expanding horizontally to test with different demographic groups more aggressively 
    - Need to clarify strategic focus: build for Western customers first versus Indian customers first 
    - Funding may be a constraint for broader market testing 



    Doing a thing and listening Yeah incredible number of characters on the Tony's box. Yeah. Correct. in the afternoon and like a I think for kids that age that kind of like alone play time was just wonderful and he's like actively thinking he's actively like taking it in it's not just like passive thing in the background going on I think I actually to introduce him to like, Hey, here's a third thing that we've also used, which was a spotlight thing that actually was animated as well.
    It could move and narrate stories and so on, but all of these were non-personals, all of these Yeah. Yeah using whatever limited creativity i have in making those up and then we also saw it i think with my kid for example i think kids that age are very very curious they'll do a bunch of things that you don't want them to they're not maybe ready to share toys they're not maybe uh uh ready to kind of like co-play together and so on and then how do you kind of like imbibe so we were also doing that thing naturally where okay here's a thing that he did and i want him to kind of like go do it differently So instead of talking Yeah Yeah His sister and brother-in-law, they're in the US at Meta.
    We spent a lot of time hanging out with them together. So I think through that, I'm like, okay, dude, this makes sense. I'm like, and then, so that was my first thing. Now, the second thing was, okay, so I've done a bunch of early stage investments. Yeah. Most of Yeah. My other thesis is, okay, I like the idea as it shapes up today, but from what I've it's not probably going to be what ends up happening.
    And I think they'll probably Correct. Correct. I spoke to him before I invested as well. Correct. specifically I think what really kind of like stood out for me was even in that very first conversation I think one is the core thesis that I just want to build my next iteration and put it out there and validate with real feedback versus go figure what is that product that I want to build and make it perfect.
    I think that iteration cycle, even when I had Correct. He had explored the space really well. I think both in terms of software, hardware, I think whenever I had feedback, so I'm again a hardcore engineer, a hard solider, I think unfortunately the critics come before the compliments. Correct. and as they came right I think the way his ability to take those on his ability to explain years why it is this way and years how I'm thinking about it I think that stood out as well for me.
    And again, yeah, so I think, and then of course, since then we've had a few, a bunch of conversation every time I'm in Bangalore. I'm actually based in Bombay. Right. So I think that gave me conviction in the individual which is super open mind They're not married to a particular version of the idea. Yeah. very very open to just like put a raw thing out there and let feedback take on and then can I treat based on like real and mission because these are LODs listen or die real user feedback versus what he thinks the product should end up being.
    So I think that gave me a lot of conviction. I think at a later point, I spoke to Rahul, who spent a bunch of time in Amazon Alexa, so for context, I spoke to Rahul, I spent my last four years at Google as a Google assistant. Correct. So again, I think I went a little bit deeper into like making sure what is his understanding? What is the depth that he actually has in terms of the ecosystem he's been part of at Alexa and so on.
    I think that was actually pretty good as well. He's probably not like the absolute best hacker I've seen. ever yeah but i think a good kind of like same shoulder or sorry head on the shoulders as well as like i thinkNewest stuff, so I think that Correct be able to do stuff and get stuff done but I think if I was betting between the two, I would bet on Shiv any given day.
    Correct. No, that makes sense and in fact Shiv is also the entrepreneur that we are looking to underwrite here. And you know, just one to two minutes of insight on the quality of tech that they have built. Divya, you said you worked at Google Assistant, Rahul has spent time on the Alexa voice team to help them do a couple of commands that lead to transactions. Have they built something like really good at the back end here because they're telling me the cost to create a story is one to two rupees, which effectively means even at a 299 per month, they will be quite in the GM positive territory zone.
    Is there something magical going on behind the scenes here or have you just not been able to probe this as yet?
    So, it's not deepening yet, but I think that cost seems like it doesn't seem to like, Hey, how the hell did you ever get to that? Right. Because I think so again, I'm sure we've been doing customer service phone calls and we've gone Yeah My pet peeves with the app today is I don't think the model, especially the TTS model that we are using actually does a wonderful job with Indian names Indian accents and so on I think it's actually trained on a bunch of like US content yeah along with with US NRI content.
    Yeah. Where, You can actually sometimes feel like it's that South Indian women living in California or New York. That's the accent that comes up sometimes. Yeah. So Yeah, no, this is very helpful.
    And you know, last question, Divyash, anything about them, which I've not asked you, which you would like to share. So you've obviously spent a bunch of time with them, you've committed personal capital, anything else that that that you feel you use that someone should know about them?
    you Yeah. I think he's and maybe like I think I think what I have liked to see a little bit more maybe faster is I think he's gone very deep with the existing user base yeah right well I think he has a very good sense of like where what my retention numbers look like what users looks like why are people keep coming back why people not coming back all of that And I think that's really good. I think I would like to, and maybe, and maybe like I think funding is probably the significant hurdle for that, but I would like him to kind of like go expand horizontally a lot more so he can get validation.
    from the different demographic groups if need be and I think that's where whether this is built for you want to build this first I mean it can be built for everywhere but do you want to like the western customer first or the Indian customer first has to clarify that. Correct.
    Correct. No, this is very true. In fact, India versus US is a question we had asked them. And no, this is super helpful. Thank you, Divyesh. I think the idea was just to get a sense of what made you pull the trigger. What have you observed about them? What I hear is that there are tech chops. Shiv is the guy you are betting on. He's the kind of person who's reaching out for help. He's a resource generator.
    And obviously there are there is clear customer problem statement that they are solving. You gave the example of your your kid and very fair. and in fact pronunciation and all will hopefully solve itself with scale.
    So it's something that one is sort of comfortable comfortable sort of acknowledging but awesome thank you so much this is super helpful Hmm Yeah One month he had just moved on to something else. and what was useful was the app for the parent kept on pulling the parent back with also a lot of like recommended stories now that we are in India I think during a bunch of the holidays Yeah I want to be the lazy parent.
    So I want like stuff ready, available, I get this feed, "Hey, I want to teach you about Holi, there you go, three days before Holi, here's a story that helps you out." Yeah some of the proactive hooks to bring people back pretty well as well.
    Very interesting. Perfect. Awesome. Thank you so much, Divyash. This was super helpful. And I think you might be running late for your next meeting. So I appreciate you taking the time out. And I will keep you in the loop on progress that we make here. But thank you. This was super helpful.
    Sounds good, if I can get any help let me know Absolutely.
    Thank you so much. Thank you so much. Take care, Divyash. Bye-bye.

---
## Inbound Pitch - Shiv Bansal - 2026-02-11
**Source:** Inbound via Rahul - Shiv Bansal emailed directly on 11 Feb 2026
**COMPANY OVERVIEW**
Pixie - "The first AI a child meets"
**Problem:**
- As AI increasingly shapes how children learn, existing tools aren't designed to be safe or usable for kids
- Parents need a controlled way to introduce AI early
**Solution:**
- Voice-first alternative to video content for kids
- Parents and children generate personalized audio stories using child's name, friends, characters, and topics of choice
- App is live with English, Hindi, Spanish, Chinese support
**Target Segment:** Children aged 3-6
- Build trust early, form habits, grow with them
**TRACTION (as of Jan 2026)**
- MAU: 620 users
- Repeat users: ~60%
- Retention stabilizes at ~15% by week 4
- Retained users stay active beyond 6 months
- Usage has doubled over last 5 months
- Top 5% users spend ~11 hours/month
- Top 1% users spend ~18 hours/month
- Usage is "child-initiated rather than enforced" (from Shiv's email)
**FUNDING**
Previous Round:
- Angel round led by Divyesh (Eng. Lead, Meesho)
Current Raise:
- Raising $1M
- Use of funds: Deepen product, scale repeat usage, launch in US, begin monetization
**KEY CLAIMS FROM PITCH**
- "Short parent feedback video describes clear child outcomes and willingness to pay"
- "Usage has doubled over the last 5 months"
- Deck was shared (need to check for link)
**FOUNDERS**
1. **Shiv Bansal** - Co-Founder & CEO
  - Background: ex-SRCC, PE
  - [shiv@mypixie.in](mailto:shiv@mypixie.in)
1. **Rahul Agarwal** - Co-Founder & CTO
  - Background: ex-Amazon Alexa, IIT Hyderabad
  - [rahul@mypixie.in](mailto:rahul@mypixie.in)
**INITIAL QUESTIONS FOR SCREEN**
- What's the monetization model? Subscription?
- Unit economics at scale?
- How defensible is this against big tech (Google, Amazon Alexa)?
- What's the US launch plan and timeline?
- Competitive landscape - other AI kids content plays?
- Content moderation / safety mechanisms?



## To Do 2026-02-24 

- [x] Consumer Collective
- [x] Boundless
- [x] Shyamal
- [ ] EMoMee
- [ ] Answers AI
- [ ] Nakshatra - Bunny Engineering
- [x] Mohit Sadaani



## MPE w/ @CV, @Trinika Kaushik, @Yashasvi Madhogaria and @Aakash 2026-02-25T13:09:00.000+05:30 


### CV: WM 

Spikey:0
++ smart folks and may figure out and compound 
?? To build in space need hacks guy with growth marketing or content exp; Both have neither  
?? Tech guy had ok refs but unless some tech moat - not v interesting play


### TK: WM to PWC 

Spikey: 0 
++ decent seller and IQ 
++ First principled
?? Inside out and no great learning from time at Alexa & other competitors
?? Not customer backward and didn’t hear any deep consumer insight 
?? Doesn’t seem like have talked to a lot of kids/parents - because each age group behave v differently 
??  Backing statements and insight based on power users which are 10 folks total?


### Yashi:




- Alexa Plus w/ Thumbtack is live in US - voice actions to get professional work done


### AI notes
<!-- transcription block -->

    ### Action Items & Next Steps
    - [ ] Investors to debrief internally and provide feedback to Shiv and the team 
    ### Product Overview
    - Pixy is a voice-first, child-safe AI storytelling app targeting children aged 3-6 years  
    - The app generates personalized audio stories using LLMs and text-to-speech models, allowing parents to customize characters, settings, and life lessons  
    - Core use cases include bedtime rituals (60% of usage occurs post-7pm), mealtimes, and drive times   
    - Recently integrated with Alexa to enable children to access content independently without needing a parent's phone 
    ### Current Traction & Metrics
    - 650 monthly active users (30-day rolling period of users who created or listened to content) 
    - Top 1% of users spend 36 minutes per day on the app, top 5% spend 22 minutes per day, and top 10% spend 14 minutes per day  
    - 70% of users are from India, with additional users from US, Australia, Europe, UAE, Canada, and Pakistan  
    - Customer acquisition cost (CAC) ranges from Rs. 27-40 through influencer collaborations   
    - User acquisition primarily through word-of-mouth and limited paid social media campaigns 
    ### Market Opportunity & Strategy
    - Initially considered both India and US markets, but decided to pursue a global approach given AI's ability to scale across languages, accents, and cultures 
    - The founding insight came from observing a 4-year-old nephew glued to screens, leading to the creation of AI-generated content that the child enjoyed  
    - Key factors supporting the opportunity: high lifetime value (LTV) potential by capturing children early, concentrated target audience (parents in WhatsApp groups enabling viral growth), and increasing parental spending on child development   
    ### Hardware vs. App Strategy
    - The team initially built a Tony Box-like hardware device and tested with 15-20 users 
    - Pivoted to app-first approach due to low willingness to pay upfront (Rs. 4,000-5,000) and uncertainty about long-term child engagement with hardware  
    - Hardware production cost would be around Rs. 2,000 at scale, with potential retail price of Rs. 5,000, compared to Tony Box's Rs. 9,999 price point 
    - Current strategy positions a potential speaker device as a companion to the app rather than the primary product  
    - Advantages of app-first approach include faster scaling, ability to add discovery features, quicker iterations, and avoiding upfront hardware costs   
    ### Competitive Landscape
    - Tony Box (Europe-based competitor) charges $100, has reached a threshold in Europe but growing well in new US market with $1B+ revenue  
    - Pixy's advantages over Tony Box: no licensing costs (Tony Box pays Disney and other IP holders), highly personalized content generation, and lower potential device cost  
    - Multiple Chinese companies are targeting the same space with LLM-powered storytelling apps and speakers 
    - India-based competitor Foxy previously attempted similar model but pivoted to language learning due to retention and monetization challenges 
    ### Key Investor Concerns & Challenges
    **Retention and Novelty**
    - Investors raised concerns about novelty factor wearing off after 3-4 months, similar to other children's products  
    - The team argues that establishing bedtime/mealtime rituals and continuously generating new personalized content addresses this issue   
    - Investors questioned why only a small percentage of the 650 users are power users at this early stage when founders could personally engage each parent 
    **Age Progression Challenge**
    - Major concern about retaining users as children age beyond 6 years old   
    - After age 5-6, children's schedules fill with extracurricular activities, reducing available time 
    - Parents increasingly prioritize reading physical books over audio content for older children  
    - The team's strategy involves adding features like language learning, concept explanations, and social features (friend connections, co-creation) to retain older users   
    **Form Factor Questions**
    - Investors challenged whether higher retention could be achieved with a device that doesn't require parent's phone  
    - Concern that the 60% post-7pm usage window requires extended parent phone access (30+ minutes), which may not be realistic  
    **Balancing Stakeholders**
    - Founder identified the biggest worry as maintaining balance between parent satisfaction (payer) and child engagement (user) as children age and develop independent decision-making  
    **Strategic Clarity**
    - Investors questioned whether Pixy is a content company, LLM guardrail company, or companion app, noting the need for clearer positioning   
    - Investors emphasized the importance of offline retail presence (especially for holiday season) and building ratings/reviews for hardware success in the US market  
    ### Business Model Evolution
    - Currently free app with plans to monetize 
    - Future revenue streams include potential device sales and upselling premium features to engaged users  
    - Vision extends beyond storytelling to broader educational use cases like language learning, concept explanations, and general knowledge  
    ### Investor Debrief (Post-Meeting)
    - Investors rated the founders as "weak, not PWC" with concerns about lack of strategic thinking and deep customer insights  
    - Specific criticisms included being "highly inside out," not learning from existing players/competitors, and over-relying on metrics from very small sample sizes  
    - Team viewed as lacking growth marketing experience and content expertise, with unclear spike/differentiation   
    - However, investors acknowledged the opportunity is interesting and warrants a follow-up meeting  



    So there was a tech limitation then, at least that's what we were told. But with the coming up of LLMs and the new Alexa Plus, I was there in the team that was trying to develop integrations with Thumbtack, which is like an urban company equivalent in the US. And they're working flawlessly. So it's live in the US, the Alexa Plus thing. And reservations for professional services, reservations to restaurants and all are working quite well.
    Yeah. So we got one assuming that it will help the sun but all it did was f*cking play baby shark on the beat so it went from Amazon MX after that.
    In India the features are still very limited.
    Yeah, it's horrible. Okay so Shiv you've sort of looked at markets. How did you convince yourself into choosing this opportunity?
    So the thought has beenCB that. With regard to TAM, it's a big TAM out there, right? Because it's not only, initially when we were trying to think whether we should be an India-focused player or a US-focused player, that's when we realized that we want to go to a larger TAM, going with the global approach would be the right way. And given the way consumer AI is right now evolving, scaling to different languages, scaling to different accents and cultures becomes much more convenient, right?
    With a few tweaks here and there. That significantly increases our time potential across the. And what's the discount?
    What's the opportunity cost? Like, I'm sure you had four or five ideas and motion pages and Excel sheets built on what markets are like. What did not make the cut?
    So, um... So, you are right, when I started off, this was one idea, this actually came out very organically. So, when I was visiting my sister in the US early last year, There I saw my four year old nephew, Rio, glued to screens. And the only time he used to take his eyes off screen is when my sister used to tell him stories. and Because she was a PM at Meta, she did not have a lot of time to devote to him.
    That's when I created a content using different LLMs and text-to-speech models and he really loved it, right? Like, um... That made me realize that this is something that we can build out. But like you said, I definitely pulled out different sectors with the spreadsheet analysis of TAM, potential to pay, etc, etc, to come down. I was not really confident whether I really want to pursue this or not.
    What really sold me CB was The possibility of increase LTV out here, right? If you get the kid earlier and build a trustable brand with that child, you can really keep monetizing and they'll keep upselling, you'll keep upselling a lot of things to them, right? Second is with this target, The TG that we're targeting, which is parents, they're very concentrated. That reduces our gap. So if I want to reach out to, let's say, 200 parents, They are in WhatsApp groups.
    I can just send it to them and they'll subgrade it very quickly. So Word of Mouth is very big in this category, right? And with the changing landscape, most of the parents are having two kids at best. So now they are focusing on their kids and spending a lot of money on their kids. If they're seeing something which is able to bring in those child outcomes and the kids are enjoying something, they would be willing to pay up for it.
    So it is a combination of a lot of these factors and a lot came from having three sisters around me whom I saw they are struggling with this and they were willing to pay as much as possible for something that solves their issues. So yeah.
    Why not just buy them a Tony box?
    So, to be honest, we did, when we started off earlier, we were making a very, we actually had made already a box exactly like Turing Box, right? We gave it to 15, 20 users and then we realized thatPhil? Willingness to pay upfront such a big amount is very low. because With toys, a lot of parents know that what kids will enjoy after a month, they don't know, right? So they wouldn't want to invest 5,000 bucks or 4,000 bucks upfront.
    Only to realize that after a month it is lying somewhere in the storeroom of their house. So we could have definitely scaled that product as well, but that will reduce our time significantly. And that's when we were also working on our app and that was taking off very well. And then we focused on only building the OPC app.
    Got it. I haven't been following Tony Box. Has the revenue declined recently?
    They definitely have reached a threshold in the Europe market, right? But since recently entered the US market, there they are doing very good.
    They are revenue, overall revenue is--At least till last year they were doing well. It's one point between a million dollars or so. I could be wrong. and they were growing decently well as well. So explain to me what your current form factor chosen is and is that the final form factor or does that change with time?
    So that's currently the focus is on the taxi app, right? That will be the focus right now. But users will tell us more about it as we move forward. What we're trying to build, I'll show you the compactor. I don't know if you got a chance to look at the demo video.
    I did look at the videos that you guys sent out for them.
    You did, right? So Pixy app is the app that we're trying to build. The thought is to make a voice-first, child-safe AI that your child meets and grows with. Since we are targeting the earlier age groups right now which is 3 to 6. Content consumption is very big in this category. They consume content while doing their bedtime, doing mealtimes, doing drive times. With Pixi, we have been able to see a change towards Pixi during those moments, right?
    So that's how it's evolving. Yeah.
    Got it. What age groups are you targeting?
    We're targeting 326. Right now 60% of our users are in this bracket but we have few users who are 8, few power users who are 9 years old and they are still enjoying the app. But the highest power user that we are seeing, top 1% top 10%, 95% of those top 10% users are in 3260 road traffic.
    So you have, is that right, about 620 miles? Is that right?
    So 620Mao is the users who are actually doing an activity. It's 6:50 now on a rolling period, right? On a rolling 30-day thing. So anyone who's come on the app either created a content or listened to a content, that's 650.
    So what is the retention? What are the metrics that you are using? What is D7? What is D30? What is the time spent?
    So, minutes of time spent changes as per the As per the percentile users that we have, right? Let me just pull this out right now and show it to you.
    So if you see this, Can you see this graph?
    Yeah. So top 1% users that we have a CV in Chan. They are using the app for 36 minutes a day.
    But what is the top 100%? There are 6 people. If it is 650, what is that number?
    Yes, if you see 650, there are 6 people. Hannah? Hence to get a more broader picture, we can look at top 5% or top 10%. Right? The top 5% is 22 minutes a day. which was 10 minutes a day in September 25 Great. for 10%, top 10% is 14 minutes. Ready? And if I look at the overall cohort retention, This is the retention of the app after December. This is that.
    And this is India behavior, extended family behavior or you've acquired them on Meta or something?
    So, these are not friends and family because it's a very limited circle that we... So, friends and family was in... At the time when we launched the app, which is in September, But now it's mostly people, random people out there, from different geographies mostly from India because that's where we have been able to test our product so far So 70% of the users are in India. Balance are... From the US, a few are from Australia, a few are from Europe.
    We have five, six users in Pakistan who are using the app. Canada is also a very good market for us. UAE is a big market.
    What cac are they coming at?
    So, um... Like I said, mostly what we've acquired is from word of mouth and through offline channels. Only in December and January we did four collaborations with social media influencers. They just had posted a story on our app. And that is coming at Rs. 30 CAC right now to us. across these four story posts that had gone out.
    I can just share the screen and show it to you.
    Trying to keep a track of... Can you see my screen? Yeah. So let's say in 28th of Jan we did this with This influencer called Shivani, right? She charged us 6000 bucks for one story. out of which 222 accounts were created and 85 of them converted. So CAG for account creation was 27 rupees. Right, similarly for Ankita, She charges 25,000 for three stories, so 8,300 per story. We got two 20 account creations So, Rs.
    40 cax came from there.
    Hi Gary man. How are the users using the app? Partly as a parent you will feel guilty. That you are not going to do it. You just want to hand over the phone. Second is It's usually not the parents phone, it could be the grandma or grandad or it could be a nanny whose phone is being used. It doesn't work in restaurants because it's on speaker mode, you're not going to give your phones to your kid anyway.
    And most of the time the parent is kind of using their phone also right and this is like a large if you say 30 minute type mod. It's a very large time period for the parent to be disconnected in the world that we're currently unfortunately living in. So how are you using it? What device are you using? Correct.
    So right now if I look at all the time duration when our app is over, right? 60% usage is happening post 7pm. Right? So I'll tell you exactly what the usage is. After 7pm, most of these parents have a bedtime ritual. They have this one hour when they are relaxing with their kid. Just changing them into their night clothes, comfortable clothes, right? And once you do that, There's a one hour where they are interacting with their child.
    And mostly it's the story time that they enjoy. Right? So in that, the parent sits with the child. "Okay, son, what story do you want to hear today?" "You want to listen to it, listen to a story on a unicorn, on a garbage truck or a race car?" The child says, "Mama, I want a race car." Then the mother asks, "Okay, son, who do you want in the story with you? Do you want your friend Akshat or do you want your friend Meera?" So then?
    The parent then slides in a lesson that she wants to teach her, teach the child. Let's say the child today got really angry when something happened, right? So the parent sneaks in, angrilyYour control as a lesson. An instant audio story gets generated, which the parent locks the screen and both of them are listening to it now. Now, Each story is five minutes long. But the engagement that you're seeing is 36 minutes, right?
    The reason that's happening is because There's a playlist that is being maintained. All the previous stories that you had created are still there. So it keeps playing one after the other. Parents then set a sleep timer and then it closes itself after half an hour or an hour. Right. This is one user behavior. Second user behavior is, let's say today I don't have time to really sit with her, with my child and create a story.
    I give my phone to my child. and my child goes through the app across the discover section where there are a lot of stories that are pre-generated. The child chooses the story that he wants to listen to the images that are there on the cover picture of the content. So the child has certain favorites to content that the child wants to hear, they select and they're listening to it. right, so this is the bedtime experience, but the balance use cases which are primary, second most important use case for us is meal times.
    When the child is eating thrice a day, parents sit with the child and they put on pixie and both of them are listening while the child is independently eating his food. Third main use case is drive time. When they are going to a shopping mall or when they are going to a friend's place or when they are going to drop their kids. This is a big use case in the US where a lot of parents are going to drop their kids to school, get them back.
    They put Pixie on their car and the entire family is listening to Pixie in the drive. That's how they're using the app.
    What is something that you've learned that you cannot would work, but didn't work.
    Couple of things. We launched a mode where you can record the story in your own voice. So after the content is generated, you have a few options. You can either record it in your own voice, you can read it in dark mode, or you can listen it in the voice that Pixy has. We thought it would be a big seller But turns out very few parents want to record long stories of 5 minutes and they just want to read the entire thing.
    So that feature is being used very little.
    I did not worry about the novelty factor sort of wearing off. I had this personal problem with my kid as well. It just wears off. After a while,. And then suddenly he said, forget it, I'm done. And then move on. And that happened with almost every form factor that we did. worry about that and what's the way out of that?
    So, can I get a purple drink? Okay. Thank you. So, there are two things out there. First is that... Kids want something which can be a part of their routine. If you can make something that is a part of their routine, Then it will not be a novelty thing because aaj man kya robot, wo globe use kya, kal nahin kya. But if it's a part of a routine that every time during bedtime we do this, every time during mealtime we do this, then there's a practice which is established and you keep doing it.
    That's one. Second is that with the advent of YouTube etc kids are now accustomed to some new things. Great. And if we have a static app where there are 5 stories, then that's not going to sell. We are so, but with AI we are able to give the control to the parent to generate as many content as you want. Today the child went to a birthday party and he got a dragon toy. Now the child wants a story on the dragon that he got.
    Immediately the parent generates a story on that dragon. Newness is being maintained by the parents who are generating content and also by the discover section that we have wherein let's say today is Mahashivratri right? We put up a story on Mahashivratri. There was a President's Day in the US. We put up a story on President's Day. The child goes to school, he sees President's Day happening. But he does not know what is the real history.
    When he comes back to his house, "Omai is lechera beta, let's listen to the real fact we have precedence day." Childhood Connect is good. That's why we make it President's Day.
    Isn't this a high fatigue use case? It happens, it'll happen, for four or five days. And then eventually something would happen, right? The app kind of, it has a certain tonality to it, it has a certain structure to it. You would have to figure out something on the back end that keeps it concise enough to be safe for the child and correct for the age group. Which results in some form of similar loops and it'll work.
    I'm not saying it won't work for three, four months. It will work for three, four months. And at some point in time, the parents will either be Honestly, if you want to know about Onam, then you go to YouTube. and there's this whatever that explains visually as well as from an audio basis, right? So in your view, What makes the retention like totally sticky? And I agree to some parts around mealtimes but dude all of this, you guys have kids?
    You guys look too young and handsome to have kids. So I'm gonna take the leap of faith and assume you don't have kids. -Be dissolved. It is a constant battle, so why does a Unfortunately, YouTube work, because they graduate on the character. And then they figure out, like right now my kid is, like he was infatuated with Harry Potter for a year and we've got the entire thing and suddenly he's on Tintin and it's all blue screen particles everywhere, right?
    That's all I hear now. So he chooses the infatuation and moves himself along the, I haven't been able to get him to stick with something for... More than say three to four months. So this is a format, this is a story format. How would this-how would you retain them, like, six months, one year into the future? Like, it just doesn't-These rituals barely stick.
    So, um... Completely get your point right. I think for 100 users that we acquire, Maybe for a lot of them it does not. They don't have a ritual and it won't stick for them. And hence you don't see the first week drop off. Right? But there are increasing, more and more increasing number of parents who are trying to establish a bedtime ritual or trying to establish blocked TV times that okay, in a day you'll only get one hour of TV time, right?
    As and when more of that awareness is increasing, people are trying to find alternatives. But how will I keep him engaged? Right? So what is the alternative? This is being an alternative for them and they are using it. using it so frequently.
    And Shiv, why is this chart not like I can see Kanak and-Kushal, why is this not at 50 people, right? Because you are at the scale where you could technically call every parent. and figure what's happening. Why isn't the percentage of power users significantly higher? This is such a ritual, especially in such a small number. You can sort of drive a lot of this as founders yourself and keep launching stuff.
    Why is this not a higher percentage? So, um, what I'm saying is, why aren't 50 people part of this? Okay, this is me. Fight.
    She's one of the power users. She used the app for 23 hours on August 25th. And she was having some family issues, so it went down. And then it increased to 26 hours in November 31 and 32. As in when your child, when it's introduced to you for the first time, it's a new thing for your child. They are not accustomed to listening to content, they are accustomed to watching content. Okay. As and when this becomes a ritual, then we see an increasing usage of the app over the months.
    So, um... That has been the experience so far, right? Um, yeah.
    And why not just solve, take out the use case fully of the mobile phone and put a device on it and present the screen capability.
    So like I said, we have that device with us, right? But are you saying that we should, why are we not doing only device?
    I'm saying you're basically saying in the 600 people you would have liked to see at this stage Our users, they were at a definition of percentage, but at least a higher percentage of people using for a long period of time. Would that have gone up if it was a device versus a phone?
    So, um... Definitely it would have gone up if there is a hybrid possibility. Right? For example, with kids, if they like something, they want to get it again and again. Right? So with us right now, if them kids, so every kid has a favorite content pool that they have, right? Now, but that to access that pool they depend on their parents phone. If mom and dad are around then only they can access. But mom is busy with her phone, maybe mom is not around she's gone to office.
    So how will the kid access that content? Right? That's the primary reason why we have integrated with Alexa now, wherein the kid can just walk over and see Alexa open Pixy and the content will start playing from Pixy while the parent is not around.
    Okay, and device how much does the Tony box cost?
    It costs 9999.
    And what is the US? You are telling me the current number. US. And how much is the cheapest version of a Tony Box Imitator cost?
    So when we ourselves made it, it costed us around 5000 bucks. But not at scale. At scale if we do it, it will cost 2000 and we will sell it around 5000 bucks.
    So why isn't the opportunity saying, you know what, Tony Box is limited in their content production. limited in their IP games. And they're required to pay a heavy royalty to Disney. and whoever else for what they're creating and they think of themselves as a content company. In your case, you're saying right now the Y now is an element in some form and you can generate these other highly personalized stories.
    The disadvantage is it probably needs a Wi-Fi access. And you need to make sure there's more controls. But is there a cheaper way to just disrupt Tony Bob's side of the game, basically? There's a device, it's much cheaper. There is no IP cost. It's almost personalized. It doesn't have to be supported, but that's for the. So why not just start there?
    Like I said, the initial point, which was that parents are hesitant in paying upfront a heavy amount. But once they see that the kids are enjoying this content, we can definitely upsell them certain things.
    What is the price point you think you can operate at? Tony Box you're saying is about $100? $100 yes Can you sign it for $50, $60?
    Yeah we can because there will be no licensing cost for us.
    But 50-60 dollars is the price of a Skillmatics car. I mean it's two Skillmatics car thing right? I am assuming they are selling 20-30 dollars car. I could be wrong. From what I remember at least they were selling 20-30 dollars car thing. It's not a large expense. Skillmatics car is a good deal. Like we just buy it.
    But there's a lot of... One, they've not done very good in India.
    Either Skillmatic or Meeko, right? One is BMF in the US. I'm not talking India at all. I'm simply saying US. Why is the US saying, "There are 20 boxers, I will kill them in their own game, my device will be cheaper, this will need Wi-Fi access, and this will be highly personalized." Couple of reasons, right?
    One is upfront cost. Second is that it can't-When you're doing the app, There's a lot of things that we can do along with as the child grows. For example, right now you're understanding life skills like sharing, teamwork. But we have kids who are six-year-old, seven-year-old who are trying to understand concepts like what is the evolution of human from apes, right? Evolution of a butterfly. The parents were trying to use this to learn a language.
    So a lot of use cases that are possible in an app which is not possible in a hardware-only product. Second, third thing is that making a speaker is not defensible at all. And a lot of parents take it as a toy. "Dude, if there's any other rip-off of China, I'll buy that instead." There's no solid defensible product possible when you build just a hardware thing.
    Because we were able to build that exact hardware in 4 months with just 2 of us and 1 more person So your argument here is that Your discovery layer needs to be important enough for it to be time-is that what you're saying? Your app adds a discovery window to increase retention? Is that your argument?
    Exactly, right? One of those because once I have hooked the user on then I can upsell them that hey if you want to increase your child's usage why don't you buy the speaker where your child can independently access stories without need of your phone or an Alexa.
    What is the monetization of this? Sorry? Monetization, how are we thinking about in the US?
    So, sorry, Rahul, what you were saying? Yeah, I was saying that we're trying to make it like the speaker is more of a companion device for the app rather than the app being a companion app for the device. Because with the entry cost being global, the apps can be scaled up much faster. There's a lot of quick transitions we can have. We can update the app much quicker. The hardware that goes much slower.
    The interaction points that we're mentioning, right? Tunis has just one interaction point to play the audio. We're able to replicate that in a month with small Arduino or Raspberry Pi and other aspects of it and make it a form factor that works. But to think it from a long LTV perspective, just the hearing perspective is not enough. There'll be more interactions, there'll be more form factors that will need to come in.
    And so the speaker being a companion device makes more sense than the app being a companion app for a device that we'll try to set. The power users and the users who use the app a lot are stressed about their own phone being used in that sense. We have opportunities where they can use it in Alexa, they can use it over any Bluetooth speaker, or in the future this companion device can also come into their lives.
    Do you guys see yourselves as aOkay. Content creation company? Or do you guys see yourself as an AI companion?
    So I would say neither. I will tell you what the thought is. To answer your latter point, AI companion, see right now the way the world stands, we adults are not comfortable if we want an AI companion for ourselves. Okay. and let alone us exposing an AI companion to a child.
    I'm not saying that you should expose a child to LLM.
    You will always have a guardrail. I don't want, I don't want, right now principally, maybe we are not right now aligned that we would want a child to be emotionally engaged, dependent on a companion that we are building. Right. So we would, and second thing was on the content based. Like I said, for three to six, content consumption is very high. Hence to hook them early We needed something that they are already used to.
    As we keep growing, the way you are interacting with the app, evolved as well. What is the core of the company you are building?
    I went to China and met four companies who are either launching an app or a speaker exactly targeting the US. Exactly with this LLM and DTS and all that on top. So, we will do everything here. In some form you are saying, my question to you is, are you building a content company? Are you building a great LLM guardrail company with the right wrapper on top? Are you building a GK company? What is the core skill set you guys have to build within the company to succeed against the barrage?
    We've been positive on this for a while now. So to your question, can something be built? Stay back in the school. ...safe for you and that it can get killed.
    But what is the form of the company? So the underlying thought isStevie? We want to build a company wherein the child can So we know that AI is going to Adapt. and help in a lot of use cases. But for a child, right now parents are afraid of giving them access to these AI tools because A it's not safe and B it's not user friendly to a child to independently access. So we want to build a tool where the child can early on get access, understanding of how the AI, the AI ecosystem works.
    And then... grow with that child, maybe after 6 years old, 7 years old they are trying to understand concepts in a simpler way. Here what is photosynthesis, right? So be a part of their journey as we grow. Maybe in a very entertaining and edutaining way. You are getting to learn and hence the payer who is the parent, they are happy. But you are also enjoying it excitedly so you as a consumer are also happy about it.
    Why do that shit? You could make the, for all of my questions, you could also take the absolute reverse stance to say I fucking don't care after 6 years old. I care about Theodore Six and I'm going to monetize the shit out of this segment. I'll do what I need to do with maybe a device, maybe an app, maybe just a story format. And that's large enough to get built on, one version. Second question. Can you name?
    Can you give me a few examples? Red. A 3 to 5 year old has used it and that same child in 5 to 7 years has used it and by now you can do any category except maybe footwear. Can you think of use cases where this migration is even possible?
    So far CV without the advent of AI that was not possible because you had to do a lot of work to cater to different age groups. But now we are able to cater to the user as per the age, as per the geography that the user is in, and as per the language that the user speaks.
    I am not saying AI cannot do it. The kids are stupid because it's not cool. So coolness is the problem. I was three years old. It's not cool anymore. This one, Coco Maran is not cool. He said, way before the age of Coco Maran died. Because whatever, kids also talk. Social circle of energy. So it just stops being cool. It's not that it's not useful.
    I'll let Rahul answer that. I think we were discussing that a few days back that hey, the app that I used to use, will my dad use that app? No, right? So yeah. you The technology, the company behind all of these would be the same. If the concept about super app, if it does not work, that is one fear that we have already. Like you've seen that with Zomato and Swiggy also. Swiggy being a super app versus Zomato splitting it across Blinkit, Distrate, and Zomato itself.
    Both of the concepts work. We can try out which one works. But with that in mind, right, that was one of the things that we were covering when we were trying to think about whether we should be adding features related to concept learning and language learning or call it something else, the engine and the company behind it would still be the same.
    That's fair. But then the other way to look at it all is to say, "Your meal ritual ends at 3:30."one, two, three, four, four. The kid is still ritualized, then the parents also have to answer some questions.
    3-5 years the rituals work beyond that children themselves are excited about learning they grow out of the rituals and all I care about from 5 years old for my child is that he or she should be able to read a book I actually don't want him to get into an abaddon I simply want them to, like reading is what matters.
    I will stop all electronics. In my house now, he's not allowed anything except for a smartwatch that calls. He's seven years old. Swapping. Cut. suddenly the app becomes irrelevant. So your super app concept which is stuck in a psychological segmentation of meal time entertainment plus edutainment has now shifted to kind of nothing. Acquiring the user almost scratch to get them into this companion/gkteacher/tellmeabouttheworldconcept whereas there may be another app that's already releasing that may just capture the 5-7 year old and kill it So, um, To answer your question about reading light, we right now have a lot of power users who are in 6 years as well.
    Let's discuss the day of a child. If you have, let's say, You come back by around 2:00 PM, right? Or for audio, because right now it's 1:00 PM or something, right? Then you have a few classes that your parents send you to, maybe a skating class or a drawing class or a piano class. Then you have approximately 5 to 6 hours inside the house where you are free to do anything you want. Because in this era, you don't have homework.
    It's a lot of them to do. So during that six hours you might use You would as a child want to engage watching YouTube a lot as much as possible. But your parent tells you, "No, now it's reading time." So you read a book. You read your storybook that I got you. See, maybe you do that for an hour. But you still have five hours left Whereas the parent needs to keep him away from television.
    That's where Pixie is coming into picture, where the parent is happy to use Pixie and engage yourself and the child is happy that he is enjoying using it Just to push back on this, like what my childhood was and what I'm seeing around, when a kid is like 6 year old or 5 year old, they usually go to extracurricular classes, right? Some are going to karate or... So they don't really have that 5 hours, they maybe have like 1 to 2 hours delta.
    Because kids, parents also want to fill their schedule with all the classes possible in the society. Correct Correct in 6 years and then reading is one of the aspects you definitely want to cover because obviously Yes. In like six to seven year age group. If the parents want that, okay, reading is my priority or exercise is my priority, and then the kids will move out of that storytelling ritual, storytelling, the time they have.
    So then how do you plan to capture that segment? Or instead, you can just stick to 3-6 year old as CV said, that's also completely okay. But I'm just saying that if we think beyond 5-7, then their day looks very different. So how do you plan to capture which part of the day?
    Do you need it? Is the primary question that we are asking. Do you need it?
    So right now, the way app does, we have a lot of users who are in seven, eight, nine year bracket as well. It's not built specifically for them, but they're using it and they're happy using it. But to get more users in that age bracket, we have to decide what would be the features that we are building out for them. I agree. I'm saying like you are in parallel. In parallel, somebody will solve that in the same year.
    Everybody will-like all entrepreneurs will go for this market in different age groups, right?
    So the thought is that if we have captured you early, Easy as day, we will crack 3-6. that's the easiest thing done right now we are getting a lot of good retention in that age group right so usme aur zyadar compliate karne ka scope humlog kar sakte hai soch sakte hai right but our thought is if we are why do we want to Let Arch and I lose after six years. Why do you want him to go away from PixyApp while he's already there hooked on to PixyApp?
    If we can cater to him, why shouldn't we do that? The focus right now is 326. But as we evolve, we keep seeing, experimenting with different use cases, How do we ensure that they don't graduate out of PICC? Yep. Language learning is one, right? One more thing is that that age group, They enjoy showing off, discussing with their friends. So what we have done for that is that, let's say we have a section in the app where you can add a friend, add a loved one.
    I don't know if you've seen that. You can add a friend, you can add your parents, right? So many kids are adding their parents to their friends. So now what we have done is, let's say I add, I have a child whose name is Rahul, you have a child whose name is Yashashvi. You have, I have connected both the accounts and the moment I create a story with you as a friend, you get notified that hey Shiv made a story with you, do you want to hear it?
    So, social circle is being formed there. They are enjoying that I listened to the story that you made with me yesterday. You can co-create a content as well, that hey, together let's co-created comic book, let's say. Right? Yeah. Got it.
    Any other questions? Okay. Sorry.
    Just one last. Shiv, what is your biggest worry right now? I think you mentioned that one is form factor. What else in the next 12 months, what is one thing your idea is like this has to work? Or like if this will not work, maybe you have to pivot or something.
    So one thing which I discussed with Rahul as well yesterday when we met is that as we grow to the older age groups, how do we balance this because there are two stakeholders here, right? One is parent and one is the consumer who is the child. Right now, the equation is very much balanced because child is enjoying listening to stories in which he is there, his friends are there, characters that he enjoys, right?
    And it's unrestricted entertainment time that parents approve. What? Parent is happy because it's screen free, they're learning vocabulary words, they're learning life skills, you know? But as we move Elder in groups The equation might be, we might have to focus on the child more and the parent less. It was there they have their own decision making capability there. They have their own Factors to consider So how do we maintain that balance is something we have to...
    Think about when you move to that category. Right here, you're fine. Okay, so, uh...
    If there are no more questions, so Shiv and I will come back after debriefing. I know I pushed you guys into a corner, but that's only because we've actually been very excited by this category in general. We've just been-We've been on the fence for more than a year now to say this is going to get built. We don't know what version of it gets built. There was an app called Foxy in India that then pivoted to language learning.
    They just couldn't get-Enough. from the parents and keep the double retention or monetization. The caveat is they were focusing on media and the All of that hadn't reached the level of sophistication it has now reached. It did not cross the uncanny road. It just kept getting stuck there. So yeah, I think Opportunity is interesting. We'll debrief and come back. There are multiple things to consider, the same questions like model kya hai, form factor kya hai, competition kya hai, and how does this play out.
    So give us some time and we'll come back. Please get back to touch.
    I just have a few questions. We want to understand in your experience so far, which are the apps that we've seen in your portfolio?
    The work that we have done on We met a bunch of companies and did some research. Overall All lo and behold that focusing on a certain age group of the child is future. and there is a real value to be unlocked and real profit pools to be built especially in the US where you don't have a patent question. Skillmatics attends to a certain age and it does well. Tony Box does the same. We think there is some value to that.
    And maybe you guys will also figure that out and decide. Like what Rahul was saying, completely different. And the insights are different. And the use cases are different. So We came out with the following provided you have a reasonable AOV you could sell a device into the US that requires about 1.5 years of working on ratings and reviews which is the single biggest decider and then you have bumper OND immediately after the bumper OND if you have a hardware device then you go offline.
    There's a holiday season is where everything is bought in the US for toys.
    SPEAKER 1: Oh, yeah, December, the Christmas season, right?
    SPEAKER 2: And once you have that good number, then you go to these offline stores to open up. Once that also opens up, you get-that's a real for folks to get out of. So we didn't walk away completely negative on the device model. We understand there's a cost associated to it as a travel.
    On the app model, That the learnings are The overlap of the parent being free and does not want to use the phone And the child is free but the parent does not want to engage with the child.
    Just decreases with age, right? Because the minute you go beyond 5 years old, I can't give my phone to my child. He can do anything with it, right? In fact, he immediately goes and buys something for some reason and he gets stuck on a free. But it takes him there, right? So I can't, there is no occasion where I am free and he is free and I have given him my phone. I used that. at this age, right? In three to five, that does happen.
    So I would... Our learning is the more the form factor ties into that specific age of the child, the higher chance you have for speaking. Because some of these apps run the risk of-If you get 100,000 downloads, there will be 10 Chinese competitors in the same market with the same ad. So that is why you guys have to spend that time thinking, am I a content company? Am I uh... a LLM guardrail company?
    Am I a parent support company? What am I? And do that role really well. And especially if it's in the US, there's enough money to be made, even if it's a niche.
    That makes sense. I think, hence I think because of that very reason, we've realized that Move to Alexa very soon. Alexa integration. And we were initially thinking we should only focus on the app, but a lot of users are trying to access it through iPads. Because the kids-Yeah, yeah, yeah. --they are given the iPads. "Son, this is your iPad, you can engage with it." In the US, we are getting a lot of requests, hey, do you have an iPad version of this or not?
    Yeah.
    We do have a right now. Okay. iPad ho sakta hai, but then you'll need an adult to operate it at least in the 3-4 year range, other than just keep clicking. See, stuff. Alexa dude, it's a bet that Alexa will find. real PMF. And if they find real PMF, the second bet is, will that PMF enable multi-developer co-creation of apps? The second leap of faith. The third leap of faith is in that multi-developer co-creation of apps, can you win?
    The third is the easiest to take a leap of faith on. But one and two are really not. A lot of things to solve for, yeah. So awesome guys, really enjoyed the conversation. Thank you for taking the time. Same here, same here. Thank you so much for the insights.
    Thanks, thanks everyone. Thanks for catching up.
    Thanks Shiv. Thanks Rahul.
    Thanks, Raleigh. Bye. Ok, Views?
    Overall week maybe 2, PWC spiky 0. Some level of first principles and decent IQ but I think what worries me is highly inside out and not great learning from the existing players, competitors. Didn't hear any deep customer insight or not very customer backward. Doesn't seem like they have gone through a kid and a parent journey and have seen like this is the exact pain point and how they can solve. Um...
    Then I think they are relying a lot on numbers which are like super early, keep saying that based on power user XXX but there are only 10 power users so that insight may not be true and need to be validated. Yeah, so net-net, very negative. Very similar views to Tanaka, did not find him very strategic and very early on to be honest. TV pushed him a lot on a lot of aspects where I could not see him being properly planned out with respect to kya banna hai, kya karna hai and customer insight too was missing.
    Wouldn't rate them spiky, were not very articulate as well. I like what they are building, it's an interesting product but I've had limited exposure so I assume Tanaka would know better. Definitely if they do something, if something cracks then there would be around 10-15 more companies innovating in this space where it would become a survival of the fittest. Where I don't see them being very well equipped to be the hustle first and just go and get it.
    And the other co-founder was silent so I don't know. I know Shiv, I don't know the other guy. CV for you?
    Even in the week, there is no PwC but even in the week for the reason that So, Aram, if you want to back this team, What it requires is some version of Growth Marketing Plus content. Unfortunately, I don't think they have the growth marketing experience. They haven't even started acquiring. They don't have the content experience because none of their background signals content and nothing he said was spiky there.
    Unless you're saying tech and they'll do something that others will not. Uh... Maybe your, your effectively signal kind of woke Okay, yeah. Bye. Cool.
    Not something I'd like really lean into when I die Yeah Yeah, no, no, I think, Cash, if you'd like to add, but I'll just throw in three questions I had for this group was, They are not consumer tech native so I am not sure GTM spike no clue analytical no clue I also don't I'm glad I heard you guys asking questions because now I know what to ask a consumer tech founders obviously like third consumer tech founder I have met but maybe I've just misread this right because I am not calibrated so Yeah, I got it.
    Smart. They just have a long way to compound before they start building stuff. Maybe. Maybe that figure but spike nahi dikha. Yeah. No, I think warranted that this group verify, so this is fine. So that bar is perfect. I think otherwise we maybe They don't have any spike yet. What is the spike? There is no clear spike. Yeah. So to your point Rahul, it's not a well rounded hit. Yeah, it didn't need a 6th pair of eyes, it did.
    So that's why it's not PWC for me, right? It's fine if you're super calibrated on the space then maybe you would have come to a PWC in first meeting. But otherwise it absolutely warrants a hookse. Yeah.
    Yeah, and this was also on track for quite a while and I think Yashi, his college refs came out good, therefore it did warrant doing the meeting and I thought given it's a thesis area for us, I... Maybe strong, maybe I over indexed on an in-person interaction. I found them way more impressive in person than what they've done today. But Would I jump all over this after hearing the train of thought today?
    I think no. Okay. Cool, man. Yeah. This is super helpful. Thank you. This is super helpful. Thank you.
