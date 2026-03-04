"""
Notion Rich Digest Template Generator
Converts content pipeline analysis data into rich Notion-flavored markdown
for Content Digest DB pages. Replaces PDF generation.

Design principles:
- Mobile-first (Notion app renders beautifully)
- Scannable dashboard at top
- Expandable detail sections via toggles
- Emoji-based visual hierarchy (replaces PDF color coding)
- Shareable via Notion public link
"""

def generate_notion_digest(data: dict) -> str:
    """
    Generate rich Notion-flavored markdown for a content digest page.

    Args:
        data: Analysis dict with fields matching Content Digest DB properties

    Returns:
        Notion-flavored markdown string for page content
    """
    sections = []

    # ═══════════════════════════════════════════════
    # 1. HEADER BAR — Channel, duration, type, link
    # ═══════════════════════════════════════════════
    meta_parts = []
    if data.get('channel'):
        meta_parts.append(f"**{data['channel']}**")
    if data.get('duration'):
        meta_parts.append(f"⏱ {data['duration']}")
    if data.get('content_type'):
        meta_parts.append(data['content_type'])
    if data.get('upload_date'):
        meta_parts.append(f"📅 {data['upload_date']}")

    header = " · ".join(meta_parts)
    if data.get('url'):
        header += f"\n\n🔗 [Watch Source]({data['url']})"

    sections.append(header)
    sections.append("---")

    # ═══════════════════════════════════════════════
    # 2. DASHBOARD STRIP — Badges + counts + buckets
    # ═══════════════════════════════════════════════

    # Net Newness badge
    newness = data.get('net_newness', 'Unknown')
    newness_emoji = {
        'Breakthrough': '🟣',
        'Significant': '🔵',
        'Additive': '🟢',
        'Reinforcing': '🟡',
        'Redundant': '⚪'
    }.get(newness, '⚫')

    # Relevance badge
    relevance = data.get('relevance_score', 'Unknown')
    relevance_emoji = {
        'Critical': '🔴',
        'High': '🟠',
        'Medium': '🟡',
        'Low': '⚪'
    }.get(relevance, '⚫')

    dashboard = f"> {newness_emoji} **Net Newness:** {newness}  ·  {relevance_emoji} **Relevance:** {relevance}"

    # Counts
    counts = []
    watch_sections = _parse_watch_sections(data.get('watch_sections', ''))
    contra_signals = _parse_contra_signals(data.get('contra_signals', ''))
    rabbit_holes = _parse_rabbit_holes(data.get('rabbit_holes', ''))
    actions = _parse_actions(data.get('proposed_actions', ''))

    if watch_sections:
        counts.append(f"📺 {len(watch_sections)} sections")
    if contra_signals:
        counts.append(f"⚡ {len(contra_signals)} contra")
    if rabbit_holes:
        counts.append(f"🕳️ {len(rabbit_holes)} rabbit holes")
    if actions:
        counts.append(f"✅ {len(actions)} actions")

    if counts:
        dashboard += "\n> " + "  ·  ".join(counts)

    # Connected buckets
    buckets = data.get('connected_buckets', [])
    if buckets:
        bucket_tags = "  ".join([f"`{b}`" for b in buckets])
        dashboard += f"\n> \n> **Buckets:** {bucket_tags}"

    sections.append(dashboard)
    sections.append("---")

    # ═══════════════════════════════════════════════
    # 3. ESSENCE — Core arguments, evidence, frameworks
    # ═══════════════════════════════════════════════
    essence = data.get('essence_notes', '')
    if essence:
        essence_block = "## 🧠 Essence\n"

        # Parse essence into sub-sections if structured
        essence_parts = _parse_essence(essence)

        if essence_parts.get('core_arguments'):
            essence_block += "\n**Core Arguments**\n"
            for arg in essence_parts['core_arguments']:
                essence_block += f"- {arg}\n"

        if essence_parts.get('evidence'):
            essence_block += "\n**Evidence & Data**\n"
            for ev in essence_parts['evidence']:
                essence_block += f"- {ev}\n"

        if essence_parts.get('frameworks'):
            essence_block += "\n**Frameworks**\n"
            for fw in essence_parts['frameworks']:
                essence_block += f"- {fw}\n"

        if essence_parts.get('key_quotes'):
            essence_block += "\n**Key Quotes**\n"
            for q in essence_parts['key_quotes']:
                essence_block += f"> {q}\n\n"

        if essence_parts.get('predictions'):
            essence_block += "\n**Predictions**\n"
            for p in essence_parts['predictions']:
                essence_block += f"- {p}\n"

        # If essence wasn't structured, render as-is
        if not any(essence_parts.values()):
            essence_block += f"\n{essence}\n"

        sections.append(essence_block)

    # ═══════════════════════════════════════════════
    # 4. NET NEWNESS ASSESSMENT
    # ═══════════════════════════════════════════════
    newness_reasoning = data.get('net_newness_reasoning', '')
    if newness_reasoning:
        sections.append(f"## {newness_emoji} Net Newness: {newness}\n\n{newness_reasoning}")

    # ═══════════════════════════════════════════════
    # 5. WATCH THESE SECTIONS — Timestamp cards
    # ═══════════════════════════════════════════════
    if watch_sections:
        watch_block = "## 📺 Watch These Sections\n"
        for ws in watch_sections:
            watch_block += f"\n<details>\n<summary>⏱ {ws.get('timestamp', '')} — {ws.get('title', '')}</summary>\n\n"
            if ws.get('why_watch'):
                watch_block += f"{ws['why_watch']}\n"
            if ws.get('connects_to'):
                watch_block += f"\n**Connects to:** {ws['connects_to']}\n"
            watch_block += "\n</details>\n"
        sections.append(watch_block)

    # ═══════════════════════════════════════════════
    # 6. CONTRA SIGNALS
    # ═══════════════════════════════════════════════
    if contra_signals:
        contra_block = "## ⚡ Contra Signals\n"
        for cs in contra_signals:
            strength_icon = {
                'Strong': '🔴',
                'Moderate': '🟠',
                'Weak': '🟡'
            }.get(cs.get('strength', ''), '⚪')

            contra_block += f"\n> {strength_icon} **{cs.get('what', '')}** ({cs.get('strength', '')})\n"
            if cs.get('evidence'):
                contra_block += f"> {cs['evidence']}\n"
            if cs.get('implication'):
                contra_block += f"> *Implication: {cs['implication']}*\n"
            contra_block += "\n"
        sections.append(contra_block)

    # ═══════════════════════════════════════════════
    # 7. RABBIT HOLES
    # ═══════════════════════════════════════════════
    if rabbit_holes:
        rabbit_block = "## 🕳️ Rabbit Holes\n"
        for rh in rabbit_holes:
            rabbit_block += f"\n<details>\n<summary>🔮 {rh.get('title', '')}</summary>\n\n"
            if rh.get('what'):
                rabbit_block += f"{rh['what']}\n"
            if rh.get('why_matters'):
                rabbit_block += f"\n**Why it matters:** {rh['why_matters']}\n"
            if rh.get('entry_point'):
                rabbit_block += f"\n**Entry point:** {rh['entry_point']}\n"
            if rh.get('newness'):
                rabbit_block += f"\n**Newness:** {rh['newness']}\n"
            rabbit_block += "\n</details>\n"
        sections.append(rabbit_block)

    # ═══════════════════════════════════════════════
    # 8. CONNECTIONS & ACTIONS
    # ═══════════════════════════════════════════════
    connections_block = ""

    # Portfolio connections
    portfolio = data.get('portfolio_relevance', '')
    thesis_conn = data.get('thesis_connections', '')

    if portfolio or thesis_conn or actions:
        connections_block = "## 🔗 Connections & Actions\n"

    if thesis_conn:
        connections_block += "\n### Thesis Threads\n"
        thesis_items = _parse_thesis_connections(thesis_conn)
        for t in thesis_items:
            stance_icon = {'for': '✅', 'against': '❌', 'new_angle': '🔄', 'nuance': '🔀'}.get(t.get('stance', ''), '➡️')
            strength = t.get('strength', '')
            connections_block += f"\n> {stance_icon} **{t.get('name', '')}** ({strength})\n"
            if t.get('reasoning'):
                connections_block += f"> {t['reasoning']}\n"
            connections_block += "\n"

    if portfolio:
        connections_block += "\n### Portfolio Relevance\n"
        portfolio_items = _parse_portfolio(portfolio)
        for p in portfolio_items:
            connections_block += f"\n> 🏢 **{p.get('company', '')}**\n"
            if p.get('reasoning'):
                connections_block += f"> {p['reasoning']}\n"
            connections_block += "\n"

    if actions:
        connections_block += "\n### Proposed Actions\n"
        # Sort by priority
        priority_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}
        actions.sort(key=lambda a: priority_order.get(a.get('priority', 'P3'), 4))

        for a in actions:
            p = a.get('priority', 'P3')
            p_icon = {'P0': '🔴', 'P1': '🟠', 'P2': '🟡', 'P3': '⚪'}.get(p, '⚪')
            connections_block += f"- {p_icon} **{p}** — {a.get('action', '')}\n"

    if connections_block:
        sections.append(connections_block)

    # ═══════════════════════════════════════════════
    # 9. TOPIC MAP (bonus — not in PDF but useful on mobile)
    # ═══════════════════════════════════════════════
    topic_map = data.get('topic_map', '')
    if topic_map:
        topic_block = "## 🗺️ Topic Map\n\n"
        topic_block += "<details>\n<summary>Full timestamp breakdown</summary>\n\n"
        for line in topic_map.strip().split('\n'):
            line = line.strip()
            if line:
                topic_block += f"- {line}\n"
        topic_block += "\n</details>\n"
        sections.append(topic_block)

    # ═══════════════════════════════════════════════
    # 10. FOOTER
    # ═══════════════════════════════════════════════
    sections.append("---")
    sections.append("*AI CoS Content Pipeline v5 · Notion Digest*")

    return "\n\n".join(sections)


