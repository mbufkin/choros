#!/usr/bin/env python3
"""Full form-fill benchmark: qwen3.6:35b on CUDA via chat endpoint (no thinking)"""
import os, json, time, re, sys
sys.path.insert(0, '/home/mbufkin/choros/scoring')
os.environ['CHOROS_BACKEND'] = 'llamacpp'
os.environ['LLAMACPP_URL'] = 'http://100.85.15.59:8080'

from calibrate import generate_chat
from sklearn.metrics import cohen_kappa_score

with open('/home/mbufkin/choros/scoring/guardrails/essays.json') as f:
    essays = json.load(f)['essays']

human_scores = []
model_scores = []
timings = []

SYSTEM = """You are an expert essay grader. For each criterion below, mark:
[x]=fully met (2pts), [/]=partially met (1pt), [ ]=not met (0pts).
Quote verbatim evidence from the essay for each.
Output only the rubric with checkboxes and evidence quotes."""

USER_TEMPLATE = """CRITERIA:
1. CLAIM: Does the essay make a clear argument? [ ]
   Evidence:
2. EVIDENCE: Does it support claims with evidence? [ ]
   Evidence:
3. STRUCTURE: Is it organized with intro/body/conclusion? [ ]
   Evidence:

ESSAY:
{}"""

print("qwen3.6:35b CUDA CHAT BENCHMARK (no thinking)\n")

for e in essays:
    user_prompt = USER_TEMPLATE.format(e['text'])
    
    start = time.time()
    response = generate_chat(SYSTEM, user_prompt,
                            temperature=0, num_predict=1024, timeout=120)
    elapsed = time.time() - start
    
    # Parse checkboxes from response
    marks = re.findall(r'\[([x/ ])\]', response)
    score = sum(2 if m == 'x' else 1 if m == '/' else 0 for m in marks[:3])
    
    human = e['score']
    human_scores.append(human)
    model_scores.append(score)
    timings.append(elapsed)
    
    print(f"{e['id']}: {score} (human={human}) | marks={marks[:3]} | {elapsed:.1f}s")
    if response.strip():
        print(f"  preview: {response[:120]}...")

kappa = cohen_kappa_score(human_scores, model_scores)

print(f"\n{'='*60}")
print(f"qwen3.6:35b on CUDA (chat endpoint)")
print(f"Kappa: {kappa:.3f}")
print(f"Avg time: {sum(timings)/len(timings):.1f}s per essay")
print(f"Human:  {human_scores}")
print(f"Model:  {model_scores}")
print(f"CPU Kappa was: 0.545")
print(f"CPU time was:  45-110s/essay")
print(f"CUDA time:     {sum(timings)/len(timings):.1f}s avg → {100/(sum(timings)/len(timings)):.0f}x speedup")
