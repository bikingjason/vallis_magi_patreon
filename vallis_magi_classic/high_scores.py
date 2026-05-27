from dataclasses import dataclass


@dataclass
class HighScore:
    name: str
    score: int
    level: int = 1


def load_high_scores(high_scores_section: list[dict[str, str | int]]) -> list[HighScore]:

    return [
        HighScore(
            name=str(entry.get("name", "")),
            score=int(entry.get("score", 0)),
            level=int(entry.get("level", 1)),
        )
        for entry in high_scores_section
    ]


def display_high_scores(high_scores: list[HighScore]) -> None:
    if not high_scores:
        print("No high scores yet.")
        return

    print("\nHigh Scores")
    print("===========")

    for rank, entry in enumerate(high_scores, start=1):
        print(f"{rank:2}. {entry.name:<20} {entry.score:>8}  Level {entry.level}")

    print("\n")
