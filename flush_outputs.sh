#!/bin/bash

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ANALYSIS_OUTPUT="${PROJECT_ROOT}/analysis/output"
ANALYSIS_RESULTS="${PROJECT_ROOT}/analysis/results"
ENHANCED_RESULTS="${PROJECT_ROOT}/analysis/enhanced_results"
DATA_OUTPUT="${PROJECT_ROOT}/data/output"
DATA_ARCHIVE="${PROJECT_ROOT}/data/archive"

ORGANIZED_OUTPUT="${PROJECT_ROOT}/data/output"
ORGANIZED_BASIC="${ORGANIZED_OUTPUT}/basic"
ORGANIZED_ENHANCED="${ORGANIZED_OUTPUT}/enhanced"
ORGANIZED_MLX="${ORGANIZED_OUTPUT}/mlx"
ORGANIZED_SUMMARY="${ORGANIZED_OUTPUT}/summary"
ORGANIZED_LOGS="${ORGANIZED_OUTPUT}/logs"
ORGANIZED_CACHE="${ORGANIZED_OUTPUT}/cache"

print_success() {
    printf "%s\n" "$1"
}

print_error() {
    printf "%s\n" "$1" >&2
}

print_info() {
    printf "%s\n" "$1"
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

show_status() {
    print_info "Output status"

    if [ -d "$ANALYSIS_OUTPUT" ]; then
        echo "  analysis/output/: $(count_files "$ANALYSIS_OUTPUT") files ($(get_dir_size "$ANALYSIS_OUTPUT"))"
    else
        echo "  analysis/output/: missing"
    fi

    if [ -d "$ANALYSIS_RESULTS" ]; then
        echo "  analysis/results/: $(count_files "$ANALYSIS_RESULTS") files ($(get_dir_size "$ANALYSIS_RESULTS"))"
    else
        echo "  analysis/results/: missing"
    fi

    if [ -d "$ENHANCED_RESULTS" ]; then
        echo "  analysis/enhanced_results/: $(count_files "$ENHANCED_RESULTS") files ($(get_dir_size "$ENHANCED_RESULTS"))"
    else
        echo "  analysis/enhanced_results/: missing"
    fi

    if [ -d "$DATA_OUTPUT" ]; then
        echo "  data/output/: $(count_files "$DATA_OUTPUT") files ($(get_dir_size "$DATA_OUTPUT"))"
    else
        echo "  data/output/: missing"
    fi

    if [ -d "$DATA_ARCHIVE" ]; then
        local archive_count=$(find "$DATA_ARCHIVE" -maxdepth 1 -type d -name "archive_*" | wc -l | tr -d ' ')
        echo "  data/archive/: $archive_count archives"
        local latest=$(find "$DATA_ARCHIVE" -maxdepth 1 -type d -name "archive_*" | sort -r | head -n 1)
        if [ -n "$latest" ]; then
            echo "    Latest: $(basename "$latest")"
        fi
    else
        echo "  data/archive/: missing"
    fi
}

archive_outputs() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local archive_dir="${DATA_ARCHIVE}/archive_${timestamp}"
    mkdir -p "$archive_dir"
    print_info "Archiving to: $archive_dir"

    local archived_count=0

    if [ -d "$ANALYSIS_OUTPUT" ] && [ "$(ls -A $ANALYSIS_OUTPUT 2>/dev/null)" ]; then
        cp -r "$ANALYSIS_OUTPUT" "${archive_dir}/analysis_output"
        local count=$(count_files "$ANALYSIS_OUTPUT")
        print_success "Archived analysis/output/ ($count files)"
        archived_count=$((archived_count + count))
    else
        print_info "Skipping analysis/output/ (empty)"
    fi

    if [ -d "$ANALYSIS_RESULTS" ] && [ "$(ls -A $ANALYSIS_RESULTS 2>/dev/null)" ]; then
        cp -r "$ANALYSIS_RESULTS" "${archive_dir}/analysis_results"
        local count=$(count_files "$ANALYSIS_RESULTS")
        print_success "Archived analysis/results/ ($count files)"
        archived_count=$((archived_count + count))
    else
        print_info "Skipping analysis/results/ (empty)"
    fi

    if [ -d "$ENHANCED_RESULTS" ] && [ "$(ls -A $ENHANCED_RESULTS 2>/dev/null)" ]; then
        cp -r "$ENHANCED_RESULTS" "${archive_dir}/enhanced_results"
        local count=$(count_files "$ENHANCED_RESULTS")
        print_success "Archived analysis/enhanced_results/ ($count files)"
        archived_count=$((archived_count + count))
    else
        print_info "Skipping analysis/enhanced_results/ (empty)"
    fi

    if [ -d "$DATA_OUTPUT" ] && [ "$(ls -A $DATA_OUTPUT 2>/dev/null)" ]; then
        cp -r "$DATA_OUTPUT" "${archive_dir}/data_output"
        local count=$(count_files "$DATA_OUTPUT")
        print_success "Archived data/output/ ($count files)"
        archived_count=$((archived_count + count))
    else
        print_info "Skipping data/output/ (empty)"
    fi

    cat > "${archive_dir}/manifest.txt" <<EOF
Archive: $timestamp
Date: $(date)
Files: $archived_count
Location: $archive_dir
EOF

    print_success "Archived $archived_count files"
}

