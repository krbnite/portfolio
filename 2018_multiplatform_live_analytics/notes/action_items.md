
## Future Work / Automation TODOs

* Create event table in Redshift
* Add all historical rows
* `create_email` function
  - Takes in variables; outputs draft email with event metrics
  - Can be wrapped by `send_email`
  - Email sent early for review; additional benefit of knowing the script is running
* 8-hour trial functions: various checks to ensure things are working properly
  - `test_youtube` (logs into YouTube Analytics and, if successful, retrieves data)
  - `test_2ndscreen` (checks to see if data is being populated into `busgrp.ga_real_time_second_screen_viewers`)
* Streaming trial functions: these do the same tests, but during the live event

## JW Player

Check this out: https://github.com/jwplayer/jwplatform-py

## Google Analytics

Check out: https://developers.google.com/analytics/devguides/reporting/core/v3/quickstart/service-py
