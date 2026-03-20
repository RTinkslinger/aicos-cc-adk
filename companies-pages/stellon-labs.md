# Stellon Labs


**Table of contents (click to navigate)**

---

## Krishs Research for the Call 2025-08-25 
### Pointers before the Call
- Building tiny frontier AI models - specifically designed to be deployed on Edge devices i.e running locally on them completely offline (Phone / Smartphones / Wearables / Robots??)
- Divam previously worked on AI at Microsoft and built the popular offline Stable Diffusion app DiffusionBee, while Rohan is an ex-Meta AI Research scientist and CMU alumnus
- KittenTTS is remarkably small – under 25 MB (~15 million parameters)
  - Accumulated over 8,000 GitHub stars and 60,000 model downloads on Hugging Face within two weeks of release
  - Has been converted to an ONNX runtime which means it can run efficiently on any CPU
  - Supports 8 diff voices (4 male / 4 female)
  - That said, as a preview model trained on ~10% of the intended dataset, it does have some artifacts – e.g. slight graininess, occasional word cut-offs, and less prosody control than larger state-of-the-art models. (The developers acknowledge the current model is an early checkpoint and plan to improve fidelity with further training) - [https://reviewramble.com/kitten-tts-installation-review/#:~:text=%E2%9D%8C%20Cons%3A](https://reviewramble.com/kitten-tts-installation-review/#:~:text=%E2%9D%8C%20Cons%3A)
  - 13 separate Hugging Face Spaces have been created
  - Overall sentiment is that: KittenTTS’s output is not *premium studio quality* but is quite good for practical use, considering the model’s size – is echoed in several reviews
  - Kokoro TTS is ~300 MB OS and far better but then its a diff usecase compared to Kitten
- Comparison
  ![](https://prod-files-secure.s3.us-west-2.amazonaws.com/b21975bb-aebf-48e3-8c44-1573c4404129/cbecc72b-9b7a-446c-9a94-fdfe335b810d/image.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466Q67CMWCK%2F20260320%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260320T110204Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEGgaCXVzLXdlc3QtMiJIMEYCIQDjj7tA8gkjUzsBWnzomfpXD023UjGDAf79zvG0mtAm6QIhAPexwwWPjLikn3cHZBl4KcdJiTV%2FRdcqugaPcxlKjouQKv8DCDEQABoMNjM3NDIzMTgzODA1IgwDNBhoggt6o%2FYMjgQq3AMLaozZvILQTnrSumz6jGJrHeohkA8x7axDYHkbx7ZJEE46NO0%2Fw4B7OVX9XbkvlM6Mo%2F8inUq5OIeuQr3dw8UIWkZLjkfShBEy88I1lEC1CJyNyOel1p9lQdsu3Yp0G8HxtXof9s9VB4zWNk2py05B1m7%2F12iTAyqhIqZxdTMzeEn9AjspfTyzntwTQ2k7GXVOpi9KXnBr6ZTlCZ5LdN8OvO4164wgmY0mMquQICvXaZuiO%2BGQEzywyRDjT9dxmU%2BtTcZxRdAViLR65faw00rUcHrGYx3bqP7EOrOaSCKAjyK30nCOZLwyMcU0T27Fn%2FNm0qcWOotrC2Y7UXzmzPGtnc6MwYI4rB77uY8y0R4SMLhC85f8Xi7Os3%2FMmiApoHphh8yC2g4Zs4lu700%2FiUTAoHBvBHmIWmHFL2jrvSev9e4A%2B6sy46P9YvDyLcOV7lkq3RkBA1RUX5EgBtNyntcDTNTxoNKlnV3jbH1O5wQLSwFpmfZqIuPxU55RmkR64x7NKpIdgFc7lhD5lJeWF6woR27bvXhlmMB3JjlLRHiC3%2BMvDXZyg%2FBMdrwXV4gQyQ0Tjj6ySBxL820Q2XHYEWozAL7y6TSc73Y%2BuClPJZsR8hTd%2Fvz%2BMYjMCHolNTCH%2FPPNBjqkAX0aoqdYfJoHngkSjc7cZmbfE%2FLSOB9HrelbysScpUXWaNv3Foa3n8WYFuplnK3N3Y4wja00s63pncCvXbBsOEiIze3HQew6gaEhwW2CWdlF0byvk%2FBQo%2FalnLMYd%2BOgtoxin%2FLOUIiRE%2BA1dUJnQh2XkaQaIXO8of8C%2BgKffmcOSenglWR10xkrCRaWxqybN2LH559krf%2FJ4Hp55E2jfhrZc00C&X-Amz-Signature=576254fd02f0ff69ccb0201fac1708106dfe34fea8a2f0c9509350de913d35c7&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

Question:
- Here, y’all have mentioned that the model has been trained on only 10% of the dataset till now, and it's under 25 MB, which is perfect for an edge device. Post-training on the complete dataset, how much do you think the model will improve, and what size would it become? Would it still be practical for an edge device? ([https://news.ycombinator.com/item?id=44807868#:~:text=improve%20more%20and%20more%21%20But,it%20for%20consumer%20facing%20applications](https://news.ycombinator.com/item?id=44807868#:~:text=improve%20more%20and%20more%21%20But,it%20for%20consumer%20facing%20applications))
- [https://github.com/KittenML/KittenTTS/issues/40](https://github.com/KittenML/KittenTTS/issues/40)
  - Views on this discussion about the right way to calculate RTF (Real time factor)
- Chip for Inference / Optimised problem? How is this being handled at the same time?
- Whats next? Kitten STT / Vision Models?

## Rohan <> Cash / Krish 2025-08-28 
### Cashs Views:
### Overall: Maybe
EO: 7-8 | Archetype: 7-8 | FMF: 7-8 | Thesis: ? | Spikey: 0.5-1 | Price: 2
AI on edge models lab in current avatar
Wants to raise at 40-45
Unlike peers has no real traction.| launched an OSS model just to have somethign compared to peers
++ Technical spike is 1 and has the right BG with CMU and meta (both co-fos)
++ Bottoms up builders and both founders are tech and shipping oriented
++ Merit to their novel approach of using rule absed phonemisation. It’s basically akin to EXL2  quanitzation with phonemisation
+/? They want to be like mistral and be more forward deployment oriented for cos who want edge models and want to use OSS general purpose as TOFU generation
?? Would have been better if they took a more end use case backwards approach. General purpose has little merit beyond fringe use cases they are using for
?? ENough GGUF models on hugginface which people will pick and choose from for edge deployment and inference
?? What is the RTP and RTW
Net: Sharp guys and might just build something specialised, but unlikely going to be something that catches fire. Can see a mistral like journey
Next steps: Connect with Aarthi, Groq fund
Get inputs from radical VC team
Get them to meet Aditya at cota if possible

### Krishs Views:
++ Technically spiky == 1 - great extrinsics right from the school they went to work done post
(-ve) Launched purely because they were out of time
Purely from a cheque perspective - will have to put a min $250K (0.5%) in, which is tough to underwrite w/o any traction, revenue, interest?? (HuggingFace downloads and GH stars is some proxy)
?? Didn’t understand enough of the tech involved to comment (Replaced Transformers for encoding / decoding with rules based phenomisation w/o loss in quality)

### **Stellon Labs Background**
- Founders: Rohan and Divam (CMU 2019-2021, same year)
  - Both MS programs: Rohan (Robotics), Akash (AI)
  - Meta Research experience on codec avatars
  - Divam: core contributor to Lex Fridman-Mark Zuckerberg demo
- Rohan’s journey: Mumbai (Greenlawns) → private college → self-taught coding → deep learning expertise → CMU → Meta
- Applied to YC with different idea, took 2 pivots to reach current focus
### **Technical Approach & Architecture**
- Problem: Current on-device AI models either degrade performance or run too slowly (10 min/image)
- Solution: Design tiny models from day zero vs scaling down cloud models
- Key innovations:
  - Rule-based phonemizer instead of transformer tokenization
    - Eliminates 80M+ parameter minimum from encoder/decoder
  - Distillation approach: Train diffusion model → distill to basis vectors
    - Linear combination method inspired by 3D face tracking (FLAME)
    - No hallucinations since input is phonemes (real speech representation)
  - LPIPS for audio: Use audio tokenizers as feature extractors
    - Higher quality gradients in latent space
### **Market Traction & Commercial Interest**
- Launched model 2.5 weeks ago (only ~10% trained due to Demo Day pressure)
- Three main inbound categories:
  - Hardware/robotics companies for voice interfaces
  - Low-end Android devices (European company can’t economically use 11 Labs for Android users)
  - Cloud deployment (unexpected) - efficiency attracts cost-conscious users
- Raspberry Pi CEO meeting scheduled next week
- Open source strategy following Mistral model (€60M+ revenue despite not being best)
### **Fundraising & Next Steps**
- Currently raising: $5M on $45M cap
- Since Monday: $2.1M committed, additional offers pending
- No prior funding before YC
- KB’s notes: Extrinsics easy to judge → highly pedigreed/great research/exposure
- Potential Grok ecosystem fund introduction (Jonathan’s TPU background relevant)
- Need: Deck/research materials for investor sharing
### **Next Steps**
- Rohan to send availability for follow-up meeting
- 80M parameter model launch on Discord (tonight)
- Technical report release with full model (1-2 weeks)
- Groq fund introduction materials needed
---

## Update re Paras convo 2025-09-27T14:41:00.000+05:30 from founder

Yo, thanks a lot for the connect to Paras! I just spoke w him last night and it was great. We discussed that I'll try to give a talk about our next models at Lossfunk in the coming months. I asked him if he'd like to join our round but seems like investing in U.S. companies from India as an angel is a hassle. He generously offered his help whenever required.


## Deck 2025-10-18T12:04:00.000+05:30 from founder
<!-- file block -->




## Heads up note 2025-10-18T12:00:00.000+05:30 from @Rahul Mathur 

Hi team,
Sharing the heads-up note for our investment in [Stellon Labs](https://stellonlabs.com/) - an AI research lab that is building tiny frontier AI models that can run on edge devices like smartphones, wearables and embedded system

DeVC is investing $250K as part of a post YC $5.2M round at $45M post money led by Felicis Ventures (early investors in Canva, Mercor, Notion etc) 

*Note: Cash was able to generate pull with the founders given his questions regarding the LPIPS approach and 1 bit quantization; founders appreciated the team’s depth in edge models & therefore created room in this round for DeVC *


**Founders**
1. [Rohan Joshi](https://www.linkedin.com/in/rohan-m-joshi/) - CEO
  1. MS @ CMU in Robotics (2019-2021)
  1. 4 YOE @ Meta
1. [Divam Gupta](https://www.linkedin.com/in/divamgupta/) - CTO
  1. MS @ CMU in AI (2019-2021)
  1. 4 YOE @ Meta
  1. 1.5 YOE @ MSFT Research

**Investing Process**
1. **We sourced Stellon Labs as part of the YC S25 structured mining process**
  1. Their Kitten TTS model accumulated over 8,000 GitHub stars and 60,000 model downloads on Hugging Face within two weeks of release prior to us interacting with the founders
1. **Cash & Krish did the 1PE**
  1. Cash - Maybe
    1. *Net: Sharp guys and might just build something specialized, but unlikely going to be something that catches fire. Can see a Mistral like journey*
    1. *++ Technical spike is 1 and has the right BG with CMU and Meta (both CoFos)*
    1. *++ Bottoms up builders and both founders are tech and shipping oriented*
    1. *?? Would have been better if they took a more end use case backwards approach. General purpose has little merit beyond fringe use cases they are using for*
  1. Krish - Strong Maybe
    1. *++ Technically spiky == 1 - great extrinsics right from the school they went to work done post*
    1. *?? Velocity: Launched purely because they were out of time for YC S25*
    1. *?? Didn’t understand enough of the tech involved to comment (Replaced Transformers for encoding / decoding with rules based phenomisation w/o loss in quality)*
1. **Expert conversations**
  1. Radical Ventures
    1. *++ ”You want to pick a technical team here. The biz side also is fully technical and not a challenge unlike other deep tech” *
    1. *++ “Team should be able to focus on being early to the SOC deployment. Great that Stellon is already working with the Raspberry team directly”*
    1. *++ “Long tail of the device world is going to be huge and someone will have to serve. The top end like Apple, Meta, OpenAI will do their own model always. Infinitely large market with the rest “*
  1. Aarthi R (DeVC Collective & GP @ Schema Ventures)
    1. *++ “Outstanding talent at Meta”*
    1. *++ “These guys have been on the XR team, so well familiar with devices play “*
    1. *?? “Worry if meta just pays and acquihires back“*
1. **Cash closed our commitment after doing a 2PE in SF**
  1. ++ “Rohan (CEO) has always been on accelerated learning path & is compounding
  1. ?? Current live model is 20% work. Had to put something out. Their work will take time.


**Business**
1. Product
  1. Problem statement: Current on-device AI models either degrade performance or run too slowly (10 min/image)
  1. Innovation in product to create tiny edge models:
    1. Rule-based phonemizer instead of transformer tokenization
    1. Distillation approach: Train diffusion model → distill to basis vectors
    1. LPIPS for audio: Use audio tokenizers as feature extractors
1. Traction - Pre-Product
  1. Got 2.3K upvotes on Reddit ([here](https://www.reddit.com/r/LocalLLaMA/comments/1mhyzp7/kitten_tts_sota_supertiny_tts_model_less_than_25/)) on Launch Week
  1. Got 1K upvotes on Hacker News ([here](/22c29bccb6fc800d8e79c59334494720)) on Launch Week
  1. Shipped ~10% of their actual product via Kitten TTS project
  1. In conversations with Raspberry Pi CEO for partnership
1. GTM
  1. Will be a FDE motion - similar to what Mistral has deployed in the EU with Enterprise clients
  1. Focused on the long tail of non-handset hardware devices like audio speakers, walkie talkies etc
  1. From Radical Ventures: This will be a technical Sale to stakeholders in client organizations

**Round details**
This is a $5.2M round led by Felicis Ventures at a $45M cap with the following investors
1. Felicis Ventures - $2.25M
1. PeakXV - $1M
1. Angel investors
  1. Paul Graham - $100K
  1. Ooshma Garg (Gobble CEO) - $75K
  1. Kulveer Taggar - $50K
  1. Sanjay Nath - $25K

Previous round constructs
1. $125K for 7% - YC S25 investment

**Investment considerations & risks**
1. GTM risk
  1. From Cash: ?? They want to be like mistral and be more forward deployment oriented for cos who want edge models and want to use OSS general purpose as TOFU generation; Mistral journey took a while top play out
  1. From Cash: ?? Enough GGUF models on Hugging Face which people will pick and choose from for edge deployment and inference
1. Technical risk
  1. From Cash: ?? Novel approach of using rule based phonemisation
  1. From Krish: ?? Launched model 2.5 weeks ago (only ~10% trained due to Demo Day pressure)
1. Acquihire risk
  1. From Aarthi R: ?? Worry if meta just pays and acquihires back 

**Tactical considerations:**
1. Committed when? Sept’ 25
1. Closing/wire expected by when? Oct’ 25


**Market Work**
| Company / Project | Modality | Edge / On-Prem | Model size / params (public) | Typical device & indicative latency | Offline licensing | Public or Private | Total capital raised (USD) | Likely buyers & use cases | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Stellon Labs – KittenTTS | TTS | On-device (CPU-optimized) | <25 MB (~15M params) | Laptop/phone CPUs; marketed as real-time | Apache-2.0 (open-source, model repo) | Private (YC W25) | $5.35M | Mobile apps, robotics/IoT voice, privacy-first assistants | Tiny frontier AI model for edge; open-source TTS |
| Piper TTS | TTS | On-device (Raspberry Pi & PCs) | Small voice models (varies) | Raspberry Pi & CPU laptops; near-real-time | Open-source (MIT/GPL across forks) | Open-source project (no company) | N/A | Hobbyist/SMB local assistants, embedded devices | Active community; local voices on HF |
| ElevenLabs (private deployment) | TTS | Private cloud/on-prem (enterprise) | Proprietary | GPU nodes; low-latency streaming via API | Enterprise private deployment; standard API SaaS otherwise | Private | $281M (reported) | Media, games, call centers needing top quality voices | Not typically on-device; strong quality baseline |
| Cartesia – Edge (SSM library) | ASR + Audio Gen (stack) | On-device library | SSM-based (varies; optimized) | Modern mobile/edge NPUs; designed for real-time | Open-source library + commercial stack | Private | $27M (reported) | Realtime agents, embedded apps needing low-latency | On-device SSMs for realtime |
| Picovoice – Cheetah / Leopard | STT (streaming & batch) | On-device SDKs | Compact engine (langs vary) | Mobile/embedded CPUs; realtime streaming | Commercial SDK; private-by-design | Private | ~$0.5M (reported) | OEMs, home devices, regulated/offline environments | Wakeword + ASR portfolio |
| Deepgram – On-Prem | STT | On-prem (self-hosted) & edge-capable | Proprietary | GPU servers / local clusters; low-latency streaming | Enterprise on-prem licensing | Private | $85.9M (reported) | Enterprises with data residency & privacy needs | Self-serve on-prem guides available |
| Keen Research – KeenASR | STT | On-device SDK (iOS/Android/Web/ChromeOS/Linux) | Not public; small mobile models | Mobile devices & browsers; local realtime | Commercial SDK | Private (privately owned) | Undisclosed / appears bootstrapped | Aviation, field apps, kids apps; no-cloud dependency | Web SDK runs locally in browser |
| NVIDIA – Riva (Jetson) | ASR + TTS | On-prem & Jetson edge deploys | Multiple models; GPU-optimized | Jetson/X86 GPUs; realtime pipelines | NVIDIA enterprise licensing | Public (NVDA) | Public company – N/A | Robotics, kiosks, industrial edge with GPUs | DeepStream plugin for Riva ASR |
| Whisper.cpp / faster-whisper | STT | On-device (CPU/GPU) | Tiny/base/small variants (39M–244M params) | RPi4/5 real-time (tiny.*) with tweaks; mobile/Jetson feasible | Open-source (MIT/permissive) | Open-source project (no company) | N/A | DIY/local assistants, developer tools, research | Quantization + CTranslate2 speedups |
| Vosk (AlphaCephei) | STT | On-device (Android/iOS/RPi) & servers | ~50–100 MB models; many langs | Small devices; streaming 'zero-latency' API | Apache-2.0 | Private (Alpha Cephei) | $0 (unfunded per trackers) | Low-end devices, offline transcription, chatbots | Kaldi-based toolkit |



Here is the link to the [Notion database](/22c29bccb6fc8019863fe1faf3b37c44#27b29bccb6fc8023a46bdf544edc119a). Please let us know if there are any questions regarding this.

Best wishes
Rahul

