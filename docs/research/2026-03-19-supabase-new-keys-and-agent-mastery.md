# Executive Summary

In 2026, Supabase has fully transitioned to a new API key system, replacing the legacy `anon` and `service_role` JWTs with a more secure and flexible model composed of publishable and secret keys. This change was motivated by the need to decouple API keys from the JWT signing secret, enable instant rotation of compromised keys, and provide better lifecycle management.

The new system consists of two key types:
1.  **Publishable Key (`sb_publishable_...`):** This key replaces the legacy `anon` key. It is a low-privilege, opaque token that is safe to embed in client-side applications (web browsers, mobile apps). It enforces Row-Level Security (RLS) for all requests, ensuring that clients can only access data they are permitted to see.
2.  **Secret Key (`sb_secret_...`):** This key replaces the legacy `service_role` key. It is a high-privilege token intended exclusively for use in trusted server-side environments. It can bypass RLS, granting administrative access to the project's data. A key improvement is the ability to create multiple, revocable secret keys per project, allowing for key rotation and scoped access for different services or agents (like an AI coding agent).

This modern system enhances security by treating keys as reference tokens rather than long-lived JWTs, allowing for immediate revocation without affecting user sessions. It also improves operational hygiene by enabling per-service credentials and regular key rotation, significantly reducing the blast radius of a potential key leak.

# Key System Overview

## Publishable Key

The publishable key, which has a format starting with `sb_publishable_...`, is the designated replacement for the legacy `anon` key. It is an opaque reference token, not a JWT itself, and is designed to be safely embedded in public-facing client-side code, such as web browsers, mobile apps, and desktop applications. When a request is made using a publishable key, the Supabase API gateway intercepts it and substitutes it with an internally generated, short-lived `anon` role JWT before forwarding the request to the backend services. This key always operates under a low-privilege context and strictly enforces all active Row-Level Security (RLS) policies. If a user is authenticated, their session JWT is sent alongside the publishable key, and RLS policies are then evaluated based on the user's authenticated role.

## Secret Key

The secret key, identifiable by its `sb_secret_...` prefix, is the successor to the legacy `service_role` key. It is a high-privilege, opaque token intended for use only in secure, trusted server-side environments like backend servers, API routes, or Edge Functions. It must never be exposed to any client-side code. When the API gateway receives a request authenticated with a secret key, it replaces it with a pre-signed `service_role` JWT, which grants elevated permissions and bypasses all Row-Level Security (RLS) by default. This allows for administrative operations on the database. The new system allows for the creation of multiple secret keys per project, enabling better security practices such as per-service credentials, regular key rotation, and instant revocation of a specific key if it is compromised, without affecting others. These keys are managed in the Supabase dashboard under **Project Settings → API Keys**.

## Privilege Summary

The privilege levels and Row-Level Security (RLS) behavior of the two key types are distinct and critical to the security model:

*   **Publishable Key (`sb_publishable_...`):**
    *   **Privilege Level:** Low. Corresponds to the `anon` Postgres role when no user is logged in, or the `authenticated` role when a user session JWT is provided.
    *   **RLS Behavior:** RLS is always **ENFORCED**. Data access is strictly governed by the RLS policies defined for the `anon` or `authenticated` roles.

*   **Secret Key (`sb_secret_...`):**
    *   **Privilege Level:** High / Administrative. Corresponds to the `service_role` Postgres role.
    *   **RLS Behavior:** RLS is **BYPASSED** by default. This key grants unrestricted access to the database, making its protection paramount. It should only be used in secure server environments for tasks requiring administrative privileges.


# Dashboard Navigation Guide

## Navigation Path

Sign in to the Supabase dashboard → Select the desired project → Navigate to Settings → API Keys.

## Page Url Pattern

/dashboard/project/_/settings/api-keys/

## Key Management Actions

Users can manage keys through several UI controls. There is a 'Create new API Keys' button to generate new keys. For each existing secret key, a three-dot action menu provides options to 'Reveal' (which shows the secret value and logs the event), 'Rename', and 'Revoke/Delete' the key. The dashboard also displays 'Last used' indicators to help identify inactive keys.

## Role Based Visibility

Access to manage secret keys is restricted based on user roles. Only users with project-level permissions, specifically 'Owners' and 'Maintainers', can perform sensitive actions like revealing, creating, rotating, or revoking keys. Users with read-only permissions can see key metadata, such as 'last-used' timestamps, but are prevented from exposing the actual secret key values.


# Legacy Vs New Key Comparison

## Motivation For Change

