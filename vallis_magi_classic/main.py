from .config import get_arguments, save_config


def main() -> None:
    config = get_arguments()

    save_config(config)


if __name__ == "__main__":
    main()
