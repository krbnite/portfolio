

# Building LIVE
# 1. Assigns labels "Current_week" and "4 week avg" to 
#    Raw and Smackdown shows (live, full) from most recent as_on_Date
#    that will be in "current_week" aggregation or "4 week avg" aggregation
sql_live = function() {
    
  dbExecute(con, "
    drop table if exists #live;
    create table #live as (
      select *,
        case 
          when match_date = raw_live then 'Current_week'
          when match_date in (raw_live - 7,raw_live - 14 ,raw_live-21,raw_live-28) then '4 week avg'
          else 'NA' 
          end as category_raw,
        case when match_date = sd_live then 'Current_week'
          when match_date in (sd_live - 7,sd_live - 14 ,sd_live-21,sd_live-28) then '4 week avg'
          else 'NA' 
          end as category_sd       
      from (
        select *, 
          '2017-06-26' as raw_live,
          '2017-06-27'  as sd_live 
        from raw_china_pptv 
          where as_on_date = '2017-06-30' 
          and trim(lower(show)) ~ '(smackdown|mon night raw)' 
          and trim(lower(type)) in ('live') 
          and trim(lower(version)) in ('full show') 
      ) 
    );
  ")
  
  # 2. Aggregates the temp table by audio, subtitle, and show 
  #    (version='Full Show' for all, so unnecessary)
  dbExecute(con, "
    drop table if exists #slide2;
    create table #slide2 as (
      select distinct audio_version,
        subtitle,
        version,
        category_raw,
        category_sd,
        avg(total_uniques) as uniques,
        avg(total_views) as views,
        avg(total_mins) as minutes
      from #live 
      group by 1,2,3,4,5 
    );
  ")
  
  # Return LIVE Info
  dbGetQuery(con, "
    select * 
    from #slide2 
      where category_raw<>'NA' 
      or category_sd<>'NA' 
    order by category_raw, category_sd;
  ")
}


#----------------------------------------
# LIVE + 7
#----------------------------------------
sql_lp7 = function(){
  dbExecute(con, "
    drop table if exists #temp2;
    create table #temp2 as (
      select *,
        case 
          when match_date = raw_live -7 then 'prev_week'
          when match_date in (raw_live-14, raw_live - 21, raw_live-28, raw_live-35) then '4 week avg'
          else 'NA' 
          end as category_raw,
        case 
          when match_date = sd_live - 7 then 'prev_week'
          when match_date in (sd_live-14, sd_live - 21, sd_live-28, sd_live-35) then '4 week avg'
          else 'NA' 
          end as category_sd       
      from (
        select *,
          '2017-06-26' as raw_live,
          '2017-06-27' as sd_live 
        from raw_china_pptv 
          where as_on_date = '2017-06-30'
          and trim(lower(show)) ~ '(smackdown|mon night raw)'  
          and trim(lower(version)) in ('full show') 
          and date <= match_Date + 6
          --and date <= match_Date + 7 
      ) 
    );
  ")
  
  
  dbExecute(con,"
    drop table if exists #slide2_2;
    create table #slide2_2 as (
      select distinct audio_version,
        subtitle,
        version,
        category_raw,
        category_sd,
        avg(total_uniques) as uniques,
        avg(total_views) as views,
        avg(total_mins) as minutes
      from (
        select distinct Audio_Version ,
          Subtitle, 
          Version, 
          Show_Title,
          category_sd,
          category_raw,
          sum(total_uniques) as total_uniques ,
          sum(Total_Views) as total_Views,
          sum(Total_Mins) as total_mins 
        from #temp2 
        group by 1,2,3,4,5,6
      )
      group by 1,2,3,4,5 
    );
  ")
  
  # Raw
  list( 
    raw=dbGetQuery(con, "
      select * 
      from #slide2_2 
        where category_raw <> 'NA' 
      order by audio_version, subtitle, category_raw
    "),
    # SD
    sd = dbGetQuery(con, "
      select * 
      from #slide2_2 
        where category_sd <> 'NA' 
      order by audio_version, subtitle, category_sd
    ")
  )
}


