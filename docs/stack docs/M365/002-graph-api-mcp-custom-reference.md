# Microsoft Graph API Integration Reference (Mail, Calendar, OneDrive)

This document serves as a production-grade, coding-agent-optimized
reference for building a Custom MCP (Model Context Protocol) service
using Microsoft Graph API.

It is structured in three implementation phases: - Phase 1: Basic -
Phase 2: Advanced - Phase 3: Elaborate (Enterprise-grade)

This document is intended to be the single starting reference for a
coding agent implementing Microsoft Graph capabilities.

------------------------------------------------------------------------

# Phase 1: Basic Functionality

## 1. Authentication & Setup

Azure AD App Registration: - Register application in Azure Portal -
Capture: - client_id - tenant_id - client_secret (or certificate) -
Configure permissions: - Mail.ReadWrite - Calendars.ReadWrite -
Files.ReadWrite - offline_access

Documentation: https://learn.microsoft.com/graph/auth/

OAuth Flows Supported: - Authorization Code (delegated) - Client
Credentials (app-only) - On-Behalf-Of (OBO)

Access tokens expire \~1 hour. Implement refresh token logic.

Best Practice: - Cache tokens securely - Validate expiry before call -
Handle 401 by refreshing

------------------------------------------------------------------------

## 2. Mail API -- Basic

Base endpoint: https://graph.microsoft.com/v1.0/

Core Endpoints:

  Operation         Endpoint
  ----------------- -----------------------------------
  List messages     GET /me/messages
  Send mail         POST /me/sendMail
  Get folders       GET /me/mailFolders
  Move message      POST /me/messages/{id}/move
  Get attachments   GET /me/messages/{id}/attachments

Docs: https://learn.microsoft.com/graph/api/resources/message

Basic Search: GET /me/messages?\$filter=isRead eq false

Known Failure Scenarios:

1.  Missing attachments when forwarding Fix: GET /messages/{id}/\$value
    (MIME) Attach .eml manually

2.  Large attachments (\>4MB) Use upload session: POST
    /me/messages/{id}/attachments/createUploadSession

Docs:
https://learn.microsoft.com/graph/api/attachment-createuploadsession

3.  Hybrid/on-prem mailbox MIME export not supported

------------------------------------------------------------------------

## 3. Calendar API -- Basic

Core Endpoints:

  Operation      Endpoint
  -------------- -------------------------------
  List events    GET /me/events
  Create event   POST /me/events
  Update event   PATCH /me/events/{id}
  Delete event   DELETE /me/events/{id}
  Free/Busy      POST /me/calendar/getSchedule

Docs: https://learn.microsoft.com/graph/api/resources/event

Common Failures:

1.  404 ErrorItemNotFound during pagination Cause: insufficient
    permissions Fix: ensure Calendars.ReadWrite.Shared

2.  Timeout errors Usually throttling. Implement retry with exponential
    backoff.

------------------------------------------------------------------------

## 4. OneDrive API -- Basic

Core Endpoints:

  Operation           Endpoint
  ------------------- --------------------------------------------
  List root           GET /me/drive/root/children
  Upload small file   PUT /me/drive/root:/path/file.txt:/content
  Get item            GET /me/drive/items/{id}
  Delete              DELETE /me/drive/items/{id}

Docs: https://learn.microsoft.com/graph/api/resources/driveitem

Known Issues:

1.  /sites/{site-id}/drive returning ItemNotFound Prefer:
    /drives/{drive-id}

2.  Upload session invalid request when including "description" Remove
    field for legacy accounts

------------------------------------------------------------------------

# Phase 2: Advanced Features

## Mail Advanced

-   MIME operations
-   Message rules
-   Delegated send-as
-   Advanced filtering
-   Upload sessions

Docs: https://learn.microsoft.com/graph/api/resources/messagerule

Retry Strategy: - 429 → respect Retry-After - 503 → exponential backoff

------------------------------------------------------------------------

## Calendar Advanced

-   Recurring events
-   Reminders
-   Webhooks

Subscription endpoint: POST /subscriptions

Docs: https://learn.microsoft.com/graph/webhooks

Handle: - validationToken - renewal before expiry

------------------------------------------------------------------------

## OneDrive Advanced

-   Delta queries
-   Upload sessions with chunk ≤60 MiB
-   Version history
-   Thumbnails

Delta: GET /me/drive/root/delta

Docs: https://learn.microsoft.com/graph/delta-query-overview

Common Failure: Invalid delta token → restart full sync

------------------------------------------------------------------------

# Phase 3: Elaborate (Enterprise)

## Mail

-   Retention labels
-   eDiscovery
-   MailTips
-   Compliance integration

Docs:
https://learn.microsoft.com/graph/api/resources/security-api-overview

------------------------------------------------------------------------

## Calendar

-   Resource scheduling
-   Meeting time suggestions
-   Cross-service integration

Docs: https://learn.microsoft.com/graph/api/user-findmeetingtimes

------------------------------------------------------------------------

## OneDrive

-   Open extensions
-   Metadata storage
-   Cross-tenant sharing

Docs: https://learn.microsoft.com/graph/extensibility-overview

------------------------------------------------------------------------

# Throttling & Retry Strategy

Graph may return: - 429 Too Many Requests - 503 Service Unavailable

Always: - Respect Retry-After header - Use exponential backoff - Log
client-request-id

Docs: https://learn.microsoft.com/graph/throttling

------------------------------------------------------------------------

# Observability Best Practices

-   Log request ID
-   Log correlation ID
-   Log endpoint + latency
-   Capture 4xx/5xx bodies
-   Monitor token expiry

------------------------------------------------------------------------

# Deployment Considerations

Recommended Hosting: - Azure Functions - Azure App Service - Containers
(AKS) - Serverless workers

Ensure: - Managed identity where possible - Secret storage in Key
Vault - Health probes - Subscription renewal job

------------------------------------------------------------------------

# Change Management

-   Use v1.0 endpoints in production
-   Monitor Graph changelog
-   Avoid beta in production

Changelog: https://learn.microsoft.com/graph/changelog

------------------------------------------------------------------------

END OF DOCUMENT
