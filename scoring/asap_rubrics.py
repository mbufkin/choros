"""
Prompt-specific rubrics for ASAP AES 2.0 topics.
Each rubric has 7 criteria (0/1/2 points, raw 0-14, calibrated to human 1-6).
"""
ASAP_RUBRICS = {
    "driverless_cars": {
        "prompt": "Write an essay explaining your position on driverless/self-driving cars. Should they be allowed on public roads? Support your position with reasons and examples.",
        "criteria": [
            {"id": "THESIS", "label": "Position on Driverless Cars",
             "question": "Does the essay state a clear position on whether driverless cars should be allowed?",
             "evidence_type": "local_quote"},
            {"id": "EVIDENCE_COUNT", "label": "Reasons/Examples",
             "question": "How many distinct reasons or examples support the position (safety, convenience, jobs, technology reliability, etc.)?",
             "evidence_type": "span_level"},
            {"id": "EVIDENCE_QUALITY", "label": "Specific Evidence",
             "question": "Are the reasons concrete and specific (not vague generalities like 'they are dangerous')?",
             "evidence_type": "local_quote"},
            {"id": "COUNTER", "label": "Opposing Views",
             "question": "Does the essay acknowledge counterarguments (e.g. 'some say driverless cars are safer, but...')?",
             "evidence_type": "local_quote"},
            {"id": "ORGANIZATION", "label": "Structure",
             "question": "Is the essay organized with clear introduction, body paragraphs, and conclusion?",
             "evidence_type": "span_level"},
            {"id": "MECHANICS", "label": "Grammar & Spelling",
             "question": "Are grammar, spelling, and punctuation generally correct?",
             "evidence_type": "local_quote"},
            {"id": "DEPTH", "label": "Depth of Reasoning",
             "question": "Does the essay go beyond surface arguments to consider broader implications (economic, social, ethical)?",
             "evidence_type": "local_quote"},
        ]
    },
    "electoral_college": {
        "prompt": "Write an essay explaining your position on the Electoral College. Should the U.S. keep it or switch to a popular vote? Support your position with reasons and examples.",
        "criteria": [
            {"id": "THESIS", "label": "Position on Electoral College",
             "question": "Does the essay state a clear position on keeping or abolishing the Electoral College?",
             "evidence_type": "local_quote"},
            {"id": "EVIDENCE_COUNT", "label": "Reasons/Examples",
             "question": "How many distinct reasons support the position (fairness, representation, swing states, founding intent, etc.)?",
             "evidence_type": "span_level"},
            {"id": "EVIDENCE_QUALITY", "label": "Specific Evidence",
             "question": "Are the reasons backed by concrete facts or examples (number of electors, specific elections, state examples)?",
             "evidence_type": "local_quote"},
            {"id": "COUNTER", "label": "Opposing Views",
             "question": "Does the essay acknowledge the other side's arguments (e.g. 'supporters say it protects small states, but...')?",
             "evidence_type": "local_quote"},
            {"id": "ORGANIZATION", "label": "Structure",
             "question": "Is the essay organized with clear introduction, body, and conclusion?",
             "evidence_type": "span_level"},
            {"id": "MECHANICS", "label": "Grammar & Spelling",
             "question": "Are grammar, spelling, and punctuation generally correct?",
             "evidence_type": "local_quote"},
            {"id": "DEPTH", "label": "Depth of Reasoning",
             "question": "Does the essay show understanding of WHY the Electoral College exists (federalism, founding compromises) rather than just surface opinions?",
             "evidence_type": "local_quote"},
        ]
    },
    "face_on_mars": {
        "prompt": "Write an essay explaining your theory about the 'Face on Mars' — is it evidence of alien life, a natural rock formation, or something else? Support your position with evidence from the provided texts.",
        "criteria": [
            {"id": "THESIS", "label": "Position on Face on Mars",
             "question": "Does the essay state a clear position on what the Face on Mars is (natural, alien, or other)?",
             "evidence_type": "local_quote"},
            {"id": "EVIDENCE_COUNT", "label": "Evidence from Source",
             "question": "How many pieces of evidence from the source texts support the position?",
             "evidence_type": "span_level"},
            {"id": "EVIDENCE_QUALITY", "label": "Specific Source Use",
             "question": "Are the sources cited with specific details (Mars Global Surveyor, mesa formations, specific measurements)?",
             "evidence_type": "local_quote"},
            {"id": "COUNTER", "label": "Alternative Theories",
             "question": "Does the essay acknowledge alternative explanations (e.g. 'while some believe it's alien, the photos show...')?",
             "evidence_type": "local_quote"},
            {"id": "ORGANIZATION", "label": "Structure",
             "question": "Is the essay organized with clear introduction, body, and conclusion?",
             "evidence_type": "span_level"},
            {"id": "MECHANICS", "label": "Grammar & Spelling",
             "question": "Are grammar, spelling, and punctuation generally correct?",
             "evidence_type": "local_quote"},
            {"id": "DEPTH", "label": "Scientific Reasoning",
             "question": "Does the essay demonstrate understanding of scientific reasoning (pareidolia, geological processes, evidence standards) rather than just opinion?",
             "evidence_type": "local_quote"},
        ]
    },
    "venus_exploration": {
        "prompt": "Write an essay explaining the challenges of exploring Venus and why it is difficult to study. Use evidence from the provided texts to support your explanation.",
        "criteria": [
            {"id": "THESIS", "label": "Main Argument",
             "question": "Does the essay clearly explain why Venus is challenging to explore?",
             "evidence_type": "local_quote"},
            {"id": "EVIDENCE_COUNT", "label": "Challenges Identified",
             "question": "How many specific challenges are identified (temperature, atmospheric pressure, sulfuric acid clouds, etc.)?",
             "evidence_type": "span_level"},
            {"id": "EVIDENCE_QUALITY", "label": "Specific Details",
             "question": "Are the challenges described with concrete details (specific temperatures, probe names, mission data)?",
             "evidence_type": "local_quote"},
            {"id": "COUNTER", "label": "Complexity",
             "question": "Does the essay acknowledge any successes or why we keep trying despite the challenges?",
             "evidence_type": "local_quote"},
            {"id": "ORGANIZATION", "label": "Structure",
             "question": "Is the essay organized with clear introduction, body, and conclusion?",
             "evidence_type": "span_level"},
            {"id": "MECHANICS", "label": "Grammar & Spelling",
             "question": "Are grammar, spelling, and punctuation generally correct?",
             "evidence_type": "local_quote"},
            {"id": "DEPTH", "label": "Scientific Understanding",
             "question": "Does the essay show understanding of WHY Venus is so extreme (runaway greenhouse, proximity to sun) rather than just listing facts?",
             "evidence_type": "local_quote"},
        ]
    },
    "facial_recognition": {
        "prompt": "Write an essay explaining whether facial expression recognition technology should be used in classrooms to monitor student engagement. Support your position with reasons and evidence.",
        "criteria": [
            {"id": "THESIS", "label": "Position on Facial Recognition",
             "question": "Does the essay state a clear position on using facial recognition in classrooms?",
             "evidence_type": "local_quote"},
            {"id": "EVIDENCE_COUNT", "label": "Reasons/Examples",
             "question": "How many distinct reasons support the position (privacy, accuracy, student anxiety, teaching benefits, etc.)?",
             "evidence_type": "span_level"},
            {"id": "EVIDENCE_QUALITY", "label": "Specific Evidence",
             "question": "Are reasons backed by concrete details (specific muscles, Dr. Huang's research, real vs fake smiles)?",
             "evidence_type": "local_quote"},
            {"id": "COUNTER", "label": "Opposing Views",
             "question": "Does the essay address counterarguments (e.g. 'some say it helps teachers, but it may embarrass students')?",
             "evidence_type": "local_quote"},
            {"id": "ORGANIZATION", "label": "Structure",
             "question": "Is the essay organized with clear introduction, body, and conclusion?",
             "evidence_type": "span_level"},
            {"id": "MECHANICS", "label": "Grammar & Spelling",
             "question": "Are grammar, spelling, and punctuation generally correct?",
             "evidence_type": "local_quote"},
            {"id": "DEPTH", "label": "Ethical Reasoning",
             "question": "Does the essay consider deeper issues (surveillance ethics, consent, false positives, power dynamics) beyond surface pros/cons?",
             "evidence_type": "local_quote"},
        ]
    },
    "car_free_zones": {
        "prompt": "Write an essay explaining whether car-free zones like Vauban, Germany are a good model for other cities. Support your position with reasons and evidence from the text.",
        "criteria": [
            {"id": "THESIS", "label": "Position on Car-Free Zones",
             "question": "Does the essay state a clear position on whether the Vauban model should be adopted elsewhere?",
             "evidence_type": "local_quote"},
            {"id": "EVIDENCE_COUNT", "label": "Reasons/Examples",
             "question": "How many distinct reasons support the position (pollution, health, community, cost, convenience, etc.)?",
             "evidence_type": "span_level"},
            {"id": "EVIDENCE_QUALITY", "label": "Specific Details",
             "question": "Are reasons backed by specific details from Vauban (70% car-free, parking at edge, tram access, etc.)?",
             "evidence_type": "local_quote"},
            {"id": "COUNTER", "label": "Alternative Views",
             "question": "Does the essay acknowledge challenges or counterarguments (rural areas, elderly, emergencies, American car culture)?",
             "evidence_type": "local_quote"},
            {"id": "ORGANIZATION", "label": "Structure",
             "question": "Is the essay organized with clear introduction, body, and conclusion?",
             "evidence_type": "span_level"},
            {"id": "MECHANICS", "label": "Grammar & Spelling",
             "question": "Are grammar, spelling, and punctuation generally correct?",
             "evidence_type": "local_quote"},
            {"id": "DEPTH", "label": "Systems Thinking",
             "question": "Does the essay consider how car-free zones connect to larger systems (urban planning, climate change, equity, public transit)?",
             "evidence_type": "local_quote"},
        ]
    },
    "seagoing_cowboys": {
        "prompt": "Write an essay explaining what the 'Seagoing Cowboys' program was and why it was significant. Use evidence from the provided texts.",
        "criteria": [
            {"id": "THESIS", "label": "Main Idea",
             "question": "Does the essay clearly explain what the Seagoing Cowboys program was?",
             "evidence_type": "local_quote"},
            {"id": "EVIDENCE_COUNT", "label": "Supporting Details",
             "question": "How many specific details support the explanation (who, what, when, where, why, how)?",
             "evidence_type": "span_level"},
            {"id": "EVIDENCE_QUALITY", "label": "Specific Evidence",
             "question": "Are details concrete (Heifer International, UNRRA, specific animals, specific countries)?",
             "evidence_type": "local_quote"},
            {"id": "COUNTER", "label": "Significance",
             "question": "Does the essay explain WHY this mattered (post-war reconstruction, humanitarian aid, etc.)?",
             "evidence_type": "local_quote"},
            {"id": "ORGANIZATION", "label": "Structure",
             "question": "Is the essay organized with clear introduction, body, and conclusion?",
             "evidence_type": "span_level"},
            {"id": "MECHANICS", "label": "Grammar & Spelling",
             "question": "Are grammar, spelling, and punctuation generally correct?",
             "evidence_type": "local_quote"},
            {"id": "DEPTH", "label": "Historical Context",
             "question": "Does the essay place the program in broader historical context (WWII aftermath, Marshall Plan, Cold War)?",
             "evidence_type": "local_quote"},
        ]
    },
}

