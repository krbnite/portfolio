---
project: pptv_viewership_analytics
language: r
tags: r redshift aws dplyr ggplot2 lubridate readxl chinese-encoding r-package roxygen2
timeline: 2016-2017
---

# PPTV Viewership Analytics

An R package for loading, parsing, quality-checking, and reporting on weekly viewership data from PPTV, a Chinese streaming platform. The data was deposited by PPTV into a secure location, ETL'd into Redshift by the data engineering team, and then consumed by this package for weekly reporting.

Prior to this project, an offshore consulting team was manually computing and reporting the viewership metrics from Excel files each week. A QC layer was built into this package to catch copy-paste errors in those reports — which turned out to catch real mistakes, including a case where the team had been reporting Table A's numbers using the *transpose* of Table A for months.

## Architecture

```
PPTV (weekly data drop)
        |
   [Data Engineering]
        | ETL
   [Redshift: raw_china_pptv]
        |
   [pptvR package]
        |
   +----+----+----+----+
   |    |    |    |    |
  QC  Live  LP7 Short  Viz
        |
   [Offshore Report]  <-- double-checked by QC layer
```

**Data flow:**
1. PPTV deposits raw viewership data weekly (initially Excel files, later via Redshift ETL)
2. `pptv.query()` loads data from either Excel (`inst/`) or Redshift, normalizes column names and Chinese character encoding
3. `pptv.qc()` runs consistency checks between this week's and last week's data sets
4. `pptv.offshore.*` functions recompute every number in the offshore report for verification
5. `pptv.viz.*` functions generate the figures used in the final PowerPoint report

## Package Structure

```
pptvR/
├── DESCRIPTION
├── NAMESPACE
├── R/
│   ├── pptv.info.R         # pptv.info() / pptv.help(): usage guide printed to console
│   ├── pptv.query.R        # pptv.query(): load from Excel or Redshift; pptv.showTitle(): parse Chinese show titles
│   ├── pptv.qc.R           # pptv.qc(): full QC suite; inner/left join comparisons between data sets
│   ├── pptv.live.R         # pptv.live(): filter to LIVE full-episode viewership
│   ├── pptv.lp7.R          # pptv.lp7(): filter to LIVE+7 viewership window
│   ├── pptv.offshore.R     # pptv.offshore.*: replicate every table in the offshore report
│   ├── pptv.sql.R          # sql_live() / sql_lp7(): ad-hoc Redshift temp table queries
│   ├── pptv.viz.R          # pptv.viz(): multi-plot layout helper (png/pdf output)
│   ├── pptv.viz.live.R     # pptv.viz.live(): LIVE uniques and minutes for Raw and Smackdown
│   ├── pptv.viz.lp7.R      # pptv.viz.lp7(): LIVE+7 views and minutes for Raw and Smackdown
│   ├── pptv.viz.short.R    # pptv.viz.short(): weekly shortform clip minutes trend
│   ├── pptv.viz.ubound.R   # pptv.viz.ubound(): upper/lower bound ribbon on unique viewer estimates
│   └── pptv.viz.webcal.R   # pptv.viz.webcal(): PPTV website traffic as a calendar heatmap
├── man/                    # Roxygen2-generated documentation
├── inst/                   # Excel data files (gitignored)
└── blogs/
    ├── 2016-12-22-Connect-to-Redshift-from-R-with-RPosgreSQL.md
    ├── 2017-01-18-Running-with-Redshift.md
    ├── 2017-04-11-Conditional-Aggregation-in-dplyr-and-Redshift.md
    ├── 2017-06-09-Customizing-R-with-RProfile.md
    └── 2017-06-21-Character-Encoding-Craziness.md
```

## Key Modules

### Data Loading (`pptv.query.R`)

`pptv.query(as_on_dt, con)` dispatches to either:
- **Excel path** (`pptv.query.excel`): reads from versioned `.xlsx` files installed in `inst/` — used during the period before Redshift ETL was available
- **Redshift path** (`pptv.query.redshift`): queries `raw_china_pptv` and applies `enc2utf8()` to handle Chinese character encoding from PostgreSQL

