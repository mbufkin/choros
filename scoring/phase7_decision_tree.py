#!/usr/bin/env python3
"""
Phase 7v2 — Decision-Tree Scoring with Quality Gate

Refined tree adds a QUALITY gate between completeness and correctness
that catches work with major errors or superficial treatment.
"""
import requests, json, sys

URL = "http://100.85.15.59:8082/v1/completions"

TREE = {
    "questions": {
        "task_alignment": {
            "question": "Does this work make a good-faith attempt to address the assignment?",
            "instructions": "Ignore quality for now. Does the work clearly try to respond to what was asked? Look for evidence of the topic being addressed at all.",
            "yes": "completeness",
            "no": "OFF_TASK"
        },
        "completeness": {
            "question": "Is the work of sufficient length and substance to count as a complete response? Does it have multiple points, paragraphs, or steps?",
            "instructions": "This is about quantity and effort, not quality. A response with a single sentence or two is NOT complete. Look for multiple sentences, multiple paragraphs, or multiple steps that show the student put in real effort.",
            "yes": "quality_gate",
            "no": "NOVICE"
        },
        "quality_gate": {
            "question": "Does the work contain SIGNIFICANT flaws that undermine its core purpose? Significant flaws include: factual errors, off-topic paragraphs, logical contradictions, or writing so unclear the meaning is lost.",
            "instructions": "Be critical here. 'Significant' means the flaw makes the work worse than average. Surface-level spelling mistakes are NOT significant. Missing the entire point of the question IS significant. Quote the most serious flaw if one exists.",
            "yes": "flaw_type",
            "no": "correctness"
        },
        "flaw_type": {
            "question": "Are the significant flaws primarily about CONTENT (factual errors, wrong concepts, missing key ideas) rather than about FORM (organization, clarity, grammar, or presentation)?",
            "instructions": "Content flaws: wrong answers, missing critical concepts, factual inaccuracies. Form flaws: messy organization, unclear writing, grammar issues. Quote the most representative flaw.",
            "yes": "DEVELOPING",
            "no": "flaw_recoverable"
        },
        "flaw_recoverable": {
            "question": "Despite the flaws, does the work demonstrate genuine understanding of the core concepts? Could you tell the student understood even if their presentation is poor?",
            "instructions": "Look past the surface issues. Do the ideas themselves show understanding, even if expressed poorly? Quote evidence of understanding.",
            "yes": "DEVELOPING",
            "no": "NOVICE"
        },
        "correctness": {
            "question": "Is the content substantively correct and well-supported? Does it demonstrate accurate understanding without significant factual errors?",
            "instructions": "Look for evidence-based reasoning, correct use of concepts, logical arguments. Quote specific evidence of correct reasoning.",
            "yes": "clarity",
            "no": "DEVELOPING"
        },
        "clarity": {
            "question": "Is the work clearly communicated, well-organized, and easy to follow?",
            "instructions": "Assess organization, logical flow, clarity of expression. Quote evidence of good structure or confusing sections.",
            "yes": "depth",
            "no": "PROFICIENT"
        },
        "depth": {
            "question": "Does the work demonstrate insight, synthesis, or creativity that exceeds standard expectations? Does it connect ideas in ways that show deep understanding?",
            "instructions": "Look for original connections, sophisticated analysis, or creative solutions. Quote evidence of exceptional depth or surface-level treatment.",
            "yes": "ADVANCED",
            "no": "PROFICIENT"
        }
    },
    "terminals": {
        "OFF_TASK": {"level": "Off-Task", "score": 1, "description": "Does not attempt the assignment"},
        "NOVICE": {"level": "Novice", "score": 2, "description": "Insufficient effort or fundamentally wrong"},
        "DEVELOPING": {"level": "Developing", "score": 3, "description": "Shows effort but has significant issues"},
        "PROFICIENT": {"level": "Proficient", "score": 4, "description": "Meets expectations, solid work"},
        "ADVANCED": {"level": "Advanced", "score": 5, "description": "Exceeds expectations, exceptional work"}
    }
}