The primary motivations for Supabase transitioning from the legacy JWT-based key system (anon/service_role) to the new opaque token model (publishable/secret) were to enhance security and operational flexibility. The legacy system tied the API keys directly to the JWT signing secret, which meant that rotating a compromised API key required rotating the entire project's JWT secret, a disruptive process that would invalidate all active user sessions. The new model was designed to decouple the API keys from the JWT signing secret, allowing for instant, independent rotation of compromised keys without affecting user sessions. This change significantly reduces the blast radius of a leaked key and improves the overall security posture. Furthermore, the new system facilitates the move towards asymmetric JWT signing for user sessions and allows for the creation of multiple secret keys, enabling better lifecycle management and per-service credentials.

## Key Type Mapping

The new API key system introduces a direct mapping from the legacy keys to the new ones, with updated naming conventions to clarify their intended use:

*   **Legacy `anon` JWT → New `publishable` key (`sb_publishable_...`)**: The `anon` key, which was a long-lived JWT safe for client-side use, is replaced by the `publishable` key. This key is intended for use in public-facing client applications like web browsers and mobile apps.
*   **Legacy `service_role` JWT → New `secret` key (`sb_secret_...`)**: The `service_role` key, a powerful JWT that could bypass Row-Level Security (RLS), is replaced by the `secret` key. This key is strictly for server-side use in trusted environments and grants elevated privileges.

## Behavioral Differences

There are significant behavioral differences between the legacy and new key systems:

*   **Token Format**: Legacy `anon` and `service_role` keys were long-lived JSON Web Tokens (JWTs), typically signed with HS256. The new `publishable` and `secret` keys are opaque reference tokens—short, random strings that are not JWTs themselves.
*   **Validation Process**: Legacy JWTs were validated directly by downstream services (like PostgREST) which would inspect the token's signature and claims. In the new model, the opaque `sb_` keys are intercepted at the Supabase API gateway. The gateway validates the opaque token and substitutes it with an appropriate, internally generated, short-lived JWT (`anon` or `service_role`) before forwarding the request to the upstream service. 
*   **Rotation**: Rotating legacy keys was a difficult process that required changing the project's JWT secret, invalidating all user sessions. With the new system, `sb_` keys can be rotated or revoked instantly and individually via the dashboard or API without affecting the JWT signing secret or user sessions.
*   **Edge Functions**: Supabase Edge Functions have built-in JWT verification for legacy keys. When using the new opaque `sb_` keys, this verification must be disabled using the `--no-verify-jwt` flag, and developers must implement their own logic to check for the `apikey` header.

## Security Improvements

The new key model introduces several critical security enhancements:

*   **Instant Rotation and Revocation**: The most significant improvement is the ability to instantly revoke a compromised key without affecting other keys or user sessions. This drastically reduces the time-to-remediation and the potential damage from a leak.
*   **Multiple Secret Keys**: The system allows for the creation of multiple `sb_secret_` keys per project. This enables the principle of least privilege by creating separate, revocable credentials for different backend services, environments (dev/stage/prod), or third-party integrations. If one key is compromised, only that specific service is affected.
*   **Decoupling from JWT Secret**: By separating API keys from the JWT signing secret, the blast radius of a compromised key is contained. A leaked API key no longer implies a compromised JWT secret, which was a major risk in the legacy system.
*   **Enhanced Auditing**: All management actions related to the new keys, including creation, revelation, and revocation, are recorded in the project's Audit Log. This provides clear traceability for security and compliance purposes.


# Nextjs App Router Implementation Guide

## Environment Variable Setup

To set up your Next.js App Router project, create a `.env.local` file at the root of your project. This file will store your Supabase credentials. It is critical to distinguish between client-safe keys and server-only secret keys.

```bash
# .env.local

# This key is safe to expose to the browser and is used for client-side operations.
# The NEXT_PUBLIC_ prefix makes it available in the browser environment.
NEXT_PUBLIC_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_XXXXXXXXXXXXXXXXXXXX

# This is a secret key and must NEVER be exposed to the browser.
# It is used for server-side operations that require elevated privileges.
# Note the absence of the NEXT_PUBLIC_ prefix.
SUPABASE_SERVICE_ROLE_KEY=sb_secret_XXXXXXXXXXXXXXXXXXXX
```

Variables prefixed with `NEXT_PUBLIC_` are automatically embedded into the client-side JavaScript bundle by Next.js. The `SUPABASE_SERVICE_ROLE_KEY`, lacking this prefix, is only accessible in server-side environments like Server Components, API Routes, and Server Actions running in a Node.js or compatible runtime.

## Client Component Pattern

In client components, you should always use the publishable key (`NEXT_PUBLIC_SUPABASE_ANON_KEY`). This key is designed to be public and enforces Row-Level Security (RLS) policies based on the authenticated user's session. A common pattern is to create a Supabase client instance and provide it to your component tree using a React Context.

Here is a code example for a provider component:

