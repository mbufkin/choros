#!/usr/bin/env python3
"""Full form-fill benchmark: gemma4:26b on CUDA"""
import os, json, time, re, sys
sys.path.insert(0, '/home/mbufkin/choros/scoring')
os.environ['CHOROS_BACKEND'] = 'llamacpp'
os.environ['LLAMACPP_URL'] = 'http://100.85.15.59:8080'

from calibrate import generate
from sklearn.metrics import cohen_kappa_score

with open('/home/mbufkin/choros/scoring/guardrails/essays.json') as f:
    essays = json.load(f)['essays']

human_scores = []
model_scores = []
timings = []
results = []

FORM_PROMPT = """You are an expert essay grader. For each criterion below, provide:
1. A checkbox: [x]=fully met (2pts), [/]=partially met (1pt), [ ]=not met (0pts)
2. Evidence: quote from essay (verbatim)

CRITERIA:
1. CLAIM: Does the essay make a clear argument? [ ]
   Evidence: 
2. EVIDENCE: Does it support claims with evidence? [ ]
   Evidence: 
3. STRUCTURE: Is it organized with intro/body/conclusion? [ ]
   Evidence: 

ESSAY: {}

Output your grading below:"""

print("gemma4:26b CUDA FORM-FILL BENCHMARK\n")

for e in essays:
    prompt = FORM_PROMPT.format(e['text'])
    
    start = time.time()
    response = generate(prompt, temperature=0, num_predict=512, timeout=120)
    elapsed = time.time() - start
    
    # Parse checkboxes from response only (not prompt)
    marks = re.findall(r'\[([x/ ])\]', response)
    score = sum(2 if m == 'x' else 1 if m == '/' else 0 for m in marks[:3])
    
    human = e['score']
    human_scores.append(human)
    model_scores.append(score)
    timings.append(elapsed)
    
    results.append((e['id'], score, human, elapsed, marks[:3]))
    print(f"{e['id']}: {score} (human={human}) | marks={marks[:3]} | {elapsed:.1f}s")

# Compute Kappa
kappa = cohen_kappa_score(human_scores, model_scores)

print(f"\n{'='*60}")
print(f"gemma4:26b on CUDA")
print(f"Kappa: {kappa:.3f}")
print(f"Avg time: {sum(timings)/len(timings):.1f}s per essay")
print(f"Human:  {human_scores}")
print(f"Model:  {model_scores}")
print(f"CPU was: 100-143s/essay → {143/(sum(timings)/len(timings)):.0f}x speedup")
