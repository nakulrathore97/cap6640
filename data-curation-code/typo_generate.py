import random
import string

ALPHABET = string.ascii_lowercase  # 'abcdefghijklmnopqrstuvwxyz'

def typo_one_word(word: str) -> str:
    """Apply exactly one typo to a word (always corrupts an alphabetic char)."""
    idxs = [i for i, c in enumerate(word) if c.isalpha()]
    if not idxs:
        return word
    i = random.choice(idxs)
    c = word[i].lower()

    # 3 possible types: deletion, substitution with random char, duplication
    op = random.choice(["delete", "neighbor", "repeat"])

    if op == "delete":
        return word[:i] + word[i+1:]

    if op == "repeat":
        return word[:i+1] + word[i] + word[i+1:]

    # neighbor: all 25 other letters are equally likely
    candidates = [ch for ch in ALPHABET if ch != c]
    repl = random.choice(candidates)
    if word[i].isupper():
        repl = repl.upper()
    return word[:i] + repl + word[i+1:]


def perturb_typos(text: str) -> str:
    """Inject exactly one typo into the text by corrupting one randomly chosen word."""
    tokens = text.split(" ")
    eligible = [i for i, w in enumerate(tokens) if any(c.isalpha() for c in w)]
    if not eligible:
        return text
    chosen = random.choice(eligible)
    tokens[chosen] = typo_one_word(tokens[chosen])
    return " ".join(tokens)


if __name__ == "__main__":
    import os

    input_path = os.path.join(os.path.dirname(__file__), "diffusiondb_prompts_small.txt")
    output_path = os.path.join(os.path.dirname(__file__), "diffusiondb_prompts_small_typo.txt")

    with open(input_path, "r", encoding="utf-8") as fin, \
         open(output_path, "w", encoding="utf-8") as fout:
        for line in fin:
            prompt = line.rstrip("\n")
            typo_prompt = perturb_typos(prompt)
            fout.write(typo_prompt + "\n")

    print(f"Done. Typo'd prompts written to {output_path}")