```tsx
// app/components/SupabaseProvider.tsx
'use client';

import { createClient } from '@supabase/supabase-js';
import { createContext, useContext, useState } from 'react';

// Define the type for the context value
import type { SupabaseClient } from '@supabase/supabase-js';
type SupabaseContextType = SupabaseClient | null;

// Create the context
export const SupabaseContext = createContext<SupabaseContextType>(null);

// Create the provider component
export default function SupabaseProvider({ children }: { children: React.ReactNode }) {
  const [supabase] = useState(() =>
    createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    )
  );

  return (
    <SupabaseContext.Provider value={supabase}>
      {children}
    </SupabaseContext.Provider>
  );
}

// Custom hook to use the Supabase client
export const useSupabase = () => {
  const context = useContext(SupabaseContext);
  if (context === null) {
    throw new Error('useSupabase must be used within a SupabaseProvider');
  }
  return context;
};
```
This setup ensures that any Supabase operation initiated from the client-side correctly respects your RLS policies, as no secret key is ever exposed to the browser.

## Server Component Pattern

In server components, you have two primary patterns for using Supabase, depending on the required privilege level:

1.  **Admin Operations (Bypassing RLS with a Secret Key)**: For tasks that require administrative privileges and need to bypass RLS (e.g., deleting data for maintenance, running internal jobs), you initialize the Supabase client with the `SUPABASE_SERVICE_ROLE_KEY`. This must only be done in server-only files (like API Routes or Server Actions) that are guaranteed not to run on the client.

    ```tsx
    // app/api/admin/clear-data/route.ts (Server-only Route Handler)
    import { createClient } from '@supabase/supabase-js';

    export async function POST(request: Request) {
      // Initialize client with the secret key for elevated privileges
      const supabase = createClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.SUPABASE_SERVICE_ROLE_KEY!
      );

      // This operation bypasses RLS
      const { error } = await supabase.from('sensitive_table').delete().gt('id', 0);
      if (error) return new Response(error.message, { status: 500 });
      return new Response('All rows cleared', { status: 200 });
    }
    ```

2.  **RLS-Preserving Actions (With a User Session)**: When you need to fetch data on the server on behalf of a specific user while respecting their permissions, you should use the publishable key and forward the user's authentication cookie. The `next/headers` utility allows you to access the cookies within a server component.

    ```tsx
    // app/dashboard/Analytics.tsx (Server Component)
    import { createClient } from '@supabase/supabase-js';
    import { cookies } from 'next/headers';

    export default async function Analytics() {
      // Initialize client with the publishable key
      const supabase = createClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
          // Forward the user's auth cookie to the Supabase client
          global: {
            headers: { cookie: cookies().toString() }
          }
        }
      );

      // This query will respect the RLS policies for the logged-in user
      const { data, error } = await supabase.from('user_stats').select();
      if (error) throw new Error(error.message);

      return (
        <div>
          {/* Render user-specific data */}
        </div>
      );
    }
    ```

## Supabase Ssr Helper Pattern

The `@supabase/ssr` library is specifically designed to simplify session management in server-side rendering (SSR) contexts like Next.js. It provides helper functions to create a Supabase client that automatically handles reading and writing the session cookie from the request and response headers. This is the recommended approach for handling user sessions across both client and server components.

Here is a typical pattern for creating a server-side Supabase client using the library:

```tsx
// lib/supabase/server.ts
import { createServerClient, type CookieOptions } from '@supabase/ssr';
import { cookies } from 'next/headers';

export function createSupabaseServerClient() {
  const cookieStore = cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value;
        },
        set(name: string, value: string, options: CookieOptions) {
          cookieStore.set({ name, value, ...options });
        },
        remove(name: string, options: CookieOptions) {
          cookieStore.set({ name, value: '', ...options });
        },
      },
    }
  );
}
```

This helper can then be used in any Server Component, Route Handler, or Server Action to get an authenticated Supabase client instance that correctly manages the user's session cookie, ensuring seamless authentication between the server and client.

## Common Pitfalls

When implementing Supabase in a Next.js App Router application, developers should be aware of several common pitfalls to avoid security vulnerabilities and bugs:

1.  **Leaking Secret Keys to the Client**: The most critical mistake is accidentally exposing your `SUPABASE_SERVICE_ROLE_KEY` to the browser. This can happen if you mistakenly prefix it with `NEXT_PUBLIC_` or import a server-only file into a client component. A leaked secret key gives an attacker full, unrestricted access to your database, bypassing all RLS policies.
    *   **Mitigation**: Never use the `NEXT_PUBLIC_` prefix for secret keys. Keep all code that uses the secret key strictly within server-only files (e.g., in `app/api/` routes or files marked for server-side execution). Use static analysis tools or lint rules to block imports of `process.env.SUPABASE_SERVICE_ROLE_KEY` in any file that might be bundled for the client.

