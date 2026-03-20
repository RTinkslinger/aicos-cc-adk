# Shiro


**Table of contents (click to navigate)**

---
## Call prep 2025-07-04T09:19:00.000+05:30 

Questions
1. Work
  1. Sarvam AI
  1. DevRev
1. Ice breakers
  1. What is up with Pikachu and calling it the cutest coding agent?
  1. “dev” joke with him
  1. Why pick coding generation as a space? 
1. Business questions
  1. Why decide to go down the asynchronous agent route?
  1. Why not a plug-in versus being built into an IDE / an actual agentic IDE like Cursor?
  1. Thoughts on prompt to prototype?
  1. Thoughts on context is the moat | does agent have context or IDE have context?
  1. Why tasks per month pricing?
1. Why join Vercel’s AI accelerator?
1. Dumb non-engineer Qs
  1. Known
    1. Bolt - web container tech - OS in your browser
    1. Devin/Replit - run VMs 
    1. V0 - Vercel’s own stack
  1. What was your architecture choice & why?

### KB’s talking points
1. Kanban board is pretty cool
1. Login through GitHub only?
1. alt-devin lol


## AI X Coding market map created by ChatGPT 2025-07-04T09:39:00.000+05:30 

 
| Category | Tool / Product | Company / Org | Year Started / First Release | Founders (Company) | What it does (1‑line) |
| --- | --- | --- | --- | --- | --- |
| Code generation | GitHub Copilot | GitHub (Microsoft) + OpenAI | 2021 | Tom Preston‑Werner, Chris Wanstrath, PJ Hyett | Autocomplete & generate code, tests, and docs directly in IDEs. |
| Code generation | Amazon CodeWhisperer | Amazon Web Services | 2022 | Jeff Bezos | Real‑time AI companion focused on AWS APIs & multi‑language completion. |
| Code generation | Tabnine | Tabnine (fka Codota) | 2013 | Dror Weiss, Eran Yahav | Privacy‑centric, on‑prem & SaaS code completion trained on permissive OSS. |
| Code generation | Codeium (Windsurf) | Windsurf (Exafunction) | 2021 | Varun Mohan, Douglas Chen | Enterprise‑grade autocomplete, refactor & search with secure context window. |
| Code generation | Replit AI (Ghostwriter / Agent) | Replit Inc. | 2022 | Amjad Masad, Faris Masad, Haya Odeh | Browser IDE with built‑in chat, completion & full‑stack app generation. |
| Code generation | CodiumAI | CodiumAI Ltd. | 2022 | Itamar Friedman, Dedy Kredo | Generates tests, explanations & reviews to ensure code integrity. |
| Agentic coding | Devin | Cognition Labs | 2024 | Scott Wu, Steven Hao, Walden Yan | AI engineer agent that autonomously completes software tasks from GitHub issues. |
| Agentic coding | Bolt | Bolt AI | 2024 | Unknown | WebContainer-based agent that builds and deploys apps from a single prompt, all in-browser. |
| Agentic coding | smol‑ai developer | Smol AI (open-source) | 2023 | Shawn “swyx” Wang | Lightweight OSS agent that scaffolds entire codebases from a prompt. |
| Agentic coding | Sweep AI | Sweep (YC S23) | 2023 | Kevin Lu, William Zeng | Agent that opens PRs to fix bugs & tech-debt inside JetBrains & GitHub workflows. |
| AI‑native IDE | Cursor | Anysphere Inc. | 2023 | Michael Truell, Sualeh Asif, Arvid Lunnemark, Aman Sanger | VS Code fork with chat, agent mode, code‑search & refactor across repo. |
| AI‑native IDE | JetBrains AI Assistant | JetBrains | 2023 | Sergey Dmitriev, Valentin Kipiatkov | Context‑aware chat, completion & tests across IntelliJ‑based IDEs. |
| AI‑native IDE | Sourcegraph Cody | Sourcegraph Inc. | 2023 | Quinn Slack, Beyang Liu | LLM assistant that taps code‑search graph for long‑context edits & queries. |
| Prompt‑to‑prototype | Lovable | Lovable AB | 2023 | Anton Osika, Fabian Hedin | Chat‑based builder that turns plain prompts into production‑ready web apps. |
| Prompt‑to‑prototype | Locofy.ai | Locofy.ai Pte Ltd | 2021 | Honey Mittal, Sohaib Muhammad | Transforms Figma & Adobe XD designs into responsive React / React‑Native code. |
| Prompt‑to‑prototype | V0 | Vercel Inc. | 2023 | Guillermo Rauch | Text-to-UI generator that turns prompts into Tailwind/React code, tightly integrated with Vercel. |

