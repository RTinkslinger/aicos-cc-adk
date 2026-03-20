# Cindy Communications Agent: Email Infrastructure Research

**Date:** 2026-03-20
**Purpose:** Evaluate email infrastructure options for the Cindy Communications Agent, enabling Aakash to CC/forward emails to Cindy for processing, thread parsing, and Network DB linking.

---

## Executive Summary

**Recommended approach: AgentMail** (primary) with custom domain `cindy@aicos.ai` or `cindy@3niac.com`.

AgentMail is purpose-built for exactly this use case: giving AI agents their own email inboxes. It is a YC-backed startup ($6M seed, launched March 2026) that provides API-first email infrastructure designed for agents. It natively handles every requirement: dedicated email addresses, webhook/websocket push notifications, thread management, attachment parsing, reply text extraction, and custom domains. The Python SDK integrates cleanly with our ClaudeSDKClient architecture on the droplet.

The cost is $20/month (Developer tier) for up to 10 inboxes and 10,000 emails/month -- more than sufficient for Cindy's use case.

---

## Comparison Table

| Feature | AgentMail | Resend | Mailgun | SendGrid | Postmark | Gmail API | MS Graph |
|---------|-----------|--------|---------|----------|----------|-----------|----------|
| **Dedicated agent inbox** | Native (API-created) | Via domain routing | Via route rules | Via MX + parse | Via inbound hash | Requires Google Workspace seat | Requires M365 license |
| **Receive emails (inbound)** | Yes (core feature) | Yes (webhook) | Yes (routes + webhook) | Yes (Inbound Parse) | Yes (webhook) | Yes (poll or Pub/Sub) | Yes (poll or subscriptions) |
| **Send emails** | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| **Webhook push** | Yes (7 event types) | Yes (`email.received`) | Yes (routes forward to URL) | Yes (POST to URL) | Yes (10 retries) | Pub/Sub only | Subscriptions API |
| **WebSocket real-time** | Yes (native) | No | No | No | No | No | No |
| **Thread management** | Native API (auto-threaded) | Manual (via headers) | No native threading | No native threading | `StrippedTextReply` field | Native (Gmail threads) | Native (conversation ID) |
| **Reply text extraction** | `extracted_text` / `extracted_html` (auto-strips quoted history) | Must parse raw email | No built-in | No built-in | `StrippedTextReply` | Must parse payload | Must parse payload |
| **Attachments** | Full API (send/receive/download) | API + download URLs | Base64 in webhook | In webhook payload | Base64 in JSON | API (base64) | API (base64) |
| **CC/BCC parsing** | Yes (in webhook payload) | Yes (in API response) | Yes (in parsed data) | Yes (in POST data) | Yes (CcFull, BccFull) | Yes | Yes |
| **Custom domain** | Yes (Developer plan+, DNS setup) | Yes (MX records) | Yes (MX + verify) | Yes (MX + auth domain) | Yes (domain forwarding) | N/A (uses Gmail domain) | N/A (uses Outlook domain) |
| **Python SDK** | `pip install agentmail` | `pip install resend` | `pip install mailgun` (community) | `pip install sendgrid` | Community libraries | `google-api-python-client` | `msgraph-sdk` |
| **Auth complexity** | API key only | API key only | API key only | API key only | API key (server token) | OAuth 2.0 + refresh tokens | OAuth 2.0 / client credentials |
| **Semantic search** | Built-in (org-wide) | No | No | No | No | Gmail search operators | OData `$search` |
| **Labels/organization** | Native labels API | No | No | No | No | Gmail labels | Categories/folders |
| **Cost (low volume)** | **$20/mo** (Developer) | **$20/mo** (Pro, 50K emails) | **$35/mo** (Foundation, 50K) | **$20/mo** (Essentials, 50K) | **$15/mo** (10K emails) | **$7.20/mo** (Workspace Starter) | **$6/mo** (M365 Basic) |
| **Free tier** | 3 inboxes, 3K emails | 3K emails, 100/day | 100 emails/day, 1 route | 100 emails/day | 100 emails/mo | N/A | N/A |
| **AI-native features** | Semantic search, auto-labeling, data extraction, MCP server | None | None | None | None | None | None |
| **Setup complexity** | Very low (5 min) | Low (15 min) | Medium (30 min, DNS + routes) | Medium (30 min, MX + parse) | Medium (20 min) | High (OAuth, GCP project) | High (Azure AD, permissions) |
| **Droplet integration** | Excellent (webhook or websocket) | Good (webhook) | Good (webhook) | Good (webhook) | Good (webhook) | Complex (Pub/Sub requires GCP) | Complex (subscriptions require Azure) |