# ═══════════════════════════════════════════════════
# PARSERS — Handle the text-blob property formats
# from Content Digest DB
# ═══════════════════════════════════════════════════

def _parse_watch_sections(text: str) -> list:
    """Parse 'Watch These Sections' property text into structured items."""
    if not text:
        return []
    items = []
    # Format: "10:22-11:45 - Title. Description. Connects to X."
    for block in text.split('\n'):
        block = block.strip()
        if not block:
            continue
        # Try to extract timestamp and title
        parts = block.split(' - ', 2)
        if len(parts) >= 2:
            timestamp = parts[0].strip()
            rest = ' - '.join(parts[1:])
            # Split on '. ' to get title vs description
            sentences = rest.split('. ')
            title = sentences[0] if sentences else rest
            why_watch = '. '.join(sentences[1:-1]) if len(sentences) > 2 else (sentences[1] if len(sentences) > 1 else '')
            connects_to = ''
            for s in sentences:
                if s.lower().startswith('connects to'):
                    connects_to = s.replace('Connects to ', '').replace('connects to ', '').strip('.')
            items.append({
                'timestamp': timestamp,
                'title': title,
                'why_watch': why_watch,
                'connects_to': connects_to
            })
        else:
            items.append({'timestamp': '', 'title': block, 'why_watch': '', 'connects_to': ''})
    return items

