# Adversarial Analysis Protocol

A structured disagreement framework for investment thesis reasoning, action evaluation, and conviction assessment. Adapted from structured multi-perspective deliberation research for Aakash Kumar's AI CoS system.

**Inspired by:** Nyk's Council of High Intelligence (structured adversarial deliberation with polarity pairs and anti-recursion). We don't use their system — we use the method, rebuilt for investing.

**Core insight:** A single reasoning pass produces polished, confident output from one analytical tradition. It sounds balanced. It isn't. Adversarial analysis externalizes disagreement by forcing multiple perspectives to engage with each other before converging.

---

## The 7 Investment Lenses

Each lens has: an analytical method, what it uniquely sees, and its declared blind spot.

```
LENS                METHOD                              SEES                                    MISSES
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Contrarian          Invert the consensus.               The crowd's blind spot. What            Can become reflexive
                    What must be true for                everyone assumes but hasn't             contrarianism — opposing
                    the majority to be wrong?            tested. Overshoot/undershoot.           consensus just because it
                                                                                                exists.

First Principles    Strip away analogy and               Hidden complexity disguised as          Dismisses pattern
                    convention. Decompose to             "that's how it's done."                 recognition and valid
                    irreducible truths.                  Structural advantages/flaws.            historical analogies.

Pattern Matcher     Where has this happened              Historical base rates. How              Over-indexes on surface
                    before? What's the closest           similar situations actually             similarity. "This time
                    analogy and how did it               resolved. Survivorship bias             is different" is sometimes
                    resolve?                             in narratives.                          true.

Network Thinker     Map the stakeholders.                Second-order effects. Who               Can lose sight of
                    Who gains, who loses,                gains power, who loses it.              fundamental value by
                    what are the second-order            Alliance shifts. Information            over-weighting politics.
                    effects?                             asymmetries between actors.

Risk Architect      Pre-mortem. Assume this              Tail risks. Correlated                  Can paralyze with risk
                    fails catastrophically.              failures. What kills the                enumeration. Not every
                    Work backwards to why.               thesis, not just weakens it.            risk is decision-relevant.

Timing Strategist   Is this the right moment?            Catalysts. Dependency chains.           Can justify indefinite
                    What must happen before              "Too early" vs "too late"               delay. Waiting for the
                    this becomes actionable?             signals. Market windows.                perfect moment = missing
                                                                                                it.

Founder Lens        Would you back THIS team             Execution capability gaps.              Can over-index on founder
                    to execute THIS plan in              Team composition vs. problem            charisma vs. structural
                    THIS market?                         shape. Builder vs. operator             market dynamics.
                                                        mismatch.
```

---

## The 4 Polarity Pairs

These prevent groupthink. Every perspective has a structural opponent.

| Pair | Tension | When It Matters |
|------|---------|-----------------|
| **Contrarian ↔ Pattern Matcher** | "Everyone is wrong" vs "This has happened before and here's how it ended." Forces the contrarian to explain why THIS time is different. Forces the pattern matcher to justify the analogy. | Thesis conviction assessment |
| **First Principles ↔ Network Thinker** | Structural truth vs messy human reality. The thesis might be structurally sound but fail because incentives are misaligned. Or it might look messy but work because the right people are behind it. | Action evaluation, company assessment |
| **Risk Architect ↔ Timing Strategist** | "This could fail because..." vs "The window is now." Forces risk to be weighed against opportunity cost of inaction. Prevents both paralysis and recklessness. | Action prioritization, investment timing |
| **Founder Lens ↔ First Principles** | "This team can execute" vs "The structural logic is flawed regardless of team." Great founders can't save broken markets. Great markets can survive mediocre founders. Which dominates here? | Investment decisions, follow-on evaluation |