---

## Detailed Analysis

### 1. AgentMail (RECOMMENDED)

**What it is:** An API-first email provider specifically designed for AI agents. Think "Gmail for AI agents." YC-backed, launched March 2026, raised $6M seed.

**Website:** https://agentmail.to | **Docs:** https://docs.agentmail.to

#### How It Works
1. Create an inbox via API: `client.inboxes.create(username="cindy", domain="aicos.ai")`
2. Register a webhook or connect via WebSocket for real-time notifications
3. When Aakash CCs/forwards to cindy@aicos.ai, AgentMail receives the email, parses it, and pushes a `message.received` event
4. The webhook payload includes: full text, HTML, attachments metadata, CC/BCC, thread context, `in_reply_to`, `references`
5. Use `extracted_text` / `extracted_html` for just the new reply content (quoted history auto-stripped via Talon)

#### Key Features for Cindy
- **Thread API:** Threads are auto-created and managed. `client.inboxes.threads.list()` returns organized conversations. Thread objects include `senders`, `recipients`, `message_count`.
- **Reply extraction:** Messages have `extracted_text` and `extracted_html` fields that contain only the new reply content, with quoted history stripped using the Talon library.
- **Webhook events:** 7 event types including `message.received` (the key one). The `message.received` payload includes both message AND thread metadata.
- **WebSocket alternative:** For the droplet, WebSocket is even better than webhooks -- no need to expose a public endpoint or use ngrok. Pure outbound connection.
- **Attachments:** Full send/receive with attachment ID-based retrieval API.
- **Custom domains:** Add `aicos.ai` or `3niac.com`, configure DNS (SPF, DKIM, MX), verify, then create inboxes on that domain.
- **Labels:** Tag messages programmatically for organization (`processed`, `action-required`, etc.).
- **Semantic search:** Search across all messages in the organization by meaning.

#### Pricing
| Tier | Cost | Inboxes | Emails/mo | Custom Domains |
|------|------|---------|-----------|----------------|
| Free | $0 | 3 | 3,000 | None |
| Developer | **$20/mo** | 10 | 10,000 | 10 |
| Startup | $200/mo | 150 | 150,000 | 150 |
| Enterprise | Custom | Custom | Custom | Custom |

**For Cindy:** Developer tier at $20/mo is sufficient. 10 inboxes means we could create separate inboxes for different contexts if needed (cindy@, research@, deals@). 10K emails/month is well beyond expected volume.

#### Python SDK Example (Cindy Integration)

```python
import os
from agentmail import AgentMail, AsyncAgentMail
from agentmail.types.websockets import Subscribe, Subscribed, MessageReceivedEvent

# Initialize
client = AgentMail(api_key=os.getenv("AGENTMAIL_API_KEY"))

# Create Cindy's inbox (idempotent with client_id)
inbox = client.inboxes.create(
    username="cindy",
    domain="aicos.ai",  # requires custom domain setup
    display_name="Cindy - AI CoS",
    client_id="cindy-inbox-v1"  # idempotent retry key
)

# Option A: Webhook-based (requires public URL on droplet)
client.webhooks.create(
    url="https://mcp.3niac.com/cindy/webhook",
    events=["message.received"]
)

# Option B: WebSocket-based (preferred for droplet -- no public URL needed)
async_client = AsyncAgentMail(api_key=os.getenv("AGENTMAIL_API_KEY"))

async with async_client.websockets.connect() as socket:
    await socket.send_subscribe(Subscribe(inbox_ids=[inbox.inbox_id]))

    async for event in socket:
        if isinstance(event, MessageReceivedEvent):
            msg = event.message
            # msg.from_ -- sender
            # msg.to -- recipients
            # msg.cc -- CC'd addresses
            # msg.subject -- subject line
            # msg.extracted_text -- reply only (no quoted history)
            # msg.text -- full text including quotes
            # msg.html -- full HTML
            # msg.thread_id -- conversation thread
            # msg.attachments -- list of attachment metadata
            # msg.in_reply_to -- parent message ID
            await process_email_for_cindy(msg)

# Reading a thread
thread = client.inboxes.threads.get(
    inbox_id=inbox.inbox_id,
    thread_id="thd_abc123"
)
for message in thread.messages:
    print(f"{message.from_}: {message.extracted_text or message.text}")

# Replying (maintains thread context automatically)
client.inboxes.messages.reply(
    inbox_id=inbox.inbox_id,
    message_id="<msg_id@agentmail.to>",
    text="Thanks for the update. I've noted this in the action queue.",
    html="<p>Thanks for the update. I've noted this in the action queue.</p>"
)

# Downloading an attachment
attachment_data = client.inboxes.messages.get_attachment(
    inbox_id=inbox.inbox_id,
    message_id="<msg_id>",
    attachment_id="att_123"
)
```

