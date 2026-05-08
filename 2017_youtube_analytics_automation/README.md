# YouTube Analytics Automation

Automated data pipeline for YouTube channel analytics — pulls daily video metrics from the YouTube Data API, computes incremental engagement stats and top-10 rankings in Redshift, and delivers a formatted HTML channel report by email each morning.

```yaml
Role: Data Engineering / Analytics Engineering / Digital Content Analytics
Domain: media / social / digital content
Type: scheduled pipeline + reporting automation
Maturity: production (historical artifact)
Stack: Python, YouTube Data API v3, YouTube Reporting API, pandas, boto3, Redshift, S3, SMTP
Topics: python, etl, api-integration, data-pipeline, analytics-engineering, youtube, redshift, s3, automation, email-reporting
Notes:
  - Originally built and maintained as a production pipeline for a media company; preserved
    here in sanitized form with employer-specific details removed
  - Credentials and channel IDs are loaded from environment variables / .env
  - Not guaranteed to run out-of-the-box due to deprecated dependencies (oauth2client, etc.)
```

---

## Architecture

Three daily jobs run in sequence each morning. An hourly job runs independently.

```
Every 2 hours      ─── Channel Surfing (legacy pipeline; see legacy/)

Hourly             ─── run_recent_video_monitoring.py
                         └─ Data API → filter recent uploads → Redshift

07:40 daily        ─── run_daily_video_metrics.py  (channel_01)
                         └─ Data API → CSV → S3 → Redshift
                       run_daily_top10_and_channel_metrics.py  (channel_01)
                         └─ Redshift temp tables → top-10 + channel activity tables

07:50 daily        ─── same pair for channel_02

08:00 daily        ─── same pair for channel_03

13:59–14:01 daily  ─── run_daily_channel_report.py  (one per channel, staggered)
                         └─ Redshift queries → styled HTML report → email
```

---

## Project Structure

```
youtube_analytics_automation/
│
├── api/
│   ├── data_api.py           # YouTube Data API v3: channel uploads, video metrics,
│   │                         #   recent video search, channel–name–ID mapping
│   └── reporting_api.py      # YouTube Reporting API: job management, bulk CSV download
│                             #   (retained for historical reference; see note in file)
│
├── pipelines/
│   ├── daily_top10_and_channel_metrics.py   # Core pipeline class: computes daily
│   │                                        #   incremental metrics from lifetime snapshots,
│   │                                        #   derives top-10 and channel-level aggregates
│   └── legacy_scraper.py     # Original BeautifulSoup scraper (pre-Data API)
│
├── scripts/
│   ├── run_daily_video_metrics.py           # Pulls lifetime stats from Data API,
│   │                                        #   writes CSV → S3 → Redshift
│   ├── run_daily_top10_and_channel_metrics.py  # Drives the pipeline class above
│   ├── run_daily_channel_report.py          # Queries Redshift, builds styled HTML
│   │                                        #   report, emails to distribution list
│   ├── run_recent_video_monitoring.py       # Hourly: scrapes all channel uploads,
│   │                                        #   filters to past 7 days, loads to Redshift
│   └── templates/
│       └── channel_report.html              # Jinja-style HTML template for the
│                                            #   daily email attachment
│
├── utils/
│   ├── csv.py                # CSV → S3 upload
│   ├── email.py              # simple_email() (plain text) and send_email()
│   │                         #   (HTML, inline images, pandas tables, attachments)
│   ├── redshift.py           # SQLAlchemy connection + DataFrame → Redshift upsert
│   ├── registry.py           # Static channel name → channel ID mapping
│   └── s3.py                 # S3 → Redshift COPY via IAM role
│
├── legacy/
│   └── channel_playlist_pipeline/   # Selenium pipeline that scraped channel/playlist
│                                    #   metadata and maintained a CPV (Channel–Playlist–
│                                    #   Video) table in Redshift; ran every 2 hours
│
└── crontab_backup.txt        # Snapshot of the production cron schedule
```

---

## Daily Pipeline Detail

### 1. Daily Video Metrics (`run_daily_video_metrics.py`)

