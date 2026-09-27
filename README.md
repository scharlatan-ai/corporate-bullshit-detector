# Corporate Bullshit Detector

> Probabilistic corporate fog detection for LinkedIn, startup hype, executive vision posts, and other professional nonsense.

The **Corporate Bullshit Detector** is a small experimental AI/ML project for analyzing English-language corporate and professional social-media communication, especially LinkedIn posts.

Instead of asking a language model a single question like _"Is this bullshit?"_, the detector evaluates several observable characteristics independently and combines them into a transparent **Corporate Bullshit Score from 0 to 100**.

Built for [scharlatan.ai](https://scharlatan.ai).

---

## What does it detect?

The detector estimates four separate dimensions:

### Buzzword Saturation

How strongly the text relies on trendy business, technology, startup, consulting, or marketing buzzwords, especially when several are stacked or used ornamentally.

### Vagueness

How strongly vague or generic language dominates the text instead of clearly explaining what is actually being done, offered, changed, or achieved.

### Grandiosity

How strongly the text makes exaggerated claims about its importance, novelty, capabilities, impact, or future consequences.

### Concrete Information

How much specific information the text contains about what happened, what was built, how something works, or what measurable result was achieved.

The first three dimensions increase the bullshit signal.

Concrete information acts as a counter-signal.

---

## How it works

The detector uses **Jev** to estimate a probability between `0` and `1` for each of the four dimensions.

The positive bullshit signal is:

\[
H = 0.30B + 0.40V + 0.30G
\]

where:

- `B` = Buzzword Saturation
- `V` = Vagueness
- `G` = Grandiosity

Concrete information then discounts that signal:

\[
S = H(1 - 0.45C)
\]

where:

- `C` = Concrete Information

The final user-facing score is:

\[
Corporate\ Bullshit\ Score = round(S \times 100)
\]

This **Evidence Discount** approach was chosen because concrete information reduces an existing bullshit signal proportionally instead of simply subtracting from it.

A technical or informative marketing post can therefore contain buzzwords without automatically being condemned to corporate hell.

The weights are heuristic and deliberately **not fitted to the evaluation dataset**.

---

## Score Levels

| Score | Verdict | Meaning |
|---:|---|---|
| **0–29** | **Looks Fine** | Mostly straightforward communication with enough concrete substance to keep the corporate fog under control. |
| **30–49** | **Hmm... Suspicious** | Some corporate fog is creeping in, but there is still enough substance to give it the benefit of the doubt. |
| **50–69** | **Getting Bullshitty** | Hype, vagueness, or inflated claims are starting to outweigh the useful information. |
| **70–100** | **Yep, That's Bullshit** | Corporate rhetoric is doing considerably more work than the actual substance. |

The score is an **experimental index**, not a calibrated probability that a text is objectively bullshit.

---

## CLI

The easiest way to use the detector is the included Python CLI.

```bash
uv run python bullshit.py "We are unlocking unprecedented synergies through a category-defining AI ecosystem."