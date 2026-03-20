---
name: "Maven"
notion_page_id: "32629bcc-b6fc-813b-b465-d541ab35bff6"
db_id: 267
fetched: "2026-03-20T03:52:57"
---

# Maven

**Table of contents (click to navigate)**



---



## Meeting 2026-03-19T22:48:00.000+05:30 



Introductions:

- Confido

- VoiceBit

- Razorpay Ventures



### RM reflections - WM unless signals work out

++ Track record of achievement - made $120K from hustling & competitive programmers

?? Pivot to nowhere story from YC

?? Payments is an EO/EF business; don’t see the depth here



### Cash reflections - WM

++ Like them as founders

++ Interesting concept

?? Not a large outcome business

?? Some merit to doing orchestration business but PO never scale up

?? Pricing model, scalability, round price etc



### RM notes

- **Background:**

  - *San Jose natives - met in 5th grade*
  - *Built their own Sneaker Bots*
    - *Buy limited edition*
    - *Sold for 2x to 20x retail on StockX*
    - *Made $120K*
  - *USA computing Olympiad *
    - *Top 200 programmers *

- **YC journey**

  - *Vertical voice intake for gyms - first pivot*

- **Product**

  - *Offers voice & dial-pad in-take*
  - *In browser voice agent*

- **Moat**

  - *Creating digital voice vault for each user*

- **Customers**

  - *Vertical payment collections using humans on phone*
    - *Home services*
    - *Collection*
  - *Avoca*
  - *Three other customers via YC launch*

- **Pricing**

  - *$0.5 per transaction*
  - *0.25% txn fee*

- **Funding**

  - *$100K from PearVC*
  - *$250K from Robinhood Ventures*
  - *$3M on $30M*



### AI notes



### Action Items & Next Steps

- [ ] Rahul to connect Vasi with Voicebit (Hitesh) for customer validation 

- [ ] Rahul to connect Vasi with Confilo (Chetan) for customer validation 

- [ ] Rahul to follow up with Razorpay Ventures for their perspective on Maven's approach 

- [ ] Team to provide investment decision within 4-5 days after portfolio company feedback 

- [ ] Vasi to send pitch deck 

### DeVC/Z47 Fund Background

- DeVC is the seed fund arm of Z47 (formerly Matrix Partners India), focusing on collaborative YC investments  

- Typical approach: start with ~1% ownership in YC companies, build up over time (e.g., grew from 1% to 5% in Codant) 

- Strong focus on voice AI investments including Smallest AI (contact center automation), Riverline (voice collections), Grey Labs (voice for bank front office) 

- Other YC portfolio companies: Boost, Codant, Nixo, Tesora, Orange Slice 

