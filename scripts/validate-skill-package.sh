#!/bin/bash

##############################################################################
# validate-skill-package.sh
# Validates .skill files (ZIP archives) and optional packaging workflow
#
# Usage:
#   ./validate-skill-package.sh <.skill-file>
#   ./validate-skill-package.sh --package <source.md> <skill-name>
#
# Exit codes:
#   0 = All validations passed
#   1 = Any validation failed
##############################################################################

set -u  # Fail on undefined variables

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0

# Helper: print colored result
pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((CHECKS_PASSED++))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((CHECKS_FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Main validation function
validate_skill() {
    local skill_file="$1"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "VALIDATING SKILL PACKAGE: $skill_file"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo

    # Check file exists
    if [[ ! -f "$skill_file" ]]; then
        fail "File does not exist: $skill_file"
        return 1
    fi
    pass "File exists"

    # Check file extension
    if [[ ! "$skill_file" =~ \.skill$ ]]; then
        warn "File does not have .skill extension (but proceeding with validation)"
    fi

    # Validate ZIP format
    if ! unzip -t "$skill_file" > /dev/null 2>&1; then
        fail "File is not a valid ZIP archive"
        return 1
    fi
    pass "Valid ZIP archive"

    # Extract skill name from ZIP structure
    # Expected: {skill-name}/SKILL.md at root level
    local skill_structure
    skill_structure=$(unzip -l "$skill_file" | grep 'SKILL.md')

    if [[ -z "$skill_structure" ]]; then
        fail "No SKILL.md found in archive"
        return 1
    fi
    pass "SKILL.md file found in archive"

    # Extract the skill directory name (first directory in path)
    local skill_dir
    skill_dir=$(echo "$skill_structure" | awk '{print $NF}' | cut -d'/' -f1)

    if [[ -z "$skill_dir" ]]; then
        fail "Could not determine skill directory name from archive structure"
        return 1
    fi
    pass "Skill directory found: $skill_dir"

    # Verify structure matches expected pattern: {name}/SKILL.md
    if ! unzip -l "$skill_file" | grep -q "^.*$skill_dir/SKILL.md$"; then
        fail "Archive structure is invalid. Expected: {skill-name}/SKILL.md"
        return 1
    fi
    pass "Archive structure is valid: $skill_dir/SKILL.md"

    # Extract SKILL.md to temporary file for validation
    local temp_skill_md
    temp_skill_md=$(mktemp)
    trap "rm -f $temp_skill_md" EXIT

    if ! unzip -p "$skill_file" "$skill_dir/SKILL.md" > "$temp_skill_md"; then
        fail "Could not extract SKILL.md from archive"
        return 1
    fi

    # Validate frontmatter
    echo
    info "Checking SKILL.md frontmatter..."

    # Check for YAML frontmatter (starts with ---)
    if ! head -1 "$temp_skill_md" | grep -q "^---"; then
        fail "Missing frontmatter marker (---) at start of SKILL.md"
        return 1
    fi
    pass "Frontmatter delimiter found"

    # Extract frontmatter (between first and second ---)
    local frontmatter
    frontmatter=$(sed -n '/^---$/,/^---$/p' "$temp_skill_md" | sed '1d;$d')

    # Check for 'name' field
    if ! echo "$frontmatter" | grep -q "^name:"; then
        fail "Missing 'name' field in frontmatter"
        return 1
    fi
    pass "Has 'name' field"

    # Check for 'version' field
    if ! echo "$frontmatter" | grep -q "^version:"; then
        fail "Missing 'version' field in frontmatter"
        return 1
    fi
    pass "Has 'version' field"

    # Check for 'description' field
    if ! echo "$frontmatter" | grep -q "^description:"; then
        fail "Missing 'description' field in frontmatter"
        return 1
    fi
    pass "Has 'description' field"

    # Validate description length (≤1024 characters)
    local description
    description=$(echo "$frontmatter" | grep "^description:" | cut -d: -f2- | sed 's/^ *//; s/ *$//')
    local desc_length
    desc_length=${#description}

    if [[ $desc_length -gt 1024 ]]; then
        fail "Description is too long: $desc_length chars (max 1024)"
        return 1
    fi
    pass "Description length valid: $desc_length/1024 chars"

    # Extract and validate version format (should be semantic: X.Y.Z)
    local version
    version=$(echo "$frontmatter" | grep "^version:" | cut -d: -f2- | sed 's/^ *//; s/ *$//' | tr -d '"' | tr -d "'")

    if [[ -z "$version" ]]; then
        fail "Version field is empty"
        return 1
    fi

    if ! echo "$version" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+'; then
        warn "Version format is non-standard: $version (expected semantic versioning: X.Y.Z)"
    else
        pass "Version format valid: $version"
    fi

    # Summary
    echo
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "VALIDATION SUMMARY"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "Checks passed: ${GREEN}$CHECKS_PASSED${NC}"
    echo -e "Checks failed: ${RED}$CHECKS_FAILED${NC}"

    if [[ $CHECKS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}✓ ALL CHECKS PASSED${NC}"
        echo
        return 0
    else
        echo -e "${RED}✗ VALIDATION FAILED${NC}"
        echo
        return 1
    fi
}

# Package and validate function
package_and_validate() {
    local source_md="$1"
    local skill_name="$2"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "PACKAGING SKILL: $skill_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo

    # Validate source file
    if [[ ! -f "$source_md" ]]; then
        fail "Source markdown file not found: $source_md"
        return 1
    fi
    pass "Source file exists: $source_md"

    # Create packaging directory
    local pkg_temp
    pkg_temp=$(mktemp -d)
    trap "rm -rf $pkg_temp" EXIT

    info "Creating package structure in $pkg_temp"
    mkdir -p "$pkg_temp/$skill_name" || {
        fail "Could not create package directory"
        return 1
    }

    # Copy source to SKILL.md
    cp "$source_md" "$pkg_temp/$skill_name/SKILL.md" || {
        fail "Could not copy source file to package"
        return 1
    }
    pass "Copied source to $skill_name/SKILL.md"

    # Create the .skill file
    local output_skill="${skill_name}.skill"
    local current_dir
    current_dir=$(pwd)

    cd "$pkg_temp" || {
        fail "Could not change to package directory"
        return 1
    }

    if ! zip -q -r "$current_dir/$output_skill" "$skill_name/"; then
        cd "$current_dir"
        fail "Could not create ZIP archive"
        return 1
    fi

    cd "$current_dir" || exit 1

    if [[ ! -f "$output_skill" ]]; then
        fail "Output .skill file was not created"
        return 1
    fi
    pass "Created package: $output_skill"

    # Now validate the created package
    echo
    validate_skill "$output_skill"
    local validate_result=$?

    if [[ $validate_result -eq 0 ]]; then
        echo
        info "Package ready at: $(pwd)/$output_skill"
    fi

    return $validate_result
}

# Main script entry point
main() {
    if [[ $# -eq 0 ]]; then
        echo "Usage:"
        echo "  $0 <.skill-file>              # Validate existing .skill package"
        echo "  $0 --package <source.md> <skill-name>  # Package and validate"
        echo
        exit 1
    fi

    if [[ "$1" == "--package" ]]; then
        if [[ $# -lt 3 ]]; then
            echo "Error: --package requires <source.md> and <skill-name>"
            exit 1
        fi
        package_and_validate "$2" "$3"
        exit $?
    else
        validate_skill "$1"
        exit $?
    fi
}

main "$@"
