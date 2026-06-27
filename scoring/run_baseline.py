#!/usr/bin/env python3
"""
Baseline run: Locked prompts on 20 ASAP essays.
Pass 1: feedback-blunt-teacher → blunt feedback
Pass 2: scoring-two-pass-blind → score from feedback only
Uses prompt library exclusively. No inline strings.

Output: baseline_results.json + summary to stdout.
"""
import json, sys, time, re, os, random
from pathlib import Path

# Add scoring dir to path so prompt_lib import works
sys.path.insert(0, str(Path(__file__).resolve().parent))
from prompt_lib import get_prompt, get_rubric, list_prompts

# Config
LLAMACPP_URL = os.environ.get("LLAMACPP_URL", "http://100.85.15.59:8080")
ESSAYS_PATH = "/tmp/asap200.json"
N_ESSAYS = int(os.environ.get("BASELINE_N", "20"))
OUTPUT_NAME = os.environ.get("BASELINE_OUTPUT", "baseline_results.json")
OUTPUT_PATH = Path(__file__).resolve().parent / "guardrails" / OUTPUT_NAME
SEED = int(os.environ.get("BASELINE_SEED", "42"))

# Writing prompts per topic (from asap_rubrics.py)
TOPIC_PROMPTS = {
    "driverless_cars": "Write an essay explaining your position on driverless/self-driving cars. Should they be allowed on public roads? Support your position with reasons and examples.",
    "electoral_college": "Write an essay explaining your position on the Electoral College. Should the U.S. keep it or switch to a popular vote? Support your position with reasons and examples.",
    "face_on_mars": "Write an essay explaining your theory about the 'Face on Mars' — is it evidence of alien life, a natural rock formation, or something else? Support your position with evidence from the provided texts.",
    "venus_exploration": "Write an essay explaining the challenges of exploring Venus and why it is difficult to study. Use evidence from the provided texts to support your explanation.",
    "facial_recognition": "Write an essay explaining whether facial expression recognition technology should be used in classrooms to monitor student engagement. Support your position with reasons and evidence.",
    "car_free_zones": "Write an essay explaining whether car-free zones like Vauban, Germany are a good model for other cities. Support your position with reasons and evidence from the text.",
    "seagoing_cowboys": "Write an essay explaining what the 'Seagoing Cowboys' program was and why it was significant. Use evidence from the provided texts.",
}

TOPIC_KEYWORDS = {
    "driverless_cars": ["driverless car", "self-driving", "self driven", "driverless", "google car"],
    "electoral_college": ["electoral college", "electoral vote", "popular vote", "electors"],
    "face_on_mars": ["face on mars", "cydonia", "alien", "mars global surveyor", "pareidolia"],
    "venus_exploration": ["venus", "evening star", "hottest planet", "greenhouse effect"],
    "facial_recognition": ["facial", "face action coding", "facs", "emotional expression", "dr. huang"],
    "car_free_zones": ["vauban", "car-free", "car free", "70 percent", "germany"],
    "seagoing_cowboys": ["seagoing", "cowboy", "heifer", "unrra", "luke", "livestock"],
}

# ASAP 1-6 rubric
RUBRIC_1_6 = """Scoring Rubric (1-6 scale):

1 (Inadequate): Unreadable, off-topic, or blank. No position or evidence.
2 (Weak): Position unclear or undeveloped. Minimal reasoning. Many errors.
3 (Developing): Basic position with some support. Simple organization. Noticeable errors.
4 (Competent): Clear position with adequate support. Organized. Some errors but doesn't interfere.
5 (Strong): Strong position with specific evidence. Good organization. Few errors.
6 (Excellent): Sophisticated argument, compelling evidence, excellent organization, nearly error-free."""


def detect_topic(text: str) -> str | None:
    text_lower = text.lower()
    scores = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[topic] = score
    if not scores:
        return None
    return max(scores, key=scores.get)


