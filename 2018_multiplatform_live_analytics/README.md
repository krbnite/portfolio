---
project: multiplatform_live_analytics
language: python
tags: facebook graph-api youtube periscope twitter selenium redshift pandas conviva okta
timeline: 2017-2018
---

# Multiplatform Live Event Analytics

A real-time data pipeline that collects audience metrics from six platforms simultaneously during a live streaming event, and writes the aggregated results into a Redshift reporting table row.

## Architecture

```
                           Live Event
                               |
        +----------+-----------+----------+------------+
        |          |           |          |            |
   [Facebook]  [YouTube]  [Twitter/   [Redshift queries              ]
        |          |      Periscope]  [App] [DotCom] [Network]
    Sentinel   Selenium    Selenium    GA   Conviva   Conviva
    (token)   (Okta SSO)  (Periscope RT   RT plays   RT concurrents)
        |          |           |          |            |
        +----------+-----------+----------+------------+
                                    |
                            [Redshift row]
```

**Execution flow:**
1. Facebook sentinel monitors the live stream until it transitions to VOD
2. After a configurable delay (default 10 min), fetches video insights from the Graph API
3. In parallel (after FB), YouTube Selenium downloads the live event CSV via Okta SSO
4. Twitter/Periscope Selenium scrapes live viewer count from Periscope analytics
5. App, DotCom, and Network metrics are queried from Redshift (Conviva real-time + GA)
6. Each platform's metrics are written directly into the event's Redshift row

The Facebook sentinel is the pipeline's synchronization mechanism: it detects when the stream ends and gates the collection of all other platforms that need `end_time`.

## Project Structure

```
multiplatform_live_analytics/
├── run_live_report.py      # Main entry point: full 6-platform pipeline
├── platforms/
│   ├── facebook.py         # fb_token class, sentinel, video insights
│   ├── youtube.py          # Selenium CSV download + CSV parser
│   ├── twitter.py          # Selenium Periscope scraper
│   ├── app.py              # GA real-time second screen viewer peak
│   ├── dotcom.py           # Conviva real-time web video plays
│   ├── network.py          # Conviva real-time streaming network concurrents
│   └── jwplayer.py         # [deprecated] JW Player Selenium scraper (superseded by dotcom.py)
├── utils/
│   ├── redshift.py         # SQLAlchemy connection helper
│   └── driver.py           # Selenium Chrome/PhantomJS driver factory
├── sql/
│   └── live_vod_dashboard.sql  # Tableau dashboard query (live + VOD)
└── notes/
    ├── action_items.md
    ├── jwplayer_notes.md
    └── selenium_notes.md
```

## Platforms

### Facebook (`platforms/facebook.py`)

- `fb_token` class: Selenium login to the Graph API Explorer → user token → page token map
  - `.change_token_by_id()` / `.change_token_by_name()` to switch active page
  - `.change_version()` to change Graph API version (default: v2.12)
- `sentinel()`: polls `live_views` every 60s until the stream ends or a hard cutoff time is reached
- `get_video_insights()`: fetches video-level metrics after the stream ends
- Collected: `fb_total_3s_views`, `fb_total_view_time_minutes`, `fb_id`

### YouTube (`platforms/youtube.py`)

- Selenium + Okta SSO: logs into YouTube Analytics, navigates to completed live events, downloads the CSV for the most recent event matching a filter word
- CSV parser: extracts global playbacks, playback minutes, and US playbacks from the downloaded file
- Collected: `yt_live_playbacks`, `yt_live_playbacks_us`, `yt_live_playbacks_percent_us`, `yt_live_playback_minutes`, `yt_id`

### Twitter / Periscope (`platforms/twitter.py`)

- Selenium: logs into Periscope analytics via Twitter OAuth, exports the analytics CSV
- Collected: `twt_live_viewers` (peak live viewer count)

### App (`platforms/app.py`)

- Queries two Redshift tables (`busgrp.ga_real_time_second_screen_viewers` and `..._snapshot`) for the maximum concurrent active app users within the event window
- Collected: `app_metric`

### DotCom (`platforms/dotcom.py`)

- Queries `dwh_read_write.conviva_realtime` for web video plays during the event window
- `account_name` and `filter_id` parameters identify the Conviva account/filter configuration
- Collected: `dotcom_plays`, `dotcom_plays_us`

### Network (`platforms/network.py`)

- Queries `dwh_read_write.conviva_realtime` for streaming network max concurrent viewers
- Also includes `get_live_minutes()`, `get_live_vod_global()`, `get_live_vod_us()` for VOD analysis
- Collected: `network_max_concurrents`, `network_max_concurrents_us`