---
## Intro conversation with Founder on 2025-07-04T17:11:00.000+05:30 

### Attendees from DeVC: @Rahul Mathur and @Krish Bajaj 


### RM Reflections — SM on founder || WM on what he is doing RN || no round to form / coming together
++ H&H - can clearly see the hardwork
++ Love how transparent he was about lack of promise here
?? Lack of clarity on what is different even for 
?? Using Cursor to build his own product (?)

### RM notes
1. “Altdevin” was initial name
  1. 2 months ago
  1. Devin web UI was very bad
  1. Dev only operated as a Slack bot
1. Started coding at age 13
1. Codeforces etc - learnt C++ himself | competitive programming
1. 9th to 12th - studied for JEE | did CP
1. gave Olympiads - national bronze for CP
1. Sarvam intern
  1. June 2024 - internship
  1. LinkedIn post
  1. Standard application process
  1. Worked on AI Agents team
  1. Operated like a quasi consulting business
1. AI X Coding - crowded but problems exist
  1. Shiro is a shameless clone of OpenAI’s Codex
  1. Iterate like mad - learn from users
  1. At Sarvam - used ChatGPT & VSCode together | then used Cursor
1. User
  1. Being leveraged for side or personal projects
  1. Enterprise ask
    1. Want a way to preview / browser attached to sandbox to see the UI before PR being raised
    1. Wanted terminal ask
1. Value:
  1. Code maintenance > Code Gen
  1. Wants to pull in data from other sources to suggest changes to the product

### AI Notes:

