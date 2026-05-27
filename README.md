# 🏆 My Sports Central

> A multi-sport bot that monitors live scores and automatically posts updates — covering basketball, MMA, and more.

## 🚧 Status
Project under active development.

## Sports Covered
| Sport | League | Status |
|-------|--------|--------|
| 🏀 Basketball | NBA | ✅ Active |
| 🥊 MMA | UFC | 🚧 Coming soon |

## Tech Stack
- Python 3.11+
- [nba_api](https://github.com/swar/nba_api) — NBA live data
- [tweepy](https://www.tweepy.org/) — Twitter/X API
- [APScheduler](https://apscheduler.readthedocs.io/) — job scheduling
- [python-dotenv](https://pypi.org/project/python-dotenv/) — environment variables

## Setup

1. Clone the repo
```bash
   git clone https://github.com/seu-usuario/my-sports-central.git
   cd my-sports-central
```
2. Install dependencies
```bash
   pip install -r requirements.txt
```
3. Configure environment variables
```bash
   cp .env.example .env
   # Edit .env with your API keys
```
4. Run the bot
```bash
   python main.py
```

## Roadmap
- [x] Project structure
- [x] NBA live score fetching
- [x] Tweet formatter with scores and top scorers
- [ ] Auto-posting (platform TBD)
- [ ] Scheduling — post every X minutes during live games
- [ ] MMA live updates
- [ ] Post-game summaries

## License
MIT