## Output Table Schema

The pipeline writes one row per event into a Redshift table (`busgrp.content_kickoff_report_live` by default):

| Column | Source |
|---|---|
| `event_name` | CLI arg |
| `event_date` | CLI arg |
| `start_time` | CLI arg |
| `end_time` | CLI arg or FB sentinel |
| `brand` | CLI arg (ppv / nxt / hof / specialty / now / other) |
| `fb_total_3s_views` | Facebook Graph API |
| `fb_total_view_time_minutes` | Facebook Graph API |
| `fb_id` | Facebook Graph API |
| `yt_live_playbacks` | YouTube Analytics CSV |
| `yt_live_playbacks_us` | YouTube Analytics CSV |
| `yt_live_playbacks_percent_us` | Derived |
| `yt_live_playback_minutes` | YouTube Analytics CSV |
| `yt_id` | YouTube Analytics CSV |
| `twt_live_viewers` | Periscope Analytics CSV |
| `dotcom_plays` | Conviva real-time (Redshift) |
| `dotcom_plays_us` | Conviva real-time (Redshift) |
| `app_metric` | GA real-time (Redshift) |
| `network_max_concurrents` | Conviva real-time (Redshift) |
| `network_max_concurrents_us` | Conviva real-time (Redshift) |

## Environment Variables

Store in a `.env` file (gitignored). Scripts load via `python-dotenv`.

| Variable | Description |
|---|---|
| `FB_USERNAME` | Facebook login email |
| `FB_PASSWORD` | Facebook login password |
| `OKTA_USERNAME` | Okta / YouTube SSO email |
| `OKTA_PASSWORD` | Okta / YouTube SSO password |
| `TWITTER_USERNAME` | Twitter / Periscope username |
| `TWITTER_PASSWORD` | Twitter / Periscope password |
| `REDSHIFT_USER` | Redshift username (prod) |
| `REDSHIFT_PASSWORD` | Redshift password (prod) |
| `REDSHIFT_HOST` | Redshift cluster endpoint (prod) |
| `REDSHIFT_DB` | Redshift database name (prod) |
| `REDSHIFT_DEV_USER` | Redshift username (dev) |
| `REDSHIFT_DEV_PASSWORD` | Redshift password (dev) |
| `REDSHIFT_DEV_HOST` | Redshift cluster endpoint (dev) |
| `REDSHIFT_DEV_DB` | Redshift database name (dev) |

## Usage

```bash
# Test run (writes to *_test table)
python run_live_report.py "Summer Slam Kickoff" ppv 2018-08-19 19:00:00 \
    --end-time 19:59:59 \
    --facebook-page-id <page_id>

# Production run
python run_live_report.py "Summer Slam Kickoff" ppv 2018-08-19 19:00:00 \
    --end-time 19:59:59 \
    --facebook-page-id <page_id> \
    --not-a-test

# Skip platforms as needed
python run_live_report.py "NXT Takeover" nxt 2018-08-18 19:00:00 \
    --no-twitter --no-app --no-network \
    --facebook-page-id <page_id>

# If event is not on Facebook (no sentinel available)
python run_live_report.py "Special Event" specialty 2018-04-02 19:00:00 \
    --end-time 19:59:59 \
    --no-facebook
```

## Notable Design Decisions

**Try/except per platform**: Each platform's collection block is independently wrapped so that one platform failure doesn't abort the others. The exception is the Facebook sentinel — if it crashes, the pipeline asserts False because DotCom/App/Network have no other way to get `end_time`.

**Sentinel as synchronization mechanism**: Facebook is the only platform where data must be collected within a short window after stream end (~10 minutes). The sentinel gates all other platforms on `end_time`, which is either pre-specified via `--end-time` or captured live by the sentinel.

**Hard cutoff time**: For events where the Facebook live node does not reliably deactivate when the broadcast ends, `--end-time` can be passed as a hard cutoff. The sentinel respects this and yields immediately when the time is exceeded.

**3s views metric**: Facebook video insights returns multiple view-count definitions. This pipeline collects `total_video_views` (3-second views) to maintain consistency with historical reports that used the Page Insights GUI "screen capture" method.

**Conviva account/filter parameterization**: `dotcom.py` and `network.py` expose `account_name` and `filter_id` as function parameters (defaulting to placeholder values) rather than hardcoding them. The caller in `run_live_report.py` uses defaults; override by passing explicit values or adding `--dotcom-account` CLI args.