`pptv.showTitle()` normalizes Chinese show title strings into a consistent format (e.g., extracting episode numbers from Raw/Smackdown titles, handling PPTV's inconsistent "takeover" labeling for NXT).

### Quality Control (`pptv.qc.R`)

`pptv.qc(pptv_data1, pptv_data2)` runs a full suite comparing two consecutive weekly data drops:

| Check | Function | What it catches |
|---|---|---|
| NULL metrics | `pptv.qc.nulls` | Rows where viewership numbers went missing |
| LIVE aggregates | `pptv.qc.live` | Changes to weekly Raw/Smackdown live numbers |
| LIVE+7 aggregates | `pptv.qc.lp7` | Changes to 7-day window numbers |
| Row-level inner join | `pptv.qc.ij` | Per-row metric drift between data drops |
| Now LJ Then | `pptv.qc.ljNowThen` | Rows in new data not in prior data |
| Then LJ Now | `pptv.qc.ljThenNow` | Rows in prior data missing from new data |

### Offshore Report Replication (`pptv.offshore.R`)

The `pptv.offshore.*` functions reconstruct every table the offshore consulting team produced:
- `pptv.offshore.live`: LIVE uniques, views, minutes + "vs 4-week avg" KPIs
- `pptv.offshore.lp7`: LIVE+7 equivalent with English subtotal breakdown
- `pptv.offshore.shortform`: top N shortform clips by show (Raw, SD, NXT, CWC)
- `pptv.offshore.topmatches`: top 20 match/game clips by views, last 30 days
- `pptv.offshore.overview`: MTD and monthly total/live viewership summary table
- `pptv.offshore.web`: PPTV website page/unique view aggregations with WoW delta

### Visualizations (`pptv.viz.*.R`)

All viz functions accept `to_pdf` or `to_png` parameters to write directly to file for use in PowerPoint:
- `pptv.viz.live`: 4-panel uniques + minutes trend for Raw and Smackdown LIVE
- `pptv.viz.lp7`: same for LIVE+7 with audio/subtitle breakdown
- `pptv.viz.short`: shortform weekly minutes trend, smoothed
- `pptv.viz.ubound`: ribbon plot bounding unique viewer estimates using Nielsen median viewing duration
- `pptv.viz.webcal`: PPTV website traffic displayed as a calendar heatmap

## Notable Design Decisions

**Two-path data loading**: For the first several months, PPTV delivered data only as Excel files while the Redshift ETL was being set up. `pptv.query()` detects whether a Redshift connection is passed and dispatches accordingly, keeping both paths working simultaneously.

**Chinese character encoding**: Data arriving from Redshift had different encoding metadata than the same data read from Excel, even though both looked correct visually. `enc2utf8()` is applied after each Redshift query, and `readxl` handles UTF-8 automatically on the Excel path. Without this, `dplyr` joins on Chinese show title strings silently failed.

**Transposed reporting bug**: The offshore team was using the transpose of a table when generating weekly numbers — a copy-paste error pattern that persisted undetected. The QC layer caught this by independently recomputing every number in the report and flagging discrepancies.

**Upper/lower bounds on uniques**: PPTV "uniques" are only unique within a given (show, day, asset, device) combination — not true unique viewers. `pptv.viz.ubound` visualizes this uncertainty as a ribbon: the upper bound is the raw unique count, the lower bound is total minutes divided by median viewing duration (64 min for Raw, 46 min for Smackdown, derived from Nielsen data).

**Early dplyr-on-laptop failure**: Initial approach pulled raw data into R via dplyr for aggregation. With ~23M rows across 89 data windows, this choked the machine. Migrated aggregations to Redshift SQL queries, cutting processing from ~10 minutes to under a minute.

## Dependencies

```r
# Package dependencies (DESCRIPTION)
dplyr, lubridate, readxl

# Also used
RPostgreSQL   # Redshift connection
ggplot2       # Visualizations
tidyr         # Reshaping for report tables
scales        # Date axis formatting
gridExtra     # Multi-panel plot layout
stringr       # Show title parsing (regex)
```

## Usage

```r
library(devtools)
devtools::install("pptvR")

# Connect to Redshift
library(RPostgreSQL)
drv = dbDriver("PostgreSQL")
con = dbConnect(drv, host=<host>, port='5439', dbname=<db>, user=<user>, password=<pw>)

# Load data
pptv_now  = pptv.query("2017-06-30", con)
pptv_then = pptv.query("2017-06-23", con)

# Run QC
qc = pptv.qc(pptv_now, pptv_then)

# Verify offshore report numbers
offshore = pptv.offshore(pptv_now)

# Generate figures
pptv.viz.live(pptv_now,  to_pdf="live")
pptv.viz.lp7(pptv_now,   to_pdf="lp7")
pptv.viz.short(pptv_now, to_pdf="shortform")
```
