#!/usr/bin/env python3
"""Generate ~200 synthetic student essays across the 7 Choros prompt topics.
Uses gemma4 on Lenovo llama.cpp to write essays at varying quality levels (1-6).
Output: /tmp/asap200.json in the same format as the original.
"""
import json, sys, time, os, hashlib, random
import urllib.request, urllib.error

LLAMACPP_URL = os.environ.get("LLAMACPP_URL", "http://100.85.15.59:8080")
OUTPUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/asap200.json"
TOTAL = int(sys.argv[2]) if len(sys.argv) > 2 else 200

PROMPTS = {
    "driverless_cars": "Write an essay explaining your position on driverless/self-driving cars. Should they be allowed on public roads? Support your position with reasons and examples.",
    "electoral_college": "Write an essay explaining your position on the Electoral College. Should the U.S. keep it or switch to a popular vote? Support your position with reasons and examples.",
    "face_on_mars": "Write an essay explaining your theory about the 'Face on Mars' — is it evidence of alien life, a natural rock formation, or something else? Support your position with evidence from the provided texts.",
    "venus_exploration": "Write an essay explaining the challenges of exploring Venus and why it is difficult to study. Use evidence from the provided texts to support your explanation.",
    "facial_recognition": "Write an essay explaining whether facial expression recognition technology should be used in classrooms to monitor student engagement. Support your position with reasons and evidence.",
    "car_free_zones": "Write an essay explaining whether car-free zones like Vauban, Germany are a good model for other cities. Support your position with reasons and evidence from the text.",
    "seagoing_cowboys": "Write an essay explaining what the 'Seagoing Cowboys' program was and why it was significant. Use evidence from the provided texts.",
}

# Score distribution: slightly skewed toward middle (2-5), fewer at extremes (1,6)
SCORE_WEIGHTS = {1: 1, 2: 3, 3: 5, 4: 6, 5: 4, 6: 2}  # total weight = 21

def generate_essays():
    topics = list(PROMPTS.keys())
    random.seed(42)
    
    essays_per_topic = TOTAL // len(topics)
    remainder = TOTAL % len(topics)
    
    all_essays = []
    
    for topic_idx, topic in enumerate(topics):
        count = essays_per_topic + (1 if topic_idx < remainder else 0)
        prompt = PROMPTS[topic]
        print(f"[{topic}] Generating {count} essays...", flush=True)
        
        for i in range(count):
            # Pick a target score with weighted distribution
            score = random.choices(list(SCORE_WEIGHTS.keys()), 
                                  weights=list(SCORE_WEIGHTS.values()))[0]
            
            # Vary word count by score: higher scores → longer essays
            if score <= 2:
                target_wc = random.randint(30, 80)
            elif score <= 3:
                target_wc = random.randint(60, 150)
            elif score <= 4:
                target_wc = random.randint(120, 250)
            elif score <= 5:
                target_wc = random.randint(180, 350)
            else:
                target_wc = random.randint(250, 500)
            
            # Craft the generation prompt — model writes as a student
            gen_prompt = f"""You are a {['below-basic','weak','developing','competent','strong','excellent'][score-1]} student writer. Write an essay responding to this prompt:

{prompt}

Your essay should be approximately {target_wc} words. Write as a real student would — include natural mistakes, sentence variety, and authentic voice appropriate to your skill level. Write ONLY the essay, no labels or meta-text."""

            payload = json.dumps({
                "messages": [
                    {"role": "system", "content": "You are a student writing an essay. Write naturally — don't sound like AI."},
                    {"role": "user", "content": gen_prompt},
                ],
                "temperature": 0.9,
                "max_tokens": 1024,
                "stream": False,
            }).encode()
            
            req = urllib.request.Request(
                f"{LLAMACPP_URL}/v1/chat/completions",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = json.loads(resp.read())
                    text = data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"  [{i+1}/{count}] ERROR: {e}", flush=True)
                continue
            
            # Generate a stable ID from the text
            essay_id = hashlib.sha256(text.encode()).hexdigest()[:7]
            
            actual_wc = len(text.split())
            all_essays.append({
                "id": essay_id,
                "score": score,
                "topic": topic,
                "text": text,
            })
            
            print(f"  [{i+1}/{count}] {essay_id} (score={score}, {actual_wc}w)", flush=True)
            time.sleep(2)  # Small gap to avoid overwhelming the server
    
    # Write output
    output = {
        "source": "synthetic — generated by gemma4 on Lenovo for BLUF experiment",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_essays": len(all_essays),
        "prompts_used": PROMPTS,
        "score_distribution": {str(k): sum(1 for e in all_essays if e["score"] == k) 
                               for k in sorted(SCORE_WEIGHTS)},
        "essays": all_essays,
    }
    
    with open(OUTPUT, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nGenerated {len(all_essays)} essays → {OUTPUT}")
    # Print score distribution
    from collections import Counter
    dist = Counter(e["score"] for e in all_essays)
    print("Score distribution:", dict(sorted(dist.items())))

if __name__ == "__main__":
    generate_essays()
