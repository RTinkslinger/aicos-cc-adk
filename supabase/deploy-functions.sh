#!/bin/bash
# =============================================================================
# IRGI Phase A: Deploy Supabase Edge Functions
# =============================================================================
# Deploys the embed and search Edge Functions to the AI CoS Supabase project.
#
# Prerequisites:
#   - Supabase CLI installed: brew install supabase/tap/supabase
#   - Logged in: supabase login
#   - Voyage AI API key ready
#
# Usage:
#   ./supabase/deploy-functions.sh                    # Deploy both functions
#   ./supabase/deploy-functions.sh --set-secrets      # Deploy + set secrets
#   ./supabase/deploy-functions.sh --status           # Check function status
# =============================================================================

set -euo pipefail

PROJECT_REF="llfkxnsfczludgigknbs"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check prerequisites
check_prerequisites() {
  if ! command -v supabase &> /dev/null; then
    log_error "Supabase CLI not found. Install: brew install supabase/tap/supabase"
    exit 1
  fi
  log_info "Supabase CLI found: $(supabase --version 2>&1 | head -1)"
}

# Deploy a single Edge Function
deploy_function() {
  local func_name="$1"
  local func_dir="${SCRIPT_DIR}/functions/${func_name}"

  if [ ! -f "${func_dir}/index.ts" ]; then
    log_error "Function not found: ${func_dir}/index.ts"
    return 1
  fi

  log_info "Deploying '${func_name}' to project ${PROJECT_REF}..."

  # Edge Functions called by pg_net (internal) don't need JWT verification
  # because pg_net sends the request from within the Postgres context.
  # The search function is called by WebFront with an anon key (JWT verified).
  local verify_jwt="--no-verify-jwt"
  if [ "$func_name" = "search" ]; then
    verify_jwt=""  # search requires JWT (called by external clients)
  fi

  supabase functions deploy "$func_name" \
    --project-ref "$PROJECT_REF" \
    $verify_jwt

  log_info "Deployed '${func_name}' successfully"
}

# Set secrets
set_secrets() {
  log_info "Setting secrets for project ${PROJECT_REF}..."

  if [ -z "${VOYAGE_API_KEY:-}" ]; then
    log_warn "VOYAGE_API_KEY not set in environment."
    echo -n "Enter Voyage AI API key: "
    read -r VOYAGE_API_KEY
  fi

  if [ -z "$VOYAGE_API_KEY" ]; then
    log_error "No API key provided. Aborting."
    exit 1
  fi

  supabase secrets set "VOYAGE_API_KEY=${VOYAGE_API_KEY}" \
    --project-ref "$PROJECT_REF"

  log_info "Secrets set successfully"
}

# Check function status
check_status() {
  log_info "Listing Edge Functions for project ${PROJECT_REF}..."
  supabase functions list --project-ref "$PROJECT_REF"
}

# Main
main() {
  check_prerequisites

  case "${1:-deploy}" in
    --status)
      check_status
      ;;
    --set-secrets)
      deploy_function "embed"
      deploy_function "search"
      set_secrets
      log_info "All functions deployed and secrets configured"
      ;;
    --secrets-only)
      set_secrets
      ;;
    deploy|"")
      deploy_function "embed"
      deploy_function "search"
      log_info "All functions deployed"
      log_warn "Remember to set secrets if not already done: $0 --set-secrets"
      ;;
    *)
      echo "Usage: $0 [--set-secrets | --secrets-only | --status]"
      exit 1
      ;;
  esac

  echo ""
  log_info "Post-deployment checklist:"
  echo "  1. Vault secret: SELECT vault.create_secret('https://${PROJECT_REF}.supabase.co', 'project_url');"
  echo "  2. Backfill: SELECT * FROM util.backfill_embeddings();"
  echo "  3. Verify: SELECT id, title, embedding IS NOT NULL FROM content_digests;"
  echo "  4. Test search: curl -X POST https://${PROJECT_REF}.supabase.co/functions/v1/search \\"
  echo "       -H 'Authorization: Bearer <anon-key>' \\"
  echo "       -H 'Content-Type: application/json' \\"
  echo "       -d '{\"query\": \"agentic AI infrastructure\"}'"
}

main "$@"