<!-- transcription block -->

    ### Background and Journey
    - Started coding at age 13, initially drawn to competitive programming on platforms like Codeforces
    - Learned C++ independently, achieved national bronze medal in competitive programming
    - Studied for JEE exams from 9th to 12th grade while continuing competitive programming
    - Currently 20 years old (turning 21 in December), started undergrad in 2023
    - Joined Sarvam AI as an intern in June 2023 through standard application process
    ### Shiro Development
    - Originally called "Alt-Devin" when started ~2 months ago
    - Initial goal was to create a better version of Devin (which had poor web UI and was only accessible via Slack)
    - Described Shiro as a "shameless clone of OpenAI's Codex" with a focus on rapid iteration
    - Development philosophy: "Get something out there, listen to users, see what works, iterate like mad"
    - Used Firebase for authentication (still had traces of "Alt-Devon" in the system)
    - Currently running on AWS (considered Daytona but faced documentation issues with their HTTP API)
    ### User Adoption and Feedback
    - Product experienced initial viral success on social media but user retention has declined
    - Most users are leveraging Shiro for side/personal projects rather than work environments
    - Enterprise users requested specific features:
    - Some users reported Shiro replacing Cursor in their workflow
    ### Strategic Direction
    - Currently questioning differentiation in the crowded AI coding space
    - Seeing potential pivot from code generation to code maintenance
    - Envisions an agent that could:
    - Challenge identified: handling sensitive data in logs while maintaining privacy
    - Value proposition shifting from code creation to maintenance and improvement
    ### Personal Workflow
    - Previously used VS Code with ChatGPT open in browser
    - Gradually evolved to using Cursor for most development work
    - Personal contribution to codebase became "lower and lower" over time
    - Now primarily gives high-level instructions to AI and reviews AI-generated code
    ### Funding Status
    - Currently bootstrapped with no external funding
    - Not actively fundraising as current costs are manageable with free credits from providers
    - Recognizes eventual need for funding to compete in the space
    - Current focus is on finding unique value proposition before seeking venture capital
    ### Next Steps
    - Participating in Vercel's accelerator program
    - Planning trip to Bay Area to explore opportunities and meet potential connections
    - [ ] DeVC to follow up with email introductions to Bay Area contacts
    - [ ] Dev to connect with recommended contacts during US trip
    - Exploring code maintenance direction as potential differentiation in market



    If there is anyone you all think that I should meet, I would definitely be down. Thank you so much, first of all, and yeah, my accommodation is pretty much sorted. I'm going to be staying with a friend. Perfect. Okay. No, that's good to hear, man, because you are like, what, 20, 19, 18, 20.
    I am exactly 20. 20, okay, perfect. So... When I stopped you on LinkedIn, the socially acceptable amount, and I was like, your undergrad started in 2023, and mine ended in 2023. And I was like, I'm officially old now. Yeah. Yeah, so therefore... I failed.
    Therefore, Dev, you're 2004-2005 born? Okay. Wow. Thank God. I'll be turning 21 in December. Okay. Perfect. And which day in December, sorry? 26th. Okay. Got it. Yeah. Very nice. So, I'm also December baby. I'm 14th December, 97. Yeah. So, a little bit of an age gap. But, I think this is the first year where I've realized that
    I am like in some different planet or different generation compared to you guys who are born in 2003-4. The first time I felt this was when I had hired Krish all the way back in... Krish, you were like 18 then or 17 then? Just turned 19. And I was like, oh wow, here's someone from 2000 dude who's working with me.
    And that was a shock. This is incredible, man. And also... I think the I was unfortunately not able to make it a local host, but the the demo that you did apparently impressed a lot of people. So really well done and also great stuff with the launch video. I'd say even before we got chatting, Krish was among the first people who shared your little Pikachu over there, which is actually going to be my first question saying where does this idea of cutest and Pikachu fit into the bigger picture, but I'll let you take it however you want.
    Intro to DVC. So where a fund that has been carved out or created under Matrix Partners India brand. Matrix is a global investment firm. Matrix India recently rebranded as Z47. Simple pitch, simple idea was Indian startup ecosystem is deepening founders like me, forget founders like you, I'm a generation before you.
    We're going to more experienced startup founders to raise our first round of capital. versus going to a traditional venture fund. So this concept of operator angels, founder angels was emerging when I had become a founder. And Matrix wanted to create a vehicle in India that could allow institutional capital to be invested into founders, alongside founder or operator capital.
    So we're a five member team. But we have 40 venture partners who we call our collective members. And they're typically founders who have built so So what we try to do is alongside our investment in each of our 125 portfolio companies now, in over 75% of them, we have at least one venture partner who is investing from the domain, which then gives you not just the capital, but then also a mentor who's been on the same journey as you maybe several stages ahead.
    So that's broadly what we've always pitched. And in the world of SaaS and AI, as a fund, we have a bunch of investments in the US, they're about 45 now, we have Confido, which does voice AI in healthcare, we have smallest AI, which is a foundation model for voice, we have Rapid Claims, which recently got funded by Excel that does medical coding and insurance, again, an AI company, Kintsugi, which raised a monster $20 million, Series B, which is in US, which is a
    sales tax and automation. So although it might seem like this, like we're a bunch of weird people who hang around only in Bangalore, our MDs are invariably on a flight to the US at least once a quarter. And a lot of our collective members are based out in the Bay Area.
    So Vijay from Atomic Works, Shree from Rocket Lane, Arvind from Super Ops. who've all sold at least one SaaS business before in their life, are LPs in the firm, venture partners, and they spend all of their time in the US. So our pitch to founders has always been, we're like another founder on your cap table, you don't think of us as an angel.
    All five of us on the team have operating experience, three out of the five of us have built a company and sold it in some shape or form. So we've suffered the same trauma as you. Thanks for watching!
    Thanks for that really cool introduction. And yeah, I also feel that if you're building like an AI product in 2025, you have to be in the USA, in San Francisco. Especially in your tool, especially in a space like developer tools, you have to be in SF because the developers there are the ones who are like really willing to try out new things.
    Correct. And yeah, I'm really glad to hear Yeah, in fact, one of our big learnings last year from going out to the Bay Area is in a post AI world, if as a venture firm, we shill this concept of AI replacing labor or AI eating into the labor budget, then as an investment firm, we have to walk the talk, right?
    And pretty much, I think in June last year, we went on this journey of saying, how much of the work that we do in venture can be Automated first through robotic process automation, which I ended up doing. And in the last six months, through through agentic workflows, which is what Krish has done for us. And that's why Krish has now joined us full time. So Krish is probably closer to you engineer by background than us who just talk shit and you know, make a little bit of money of investing in companies.
    But, you know, where Krish and I got very interested is every Tuesday we come across Someone in the AI code gen space and their different approaches. There's prompt to prototype, design to code, there is true agentic IDs, there are also fully autonomous AI coding agents, which is sort of the direction you are moving towards and maybe a good place for us to start Dev is why pick this market, right?
    And why even pick to go start a company? You're still in college. You're probably taking some time One very true thing that you have mentioned is that there are so many people in the space and almost every other week someone claims to have a really new product which revolutionizes the whole AI space. To answer your question, why did I choose to build what I am building?
    It just felt, how do I say? It just felt right in a sense. I mean, software engineering, I started coding back when I was just like 13 years old, so it has really stuck with me. And when Chad GPT and other AI tools came out and people were saying, hey, AI is gonna take your software engineering jobs a decade from now, I was very pissed because I had learned coding
    bunch of years and I spent a lot of my time and effort learning it. And then in 2022, charge EPD comes out and now anyone can code. I was really mad. I had worked so much time to, to get the skills, but yeah, over time I understood that, uh, don't think of it as like, uh, as like a blow to my ego, but just think of the possibilities.
    And what got you into coding at the age of 13? Was there someone at home who gave you one of those introductions to This is a voice memo. It has been edited to include proper punctuation. And how it came about is, I actually came across this thing called comparative programming online, like Codeforces, LeetCode, all that stuff. And yeah, at that time, I really found it interesting to solve these algorithmic problems and whatnot. So that is when I first started learning C++.
    for competitive programming. After that, I took a small break for exams, GE, and stuff like that. Now, after ChargeGBT came out, I just started asking myself, that the way that we build, maintain, and improve software now is going to look very different than how we do it 10 years down the line.
    And I just wanted to protect it. I mean, quite frankly, I don't know what they really do sometimes. But what prompted you to step out of what is otherwise believed to be a very, almost like an open AI type, developer friendly, research oriented company, which is rare to find in India to go and build yourself.
    Right, so I started work interning at Salvam right after my first year of college. I started in like I think June of 2024. So almost a year ago from now. And the way I got in isn't very interesting actually. They just put up like a LinkedIn post saying, Hey, we want some interns, apply, you can apply over here.
    And I luckily got in. My time at Salwam lasted about two and a half months. It was my first time working in the startup office space. I had a lot of fun. At that time, I was working on the AI agents team, which was kind of unexpected. And at Salwam, we used to do that things also. And that was a team that I was working at. And in contrast, we definitely had some proper foundational model-oriented teams too. But yeah, I didn't get a chance to work with them. And to be honest, I was also more interested in the application layer side.
    But yeah, overall, my time at Salwam, really cool people, a lot of fun. And yeah, I think... Over the past few weeks, they have been caught up in some controversies. I just believe that they have a really great team and I am sure they will come out on top.
    When did you start working on Shiro? Would love to figure out how you think about building an asynchronous synchronous coding agent. Actually, let's start there. I have a follow-up question. But let's just begin with the story behind Shiro. Unless, Krish, you have something. No, no. Also, just to add on. While authenticating myself, I think you're using Firebase. Your name was still Alt-Devon.
    So, I think it started with Alt-Devon. Why was that the non-stop first and Shiro now just some background?
    So about, I think, two months ago now. And yeah, the initial goal was to create like a Devin kind of thing. But at that time, Devin was mostly accessible only through the Slack integration. And they even had a web UI, but it was very bad. And on top of that, they were quite expensive, too.
    So my initial goal wasn't very original, I would say. But just like Devin in like a much web interface and this made a lot of sense to me because when building something new I wanted people to be able to try it out as soon as as soon as possible I didn't want them to have to make like a slack account or like kind of slack channels and all that stuff but yeah over the time I was building it
    My goals have changed slightly. And I believe that even though there's so much competition in this AI coding space, I believe that there's still some unsolved problems. And I feel that the right interface, we're still figuring out the right interface and the right capabilities to give AI agents so they can be most effective in working on our
    But yeah, that's the problem, but I don't think I found a good solution yet. And over time, Shiro has built Shiro to be almost like a shameless clone of OpenAI's codecs. And yeah, the plan was to just put it to get something first out there. Listen to useless, see what works, see what doesn't, and then iterate like mad.
    Just adding features, cutting out what doesn't work, and including the rest. I thought it would as based on users' feedback. I wanted to double click on one thing, Dev. Today as you build Shiro out, what AI coding tools are you using? What coding tools did you use back in the day? Where are you finding the biggest unlock in productivity?
    So personally, before ChadGPT, I was using VS Code, I think as almost everyone was doing. And after ChadGPT came out, and even when I was working at Cellbomb just a year ago, I was just having VS Code and ChadGPT open in my browser. I already knew a lot of stuff about what I was coding out, and I still had some ego back then.
    So I didn't want AI to do a lot of work. like most of the work that I was doing. So I was handwriting like most of the code myself. But then over time, once I started using cursor, also like I feel that my contribution to my code base became lower and lower, and it eventually evolved to just me giving like high-level instructions to the AI agent, and then it executing it, and then me just reviewing the code that the AI wrote for me.
    I feel this is a very common experience that most developers have been through. To answer your question completely, what AI tools do I use where I'm finding the most productivity, I just mainly use Cursor itself. That is where I get all my work done. It's kind of interesting also because Cursor, just a few days ago, is something which is almost exactly like what we are doing here.
    much better web interface to run multiple coding tasks all at once. And I noticed one very interesting thing on the, I don't know whether this was AI slop landing page or whether you had actually thought through this. A lot of people today are pricing on a per seat per token hybrid of per seat per token depends on which industry report you go out and read.
    You had a very interesting approach, which is pricing per task. And I'd love to understand why do you define it as pricing per task? What work did you do to arrive at? Maybe this is an interesting pricing model for you guys. Right. So, at that time when I came up with that, I wasn't thinking about our business model or how we're going to plan revenue. I just wanted to be best for the users who are using Shiloh.
    And I wanted it to be more like an... I don't... I want them to pay based on... Not based on tokens per se, but based on... But based on outcomes, so if a task was completed, if like a PR was created, then only you pay us. We took a step back from the whole PR, I mean paper pull requesting and we made a paper task. But yeah, that was initially the vision that we had for our pricing model.
    You pay us only when we make a proper code contribution. Interesting. Okay. That makes sense. And is there any other nuance to task apart from the pull request being raised? Is it that the pull request has to be accepted? Is that there is a certain run time or token limit on the task? Nothing of that form.
    When we launched there was nothing of that sort at all. There was no there was no there was no rate. There was no rate Limiting. Yeah, there was no there was no There was no token cap also And yeah, not a very good business model for someone who has a bunch of Bunch of users.
    Yeah, but we didn't have that many it worked for us and it uh, And it helped us get to the stage that we are at right now makes sense And i'd love to understand I think I remember on Twitter, this went absolutely thermonuclear, right? I mean, everyone from Tokyo to Timbuktu was at least retweeting this. Krish seemed most excited about it. I wanted to understand...
    Amongst your users, sure it's an early product. You'll see a little bit of churn, you'll see a little bit of vaporware signups. For those users who are sticking around, and however you define sticking around, where are you seeing them most use the product?
    Is it for work? Is it for side projects? When you talk to your users, are they saying that this is a good alternative to X or is this a good replacement for Y? What is the voice of the customer telling you? So I'll start with your first question on what our users are going to be using Shadowforth. And I don't have a very good answer to that. They're actually using it for their personal and their side projects mainly. I think not many of them were...
    very open to the idea of giving a new tool access to their work, their positives, and all that stuff. So yeah, I spoke to a bunch of users too, and one of them said that this is the place's cursor also for them, which was happy to hear, but I felt I was a little far-fetched, to be honest.
    But most users I spoke to, they just thought about us as like a new tool they wanted to Integrated to how they work right now, so not very good Feedback from the users or whatever Makes sense and if you had to look at a cluster on Most critical feedback where you know you need to improve where your users are telling you you need to improve What does it take for you?
    And let me articulate this a little bit better. I think there will always be niches and pockets where within a particular craft, whether it's software engineering, design, etc, there will be tools that emerge that cater to a specific preference, right?
    What direction do you find users pulling you towards? What direction do you think will let you unlock that word of mouth and capture some share of sticky users in the code gen space? That is a very good question and I believe I don't have a very good answer to that. But what I can tell you is a few of the things that the users really wanted from us. So one of the things we did after our launch, we were invited by a startup in Kodamangala and they wanted to see if they could integrate, they could buy Shiro for their entire company and just want us to
    And so I did that demo. And one feedback that we, that one primary feedback that we received is that when Shiro makes the changes in your code base, especially if it's like a change on the, They really want a way to preview that change before creating a pull request for it. So they basically wanted like a browser attached to...
    from ours to our sandbox. So they just like to see what the changes and then create a pull request for it. Other than that, they wanted more customizability over the sandbox, as in they wanted to add environment variables and things like those. They even wanted terminal access, so they could run their own commands and whatnot.
    But yeah, I feel I still don't have, despite all this, I don't have a very. I think as a whole, this code generation space is getting way too competitive. People have raised millions, I think billions of dollars now. And as a startup, it's going to be very very hard to compete and add value to this space.
    Now that code generation is becoming almost a solved problem, I feel that there is some value we can add in the code maintenance part. For example, when I launched Shiro, there was a bunch of bugs that came up. There was my, and my website was going down.
    My sandboxes were failing sometimes and this happened after the code generation part, or this happened after I deployed it. So I feel like there is maybe some value we can add here, maybe like an autonomous agent which listens to all my logs. from Vercel's AWS Datadog, and it autonomously pushes fixes right as the logs tell them to. I hope that made sense. No, no. Makes sense. Makes sense. You want to go after the post-code generation part of it? Pretty cool. Not a lot of people have fixed that, to be honest.
    Interesting. I feel... Just go grab it if I'm not wrong. There's something which generates these AI agents which run through it. Need to check it out. But yeah, compared to GoGeneration, this is a big space not checked out. And this is interesting. So effectively, what would be some data sources for you to go do the code maintenance? Would this be server error logs? Would this be social listening and seeing what customers are saying about the product? Is this like Slack chit chat about what's broken?
    Where do you think you will, where do you think you will get the signal to be able to recommend changes to the product? That is a very good point and I believe one of the reasons why maintenance, why good maintenance is kind of tough right now is because of so much fragmentation. Like the front-end logs will be on a first cell or wherever you host your front-end. Your back-end logs will be on your server.
    Your infrastructure logs will be on And your application logs would be on Zen 3. And, of course, if the users find any bug, they'll hit you up on your support service, Zendesk, or something like that. And if your employees itself notice something odd, they'll tag it on Slack or something similar, right?
    So I feel that we're going to need a bunch of integrations, and there's no one single source of truth that we can use to say, hey, there's a... of someone's logs and so on. Isn't that be a problem? That is a very good question. And yeah, I haven't thought of that yet. And now that you bring it up, yes. Logs probably contain sensitive user data and so on. So it might be a bit difficult to get that out.
    But I feel there are still workarounds to it. For example, like analytics websites, like, uh. post-hoc, mixed-panel, they have a thing called session replace, which basically records the user's screen as they're doing something, and privacy is also a big issue over here, so what they managed to do is, all the user-sensitive information, they basically encrypt that out, and it's just shown as black dots, so basically they don't have access to any sensitive information, they just focus on what they need, which is like...
    How is it going? Is anything breaking or not? Yeah, so the short answer to that is I know we are still on AWS actually. Okay. Daytona seemed very good for us, at least very good for me, at that time because AWS was breaking down. But when I tried to integrate it, I found out that Daytona's HTML API for spinning up sandboxes has terrible documentation.
    Okay. It's basically just a bunch of endpoints like listed out and there's not much information And I feel that the main ways that users can use them is through that Python or TypeScript SDKs. HTTP API requirement was crucial for us. So we ended up fixing the AWS thing, and we are still on AWS right now. And the fact that we have a bunch of free credits on AWS also contributed a bit to this.
    Makes sense. Makes sense. I remember you mentioned you wanted the front-end. We wanted to build where you need to also show the front end. And that's why you want to run a website on a sandbox. And then, right? Not a website, per se. I mean, I believe that can be done on Daytona, too. But the reason we wanted to be able to spin up these sandboxes through an API request.
    For example, read a request. Yeah. So AWS just gives us like an endpoint and that we can just hit to spin it up and they did have that but the documentation was terrible and we ended up using AWS instead. Makes sense, makes sense. Krish, do you have any more questions about everything on the product engineering side? Nothing really. I still have to play around with the product to be honest. I saw the GitHub integration and I was like this is going to take some time. And I was 100% positive.
    I saw your videos, the demo videos which were really good. Love what you are doing. I feel integrations and the logs part may be a good starting point. Yeah, and just like the follow up final question here, Dave, is it seems like it's a little early to be pouring fuel on a fire, right? I don't think venture money is right now going to help you answer some of these questions like, what is that narrow wedge in what is the ICP, whether this monitoring use case is compelling even for you to pursue?
    Where are you in your fundraise journey? Are you bootstrapping this? Have you already raised capital? Are you raising capital for the business or are you still thinking about raising capital for the business? One very important thing which you pointed out is that at this point of time, we definitely haven't gotten to the stage where we need venture capital.
    It's because of... of mainly two things. The first one being we haven't reached that growth stage yet where we either need money right now or we are just all we are we are just gonna die and second thing being that most of our costs are just like model providers and other services basically.
    Yeah. And we got like a bunch of free or credits for those. Correct. So for our current scale, our current user base And we really don't need any external capital right now. And this is the same thing that I've told to other people too. And yeah, so to answer your question, where are we fundraising? We haven't fundraised anything yet, but I believe that such a thing, especially in such a hot space, bootstrapping anything, especially when your computers have raised like so much, and the values also, we can add like so much value here, I feel bootstrapping again might not be...
    But I feel there is a time for raising capital and we are not at that time yet. Right now, it's not very good to be honest. After the first week or so, our users have been dwindling. We just have a few users who are using it day in day out. And to be honest, I have moved more towards focusing on what Krish had mentioned earlier about seeing where you can add value in the maintenance side. And I've been exploring ideas over there mainly and just leaving this on like on autopilot. Yeah, makes sense.
    And I do feel that the opportunity that Vercel is giving you with that accelerators time, not only can you use that to, you know, build a little bit of. Awareness around the product there. Also, I think the trip to the Bay Area will give you a chance to speak to other people and see what are some adjacencies here, right? I sense there is something that could click in this monitoring and I won't say not observable, but in the code monitoring and improvement space and you should give yourself that time in the Bay Area to explore.
    Because I think you'll land up on something that could be 100x bigger than what this is today. That is very true. And yeah, I'm also very excited to be to be going out to be going there. And I'll probably, I'll probably text you, I'll probably hit you up again in a while once I'm there. Yeah, see if I can meet any of your interesting friends. Yeah, absolutely.
    In fact, what I'll do is on email, I'll follow up with a couple of names. And if you'd like to be introduced to any of them, I'll do a double opt in so you can connect with them. They're all broadly in your age group as well, building out in the Bay Area.
    So you might get to chat with other people and see where things land. That is very kind. Thank you so much. Yeah. Awesome, man. I'm very impressed. I think what you've done at 20 turning 21 is incredible and just want to wish you the very best. I'll definitely be in touch with you.
    And if you need anything, feel free to reach out. I'll share our contact info as well. So you can text even on WhatsApp, not just on email. Well, this was good, man. Super, super stuff. And I hope you have a good U.S. trip. Best of luck. All the best, Dev. Love what you've done till now. Have a safe trip. Thank you all so much. I'm really glad we had this meeting. It's been a lot of fun. Likewise, Dev. Take care. See you. Bye-bye.
    Yo, what's up?


