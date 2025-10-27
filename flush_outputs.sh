#!/bin/bash

###############################################################################
# Output Flushing and Organization Script
#
# This script provides utilities to:
# 1. Flush/clean all analysis outputs
# 2. Archive old outputs with timestamps
# 3. Move outputs from scattered locations to organized data/output structure
# 4. Prepare clean slate for new analysis runs
#
# Usage:
#   ./flush_outputs.sh --flush          # Clean all outputs
#   ./flush_outputs.sh --archive        # Archive outputs before cleaning
#   ./flush_outputs.sh --organize       # Move outputs to data folder
#   ./flush_outputs.sh --all            # Archive, flush, and prepare clean state
#   ./flush_outputs.sh --status         # Show current output status
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Output directories
ANALYSIS_OUTPUT="${PROJECT_ROOT}/analysis/output"
ANALYSIS_RESULTS="${PROJECT_ROOT}/analysis/results"
ENHANCED_RESULTS="${PROJECT_ROOT}/analysis/enhanced_results"
DATA_OUTPUT="${PROJECT_ROOT}/data/output"
DATA_ARCHIVE="${PROJECT_ROOT}/data/archive"

# Organized output structure
ORGANIZED_OUTPUT="${PROJECT_ROOT}/data/output"
ORGANIZED_BASIC="${ORGANIZED_OUTPUT}/basic"
ORGANIZED_ENHANCED="${ORGANIZED_OUTPUT}/enhanced"
ORGANIZED_MLX="${ORGANIZED_OUTPUT}/mlx"
ORGANIZED_SUMMARY="${ORGANIZED_OUTPUT}/summary"
ORGANIZED_LOGS="${ORGANIZED_OUTPUT}/logs"
ORGANIZED_CACHE="${ORGANIZED_OUTPUT}/cache"

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo -e "${CYAN}$1${NC}"
    echo "================================================================="
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

count_files() {
    local dir="$1"
    if [ -d "$dir" ]; then
        find "$dir" -type f | wc -l | tr -d ' '
    else
        echo "0"
    fi
}

get_dir_size() {
    local dir="$1"
    if [ -d "$dir" ]; then
        du -sh "$dir" 2>/dev/null | cut -f1
    else
        echo "0B"
    fi
}

###############################################################################
# Status Check
###############################################################################

show_status() {
    print_header "📊 Current Output Status"

    echo ""
    echo "Analysis Output Directories:"
    echo "----------------------------"

    # Analysis output
    if [ -d "$ANALYSIS_OUTPUT" ]; then
        local count=$(count_files "$ANALYSIS_OUTPUT")
        local size=$(get_dir_size "$ANALYSIS_OUTPUT")
        echo -e "  analysis/output/         ${GREEN}$count files${NC} ($size)"
    else
        echo -e "  analysis/output/         ${YELLOW}Does not exist${NC}"
    fi

    # Analysis results
    if [ -d "$ANALYSIS_RESULTS" ]; then
        local count=$(count_files "$ANALYSIS_RESULTS")
        local size=$(get_dir_size "$ANALYSIS_RESULTS")
        echo -e "  analysis/results/        ${GREEN}$count files${NC} ($size)"
    else
        echo -e "  analysis/results/        ${YELLOW}Does not exist${NC}"
    fi

    # Enhanced results
    if [ -d "$ENHANCED_RESULTS" ]; then
        local count=$(count_files "$ENHANCED_RESULTS")
        local size=$(get_dir_size "$ENHANCED_RESULTS")
        echo -e "  analysis/enhanced_results/ ${GREEN}$count files${NC} ($size)"
    else
        echo -e "  analysis/enhanced_results/ ${YELLOW}Does not exist${NC}"
    fi

    # Data output
    if [ -d "$DATA_OUTPUT" ]; then
        local count=$(count_files "$DATA_OUTPUT")
        local size=$(get_dir_size "$DATA_OUTPUT")
        echo -e "  data/output/             ${GREEN}$count files${NC} ($size)"
    else
        echo -e "  data/output/             ${YELLOW}Does not exist${NC}"
    fi

    echo ""
    echo "Archives:"
    echo "----------------------------"

    if [ -d "$DATA_ARCHIVE" ]; then
        local archive_count=$(find "$DATA_ARCHIVE" -maxdepth 1 -type d -name "archive_*" | wc -l | tr -d ' ')
        echo -e "  data/archive/            ${GREEN}$archive_count archived runs${NC}"

        # Show latest archive
        local latest=$(find "$DATA_ARCHIVE" -maxdepth 1 -type d -name "archive_*" | sort -r | head -n 1)
        if [ -n "$latest" ]; then
            local archive_name=$(basename "$latest")
            echo -e "  Latest:                  ${CYAN}$archive_name${NC}"
        fi
    else
        echo -e "  data/archive/            ${YELLOW}Does not exist${NC}"
    fi

    echo ""
}

