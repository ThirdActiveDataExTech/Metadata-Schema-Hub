#!/bin/bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECTS=(
    "packages/active-metadata"
    "apps/catalog-service"
    "apps/metadata-ingestion"
)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

QUIET=false

usage() {
    echo "Usage: $0 [-q|--quiet]"
    echo "  -q, --quiet  Suppress output on success, show only on failure"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -q|--quiet) QUIET=true; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

run_cmd() {
    local label=$1
    shift
    if $QUIET; then
        local output
        if output=$("$@" 2>&1); then
            echo -e "${GREEN}✓${NC} $label"
        else
            echo -e "${RED}✗${NC} $label"
            echo "$output"
            exit 1
        fi
    else
        echo -e "\n${GREEN}[$label]${NC} $*"
        "$@"
    fi
}

run_checks() {
    local project=$1
    local dir="$ROOT_DIR/$project"
    unset VIRTUAL_ENV

    if [[ ! -d "$dir" ]]; then
        $QUIET || echo -e "${YELLOW}[SKIP]${NC} $project (not found)"
        return
    fi

    if $QUIET; then
        echo -e "${YELLOW}▶${NC} $project"
    else
        echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}▶ $project${NC}"
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    fi

    cd "$dir"

    run_cmd "sync" uv sync --all-groups
    run_cmd "ruff" uv run ruff check .
    run_cmd "pyright" uv run pyright ./

    if [[ -d "tests" ]]; then
        if $QUIET; then
            run_cmd "pytest" uv run pytest tests/ -q
        else
            run_cmd "pytest" uv run pytest tests/ -v
        fi
    fi
}

main() {
    echo -e "${GREEN}Starting checks for all projects...${NC}"

    for project in "${PROJECTS[@]}"; do
        run_checks "$project"
    done

    echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✓ All checks passed${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

main "$@"
