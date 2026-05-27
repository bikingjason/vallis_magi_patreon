import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path

import tomli_w


@dataclass
class HighScore:
    name: str
    score: int
    level: int = 1


class HighScoresManager:
    def __init__(self, working_dir: Path, high_scores_dir: str, high_scores_file_name: str, max_scores: int) -> None:
        super().__init__()
        self.working_dir = working_dir
        self.file_path = Path(working_dir / high_scores_dir / high_scores_file_name)
        self.max_scores = max_scores
        self.high_scores: list[HighScore] = []

    def normalise_high_scores(self) -> None:
        self.high_scores = sorted(
            self.high_scores,
            key=lambda entry: entry.score,
            reverse=True,
        )[: self.max_scores]

    def load_high_scores(self) -> None:
        if not self.file_path.exists():
            print(f"\nConfig: {self.file_path} not found, using default config.\n")
            return

        with self.file_path.open("rb") as f:
            data = tomllib.load(f)

        high_scores_section = data.get("high_scores", [])

        self.high_scores = [
            HighScore(
                name=str(entry.get("name", "")),
                score=int(entry.get("score", 0)),
                level=int(entry.get("level", 1)),
            )
            for entry in high_scores_section
        ]

        self.normalise_high_scores()

    def save_high_scores(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        self.normalise_high_scores()

        data = {
            "high_scores": [asdict(entry) for entry in self.high_scores],
        }

        with self.file_path.open("wb") as f:
            tomli_w.dump(data, f)

    def add_high_score(self, new_score: HighScore) -> None:
        self.high_scores.append(new_score)
        self.normalise_high_scores()

    def display_high_scores(self) -> None:
        if not self.high_scores:
            print("No high scores yet.")
            return

        print("\nHigh Scores")
        print("===========")

        for rank, entry in enumerate(self.high_scores, start=1):
            print(f"{rank:2}. {entry.name:<20} {entry.score:>8}  Level {entry.level}")

        print("\n")
