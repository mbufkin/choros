#!/usr/bin/env python3
"""
Synthetic Rubric Validation
============================
Tests whether gemma4:26b can accurately count discrete, unambiguous
criteria in synthetic essays. If the rubric is well-designed, the
model should check exactly the right number of boxes — no bias,
no compression, no walk-down.

We control the ground truth: each essay is constructed to meet
exactly N criteria. The model's job is to count them.
"""
import json, urllib.request, time, os, re
from pathlib import Path

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://100.85.15.59:11434")
MODEL = "gemma4:26b"
DATA_DIR = Path(__file__).resolve().parent / "guardrails"
OUTPUT_PATH = DATA_DIR / "synthetic_rubric_results.json"

# 12 discrete, unambiguous criteria — each observable in the text
CRITERIA = [
    ("Position", "States a clear position for or against school uniforms"),
    ("Reason 1", "Gives at least one specific reason for their position"),
    ("Reason 2", "Gives a second distinct reason (different from the first)"),
    ("Example", "Provides a concrete example (names a specific situation, person, or scenario)"),
    ("Cost", "Mentions cost, money, or financial burden"),
    ("Expression", "Mentions self-expression, individuality, creativity, or identity"),
    ("Counter Notice", "Acknowledges that an opposing viewpoint exists"),
    ("Counter Reply", "Responds to or rebuts the opposing viewpoint"),
    ("Intro", "Has a recognizable introductory sentence or paragraph"),
    ("Conclusion", "Has a recognizable concluding sentence or paragraph"),
    ("Transition", "Uses at least one transition word (however, therefore, furthermore, in addition, etc.)"),
    ("Spelling", "First three sentences contain no spelling errors"),
]

RUBRIC_FORM = """## Essay Rubric — Uniform Debate

Read the essay below. For each criterion, mark [x] if clearly met, [ ] if not.
Be strict — only check if EXPLICITLY demonstrated in the text.

{criteria_list}

STUDENT ESSAY:
{essay}
"""

# Synthetic essays — each constructed to meet exactly N criteria
SYNTHETIC_ESSAYS = [
    {
        "id": "synth-01",
        "expected_checks": 1,
        "text": "i think they should not.",
        "meets": ["Position"]
    },
    {
        "id": "synth-03", 
        "expected_checks": 3,
        "text": "Students should not have to wear uniforms. My first reason is that uniforms are uncomfortable and restrict movement during the school day. In conclusion, I believe schools should let students wear their own clothes.",
        "meets": ["Position", "Reason 1", "Conclusion"]
    },
    {
        "id": "synth-05",
        "expected_checks": 7,
        "text": "I believe students should not be required to wear school uniforms. First, uniforms limit students' ability to express their individuality and personal style. Second, purchasing specialized uniform clothing places an unnecessary financial burden on families who may already struggle with school supply costs. For example, my cousin's family had to spend over $200 just on uniform polo shirts and khaki pants before school even started. In conclusion, the costs to both self-expression and family budgets make mandatory uniforms a poor policy choice.",
        "meets": ["Position", "Reason 1", "Reason 2", "Example", "Cost", "Expression", "Conclusion"]
    },
    {
        "id": "synth-07",
        "expected_checks": 7,
        "text": "I believe students should not be required to wear school uniforms for several important reasons. First, uniforms restrict students' self-expression and individuality during a critical period of identity development. For example, being able to wear a favorite band t-shirt or choose colors that reflect your mood can help teenagers explore who they are. Second, the cost of uniforms creates a significant financial burden. A typical school uniform package including shirts, pants, and a blazer can cost over $150 per child — money that could instead go toward books, technology, or educational activities. Some people argue that uniforms reduce bullying based on clothing brands. However, this approach teaches students to hide differences rather than learn to respect them — a troubling lesson for a diverse society. Therefore, I conclude that the harm to self-expression and family finances outweighs any potential benefits of mandatory uniforms.",
        "meets": ["Position", "Reason 1", "Reason 2", "Example", "Cost", "Expression", "Counter Notice", "Counter Reply", "Intro", "Conclusion", "Transition"]
    },
    {
        "id": "synth-11",
        "expected_checks": 11,
        "text": "The question of mandatory school uniforms touches on fundamental tensions between institutional order and individual liberty. I contend that schools should not require uniforms, and I will support this position with evidence from economics, psychology, and educational research. First, the financial argument: a study by the National Center for Education Statistics found that the average family spends $249 per child annually on school uniforms alone — money that could fund tutoring, enrichment programs, or college savings. Second, uniforms suppress self-expression and identity development. Adolescent psychology research by Dr. Sarah Thompson at Stanford University demonstrates that clothing choice is one of the few safe avenues teenagers have for exploring their emerging identities in a structured environment. For example, a student who wears a science-themed t-shirt signals intellectual curiosity; a student in athletic wear signals team affiliation — both forms of healthy identity expression that uniforms erase. Some administrators argue that uniforms improve discipline and reduce bullying. However, a comprehensive Department of Education study found no statistically significant difference in disciplinary incidents between uniform and non-uniform schools after controlling for socioeconomic factors. Furthermore, teaching students to eliminate visible differences rather than navigate them fails to prepare young people for a diverse democratic society. In conclusion, mandatory uniform policies impose regressive financial costs and suppress healthy identity development while failing to deliver the promised behavioral benefits. Schools should instead implement flexible dress codes that prohibit genuinely disruptive attire while preserving students' freedom of expression.",
        "meets": ["Position", "Reason 1", "Reason 2", "Example", "Cost", "Expression", "Counter Notice", "Counter Reply", "Intro", "Conclusion", "Transition"]
    },
]

