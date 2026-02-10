#!/usr/bin/env bash
# ============================================================
# SessionEnd Hook: Auto-Doku Update
# Analysiert git diff und aktualisiert relevante Doku-Dateien.
# Wird automatisch am Ende jeder Claude Code Session ausgefuehrt.
# ============================================================

set -euo pipefail

LOG_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/hooks/session-end.log"
MAX_DIFF_LINES=3000
MAX_BUDGET="0.05"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# --- Projekt-Root ermitteln ---
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
cd "$PROJECT_DIR"

log "=== SessionEnd Hook gestartet ==="
log "Projekt: $PROJECT_DIR"

# --- Geaenderte Dateien ermitteln ---
CHANGED_FILES=$(git diff HEAD --name-only 2>/dev/null || true)

if [ -z "$CHANGED_FILES" ]; then
    log "Keine Aenderungen erkannt. Exit."
    exit 0
fi

log "Geaenderte Dateien: $(echo "$CHANGED_FILES" | wc -l | tr -d ' ')"

# --- Nur Doku-Aenderungen? → Skip (Endlosschleife vermeiden) ---
NON_DOC_FILES=$(echo "$CHANGED_FILES" | grep -v -E '(CLAUDE\.md|README\.md|WORKBENCH_CONTEXT\.md|TELEGRAM-FIRST\.md|\.log$)' || true)

if [ -z "$NON_DOC_FILES" ]; then
    log "Nur Doku-Aenderungen. Kein Update noetig. Exit."
    exit 0
fi

log "Code-Aenderungen erkannt: $(echo "$NON_DOC_FILES" | wc -l | tr -d ' ') Dateien"

# --- Relevante Doku-Dateien identifizieren ---
DOCS_TO_UPDATE=""

# Mapping: Code-Aenderung → Doku-Update
while IFS= read -r file; do
    case "$file" in
        apps/finance/src/*)
            DOCS_TO_UPDATE="$DOCS_TO_UPDATE apps/finance/CLAUDE.md apps/finance/README.md"
            ;;
        apps/tool-backend/src/*)
            DOCS_TO_UPDATE="$DOCS_TO_UPDATE apps/tool-backend/CLAUDE.md apps/tool-backend/README.md"
            ;;
        apps/tool-web/src/*)
            DOCS_TO_UPDATE="$DOCS_TO_UPDATE apps/tool-web/CLAUDE.md apps/tool-web/README.md"
            ;;
        apps/main-bot/src/*)
            DOCS_TO_UPDATE="$DOCS_TO_UPDATE apps/main-bot/CLAUDE.md apps/main-bot/README.md docs/TELEGRAM-FIRST.md"
            ;;
        apps/guardian-bot/src/*)
            DOCS_TO_UPDATE="$DOCS_TO_UPDATE apps/guardian-bot/CLAUDE.md apps/guardian-bot/README.md"
            ;;
        apps/workbench-bot/src/*)
            DOCS_TO_UPDATE="$DOCS_TO_UPDATE apps/workbench-bot/CLAUDE.md apps/workbench-bot/README.md"
            ;;
        apps/ai-proxy/*)
            DOCS_TO_UPDATE="$DOCS_TO_UPDATE apps/ai-proxy/CLAUDE.md apps/ai-proxy/README.md"
            ;;
        packages/*)
            DOCS_TO_UPDATE="$DOCS_TO_UPDATE CLAUDE.md"
            ;;
        infra/*)
            DOCS_TO_UPDATE="$DOCS_TO_UPDATE .claude/WORKBENCH_CONTEXT.md"
            ;;
        apps/*/Dockerfile)
            DOCS_TO_UPDATE="$DOCS_TO_UPDATE .claude/WORKBENCH_CONTEXT.md"
            ;;
    esac
done <<< "$NON_DOC_FILES"

# Duplikate entfernen
DOCS_TO_UPDATE=$(echo "$DOCS_TO_UPDATE" | tr ' ' '\n' | sort -u | grep -v '^$' || true)

if [ -z "$DOCS_TO_UPDATE" ]; then
    log "Keine relevanten Doku-Dateien zum Aktualisieren. Exit."
    exit 0
fi

log "Doku-Dateien zum Aktualisieren: $DOCS_TO_UPDATE"

# --- Diff holen (begrenzt) ---
DIFF=$(git diff HEAD 2>/dev/null | head -n "$MAX_DIFF_LINES")
DIFF_LINES=$(echo "$DIFF" | wc -l | tr -d ' ')
log "Diff: $DIFF_LINES Zeilen (max $MAX_DIFF_LINES)"

