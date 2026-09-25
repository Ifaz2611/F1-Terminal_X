"""Questionary fallback for f1 --interactive."""

from __future__ import annotations

from typing import Optional

from f1_terminal.config import get_logger

logger = get_logger(__name__)

try:
    import questionary

    HAS_QUESTIONARY = True
except ImportError:
    HAS_QUESTIONARY = False


def _fallback_input(choices, prompt: str) -> str:
    print(f"\n{prompt}")
    for i, (title, _) in enumerate(choices, 1):
        print(f"  {i}. {title}")
    while True:
        try:
            idx = int(input("Enter number: ").strip()) - 1
            if 0 <= idx < len(choices):
                return choices[idx][1]
            print("Invalid selection. Try again.")
        except ValueError:
            print("Please enter a valid number.")


def interactive_flow() -> None:
    """Launch interactive questionary flow (legacy behavior)."""
    print("\n F1 Terminal X — Interactive Mode")
    print("=" * 50)

    # Simple chooser: advanced / qualifying / practice
    choices = [
        ("Advanced Visualizer (Race session)", "advanced"),
        ("Qualifying Comparison", "qualifying"),
        ("Practice Session", "practice"),
        ("Exit", "exit"),
    ]

    if HAS_QUESTIONARY:
        picked = questionary.select("Select analysis:", choices=[questionary.Choice(title=t, value=v) for t, v in choices]).ask()
    else:
        picked = _fallback_input(choices, "Select analysis:")

    if picked is None or picked == "exit":
        print("Goodbye!")
        return

    # Dispatch to legacy interactive mains without import side-effects?
    # We lazily import
    if picked == "advanced":
        from f1_terminal.f1_advanced_visualizer import main as adv_main

        adv_main()
    elif picked == "qualifying":
        from f1_terminal.f1_qualifying import main as quali_main

        quali_main()
    elif picked == "practice":
        from f1_terminal.PracticeSession import main as prac_main

        prac_main()
