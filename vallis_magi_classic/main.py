from .config import get_arguments, save_config


def main() -> None:
    config, _ = get_arguments()  # Don't need high_scores yet.
    if config.score:
        return

    save_config(config)


if __name__ == "__main__":
    main()
