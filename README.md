# LinkedIn Easy Apply Bot

Automate the LinkedIn "Easy Apply" workflow using Selenium. The bot logs in to
LinkedIn, performs a job search based on your keywords, and attempts to submit
"Easy Apply" applications for matching postings.

> ⚠️ Use this project responsibly and at your own risk. Automated access to
> LinkedIn may violate their terms of service. Ensure you have permission to use
> automation tools before running this bot.

## Features

- Headless-capable Selenium automation for LinkedIn Easy Apply
- Command-line interface with environment variable support for credentials
- Skips multi-step applications to avoid submitting incomplete information
- Customizable maximum number of applications per run

## Requirements

- Python 3.10+
- Google Chrome and the matching ChromeDriver binary available in your `PATH`
- Selenium (install via `pip install -r requirements.txt`)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Set your LinkedIn credentials via environment variables or command-line
arguments. Then run the bot with your desired search keywords.

```bash
export LINKEDIN_USERNAME="your_email@example.com"
export LINKEDIN_PASSWORD="your_secure_password"
python main.py "python developer" --location "United States" --max-applications 5 --headless
```

### Command-line options

- `keywords` (positional): keywords used in the job search query
- `--location`: optional location filter
- `--experience`: zero or more LinkedIn experience level codes (e.g., `2` for entry level)
- `--max-applications`: limit the number of applications per run (default 10)
- `--headless`: run Chrome in headless mode
- `--username` / `--password`: override environment variables for credentials
- `--log-level`: adjust verbosity (default `INFO`)

## How it works

1. Launches a Selenium-controlled Chrome browser
2. Logs into LinkedIn using provided credentials
3. Navigates to the jobs search page with Easy Apply filter enabled
4. Iterates through job postings and opens each listing
5. Attempts to submit the Easy Apply form; skips postings requiring manual input

## Disclaimer

This tool is provided for educational purposes. LinkedIn regularly updates its
UI and anti-automation measures, so the bot may require adjustments over time.
Always respect the platform's policies and consider the ethical implications of
automated job applications.
