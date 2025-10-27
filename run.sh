#!/bin/bash

# combined url analysis runner
# bundles pipelines, validation, outputs, and summary

set -e  # exit on error

# color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # no color

# get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# section: configuration

VENV_DIR="venv"
DEFAULT_INPUT="Site.jsonl"
DEFAULT_OUTPUT="data/output"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# section: helpers

print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}➜ $1${NC}"
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

# section: environment setup

check_system_dependencies() {
    print_info "Checking system dependencies..."

    # check for homebrew
    if ! command -v brew &> /dev/null; then
        print_error "Homebrew not found. Please install from https://brew.sh"
        exit 1
    fi

    # check for PostgreSQL (needed for psycopg2)
    if ! command -v pg_config &> /dev/null; then
        print_info "PostgreSQL not found. Installing via Homebrew..."
        brew install postgresql@16

        # add postgresql to path for current session
        export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"

        # add to zshrc if not already there
        if ! grep -q 'postgresql@16/bin' ~/.zshrc 2>/dev/null; then
            echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
        fi

        print_success "PostgreSQL installed"
    else
        print_success "PostgreSQL already installed"
    fi

    # ensure pg_config is in PATH (for keg-only postgresql)
    if [ -f "/opt/homebrew/opt/postgresql@16/bin/pg_config" ]; then
        export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
    fi
}

setup_environment() {
    print_info "Setting up environment..."

    # check and install system dependencies first
    check_system_dependencies

    # check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi

    # activate virtual environment
    source "$VENV_DIR/bin/activate"

    # install or upgrade dependencies
    print_info "Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt

    print_success "Environment ready"
}

prepare_output_structure() {
    local root_dir="$1"

    mkdir -p "$root_dir"/{basic,enhanced,mlx,SUMMARY,logs,cache}
    touch "$root_dir"/{basic,enhanced,mlx,SUMMARY,logs,cache}/.gitkeep 2>/dev/null || true
}

# section: data validation

validate_data() {
    local input_file="$1"

    print_header "DATA QUALITY VALIDATION"

    if [ ! -f "$input_file" ]; then
        print_error "Input file not found: $input_file"
        exit 1
    fi

    print_info "Validating: $input_file"

    # run data validator
    python3 analysis/data_validator.py "$input_file"

    if [ $? -eq 0 ]; then
        print_success "Data validation passed"
        return 0
    else
        print_error "Data validation failed"
        return 1
    fi
}

# section: analysis execution

run_basic_analysis() {
    local input_file="$1"
    local output_dir="$2/basic"

    print_header "BASIC ANALYSIS"

    mkdir -p "$output_dir"

    print_info "Running basic statistical and network analysis..."
    python3 analysis/pipeline/master_pipeline.py "$input_file" "$output_dir"

    if [ $? -eq 0 ]; then
        print_success "Basic analysis completed: $output_dir/"
        return 0
    else
        print_error "Basic analysis failed"
        return 1
    fi
}

run_enhanced_analysis() {
    local input_file="$1"
    local output_dir="$2/enhanced"

    print_header "ENHANCED ANALYSIS"

    mkdir -p "$output_dir"

    print_info "Running enhanced analysis with URL parsing and subdomain detection..."
    python3 analysis/pipeline/enhanced_pipeline.py "$input_file" "$output_dir"

    if [ $? -eq 0 ]; then
        print_success "Enhanced analysis completed: $output_dir/"
        return 0
    else
        print_error "Enhanced analysis failed"
        return 1
    fi
}

run_mlx_analysis() {
    local input_file="$1"
    local output_dir="$2/mlx"

    print_header "MLX-POWERED ANALYSIS"

    mkdir -p "$output_dir"

    print_info "Running MLX analysis with embeddings, batching, and ML pattern detection..."
    python3 analysis/pipeline/mlx_enhanced_pipeline.py "$input_file" "$output_dir"

    if [ $? -eq 0 ]; then
        print_success "MLX analysis completed: $output_dir/"
        return 0
    else
        print_error "MLX analysis failed"
        return 1
    fi
}

# section: summary generation

generate_summary() {
    local output_dir="$1"

    print_header "GENERATING COMPREHENSIVE SUMMARY"

    print_info "Aggregating results from all analysis types..."
    python3 analysis/summary_aggregator.py "$output_dir" --print

    if [ $? -eq 0 ]; then
        print_success "Summary report generated: $output_dir/SUMMARY/"
        return 0
    else
        print_error "Summary generation failed"
        return 1
    fi
}

# section: cleanup and organization

flush_results() {
    local do_archive=false
    local do_clean=false

    # parse flush options
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

    print_header "FLUSHING ANALYSIS RESULTS"

    # if clean mode, use flush_outputs.sh --all
    if [ "$do_clean" = true ]; then
        print_info "Running complete clean workflow (archive + flush + organize)..."
        bash flush_outputs.sh --all
        return $?
    fi

    # if archive mode, use flush_outputs.sh with archive
    if [ "$do_archive" = true ]; then
        print_info "Archiving outputs before flushing..."
        bash flush_outputs.sh --archive --flush
        return $?
    fi

    # interactive mode - ask user
    read -p "Are you sure you want to delete all analysis results? (y/N) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Do you want to archive outputs first? (y/N) "
        read -p "" -n 1 -r
        echo

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            bash flush_outputs.sh --archive --flush
        else
            bash flush_outputs.sh --flush
        fi

        print_success "Flush complete"
    else
        print_info "Flush cancelled"
    fi
}

organize_outputs() {
    print_header "ORGANIZING OUTPUTS"

    print_info "Moving outputs to data/output structure..."
    bash flush_outputs.sh --organize

    if [ $? -eq 0 ]; then
        print_success "Outputs organized successfully"
        return 0
    else
        print_error "Output organization failed"
        return 1
    fi
}

# section: main execution

main() {
    local command="${1:-analyze}"
    shift || true

    # parse arguments
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

    # execute command
    case $command in
        analyze)
            print_header "URL ANALYSIS SYSTEM"
            echo "Input: $input_file"
            echo "Output: $output_dir"
            echo "Type: $analysis_type"
            echo ""

            # setup environment
            setup_environment

            # ensure output layout is ready
            prepare_output_structure "$output_dir"

            # validate data unless skipped
            if [ "$skip_validation" = false ]; then
                validate_data "$input_file" || exit 1
            fi

            # run analyses based on type
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
                    print_error "Unknown analysis type: $analysis_type"
                    exit 1
                    ;;
            esac

            # generate summary if running all analyses
            if [ "$analysis_type" = "all" ]; then
                generate_summary "$output_dir"
            fi

            # show results location
            print_header "ANALYSIS COMPLETE"
            echo "Results saved to: $output_dir/"
            echo ""
            echo "Generated directories:"
            [ -d "$output_dir/basic" ] && echo "  • basic/     - Statistical and network analysis"
            [ -d "$output_dir/enhanced" ] && echo "  • enhanced/  - URL parsing and subdomain analysis"
            [ -d "$output_dir/mlx" ] && echo "  • mlx/       - ML-powered pattern detection"
            [ -d "$output_dir/SUMMARY" ] && echo "  • SUMMARY/   - Comprehensive cross-analysis report"
            echo ""
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
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# run main function with all arguments
main "$@"
