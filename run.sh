#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="venv"
DEFAULT_INPUT="data/input/site_02.jsonl"
DEFAULT_OUTPUT="data/output"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

say() {
    printf "%s\n" "$1"
}

tell_err() {
    printf "%s\n" "$1" >&2
}

show_usage() {
    cat << EOF
Usage: ./run.sh [COMMAND] [OPTIONS]

COMMANDS:
  analyze       Run complete analysis pipeline (default)
  validate      Validate data quality before analysis
  flush         Remove all analysis results and cached data (uses flush_outputs.sh)
  organize      Move outputs to organized data/output structure
  help          Show this help message

OPTIONS:
  -i, --input FILE       Input JSONL file (default: Site.jsonl)
  -o, --output DIR       Output directory (default: data/output)
  -t, --type TYPE        Analysis type: basic|enhanced|all (default: all)
  --skip-validation      Skip data quality validation
  --recursive            Run analysis recursively on generated insights
  --archive              Archive outputs before flushing
  --clean                Complete clean: archive, flush, organize

EXAMPLES:
  ./run.sh analyze                           # Run all analyses on Site.jsonl
  ./run.sh analyze -i data.jsonl             # Analyze custom input file
  ./run.sh analyze -t basic                  # Run only basic analysis
  ./run.sh validate -i data.jsonl            # Validate data quality
  ./run.sh flush                             # Clear all results (with prompt)
  ./run.sh flush --archive                   # Archive before flushing
  ./run.sh organize                          # Reorganize outputs to data folder
  ./run.sh flush --clean                     # Complete clean state

EOF
}

check_system_dependencies() {
    say "Checking dependencies..."

    if command -v brew >/dev/null 2>&1; then
        say "Homebrew available."
    else
        tell_err "Homebrew missing. Install it from https://brew.sh."
        exit 1
    fi

    if command -v pg_config >/dev/null 2>&1; then
        say "PostgreSQL client available."
    else
        say "Installing postgresql@16 with Homebrew..."
        if brew install postgresql@16; then
            say "PostgreSQL installed."
        else
            tell_err "PostgreSQL install failed."
            exit 1
        fi
    fi

    if [ -d "/opt/homebrew/opt/postgresql@16/bin" ]; then
        export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
        if ! grep -q 'postgresql@16/bin' ~/.zshrc 2>/dev/null; then
            echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
        else
            :
        fi
    else
        tell_err "Expected PostgreSQL binaries at /opt/homebrew/opt/postgresql@16/bin."
    fi
}

setup_environment() {
    say "Setting up environment..."
    check_system_dependencies

    if [ ! -d "$VENV_DIR" ]; then
        say "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    else
        :
    fi

    source "$VENV_DIR/bin/activate"
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    say "Environment ready."
}

prepare_output_structure() {
    local root_dir="$1"
    mkdir -p "$root_dir"/{basic,enhanced,mlx,SUMMARY,logs,cache}
    touch "$root_dir"/{basic,enhanced,mlx,SUMMARY,logs,cache}/.gitkeep 2>/dev/null || true
}

validate_data() {
    local input_file="$1"

    if [ ! -f "$input_file" ]; then
        tell_err "Input file not found: $input_file"
        exit 1
    else
        if python3 analysis/data_validator.py "$input_file"; then
            say "Validation finished for $input_file."
        else
            tell_err "Validation failed for $input_file."
            return 1
        fi
    fi
    return 0
}

run_analysis() {
    local input_file="$1"
    local output_dir="$2"
    local analysis_type="$3"

    mkdir -p "$output_dir"
    say "Running pipeline: $analysis_type"
    if python3 analysis/pipeline/master_pipeline.py "$input_file" "$output_dir" "global.yml"; then
        say "Analysis complete: $output_dir/"
        return 0
    else
        tell_err "Analysis failed."
        return 1
    fi
}

run_basic_analysis() {
    run_analysis "$1" "$2/basic" "basic"
}

run_enhanced_analysis() {
    run_analysis "$1" "$2/enhanced" "enhanced"
}

run_mlx_analysis() {
    run_analysis "$1" "$2/mlx" "mlx"
}

