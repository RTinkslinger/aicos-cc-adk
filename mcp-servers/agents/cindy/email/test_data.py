"""
Sample email data for development and testing.

Usage:
    python3 -m cindy.email --dry-run --use-sample-data

These messages simulate the AgentMail API response format
(GET /v0/inboxes/{inbox_id}/messages).
"""

from __future__ import annotations

SAMPLE_MESSAGES: list[dict] = [
    # --- 1. Series A follow-up with deal signals + obligations ---
    {
        "message_id": "msg_sample_001",
        "thread_id": "thd_series_a_composio",
        "inbox_id": "sample_inbox",
        "from": "Rahul Sharma <rahul@composio.dev>",
        "to": ["Aakash Kumar <ak@z47.com>"],
        "cc": ["Cindy <cindy.aacash@agentmail.to>", "Sneha <sneha@z47.com>"],
        "bcc": [],
        "subject": "Re: Series A follow-up",
        "text": (
            "Hi Aakash,\n\n"
            "Great meeting yesterday. As discussed, we're targeting a $20M round "
            "at $100M pre-money valuation. I'll send you the updated cap table and "
            "data room access by Friday.\n\n"
            "Our ARR is now at $4.2M with 3x YoY growth. The agentic AI infrastructure "
            "market is moving fast and we want to close this round before end of month.\n\n"
            "Could you send me the IC deck template so we can prepare our materials?\n\n"
            "Also, I'll introduce you to our new CTO, Sarah Lee, who joined from Google DeepMind.\n\n"
            "Best,\nRahul"
        ),
        "html": "",
        "extracted_text": (
            "Great meeting yesterday. As discussed, we're targeting a $20M round "
            "at $100M pre-money valuation. I'll send you the updated cap table and "
            "data room access by Friday.\n\n"
            "Our ARR is now at $4.2M with 3x YoY growth. The agentic AI infrastructure "
            "market is moving fast and we want to close this round before end of month.\n\n"
            "Could you send me the IC deck template so we can prepare our materials?\n\n"
            "Also, I'll introduce you to our new CTO, Sarah Lee, who joined from Google DeepMind."
        ),
        "attachments": [
            {
                "attachment_id": "att_001",
                "filename": "Composio_Pitch_Deck_v3.pdf",
                "content_type": "application/pdf",
                "size": 2048000,
                "content_disposition": "attachment",
            }
        ],
        "labels": [],
        "timestamp": "2026-03-20T10:30:00Z",
        "created_at": "2026-03-20T10:30:00Z",
        "in_reply_to": "msg_prev_001",
        "references": ["msg_prev_001"],
    },

    # --- 2. Calendar invite (.ics) with meeting ---
    {
        "message_id": "msg_sample_002",
        "thread_id": "thd_calendar_invite",
        "inbox_id": "sample_inbox",
        "from": "Sarah Lee <sarah@composio.dev>",
        "to": ["Aakash Kumar <ak@z47.com>"],
        "cc": ["cindy.aacash@agentmail.to"],
        "bcc": [],
        "subject": "Invite: Composio Deep Dive - Product Demo",
        "text": "You've been invited to a meeting: Composio Deep Dive - Product Demo\nMarch 25, 2026 at 2:00 PM IST",
        "html": "",
        "extracted_text": "You've been invited to a meeting: Composio Deep Dive - Product Demo\nMarch 25, 2026 at 2:00 PM IST",
        "attachments": [
            {
                "attachment_id": "att_002",
                "filename": "invite.ics",
                "content_type": "text/calendar",
                "size": 1500,
                "content_disposition": "attachment",
            }
        ],
        "labels": [],
        "timestamp": "2026-03-20T11:00:00Z",
        "created_at": "2026-03-20T11:00:00Z",
        "in_reply_to": None,
        "references": [],
    },

    # --- 3. Thesis-relevant email about developer tools ---
    {
        "message_id": "msg_sample_003",
        "thread_id": "thd_devtools_intro",
        "inbox_id": "sample_inbox",
        "from": "Priya Mehta <priya@earlybird.vc>",
        "to": ["ak@z47.com"],
        "cc": ["cindy.aacash@agentmail.to"],
        "bcc": [],
        "subject": "Intro: Exciting DevTools Startup - BuildKit",
        "text": (
            "Hi Aakash,\n\n"
            "I'd like to introduce you to the founders of BuildKit, a developer tools "
            "platform that's reimagining CI/CD for the AI-native era. They've built an "
            "autonomous agent framework for testing and deployment.\n\n"
            "They're raising a seed round ($5M target) and I think this fits your "
            "agentic AI infrastructure thesis perfectly.\n\n"
            "Let me know if you'd like to schedule a call. I'll connect you with "
            "their CEO, Vikram, next week.\n\n"
            "Cheers,\nPriya"
        ),
        "html": "",
        "extracted_text": (
            "I'd like to introduce you to the founders of BuildKit, a developer tools "
            "platform that's reimagining CI/CD for the AI-native era. They've built an "
            "autonomous agent framework for testing and deployment.\n\n"
            "They're raising a seed round ($5M target) and I think this fits your "
            "agentic AI infrastructure thesis perfectly.\n\n"
            "Let me know if you'd like to schedule a call. I'll connect you with "
            "their CEO, Vikram, next week."
        ),
        "attachments": [],
        "labels": [],
        "timestamp": "2026-03-20T09:15:00Z",
        "created_at": "2026-03-20T09:15:00Z",
        "in_reply_to": None,
        "references": [],
    },

    # --- 4. Aakash sends an email (for I_OWE testing) ---
    {
        "message_id": "msg_sample_004",
        "thread_id": "thd_portfolio_update",
        "inbox_id": "sample_inbox",
        "from": "Aakash Kumar <ak@z47.com>",
        "to": ["amit@fintech-startup.com"],
        "cc": ["cindy.aacash@agentmail.to"],
        "bcc": [],
        "subject": "Re: Q1 Board Deck",
        "text": (
            "Hi Amit,\n\n"
            "Thanks for the Q1 update. Revenue growth looks strong.\n\n"
            "I'll review the full board deck this weekend and send you my notes by Monday. "
            "Let me also schedule a call with our fintech analyst to go through the "
            "burn rate projections.\n\n"
            "Could you send me the updated cap table with the new ESOP pool?\n\n"
            "I'll follow up with Sneha on the IC timeline.\n\n"
            "Best,\nAakash"
        ),
        "html": "",
        "extracted_text": (
            "Thanks for the Q1 update. Revenue growth looks strong.\n\n"
            "I'll review the full board deck this weekend and send you my notes by Monday. "
            "Let me also schedule a call with our fintech analyst to go through the "
            "burn rate projections.\n\n"
            "Could you send me the updated cap table with the new ESOP pool?\n\n"
            "I'll follow up with Sneha on the IC timeline."
        ),
        "attachments": [],
        "labels": [],
        "timestamp": "2026-03-20T14:00:00Z",
        "created_at": "2026-03-20T14:00:00Z",
        "in_reply_to": "msg_board_deck_001",
        "references": ["msg_board_deck_001"],
    },

    # --- 5. Simple operational email (low signal) ---
    {
        "message_id": "msg_sample_005",
        "thread_id": "thd_logistics",
        "inbox_id": "sample_inbox",
        "from": "Events Team <events@z47.com>",
        "to": ["ak@z47.com"],
        "cc": ["cindy.aacash@agentmail.to"],
        "bcc": [],
        "subject": "Annual LP Meet - Logistics Update",
        "text": (
            "Hi Aakash,\n\n"
            "The venue for the LP Meet has been confirmed at Taj Lands End, Mumbai. "
            "Date: April 15. Please block your calendar.\n\n"
            "Agenda draft will be shared tomorrow.\n\n"
            "Regards,\nEvents Team"
        ),
        "html": "",
        "extracted_text": (
            "The venue for the LP Meet has been confirmed at Taj Lands End, Mumbai. "
            "Date: April 15. Please block your calendar.\n\n"
            "Agenda draft will be shared tomorrow."
        ),
        "attachments": [],
        "labels": [],
        "timestamp": "2026-03-20T08:00:00Z",
        "created_at": "2026-03-20T08:00:00Z",
        "in_reply_to": None,
        "references": [],
    },

    # --- 6. Cybersecurity deal with term sheet mention ---
    {
        "message_id": "msg_sample_006",
        "thread_id": "thd_cyberco_terms",
        "inbox_id": "sample_inbox",
        "from": "James Chen <james@cyberco.io>",
        "to": ["ak@z47.com"],
        "cc": ["cindy.aacash@agentmail.to"],
        "bcc": [],
        "subject": "Term Sheet Discussion - CyberCo Series B",
        "text": (
            "Hi Aakash,\n\n"
            "Following our due diligence process, we're ready to discuss term sheet "
            "details for our Series B. We're looking at $30M at $150M pre-money valuation.\n\n"
            "Our zero trust platform has seen strong traction — 200% ARR growth and "
            "we've signed 3 Fortune 500 contracts in Q1.\n\n"
            "I'll send you the data room access by tomorrow. Will also get back to you "
            "on the co-investor question.\n\n"
            "Looking forward to the IC review next week.\n\n"
            "Best,\nJames"
        ),
        "html": "",
        "extracted_text": (
            "Following our due diligence process, we're ready to discuss term sheet "
            "details for our Series B. We're looking at $30M at $150M pre-money valuation.\n\n"
            "Our zero trust platform has seen strong traction — 200% ARR growth and "
            "we've signed 3 Fortune 500 contracts in Q1.\n\n"
            "I'll send you the data room access by tomorrow. Will also get back to you "
            "on the co-investor question.\n\n"
            "Looking forward to the IC review next week."
        ),
        "attachments": [
            {
                "attachment_id": "att_006",
                "filename": "CyberCo_Term_Sheet_Draft.pdf",
                "content_type": "application/pdf",
                "size": 512000,
                "content_disposition": "attachment",
            }
        ],
        "labels": [],
        "timestamp": "2026-03-20T16:45:00Z",
        "created_at": "2026-03-20T16:45:00Z",
        "in_reply_to": None,
        "references": [],
    },
]
