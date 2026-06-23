#!/bin/bash
# ZoATS Installation Script
# Requires: Zo Computer with N5OS Ode v2.0+ installed
# Usage: bash install.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

CANONICAL_INSTALL_DIR="/home/workspace/ZoATS"
INSTALL_DIR="${INSTALL_DIR:-${ZOATS_HOME:-$CANONICAL_INSTALL_DIR}}"
N5_DIR="/home/workspace/N5"
SKILLS_DIR="/home/workspace/Skills"
BACKUP_DIR="/home/workspace/.n5-ats-backups"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ZoATS Installation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================
# PREFLIGHT GATE: Ode v2.0+ (HARD — no bypass)
# ============================================
# ZoATS requires N5OS (Ode v2.0+) for its operational substrate:
# scripts, config, Pulse build orchestration, and protection system.
# There is NO --skip-preflight flag. This gate is mandatory.

preflight_fail=0
failed_checks=()

log_info "Preflight check: verifying N5OS Ode v2.0+ installation..."
echo ""

# Hard gates — abort if ANY missing
HARD_CHECKS=(
    "$N5_DIR/scripts/session_state_manager.py:Session state manager"
    "$N5_DIR/scripts/n5_load_context.py:Context loader"
    "$N5_DIR/scripts/n5_protect.py:File protection system"
    "$N5_DIR/scripts/n5_safety.py:Safety validator"
    "$N5_DIR/scripts/build_orchestrator_v2.py:Build orchestrator (Ode v2 check)"
    "$N5_DIR/config:N5 config directory"
    "$N5_DIR/prefs/context_manifest.yaml:Context manifest"
    "$N5_DIR/prefs/prefs.md:Core preferences"
    "$SKILLS_DIR/pulse/SKILL.md:Pulse build orchestration skill"
)

for check in "${HARD_CHECKS[@]}"; do
    path="${check%%:*}"
    label="${check##*:}"
    if [ -e "$path" ]; then
        log_success "$label"
    else
        log_error "$label — missing: $path"
        failed_checks+=("$label ($path)")
        preflight_fail=1
    fi
done

if [ "$preflight_fail" -eq 1 ]; then
    echo ""
    log_error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_error "ZoATS requires N5OS Ode v2.0+ to be installed first."
    log_error ""
    log_error "Install Ode:"
log_error "  git clone https://github.com/thevibethinker/n5os-ode.git"
    log_error "  cd n5os-ode && bash install.sh"
    log_error ""
    log_error "Or visit: https://va.zo.space/ode"
    log_error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    log_error "Failed checks (${#failed_checks[@]}):"
    for fc in "${failed_checks[@]}"; do
        log_error "  - $fc"
    done
    exit 1
fi

echo ""

# Soft gates — warn but continue
SOFT_CHECKS=(
    "$N5_DIR/cognition/brain.db:Semantic memory (optional — enables enriched scoring)"
    "$N5_DIR/cognition/n5_memory_client.py:Memory client (optional — enables candidate memory)"
)

for check in "${SOFT_CHECKS[@]}"; do
    path="${check%%:*}"
    label="${check##*:}"
    if [ -e "$path" ]; then
        log_success "$label"
    else
        log_warning "$label — not found (non-critical)"
    fi
done

log_success "Preflight gate passed — Ode v2.0+ confirmed"
echo ""

# Step 1: Backup existing installation
if [ -d "$INSTALL_DIR" ]; then
    log_warning "Existing ZoATS installation found"
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    mkdir -p "$BACKUP_DIR"
    BACKUP_PATH="$BACKUP_DIR/zoats-$TIMESTAMP"
    log_info "Creating backup: $BACKUP_PATH"
    cp -r "$INSTALL_DIR" "$BACKUP_PATH"
    log_success "Backup created"
fi

# Step 2: Install ZoATS
log_info "Installing ZoATS..."

if [ -d "$INSTALL_DIR/.git" ]; then
    log_info "Updating existing repository..."
    cd "$INSTALL_DIR"
    git fetch origin --quiet
    git reset --hard origin/main
else
    log_info "Cloning repository..."
    rm -rf "$INSTALL_DIR"
    git clone https://github.com/thevibethinker/ZoATS.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