flush_outputs() {
    local preserve_structure=${1:-true}
    local removed_count=0

    if [ -d "$ANALYSIS_OUTPUT" ]; then
        local count=$(count_files "$ANALYSIS_OUTPUT")
        if [ "$preserve_structure" = true ]; then
            find "$ANALYSIS_OUTPUT" -type f -delete
            print_success "Flushed analysis/output/ ($count files)"
        else
            rm -rf "$ANALYSIS_OUTPUT"
            print_success "Removed analysis/output/ ($count files)"
        fi
        removed_count=$((removed_count + count))
    else
        print_info "analysis/output/ missing"
    fi

    if [ -d "$ANALYSIS_RESULTS" ]; then
        local count=$(count_files "$ANALYSIS_RESULTS")
        if [ "$preserve_structure" = true ]; then
            find "$ANALYSIS_RESULTS" -type f -delete
            print_success "Flushed analysis/results/ ($count files)"
        else
            rm -rf "$ANALYSIS_RESULTS"
            print_success "Removed analysis/results/ ($count files)"
        fi
        removed_count=$((removed_count + count))
    else
        print_info "analysis/results/ missing"
    fi

    if [ -d "$ENHANCED_RESULTS" ]; then
        local count=$(count_files "$ENHANCED_RESULTS")
        if [ "$preserve_structure" = true ]; then
            find "$ENHANCED_RESULTS" -type f -delete
            print_success "Flushed analysis/enhanced_results/ ($count files)"
        else
            rm -rf "$ENHANCED_RESULTS"
            print_success "Removed analysis/enhanced_results/ ($count files)"
        fi
        removed_count=$((removed_count + count))
    else
        print_info "analysis/enhanced_results/ missing"
    fi

    if [ -d "$DATA_OUTPUT" ]; then
        local count=$(count_files "$DATA_OUTPUT")
        if [ "$preserve_structure" = true ]; then
            find "$DATA_OUTPUT" -type f -delete
            print_success "Flushed data/output/ ($count files)"
        else
            rm -rf "$DATA_OUTPUT"
            print_success "Removed data/output/ ($count files)"
        fi
        removed_count=$((removed_count + count))
    else
        print_info "data/output/ missing"
    fi

    print_success "Flushed $removed_count files total"
}