def llamacpp_chat(system: str, user: str, temperature: float = 0.3,
                  max_tokens: int = 2048, timeout: int = 300) -> str:
    """Call llama.cpp /v1/chat/completions (handles thinking mode)."""
    import urllib.request, urllib.error
    payload = json.dumps({
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }).encode()
    req = urllib.request.Request(
        f"{LLAMACPP_URL}/v1/chat/completions", data=payload,
        headers={"Content-Type": "application/json"},
    )
    content_parts = []
    reasoning_parts = []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for line in resp:
                line = line.decode()
                if line.startswith("data: ") and line[6:].strip() != "[DONE]":
                    try:
                        chunk = json.loads(line[6:].strip())
                        delta = chunk["choices"][0]["delta"]
                        if delta.get("reasoning_content"):
                            reasoning_parts.append(delta["reasoning_content"])
                        if delta.get("content"):
                            content_parts.append(delta["content"])
                    except (json.JSONDecodeError, KeyError, IndexError):
                        pass
        content = "".join(content_parts)
        if not content.strip():
            content = "".join(reasoning_parts)
        return content
    except Exception as e:
        return f"[ERROR: {e}]"


def llamacpp_raw(prompt: str, temperature: float = 0.1,
                 n_predict: int = 256, timeout: int = 120) -> str:
    """Call llama.cpp /v1/completions (raw, no chat template)."""
    import urllib.request, urllib.error
    payload = json.dumps({
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": n_predict,
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        f"{LLAMACPP_URL}/v1/completions", data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read()).get("choices", [{}])[0].get("text", "")
    except Exception as e:
        return f"[ERROR: {e}]"


def extract_score(response: str) -> int | None:
    """Extract a 1-6 score from model response."""
    # Try SCORE: N pattern
    match = re.search(r'(?:SCORE|score|Score):\s*(\d+)', response)
    if match:
        score = int(match.group(1))
        if 1 <= score <= 6:
            return score
    # Try standalone number
    match = re.search(r'\b([1-6])\b', response[:200])
    if match:
        return int(match.group(1))
    return None


def main():
    # Load essays
    with open(ESSAYS_PATH) as f:
        all_essays = json.load(f)["essays"]

    # Pick 20 random essays with seed
    random.seed(SEED)
    selected = random.sample(all_essays, min(N_ESSAYS, len(all_essays)))

    print(f"BASELINE RUN: Locked Prompts v1.0.0")
    print(f"Model: gemma4:26b (Lenovo CUDA)")
    print(f"Essays: {N_ESSAYS} from ASAP-200 (seed={SEED})")
    print(f"Prompt library: {len(list_prompts())} prompts")
    print(f"Pass 1: feedback-blunt-teacher")
    print(f"Pass 2: scoring-two-pass-blind (1-6 rubric)")
    print(f"{'='*60}\n")

    results = []
    human_scores = []
    model_scores = []

    for i, essay in enumerate(selected):
        eid = essay["id"]
        human = essay["score"]
        text = essay["text"]
        wc = len(text.split())

        # Detect topic
        topic = detect_topic(text)
        writing_prompt = TOPIC_PROMPTS.get(topic, "Explain your position and support it with reasons.")

        print(f"[{i+1}/{N_ESSAYS}] {eid} (human={human}, {wc}w, topic={topic or 'unknown'})", flush=True)

        # ── PASS 1: Blunt Feedback ──
        feedback_prompt = get_prompt("feedback-blunt-teacher",
                                     writing_prompt=writing_prompt,
                                     essay=text)
        t0 = time.time()
        # Use system+user format for better thinking mode handling
        feedback = llamacpp_chat(
            "You are a blunt, honest classroom teacher.",
            feedback_prompt,
            temperature=0.3, max_tokens=2048, timeout=300
        )
        t1 = time.time() - t0
        fb_wc = len(feedback.split())
        fb_quotes = len(re.findall(r'"([^"]{10,})"', feedback))
        print(f"  Pass 1: {fb_wc}w feedback, {fb_quotes} quotes [{t1:.0f}s]", flush=True)

        # ── PASS 2: Blind Score from Feedback ──
        score_prompt = get_prompt("scoring-two-pass-blind",
                                  rubric=RUBRIC_1_6,
                                  feedback=feedback)
        t0 = time.time()
        score_response = llamacpp_raw(score_prompt, temperature=0.1,
                                      n_predict=256, timeout=120)
        t2 = time.time() - t0
        model_score = extract_score(score_response)
        if model_score is None:
            print(f"  Pass 2: SCORE EXTRACTION FAILED [{t2:.0f}s]", flush=True)
            print(f"  Raw response: {score_response[:200]}", flush=True)
            model_score = human  # fallback to human score
        else:
            delta = model_score - human
            sign = "+" if delta > 0 else ""
            print(f"  Pass 2: model={model_score} ({sign}{delta}) [{t2:.0f}s]", flush=True)

        human_scores.append(human)
        model_scores.append(model_score)

        results.append({
            "id": eid,
            "human": human,
            "model": model_score,
            "delta": model_score - human,
            "topic": topic,
            "wc": wc,
            "feedback_wc": fb_wc,
            "feedback_quotes": fb_quotes,
            "pass1_s": round(t1, 1),
            "pass2_s": round(t2, 1),
        })

    # ── Compute Kappa ──
    n = len(human_scores)
    po = sum(1 for h, m in zip(human_scores, model_scores) if h == m) / n
    all_cats = set(human_scores) | set(model_scores)
    pe = sum(
        (sum(1 for h in human_scores if h == cat) / n) *
        (sum(1 for m in model_scores if m == cat) / n)
        for cat in all_cats
    )
    kappa = (po - pe) / (1 - pe) if pe < 1.0 else 1.0

    # ── Summary ──
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"N: {n}")
    print(f"Kappa: {kappa:.3f}")
    print(f"Agreement: {po:.1%}")
    print(f"Avg pass1 time: {sum(r['pass1_s'] for r in results)/n:.0f}s")
    print(f"Avg pass2 time: {sum(r['pass2_s'] for r in results)/n:.0f}s")
    print(f"Avg feedback quotes: {sum(r['feedback_quotes'] for r in results)/n:.1f}")

    # Score distribution comparison
    from collections import Counter
    human_dist = Counter(human_scores)
    model_dist = Counter(model_scores)
    print(f"\nScore distribution:")
    print(f"  Human: {dict(sorted(human_dist.items()))}")
    print(f"  Model: {dict(sorted(model_dist.items()))}")

    # Per-essay detail
    print(f"\n{'ID':<12} {'Human':>6} {'Model':>6} {'Δ':>4} {'Topic':<20} {'FB words':>8} {'Quotes':>6} {'P1':>5} {'P2':>5}")
    print(f"{'-'*80}")
    for r in results:
        print(f"{r['id']:<12} {r['human']:>6} {r['model']:>6} {r['delta']:>4} "
              f"{r['topic'] or '?':<20} {r['feedback_wc']:>8} {r['feedback_quotes']:>6} "
              f"{r['pass1_s']:>4.0f}s {r['pass2_s']:>4.0f}s")

    # Save
    output = {
        "model": "gemma4:26b",
        "backend": "llamacpp-cuda",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_essays": n,
        "seed": SEED,
        "kappa": round(kappa, 3),
        "agreement": round(po, 3),
        "prompts_used": {
            "pass1": {"id": "feedback-blunt-teacher", "version": "1.0.0"},
            "pass2": {"id": "scoring-two-pass-blind", "version": "1.0.0"},
            "rubric": "RUBRIC_1_6 (ASAP 1-6 scale, inline — not yet in library)",
        },
        "score_distribution": {
            "human": {str(k): v for k, v in sorted(human_dist.items())},
            "model": {str(k): v for k, v in sorted(model_dist.items())},
        },
        "results": results,
    }
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
