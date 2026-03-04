# Workflow Automation Platforms (Zapier, Make, etc.)

## Overview

Workflow automation platforms connect to LinkedIn and X primarily
through official APIs using OAuth. They provide orchestration layers,
triggers, retries, and webhooks.

## Key Characteristics

-   Pre-built OAuth connectors
-   Trigger/action execution engine
-   Task-based billing
-   Webhook support
-   Managed authentication

## Sub-Options

-   Zapier MCP (Model Context Protocol exposure)
-   Make (HTTP modules + API orchestration)
-   Custom HTTP connector steps

## Capabilities

-   Posting content
-   Reading limited data exposed via official APIs
-   Cross-platform workflows
-   Scheduling and retries

## Structural Gaps

-   Cannot access non-public LinkedIn endpoints
-   No inbox access on LinkedIn
-   Limited by official API permissions
-   Dependent on API rate limits

## Infrastructure Model

-   Vendor-managed execution
-   OAuth token storage inside vendor platform
-   Task quota and concurrency limits