organize_outputs() {
    mkdir -p "$ORGANIZED_BASIC" "$ORGANIZED_ENHANCED" "$ORGANIZED_MLX" "$ORGANIZED_SUMMARY" "$ORGANIZED_LOGS" "$ORGANIZED_CACHE"
    local moved_count=0

    if [ -d "$ANALYSIS_RESULTS" ] && [ "$(ls -A $ANALYSIS_RESULTS 2>/dev/null)" ]; then
        local count=$(count_files "$ANALYSIS_RESULTS")
        cp -r "$ANALYSIS_RESULTS"/* "$ORGANIZED_BASIC/" 2>/dev/null || true
        print_success "Moved analysis/results/ ($count files)"
        moved_count=$((moved_count + count))
    else
        print_info "Skipping analysis/results/ (empty)"
    fi

    if [ -d "$ENHANCED_RESULTS" ] && [ "$(ls -A $ENHANCED_RESULTS 2>/dev/null)" ]; then
        local count=$(count_files "$ENHANCED_RESULTS")
        cp -r "$ENHANCED_RESULTS"/* "$ORGANIZED_ENHANCED/" 2>/dev/null || true
        print_success "Moved analysis/enhanced_results/ ($count files)"
        moved_count=$((moved_count + count))
    else
        print_info "Skipping analysis/enhanced_results/ (empty)"
    fi

    if [ -d "$ANALYSIS_OUTPUT" ]; then
        if [ -d "$ANALYSIS_OUTPUT/basic" ]; then
            local count=$(count_files "$ANALYSIS_OUTPUT/basic")
            cp -r "$ANALYSIS_OUTPUT/basic"/* "$ORGANIZED_BASIC/" 2>/dev/null || true
            print_success "Moved basic/ ($count files)"
            moved_count=$((moved_count + count))
        fi

        if [ -d "$ANALYSIS_OUTPUT/enhanced" ]; then
            local count=$(count_files "$ANALYSIS_OUTPUT/enhanced")
            cp -r "$ANALYSIS_OUTPUT/enhanced"/* "$ORGANIZED_ENHANCED/" 2>/dev/null || true
            print_success "Moved enhanced/ ($count files)"
            moved_count=$((moved_count + count))
        fi

        if [ -d "$ANALYSIS_OUTPUT/mlx" ]; then
            local count=$(count_files "$ANALYSIS_OUTPUT/mlx")
            cp -r "$ANALYSIS_OUTPUT/mlx"/* "$ORGANIZED_MLX/" 2>/dev/null || true
            print_success "Moved mlx/ ($count files)"
            moved_count=$((moved_count + count))
        fi

        if [ -d "$ANALYSIS_OUTPUT/SUMMARY" ]; then
            local count=$(count_files "$ANALYSIS_OUTPUT/SUMMARY")
            cp -r "$ANALYSIS_OUTPUT/SUMMARY"/* "$ORGANIZED_SUMMARY/" 2>/dev/null || true
            print_success "Moved SUMMARY/ ($count files)"
            moved_count=$((moved_count + count))
        fi

        if [ -d "$ANALYSIS_OUTPUT/logs" ]; then
            local count=$(count_files "$ANALYSIS_OUTPUT/logs")
            cp -r "$ANALYSIS_OUTPUT/logs"/* "$ORGANIZED_LOGS/" 2>/dev/null || true
            print_success "Moved logs/ ($count files)"
            moved_count=$((moved_count + count))
        fi

        if [ -d "$ANALYSIS_OUTPUT/cache" ]; then
            local count=$(count_files "$ANALYSIS_OUTPUT/cache")
            cp -r "$ANALYSIS_OUTPUT/cache"/* "$ORGANIZED_CACHE/" 2>/dev/null || true
            print_success "Moved cache/ ($count files)"
            moved_count=$((moved_count + count))
        fi
    else
        print_info "Skipping analysis/output/ (missing)"
    fi

    print_success "Organized $moved_count files"
    echo "  basic/: $(count_files "$ORGANIZED_BASIC") files"
    echo "  enhanced/: $(count_files "$ORGANIZED_ENHANCED") files"
    echo "  mlx/: $(count_files "$ORGANIZED_MLX") files"
    echo "  summary/: $(count_files "$ORGANIZED_SUMMARY") files"
    echo "  logs/: $(count_files "$ORGANIZED_LOGS") files"
    echo "  cache/: $(count_files "$ORGANIZED_CACHE") files"
}

prepare_clean_state() {
    mkdir -p "${PROJECT_ROOT}/data/input"
    mkdir -p "${PROJECT_ROOT}/data/output"
    mkdir -p "${PROJECT_ROOT}/data/archive"
    mkdir -p "$ORGANIZED_BASIC" "$ORGANIZED_ENHANCED" "$ORGANIZED_MLX" "$ORGANIZED_SUMMARY" "$ORGANIZED_LOGS" "$ORGANIZED_CACHE"
    print_success "Directory structure ready"
}

DO_FLUSH=false
DO_ARCHIVE=false
DO_ORGANIZE=false
DO_ALL=false
DO_STATUS=false
REMOVE_STRUCTURE=false

if [ $# -eq 0 ]; then
    show_status
    print_info "Use --help for options"
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
            echo "  --flush         Remove output files"
            echo "  --archive       Archive outputs with timestamp"
            echo "  --organize      Move outputs to data/output"
            echo "  --all           Archive, flush, prepare clean state"
            echo "  --status        Show output status"
            echo "  --remove-structure  Remove directories (not just files)"
            echo "  --help          Show help"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help"
            exit 1
            ;;
    esac
done

if [ "$DO_STATUS" = true ]; then
    show_status
    exit 0
fi

if [ "$DO_ALL" = true ]; then
    archive_outputs
    if [ "$REMOVE_STRUCTURE" = true ]; then
        flush_outputs false
    else
        flush_outputs true
    fi
    prepare_clean_state
    print_success "Full reset complete"
    exit 0
fi

if [ "$DO_ARCHIVE" = true ]; then
    archive_outputs
fi

if [ "$DO_ORGANIZE" = true ]; then
    organize_outputs
fi

if [ "$DO_FLUSH" = true ]; then
    if [ "$REMOVE_STRUCTURE" = true ]; then
        flush_outputs false
    else
        flush_outputs true
    fi
    prepare_clean_state
fi

print_success "Operations complete"
