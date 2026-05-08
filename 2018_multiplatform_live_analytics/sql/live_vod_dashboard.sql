-- Dashboard query for Tableau: transforms the live+VOD event reporting table
-- into a per-platform view with period-over-period comparisons.
--
-- Source table:  busgrp.content_kickoff_report_live_plus_vod
-- Output table:  busgrp.content_kickoff_report_live_plus_vod_tableau
--
-- Before running:
--   1. Update <prior_month_event> and <prior_year_event> in the #prior_change CTE
--   2. Update tier classification patterns to match your event naming conventions

--select * from busgrp.content_kickoff_report_live_plus_vod;

select *
into #tot_platforms
from
(select event_name, event_date, start_time, end_time, 'YouTube' as platform,
case when yt_validated_views is null then yt_invalidated_views
else yt_validated_views end as views,
yt_validated_views_us as us_views,
yt_validated_minutes as minutes
from busgrp.content_kickoff_report_live_plus_vod
where brand='ppv')
union all
(select event_name, event_date, start_time, end_time, 'Facebook' as platform,
fb_total_3s_views as views,
null as us_views,
fb_total_view_time_minutes as minutes
from busgrp.content_kickoff_report_live_plus_vod
where brand='ppv')
union all
(select event_name, event_date, start_time, end_time, 'DotCom' as platform,
dotcom_plays as views,
dotcom_plays_us as us_views,
null as minutes
from busgrp.content_kickoff_report_live_plus_vod
where brand='ppv')
union all
(select event_name, event_date, start_time, end_time, 'App' as platform,
app_metric as views,
null as us_views,
null as minutes
from busgrp.content_kickoff_report_live_plus_vod
where brand='ppv')
union all
(select event_name, event_date, start_time, end_time, 'Twitter' as platform,
twt_viewers as views,
null as us_views,
null as minutes
from busgrp.content_kickoff_report_live_plus_vod
where brand='ppv')
union all
(select event_name, event_date, start_time, end_time, 'Network' as platform,
network_streams as views,
network_streams_us as us_views,
network_total_minutes_watched as minutes
from busgrp.content_kickoff_report_live_plus_vod
where brand='ppv');


select a.event_name, a.event_date, a.start_time, a.end_time, a.platform,
views, us_views, minutes, per_us_views
into #totals
from
(select event_name, event_date, start_time, end_time, 'Total' as platform,
sum(views) as views,
sum(us_views) as us_views,
sum(minutes) as minutes
from #tot_platforms
group by event_name, event_date, start_time, end_time) as a
left join
(select event_name, event_date, start_time, end_time,
(sum(us_views)*1.00)/sum(views) as per_us_views
from #tot_platforms
where us_views is not null
group by event_name, event_date, start_time, end_time) as b
on a.event_name=b.event_name
and a.event_date=b.event_date;