#### Custom Domain Setup
1. Add domain via API: `client.domains.create("aicos.ai")`
2. Add DNS records provided by AgentMail:
   - **TXT (SPF):** Authorizes AgentMail to send on behalf of the domain
   - **CNAME (DKIM):** Cryptographic signature for email authenticity
   - **MX:** Routes incoming mail to AgentMail servers (needed for receiving)
3. Wait for verification (usually minutes with Cloudflare)
4. Create inboxes on the domain: `client.inboxes.create(username="cindy", domain="aicos.ai")`

**Important:** If `aicos.ai` already has MX records (e.g., Google Workspace), use a subdomain like `mail.aicos.ai` or `agent.aicos.ai` to avoid conflicts. This means the address would be `cindy@agent.aicos.ai`.

#### Integration Architecture for Droplet

```
Aakash's Gmail                    AgentMail Cloud
  |                                    |
  | CC/forward to cindy@agent.aicos.ai |
  |----------------------------------->|
  |                                    |
  |                    WebSocket event |
  |                    (message.received)
  |                                    |
  |                              Droplet (/opt/agents/)
  |                                    |
  |                    CindyAgent (ClaudeSDKClient)
  |                    - Parse email content
  |                    - Extract participants -> Network DB lookup
  |                    - Identify action items -> Actions Queue
  |                    - Update Thesis Tracker if relevant
  |                    - Reply if needed (via AgentMail API)
```

**WebSocket approach is ideal for the droplet** because:
- No need to expose a new public HTTPS endpoint
- Pure outbound connection (no firewall changes)
- True real-time (lower latency than webhook HTTP round-trip)
- Works with the existing persistent agent architecture (lifecycle.py)
- Reconnection is built into the SDK

---

### 2. Resend (Strong Alternative)

**What it is:** Modern email API for developers, originally sending-only but launched inbound email support in November 2025.

**Strengths:**
- Beautiful developer experience and documentation
- Python SDK: `pip install resend`
- Inbound emails via webhook (`email.received` event)
- Custom domain support with MX records
- Free tier: 3K emails/mo, $20/mo Pro tier with 50K
- Good attachment handling via separate API calls

**Weaknesses:**
- No native thread management (must track via message headers manually)
- No reply text extraction (must parse raw email yourself)
- No WebSocket support (webhook only)
- Webhook payload does NOT include email body/headers/attachments -- you must call the Received Emails API separately to get content
- No semantic search or AI-native features
- Relatively new inbound feature (launched Nov 2025)

**Verdict:** Good for simple inbound use cases, but AgentMail's thread management, reply extraction, and WebSocket support are significant advantages for Cindy's use case.

---

### 3. Mailgun (Established, Complex)

**What it is:** Veteran email API (now owned by Sinch). Strong inbound routing with webhook forwarding.

**Strengths:**
- Mature, battle-tested infrastructure
- Inbound routing with flexible filter expressions (match by recipient, header, etc.)
- Parses emails into structured JSON (headers, body, attachments)
- Good Python SDK support
- Talon library (for reply parsing) was originally built by Mailgun

**Weaknesses:**
- No native inbox concept -- inbound emails are processed and forwarded, not stored
- Must configure MX records + routes (more setup than AgentMail)
- No thread management
- No WebSocket support
- Foundation plan ($35/mo) needed for full inbound routing access
- More complex setup overall
- Not designed for agent use cases

