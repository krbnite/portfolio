

## How to get a page token
1. Go to business.facebook.com and sign in.
2. Go to the Graph API Explorer
3. Get Token: Click on one of the pages you have page-token rights to

## List the videos for a given Page ID
```python
import requests
import json
response = requests.get('https://graph.facebook.com/me/videos?access_token='+token)
json.loads(response.text)
```

## List the video broadcasts for a given Page ID
Use Case: Say your company is streaming something live on a regular basis and you want to automatically
collect video insights.  You might use this edge to first identify the name of a current live stream
(will have a LIVE status as opposed to VOD).
```python
import requests
import json
response = requests.get('https://graph.facebook.com/me/video_broadcasts?access_token='+token)
json.loads(response.text)
```

### Extract current LIVE streams
```python
response_dict = json.loads(response.text)
live_videos = [item for item in response_dict['data'] 
    if item['status'].lower()=='live']
```

### Get live video views
* Note: live views seems to correspond to "instantaneous number of viewers" (it is not cumulative)
```python
lvid0 = live_videos[0]['id']
live_views = requests.get(gurl+'v2.10/' + lvid0 + '?fields=live_views&access_token='+token)
live_views.text
```

### Get corresponding video ID
Note that the "id" field corresponds to the LiveVideo ID, but to extract video insight metrics,
we need the Video ID, which is not the same thing.  Fortunately, there is a way to get it from the
LiveVideo object.

```python
response = requests.get(gurl+'v2.10/' + lvid0 + '?fields=video&access_token='+token)
response_dict = json.loads(response.text)
video_id = response_dict['video']['id']
```


## List the photo albums for a given Page ID
```python
import requests
import json
response = requests.get('https://graph.facebook.com/me/albums?access_token='+token)
json.loads(response.text)
```

## List the events for a given Page ID
```python
import requests
import json
response = requests.get('https://graph.facebook.com/me/events?access_token='+token)
json.loads(response.text)
```

## What in the feed for a given Page ID?
Def: The feed of posts (including status updates) and links published by this page, or by others on this page.
* Seem to be the same as the "posts" edge
```python
import requests
import json
response = requests.get('https://graph.facebook.com/me/feed?access_token='+token)
json.loads(response.text)
```

## List the posts for a given Page ID
Def: The feed of posts (including status updates) and links published by this page, or by others on this page.
* seems to be the same as the "feed" edge
```python
import requests
import json
response = requests.get('https://graph.facebook.com/me/posts?access_token='+token)
json.loads(response.text)
```

## Page Insights for a given Page ID
Here I give just a few examples.  Go to [Page/Insights reference manual](https://developers.facebook.com/docs/graph-api/reference/v2.11/insights)
for a full list of insight metrics, paratemeters, etc.

### Number of stories written about your page in a day
```python
import requests
import json
response = requests.get('https://graph.facebook.com/me/insights/page_stories/day?access_token='+token)
json.loads(response.text)
```


## Comments on a given video object ID
```python
import requests
import json
response = requests.get('https://graph.facebook.com/'+obj_id+'/comments?access_token='+token)
json.loads(response.text)
```

## Likes on a given video object ID
```python
import requests
import json
response = requests.get('https://graph.facebook.com/'+obj_id+'/likes?access_token='+token)
json.loads(response.text)
```

## Reactions on a given video object ID
Note: The Reactions read API requires version v2.6 or higher.
```python
import requests
import json
response = requests.get('https://graph.facebook.com/v2.10/'+obj_id+'/reactions?access_token='+token)
json.loads(response.text)
```

## Shared posts on a given video object ID
```python
import requests
import json
response = requests.get('https://graph.facebook.com/'+obj_id+'/sharedposts?access_token='+token)
json.loads(response.text)
```

## Video Insights on a given video object ID
Note: The video insights API requires version v2.6 or higher.
```python
import requests
import json
response = requests.get('https://graph.facebook.com/v2.10/'+obj_id+'/reactions?access_token='+token)
json.loads(response.text)
```

### Print the list of Video Insight metric names
```python
response_dict = json.loads(response.text)
[item['description'] for item in response_dict['data']]
```