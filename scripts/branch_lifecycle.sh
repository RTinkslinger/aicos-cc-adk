#!/bin/bash
################################################################################
# branch_lifecycle.sh
#
# AI CoS Parallel Development — 6-Step Branch Lifecycle Helper
#
# Codifies the standard workflow:
#   1. CREATE — git checkout -b {prefix}/{slug}
#   2. WORK — (manual commits)
#   3. COMPLETE — (manual status update to Testing in Notion)
#   4. REVIEW — diff vs main
#   5. MERGE — merge to main with message
#   6. CLOSE — delete branch
#
# Usage:
#   ./scripts/branch_lifecycle.sh create feat/my-feature
#   ./scripts/branch_lifecycle.sh status
#   ./scripts/branch_lifecycle.sh diff feat/my-feature
#   ./scripts/branch_lifecycle.sh merge feat/my-feature
#   ./scripts/branch_lifecycle.sh close feat/my-feature
#   ./scripts/branch_lifecycle.sh full feat/my-feature
#   ./scripts/branch_lifecycle.sh help
#
################################################################################

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_success() {
  echo -e "${GREEN}✓${NC} $1"
}

log_info() {
  echo -e "${BLUE}ℹ${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
  echo -e "${RED}✗${NC} $1" >&2
}

# Check if on main branch
check_on_main() {
  local current_branch
  current_branch=$(git rev-parse --abbrev-ref HEAD)
  if [ "$current_branch" != "main" ]; then
    log_error "Not on main branch. Current: $current_branch"
    return 1
  fi
  return 0
}

# Check if branch exists
branch_exists() {
  git rev-parse --verify "$1" > /dev/null 2>&1
}

# Command: create
cmd_create() {
  local branch_name="$1"
  
  if [ -z "$branch_name" ]; then
    log_error "Branch name required: create <branch>"
    return 1
  fi
  
  if branch_exists "$branch_name"; then
    log_error "Branch '$branch_name' already exists"
    return 1
  fi
  
  check_on_main || return 1
  
  git checkout -b "$branch_name"
  log_success "Created and checked out branch: $branch_name"
  echo
  log_info "Next steps:"
  echo "  1. Make your changes and commit: git commit -m '...'"
  echo "  2. Update Build Roadmap: Status = 🔨 In Progress, Branch = $branch_name"
  echo "  3. When done, run: ./scripts/branch_lifecycle.sh diff $branch_name"
}

# Command: status
cmd_status() {
  log_info "Active branches:"
  echo
  git branch -v
  echo
  
  # Check for worktrees
  if git worktree list > /dev/null 2>&1; then
    local worktree_count
    worktree_count=$(git worktree list | wc -l)
    if [ "$worktree_count" -gt 1 ]; then
      echo
      log_info "Active worktrees:"
      git worktree list
    fi
  fi
  echo
  log_info "Current HEAD:"
  git log -1 --oneline
}

# Command: diff
cmd_diff() {
  local branch_name="$1"
  
  if [ -z "$branch_name" ]; then
    log_error "Branch name required: diff <branch>"
    return 1
  fi
  
  if ! branch_exists "$branch_name"; then
    log_error "Branch '$branch_name' does not exist"
    return 1
  fi
  
  check_on_main || return 1
  
  echo
  log_info "Diff stats (main..$branch_name):"
  echo
  git diff main.."$branch_name" --stat
  echo
  log_info "Full diff:"
  echo "────────────────────────────────────────────────────────────"
  git diff main.."$branch_name"
  echo "────────────────────────────────────────────────────────────"
  echo
  log_info "Review complete. Next: ./scripts/branch_lifecycle.sh merge $branch_name"
}

# Command: merge
cmd_merge() {
  local branch_name="$1"
  
  if [ -z "$branch_name" ]; then
    log_error "Branch name required: merge <branch>"
    return 1
  fi
  
  if ! branch_exists "$branch_name"; then
    log_error "Branch '$branch_name' does not exist"
    return 1
  fi
  
  check_on_main || return 1
  
  git merge "$branch_name" --message "Merge branch '$branch_name' into main"
  log_success "Merged '$branch_name' into main"
  echo
  log_info "Recent commits:"
  git log -3 --oneline
}

