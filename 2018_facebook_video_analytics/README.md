---
project: facebook_video_analytics
language: python
tags: facebook instagram graph-api etl aws s3 redshift selenium pandas
timeline: 2017-2018
---

# Facebook Video Analytics

A production data pipeline that pulls Facebook video insights from the Graph API across all authorized Pages, normalizes the data into 8 relational tables, and loads it into Amazon S3 for downstream Redshift ingestion.

A secondary Selenium-based module automates the Graph API Explorer login flow to obtain short-lived user tokens without manual browser interaction.

## Architecture

```
[Selenium Login]
      |
      v
[Graph API Explorer]  -->  User Token
                               |
                               v
                    [fb_token: page token map]
                               |
                    +----------+----------+
                    |          |          |
                 Page 1     Page 2    Page N
                    |
                    v
         [Graph API: /videos edge]
            |
            +-- video fields (title, length, status, ...)
            +-- video_insights.metric(...) [55 metrics]
                    |
                    v
          [Normalize into 8 tables]
                    |
                    v
           [CSV --> S3 --> Redshift]
```

## Project Structure

```
facebook_video_analytics/
├── api/
│   ├── graph_api.py        # fb_token + ig_token + module-level helpers
│   └── page.py             # Page album/field utilities
├── pipelines/
│   ├── daily_video_insights.py   # Core extraction: 55 metrics → 8 tables
│   └── post_insights.py          # Post-level insight metric list + helpers
├── scripts/
│   ├── run_daily_video_insights.py     # Daily driver: all pages → S3
│   └── run_universal_video_id_scan.py  # One-time scan for cross-platform IDs
├── utils/
│   ├── redshift.py     # SQLAlchemy connection + append helper
│   ├── s3.py           # boto3 CSV upload (AES256 encrypted)
│   └── registry.py     # Static page name → ID mapping (placeholder)
├── legacy/
│   └── live_event_monitoring/
│       ├── live_event_monitor.py   # Real-time live view polling
│       └── data/
│           ├── event_live_views.txt       # Sample live view time series
│           └── event_video_insights.json  # Sample post-broadcast insights
└── notes/
    ├── facebook-graph-api-notes.md   # Graph API endpoint reference
    └── instagram-graph-api-notes.md  # Instagram Graph API exploration + pipeline TODOs
```

## Pipelines

### Daily Video Insights (`scripts/run_daily_video_insights.py`)

Runs daily via cron. For each authorized Facebook Page:

1. Uses Selenium (`api/graph_api.py`) to log in to the Graph API Explorer and obtain a user token
2. Exchanges the user token for per-page tokens via `me/accounts`
3. Queries `me/videos.since(date).until(date)` for each day in the rolling window
4. Normalizes insights into 8 DataFrames (see table schema below)
5. Writes each table to CSV, uploads to S3 (AES256), removes local file

**Key design decision:** Metrics are explicitly specified in `.metric(...)` rather than using the default return-all behavior, which is unstable in Graph API v3.0. See the extended notes at the top of `pipelines/daily_video_insights.py` for the full story.

### Universal Video ID Scan (`scripts/run_universal_video_id_scan.py`)

One-time (or periodic) scan across all Pages to find videos with a `universal_video_id` — Facebook's cross-platform identifier for syndicated content. Outputs a flat CSV with video metadata and basic performance metrics.

### Live Event Monitor (`legacy/live_event_monitoring/live_event_monitor.py`)

Polls `me/video_broadcasts` at a configurable cadence during a live stream to capture instantaneous viewer counts. After the broadcast ends, fetches post-broadcast video insights. Sample output data is in `legacy/live_event_monitoring/data/`.

## Output Tables

`get_video_insights_tables()` returns a dict of up to 8 DataFrames:

| Table | Grain | Key Columns |
|---|---|---|
| `fields` | 1 row per video | title, description, length, live_status, privacy, content_category, universal_video_id, ... |
| `viewership` | 1 row per video | 33 view/time metrics (3s, 10s, 30s, complete; organic/paid/autoplayed) |
| `impressions` | 1 row per video | 12 impression/reach metrics |
| `viewership_by_dist_type` | 3 rows per video | page_owned / shared / crossposted views and view time |
| `viewership_by_country` | ≤45 rows per video | view time by country (in minutes) |
| `viewership_by_region` | ≤45 rows per video | view time by region/state (in milliseconds) |
| `viewership_by_age_and_gender` | 21 rows per video | view time by age bucket × gender (all buckets always present) |
| `video_engagement_by_action_and_reaction` | 1 row per video | comment, share, story_like, reaction_like, love, wow, anger, haha, sorry |

**Time unit warning:** Facebook uses inconsistent time units across metrics — milliseconds for ad breaks, region time, and age/gender; seconds for video length; minutes for country time. Values are stored as-is (no normalization). See the docstring in `pipelines/daily_video_insights.py` for the full breakdown.

## Token Classes

### `fb_token`
Selenium-based login to the Graph API Explorer. On init:
- Gets user token via browser automation
- Fetches all authorized Page accounts
- Builds `page_to_token`, `id_to_token`, `page_to_id`, `id_to_page` lookup dicts
- `.get(url)` and `.pget(url)` for Graph API requests
- `.change_token_by_name()` / `.change_token_by_id()` to switch active Page
- `.change_version()` to switch API version (default: v2.12)

### `ig_token(fb_token)`
Extends `fb_token` for Instagram Graph API queries. Filters to only Pages with an associated Instagram Business Account. Uses the user token (not the page token) for all requests, since Instagram Graph API requires a privileged user token.

## Environment Variables

| Variable | Description |
|---|---|
| `FB_USERNAME` | Facebook login email |
| `FB_PASSWORD` | Facebook login password |
| `S3_BUCKET` | Target S3 bucket name |
| `S3_KEYPATH` | S3 key prefix (e.g., `facebook/video_insights/`) |
| `REDSHIFT_USER` | Redshift username |
| `REDSHIFT_PASSWORD` | Redshift password |
| `REDSHIFT_HOST` | Redshift cluster endpoint |
| `REDSHIFT_DB` | Redshift database name |

Store in a `.env` file (gitignored). Scripts load via `python-dotenv`.

## Notable Graph API Quirks

- **`total_video_play_count`** is available via the default (return-all) behavior in v2.12 but cannot be requested explicitly via `.metric()`, and its availability in v3.0 is inconsistent. Not collected in this pipeline.
- **`autoplayed` vs `auto_played`** naming is inconsistent across metric names (e.g., `total_video_views_autoplayed` vs `total_video_complete_views_auto_played`).
- **v3.0 instability:** The default return-all behavior for `video_insights` works differently depending on the user account. This pipeline explicitly lists all metrics to avoid unpredictable behavior.
- **`total_video_stories_by_action_type`:** In v3.0, Facebook renamed "stories" to "activity" for page/post metrics, but kept "stories" for video metrics. Watch for this to change in future versions.

## Legacy

The `legacy/live_event_monitoring/` folder contains the real-time live broadcast polling script and sample data files from live streaming events. This was run manually during broadcasts rather than on a scheduled pipeline.

The `utils/registry.py` page registry is a sanitized placeholder for what was originally a CSV file mapping page names to Facebook Page IDs. In production, the page map was populated dynamically from `fb_token.accounts` on each run.