def _parse_contra_signals(text: str) -> list:
    """Parse 'Contra Signals' property text into structured items."""
    if not text:
        return []
    items = []
    # Format: "What (Strength): evidence. implication."
    for block in text.split('\n'):
        block = block.strip()
        if not block:
            continue
        # Try to extract strength in parentheses
        import re
        match = re.match(r'(.+?)\s*\((\w+)\)(?:\s*:\s*|\s*-\s*)(.+)', block)
        if match:
            what = match.group(1).strip()
            strength = match.group(2).strip()
            rest = match.group(3).strip()
            items.append({
                'what': what,
                'strength': strength,
                'evidence': rest,
                'implication': ''
            })
        else:
            items.append({'what': block, 'strength': '', 'evidence': '', 'implication': ''})
    return items

def _parse_rabbit_holes(text: str) -> list:
    """Parse 'Rabbit Holes' property text into structured items."""
    if not text:
        return []
    items = []
    # Format: "Title - description"
    for block in text.split('\n'):
        block = block.strip()
        if not block:
            continue
        parts = block.split(' - ', 1)
        if len(parts) == 2:
            items.append({
                'title': parts[0].strip(),
                'what': parts[1].strip(),
                'why_matters': '',
                'entry_point': '',
                'newness': ''
            })
        else:
            items.append({'title': block, 'what': '', 'why_matters': '', 'entry_point': '', 'newness': ''})
    return items

def _parse_actions(text: str) -> list:
    """Parse 'Proposed Actions' property text into structured items."""
    if not text:
        return []
    items = []
    import re
    for line in text.split('\n'):
        line = line.strip().strip('- ')
        if not line:
            continue
        # Extract priority like (P0), (P1), etc.
        match = re.search(r'\(P(\d)\)', line)
        if match:
            priority = f"P{match.group(1)}"
            action = re.sub(r'\s*\(P\d\)\s*\.?\s*', '', line).strip().rstrip('.')
        else:
            priority = 'P3'
            action = line.rstrip('.')
        items.append({'priority': priority, 'action': action})
    return items