# Command: close
cmd_close() {
  local branch_name="$1"
  
  if [ -z "$branch_name" ]; then
    log_error "Branch name required: close <branch>"
    return 1
  fi
  
  if ! branch_exists "$branch_name"; then
    log_error "Branch '$branch_name' does not exist"
    return 1
  fi
  
  # Safety check: don't delete main
  if [ "$branch_name" = "main" ]; then
    log_error "Cannot delete main branch"
    return 1
  fi
  
  git branch -d "$branch_name"
  log_success "Deleted branch: $branch_name"
  echo
  log_info "Update Build Roadmap: Branch = clear, Status = ✅ Shipped"
}

# Command: full
cmd_full() {
  local branch_name="$1"
  
  if [ -z "$branch_name" ]; then
    log_error "Branch name required: full <branch>"
    return 1
  fi
  
  if ! branch_exists "$branch_name"; then
    log_error "Branch '$branch_name' does not exist"
    return 1
  fi
  
  check_on_main || return 1
  
  # Show diff
  echo
  log_info "Step 4: REVIEW — Showing diff..."
  echo
  git diff main.."$branch_name" --stat
  echo
  
  # Ask for confirmation
  echo
  read -p "$(echo -e ${YELLOW}?)$(echo -ne ${NC}) Proceed with merge and close? (y/N): " -r
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warn "Aborted"
    return 0
  fi
  
  # Merge
  echo
  log_info "Step 5: MERGE..."
  git merge "$branch_name" --message "Merge branch '$branch_name' into main"
  log_success "Merged '$branch_name' into main"
  
  # Close
  echo
  log_info "Step 6: CLOSE..."
  git branch -d "$branch_name"
  log_success "Deleted branch: $branch_name"
  echo
  log_info "Full lifecycle complete!"
  echo
  log_info "Final steps:"
  echo "  - Update Build Roadmap: Branch = clear, Status = ✅ Shipped"
  echo "  - Push to remote if needed: git push origin main"
}

# Command: help
cmd_help() {
  cat << 'EOF'
AI CoS Parallel Development — Branch Lifecycle Helper
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6-Step Branch Lifecycle:
  1. CREATE  — checkout -b <branch>       [automated]
  2. WORK    — commit changes             [manual]
  3. COMPLETE — update Notion status      [manual]
  4. REVIEW  — diff main..<branch>        [automated]
  5. MERGE   — merge to main              [automated]
  6. CLOSE   — delete branch              [automated]

COMMANDS:
  create <branch>     Create and checkout a new branch
  status              Show active branches and current HEAD
  diff <branch>       Show diff vs main (Step 4)
  merge <branch>      Merge branch to main (Step 5)
  close <branch>      Delete branch (Step 6)
  full <branch>       Run Steps 4→5→6 in sequence (interactive)
  help                Show this message

EXAMPLES:
  ./scripts/branch_lifecycle.sh create feat/my-feature
  ./scripts/branch_lifecycle.sh status
  ./scripts/branch_lifecycle.sh diff feat/my-feature
  ./scripts/branch_lifecycle.sh full feat/my-feature

BRANCH NAMING:
  feat/<feature>      New feature (e.g., feat/content-pipeline-v5)
  fix/<bug>           Bug fix (e.g., fix/dedup-logic)
  research/<topic>    Research task (e.g., research/agent-sdk)
  infra/<task>        Infrastructure (e.g., infra/parallel-dev-phase1)

EOF
}

# Main dispatcher
main() {
  if [ $# -eq 0 ]; then
    cmd_help
    exit 0
  fi
  
  local cmd="$1"
  shift || true
  
  case "$cmd" in
    create)
      cmd_create "$@"
      ;;
    status)
      cmd_status
      ;;
    diff)
      cmd_diff "$@"
      ;;
    merge)
      cmd_merge "$@"
      ;;
    close)
      cmd_close "$@"
      ;;
    full)
      cmd_full "$@"
      ;;
    help)
      cmd_help
      ;;
    *)
      log_error "Unknown command: $cmd"
      echo
      cmd_help
      exit 1
      ;;
  esac
}

main "$@"
