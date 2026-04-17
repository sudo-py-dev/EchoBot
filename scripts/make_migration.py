import sys
import subprocess
from loguru import logger


def make_migration(message: str = "auto_migration"):
    """
    Convenience script to generate a new Alembic migration based on model changes.
    """
    try:
        logger.info(f"Generating migration: {message}...")
        cmd = ["uv", "run", "alembic", "revision", "--autogenerate", "-m", message]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("✅ Migration generated successfully!")
            print(result.stdout)
        else:
            logger.error(f"❌ Migration generation failed:\n{result.stderr}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "auto_migration"
    make_migration(msg)
