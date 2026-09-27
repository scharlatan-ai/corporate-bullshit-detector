import argparse
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence

from dotenv import load_dotenv
from typesafe_sdk import Noul, TypeSafeClient


BUZZWORD_WEIGHT = 0.30
VAGUENESS_WEIGHT = 0.40
GRANDIOSITY_WEIGHT = 0.30
CONCRETE_LAMBDA = 0.45

DECISION_QUESTIONS = {
    "buzzword_saturation": (
        "How likely is it that this text contains a noticeable concentration of trendy "
        "business, technology, startup, consulting, or marketing buzzwords, especially when "
        "several are stacked or used ornamentally?"
    ),
    "vagueness": (
        "How likely is it that vague or generic language materially dominates the text, even "
        "if some concrete details are also present? Do not treat brevity or missing external "
        "context alone as vagueness."
    ),
    "grandiosity": (
        "How likely is it that the overall text makes clearly exaggerated or grandiose claims "
        "whose stated importance, novelty, capabilities, impact, or future consequences are "
        "substantially disproportionate to what the text itself describes or supports? "
        "Individual promotional words, superlatives, or large numbers alone should not be "
        "sufficient."
    ),
    "concrete_information": (
        "How likely is it that this text contains specific, concrete information about what "
        "happened, what was built, how something works, or what measurable result was achieved?"
    ),
}


@dataclass
class DecisionResult:
    buzzword_saturation: float
    vagueness: float
    grandiosity: float
    concrete_information: float

    def __post_init__(self) -> None:
        probabilities = (
            self.buzzword_saturation,
            self.vagueness,
            self.grandiosity,
            self.concrete_information,
        )
        if any(not 0.0 <= probability <= 1.0 for probability in probabilities):
            raise ValueError("Probabilities must be between 0.0 and 1.0.")


class DecisionProvider(ABC):
    @abstractmethod
    def analyze(self, text: str) -> DecisionResult:
        ...


class JevProvider(DecisionProvider):
    def __init__(self, mode: str = "openrouter") -> None:
        if mode not in {"openrouter", "native"}:
            raise ValueError("mode must be either 'openrouter' or 'native'")

        if mode == "openrouter":
            self.client = TypeSafeClient(
                api_key=os.environ["OPENROUTER_API_KEY"],
                base_url="https://openrouter.ai/api",
                model="~typesafe/jev-latest",
            )
        else:
            self.client = TypeSafeClient(api_key=os.environ["TYPESAFE_API_KEY"])

        self.questions = {
            name: Noul(instructions=question)
            for name, question in DECISION_QUESTIONS.items()
        }

    def analyze(self, text: str) -> DecisionResult:
        response = self.client.system_one(text, self.questions)
        return DecisionResult(
            buzzword_saturation=response.nouls["buzzword_saturation"].noul,
            vagueness=response.nouls["vagueness"].noul,
            grandiosity=response.nouls["grandiosity"].noul,
            concrete_information=response.nouls["concrete_information"].noul,
        )


def _weighted_positive_signal(result: DecisionResult) -> float:
    return (
        BUZZWORD_WEIGHT * result.buzzword_saturation
        + VAGUENESS_WEIGHT * result.vagueness
        + GRANDIOSITY_WEIGHT * result.grandiosity
    )


def bullshit_score_evidence_discount(result: DecisionResult) -> float:
    score = _weighted_positive_signal(result) * (
        1 - CONCRETE_LAMBDA * result.concrete_information
    )
    return min(1.0, max(0.0, score))


@dataclass
class BullshitVerdict:
    bullshit_score: int
    level: str
    color: str
    explanation: str


def interpret_bullshit_score(raw_score: float) -> BullshitVerdict:
    if not 0.0 <= raw_score <= 1.0:
        raise ValueError("raw_score must be between 0.0 and 1.0.")

    bullshit_score = round(raw_score * 100)

    if bullshit_score <= 29:
        level = "Looks Fine"
        color = "green"
        explanation = (
            "Mostly straightforward communication with enough concrete substance to keep "
            "the corporate fog under control."
        )
    elif bullshit_score <= 49:
        level = "Hmm... Suspicious"
        color = "yellow"
        explanation = (
            "Some corporate fog is creeping in, but there is still enough substance to give "
            "it the benefit of the doubt."
        )
    elif bullshit_score <= 69:
        level = "Getting Bullshitty"
        color = "orange"
        explanation = (
            "Hype, vagueness, or inflated claims are starting to outweigh the useful information."
        )
    else:
        level = "Yep, That's Bullshit"
        color = "red"
        explanation = (
            "Corporate rhetoric is doing considerably more work than the actual substance."
        )

    return BullshitVerdict(bullshit_score, level, color, explanation)


def analyze_corporate_text(
    text: str, provider: DecisionProvider
) -> BullshitVerdict:
    decision = provider.analyze(text)
    raw_score = bullshit_score_evidence_discount(decision)
    return interpret_bullshit_score(raw_score)


def print_bullshit_verdict(verdict: BullshitVerdict) -> None:
    ansi_colors = {
        "green": "\033[32m",
        "yellow": "\033[33m",
        "orange": "\033[93m",
        "red": "\033[31m",
    }
    reset = "\033[0m"
    color = ansi_colors[verdict.color]

    print("Corporate Bullshit Detector™")
    print()
    print(f"Bullshit Score: {verdict.bullshit_score}/100")
    print(f"{color}{verdict.level}{reset}")
    print()
    print(verdict.explanation)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze corporate text with the Corporate Bullshit Detector™."
    )
    parser.add_argument("text", help="Corporate or professional text to analyze.")
    parser.add_argument(
        "--mode",
        choices=("openrouter", "native"),
        default="openrouter",
        help="Jev API provider mode (default: openrouter).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.text.strip():
        parser.error("text must not be empty")

    api_key_name = (
        "OPENROUTER_API_KEY" if args.mode == "openrouter" else "TYPESAFE_API_KEY"
    )
    if not os.getenv(api_key_name):
        parser.error(f"{api_key_name} is not set")

    provider = JevProvider(mode=args.mode)
    verdict = analyze_corporate_text(args.text, provider)
    print_bullshit_verdict(verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