def build_criteria_list():
    lines = []
    for i, (name, desc) in enumerate(CRITERIA, 1):
        lines.append(f"- [ ] {i}. **{name}**: {desc}")
    return "\n".join(lines)

def call_ollama(prompt):
    payload = json.dumps({
        "model": MODEL, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.1, "num_predict": 2048}
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate", data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read()).get("response", "")

def parse_form(filled_form):
    """Count checked boxes."""
    checked = len(re.findall(r'-\s*\[[xX]\]', filled_form))
    unchecked = len(re.findall(r'-\s*\[\s\]', filled_form))
    return {"checked": checked, "unchecked": unchecked, "total": checked + unchecked}

def main():
    criteria_text = build_criteria_list()
    results = []
    total_err = 0
    
    for essay in SYNTHETIC_ESSAYS:
        expected = essay["expected_checks"]
        
        print(f"[{essay['id']}] expected {expected} checks...", end=" ", flush=True)
        t0 = time.time()
        
        prompt = RUBRIC_FORM.format(criteria_list=criteria_text, essay=essay["text"])
        filled = call_ollama(prompt)
        parsed = parse_form(filled)
        
        elapsed = time.time() - t0
        error = parsed["checked"] - expected
        total_err += abs(error)
        status = "✓" if error == 0 else f"{'+' if error > 0 else ''}{error}"
        
        print(f"got {parsed['checked']}/{parsed['total']} ({status}) [{elapsed:.0f}s]")
        
        results.append({
            "id": essay["id"],
            "expected": expected,
            "checked": parsed["checked"],
            "error": error,
            "elapsed_s": round(elapsed, 1)
        })
    
    # Summary
    print(f"\n{'='*60}")
    print("SYNTHETIC RUBRIC VALIDATION")
    print(f"{'='*60}")
    print(f"{'Essay':<12} {'Expected':>8} {'Got':>6} {'Error':>8}")
    print(f"{'-'*12} {'-'*8} {'-'*6} {'-'*8}")
    
    perfect = 0
    for r in results:
        marker = " ✓" if r["error"] == 0 else ""
        print(f"{r['id']:<12} {r['expected']:>8} {r['checked']:>6} {r['error']:+>5}{marker}")
        if r["error"] == 0:
            perfect += 1
    
    mae = total_err / len(results)
    print(f"\nPerfect: {perfect}/{len(results)} | MAE: {mae:.1f} checks")
    
    output = {
        "model": MODEL,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": {"perfect": perfect, "total": len(results), "mae": mae},
        "results": results
    }
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"Saved: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
