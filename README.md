# EchoBot - Telegram Channel Forwarder

High-performance Telegram bot for mirroring content across channels with **automated translation**, **custom signatures**, and **multi-language support**.

## Features

- **Channel Mirroring**: Automatically forward posts from source channels to up to 3 destinations
- **Real-time Translation**: Translate messages using Google Translate (30+ languages supported)
- **Custom Signatures**: Add branded credits to all forwarded messages
- **Donation System**: Integrated Telegram Stars payments + external donation links
- **Multi-language UI**: 28 languages supported for bot interface
- **Plugin Architecture**: Modular, auto-discovery plugin system
- **Admin Dashboard**: Web-like callback-driven UI for managing channels
- **Performance Optimized**: Async caching layer and SQLAlchemy 2.0 database

## Commands

| Command | Description | Context |
|---------|-------------|---------|
| `/start` | Open user dashboard | Private chat |
| `/settings` | Configure channel (must be sent in channel) | Channel/Group |
| `/about` | Show bot info and tech stack | Any |
| `/donate` / `/support` | Support the project via Stars or external links | Private chat |
| `/cancel` | Cancel current operation | Any |

## Architecture

```
EchoBot/
├── main.py                 # Application entry point
├── config.py               # Environment configuration
├── plugins/                # Auto-discovered plugins
│   ├── admin_panel/        # Channel management UI
│   ├── bot/                # Core bot commands (/about, etc.)
│   ├── donate.py           # Donation handlers
│   ├── forward/            # Message forwarding logic
│   ├── middleware/         # Rate limiting & logging
│   └── user_panel/         # User dashboard
├── db/
│   ├── engine.py           # Async DB engine with migrations
│   ├── models/             # SQLAlchemy ORM models
│   └── repos/              # Repository pattern
├── locales/                # 28 translation files (JSON)
├── custom_filters/         # Pyrogram custom filters
└── utils/
    ├── cache.py            # Async TTL cache implementation
    ├── i18n.py             # Internationalization utilities
    ├── translator.py       # Translation service wrapper
    └── ui.py               # UI component builders
```

## Installation

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- Telegram API credentials ([my.telegram.org](https://my.telegram.org))

### Setup

1. Clone the repository:
```bash
git clone https://github.com/sudo-py-dev/EchoBot.git
cd EchoBot
```

2. Install dependencies:
```bash
uv sync
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Run database migrations:
```bash
uv run alembic upgrade head
```

5. Start the bot:
```bash
uv run python main.py
```

### Deployment with Docker

EchoBot follows a professional multi-stage Docker pattern for efficient and secure production deployment.

#### 1. Build and Run with Docker Compose (Recommended)

1. Make sure your `.env` file is configured.
2. Build and start the services:
```bash
docker compose up -d --build
```
3. Check logs:
```bash
docker compose logs -f bot
```

#### 2. Persistence and Security
- **Volumes**: Data is persisted in `./data`, `./sessions`, and `./logs` on the host.
- **Security**: The container runs as a non-privileged `bot` user with a read-only root filesystem.
- **Database Support**: EchoBot supports both SQLite and PostgreSQL.
  - **SQLite (Default)**: Uses the `/app/data/bot.db` file. No extra setup required.
  - **PostgreSQL**: uncomment the `db` service in `docker-compose.yml` and set your `DATABASE_URL` in `.env`. The bot will automatically use the high-performance `asyncpg` driver.

## Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `API_ID` | Telegram API ID from my.telegram.org | `123456` |
| `API_HASH` | Telegram API Hash | `abc123...` |
| `BOT_TOKEN` | Bot token from @BotFather | `123456:ABC-DEF...` |
| `OWNER_IDS` | Comma-separated admin user IDs | `123456789,987654321` |
| `DATABASE_URL` | Database connection string | `postgresql://user:pass@db:5432/db` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///bot.db` |
| `CACHE_TTL` | Cache time-to-live (seconds) | `300` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, etc.) | `INFO` |
| `SUPPORT_URL` | Buy Me a Coffee link | - |
| `GITHUB_SPONSORS_URL` | GitHub Sponsors link | - |

### Example `.env` file

```env
API_ID=123456
API_HASH=your_api_hash_here
BOT_TOKEN=123456:your_bot_token_here
OWNER_IDS=123456789
ADMIN_IDS=123456789
DATABASE_URL=sqlite+aiosqlite:///bot.db?timeout=20
CACHE_TTL=300
SUPPORT_URL=https://buymeacoffee.com/yourname
GITHUB_SPONSORS_URL=https://github.com/sponsors/yourname
```

## Usage Guide

### Adding a Channel

1. Add the bot to your source channel as **Administrator** with "Post Messages" permission
2. Send any message in the channel
3. The bot will auto-detect it - use `/settings` in the channel to configure

### Setting Up Forwarding

1. Go to **Mirroring Setup** in the channel settings
2. Click **Add Destination** and select a target channel (must also be admin there)
3. Optionally enable translation and select target language

### Supporting the Project

Users can donate via:
- **Telegram Stars**: In-app payment (50, 250, or 500 Stars)
- **Buy Me a Coffee**: External link
- **GitHub Sponsors**: External link

Configure donation URLs in your `.env` file.

## Tech Stack

| Component | Technology |
|-----------|------------|
| **MTProto Client** | [Kurigram](https://github.com/KurimuzonAkuma/kurigram) (Pyrogram fork) |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Database** | SQLite (default) / PostgreSQL |
| **Migrations** | Alembic |
| **Translation** | deep-translator (Google Translate) |
| **Package Manager** | uv |
| **Code Quality** | Ruff (linting & formatting) |

## Development

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run ruff format
uv run ruff check --fix
```

### Managing Translations

```bash
# Sync translations across all locale files
uv run python scripts/translate_locales.py

# Sort translation keys
uv run python scripts/translate_locales.py --sort
```

## License

MIT © [License](LICENSE)
[sudo-py-dev](https://github.com/sudo-py-dev)