log_success "Repository installed"

# Step 3: Install Python dependencies
log_info "Installing Python dependencies..."
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    python3 -m pip install -r "$INSTALL_DIR/requirements.txt" --quiet
    log_success "Dependencies installed"
else
    log_warning "requirements.txt not found — skipping dependency install"
fi

# Step 4: Create directories
log_info "Creating runtime directories..."
mkdir -p "$INSTALL_DIR"/{jobs,inbox_drop,logs,data}
log_success "Directories created"

# Step 5: Set permissions
log_info "Setting permissions..."
chmod +x "$INSTALL_DIR"/scripts/*.py 2>/dev/null || true
chmod +x "$INSTALL_DIR"/*.sh 2>/dev/null || true
log_success "Permissions set"

# Step 6: Configuration
if [ ! -f "$INSTALL_DIR/config/settings.json" ]; then
    if [ -f "$INSTALL_DIR/config/settings.example.json" ]; then
        log_info "Creating default configuration..."
        cp "$INSTALL_DIR/config/settings.example.json" "$INSTALL_DIR/config/settings.json"
        log_success "Configuration created — edit $INSTALL_DIR/config/settings.json"
    fi
fi

# Keep runtime contract explicit for routes and shell sessions
export ZOATS_HOME="$INSTALL_DIR"

# Step 7: Verify installation
log_info "Verifying installation..."

CHECKS_PASSED=0
CHECKS_TOTAL=5

check_install_artifact() {
    local path="$1"
    local label="$2"
    if [ -e "$path" ]; then
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        log_success "$label"
    else
        log_error "Missing $label at $path"
    fi
}

check_install_artifact "$INSTALL_DIR/workers" "workers/"
check_install_artifact "$INSTALL_DIR/pipeline" "pipeline/"
check_install_artifact "$INSTALL_DIR/config/commands.jsonl" "config/commands.jsonl"
check_install_artifact "$INSTALL_DIR/requirements.txt" "requirements.txt"
check_install_artifact "$INSTALL_DIR/lib/paths.py" "lib/paths.py"

if [ $CHECKS_PASSED -eq $CHECKS_TOTAL ]; then
    log_success "Installation verified ($CHECKS_PASSED/$CHECKS_TOTAL checks passed)"
else
    log_error "Installation incomplete ($CHECKS_PASSED/$CHECKS_TOTAL checks passed)"
    exit 1
fi

# Step 8: Provision zo.space routes (job board)
if [ -n "$ZO_API_KEY" ]; then
    log_info "Provisioning job board routes on zo.space..."
    if python3 "$INSTALL_DIR/scripts/provision_space_routes.py"; then
        log_success "Job board routes provisioned"
    else
        log_warning "Route provisioning failed — run manually: python3 $INSTALL_DIR/scripts/provision_space_routes.py"
    fi
else
    log_warning "ZO_API_KEY not set — skipping job board route provisioning"
    log_info "Create a Zo access token in Settings > Advanced > Access Tokens, export it as ZO_API_KEY, then run:"
    log_info "  export ZO_API_KEY=zo_sk_... && python3 $INSTALL_DIR/scripts/provision_space_routes.py"
fi

# Step 9: Display info
CURRENT_COMMIT=$(git rev-parse --short HEAD)
CURRENT_VERSION=$(cat VERSION 2>/dev/null || echo "0.1.0")

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_success "ZoATS Installation Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Version:    $CURRENT_VERSION"
echo "  Commit:     $CURRENT_COMMIT"
echo "  Location:   $INSTALL_DIR"
echo "  N5OS:       $N5_DIR"
echo ""
echo "Next Steps:"
echo "  1. Configure: $INSTALL_DIR/config/settings.json"
echo "  2. Create a job: mkdir -p $INSTALL_DIR/jobs/my-first-job"
echo "  3. Add job-description.md, rubric.json, deal_breakers.json, metadata.json"
echo "  4. Provision template pages if needed: python3 $INSTALL_DIR/scripts/provision_space_routes.py"
echo "  5. Drop resumes into $INSTALL_DIR/inbox_drop and run the pipeline"
echo ""
log_success "Ready to hire!"