generate_summary() {
    local output_dir="$1"
    say "Generating summary..."
    if python3 analysis/summary_aggregator.py "$output_dir"; then
        say "Summary saved to $output_dir/SUMMARY/"
        return 0
    else
        tell_err "Summary generation failed."
        return 1
    fi
}

flush_results() {
    local do_archive=false
    local do_clean=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --archive)
                do_archive=true
                shift
                ;;
            --clean)
                do_clean=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    if [ "$do_clean" = true ]; then
        if bash flush_outputs.sh --all; then
            say "Flush complete."
            return 0
        else
            tell_err "Flush failed."
            return 1
        fi
    elif [ "$do_archive" = true ]; then
        if bash flush_outputs.sh --archive --flush; then
            say "Flush complete."
            return 0
        else
            tell_err "Flush failed."
            return 1
        fi
    else
        read -p "Delete all analysis results? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -p "Archive first? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                if bash flush_outputs.sh --archive --flush; then
                    say "Flush complete."
                else
                    tell_err "Flush failed."
                fi
            else
                if bash flush_outputs.sh --flush; then
                    say "Flush complete."
                else
                    tell_err "Flush failed."
                fi
            fi
        else
            say "Cancelled."
        fi
    fi
}

organize_outputs() {
    say "Organizing outputs..."
    if bash flush_outputs.sh --organize; then
        say "Outputs organized."
        return 0
    else
        tell_err "Organization failed."
        return 1
    fi
}

main() {
    local command="${1:-analyze}"
    shift || true

    local input_file="$DEFAULT_INPUT"
    local output_dir="$DEFAULT_OUTPUT"
    local analysis_type="all"
    local skip_validation=false
    local recursive=false
    local do_archive=false
    local do_clean=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--input)
                input_file="$2"
                shift 2
                ;;
            -o|--output)
                output_dir="$2"
                shift 2
                ;;
            -t|--type)
                analysis_type="$2"
                shift 2
                ;;
            --skip-validation)
                skip_validation=true
                shift
                ;;
            --recursive)
                recursive=true
                shift
                ;;
            --archive)
                do_archive=true
                shift
                ;;
            --clean)
                do_clean=true
                shift
                ;;
            *)
                echo "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    case $command in
        analyze)
            say "Input: $input_file | Output: $output_dir | Type: $analysis_type"
            setup_environment
            prepare_output_structure "$output_dir"

            if [ "$skip_validation" = false ]; then
                validate_data "$input_file" || exit 1
            else
                say "Skipping validation."
            fi

            case $analysis_type in
                basic)
                    run_basic_analysis "$input_file" "$output_dir"
                    ;;
                enhanced)
                    run_enhanced_analysis "$input_file" "$output_dir"
                    ;;
                mlx)
                    run_mlx_analysis "$input_file" "$output_dir"
                    ;;
                all)
                    run_basic_analysis "$input_file" "$output_dir"
                    run_enhanced_analysis "$input_file" "$output_dir"
                    run_mlx_analysis "$input_file" "$output_dir"
                    ;;
                *)
                    tell_err "Unknown type: $analysis_type"
                    exit 1
                    ;;
            esac

            if [ "$analysis_type" = "all" ]; then
                generate_summary "$output_dir"
            else
                :
            fi

            say "Analysis complete."
            echo "Results: $output_dir/"
            if [ -d "$output_dir/basic" ]; then
                echo "  basic/"
            else
                :
            fi
            if [ -d "$output_dir/enhanced" ]; then
                echo "  enhanced/"
            else
                :
            fi
            if [ -d "$output_dir/mlx" ]; then
                echo "  mlx/"
            else
                :
            fi
            if [ -d "$output_dir/SUMMARY" ]; then
                echo "  SUMMARY/"
            else
                :
            fi
            ;;

        validate)
            setup_environment
            validate_data "$input_file"
            ;;

        flush)
            if [ "$do_clean" = true ]; then
                flush_results --clean
            elif [ "$do_archive" = true ]; then
                flush_results --archive
            else
                flush_results
            fi
            ;;

        organize)
            organize_outputs
            ;;

        help|--help|-h)
            show_usage
            ;;

        *)
            tell_err "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
