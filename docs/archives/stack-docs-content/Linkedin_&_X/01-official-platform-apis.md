# Official Platform APIs (LinkedIn & X)

## Overview

Official platform APIs provide structured, OAuth-based access to
LinkedIn and X (Twitter). They are the only fully supported integration
mechanism recognized by the platforms.

------------------------------------------------------------------------

# LinkedIn API

## Access Model

-   OAuth 2.0 Authorization Code Flow
-   Access + Refresh tokens
-   Scoped permissions

## Public (Self-Serve) API Capabilities

-   r_liteprofile -- Basic profile data
-   r_emailaddress -- Email retrieval
-   w_member_social -- Post content (shares, comments, reactions)

## Restricted / Partner APIs

-   Messaging APIs
-   Connection lists
-   Full profile access
-   Advanced search
-   Sales Navigator APIs
-   Marketing APIs

## Technical Characteristics

-   REST-based JSON endpoints
-   Rate limits per app and per user
-   Daily quota reset (UTC)
-   429 error on limit exceedance
-   Token expiration and refresh handling required

## Functional Gaps

-   No general LinkedIn inbox access
-   No bulk connection export
-   No unrestricted search API
-   No historical content export for general developers

------------------------------------------------------------------------

# X (Twitter) API v2

## Access Model

-   OAuth 2.0 (App-only + User context)
-   Pay-per-use credit system

## Capabilities

-   Post tweets
-   Delete tweets
-   Read timeline
-   Read mentions
-   Search tweets (recent and full archive tiers)
-   Media upload
-   Direct message read/write
-   Streaming APIs

## Technical Characteristics

-   Endpoint-level rate limits
-   Monthly usage caps (non-enterprise tiers)
-   Bearer token authentication
-   Elevated and Enterprise tiers available

## Functional Gaps

-   Cost constraints at scale
-   Strict rate caps for some endpoints
-   No bypass of moderation controls

------------------------------------------------------------------------

# Security Model

-   OAuth token storage required
-   Refresh token lifecycle management
-   Secrets must be stored in secure vault systems
-   Least-privilege scope usage recommended

------------------------------------------------------------------------

# Infrastructure Considerations

-   Rate-limit aware scheduling
-   Central token refresh service
-   Logging and monitoring of API usage
-   Idempotency controls for posting endpoints

------------------------------------------------------------------------

# Capability Envelope Summary

  Capability           LinkedIn API   X API
  -------------------- -------------- ----------------
  Post content         Yes            Yes
  Read inbox           No             Yes
  Export connections   No             No
  Search content       Limited        Yes
  Historical export    No             Tier-dependent

------------------------------------------------------------------------

End of document.