Hits the Data API for every video in a channel's uploads playlist and records lifetime cumulative stats (views, likes, dislikes, comments) as a dated snapshot. The pattern:

```
Data API → DataFrame → CSV (local) → S3 → Redshift COPY → delete local CSV
```

Run for each channel separately (staggered by 10 minutes in cron to avoid Redshift contention).

### 2. Daily Top-10 and Channel Metrics (`run_daily_top10_and_channel_metrics.py`)

Drives `pipelines/daily_top10_and_channel_metrics.py`. Given two consecutive daily snapshots in Redshift, computes:

- **Incremental daily metrics** per video: `today_lifetime − yesterday_lifetime`
- **Top-10 tables**: ranked by views, likes, dislikes, and comments — separately for all-time videos and for videos published in the past 7 days
- **Channel-level aggregates**: sum of incremental metrics across all videos (and across recent-only videos)

Edge cases handled: videos that go private (negative diff clamped), new videos (yesterday coalesces to 0), and missing scrape dates (assertion check before any inserts).

### 3. Daily Channel Report (`run_daily_channel_report.py`)

Runs after the metrics jobs complete. Queries Redshift for the day's top-10 and 30-day channel view history, then:

- Computes vs-7-day-avg and vs-30-day-avg percentage comparisons
- Renders styled pandas DataFrames (progress bars, comma-formatted numbers) as HTML tables
- Injects tables into `templates/channel_report.html` and saves the rendered file
- Builds a MIME email with inline images (channel logo + YouTube logo) and the HTML report as an attachment
- Sends to a distribution list via SMTP

The channel metrics query uses a hybrid source: the incremental metrics table for the most recent 3 days (where Reporting API data lags), and a longer-history reporting detail table for days 4–30.

### 4. Hourly Recent Video Monitoring (`run_recent_video_monitoring.py`)

Runs at the top of every hour. Fetches current video metrics for all managed channels, filters to uploads from the past 7 days, and appends a timestamped snapshot to Redshift. Used to track view velocity on new content in near-real-time.

The original production version ran as an infinite loop; the cron approach was adopted after a crash caused a multi-day data gap.

---

## Environment Variables

| Variable | Used by | Description |
|---|---|---|
| `REDSHIFT_USER` | all scripts | Redshift username |
| `REDSHIFT_PASSWORD` | all scripts | Redshift password |
| `REDSHIFT_HOST` | all scripts | Redshift cluster endpoint |
| `YOUTUBE_DATABASE` | all scripts | Redshift database name |
| `CLIENT_SECRETS_FILE` | api/ | OAuth 2.0 client secrets (from Google Cloud Console) |
| `DATA_CREDENTIALS_FILE` | data_api.py | Cached OAuth token for Data API |
| `STORAGE_CREDENTIALS_FILE` | reporting_api.py | Cached OAuth token for Reporting API |
| `CONTENT_OWNER_ID` | run_recent_video_monitoring.py | YouTube CMS content owner ID |
| `YOUTUBE_IAM_ROLE` | run_daily_video_metrics.py | IAM role ARN for Redshift S3 COPY |
| `EMAIL_SENDER` | run_daily_channel_report.py | Outbound email address |
| `EMAIL_PASSWORD` | run_daily_channel_report.py | SMTP password |

---

## Legacy Subfolder

`legacy/channel_playlist_pipeline/` is a self-contained earlier pipeline that used Selenium with a headless Chrome driver to scrape YouTube channel pages, maintain a normalized Channel–Playlist–Video (CPV) table in Redshift, and send status emails. It ran every 2 hours in production. See its own [README](legacy/channel_playlist_pipeline/README.md) for detail.

---

## Reporting API Note

`api/reporting_api.py` contains a full wrapper for the YouTube Reporting API (bulk CSV download of channel analytics). It was written to support a reporting backfill workflow but was never wired into the automated cron pipeline — the daily channel report script uses the Data API metrics tables directly for recent data. The file is retained here because the API surface it covers (job management, paginated report listing, chunked CSV streaming) is non-trivial and worth preserving.