**Pricing:**
| Tier | Cost | Emails/mo | Inbound Routes |
|------|------|-----------|----------------|
| Free | $0 | 100/day | 1 |
| Basic | $15/mo | 10,000 | 5 |
| Foundation | $35/mo | 50,000 | Full access |
| Scale | $90/mo | 100,000 | Full access |

**Verdict:** Overkill for this use case. The inbound routing is powerful but designed for high-volume email processing at scale, not for giving an AI agent a personal inbox.

---

### 4. SendGrid Inbound Parse (Webhook-Only)

**What it is:** Twilio SendGrid's inbound email processing. Receives emails via MX records, parses them, and POSTs to a webhook URL.

**Strengths:**
- Well-documented webhook format
- Parses headers, body (text + HTML), attachments
- Spam checking included
- Can POST raw MIME or parsed format

**Weaknesses:**
- No inbox concept (pure email-to-webhook pipe)
- No thread management
- No reply text extraction
- No WebSocket support
- Requires MX record setup + authenticated domain
- No message storage (fire-and-forget webhook)
- Limited debugging (no delivery logs for Inbound Parse)

**Pricing:** Starting at ~$20/mo (Essentials plan). Inbound parse is included but requires domain authentication.

**Verdict:** Simple webhook pipe, but lacks the inbox/thread/storage features that Cindy needs.

---

### 5. Postmark (Clean JSON, Good Reply Parsing)

**What it is:** Transactional email service with solid inbound email processing.

