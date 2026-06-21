#!/usr/bin/env python3
"""Full form-fill benchmark: qwen3.6:35b on CUDA with chat template"""
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

QWEN_FORM = """<|im_start|>system
You are an expert essay grader. Fill out the rubric below. Mark [x]=fully met (2pts), [/]=partially met (1pt), [ ]=not met (0pts). For each, quote verbatim evidence from the essay.<|im_end|>
<|im_start|>user
CRITERIA:
1. CLAIM: Clear argument? [ ]
   Evidence:
2. EVIDENCE: Supports claims? [ ]
   Evidence:
3. STRUCTURE: Organized? [ ]
   Evidence:

ESSAY:
{}<|im_end|>
<|im_start|>assistant
"""

print("qwen3.6:35b CUDA FORM-FILL BENCHMARK\n")

for e in essays:
    prompt = QWEN_FORM.format(e['text'])
    
    start = time.time()
    response = generate(prompt, temperature=0, num_predict=512, timeout=120)
    elapsed = time.time() - start
    
    # Parse checkboxes from response only
    marks = re.findall(r'(?:CRITERIA|CLAIM|EVIDENCE|STRUCTURE).*?\[([x/ ])\]', response, re.DOTALL)
    if not marks:
        marks = re.findall(r'\[([x/ ])\]', response)
    score = sum(2 if m == 'x' else 1 if m == '/' else 0 for m in marks[:3])
    
    human = e['score']
    human_scores.append(human)
    model_scores.append(score)
    timings.append(elapsed)
    
    print(f"{e['id']}: {score} (human={human}) | marks={marks[:3]} | {elapsed:.1f}s")
    if elapsed > 5 and response:
        print(f"  preview: {response[:120]}...")

kappa = cohen_kappa_score(human_scores, model_scores)

print(f"\n{'='*60}")
print(f"qwen3.6:35b on CUDA")
print(f"Kappa: {kappa:.3f}")
print(f"Avg time: {sum(timings)/len(timings):.1f}s per essay")
print(f"Human:  {human_scores}")
print(f"Model:  {model_scores}")
print(f"CPU was: 45-110s/essay → {100/(sum(timings)/len(timings)):.0f}x speedup")
print(f"CPU Kappa was: 0.545 (same model, same approach)")