###############################################################################
# Archive Outputs
###############################################################################

archive_outputs() {
    print_header "📦 Archiving Outputs"

    # Create timestamp
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local archive_dir="${DATA_ARCHIVE}/archive_${timestamp}"

    # Create archive directory
    mkdir -p "$archive_dir"

    print_info "Archive location: $archive_dir"
    echo ""

    local archived_count=0

    # Archive analysis/output
    if [ -d "$ANALYSIS_OUTPUT" ] && [ "$(ls -A $ANALYSIS_OUTPUT 2>/dev/null)" ]; then
        cp -r "$ANALYSIS_OUTPUT" "${archive_dir}/analysis_output"
        local count=$(count_files "$ANALYSIS_OUTPUT")
        print_success "Archived analysis/output/ ($count files)"
        archived_count=$((archived_count + count))
    fi

    # Archive analysis/results
    if [ -d "$ANALYSIS_RESULTS" ] && [ "$(ls -A $ANALYSIS_RESULTS 2>/dev/null)" ]; then
        cp -r "$ANALYSIS_RESULTS" "${archive_dir}/analysis_results"
        local count=$(count_files "$ANALYSIS_RESULTS")
        print_success "Archived analysis/results/ ($count files)"
        archived_count=$((archived_count + count))
    fi

    # Archive analysis/enhanced_results
    if [ -d "$ENHANCED_RESULTS" ] && [ "$(ls -A $ENHANCED_RESULTS 2>/dev/null)" ]; then
        cp -r "$ENHANCED_RESULTS" "${archive_dir}/enhanced_results"
        local count=$(count_files "$ENHANCED_RESULTS")
        print_success "Archived analysis/enhanced_results/ ($count files)"
        archived_count=$((archived_count + count))
    fi

    # Archive data/output
    if [ -d "$DATA_OUTPUT" ] && [ "$(ls -A $DATA_OUTPUT 2>/dev/null)" ]; then
        cp -r "$DATA_OUTPUT" "${archive_dir}/data_output"
        local count=$(count_files "$DATA_OUTPUT")
        print_success "Archived data/output/ ($count files)"
        archived_count=$((archived_count + count))
    fi

    # Create manifest
    cat > "${archive_dir}/archive_manifest.txt" <<EOF
Archive Manifest
================
Timestamp: $timestamp
Date: $(date)
Total Files: $archived_count
Archive Location: $archive_dir

Directories Archived:
- analysis/output
- analysis/results
- analysis/enhanced_results
- data/output
EOF

    echo ""
    print_success "Archived $archived_count files to: $archive_dir"
}

###############################################################################
# Flush Outputs
###############################################################################

flush_outputs() {
    print_header "🧹 Flushing Outputs"

    local preserve_structure=${1:-true}
    local removed_count=0

    # Flush analysis/output
    if [ -d "$ANALYSIS_OUTPUT" ]; then
        if [ "$preserve_structure" = true ]; then
            local count=$(count_files "$ANALYSIS_OUTPUT")
            find "$ANALYSIS_OUTPUT" -type f -delete
            print_success "Flushed analysis/output/ ($count files, structure preserved)"
            removed_count=$((removed_count + count))
        else
            local count=$(count_files "$ANALYSIS_OUTPUT")
            rm -rf "$ANALYSIS_OUTPUT"
            print_success "Removed analysis/output/ ($count files)"
            removed_count=$((removed_count + count))
        fi
    fi

    # Flush analysis/results
    if [ -d "$ANALYSIS_RESULTS" ]; then
        if [ "$preserve_structure" = true ]; then
            local count=$(count_files "$ANALYSIS_RESULTS")
            find "$ANALYSIS_RESULTS" -type f -delete
            print_success "Flushed analysis/results/ ($count files, structure preserved)"
            removed_count=$((removed_count + count))
        else
            local count=$(count_files "$ANALYSIS_RESULTS")
            rm -rf "$ANALYSIS_RESULTS"
            print_success "Removed analysis/results/ ($count files)"
            removed_count=$((removed_count + count))
        fi
    fi

    # Flush analysis/enhanced_results
    if [ -d "$ENHANCED_RESULTS" ]; then
        if [ "$preserve_structure" = true ]; then
            local count=$(count_files "$ENHANCED_RESULTS")
            find "$ENHANCED_RESULTS" -type f -delete
            print_success "Flushed analysis/enhanced_results/ ($count files, structure preserved)"
            removed_count=$((removed_count + count))
        else
            local count=$(count_files "$ENHANCED_RESULTS")
            rm -rf "$ENHANCED_RESULTS"
            print_success "Removed analysis/enhanced_results/ ($count files)"
            removed_count=$((removed_count + count))
        fi
    fi

    # Flush data/output
    if [ -d "$DATA_OUTPUT" ]; then
        if [ "$preserve_structure" = true ]; then
            local count=$(count_files "$DATA_OUTPUT")
            find "$DATA_OUTPUT" -type f -delete
            print_success "Flushed data/output/ ($count files, structure preserved)"
            removed_count=$((removed_count + count))
        else
            local count=$(count_files "$DATA_OUTPUT")
            rm -rf "$DATA_OUTPUT"
            print_success "Removed data/output/ ($count files)"
            removed_count=$((removed_count + count))
        fi
    fi

    echo ""
    print_success "Flushed $removed_count output files"
}

