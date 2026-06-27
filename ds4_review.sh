#!/bin/bash
# Feed choros core source files to DS4 V4 Flash on G10 for improvement review
# Usage: bash ds4_review.sh

DS4_URL="http://100.85.15.59:8082/v1/completions"
CHOROS_DIR="/home/mbufkin/choros"
OUTPUT_DIR="/tmp/ds4_choros_review"
mkdir -p "$OUTPUT_DIR"

# Define the core crystallization-phase files to review
FILES=(
  "$CHOROS_DIR/server.py"
  "$CHOROS_DIR/workspace.py"
  "$CHOROS_DIR/crystallize.py"
  "$CHOROS_DIR/crystallize_multipass.py"
  "$CHOROS_DIR/gen_lessons.py"
  "$CHOROS_DIR/PRODUCT.md"
  "$CHOROS_DIR/DESIGN.md"
  "$CHOROS_DIR/AGENTS.md"
  "$CHOROS_DIR/DECISIONS.md"
  "$CHOROS_DIR/BASELINE.md"
  "$CHOROS_DIR/MODELS.md"
  "$CHOROS_DIR/teacher.html"
  "$CHOROS_DIR/student.html"
  "$CHOROS_DIR/teacher.js"
  "$CHOROS_DIR/student.js"
  "$CHOROS_DIR/domains/algebra.py"
)

for f in "${FILES[@]}"; do
  basename=$(basename "$f")
  echo "===== REVISING: $basename ====="
  
  content=$(cat "$f")
  char_count=$(echo "$content" | wc -c)
  
  echo "  ($char_count chars)" 
  
  # Build the prompt with the file content (truncate to 14000 chars for 13 tok/s speed)
  # Actually at 13 tok/s, let's be reasonable — 5000 chars per file
  if [ "$char_count" -gt 5000 ]; then
    echo "  Truncating to 5000 chars for speed..."
    content="${content:0:5000}"
  fi
  
  prompt="You are a senior software engineer reviewing the Choros project — an AI-powered curriculum mapping and lesson generation system for schools.

FILE: $basename

\`\`\`
$content
\`\`\`

CRITICAL CONTEXT (read these constraints before making suggestions):
- Zero build step. Classic <script> tags. No npm, no bundler, no ES modules, no framework.
- Python stdlib only — zero pip packages on the server.
- The model cannot generate outside the uploaded source documents. Every lesson, question, and feedback must be grounded in the teacher's curriculum documents.
- Filesystem as database — JSON files, no SQL.
- Teacher batch jobs (crystallization, lesson generation) are async.
- Deterministic scoring is separate from LLM feedback. Right/wrong is math. \"Why\" is LLM.
- Dark theme UI — see DESIGN.md for color tokens.
- Target models: the crystallization engine runs on a Lenovo DGX Spark (GB10, unified 128GB memory, aarch64). Current primary model is DeepSeek V4 Flash at IQ2XXS (the model you are).

TASK: Review this single file thoroughly. Identify:
1. BUGS — logic errors, edge cases, security issues
2. ROBUSTNESS — missing error handling, silent failures, resource leaks
3. ARCHITECTURE — poor separation of concerns, tight coupling, future-proofing
4. PERFORMANCE — unnecessary work, blocking operations, memory issues
5. CLARITY — confusing variable names, missing comments, hard-to-follow flow
6. CONSTRAINT VIOLATIONS — anything that breaks the zero-dep / stdlib-only / filesystem-as-db rules

Be specific. Reference exact line numbers. Rate each finding HIGH/MEDIUM/LOW.
Do NOT praise. Find problems."

  # Write prompt to a temp file to avoid shell quoting issues
  echo "$prompt" > /tmp/choros_review_prompt.txt
  
  # Create the curl payload
  cat > /tmp/choros_review_payload.json << PAYLOADEOF
{
  "prompt": $(cat /tmp/choros_review_prompt.txt | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'),
  "max_tokens": 1024,
  "temperature": 0.3
}
PAYLOADEOF

  # Send to DS4
  output=$(curl -s -X POST "$DS4_URL" \
    -H "Content-Type: application/json" \
    -d @/tmp/choros_review_payload.json \
    --max-time 90 2>&1)
  
  # Extract text from response
  echo "$output" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    text = data.get('choices', [{}])[0].get('text', '')
    print(text)
except Exception as e:
    print(f'[PARSE ERROR: {e}]')
    print(sys.stdin.read()[:200])
  " > "$OUTPUT_DIR/${basename}.review.md"
  
  lines=$(wc -l < "$OUTPUT_DIR/${basename}.review.md")
  echo "  → ${lines} lines of review saved"
  
  # Brief pause between files
  sleep 2
done

echo ""
echo "===== ALL FILES REVIEWED ====="
echo "Reviews saved to: $OUTPUT_DIR"
ls -la "$OUTPUT_DIR/"