def _parse_essence(text: str) -> dict:
    """Parse essence notes into structured sub-sections."""
    result = {
        'core_arguments': [],
        'evidence': [],
        'frameworks': [],
        'key_quotes': [],
        'predictions': []
    }
    if not text:
        return result

    # The essence is typically a block of text with sections separated by
    # "Frameworks:", "Data:", etc.
    current_section = 'core_arguments'

    lines = text.split('. ')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        lower = line.lower()
        if lower.startswith('framework'):
            current_section = 'frameworks'
            line = line.split(':', 1)[-1].strip() if ':' in line else ''
        elif lower.startswith('data:') or lower.startswith('data '):
            current_section = 'evidence'
            line = line.split(':', 1)[-1].strip() if ':' in line else ''
        elif lower.startswith('prediction'):
            current_section = 'predictions'
            line = line.split(':', 1)[-1].strip() if ':' in line else ''
        elif lower.startswith('key quote'):
            current_section = 'key_quotes'
            line = line.split(':', 1)[-1].strip() if ':' in line else ''

        if line and current_section in result:
            # Split on periods that separate distinct points
            result[current_section].append(line.rstrip('.'))

    return result

def _parse_thesis_connections(text: str) -> list:
    """Parse thesis connections text."""
    if not text:
        return []
    items = []
    import re
    # Format: "Name (stance, Strength): reasoning"
    for block in text.split('\n'):
        block = block.strip()
        if not block:
            continue
        match = re.match(r'(.+?)\s*\((\w+),\s*(\w+)\)(?:\s*[-:]\s*)(.+)', block)
        if match:
            items.append({
                'name': match.group(1).strip(),
                'stance': match.group(2).strip(),
                'strength': match.group(3).strip(),
                'reasoning': match.group(4).strip()
            })
        else:
            # Try simpler format
            parts = block.split(' - ', 1)
            items.append({
                'name': parts[0].strip() if parts else block,
                'stance': '',
                'strength': '',
                'reasoning': parts[1].strip() if len(parts) > 1 else ''
            })
    return items

def _parse_portfolio(text: str) -> list:
    """Parse portfolio relevance text."""
    if not text:
        return []
    items = []
    # Format: "Company - reasoning"
    for block in text.split('\n'):
        block = block.strip()
        if not block:
            continue
        parts = block.split(' - ', 1)
        if len(parts) == 2:
            items.append({'company': parts[0].strip(), 'reasoning': parts[1].strip()})
        else:
            items.append({'company': block, 'reasoning': ''})
    return items


# ═══════════════════════════════════════════════════
# NOTION PAGE CREATOR — Uses the template to build pages
# ═══════════════════════════════════════════════════

def build_page_from_properties(props: dict) -> str:
    """
    Convert Content Digest DB property values into rich page content.
    This is the main entry point — takes raw Notion properties
    (as returned by notion-fetch) and produces the digest markdown.
    """
    data = {
        'channel': props.get('Channel', ''),
        'duration': props.get('Duration', ''),
        'content_type': props.get('Content Type', ''),
        'upload_date': props.get('date:Upload Date:start', ''),
        'url': props.get('Video URL', ''),
        'net_newness': props.get('Net Newness', ''),
        'relevance_score': props.get('Relevance Score', ''),
        'connected_buckets': props.get('Connected Buckets', []),
        'essence_notes': props.get('Essence Notes', ''),
        'watch_sections': props.get('Watch These Sections', ''),
        'contra_signals': props.get('Contra Signals', ''),
        'rabbit_holes': props.get('Rabbit Holes', ''),
        'thesis_connections': props.get('Thesis Connections', ''),
        'portfolio_relevance': props.get('Portfolio Relevance', ''),
        'proposed_actions': props.get('Proposed Actions', ''),
        'topic_map': props.get('Topic Map', ''),
        'summary': props.get('Summary', ''),
    }
    return generate_notion_digest(data)


