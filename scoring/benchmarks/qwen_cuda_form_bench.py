#!/usr/bin/env python3
"""Run form-fill grading benchmark on CUDA qwen3.6"""
import os, json, time, sys
sys.path.insert(0, '/home/mbufkin/choros/scoring')
os.environ['CHOROS_BACKEND'] = 'llamacpp'
os.environ['LLAMACPP_URL'] = 'http://100.85.15.59:8080'

from calibrate import generate

with open('/home/mbufkin/choros/scoring/guardrails/essays.json') as f:
    essays = json.load(f)['essays']

print(f"Testing {len(essays)} essays with qwen3.6 on CUDA\n")

for e in essays:
    essay = e['text']
    human = e['score']
    
    # Simple form-fill prompt
    prompt = (
        '<|im_start|>system\n'
        'You are an expert essay grader. Fill out the rubric below.\n'
        'Mark [x] for 2pts (fully meets), [/] for 1pt (partially meets), [ ] for 0pts.\n'
        'For each, quote a short phrase from the essay as evidence.\n'
        '<|im_end|>\n'
        '<|im_start|>user\n'
        'CRITERIA:\n'
        '1. CLAIM: Clear argument [ ]\n'
        '   Evidence:\n'
        '2. EVIDENCE: Supports claims [ ]\n'
        '   Evidence:\n'
        '3. STRUCTURE: Organized [ ]\n'
        '   Evidence:\n'
        '\n'
        f'ESSAY: {essay}\n'
        '<|im_end|>\n'
        '<|im_start|>assistant\n'
        'Here is my grading:\n'
        '1. CLAIM: ['
    )
    
    start = time.time()
    response = generate(prompt, temperature=0, num_predict=256, timeout=120)
    elapsed = time.time() - start
    
    full = '1. CLAIM: [' + response
    # Parse [x] [/] [ ] marks
    import re
    marks = re.findall(r'\[([x/ ])\]', full)
    score = sum(2 if m == 'x' else 1 if m == '/' else 0 for m in marks[:3])
    
    print(f"{e['id']}: model={score} human={human} ({elapsed:.1f}s) | {' '.join(f'[{m}]' for m in marks[:3])}")
    
print("\nCUDA BENCHMARK COMPLETE")