# Topic detection keywords — run this first to route essays
TOPIC_KEYWORDS = {
    "driverless_cars": ["driverless car", "self-driving", "self driven", "driverless", "google car", "cars that drive themselves"],
    "electoral_college": ["electoral college", "electoral vote", "popular vote", "electors", "president should be elected"],
    "face_on_mars": ["face on mars", "cydonia", "alien", "mars global surveyor", "mesa", "pareidolia"],
    "venus_exploration": ["venus", "evening star", "hottest planet", "greenhouse effect", "spacecraft"],
    "facial_recognition": ["facial", "face action coding", "facs", "emotional expression", "dr. huang", "classroom"],
    "car_free_zones": ["vauban", "car-free", "car free", "70 percent", "germany"],
    "seagoing_cowboys": ["seagoing", "cowboy", "heifer", "unrra", "luke", "livestock", "cattle", "horses"],
}

def detect_topic(text: str) -> str:
    """Route essay to the right prompt-specific rubric."""
    text_lower = text.lower()
    scores = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[topic] = score
    if not scores:
        return None  # unknown topic
    return max(scores, key=scores.get)

def get_rubric_for_essay(text: str):
    """Return the prompt-specific rubric for this essay."""
    topic = detect_topic(text)
    if topic and topic in ASAP_RUBRICS:
        return ASAP_RUBRICS[topic]
    return None  # fall back to generic?
