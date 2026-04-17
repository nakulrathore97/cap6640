"""
grammar_generate.py
Introduce exactly ONE grammatical error per prompt line, analogous to typo_generate.py.

Error types (chosen randomly if they apply to the sentence):
  1. subject_verb_agreement  – "are" ↔ "is",  "were" ↔ "was",  "have" ↔ "has",  "do" ↔ "does"
  2. drop_article            – remove a randomly chosen "a", "an", or "the"
  3. wrong_article           – swap "a"↔"an", or "a"/"an" ↔ "the"
  4. wrong_preposition       – replace a preposition with a different one
  5. bad_verb_form           – gerund → base ("running" → "run") or base → gerund ("run" → "running")
  6. double_subject          – insert a redundant pronoun after a noun phrase subject
  7. tense_shift             – simple past ↔ present tense for common irregular/regular verbs

If none of the targeted patterns are found the prompt is returned unchanged (rare for these prompts).
"""

import random
import re

# ── 1. Subject-verb agreement ────────────────────────────────────────────────
SV_PAIRS = [
    # (correct, wrong)  – applied in both directions randomly
    (r'\bare\b', 'is'),
    (r'\bis\b',  'are'),
    (r'\bwere\b','was'),
    (r'\bwas\b', 'were'),
    (r'\bhave\b','has'),
    (r'\bhas\b', 'have'),
    (r'\bdo\b',  'does'),
    (r'\bdoes\b','do'),
]

# ── 2 & 3. Articles ──────────────────────────────────────────────────────────
ARTICLE_RE = re.compile(r'\b(a|an|the)\b', re.IGNORECASE)

ARTICLE_SWAPS = {
    'a':   ['an', 'the', ''],   # '' means drop it
    'an':  ['a',  'the', ''],
    'the': ['a',  'an',  ''],
}

# ── 4. Prepositions ──────────────────────────────────────────────────────────
PREPS = ['in', 'on', 'at', 'by', 'for', 'with', 'from', 'of', 'to', 'into', 'onto', 'through', 'under', 'over', 'about']
PREP_RE = re.compile(r'\b(' + '|'.join(PREPS) + r')\b', re.IGNORECASE)

# ── 5. Verb form (gerund ↔ base) ─────────────────────────────────────────────
# Heuristic: words ending in "-ing" that look like verbs (preceded by is/are/was/were or standalone)
GERUND_RE = re.compile(r'\b([a-z]{3,})ing\b', re.IGNORECASE)

# ── 6. Double subject ────────────────────────────────────────────────────────
# Insert pronoun after common NP subjects
DOUBLE_SUBJ_PRONOUNS = ['it', 'they', 'he', 'she']
# Pattern: "a/an/the <noun> <verb>"  – insert pronoun between noun and verb
DOUBLE_SUBJ_RE = re.compile(
    r'\b(a|an|the)\s+([a-z]+(?:\s+[a-z]+){0,2})\s+(is|are|was|were|has|have|do|does|can|will|would|should|must|may|might|run|runs|walk|walks|play|plays|make|makes|show|shows|stand|stands|sit|sits|lie|lies|hold|holds)\b',
    re.IGNORECASE
)

# ── 7. Tense shift ───────────────────────────────────────────────────────────
# ── 8. Universal fallback: word duplication or deletion ─────────────────────
# Targets any "word" of 4+ alpha chars that isn't a common stopword
FALLBACK_STOP = {'with', 'from', 'that', 'this', 'they', 'have', 'will', 'been', 'were', 'very',
                 'more', 'most', 'then', 'also', 'each', 'over', 'into', 'your', 'what', 'when',
                 'their', 'there', 'about', 'which', 'would', 'could', 'should', 'other', 'some'}

# ── 7. Tense shift ───────────────────────────────────────────────────────────
# Simple past → simple present (and vice-versa), for a curated word list
TENSE_PAIRS = [
    (r'\bran\b',      'run'),   (r'\brun\b',     'ran'),
    (r'\bwent\b',     'go'),    (r'\bgo\b',       'went'),
    (r'\bsaw\b',      'see'),   (r'\bsee\b',      'saw'),
    (r'\bmade\b',     'make'),  (r'\bmake\b',     'made'),
    (r'\btook\b',     'take'),  (r'\btake\b',     'took'),
    (r'\bcame\b',     'come'),  (r'\bcome\b',     'came'),
    (r'\bstood\b',    'stand'), (r'\bstand\b',    'stood'),
    (r'\bshowed\b',   'show'),  (r'\bshow\b',     'showed'),
    (r'\blocked\b',   'look'),  (r'\blook\b',     'looked'),
    (r'\bwalked\b',   'walk'),  (r'\bwalk\b',     'walked'),
    (r'\bplayed\b',   'play'),  (r'\bplay\b',     'played'),
    (r'\bpointed\b',  'point'), (r'\bpoint\b',    'pointed'),
    (r'\bcreated\b',  'create'),(r'\bcreate\b',   'created'),
    (r'\bsurrounded\b','surround'),(r'\bsurround\b','surrounded'),
]


