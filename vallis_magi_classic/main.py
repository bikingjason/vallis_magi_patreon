from .config import display_config, get_arguments
from .high_scores import display_high_scores


def main() -> None:
    config, high_scores = get_arguments()  # Don't need high_scores yet.

    if config.scores:
        display_high_scores(high_scores)
        return

    display_config(config)


if __name__ == "__main__":
    main()