if __name__ == '__main__':
    # Test with sample data
    test_data = {
        'channel': 'a16z',
        'duration': '54:36',
        'content_type': 'Interview',
        'upload_date': '2026-02-28',
        'url': 'https://www.youtube.com/watch?v=Kdql4I-NJ0M',
        'net_newness': 'Additive',
        'relevance_score': 'High',
        'connected_buckets': ['New Cap Tables', 'Deepen Existing', 'Thesis Evolution'],
        'essence_notes': 'AI reinvents computer itself (steam/electricity scope). All human processes restructure around AI-native architectures in 5-10 years. Market sizing invalid when fundamental capability breakthrough. Supply-driven: new suppliers create previously invisible demand. 10x pattern: new architecture + new economics = old market × 10-1000. Real world big, messy, hostile; great products fail without founder psychology. Founder variable is core; everything else secondary. Zoomer founders best-trained via self-education + AI-native. AI accelerates R&D via capital deployability at scale. Frameworks: Venture Triangle in Breakthrough (market sizing irrelevant; focus on founder psychology). Supply-Driven vs Demand-Driven. 10x Pattern: architecture > economics > supply > demand. Real-World Execution (product ≠ company). Reputation Compounding (16-year accumulation drives 50x capital raised). Data: PeopleSoft to Workday ($1.5B to $15B+). A16Z: Fund 1 ($300M) to Fund 6 ($15B on reputation).',
        'watch_sections': '10:22-11:45 - 10x Market Mechanism: Cloud Precedent. Ben maps on-prem to cloud 10x expansion. Precise playbook for market expansion. Connects to SaaS Death thesis.\n16:02-20:15 - Venture Triangle Collapse. Market sizing breaks when capability shifts. Cannot validate with math.\n23:46-25:10 - Real World Friction: 8 Billion Voters. Marc: product doesn\'t equal company. Execution matters more than tech.\n46:54-48:05 - AI Acceleration of R&D Economics. Money now accelerates capability gaps. Elon caught OpenAI/Anthropic.\n52:02-54:20 - Zoomer Founders. Most capable generation. AI-native, self-educated, unapologetic.',
        'contra_signals': 'Product-centric view underweights regulatory friction (Moderate): healthcare, financial, aviation constrain adoption differently.\nAssumes Zoomer founders execute better despite less life experience (Moderate): haven\'t met all people or dealt with all real-world issues.\n10x assumes perfect execution (Weak): Ben acknowledges real world rejects ideas; thesis rests on multiple 10x all requiring similar execution.',
        'rabbit_holes': 'Harness Layer Consolidation vs. Fragmentation - single dominant orchestration or fragmented tooling?\nVoice AI Moat in Healthcare Regulatory Sandbox - how do regulated domains maintain moats?\nFounder Psychology & Survivorship Bias - is Zoomer advantage real or narrative?\nSupply-Driven Markets Without Demand Saturation - when does supply abundance saturate specific markets?\nReputation as Venture Brand - does reputation become table stakes?',
        'thesis_connections': 'SaaS Death / Agentic Replacement (for, Strong) - Ben\'s 10x mechanism (on-prem to cloud to AI-native) validates that architecture shift displaces existing systems. Timeline open: 2-3 years or 5-10 years.\nAgentic AI Infrastructure (new_angle, Strong) - Marc/Ben don\'t specify harness layer consolidation question: single dominant orchestration or fragmented tooling?',
        'portfolio_relevance': 'Smallest AI - voice AI solves healthcare but Ben/Marc don\'t address regulated domains moat persistence.\nCodeAnt AI - automated code review maps to \'AI building stuff\'; success depends on synthesis quality + workflow embedding.\nHighperformr AI - supply-driven thesis applies; supply could saturate faster than demand.\nUnifize - vertical SaaS directly exposed to SaaS Death thesis.\nStep Security - infrastructure layer positioning validated; moat depends on consolidation level.\nAll Portfolio - real-world friction (\'8 billion voters\') and founder psychology matter equally with product.',
        'proposed_actions': 'Depth research: harness layer consolidation in AI infrastructure. Interview portfolio CTOs on orchestration assumptions (P0).\nPortfolio check-in: Smallest AI on healthcare moat (regulatory vs. tech) (P1).\nResearch: benchmark Zoomer vs. millennial founder success rates (P2).\nProduct deep-dive: Unifize and CodeAnt agentic AI migration roadmaps (P1).\nCompetitive analysis: AI-native dev tools vs. CodeAnt defensibility (P2).\nMeeting: interview Z47 LPs on fund conviction under AI reinvention (P1).\nThesis update: SaaS Death timing consolidating 10x mechanism evidence (P1).\nContent follow-up: request a16z research on harness layer consolidation (P2).',
        'topic_map': '00:00-01:00: Opening - Real World is Big and Messy.\n01:00-05:26: Media Ecosystem Shift - Substack and free speech.\n05:26-10:22: Supply-Driven Markets - Substack thesis.\n10:22-16:02: 10x Mechanism - cloud vs on-prem precedent.\n16:02-17:32: Reinvented Computer - AI as new foundation.\n17:32-23:46: Venture Triangle Breakdown - market sizing impossible.\n23:46-26:27: Real World Execution - product vs company.\n26:27-34:00: A16Z Culture and dream builders.\n34:00-46:54: Reputation compounding and fund raise.\n46:54-52:02: AI Acceleration of R&D - Elon and foundation models.\n52:02-54:30: Zoomer Founders - AI-native, unapologetic.\n54:30-54:36: Closing.'
    }

    result = generate_notion_digest(test_data)
    print(result)