2.  **Accidentally Bypassing RLS**: Using the secret key for operations that should be user-scoped will bypass RLS and potentially expose or modify data incorrectly. This can lead to data leakage between tenants or unauthorized data access.
    *   **Mitigation**: Default to using the publishable key for all data access. Only use the secret key for explicit, trusted administrative operations. Always have comprehensive RLS policies defined for every table and test them thoroughly.

3.  **Cookie Mismatch in SSR**: During Server-Side Rendering, if the auth cookie is not correctly forwarded to the server-side Supabase client, the server will render the page as if the user is unauthenticated. This leads to a flash of unauthenticated content before the client-side code hydrates and corrects it.
    *   **Mitigation**: Use the `@supabase/ssr` library, as it is designed to handle the forwarding of cookies correctly between the client and server environments. Ensure the Supabase auth cookie name (e.g., `sb-access-token`) is not being overwritten or blocked.

4.  **Using Secret Keys in Edge Runtimes**: Vercel's Edge runtime does not support traditional secret environment variables securely. Attempting to access `process.env.SUPABASE_SERVICE_ROLE_KEY` in an Edge function can fail or expose the key.
    *   **Mitigation**: For routes deployed to the Edge, rely exclusively on the publishable key and RLS for security. If admin-level access is required, use a standard Serverless Function (Node.js runtime) which securely supports environment variables.


# Server Component Authentication Strategy

## Admin Operations Strategy

For administrative operations within a server component or server-side route that must bypass Row-Level Security (RLS), the correct strategy is to initialize the Supabase client using the secret key (`SUPABASE_SERVICE_ROLE_KEY`). This key grants elevated privileges equivalent to the `service_role` in PostgreSQL, allowing it to perform actions like bulk data modifications, system-wide maintenance, or accessing tables without RLS policies. This approach should be used sparingly and only in trusted, server-only environments (e.g., API routes, Server Actions) that are never exposed to the client. An example is an internal API endpoint for clearing test data, where the client is created via `createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.SUPABASE_SERVICE_ROLE_KEY!)`. Exposing this key is a critical security risk, so it must be stored securely as a server-side environment variable without the `NEXT_PUBLIC_` prefix.

## User Scoped Strategy

For all operations in a server component that should respect a user's permissions and be subject to Row-Level Security (RLS), the correct strategy is to use the publishable key (`NEXT_PUBLIC_SUPABASE_ANON_KEY`) in combination with the user's session cookie. The Next.js App Router allows server components to access incoming request headers via the `cookies()` function from `next/headers`. By initializing the Supabase client with the publishable key and forwarding the user's cookie, the resulting client instance makes requests on behalf of that user. Supabase then correctly identifies the user's session and enforces all relevant RLS policies. This is the standard and secure way to fetch user-specific data during Server-Side Rendering (SSR). The client is created like this: `createClient(URL, ANON_KEY, { global: { headers: { cookie: cookies().toString() } } })`. This ensures that the server component has the exact same data access permissions as the user would have on the client side.


# Security Implications And Best Practices

## Threat Model

The primary security threats associated with Supabase secret keys (sb_secret_...) in 2026 involve their potential for exposure and misuse, as they grant elevated privileges and can bypass Row-Level Security (RLS). The threat model includes: 
1. **Client-Side Leak**: The most critical threat is the accidental exposure of a secret key in front-end code (e.g., JavaScript bundles) or browser storage. This would grant any user full, unrestricted access to the project's data and administrative functions. 
2. **Server Compromise**: An attacker gaining access to the server environment (e.g., VM, container, CI/CD runner) where the secret key is stored as an environment variable can exfiltrate the key and compromise the entire Supabase project. 
3. **Supply-Chain Breach**: A compromised third-party library or dependency (e.g., a malicious version of `@supabase/supabase-js`) could be designed to detect and log the secret key, sending it to an attacker. 
4. **Log and Build Artifact Leakage**: Secret keys can be inadvertently written to application logs, error reports (like Sentry), or baked into build artifacts such as Docker images, making them accessible to anyone who can view these assets. 
5. **Managed Cloud Platform (MCP) Server Abuse**: For integrations like Claude Code, if the MCP server where the agent runs is compromised, the agent's secret key can be stolen, leading to abuse of its granted permissions.

## Secure Storage Recommendations