- Partners: Rahul (former YC W21 founder who sold insurance software business), Akash (angel investor in Supabase, built and sold India's largest real estate portal), Rajat (first investor in Razorpay)   

### Founders' Background

- Vasi and Brendan met at UC Berkeley, both studying CS/EECS 

- Started together in 7th grade building sneaker bots to arbitrage limited edition sneakers (Jordans, Yeezys), generating $200K gross revenue and ~$120K profit between them   

- Both competed in USA Computing Olympiad (Vasi in platinum division, Brendan in gold/top 200 in US) 

- Worked at Amazon and Meta during college 

- Dropped out of Berkeley after sophomore year, been out for two semesters 

### Maven's Product & Technology

- **Original thesis:** Started building vertical voice agents for gyms, discovered payment collection gap when gyms couldn't sign up members over the phone  

- **Current product:** Payment infrastructure for voice agents - solving the problem that voice agents can't collect payments and currently require human call transfers  

- **How it works:** Generate transfer to phone number that clones original voice agent's voice, compliantly collect card details (number, expiration, CVV) through voice, process to payment gateway, transfer back to original agent 

- **Key innovation - Digital Voice Wallet:** After one-time collection, create encrypted tokenized credit card mapped to phone number as identity, enabling frictionless repeat purchases across merchants on their platform  

- **Support for both voice and dialpad:** Voice is primary interface to maintain conversation flow, but dialpad available for privacy concerns 

- **Gateway agnostic:** Integrates with all major payment gateways (Stripe, [Authorize.Net](http://authorize.net/), Razorpay, Adyen) - one integration for merchants vs. each gateway building separately  

- **Future expansion:** Exploring payment widgets for chatbots and other human-to-agent interfaces  

### Target Market & Customers

- **Primary verticals:** Industries doing phone-based payment collection through human call centers - debt collection, home services, insurance workflows, financial services/bank verification  

- **Current customers:** 

  - Avoca (acquired through cold outbound, YC company in debt collection)  
  - Three other voice agent companies in debt collection 
  - One in television advertising and commerce 
  - Strong pipeline in restaurants, more debt collection, home services 

- **Distribution partnerships:** Working with Retail AI (voice agent orchestration platform) on MCP integration library so all their users can use Maven for payments 

- **Market thesis:** Voice agents replacing human call centers in traditional businesses that rely on phone payment collection 

### Business Model

- **Pricing:** 50 cents per payment collection/transaction (regardless of success or decline) + planned 0.25% transaction fee  

- **Scalability advantage:** Revenue scales not just with direct customers (e.g., Avoca) but with their customers' transaction volumes 

### Fundraising Details

- **Current round:** Raising $3M at $30M post-money valuation 

- **Raised to date:** $925K total 

  - $100K from parents pre-YC at $5M cap 
  - $50K from Robinhood Ventures  
  - $300K from Blast VC (YC tracker fund)  
  - YC investment (amount not specified) 

### Internal Discussion & Concerns

Post-meeting, Rahul and Akash discussed reservations:  

- Concern that Stripe and modern payment providers may build this functionality themselves 

- Historical skepticism about payment orchestration businesses scaling 

- Acknowledged phone-based card transactions are common in US (unlike India where payment links work well via WhatsApp)  

- Plan to validate with portfolio companies (Voicebit, Confilo) and get Razorpay Ventures' perspective before deciding  

- Overall sentiment: founders are strong and onto something, but concerns about scalability and competitive risk warrant further diligence  

### Key Connections & Follow-ups

- Maven already in discussions with Razorpay Ventures for partnership and potential strategic investment 

- DeVC offered to help facilitate Razorpay connection given their close relationship as early investor   

- Portfolio companies identified for customer validation: Voicebit (restaurants) and Confilo (bank front office)  





Notion AI is transcribing this meeting.

That's the PII warning, I am gonna transcribe the meeting so I can share it with Akash. Awesome. I'll give you a quick background about me, about the firm, and then would love to hear from your end. I was an entrepreneur like you, your YC Winter 26, I was YC Winter 21, different era, that was a Zepto batch, that was a COVID batch, that was 500 companies in one batch twice a year versus where you guys are now.

And I sold my business, it was doing software for insurance brokers, very boring, pre-AI. I built a company in the era where you had to hire engineers to get code. Today you can burn through millions of tokens and get the same code built 10x faster and better. We're three partners in the fund. Akash is an angel in Superbase, which is another super successful YC company. He also built and sold India's largest real estate portal back when you and I were literally in our diapers.

Second partner, Rajat, is the first investor in Razorpay, which is the stripe for India. Again, one of IC's big hits in India as well. From the fund we've invested in several YC companies over the last couple of batches. Boost from spring last year, Codant from winter the year prior to that, Nixo, Tesora, Orange Slice from the batch prior. Typical philosophy when investing in YC companies is to start with about a 1% ownership, collaborative check, no sharp elbows, build up ownership over time.

For example, in Kodant, we've gone from 1% to 5%, 5% in their Series A at a significantly large valuation, which now brings me to where do we get the capital from? We were earlier called Matrix Partners India, a joint venture with Matrix US, which like Sequoia, Kleiner Perkins, etc. and 70s we were rebranded to z47 or z47 that's the name of our venture fund even today that does large series a series b rounds and devc is therefore the seed fund or the sort of smaller vehicle where we do these sort of yc and other collaborative checks where last minute we're super bullish about voice i don't know how to type i literally only use voice to get all of our work done We were early investors in smallest AI, which is contact center automation with voice, Riverline, which is voice collections, Grey Labs, which is voice for AI automation in the front office at banks.

Okay. So yeah, anything voice for us sounds very exciting and we don't have any common connects. I appreciate you accepting this outreach on LinkedIn. We have a couple of founders in the Berkeley network, but they graduated before you and your co-founder joined. So that's quick context. I'd love to jump into questions that you might have for me and then would love to hear from you.

I think you answered. So most of it is average check sizes, like 1% of whatever we're raising. Yes. Yes. Okay, Yeah, I'll go intro on myself.

Hey, Cash, you jumped in just at the right time. I gave Vasi the intro to DVC Z47 and our voice investments and your background as well.

Oh, perfect. Perfect. I was actually stuck because I don't know what the Zoom link was asking me, but passcode usually just auto fills.

It's your meeting, dude. How did that happen?

Yeah, that's why. That's why I'm surprised. Oh, is it your meeting? I thought it was ours. Oh, okay.

Yeah, yeah, yeah. Okay, maybe it's yours. Awesome. Over to you, Basi. Would love to get quick background about you and Brendan. I think you guys met at Berkeley and would love to understand what prompted you to start Maven. Over to you.

The payment space was actually through sneaker botting. So in seventh grade, we developed our own sneaker bots that could hack like Shopify checkout workflows, Stripe checkout workflows. So we could buy like limited sneakers like Jordans, Yeezys at retail prices and then sell them on secondary markets like eBay and StockX for $2 to $20 retail. We ran that business for two, three years, got to $200,000 in gross revenue.

And yeah, later on in high school, we got big into competitive programming. We both were part of the USA Computing Olympiad. division, Brandon was part of the gold division. So things like top 200 competitive groomers in the US. Um, flash forward to college, we both got to UC Berkeley together as well. I'm studying CS, Brandon's studying EECS. We worked at Amazon Meta. And yeah, after our second year, Berkeley, we dropped out together and we've been out of school for two semesters now.

Awesome. That is incredible to hear. How much cash did you guys end up making from the sneaker business?

It was like 120 between the both of us.

And you were what, 17, 18 then?

No, it's 13 14 Wow.

Okay. Awesome. Awesome. No, that's very cool. And then, so this was, this was, this was the StockX arbitrage play. Did you all do anything else entrepreneurial in college or was it just the computing Olympiad?

Awesome, perfect.

And how did this lead to Maven for you guys?

Yeah, so when we first got into YC, we were actually building vertical voice agents for gyms. So it's pretty different than what we're doing now, but the whole issue we were trying to solve was like, okay, right now a lot of people call in to these gyms and are very interested in signing up and what the gym is like, but the problem is they never show up to the gym to actually sign up for a membership.

So it'd be really cool if we could convince them to sign up for the gym membership over the phone and basically process their first month of payment and get them signed up for the gym CRM all through the voice agent. Today collect payments and we realize like okay right now what there are no solutions for both it's to collect payments What they do is they do human call to come transfers when it comes to payment time So yeah, maybe this is not important for my gyms.

But when we look at these huge ministries like debt collection Like insurance workflows home services and like financial services equipping verification These are all real human industries that rely on payment collection over the phone, which is kind of why we're here today Big problem, especially with the voice market exploding. Our whole thesis is that voice agents are going to replace these human call lines and human call centers for these traditional businesses.

So we're like, yeah, they definitely need to collect payments. So we're kind of the payment infrastructure behind that.

Very interesting. And you know, I'll obviously let Akash jump in. I know I'm hogging up a bunch of the limelight. Very naive question, but today on on non-payment enabled voice agents, for example, the debt collections ones that we have in India, they send a Stripe link on iMessage, on WhatsApp, etc. What are you guys doing different here? Maybe you have a demo that you can show us or you can walk us through something we just love to get.

Yeah, for sure. Yeah. um i'll kind of walk you through like the problem with the stripe checkout yes from both yes yes yes in our customers perspective yes so right now the Yes.

Yeah. Yeah.

Yeah. Call where we generate a transfer to phone number that clones the original voice agents voice and we compliantly collect credit card expiration your CVV your credit card number your expiration day your CVV through voice Process it to the end payment gateway and then transfer back to the original voice agent But what's really cool about us is after this one-time collection. We basically essentially build this whole data mode Which is our digital voice wallet we use your identity Which is your phone number and map it to an encrypted tokenized credit card that you just gave us to use the same identity for subsequent purchases you might have for either this merchant or any class merchants that work with our platform.

Oh. Oh wow, okay. That is very interesting. you know and i guess your your your merchant partners are okay with you creating this uh this digital library because they're sort of contributing to your data network effect in some way. There's no issue.

They were also helping them, right? Right. Because for subsequent purchases, they don't have to make their customer read out their entire credit card number again. They can just come to us and say, oh, we have this card on file. And yeah.

Yeah. Very interesting. And are you aware of any previous attempts to do this using using voice in the pre-AI era or?

No. Everything previous to us were these very legacy IVR type systems. Right. So think about like the dial pad that are like, hey, type one under dial pad to go. Your type 200 out about to go here there's actually been no efforts to do voice collection or payments Oh for voice so yet Very cool and Cash over just one quick quick quick one Probably shows the body payment flow.

Why choose voice over the dial pack?

Yeah, so we actually offer support for both right let's say someone is out in public and they can't read their credit card number outside They are allowed to type it in an iPad But like the whole reason for doing voices you're all essentially already continuing with this voice workflow, right? When you're talking to this deck collector voice agent when you're transferring over to us So our customers really want this ASR system where they're able to collect through voice interface because they're already talking through the voice workflow And especially when you look at things like in-browser checkouts, right?

Let's say you're doing an in-browser voice agent, so it's not actually an outbound or inbound call. There's essentially no support for Dialpad, right? Yeah, okay.

And in which case do you almost think of it over time?

extending into like multiple methods because you know you could also start if it's in browser you could start doing pass keys uh there is multiple ways you could try and build the cat Yeah, so right now we're really trying to focus in on the voice interfaces because we think that voice AI is the future because every business will have a voice agent. We're also exploring these other human to agent payment touch interfaces, right?

Like chatbots right now. Right now chatbots have no payment widget. But since we already integrate with all the legacy payment gateways that will never build this out themselves, we can compliantly integrate with a widget on these chatbots to do payment collection as well. Which is something we're looking into.

And why would you say the legacy, like the truly legacy PGs might not, but why wouldn't the likes of more modern PGPAs extend themselves to all these Asian tech services?

Yeah, so are you talking about like Stripe, for example, correct? Yeah. Yeah, so I guess we can look at it like a perspective of Yeah, yeah, yeah. So many of these different payment gateways, you really need this all-in-one payment gateway agnostic solution like us, where we integrate to every single payment gateway. Like, for example, Stripe will only build it for Stripe. Stripe won't build it for Authorized OnNet.

They won't build it for Razorpay. They won't build it for Adyen. So you kind of need this gateway agnostic solution where it's one integration for the payment collection itself, and then it's very easy to disintegrate into all these different payment gateways. Makes sense.

Got it, got it. Did Raul mention that we are theAre the earliest investors in Razorpay?

Yeah, he did mention, we're actually talking to Razorpay Ventures for like a partnership and then some like maybe a strategic investment, but yeah, it's very interesting.

Awesome. Got it. Okay. thenAnd actually, Vasi, I'll follow up with you on the Razorpay Ventures thing in case you're not able to get the, the sort of right connect with them because we've invested with them in a bunch of payment, payments, payments, adjacent companies like a metered billing sort of suite. If I could just double click on Avoca, I know it's a YC company as well. Could you just tell us a little bit about how you found them as a customer outside of Avoca?

Who else is there in the pipeline? How are you and Brendan nurturing the pipeline sense of what is a good archetype of a customer for you at this point?

you So yeah, I got So I answered the last question first. So right now it's really these verticals that are doing payment collection over the phone already through human centers, right? So debt collection, home services, insurance workflows, and financial services for like bank verification. So these are the main verticals we really want to dial in on. How we got to Avoca, Avoca was through Code Outbound.

We were like, okay, we're building solution we have it ready would you guys be interested in it and they're like oh yeah we We've been thinking we've been waiting for something like this to come on the market and yeah that's why we signed them up. Right now we're also working with three other voice agent companies doing a debt collection space. One in the television advertising and commerce space and these are through our YC launch.

So right now we have four side customers but we also have a lot more in the pipeline. A bunch in the restaurant use case, more in the debt collection use case, more in the home service use case. And what's your pricing model? Yeah, so how our pricing model works is 50 cents for every time you do a payment collection slash transaction through us. So regardless if the payment is successful or the credit card got declined, we charge 50 cents.

And then on top of that, we're soon going to add a 0.25% transaction fee on top of that. So our pricing model is pretty cool because we don't just scale with Avoca, but we scale with Avoca's customers, if that makes sense. how many transactions they're doing a month. Yeah.

Got it. Got it. No, I think we don't have too many incremental questions. We understand the people pretty well.

Because both payments and voice comes pretty naturally to us.

What would be great is Rahul could follow up with connecting you with a few of our portfolio who would be great customers. So I think the best one Rahul would be Voicebit.

Voicebit? Yeah?

Yeah. I was literally going to send it to Asi.

Yeah, I mean, yeah, that'd be huge I guess one thing I wanted to mention that and get to was we're also working with these huge voice agent orchestration platforms I don't know if you're familiar with retail AI So this is like where everyone's going to build their voice agent right now Retail AI's actually came to us through inbound and we're essentially working on this MCP integration library So all of retails users can actually use Maven as a payment service while building their voice agent I'm about to be on a more self-serve model.

But yeah, but yeah, I mean yeah voice bit would it would be a huge intro to yeah there in the restaurant space and again uh raul also confido which is with the front office sites uh yes i can definitely get confido onto this and on razor payment we work very closely with them they're actually part of our uh theseCan you see go?

So as I mentioned, we have done a lot of things together.

If you have any information handy, send it across. I think we don't have too many questions. What would be great is you speak to the portfolio companies and just say that we went to sync and we'll take maybe like four to five days to turn around and get you a complimentary answer from our end about our participation. Okay. Yeah. I was just going to come to that. So on, On process, like Kash mentioned, I think the idea here is when we sat and reflected on this before jumping in the call with you, we said it's a little Especially as Indians, we're so used to getting the payment link on WhatsApp and then just hitting the pay and moving forward.

This felt a little out there and if I may say weird, but you know, as investors, we have to keep our eyes and ears open and there's obviously something here that's working. We want to run this by real customers of yours. I think that's the, that's sort of the proof in the pudding for us to be able to pull the trigger. I'll ping these two companies, but I just love to get a sense from you on whether you all raised capital before YC, what's the capital position now, how much are you looking to raise, are you all doing party round, lead round, what's the cap, etc.?

So we raised $100 from parents. Before YC, that was at a 5 male cat. Guarded? Uh, and then August. See why see money came in. Yeah. So far we've raised 50 from Robin Hood, 300 from Blast. And we're racing a 3 mil at 30, so far we've raised 925 for the front.

Perfect, okay, three on 30. And sorry, the Robinhood one comes from a Ventures fund or? From Robin Hood?

Mr. Venture Arm.

Got it. So you have Robinhood Ventures as well. And there's Blaine West that you mentioned.

-Oh, sorry, what did you say?

The other person on the cap table, so yeah, I heard--Blast, blah, blah. blast VC okay got it yes they are one of the YC tracker funds awesome this is super helpful and thank you I appreciate this so much and an email is the best place to get you connected with these founders once they opt-in awesome yeah over deck too all right thank you so much that's awesome thank you have a good one thank you I'll call you.

Okay. Hello, okay, so here's my view Interesting, but not necessarily a large outcome business. Stripe and the modern teams will build it themselves. There is some merit to being like the same in the orchestration side, the PO side, but the PO business has never really scaled in the past. So I don't know why PO becomes a big thing now. I think as founders, I like them, but I got business and I got a drive.

Sorry, Cash. I've lost you for the last couple of seconds. I was saying as founders I like them and I do think they are on to something but overall net-net between the pricing models, scalability, risk from the stripes and the other people in the world doing it themselves. actual round tries Yeah, I am in the same case. I guess it's a week maybe but I will follow up with Razorpay Ventures.

Yes, yes, but we should.

This is one of those where we should follow up and be plugged in. Yeah. because there is something to it Yeah, like I told him, I said my initial thought when I read what he sent was dude, what, what, like, what the fuck is this? How can you even raise money? But I wanted to keep an open mind. No no see this phone based card transaction is a common thing in the US. In India we don't care because obviously we don't have the Because the links and all this work.

Correct.

But in the US it's a pretty common thing. Got it. Yeah.

Thank you. Okay, this makes sense. So we have a 45 minute gap now.

And your best validation is voicemail.

Yes, exactly. And 100% that I can 100% see. So the next zoom is in 45 minutes.

I'll take one right now.

No, no, that got cancelled. Yeah, and then I'll walk over to your hotel and we leave for emergent. Yes, done. Okay, awesome. Thank you, man. Okay. Yeah, bye-bye. Need to send across a couple of voice notes, need to send a couple of messages across based on this voice note I'm sending you. Hi Hitesh, we met a YCW26 company called Maven which is providing a payment orchestration service for Voice based payments Would love to make a double opt-in introduction if you feel this could improve the customer outcome and be relevant for you folks at Voicebit.

So that's to Hitesh from Voicebit. The next one is, Email to Hey Naman, as mentioned on our call yesterday, making this double opt-in introduction to Sandeep Singh Kohli, who is the former CMO of Venafe and Kong. SSK is very keen to connect with you to explore An angel and advisory relationship. We'll let the two of you take this conversation forward The next one is for the team at Razorpay Ventures.

Hi team, we just spent some time with Vasi from Maven Labs, they mentioned, Vasi from Maven Labs in bracket YC26, they mentioned they are in touch with you, would love to get your perspective on A, The thesis for building a payment orchestrator focused on voice payments B The perspective from a PAPG provider like Razorpay as to whether or not this could be subsumed within your own offering. And three, any other thoughts?

About the approach, we are also in parallel getting some feedback from one of our portfolio companies. Next message is to... Chetan from Confilo. Hey Chetan, Cash and I met a YCW26 company called Maven Labs. which is a payment orchestrator for voice based payments We'd love to make the introduction to Wasi and team NK's You feel that this voice based payment acceptance stack can improve the customer outcomes at confido?

which is a payment orchestrator for voice based payments We'd love to make the introduction to Wasi and team NK's You feel that this voice based payment acceptance stack can improve the customer outcomes at





## Deck 2026-03-19T23:17:00.000+05:30 

[File: download](https://prod-files-secure.s3.us-west-2.amazonaws.com/b21975bb-aebf-48e3-8c44-1573c4404129/c58b7da5-d572-4d0a-b6c1-7a0951ea25ca/Maven_Fundraising_Deck.pptx.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466WRZNFKQB%2F20260320%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260320T105232Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEGgaCXVzLXdlc3QtMiJIMEYCIQDabrjzKorGGFf%2BQ%2BfmHEuY9%2FpWgicayG8AdwmWeT0oaQIhAOLtEZ9jSyL9hHxEWNKGtBVkbFcTRIFN78BSrVkbY%2FvOKv8DCDEQABoMNjM3NDIzMTgzODA1Igw6sGtEPb4zvbrkyVkq3ANfmgZSLupbqPjm%2Fly6gokTCZ2DPuTavT5RPq%2BEZ8B9lB62bZ9R%2FKs9ZXz36znKc%2FNgb%2BQppvdiD7L3SG50ZXuwwu6Ov8avtrSHzOkQsbm9dkYm0J2utw98lYkNs1Do%2FvsqYNmtq34ir%2BRR%2F5XxYp7as%2FwZ%2BUZmArCQeRFLvclg9B2JTfgrR2uxXHK7PKJHXzfxu8AFOZSnDjLG9H2bZulxKX9j3ocKKAe1D%2FfSshLHyXZyEREnZVp9y2X19LeIlARJ97aypE7YxqypyBQfkigCVmAqHBHzvGCLcxJWRVEcP4VQOcTxc9YtUPMVinIZo8iGwRKk8h1x%2BqKCRSX7N%2FUQTairWl6YcJgZmWOfESyikvBeWgLVgE9FeyDNmZnpgWb9jyD3vOMvVnZ6hg57IQP4Dw98qTrv5ox%2FBYz4BA212RMFw%2FUj42BuWchIM%2F3nrUvR1iMjzF8NXtf0Z2XbYKMOt3UoSdTl1%2FmwYANTY%2FipVOx8UE0oAW%2FWRoO4TEwkGVVlqHMOUOIkU%2FJwv8DgeL0uXbrNXbeaZgJ02mQTw2HVdjLnu18HZrsAGhqhoMgcibc%2FaZqheTTd%2BFxUcRbT7gqM0%2Bh4%2Bdu65Y97X8jLYlko189S9T7NvFBUtuSgGjDU%2FPPNBjqkAcOZDMgFMYvWIOtM3QWnz6jxpV%2FrXzqVyoU6KLFR91hiXDg2NuXoAxrBDLbjdO5SdUw7N8xaaeTCwdmHEILurIZQvbFugX%2FqbGmboN5LWjQrVl4RWMRHwJTKm997lErLsrl6Vcw8ODsABs%2BGBe%2FZHbMDYIjv9EbhwmxFFIvME0hp8%2BL%2BRhrXxf76jZwNn4xIPKKNXPaJU0V4K48mqFNcUNtWViDq&X-Amz-Signature=42e3438d98020bcdae8cfc05d552eb85b190fea18ae57dea41057cf3100f2a09&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)



## Notes from Vishnu at Razorpay Ventures 2026-03-20

1. Hey Rahul, yes we are also spending time.
2. Some PGs have/are already building capability to do agentic collections directly with voice agents. Stripe has done it in the US. We have also partnered with Gnani in India + actively doing more
3. It seems a product more for smaller or long tail PGs + primarily solving for compliance. Good wedge to enter but may not be enough to sustain
4. Partnership led GTM, still early thoughts for us, but may not be necessary as the number of PGs + voice agents is limited + partners may not solve for integration & onboarding effort. But this are still early thoughts - we only figured towards the end of the call that they are doing partner led GTM
5. Our main Qn is - how many payment dependant voice players won’t do this themselves, and why payment companies beyond stripe also won’t do this as the world evolves
6. So is their wedge and stack deep enough or can the move fast enough to capture market to deepen their stack and defend
7. Didn’t get any directions from Wasi on the above

---