**Strengths:**
- Excellent JSON webhook format (clean, well-structured)
- **`StrippedTextReply`** field -- auto-extracts just the reply text (similar to AgentMail's `extracted_text`)
- Full CC/BCC parsing with structured `CcFull` and `BccFull` arrays
- SpamAssassin scoring included
- Good retry behavior (10 retries with growing intervals)
- Pre-made inbound address or custom domain

**Weaknesses:**
- Only 1 inbound stream per server
- Only 1 webhook URL per inbound stream
- Only 1 domain per inbound stream
- No thread management API
- No WebSocket support
- 100 emails/mo on free plan (very limited)

**Pricing:** $0 (100 emails/mo), $15/mo (10K), scales from there. Inbound emails count toward monthly email quota.

**Verdict:** The `StrippedTextReply` feature is excellent, but the 1-stream-per-server limitation and lack of thread management make it less suitable than AgentMail.

---

### 6. Gmail API (Complex But Feature-Rich)

**What it is:** Google's API for programmatic Gmail access.

**Strengths:**
- Full-featured email platform (threads, labels, search, filters)
- Native thread management (Gmail pioneered email threading)
- Rich search operators
- Can use a real Gmail/Workspace address
- Push notifications via Google Cloud Pub/Sub

**Weaknesses:**
- **OAuth 2.0 complexity** -- requires GCP project, OAuth consent screen, credential management, token refresh
- **Requires Google Workspace seat** ($7.20/mo minimum) for a dedicated address
- Push notifications require Google Cloud Pub/Sub setup (additional infrastructure)
- Must parse MIME messages yourself (base64 encoded, multipart)
- No reply text extraction
- Token refresh handling on a headless server is finicky
- Google may rate-limit or restrict automated access

**Verdict:** Powerful but the auth complexity and infrastructure overhead (GCP project + Pub/Sub + Workspace seat) make it a poor fit for a droplet-based agent. Best if Cindy needed to access Aakash's existing Gmail directly.

---

### 7. Microsoft Graph API (Enterprise, Complex)

**What it is:** Microsoft's API for Outlook/Exchange email access.

**Strengths:**
- Full Outlook feature set (threads, categories, rules)
- Change notifications (webhook subscriptions for new mail)
- App-only auth possible (client credentials flow)

**Weaknesses:**
- Requires Microsoft 365 license ($6/mo minimum)
- Azure AD app registration + permissions
- Subscriptions expire and must be renewed
- Complex multi-step setup
- Not designed for agent use cases

**Verdict:** Not suitable. Over-engineered for this use case and requires Microsoft infrastructure.

---

### 8. Custom IMAP Polling (DIY)

**What it is:** Poll a standard email inbox via IMAP protocol using Python's `imaplib` or `imapclient`.

**Strengths:**
- Works with any email provider
- No vendor lock-in
- Simple Python implementation
- Can use an existing email address

**Weaknesses:**
- **Polling, not push** -- introduces latency (1-5 min intervals typical)
- Must parse MIME messages yourself
- No thread management (must implement from headers)
- No reply text extraction
- Must handle connection management, reconnections
- Must handle email deletion/marking as read
- Security concerns with stored credentials

**Verdict:** The simplest fallback, but the polling model and manual parsing make it inferior to any of the API-based solutions.

---

## Recommendation

### Primary: AgentMail ($20/mo Developer tier)

AgentMail is the clear winner for Cindy's use case:

1. **Purpose-built for AI agents** -- the entire API is designed around the exact use case we need
2. **WebSocket support** -- perfect for the droplet (no public endpoint needed, true real-time)
3. **Thread management** -- auto-threaded conversations with API access, exactly what Cindy needs to understand email context
4. **Reply extraction** -- `extracted_text`/`extracted_html` automatically strips quoted history, so Cindy sees just what the person actually wrote
5. **Attachments** -- full send/receive with download API
6. **Custom domains** -- `cindy@agent.aicos.ai` (subdomain to avoid MX conflicts)
7. **Python SDK** -- clean, well-documented, async-capable
8. **Labels** -- tag processed emails, flag action items
9. **Semantic search** -- find relevant past conversations by meaning
10. **Simple auth** -- API key, no OAuth complexity
11. **Low cost** -- $20/mo for 10K emails/mo

### Fallback: Resend ($20/mo Pro tier)

If AgentMail has reliability issues or limitations in practice, Resend is the strongest alternative. The main trade-off is losing thread management and reply extraction (would need to implement via email headers and a parsing library like `email-reply-parser`).

---

## Implementation Plan

### Phase 1: Setup (1-2 hours)
1. Sign up at https://console.agentmail.to
2. Get API key
3. Add `AGENTMAIL_API_KEY` to droplet `.env`
4. Install SDK: `pip install agentmail`
5. Create Cindy's inbox (initially on `@agentmail.to` for testing)
6. Test send/receive manually

### Phase 2: Custom Domain (1 hour)
1. Choose domain: `agent.aicos.ai` or `cindy.3niac.com` (subdomain recommended)
2. Add domain via API
3. Configure DNS records (SPF, DKIM, MX)
4. Verify domain
5. Recreate Cindy's inbox on custom domain

### Phase 3: Integration (3-5 hours)
1. Add WebSocket listener to Cindy agent (new module in `/opt/agents/`)
2. On `message.received` event:
   - Parse sender email -> look up in Network DB
   - Parse CC list -> identify all participants
   - Extract reply text via `extracted_text`
   - Feed full context to Claude for analysis
   - Determine action items -> write to Actions Queue
   - Determine thesis relevance -> flag for Thesis Tracker
   - If reply warranted, compose and send via AgentMail API
3. Store email metadata in Postgres for querying
4. Add to orchestrator lifecycle management

### Phase 4: Network DB Integration (2-3 hours)
1. Build email-to-person resolver (match email addresses to Network DB entries)
2. On new contact, create Network DB entry or flag for review
3. Track communication frequency per contact
4. Link email threads to Companies DB / Portfolio DB where relevant

### Estimated Total Cost
- AgentMail Developer: **$20/month**
- No additional infrastructure needed (uses existing droplet)
- Total: **$20/month**

---

## Sources

- AgentMail: https://agentmail.to, https://docs.agentmail.to
- AgentMail Pricing: https://agentmail.to/pricing
- AgentMail Python SDK: https://github.com/agentmail-to/agentmail-python
- AgentMail YC Launch: https://www.ycombinator.com/launches/NvQ-agentmail-the-api-first-email-provider-for-ai-agents
- Resend: https://resend.com, https://resend.com/docs/dashboard/receiving/introduction
- Mailgun: https://www.mailgun.com, https://www.mailgun.com/features/inbound-email-routing/
- SendGrid Inbound Parse: https://www.twilio.com/docs/sendgrid/for-developers/parsing-email/setting-up-the-inbound-parse-webhook
- Postmark: https://postmarkapp.com/developer/webhooks/inbound-webhook
- Gmail API: https://developers.google.com/workspace/gmail/api/guides
- Microsoft Graph: https://learn.microsoft.com/en-us/graph/tutorials/python-email