To mitigate storage-related threats, secret keys (`sb_secret_...`) must be treated as highly sensitive credentials and never be hard-coded in source code. The best practice is to use dedicated secret management services. Recommendations include:
1. **Cloud-Native Secret Managers**: Store `sb_secret_...` values in services like AWS Secrets Manager, GCP Secret Manager, or Azure Key Vault. These services provide encryption at rest, fine-grained access control, and audit trails for secret access.
2. **Strict Access Policies**: Enforce IAM policies that grant read-only access to the secret exclusively to the specific server-side runtime identity (e.g., the IAM role for a Next.js server component's Lambda function) that requires it. Explicitly deny access from any client-side or public context.
3. **Environment Variable Injection**: Secrets should be injected into the application environment at deployment or runtime (e.g., by a CI/CD pipeline or container orchestration system). This prevents them from being committed to version control. In Next.js, server-only environment variables (not prefixed with `NEXT_PUBLIC_`) should be used.

## Key Rotation Strategy

Regularly rotating secret keys is a critical security hygiene practice that limits the impact of an undetected leak. The strategy should be:
1. **Rotation Cadence**: Rotate all secret keys at least quarterly. For highly sensitive environments or after any personnel changes with access, rotation should be more frequent. Immediate rotation is mandatory after any suspected compromise.
2. **Automation**: Key rotation should be automated via CI/CD pipelines. A typical automated workflow involves using the Supabase Management API to create a new secret key, securely storing it in the secrets manager, updating the application's environment configuration to use the new key, and then deploying the updated service.
3. **Dual-Key Rollout**: To ensure zero downtime, implement a dual-key or graceful rollout. The old key should remain valid for a short grace period while all services and clients transition to the new key. Once monitoring confirms the old key is no longer in use, it can be safely revoked via the Supabase dashboard or API.

## Leak Detection And Response

Proactive detection and a rapid response plan are essential for minimizing damage from a key leak. 
1. **Detection Methods**: 
   - **Code Repository Scanning**: Enable automated secret scanning services like GitHub secret scanning or GitLab's equivalent. These tools scan commits in real-time and can identify patterns matching Supabase secret keys.
   - **Log Monitoring**: Continuously monitor Supabase audit logs for unusual usage patterns, such as a high volume of administrative calls, queries from unexpected IP addresses, or access at odd hours. Ship these logs to a SIEM for advanced analysis and alerting.
2. **Immediate Remediation**: If a leak is detected or suspected, the response must be immediate:
   - **Instant Revocation**: The compromised `sb_secret_...` key must be revoked instantly. This can be done via the Supabase dashboard (Project Settings → API Keys → Revoke) or programmatically via the Management API.
   - **Rotation**: Immediately generate a new secret key to replace the compromised one and deploy it to all affected services.
   - **Investigation**: Use the audit logs to investigate what actions were performed using the leaked key to assess the extent of the breach.

## Auditing And Compliance

Comprehensive auditing is necessary for security, accountability, and compliance. 
1. **Supabase Audit Logs**: Supabase provides detailed audit logs that record which key was used, who used it, when it was used, and from what IP address. All creation, reveal, and revocation events for secret keys are logged. These logs are the primary source of truth for tracking key usage.
2. **Log Aggregation and Analysis**: For long-term retention and advanced analysis, audit logs should be shipped to a centralized Security Information and Event Management (SIEM) system. This allows for correlation with other security signals and setting up automated alerts for suspicious activities.
3. **Key Tagging**: When creating multiple secret keys, tag each one with metadata (e.g., service name, agent ID, purpose) to simplify traceability in audit logs.
4. **Compliance Alignment**: Secret management practices must align with relevant compliance standards. Treat `sb_secret_...` keys as sensitive data, potentially PII-sensitive if they provide access to PII. Enforce GDPR-compatible principles like data minimization (using scoped keys). Align access control, change management, and incident response procedures with frameworks like SOC 2 and ISO 27001. It's important to understand the shared responsibility model: Supabase secures the platform, but the user is responsible for protecting and managing their keys.


# Claude Code Integration Guide

## Mcp Server Setup

The recommended architecture for deploying a Managed Cloud Platform (MCP) server for Claude Code integration involves creating dedicated, isolated services, preferably self-hosted within a private network like a VPC or on-premises to control network egress. This setup enhances security by using mTLS for encrypted communication, restricting inbound traffic exclusively to the Claude Code control plane, and placing the MCP server behind an internal load balancer and a Web Application Firewall (WAF). For managing sensitive credentials like API keys, it is critical to use a dedicated secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault) instead of storing them in plaintext files like `.env` in production environments. Configuration can be managed through project-scoped settings for team collaboration and user-scoped settings for individual keys and preferences.

## Agent Key Management

For each AI agent, such as Claude Code, it is a best practice to create a dedicated, minimally-scoped secret key (`sb_secret_...`). This follows the principle of least privilege. The key should be scoped with the minimum required Supabase capabilities, for example, granting access only to specific schemas or tables via RLS policies and minimal REST permissions. When possible, using Supabase's scoped service keys or a short-lived proxy token is preferred. These keys must be stored securely in a secrets manager and injected into the MCP server's environment at runtime. To mitigate the risk of a compromised key, they should be rotated frequently, and their usage can be bound to the MCP server's identity, such as its IP address or a client certificate.

## Security Guardrails

