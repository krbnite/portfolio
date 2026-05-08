---
title: Instagram Graph API — Exploration Notes & Pipeline TODOs
---

# Instagram Graph API Notes

The `ig_token` class in `api/graph_api.py` handles authentication (filters FB pages
to those with an associated Instagram Business Account, uses the user token for all
requests). The data collection pipeline below was designed but not implemented.

---

## Getting the Instagram Business Account ID

```python
insta_id = token.get('fb_page_id?fields=instagram_business_account')['instagram_business_account']['id']
```

---

## Account Node: Fields & Edges

Fields available on an Instagram Business Account (`{insta_id}?metadata=1`):
- `id`, `biography`, `business_discovery`, `followers_count`, `ig_id`,
  `media_count`, `mentioned_comment`, `mentioned_media`, `name`,
  `profile_picture_url`, `username`, `website`

Edges: `insights`, `media`, `stories`, `tags`

---

## Account Insights

Day-level metrics (request with `period(day)`):
```python
day_level_metrics = [
    'impressions', 'reach', 'follower_count',
    'email_contacts', 'phone_call_clicks', 'text_message_clicks',
    'get_directions_clicks', 'website_clicks', 'profile_views',
]
token.get(f'{insta_id}?fields=insights.metric({",".join(day_level_metrics)}).period(day)')
```

Lifetime metrics (request with `period(lifetime)`; note: audience metrics only use prior day's data):
```python
lifetime_level_metrics = [
    'audience_gender_age', 'audience_locale', 'audience_country',
    'audience_city', 'online_followers',
]
token.get(f'{insta_id}?fields=insights.metric({",".join(lifetime_level_metrics)}).period(lifetime)')
```

Design note: collect day-level data only; week and days_28 can be derived. Day-level
and lifetime metrics must be collected in separate requests.

---

## Media Types

Instagram has 3 media types: `IMAGE`, `VIDEO`, `CAROUSEL_ALBUM`.

All types share the same fields:
- `id`, `caption`, `comments_count`, `ig_id`, `is_comment_enabled`, `like_count`,
  `media_type`, `media_url`, `owner`, `permalink`, `shortcode`, `thumbnail_url`,
  `timestamp`, `username`

Edges: `children`, `comments`, `insights`

---

## Media Insights

Available insights metrics for `IMAGE` and `VIDEO`:
```
impressions, reach, engagement, saved, video_views,
taps_forward, taps_back, exits, replies
```

Available insights metrics for `CAROUSEL_ALBUM`:
```
impressions, reach, engagement, saved, video_views,
carousel_album_impressions, carousel_album_reach, carousel_album_engagement,
carousel_album_saved, carousel_album_video_views
```

**Key quirk**: `carousel_album_*` names are redundant — the base metric names return
identical values for carousels. No need to use the `carousel_album_` prefix.

**Key quirk**: `taps_forward`, `taps_back`, `exits`, `replies` are story-only metrics.
Requesting them on IMAGE or VIDEO nodes returns a `(#100) Incompatible metrics` error.
Any collection loop must condition metric selection on media type.

**Carousel children**: children of a carousel have no insights — requesting them returns
`(#100) Field is not available for Carousel children media`.

---

## Story Insights

Available metrics on a story node:
```
exits, impressions, reach, replies, taps_forward, taps_back
```

**Critical constraint**: story insights expire after 24 hours (even if archived/highlighted).
To reliably capture end-of-life insights, either:
1. Poll the stories edge hourly, or
2. Use a Webhook for the Instagram topic, subscribed to `story_insights`

Webhooks approach is preferred per FB documentation but was not implemented.

---

## Competitive Intelligence via `business_discovery`

```python
token.get(
    f'{insta_id}?fields=business_discovery.'
    f'username(competitor_handle){{followers_count,media_count,media{{media_type,caption}}}}'
)
```

---

## Pipeline TODOs (Not Yet Implemented)

- [ ] `ig_daily_account_insights.py`: collect day-level + lifetime account metrics on a daily cadence
- [ ] `ig_media_insights.py`: collect fields + insights for all media nodes; handle media-type-conditional metric selection and carousel children exclusion
- [ ] `ig_story_insights.py`: hourly story polling to capture insights before 24hr expiration; OR webhook setup (`story_insights` field subscription)
- [ ] Normalize into relational tables (account, media_fields, media_insights, story_insights) and load to S3 → Redshift
- [ ] Webhook setup docs (Instagram topic, `story_insights` field) — see Blog 3 for context