# ── Helper: single random substitution ──────────────────────────────────────
def _replace_one(text: str, pattern: str, replacement: str, flags=re.IGNORECASE) -> str | None:
    """Replace the FIRST randomly-chosen occurrence of `pattern` with `replacement`.
    Returns the new string, or None if pattern not found."""
    matches = list(re.finditer(pattern, text, flags))
    if not matches:
        return None
    m = random.choice(matches)
    # preserve leading whitespace if replacement is '' (article drop)
    if replacement == '':
        # remove the article + exactly one trailing space
        start, end = m.start(), m.end()
        if end < len(text) and text[end] == ' ':
            end += 1
        new_text = text[:start] + text[end:]
    else:
        new_text = text[:m.start()] + replacement + text[m.end():]
    return new_text


# ── Individual perturbation functions ────────────────────────────────────────

def _perturb_sv_agreement(text: str) -> str | None:
    # Collect all applicable (pattern, replacement) pairs that actually match
    candidates = []
    for pat, repl in SV_PAIRS:
        if re.search(pat, text, re.IGNORECASE):
            candidates.append((pat, repl))
    if not candidates:
        return None
    pat, repl = random.choice(candidates)
    return _replace_one(text, pat, repl)


def _perturb_article(text: str) -> str | None:
    matches = list(ARTICLE_RE.finditer(text))
    if not matches:
        return None
    m = random.choice(matches)
    original = m.group(0).lower()
    replacement = random.choice(ARTICLE_SWAPS[original])
    return _replace_one(text, r'\b' + re.escape(m.group(0)) + r'\b', replacement)


def _perturb_preposition(text: str) -> str | None:
    matches = list(PREP_RE.finditer(text))
    if not matches:
        return None
    m = random.choice(matches)
    original = m.group(0).lower()
    alternatives = [p for p in PREPS if p != original]
    replacement = random.choice(alternatives)
    return _replace_one(text, r'\b' + re.escape(m.group(0)) + r'\b', replacement)


def _perturb_verb_form(text: str) -> str | None:
    """Strip '-ing' suffix to convert gerund → base form, or add '-ing' to a short verb."""
    # gerund → base
    matches = list(GERUND_RE.finditer(text))
    if matches:
        m = random.choice(matches)
        base = m.group(1)  # everything before 'ing'
        new_text = text[:m.start()] + base + text[m.end():]
        return new_text
    return None


def _perturb_double_subject(text: str) -> str | None:
    matches = list(DOUBLE_SUBJ_RE.finditer(text))
    if not matches:
        return None
    m = random.choice(matches)
    pronoun = random.choice(DOUBLE_SUBJ_PRONOUNS)
    # Insert pronoun between the noun phrase and the verb
    # Group structure: (article) (noun phrase) (verb)
    insert_pos = m.start(3)  # start of the verb group
    new_text = text[:insert_pos] + pronoun + ' ' + text[insert_pos:]
    return new_text


def _perturb_fallback(text: str) -> str | None:
    """Universal fallback: either duplicate or drop a random content word (4+ chars).
    Works on any prompt, including pure tag-lists."""
    WORD_RE = re.compile(r'\b([a-zA-Z]{4,})\b')
    matches = [m for m in WORD_RE.finditer(text) if m.group(0).lower() not in FALLBACK_STOP]
    if not matches:
        return None
    m = random.choice(matches)
    op = random.choice(['duplicate', 'delete'])
    if op == 'duplicate':
        # insert the word again right after itself, separated by a space
        new_text = text[:m.end()] + ' ' + m.group(0) + text[m.end():]
    else:
        # delete the word and any immediately following space
        start, end = m.start(), m.end()
        if end < len(text) and text[end] == ' ':
            end += 1
        new_text = text[:start] + text[end:]
    return new_text


def _perturb_tense(text: str) -> str | None:
    candidates = []
    for pat, repl in TENSE_PAIRS:
        if re.search(pat, text, re.IGNORECASE):
            candidates.append((pat, repl))
    if not candidates:
        return None
    pat, repl = random.choice(candidates)
    return _replace_one(text, pat, repl)


# ── Master perturbation function ─────────────────────────────────────────────

# All available perturbation types with their functions
# _perturb_fallback is intentionally last — it is the guaranteed backstop.
ALL_PERTURBATIONS = [
    _perturb_sv_agreement,
    _perturb_article,
    _perturb_preposition,
    _perturb_verb_form,
    _perturb_double_subject,
    _perturb_tense,
    _perturb_fallback,   # always fires if nothing else does
]


def perturb_grammar(text: str) -> str:
    """Inject exactly one grammatical error into the text (if any pattern matches).
    Tries perturbation types in a random order; returns the first successful one.
    If none applies, returns text unchanged."""
    order = list(ALL_PERTURBATIONS)
    random.shuffle(order)
    for fn in order:
        result = fn(text)
        if result is not None and result != text:
            return result
    return text  # no applicable pattern found


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import os

    input_path  = os.path.join(os.path.dirname(__file__), 'diffusiondb_prompts_small.txt')
    output_path = os.path.join(os.path.dirname(__file__), 'diffusiondb_prompts_small_grammar.txt')

    changed = 0
    total   = 0
    with open(input_path, 'r', encoding='utf-8') as fin, \
         open(output_path, 'w', encoding='utf-8') as fout:
        for line in fin:
            prompt = line.rstrip('\n')
            perturbed = perturb_grammar(prompt)
            fout.write(perturbed + '\n')
            total += 1
            if perturbed != prompt:
                changed += 1

    print(f"Done. {changed}/{total} prompts perturbed → {output_path}")