Implementing robust security guardrails is crucial. All Supabase tables should have Row-Level Security (RLS) enforced to ensure least-privilege access. Policies should be designed to be restrictive for the public-facing publishable key, while the agent's secret key should operate under a 'surrogate service role' that allows for controlled elevation of privileges for specific, audited actions only. This can be achieved by denying direct write access and instead channeling modifications through audited stored procedures or RPCs. Further guardrails include separating read-only and write capabilities into different keys or agents, enforcing rate limits and resource quotas at both the MCP server layer and within Supabase (via a proxy or middleware), and utilizing the Claude Code sandbox and skill configurations to strictly limit the tools and actions the agent can perform. Per-agent action quotas, maximum conversation turns, and MCP timeouts should also be configured to prevent abuse and runaway processes.

## Observability And Auditing

A comprehensive observability strategy involves logging all agent prompts, MCP server requests, and resulting Supabase queries using structured telemetry. It is critical to redact all Personally Identifiable Information (PII) and secrets from logs before they are persisted. Logs should be correlated with unique identifiers for the agent, session, and request to enable effective tracing and debugging. For compliance and security analysis, an immutable audit trail should be maintained in a separate, write-once data store, such as an append-only log in object storage or a WORM-enabled database. Tools like Sentry can be used for error tracking, while cloud provider audit trails (e.g., AWS CloudTrail) should be monitored for any operations related to the secret keys themselves.


# Programmatic Project Control Guide

## Management Api Overview

Full programmatic control over a Supabase project is achieved primarily through the official Supabase Management API (also referred to as the Admin API). This API is specifically designed for automating platform-level administrative actions, such as creating and managing projects, configuring API keys, and adjusting project settings. It is distinct from the auto-generated PostgREST and Realtime APIs, which are intended for application-level data access. Administrative automation, such as scripts run by an AI agent like Claude Code, would typically execute from a trusted environment like a Supabase Managed Cloud Platform (MCP) server, which would then interact with the Management API to perform its tasks.

## Key Management Automation

The Management API provides a suite of endpoints for the complete lifecycle management of API keys. This includes programmatically creating new keys (both `sb_publishable_...` and `sb_secret_...`), rotating existing keys to enhance security, and deactivating or revoking keys immediately in case of a compromise. A typical automation workflow involves making a POST request to a create-key endpoint, which returns a key ID and its value. The secret value must then be stored securely. To rotate a key, another endpoint is called to generate a replacement, with an option to revoke the old one after a grace period. The ability to define fine-grained scopes on secret keys during creation allows for adherence to the principle of least privilege, limiting the key's capabilities to only what is necessary for its intended automation task.

## Resource Management Automation

Beyond key management, the Management API allows for programmatic control over a project's core resources. For the database, the API can handle project-level actions like creation and high-level settings, while schema modifications, table creation, and role management are typically performed by executing SQL statements through an admin endpoint or a direct database connection using an elevated secret key. Row-Level Security (RLS) policies are also managed via SQL. For authentication, the API enables management of auth providers, OIDC settings, and email templates. For storage, the API permits the management of buckets and objects, including admin-level actions like creating buckets and setting access policies.

## Automation Patterns

For reliable and predictable automation, it is best to adopt idempotent patterns, often associated with Infrastructure-as-Code (IaC). This involves treating API calls declaratively. For example, before creating a resource, a script should first check if it already exists (e.g., GET resource by name/ID). If it's missing, a POST request is made to create it; if it's present, a PATCH or PUT request is used to update it to the desired configuration. This 'upsert' logic prevents errors from re-running automation scripts. Automation clients must also be built to handle API constraints gracefully, such as implementing exponential backoff for 429 (Too Many Requests) rate-limiting responses and correctly handling pagination for list operations using tokens or limit/offset parameters as specified in the API documentation.


# Migration Playbook From Legacy Keys

## Deprecation Timeline

Supabase announced the new API key model in late 2025. A migration window was established, allowing both the legacy (anon/service_role) and new (publishable/secret) keys to coexist to facilitate a smooth transition. According to documentation and announcements from 2025-2026, the full deprecation of the legacy keys is expected in late 2026. New projects created during the transition period (approximately July–November 2025) were automatically provisioned with both sets of keys, but the use of legacy keys is discouraged for any new development.

## Migration Steps

A comprehensive, step-by-step playbook for migrating from legacy anon/service_role keys to the new publishable/secret key system is as follows:

