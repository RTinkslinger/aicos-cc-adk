---
company: Stellon Labs
notion_page_id: 29629bcc-b6fc-8148-b08e-f20d3dbb2334
source: portfolio_db
fetched: 2026-03-20
---

**Table of contents**

---



## Founders <> RM / Cash (SF 2025-11-11)

Notes

1. Samsung Next is investing

2. Have realised that the money is in Vision but focusing on speech for now

3. Speech is Consumer Electronics

4. Raspberry Pi not interested in Speech

5. Raspberry Pi introduced them to customers

6. Speech model 3 will likely be considered by Samsung

7. To connect with Spot AI and ODMs in China

8. Angel cheque for network access - Ramesh Raskar and Anand Lalwani

9. UC Berkeley Frontier Labs is on the cap table too

10. C++ kernel engineer, request Ashish from HC to reach out

11. Audio quality is the main problem

12. Vison push later in the year will also require ASIC partnerships

13. Should do an event later next year with Paras for hiring in India

14. IIT Madras introduction to Rama who Cash knows

15. Publishing papers from Q1 next CY







## Kitten TTS launch 2026-03-19T14:37:00.000-07:00 


---
*Stellon Labs / Kitten TTS — HN Launch Note*Show HN | 235 pts | 71 comments | github.com/KittenML/KittenTTS
---
*THE LAUNCH*
Three new Kitten TTS models released: 80M, 40M, and 14M parameters. The 14M variant is under 25MB and claims SOTA expressivity among models of similar size. All three are a major step up from the previous release (founder notes the new 15M is already better than the old 80M).
Key specs:• English-only, 8 voices (4M / 4F)• Quantized int8 + fp16, ONNX runtime• Runs on Raspberry Pi, low-end phones, wearables, browsers — no GPU needed• Demo on HuggingFace Spaces
Roadmap teased: multilingual model, mobile SDK (~2 weeks out), voice cloning model by May (experimenting 15M → 500M range), STT models coming soon.
---
*KEY COMMENT THEMES*
*1. Quality reception — positive*General consensus: impressive for the size. One commenter ran it via an AI assistant (Discord), got it deployed and benchmarked within minutes. Intel 9700 CPU: ~1.5x realtime on 80M. Main critique: voices sound "cartoon-ish" — rohan acknowledged this, says professional voices are already in progress.
*2. Prosody is the open problem*Raised by multiple commenters. Small models generally struggle here — rhythm, emphasis, handling English words in non-English phrases. Rohan's take: Kokoro is the benchmark to beat; next release targets Kokoro quality at ~1/5 the size.
*3. Mobile / on-device use cases generating real demand*• Epub-to-audiobook (replace Moon+ built-in TTS) — rohan pointed to someone already building this• Android TTS replacement — mobile SDK ETA ~2 weeks• Voice assistants — voice cloning highly requested
*4. Voice cloning — high excitement*Most upvoted ask. Rohan confirmed: cloning model by May. Experimenting with 15M-param cloning approach.
*5. Repo gaps flagged*• No GPU example in the codebase (rohan: will add)• No side-by-side comparison across all 4 models (rohan: will add)• Expressive control tags ([laughs], [urgently], pitch/speed) — not yet supported, noted as future direction
---
Ask me anything on this.