select *
into #content_kickoff_report_live_tableau
from
(select * from #totals)
union all
(select *, (us_views*1.00)/views as per_us_views
from #tot_platforms);


select case when lower(event_name) like '%%annual_event_1%%' then event_name
else event_name||' '||extract(year from event_date) end as event,
event_name, event_date, start_time, end_time, platform,
views, us_views, minutes, per_us_views
into #content_kickoff_report_live_tableau2
from #content_kickoff_report_live_tableau;

drop table if exists #content_kickoff_report_live_tableau3;
select a.event,
a.event_name, a.event_date, a.start_time, a.end_time, a.platform,
a.views, a.us_views, a.minutes, a.per_us_views,
prev_month_views, prev_month_event, prev_year_views, prev_year_event,
event_name2
into #content_kickoff_report_live_tableau3

from (select event,
event_name, event_date, start_time, end_time, platform,
views, us_views, minutes, per_us_views
from #content_kickoff_report_live_tableau2) as a
left join
(select event, event_date, platform, views, LAG(views) over (partition by platform order by event_date) as prev_month_views
from #content_kickoff_report_live_tableau2 group by event, event_date, platform, views) as b
on a.event=b.event
and a.platform=b.platform
left join
(select event, event_date, platform, LAG(event) over (partition by platform order by event_date) as prev_month_event
from #content_kickoff_report_live_tableau2 group by event, event_date, platform) as c
on a.event=c.event
and a.platform=c.platform
left join
(select event, event_name, event_date, platform, views,
case when event_date<'2017-01-01' then null else LAG(views) over (partition by platform order by event_name, event_date) end as prev_year_views
from #content_kickoff_report_live_tableau2 group by event, event_name, event_date, platform, views) as d
on a.event=d.event
and a.platform=d.platform
left join
(select event, event_name, event_date, platform,
case when event_date<'2017-01-01' then null else LAG(event) over (partition by platform order by event_name, event_date) end as prev_year_event
from #content_kickoff_report_live_tableau2 group by event, event_name, event_date, platform) as e
on a.event=e.event
and a.platform=e.platform
left join
(select event, event_name, event_date, platform,
case when event_date<'2017-01-01' then null else LAG(event_name) over (partition by platform order by event_name, event_date) end as event_name2
from #content_kickoff_report_live_tableau2 group by event, event_name, event_date, platform) as f
on a.event=f.event
and a.platform=f.platform;


--select * from #content_kickoff_report_live_tableau3 order by platform, event_date ;

drop table if exists #duplicate_total;
select *, to_date(event_date,'yyyy-mm-01') as debut_month,
to_date(event_date-365,'yyyy-mm-01') last_year
into #duplicate_total
from #content_kickoff_report_live_tableau3
order by debut_month;

drop table if exists #switches;
select *, to_date(event_date,'yyyy-mm-01') as debut_month,
to_date(event_date-365,'yyyy-mm-01') last_year
into #switches
from #content_kickoff_report_live_tableau3
where event_name<>event_name2
and lower(event) not like '%%annual_event_1%%'
and event_name2 is not null
order by debut_month;

select
b.event, b.event_name, b.event_date, b.start_time, b.end_time, b.platform,
b.views, b.us_views, b.minutes, b.per_us_views,
b.prev_month_views, b.prev_month_event, a.views as prev_year_views,
a.event as prev_year_event
into #replacement
from #duplicate_total as a
join #switches as b
on b.last_year=a.debut_month
and a.platform=b.platform
order by a.event_date;

--select * from #content_kickoff_report_live_tableau2 ;
--select * from #replacement ;

select *
into #content_kickoff_report_live_tableau4
from (
(select *
from #content_kickoff_report_live_tableau3
where event not in (select distinct event from #replacement))
union all
(select *, null as event_name2 from #replacement) )
order by platform, event_date;


drop table if exists #prior_change;
select a.*, prev_year_views, prev_year_event
into #prior_change
from
-- Choosing comparison event for prior month (update as needed)
(select platform,
       views as prev_month_views,
       event as prev_month_event
from busgrp.content_kickoff_report_live_plus_vod_tableau
where event='<prior_month_event>') as a   --Change event name here
join
-- Choosing comparison event for prior year (update as needed)
(select platform,
       views as prev_year_views,
       event as prev_year_event
from busgrp.content_kickoff_report_live_plus_vod_tableau_nxt
where event='<prior_year_event>') as b    --Change event name here
on a.platform=b.platform;

drop table if exists #content_kickoff_report_live_tableau5;
select *
into #content_kickoff_report_live_tableau5
from
(select * from #content_kickoff_report_live_tableau4
where event_date <> (select max(event_date) from #content_kickoff_report_live_tableau4) )
union all
select distinct event, event_name, event_date, start_time, end_time, a.platform, views,
us_views, minutes, per_us_views, b.prev_month_views, b.prev_month_event,
b.prev_year_views, b.prev_year_event, event_name as event_name2
from
((select * from #content_kickoff_report_live_tableau4
where event_date = (select max(event_date) from #content_kickoff_report_live_tableau4) ) as a
join (select * from #prior_change) as b
on a.platform=b.platform)
order by event_date, platform;


drop table if exists busgrp.content_kickoff_report_live_plus_vod_tableau;
select
a.event,
case when lower(a.event) like '%%annual_event_1%%' then event_name
else a.event_name
end as event_name,
a.event_date, a.start_time, a.end_time, a.platform, a.views, a.us_views, a.minutes, a.per_us_views,
a.prev_month_views, a.prev_month_event, a.prev_year_views, a.prev_year_event, a.event_name2,
(a.views*1.00)/a.prev_month_views-1 as monthly_per_change_views,
(a.views*1.00)/a.prev_year_views-1 as yearly_per_change_views,
(EXTRACT(EPOCH FROM ((end_time) - (start_time)))/60::numeric)+1 as duration,
row_number() OVER (PARTITION BY a.platform ORDER BY a.views desc) as overall_rank,
case when yearly_rank>0 then yearly_rank else null end as yearly_rank,
-- Tier classification: update these patterns to match your event naming conventions
case when lower(a.event) like '%%annual_event_1%%' then 'Tier 1'
     when lower(a.event) like '%%annual_event_2%%' then 'Tier 1'
     when lower(a.event) like '%%annual_event_3%%' then 'Tier 1'
     when lower(a.event) like '%%annual_event_4%%' then 'Tier 1'
     else 'Tier 2' end as tier,
case when (a.views*1.00)/a.prev_month_views-1 >= 0 then '1'
else '0' end as monthly_color,
case when (a.views*1.00)/a.prev_year_views-1 >= 0 then '1'
else '0' end as yearly_color,
case when a.event_date=(select max(event_date) from #content_kickoff_report_live_tableau3) then 'Most Recent Event' else 'Prior Events' end as Choose_Event
into busgrp.content_kickoff_report_live_plus_vod_tableau
from #content_kickoff_report_live_tableau5 as a
left join
(select platform, event, views,
(row_number() OVER (PARTITION BY platform ORDER BY views desc)) as yearly_rank
 from #content_kickoff_report_live_tableau5 where current_date-event_date<=380) as b
 on a.platform=b.platform
 and a.event=b.event
order by a.platform, a.event_date;

grant select on busgrp.content_kickoff_report_live_plus_vod_tableau to public;


--select * from busgrp.content_kickoff_report_live_plus_vod_tableau;

--select * from busgrp.content_kickoff_report_live_plus_vod_tableau order by platform, event_date;