1.  **Inventory:** Conduct a thorough audit of your entire codebase and infrastructure to identify all instances where the legacy `ANON_KEY` and `SERVICE_ROLE_KEY` are used. This includes frontend bundles, serverless functions, backend services, CI/CD pipelines, and any third-party integrations.
2.  **Create New Keys:** Navigate to the Supabase dashboard for each project environment (development, staging, production) and generate new key pairs: one publishable key (`sb_publishable_...`) and at least one secret key (`sb_secret_...`).
3.  **Update Environment Variables:** Add the new keys to your environment's secret store as new variables (e.g., `SB_PUBLISHABLE_KEY`, `SB_SECRET_KEY`). It is crucial to retain the legacy key variables temporarily to facilitate a potential rollback.
4.  **Upgrade SDKs:** Update all relevant Supabase client libraries to versions that support the new key system. This includes `@supabase/supabase-js` (to a version from 2024-2025 or later) and `@supabase/ssr` if used.
5.  **Code Refactoring:** Modify your application's initialization code. Client-side code (e.g., in Next.js client components) should now use the publishable key. Server-side code (e.g., in Next.js server components or API routes) should use the secret key.
6.  **Staging Deployment & Verification:** Deploy the updated application to a staging environment. Perform rigorous testing:
    *   **Client-Side Functional Tests:** Verify all user-facing authentication flows like sign-up, sign-in, password reset, and anonymous access using the publishable key.
    *   **RLS Policy Verification:** Execute a dedicated test suite to confirm that all Row Level Security policies behave as expected and correctly enforce data access rules with the new JWTs generated from publishable keys.
    *   **Server-Side Verification:** Test all backend jobs, administrative endpoints, and server-side logic that use the new secret key to ensure privileged operations succeed.
7.  **Canary Cut-over:** Begin routing a small percentage of production traffic (e.g., 5-10%) to the newly migrated infrastructure. Closely monitor key performance and error metrics.
8.  **Full Cut-over:** Once confident in the stability and correctness of the canary deployment, gradually increase traffic until 100% of users are on the new system.
9.  **Decommission Legacy Keys:** After a period of stable operation on the new keys, you can safely disable and remove the legacy keys from the Supabase dashboard and your environment variables.

## Validation Tests

To ensure a successful migration, a multi-layered testing strategy is essential. The following tests should be performed:

1.  **Functional and End-to-End Tests:**
    *   **Authentication Flows:** Test the complete user lifecycle, including sign-up, sign-in, sign-out, token refresh, and password recovery.
    *   **Anonymous Access:** Verify that unauthenticated users can access public data as intended using the publishable key.
    *   **Third-Party Integrations:** Run smoke tests for any external services that connect to your Supabase backend to ensure they continue to function correctly.

2.  **Row Level Security (RLS) Policy Verification:**
    *   **Allow/Deny Scenarios:** Create a comprehensive test suite that explicitly checks RLS policies. This should include tests for scenarios where access should be granted and, more importantly, where it should be denied for different user roles.
    *   **Authenticated vs. Anonymous Roles:** Confirm that RLS policies correctly differentiate between requests made with a user's session token versus an anonymous request using only the publishable key.

3.  **Server-Side Verification:**
    *   **Admin Endpoint Tests:** Execute tests against all server-side endpoints that use the secret key to perform administrative or privileged operations. Verify they can successfully perform actions that bypass RLS.
    *   **Background Jobs:** Ensure any background or scheduled jobs that rely on the `service_role` equivalent permissions are functioning correctly with the new secret key.

4.  **CI/CD and Static Analysis:**
    *   **Linting Rules:** Implement static analysis checks in your CI pipeline to prevent the secret key from being accidentally imported into client-side components or committed to source control.

## Rollback Plan

A clear rollback plan is critical in case of unforeseen issues during the migration. The strategy should be as follows:

**Rollback Procedure:**
1.  **Maintain Legacy Keys:** Do not disable or delete the legacy `anon` and `service_role` keys in the Supabase dashboard until the migration has been fully validated in production for a sufficient period.
2.  **Revert Environment Variables:** If a critical issue is detected, the immediate action is to revert the environment variables in your hosting environment (e.g., Vercel, AWS) back to the legacy `ANON_KEY` and `SERVICE_ROLE_KEY`.
3.  **Redeploy:** Trigger a redeployment of the previous stable version of your application. Since the legacy keys were never disabled on the Supabase platform, the older application build will be able to connect and function immediately.

**Key Monitoring Signals to Watch:**
To detect issues proactively during the cut-over, set up alerts and closely monitor the following metrics:
*   **API Error Rates:** A spike in HTTP `401 Unauthorized`, `403 Forbidden`, or `5xx` server error responses.
*   **Authentication Errors:** An increase in logs related to 'invalid JWT', 'signature mismatch', or other authentication failures.
*   **RLS Denials:** Unexpected increases in database logs showing RLS policy violations, indicating that client-side requests are being improperly denied.
*   **Application-Specific Errors:** A rise in sign-in/sign-up failures or errors from administrative endpoints.
*   **API Latency:** Any significant increase in response times, which could indicate issues with the new key exchange mechanism at the gateway.


# Technical Model Of New Keys

## Token Type

