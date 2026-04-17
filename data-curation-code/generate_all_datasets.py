import os
import random
import re
import argparse

# Import base functions
from typo_generate import typo_one_word
from language_discrepancy_generate import LANG_DICTS, _find_candidates
from grammar_generate import ALL_PERTURBATIONS

# Error levels configuration (Low, Med, High)
LOW_ERRORS = 1
MED_ERRORS = 3
HIGH_ERRORS = 5
MAX_ERRORS = max(LOW_ERRORS, MED_ERRORS, HIGH_ERRORS)

def perturb_typo_multi(text: str, k: int) -> str | None:
    """Inject exactly k typos. Returns None if there are fewer than k eligible words."""
    tokens = text.split(" ")
    eligible = [i for i, w in enumerate(tokens) if any(c.isalpha() for c in w)]
    if len(eligible) < k:
        return None
    
    # Randomly pick k distinct indices to corrupt
    chosen_indices = random.sample(eligible, k)
    
    # We apply them in any order since they are distinct indices
    for i in chosen_indices:
        tokens[i] = typo_one_word(tokens[i])
        
    return " ".join(tokens)


def perturb_language_multi(text: str, k: int, lang: str | None = None) -> str | None:
    """Inject exactly k language discrepancy substitutions."""
    if lang is None:
        lang = random.choice(list(LANG_DICTS.keys()))
    translation_dict = LANG_DICTS[lang]
    
    # We must do this sequentially because translating changes string length 
    # and invalidates indices, and also changes the word itself so it won't be matched again.
    current_text = text
    for _ in range(k):
        candidates = _find_candidates(current_text, translation_dict)
        if not candidates:
            return None # Couldn't do k substitutions
            
        m = random.choice(candidates)
        en_word = m.group(0)
        foreign = translation_dict[en_word.lower()]
        if en_word[0].isupper() and len(foreign) > 0:
            foreign = foreign[0].upper() + foreign[1:]
            
        current_text = current_text[:m.start()] + foreign + current_text[m.end():]
        
    return current_text


def perturb_grammar_multi(text: str, k: int) -> str | None:
    """Inject exactly k grammar errors."""
    current_text = text
    for _ in range(k):
        # We need to make sure we don't just pick something that does nothing.
        # Note: if the text gets too short, fallback will just fail.
        order = list(ALL_PERTURBATIONS)
        random.shuffle(order)
        perturbed = False
        for fn in order:
            result = fn(current_text)
            if result is not None and result != current_text:
                current_text = result
                perturbed = True
                break
        if not perturbed:
            return None
    return current_text


def is_eligible(prompt: str) -> bool:
    """Fast check to see if a prompt is even worth attempting."""
    # Check word count
    words = prompt.split()
    if len(words) < MAX_ERRORS:
        return False
        
    # Check translatable words
    # A prompt must be translatable to *some* language at least MAX_ERRORS times.
    es_dict = LANG_DICTS["spanish"]
    fr_dict = LANG_DICTS["french"]
    es_cands = _find_candidates(prompt, es_dict)
    fr_cands = _find_candidates(prompt, fr_dict)
    if len(es_cands) < MAX_ERRORS and len(fr_cands) < MAX_ERRORS:
        return False
        
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate datasets with varying error levels.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--n-samples", type=int, default=200, help="Number of valid prompts to randomly select")
    args = parser.parse_args()

    # Set the random seed to ensure reproducible selection and perturbations
    random.seed(args.seed)

    input_path = os.path.join(os.path.dirname(__file__), "diffusiondb_prompts.txt")
    
    # Output file paths
    # Control
    control_out = os.path.join(os.path.dirname(__file__), "control.txt")
    
    # Typos
    typo_1_out = os.path.join(os.path.dirname(__file__), "typo_low.txt")
    typo_4_out = os.path.join(os.path.dirname(__file__), "typo_med.txt")
    typo_10_out = os.path.join(os.path.dirname(__file__), "typo_high.txt")
    
    # Lang
    lang_1_out = os.path.join(os.path.dirname(__file__), "language_discrepancy_low.txt")
    lang_4_out = os.path.join(os.path.dirname(__file__), "language_discrepancy_med.txt")
    lang_10_out = os.path.join(os.path.dirname(__file__), "language_discrepancy_high.txt")
    
    # Grammar
    grammar_1_out = os.path.join(os.path.dirname(__file__), "grammar_low.txt")
    grammar_4_out = os.path.join(os.path.dirname(__file__), "grammar_med.txt")
    grammar_10_out = os.path.join(os.path.dirname(__file__), "grammar_high.txt")

    TARGET_COUNT = args.n_samples
    collected = 0
    
    # We will buffer outputs so we can write them all at once at the end
    # or write line by line. We'll write line-by-line as we collect.
    
    try:
        fc = open(control_out, "w", encoding="utf-8")
        ft1 = open(typo_1_out, "w", encoding="utf-8")
        ft4 = open(typo_4_out, "w", encoding="utf-8")
        ft10 = open(typo_10_out, "w", encoding="utf-8")
        fl1 = open(lang_1_out, "w", encoding="utf-8")
        fl4 = open(lang_4_out, "w", encoding="utf-8")
        fl10 = open(lang_10_out, "w", encoding="utf-8")
        fg1 = open(grammar_1_out, "w", encoding="utf-8")
        fg4 = open(grammar_4_out, "w", encoding="utf-8")
        fg10 = open(grammar_10_out, "w", encoding="utf-8")
        
        with open(input_path, "r", encoding="utf-8") as fin:
            all_lines = fin.readlines()

        # Shuffle the lines to randomly select prompts
        random.shuffle(all_lines)

        for line_idx, line in enumerate(all_lines):
            prompt = line.rstrip("\n")
            
            # Check basic eligibility (length >= 10, >= 10 foreign candidates)
            if not is_eligible(prompt):
                continue
                
            # Now try to actually do the generation
            t1 = perturb_typo_multi(prompt, LOW_ERRORS)
            t4 = perturb_typo_multi(prompt, MED_ERRORS)
            t10 = perturb_typo_multi(prompt, HIGH_ERRORS)
            if not all([t1, t4, t10]): continue
            
            # Fix language to one randomly chosen for this prompt consistency
            lang = random.choice(["spanish", "french"])
            l1 = perturb_language_multi(prompt, LOW_ERRORS, lang)
            l4 = perturb_language_multi(prompt, MED_ERRORS, lang)
            l10 = perturb_language_multi(prompt, HIGH_ERRORS, lang)
            if not all([l1, l4, l10]): continue
            
            g1 = perturb_grammar_multi(prompt, LOW_ERRORS)
            g4 = perturb_grammar_multi(prompt, MED_ERRORS)
            g10 = perturb_grammar_multi(prompt, HIGH_ERRORS)
            if not all([g1, g4, g10]): continue
            
            # If we get here, all variants successfully generated!
            fc.write(prompt + "\n")
            
            ft1.write(t1 + "\n")
            ft4.write(t4 + "\n")
            ft10.write(t10 + "\n")
            
            fl1.write(l1 + "\n")
            fl4.write(l4 + "\n")
            fl10.write(l10 + "\n")
            
            fg1.write(g1 + "\n")
            fg4.write(g4 + "\n")
            fg10.write(g10 + "\n")
            
            collected += 1
            if collected >= TARGET_COUNT:
                break

        print(f"Dataset generation complete! Collected {collected} valid prompts across all 10 datasets.")

    finally:
        # Close all files
        for f in [fc, ft1, ft4, ft10, fl1, fl4, fl10, fg1, fg4, fg10]:
            f.close()