The 7th lens (whichever isn't paired) serves as a **swing vote** — it has no structural opponent and is selected based on the domain.

---

## The Protocol: 3 Rounds

### Round 1: Independent Analysis
Each selected lens receives the problem and produces a standalone assessment.

**Template per lens (200 words max):**
```
## [Lens Name] Analysis

**Essential question:** [The one question this lens asks]
**Assessment:** [Core analysis from this perspective]
**Verdict:** [Clear position: for/against/conditional, with conditions stated]
**Confidence:** [High/Medium/Low + why]
**Blind spot disclosure:** [Where this lens might be wrong]
```

All lenses execute in parallel.

### Round 2: Cross-Examination
Each lens receives ALL Round 1 outputs and must answer:

1. **Which position do you most disagree with, and why?** (Must name the lens)
2. **Which insight from another lens strengthens your own position?**
3. **What, if anything, changed your view?**
4. **Restated position** (150 words max)

Must engage at least 2 other lenses by name. This is where value emerges — the Contrarian has to explain why the Pattern Matcher's analogy is wrong. The Risk Architect has to weigh the Timing Strategist's window argument.

### Round 3: Crystallization
Each lens states final position in **50 words or fewer**. No new arguments. Convergence only.

---

## Anti-Recursion Rules

**The Contrarian Lock:** If the Contrarian re-inverts a position that has already been addressed with evidence, they must state their own positive thesis in 50 words. No more inversion.

**Depth Limit:** Any lens may question another lens's position at most 2 levels deep. After that: state your own position.

**Exchange Limit:** If two lenses exchange more than 2 messages, the protocol forces Round 3 for both.

**Time Box:** The entire protocol completes in 3 rounds. No extensions. Unresolved disagreements are preserved in the Minority Report, not debated further.

---

## Domain Triads

Pick 3 lenses (with at least 1 polarity pair) based on the domain. The third lens is the swing vote.

```
DOMAIN                    TRIAD                                           WHY
───────────────────────────────────────────────────────────────────────────────────────────
Thesis Conviction         Contrarian + Pattern Matcher + First Principles  invert → historical check → structural truth
Action Evaluation         Risk Architect + Timing Strategist + Network     risk → urgency → stakeholder map
Company Assessment        First Principles + Founder Lens + Pattern Match  structural → execution → base rate
Follow-on Decision        Risk Architect + Pattern Matcher + Founder Lens  what kills it → where it's heading → can they do it
New Thesis Creation       Contrarian + First Principles + Timing           is this real → what's structurally true → is it time
Competitive Intelligence  Network Thinker + Risk Architect + First Princ.  who gains → what breaks → what's fundamental
Content Analysis          Pattern Matcher + Contrarian + Timing            seen before → what's new → why now
Meeting Prep              Network Thinker + Founder Lens + First Princ.    stakeholders → person → structural fit
```

---

## Output Format

```markdown
## Adversarial Analysis: [Decision/Question]

### Lenses Selected
[Triad name] — [Lens 1], [Lens 2], [Lens 3]

### Round 1: Independent Assessments
[Each lens's 200-word analysis]

### Round 2: Cross-Examination
[Each lens's response to the others]

### Consensus Position
[What 2/3+ lenses agree on, if anything]

### Key Tensions
[The unresolved disagreements — these are the most valuable output]

### Minority Report
[The dissenting position and why it matters]

### Conviction Impact
[How this analysis should move conviction: ↑/↓/↔ and by how much]
[IDS notation for the strongest signals: ++, +, +?, ?, ??, -]

### Recommended Actions
[Scored actions emerging from the analysis]
```

---

## Decision Rules

- **2/3 majority** → Consensus position. Dissent recorded in Minority Report.
- **No majority** → Present the dilemma with each position clearly stated. Do NOT force artificial consensus.
- **Domain expert weighting** → The lens whose domain most directly matches the problem gets tie-breaking weight.
- **Minority Report is mandatory** → Even in consensus, the dissenting view is recorded. Sometimes it's the most valuable output. A well-argued minority position is a leading indicator.

---

## When to Use

**Use for:**
- Thesis conviction changes (especially ↑ to High or ↓ to Low)
- Actions scoring ≥ 7 that involve significant commitment
- New thesis thread creation (is this genuinely new or fragmented?)
- Follow-on investment evaluation
- Strategic decisions with real trade-offs
- Content that produces contra signals against active thesis

**Do NOT use for:**
- Routine content analysis (use standard analysis framework)
- Clear factual questions
- Actions scoring < 4 (not worth the deliberation cost)
- Incremental evidence that doesn't change conviction

**The sweet spot:** Decisions where you already have an inclination but suspect you're missing something. The protocol surfaces what you're not seeing — structured, with the disagreements visible.

---

## Integration with ENIAC

When ENIAC encounters content that:
- Produces a **Strong contra signal** against an Active thesis → trigger `thesis-conviction` triad
- Proposes an action **scoring ≥ 8** with strategic implications → trigger `action-evaluation` triad
- Suggests a **new thesis thread** → trigger `new-thesis-creation` triad
- Touches a thesis where conviction is about to move from Evolving → Low/Medium/High → trigger `thesis-conviction` triad

ENIAC can run the protocol internally (sequential lens analysis within its context) or spawn 3 subagents (one per lens) for true parallel deliberation.

The output's **Conviction Impact** section feeds directly into thesis_threads evidence updates. The **Key Tensions** become open key questions. The **Minority Report** becomes contra evidence.

---

## Adaptation Notes

This protocol replaces generic "think about pros and cons" with structured adversarial reasoning. The value isn't in the individual lens outputs — it's in the cross-examination (Round 2) where lenses must engage with positions they disagree with.

The 7 lenses and 4 polarity pairs are calibrated for venture capital / growth equity decision-making. They can be extended:
- Add an **LP Lens** (how does the LP see this allocation?) for fund-level decisions
- Add a **Regulatory Lens** for regulated industry thesis work
- Add a **Technical Moat Lens** for deep-tech evaluation

Keep total lenses ≤ 9 per analysis. The cross-examination round scales O(n²) — more lenses means more surface area but less depth per exchange.