# --- Bestehende Doku-Inhalte sammeln ---
EXISTING_DOCS=""
for doc_file in $DOCS_TO_UPDATE; do
    if [ -f "$doc_file" ]; then
        EXISTING_DOCS="$EXISTING_DOCS
--- EXISTING FILE: $doc_file ---
$(cat "$doc_file")
--- END FILE ---"
    else
        EXISTING_DOCS="$EXISTING_DOCS
--- EXISTING FILE: $doc_file ---
(Datei existiert noch nicht)
--- END FILE ---"
    fi
done

# --- Claude aufrufen ---
PROMPT="Du bist ein Dokumentations-Updater fuer das Tobys-Tool Monorepo.

Analysiere den folgenden Git-Diff und aktualisiere die relevanten Dokumentationsdateien.

REGELN:
- Aktualisiere NUR Abschnitte die von den Aenderungen betroffen sind
- Behalte die bestehende Struktur und Formatierung bei
- Schreibe auf Deutsch (technische Begriffe auf Englisch)
- Sei praezise und knapp
- Fuege keine neuen Abschnitte hinzu die nicht durch den Diff begruendet sind
- Wenn eine Datei nicht existiert, erstelle eine minimale Version

OUTPUT-FORMAT (EXAKT so):
Fuer jede aktualisierte Datei:
--- FILE: pfad/zur/datei ---
(kompletter Dateiinhalt)
--- END FILE ---

Wenn keine Aenderung noetig ist, antworte mit: KEINE_AENDERUNG

GEAENDERTE DATEIEN:
$CHANGED_FILES

GIT DIFF:
$DIFF

BESTEHENDE DOKUMENTATION:
$EXISTING_DOCS"

log "Rufe Claude auf (model: sonnet, budget: $MAX_BUDGET USD)..."

RESULT=$(echo "$PROMPT" | claude -p --model sonnet --max-budget-usd "$MAX_BUDGET" 2>/dev/null || true)

if [ -z "$RESULT" ]; then
    log "FEHLER: Claude hat keine Antwort geliefert."
    exit 0
fi

# --- Pruefen ob Aenderungen noetig ---
if echo "$RESULT" | grep -q "KEINE_AENDERUNG"; then
    log "Claude: Keine Doku-Aenderungen noetig."
    exit 0
fi

# --- Output parsen und Dateien schreiben ---
UPDATED_COUNT=0

# Parse --- FILE: pfad --- ... --- END FILE --- Bloecke
while IFS= read -r line; do
    if [[ "$line" =~ ^---\ FILE:\ (.+)\ ---$ ]]; then
        CURRENT_FILE="${BASH_REMATCH[1]}"
        CURRENT_CONTENT=""
        COLLECTING=true
    elif [[ "$line" == "--- END FILE ---" ]] && [ "$COLLECTING" = true ]; then
        COLLECTING=false
        if [ -n "$CURRENT_FILE" ] && [ -n "$CURRENT_CONTENT" ]; then
            # Sicherstellen dass Verzeichnis existiert
            mkdir -p "$(dirname "$CURRENT_FILE")"
            # Datei schreiben (ohne fuehrende Leerzeile)
            echo "${CURRENT_CONTENT#$'\n'}" > "$CURRENT_FILE"
            git add "$CURRENT_FILE"
            UPDATED_COUNT=$((UPDATED_COUNT + 1))
            log "Aktualisiert: $CURRENT_FILE"
        fi
        CURRENT_FILE=""
        CURRENT_CONTENT=""
    elif [ "$COLLECTING" = true ]; then
        CURRENT_CONTENT="$CURRENT_CONTENT
$line"
    fi
done <<< "$RESULT"

if [ "$UPDATED_COUNT" -gt 0 ]; then
    log "Commit und Push der Doku-Updates..."
    git commit -m "docs(auto): update documentation after session

Auto-generated documentation update based on code changes.
Updated $UPDATED_COUNT file(s).

Co-Authored-By: Claude Sonnet <noreply@anthropic.com>" 2>/dev/null || true
    git push 2>/dev/null || log "WARNUNG: git push fehlgeschlagen (evtl. kein Remote oder Konflikte)"
    log "Commit + Push erfolgreich."
fi

log "=== Hook fertig: $UPDATED_COUNT Datei(en) aktualisiert ==="
log ""