### KB’s Notes:
++ Technically sound (CPP with C++ at an early age)
+ High agency / transparent about what he’s built is not enough
(-ve) code gen as a problem has been solved
(-ve) no clear view on what next? wants to go after active maintanance through logs which is not an easy problem to solve
(-ve) uses GitHub as the only form of auth even though he is aware that adds a ton of friction
Takeaway: 
1. He’ll end up doing something for sure in life, just not this
1. He uses cursor to code, the fact that devs at the cutting edge use inline coding tools to build says a lot about what will stick in this industry
# **Dev (Shiro) <> DeVC**
Fri, 04 Jul 25
### **Background & Experience**
- Started coding with C++ at age 13 (competitive programming)
- Won bronze medal at national level for competitive programming
- Previously interned at Sarvam AI (2.5 months)
  - Worked on AI agents team
  - First startup office experience
### **Current Product (Shiro)**
- Started building 2 months ago
- Initially aimed to be better version of Devin with web interface
- Current features:
  - GitHub integration
  - Kanban board functionality
  - Pay-per-task pricing model (no rate limiting or token caps)
- Users primarily using for personal/side projects
- Using AWS for sandbox infrastructure (considered but didn’t switch to Daytona)
### **User Feedback & Challenges**
- Key user requests:
  - Preview capability before pull request creation
  - Browser attachment to sandbox
  - Environment variables customization
  - Terminal access
- Current limitations:
  - Limited enterprise adoption due to access concerns
  - User base dwindling after initial launch
  - Documentation challenges with integrations
### **Future Direction**
- Shifting focus from code generation to code maintenance
- Planning to build autonomous agent for:
  - Log monitoring across platforms (Vercel, AWS, Datadog)
  - Automated fix deployment
- Not currently fundraising
  - Operating on free credits
  - Waiting for right timing for venture capital
### **Next Steps**
- Dev heading to San Francisco for Vercel accelerator
- DeVC team to make introductions to Bay Area contacts
- Follow-up email with potential contact names for networking
---
Chat with meeting transcript: [https://notes.granola.ai/d/5449e209-e038-4917-987c-ca16064d0aea](https://notes.granola.ai/d/5449e209-e038-4917-987c-ca16064d0aea)
---