###############################################################################
# Organize Outputs
###############################################################################

organize_outputs() {
    print_header "📁 Organizing Outputs to data/output/"

    # Create organized structure
    mkdir -p "$ORGANIZED_BASIC"
    mkdir -p "$ORGANIZED_ENHANCED"
    mkdir -p "$ORGANIZED_MLX"
    mkdir -p "$ORGANIZED_SUMMARY"
    mkdir -p "$ORGANIZED_LOGS"
    mkdir -p "$ORGANIZED_CACHE"

    local moved_count=0

    # Move from analysis/results (basic pipeline)
    if [ -d "$ANALYSIS_RESULTS" ] && [ "$(ls -A $ANALYSIS_RESULTS 2>/dev/null)" ]; then
        local count=$(count_files "$ANALYSIS_RESULTS")
        cp -r "$ANALYSIS_RESULTS"/* "$ORGANIZED_BASIC/" 2>/dev/null || true
        print_success "Moved analysis/results/ → data/output/basic/ ($count files)"
        moved_count=$((moved_count + count))
    fi

    # Move from analysis/enhanced_results
    if [ -d "$ENHANCED_RESULTS" ] && [ "$(ls -A $ENHANCED_RESULTS 2>/dev/null)" ]; then
        local count=$(count_files "$ENHANCED_RESULTS")
        cp -r "$ENHANCED_RESULTS"/* "$ORGANIZED_ENHANCED/" 2>/dev/null || true
        print_success "Moved analysis/enhanced_results/ → data/output/enhanced/ ($count files)"
        moved_count=$((moved_count + count))
    fi

    # Move from analysis/output subdirectories
    if [ -d "$ANALYSIS_OUTPUT" ]; then
        # Move basic/
        if [ -d "$ANALYSIS_OUTPUT/basic" ]; then
            local count=$(count_files "$ANALYSIS_OUTPUT/basic")
            cp -r "$ANALYSIS_OUTPUT/basic"/* "$ORGANIZED_BASIC/" 2>/dev/null || true
            print_success "Moved analysis/output/basic/ → data/output/basic/ ($count files)"
            moved_count=$((moved_count + count))
        fi

        # Move enhanced/
        if [ -d "$ANALYSIS_OUTPUT/enhanced" ]; then
            local count=$(count_files "$ANALYSIS_OUTPUT/enhanced")
            cp -r "$ANALYSIS_OUTPUT/enhanced"/* "$ORGANIZED_ENHANCED/" 2>/dev/null || true
            print_success "Moved analysis/output/enhanced/ → data/output/enhanced/ ($count files)"
            moved_count=$((moved_count + count))
        fi

        # Move mlx/
        if [ -d "$ANALYSIS_OUTPUT/mlx" ]; then
            local count=$(count_files "$ANALYSIS_OUTPUT/mlx")
            cp -r "$ANALYSIS_OUTPUT/mlx"/* "$ORGANIZED_MLX/" 2>/dev/null || true
            print_success "Moved analysis/output/mlx/ → data/output/mlx/ ($count files)"
            moved_count=$((moved_count + count))
        fi

        # Move SUMMARY/
        if [ -d "$ANALYSIS_OUTPUT/SUMMARY" ]; then
            local count=$(count_files "$ANALYSIS_OUTPUT/SUMMARY")
            cp -r "$ANALYSIS_OUTPUT/SUMMARY"/* "$ORGANIZED_SUMMARY/" 2>/dev/null || true
            print_success "Moved analysis/output/SUMMARY/ → data/output/summary/ ($count files)"
            moved_count=$((moved_count + count))
        fi

        # Move logs/
        if [ -d "$ANALYSIS_OUTPUT/logs" ]; then
            local count=$(count_files "$ANALYSIS_OUTPUT/logs")
            cp -r "$ANALYSIS_OUTPUT/logs"/* "$ORGANIZED_LOGS/" 2>/dev/null || true
            print_success "Moved analysis/output/logs/ → data/output/logs/ ($count files)"
            moved_count=$((moved_count + count))
        fi

        # Move cache/
        if [ -d "$ANALYSIS_OUTPUT/cache" ]; then
            local count=$(count_files "$ANALYSIS_OUTPUT/cache")
            cp -r "$ANALYSIS_OUTPUT/cache"/* "$ORGANIZED_CACHE/" 2>/dev/null || true
            print_success "Moved analysis/output/cache/ → data/output/cache/ ($count files)"
            moved_count=$((moved_count + count))
        fi
    fi

    echo ""
    print_success "Organized $moved_count files into data/output/"
    echo ""
    echo "New structure:"
    echo "  basic/      : $(count_files "$ORGANIZED_BASIC") files → $ORGANIZED_BASIC"
    echo "  enhanced/   : $(count_files "$ORGANIZED_ENHANCED") files → $ORGANIZED_ENHANCED"
    echo "  mlx/        : $(count_files "$ORGANIZED_MLX") files → $ORGANIZED_MLX"
    echo "  summary/    : $(count_files "$ORGANIZED_SUMMARY") files → $ORGANIZED_SUMMARY"
    echo "  logs/       : $(count_files "$ORGANIZED_LOGS") files → $ORGANIZED_LOGS"
    echo "  cache/      : $(count_files "$ORGANIZED_CACHE") files → $ORGANIZED_CACHE"
}

###############################################################################
# Prepare Clean State
###############################################################################

prepare_clean_state() {
    print_header "🔧 Preparing Clean State"

    # Ensure data directories exist
    mkdir -p "${PROJECT_ROOT}/data/input"
    mkdir -p "${PROJECT_ROOT}/data/output"
    mkdir -p "${PROJECT_ROOT}/data/archive"

    # Create organized output subdirs
    mkdir -p "$ORGANIZED_BASIC"
    mkdir -p "$ORGANIZED_ENHANCED"
    mkdir -p "$ORGANIZED_MLX"
    mkdir -p "$ORGANIZED_SUMMARY"
    mkdir -p "$ORGANIZED_LOGS"
    mkdir -p "$ORGANIZED_CACHE"

    print_success "Directory structure ready"
    echo ""
    echo "  data/input/   → Input data files"
    echo "  data/output/  → Analysis results"
    echo "  data/archive/ → Archived outputs"
}

###############################################################################
# Main Script
###############################################################################

# Parse arguments
DO_FLUSH=false
DO_ARCHIVE=false
DO_ORGANIZE=false
DO_ALL=false
DO_STATUS=false
REMOVE_STRUCTURE=false

if [ $# -eq 0 ]; then
    show_status
    echo ""
    print_info "Use --help to see available operations"
    exit 0
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        --flush)
            DO_FLUSH=true
            shift
            ;;
        --archive)
            DO_ARCHIVE=true
            shift
            ;;
        --organize)
            DO_ORGANIZE=true
            shift
            ;;
        --all)
            DO_ALL=true
            shift
            ;;
        --status)
            DO_STATUS=true
            shift
            ;;
        --remove-structure)
            REMOVE_STRUCTURE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --flush              Remove all output files (preserves directory structure)"
            echo "  --archive            Archive current outputs with timestamp"
            echo "  --organize           Move outputs to organized data/output structure"
            echo "  --all                Full reset: archive, flush, and prepare clean state"
            echo "  --status             Show current output status"
            echo "  --remove-structure   When flushing, remove directories entirely (not just files)"
            echo "  --help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                   # Show status"
            echo "  $0 --flush           # Clean all outputs"
            echo "  $0 --archive         # Archive before cleaning"
            echo "  $0 --organize        # Reorganize to data/output"
            echo "  $0 --all             # Complete reset workflow"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help to see available options"
            exit 1
            ;;
    esac
done

# Execute operations
if [ "$DO_STATUS" = true ]; then
    show_status
    exit 0
fi

if [ "$DO_ALL" = true ]; then
    print_header "🔄 Full Reset Workflow"
    echo ""

    # Archive
    archive_outputs
    echo ""

    # Flush
    if [ "$REMOVE_STRUCTURE" = true ]; then
        flush_outputs false
    else
        flush_outputs true
    fi
    echo ""

    # Prepare clean state
    prepare_clean_state
    echo ""

    echo "================================================================="
    print_success "Full reset complete! Ready for fresh analysis."
    exit 0
fi

# Individual operations
if [ "$DO_ARCHIVE" = true ]; then
    archive_outputs
    echo ""
fi

if [ "$DO_ORGANIZE" = true ]; then
    organize_outputs
    echo ""
fi

if [ "$DO_FLUSH" = true ]; then
    if [ "$REMOVE_STRUCTURE" = true ]; then
        flush_outputs false
    else
        flush_outputs true
    fi
    echo ""
    prepare_clean_state
    echo ""
fi

print_success "Operations complete!"