def ask_node(node_name, essay, history):
    node = TREE["questions"][node_name]
    
    context = ""
    if history:
        context = "Previous decisions in this evaluation:\n"
        for h in history:
            context += f"- {h['question']}\n  Answer: {h['answer']}\n  Evidence: {h['quotes'][0][:120] if h.get('quotes') else 'N/A'}\n\n"
    
    prompt = f"""You are an educational evaluator. Answer ONE yes/no question about the student work below.

{context}
Current Question: {node['question']}

{node['instructions']}

Student Work:
---
{essay}
---

Your response must be valid JSON:
{{"answer": "YES" or "NO", "quotes": ["exact verbatim passage supporting your answer"]}}

CRITICAL:
- Answer MUST be exactly "YES" or "NO" (uppercase, in quotes).
- Include at least one verbatim quote from the work.
- Be honest and critical — don't be generous just because the student tried.
- If you're uncertain, choose the MORE conservative answer."""

    payload = {"prompt": prompt, "max_tokens": 384, "temperature": 0.1}
    
    try:
        r = requests.post(URL, json=payload, timeout=120)
    except Exception as e:
        return {"answer": "NO"}, {"error": str(e)}
    
    text = r.json().get("choices", [{}])[0].get("text", "")
    usage = r.json().get("usage", {})
    
    # Parse
    try:
        import re
        match = re.search(r'\{[^}]+\}', text, re.DOTALL)
        if match:
            result = json.loads(match.group())
        else:
            result = {"answer": "NO", "quotes": [text[:200]]}
    except:
        result = {"answer": "NO", "quotes": [text[:200]]}
    
    answer = result.get("answer", "NO").upper().strip('" ')
    quotes = result.get("quotes", ["(No quote)"])
    if isinstance(quotes, str):
        quotes = [quotes]
    
    log = {
        "answer": answer,
        "quotes": quotes,
        "raw": text[:200],
        "tokens": usage.get("completion_tokens", 0),
        "speed": usage.get("completion_tokens", 0) / (r.elapsed.total_seconds() or 1)
    }
    return result, log


def grade_essay(essay):
    history = []
    current = "task_alignment"
    calls = 0
    path = []
    
    while current in TREE["questions"]:
        result, log = ask_node(current, essay, history)
        calls += 1
        
        answer = result.get("answer", "NO").upper().strip('" ')
        quotes = result.get("quotes", ["(no quote)"])
        if isinstance(quotes, str):
            quotes = [quotes]
        
        entry = {
            "node": current,
            "question": TREE["questions"][current]["question"],
            "answer": answer,
            "quotes": quotes,
            "log": log
        }
        path.append(entry)
        history.append(entry)
        
        # Navigate tree
        next_key = TREE["questions"][current].get(answer.lower(), "NOVICE")
        
        if next_key in TREE["terminals"]:
            t = TREE["terminals"][next_key]
            path.append({"final": True, "key": next_key, "level": t["level"], "score": t["score"]})
            return {"path": path, "level": t["level"], "score": t["score"], "calls": calls}
        
        current = next_key
    
    return {"path": path, "level": "Unknown", "score": 0, "calls": calls}


# Test essays
test_essays = [
    {
        "id": "weak-1 (below-basic)",
        "expected": 2,
        "text": """I think students should not wear uniforms because they want to ware there own close. Its not fare that we have to ware the same thing ever day. Some students like to show there style. That is why uniforms are bad."""
    },
    {
        "id": "medium-1 (basic)",
        "expected": 6,
        "text": """Some people think school uniforms are good because they make everyone equal. But I think they are bad because students should be able to express themselves. When I was in middle school we had uniforms and it was not that bad actually. The uniforms made it easier to get ready in the morning because I didn't have to pick out clothes. But some kids felt like they couldn't be themselves. I think schools should let students vote on whether to have uniforms. That way everyone has a say."""
    },
    {
        "id": "strong-1 (advanced)",
        "expected": 11,
        "text": """The debate over school uniforms touches on fundamental questions about education, individuality, and social equality. While uniforms are often promoted as tools for reducing socioeconomic disparities and improving focus, the evidence suggests their benefits are overstated. A 2023 study of 10,000 students across 50 schools found no significant correlation between uniform policies and academic performance. What uniforms do accomplish is the suppression of personal expression during a critical period of identity formation. Adolescents use clothing as a medium of self-discovery, and imposing uniformity during this developmental stage may have unintended psychological costs. Furthermore, the argument that uniforms reduce bullying based on clothing is flawed — bullying adapts, shifting from clothing to accessories, shoes, or other markers of status. Schools would be better served by investing in socio-emotional learning programs that address the root causes of bullying rather than implementing superficial equality measures."""
    }
]

print("=" * 60)
print("Phase 7v2 — Decision-Tree Scoring (with quality gate)")
print("=" * 60)

for essay in test_essays:
    print(f"\n{'='*60}")
    print(f"ESSAY: {essay['id']} (Expected: ~{essay['expected']}/12)")
    print(f"{'='*60}")
    
    result = grade_essay(essay["text"])
    
    print(f"\nFINAL: {result['level']} (Score: {result['score']}, {result['calls']} API calls)")
    print()
    
    for step in result["path"]:
        if step.get("final"):
            continue
        print(f"  [{step['node']}]")
        print(f"  Q: {step['question']}")
        print(f"  → {step['answer']}")
        if step.get("quotes"):
            print(f"    \"{step['quotes'][0][:120]}...\"")
        print()
    
    print(f"  >>> {result['level']} ({result['score']}/5)")
    print()