The new Supabase API keys (both `sb_publishable_...` and `sb_secret_...`) are not JSON Web Tokens (JWTs). Instead, they are opaque reference tokens. These tokens are short, randomly generated strings with a checksum, which act as pointers or references to the actual credentials and permissions stored securely within the Supabase platform. They do not contain any claims or user data themselves, unlike JWTs.

## Validation Process

The validation of these opaque tokens is handled at the edge by the Supabase API gateway, not by the downstream services like PostgREST or Storage. When a request arrives with an `apikey` header containing an `sb_` token, the gateway intercepts it. It validates the opaque token against its internal database. If the token is valid, the gateway substitutes it with an appropriate, internally generated, short-lived JWT signed with ES256. 
- If the request uses a `publishable` key, the gateway generates an `anon` role JWT.
- If the request uses a `secret` key, the gateway generates a `service_role` JWT, which can bypass Row-Level Security.
This internal JWT is then passed in the `Authorization` header to the upstream service, which processes the request as it did with the legacy system. This process is transparent to the end service but centralizes and secures the key validation logic at the gateway.

## Implications For Developers

This new technical model has several practical implications for developers:

*   **Edge Functions**: Since the new keys are not JWTs, the default JWT verification in Supabase Edge Functions will fail. Developers using `sb_` keys with Edge Functions must invoke the function with the `--no-verify-jwt` flag. Consequently, they become responsible for implementing their own authorization logic within the function, such as manually checking for the presence and validity of the `apikey` header.
*   **Self-Hosted Instances**: As of 2026, self-hosted Supabase deployments have a limitation where they only support a single publishable key and a single secret key per project. This contrasts with the Supabase cloud platform, which allows for the creation of multiple secret keys for better security segmentation.
*   **Local Development**: When migrating to the new opaque keys, developers working in a local environment may need to perform additional configuration related to the JWT signing key or JWKS (JSON Web Key Set) to properly simulate the gateway's token substitution behavior for testing purposes.


# Required Library Versions

## Supabase Js Version

≥ 2.39.0

## Supabase Ssr Version

≥ 0.4.0

## Next Js Version

13.5+


# Testing And Observability Strategies

## Testing Approaches

A robust testing strategy is crucial to validate that API keys are used correctly and that security policies like Row-Level Security (RLS) are enforced as intended. Recommended approaches include:
1. **Unit Tests**: Use mock libraries for `supabase-js` to write unit tests. These tests can simulate different authentication states (e.g., anonymous user, authenticated user) and verify that your application logic correctly attempts to perform actions that would be governed by RLS, without needing a live database connection.
2. **Integration Tests**: These are essential for validating real-world behavior. Set up a temporary Supabase project (either using the local development stack via `supabase start` or a dedicated cloud project for staging). Write end-to-end tests that:
   - Log in as a test user with a client-side instance using the publishable key. The test should assert that the user can only fetch and modify data they own, confirming RLS policies are working.
   - Call a server-only admin route or server action that uses the secret key. The test should confirm that this client can perform privileged operations that would otherwise be blocked by RLS (e.g., deleting data across all users).

## Observability And Monitoring

Continuous monitoring helps detect anomalies, accidental key exposure, and security threats. Key observability practices include:
1. **Supabase Logs**: Enable Supabase's Realtime logs and Audit logs. These logs provide detailed information on API requests, including the user ID, method, route, and key usage. Unusual patterns, such as high-volume admin calls from unexpected IPs, can be detected by analyzing these logs.
2. **Log Sinks and Aggregation**: Forward Supabase logs to an external logging provider or SIEM (e.g., Cloudflare/Logflare, Datadog). This allows for long-term retention, advanced querying, and setting up automated alerts. For instance, an alert can be configured to trigger if a secret key is detected being used in a context that suggests a client-side origin.
3. **Client-Side Log Inspection**: Specifically monitor client-side error reports and logs for any accidental inclusion of secret keys or other sensitive environment variables.

## Ci Cd Checks

Integrating automated security checks into the CI/CD pipeline is a proactive measure to prevent secret key exposure before code is deployed. Key suggestions include:
1. **Lint Rules for Secret Exposure**: Implement custom lint rules in your CI pipeline. A critical rule would be to forbid the import or usage of the secret key environment variable (e.g., `process.env.SUPABASE_SERVICE_ROLE_KEY` or `process.env.SB_SECRET_KEY`) in any file identified as a client component (e.g., files containing `'use client';` in Next.js) or in any file outside of designated server-only directories like `app/api/`.
2. **Static Analysis Security Testing (SAST)**: Incorporate SAST tools that can scan the codebase for hardcoded secrets or unsafe usage patterns before a build is created.
3. **Build Log Scanning**: Ensure that CI/CD build and test logs are configured to mask secrets, and add a post-build step to scan the logs for any accidentally exposed credentials.

