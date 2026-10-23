"""Database commands: python -m app.cli"""

from app.db.session import init_db
from app.logging_config import configure_logging


def main() -> None:
    configure_logging()
    init_db(seed=True)
    print("Database initialized and synthetic demo data seeded.")


if __name__ == "__main__":
    main()
