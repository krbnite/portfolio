# This file contains all QC-related functions:
#  - pptv.qc
#  - pptv.qc.ij
#  - pptv.qc.ljNowThen
#  - pptv.qc.ljThenNow
#  - pptv.qc.live
#  - pptv.qc.lp7
#  - pptv.qc.nulls
#  - pptv.qc.clipsVsFull
#$


#===================================================================
#  pptv.qc
#===================================================================
#' Run PPTV Quality Control (QC) Checks
#' 
#' This function will print notes to screen as its runs, and
#' ultimately will return a list of the QC checks.  
#' 
#' @param pptv_data1
#' 
#' @param pptv_data2
#' 
#' @export
#$
pptv.qc = function(
    pptv_data1,
    pptv_data2 
) {
    
    print("")
    
    print("-------------------------------------------------")
    print("Checking for Records with NULL metrics...")  
    nulls = as.data.frame(pptv.qc.nulls(pptv_data1))
    print(nrow(nulls))
    print("")
    
    print("-------------------------------------------------")
    print("Checking for Consistency in Aggregated Numbers...")
    print("LIVE...")
    live.diff = pptv.qc.live(pptv_data1, pptv_data2)
    print(nrow(live.diff))
    print("LIVE+7...")
    lp7.diff = pptv.qc.lp7(pptv_data1, pptv_data2)
    print(nrow(lp7.diff))
    print("")
    
    print("-------------------------------------------------")
    print("Checking for Consistency at Granular Level...")
    print("Inner Join on all dimensional parameters...")
    ij.nowthen = pptv.qc.ij(pptv_data1, pptv_data2)
    print(nrow(ij.nowthen))
    if (nrow(ij.nowthen)==1) print(ij.nowthen) else print(nrow(ij.nowthen))
    
    print("-------------------------------------------------")
    print("On Now LJ Then...")
    print("On all dimensional parameters where usAirDate not NULL...")
    lj.nowthen.1 = pptv.qc.ljNowThen(pptv_data1, pptv_data2)
    if (nrow(lj.nowthen.1)==1) print(lj.nowthen.1) else print(nrow(lj.nowthen.1))
    print("On all dimensional parameters excluding usAirDate where usAirDate is NULL...")
    lj.nowthen.2 = pptv.qc.ljNowThen(pptv_data1, pptv_data2, nulls=TRUE)
    if (nrow(lj.nowthen.2)==1) print(lj.nowthen.2) else print(nrow(lj.nowthen.2))
    
    print("-------------------------------------------------")
    print("On Then LJ Now...")
    lj.thennow.1 = pptv.qc.ljThenNow(pptv_data1, pptv_data2)
    if (nrow(lj.thennow.1)==1) print(lj.thennow.1) else print(nrow(lj.thennow.1))
    print("On all dimensional parameters excluding usAirDate where usAirDate is NULL...")
    lj.thennow.2 = pptv.qc.ljThenNow(pptv_data1, pptv_data2, nulls=TRUE)
    if (nrow(lj.thennow.2)==1) print(lj.thennow.2) else print(nrow(lj.thennow.2))
    
    print("-------------------------------------------------")
    print("Recording lists of episodes ('showTitle') for version=='FULL' and version!='FULL'...")
    print("(Check them for Consistency.)")
    clipVsFull = pptv.qc.clipVsFull(pptv_data1)
    
    print("-------------------------------------------------")
    print("")
    # Return Stuff
    list(nulls=nulls, live.diff=live.diff, lp7.diff=lp7.diff,
         ij.nowthen=ij.nowthen, lj.nowthen.1=lj.nowthen.1,
         lj.nowthen.2=lj.nowthen.2, lj.thennow.1=lj.thennow.1,
         lj.thennow.2=lj.thennow.2)
}




#===================================================================
#  pptv.qc.ij
#===================================================================
#      2017-03-10, Kevin Urban (created)
#===================================================================
#' Check whether the metrics and KPIs corresponding each row in
#' the inner join between as_on_dt1 and as_on_dt2 are consistent.  
#' 
#' This function does not restrict the data to any subsets, nor does
#' this function compare the consistency of aggregated values. 
#' This is a brute force row-to-row comparison, where the compared
#' rows are those found by taking the inner join on PPTV viewership
#' dimensions (chinaAirDate, dataDate, )
#' We have found that inconsistencies may exist in the untouched 
#' data that do not affect all or any aggregated values of interest,
#' but are still disconcerting and require discovery just in case.
#' For example, in the 2017-03-09 data set, we found that...
#' 
#' @param pptv_data1
#' PPTV data set
#' 
#' @param pptv_data2
#' PPTV data set
#' 
#' @param pcDiffs
#' ...
#' 
#' @param View (optional; {TRUE|FALSE} or {0|1})
#' By default (FALSE) data is returned to parent environment
#' (whether that is to a variable or to screen). By
#' flagging View (TRUE), the data is instead routed to 
#' View()
#' 
#' @export        
pptv.qc.ij = function(
    pptv_data1, 
    pptv_data2, 
    pcDiffs=TRUE, 
    View=FALSE
) {
  
  as_on_dt1 = as.Date(max(pptv_data1$dataDate)) + lubridate::days(1)
  as_on_dt2 = as.Date(max(pptv_data2$dataDate)) + lubridate::days(1)
  
  # CHECK DATES:  For consistency ensure that as_on_dt1 > as_on_dt2
  #   The reason is that we are see if any changes are in the
  #   "now" file vs the "then" file.
  if(as_on_dt1 < as_on_dt2) {
    as_on_dt_now = as_on_dt2
    as_on_dt_then = as_on_dt1
    now = pptv_data2
    then = pptv_data1
  } else {
    as_on_dt_now = as_on_dt1
    as_on_dt_then = as_on_dt2
    now = pptv_data1
    then = pptv_data2
  }
  
  # Want to JOIN on liveAir, show, audio, 
  #   subtitle (in case its implemented in future)
  #
  # [1] Changes totUniq and totMin colnames to avoid JOIN
  #     giving arbitrary names to replicated colnames
  colnames(now)=c("usAirDate","chinaAirDate","dataDate",
                       "show","showTitle","game","type","audio","version","subtitle","payment",
                       "totViewNow","totUniqNow", "totMinNow","vpuNow","mpvNow","mpuNow")
  colnames(then)=c("usAirDate","chinaAirDate","dataDate",
                       "show","showTitle","game","type","audio","version","subtitle","payment",
                       "totViewThen","totUniqThen", "totMinThen","vpuThen","mpvThen","mpuThen")
  
  # this would be a cool parameter, but how would I do the "diffs" code below?
  #if !(is.null(drop)) {
  #    now  = now  %>% dplyr::select(-drop)
  #    then = then %>% dplyr::select(-drop)
  #}
  
  # [2] INNER JOIN Now w/ Then:  (Now) IJ (Then)
  ij = dplyr::inner_join(now,then,
         by=c("usAirDate","chinaAirDate","dataDate", "show","showTitle","game","type",
              "audio","version","subtitle","payment"))
       
  diffs = ij %>%
      dplyr::mutate(
          diffView= dplyr::coalesce(totViewNow,0) - dplyr::coalesce(totViewThen,0),
          diffUniq= dplyr::coalesce(totUniqNow,0) - dplyr::coalesce(totUniqThen,0),
          diffMin = dplyr::coalesce(totMinNow,0)  - dplyr::coalesce(totMinThen,0),
          diffVpu = dplyr::coalesce(vpuNow,0)     - dplyr::coalesce(vpuThen,0), 
          diffMpv = dplyr::coalesce(mpvNow,0)     - dplyr::coalesce(mpvThen,0), 
          diffMpu = dplyr::coalesce(mpuNow,0)     - dplyr::coalesce(mpuThen,0)
          ) %>%
      dplyr::filter(
          diffView > 0 | diffUniq > 0 | diffMin > 1e-7 | diffVpu > 0 |  diffMpv > 1e-7 | diffMpu > 1e-7
          ) %>%
      dplyr::mutate(
          pcDiffView = round(100*diffView/totViewThen,2),
          pcDiffUniq = round(100*diffUniq/totUniqThen,2),
          pcDiffMin  = round(100*diffMin/totMinThen,2),
          pcDiffVpu  = round(100*diffVpu/vpuThen,2),
          pcDiffMpv  = round(100*diffMpv/mpvThen,2),
          pcDiffMpu  = round(100*diffMpu/mpuThen,2)
          ) %>%
      dplyr::select(
          usAirDate, chinaAirDate, dataDate, show, showTitle, 
          game, type, audio, version, subtitle, payment,
          totViewNow, totViewThen, diffView, pcDiffView,
          totUniqNow, totUniqThen, diffUniq, pcDiffUniq,
          totMinNow, totMinThen, diffMin, pcDiffMin,
          vpuNow, vpuThen, diffVpu, pcDiffVpu,
          mpvNow, mpvThen, diffMpv, pcDiffMpv,
          mpuNow, mpuThen, diffMpu, pcDiffMpu)
  
  if (pcDiffs == TRUE) {
    diffs = diffs %>%
    dplyr::select(usAirDate, chinaAirDate, dataDate, show, showTitle, 
           game, type, audio, version, subtitle, payment, pcDiffView, 
           pcDiffUniq, pcDiffMin, pcDiffVpu, pcDiffMpv, pcDiffMpu)
  }
  
  if (nrow(diffs) == 0) {
    return(data.frame(Result="The two data sets are consistent!"))
  } else {
    if(View == FALSE) { return(as.data.frame(diffs)) } else {View(diffs)}
  } 
}




#===================================================================
#  pptv.qc.ljNowThen
#===================================================================
#      2017-03-10, Kevin Urban (created)
#===================================================================
#' Check whether the metrics and KPIs corresponding each row in
#' the inner join between as_on_dt1 and as_on_dt2 are consistent.  
#' 
#' This function does not restrict the data to any subsets, nor does
#' this function compare the consistency of aggregated values. 
#' This is a brute force row-to-row comparison, where the compared
#' rows are those found by taking the inner join on PPTV viewership
#' dimensions (chinaAirDate, dataDate, )
#' We have found that inconsistencies may exist in the untouched 
#' data that do not affect all or any aggregated values of interest,
#' but are still disconcerting and require discovery just in case.
#' For example, in the 2017-03-09 data set, we found that...
#' 
#' @param pptv_data1
#' PPTV data set
#' 
#' @param pptv_data2
#' PPTV data set
#' 
#' @param nulls (default: FALSE)
#' Defaults to joining on all PPTV dimensional parameters. However,
#' sometimes PPTV does not specify usAirDate ("MatchDate"), and so
#' usAirDate shows up as NULL.  By setting nulls=TRUE, we...
#' 
#' @param pcDiffs
#' ...
#' 
#' @param View (optional; {TRUE|FALSE} or {0|1})
#' By default (FALSE) data is returned to parent environment
#' (whether that is to a variable or to screen). By
#' flagging View (TRUE), the data is instead routed to 
#' View()
#' 
#' @export        
# nulls:  
#    if false, then remove all rows where usAirDate is null
#        and join by all PPTV dimensions;
#    if true, then remove all rows where usAirDate is NOT null
#        and join by all PPTV dimensions except for usAirDate
pptv.qc.ljNowThen = function(
    pptv_data1, 
    pptv_data2,
    nulls=FALSE,
    pcDiffs=FALSE, 
    View=FALSE) {
  
  as_on_dt1 = as.Date(max(pptv_data1$dataDate)) + lubridate::days(1)
  as_on_dt2 = as.Date(max(pptv_data2$dataDate)) + lubridate::days(1)
  
  # CHECK DATES:  For consistency ensure that as_on_dt1 > as_on_dt2
  #   The reason is that we are see if any changes are in the
  #   "now" file vs the "then" file.
  if(as_on_dt1 < as_on_dt2) {
    as_on_dt_now = as_on_dt2
    as_on_dt_then = as_on_dt1
    now = pptv_data2
    then = pptv_data1
  } else {
    as_on_dt_now = as_on_dt1
    as_on_dt_then = as_on_dt2
    now = pptv_data1
    then = pptv_data2
  }
  
  colnames(now)=c("usAirDate","chinaAirDate","dataDate", "show",
                  "showTitle", "game", "type", "audio", "version", 
                  "subtitle", "payment", "totViewNow", "totUniqNow", "totMinNow",
                  "vpuNow", "mpvNow", "mpuNow")
  colnames(then)=c("usAirDate", "chinaAirDate", "dataDate", "show",
                   "showTitle", "game", "type", "audio", "version", 
                   "subtitle", "payment", "totViewThen", "totUniqThen", "totMinThen",
                   "vpuThen", "mpvThen", "mpuThen")
  
  # (then) LJ (now):  This will force the comparison table to consider all rows
  #   in the previous data, which means that if they do not show up in the new
  #   data set, we can detect that.  
  # (now) LJ (then):  This will force the comparison table to consider all rows
  #   in the recent data, which means that if they do not show up in the previous
  #   data set, we can detect that. Obviously diffs exist for all dates in the
  #   recent data that are not covered in the previous data.  To avoid reporting
  #   this, only dates covered in the previous data set are considered.
  
  # [1] Before LJ, filter out now-only "future dates"
  now = now %>%
      dplyr::filter(dataDate <= max(then$dataDate, na.rm=TRUE))
  # [2] Filter out usAirDate==NULL or usAirDate!=NULL?
  if (nulls==FALSE) {
      now = now %>%
          dplyr::filter(!is.na(usAirDate))
      then = then %>%
          dplyr::filter(!is.na(usAirDate))
  } else {
      now = now %>%
          dplyr::filter(is.na(usAirDate))
      then = then %>%
          dplyr::filter(is.na(usAirDate))
  }
  
  LJ = dplyr::left_join(now, then,
         by=c("usAirDate","chinaAirDate","dataDate","show","showTitle","game","type",
              "audio","version","subtitle","payment"))
       
  diffs = LJ %>%
      dplyr::mutate(
          totViewNow  = dplyr::coalesce(totViewNow, 0),
          totViewThen = dplyr::coalesce(totViewThen,0),
          totUniqNow  = dplyr::coalesce(totUniqNow, 0),
          totUniqThen = dplyr::coalesce(totUniqThen,0),
          totMinNow   = dplyr::coalesce(totMinNow,  0),
          totMinThen  = dplyr::coalesce(totMinThen, 0),
          vpuNow      = dplyr::coalesce(vpuNow,  0),
          vpuThen     = dplyr::coalesce(vpuThen, 0),
          mpvNow      = dplyr::coalesce(mpvNow,  0),
          mpvThen     = dplyr::coalesce(mpvThen, 0),
          mpuNow      = dplyr::coalesce(mpuNow,  0),
          mpuThen     = dplyr::coalesce(mpuThen, 0),
          diffView    = totViewNow - totViewThen,
          diffUniq    = totUniqNow - totUniqThen,
          diffMin     = totMinNow  - totMinThen,
          diffVpu     = vpuNow     - vpuThen,    
          diffMpv     = mpvNow     - mpvThen,    
          diffMpu     = mpuNow     - mpuThen,
          pcDiffView  = round(100 * diffView / totViewThen, 2),
          pcDiffUniq  = round(100 * diffUniq / totUniqThen, 2),
          pcDiffMin   = round(100 * diffMin  / totMinThen,  2),
          pcDiffVpu   = round(100 * diffVpu  / vpuThen,     2),
          pcDiffMpv   = round(100 * diffMpv  / mpvThen,     2),
          pcDiffMpu   = round(100 * diffMpu  / mpuThen,     2)
          ) %>%
      dplyr::filter(
          diffView > 0 | diffUniq > 0 | diffMin > 1e-7 | diffVpu > 0 |  diffMpv > 1e-7 | diffMpu > 1e-7
          ) %>%
      dplyr::select(
          usAirDate, chinaAirDate, dataDate, show, showTitle, 
          game, type, audio, version, subtitle, payment,
          totViewNow, totViewThen, diffView, pcDiffView,
          totUniqNow, totUniqThen, diffUniq, pcDiffUniq,
          totMinNow, totMinThen, diffMin, pcDiffMin,
          vpuNow, vpuThen, diffVpu, pcDiffVpu,
          mpvNow, mpvThen, diffMpv, pcDiffMpv,
          mpuNow, mpuThen, diffMpu, pcDiffMpu)
  
  if (pcDiffs == TRUE) {
    diffs = diffs %>%
    select(usAirDate, chinaAirDate, dataDate, show, showTitle, 
           game, type, audio, version, subtitle, payment, pcDiffView, 
           pcDiffUniq, pcDiffMin, pcDiffVpu, pcDiffMpv, pcDiffMpu)
  }
  
  if (nrow(diffs) == 0) {
    return(data.frame(Result="The two data sets are consistent!"))
  } else {
    if(View == FALSE) { return(as.data.frame(diffs)) } else {View(diffs)}
  } 
}




#===================================================================
#  pptv.qc.ljThenNow
#===================================================================
#      2017-03-10, Kevin Urban (created)
#===================================================================
#' Check whether the metrics and KPIs corresponding each row in
#' the inner join between as_on_dt1 and as_on_dt2 are consistent.  
#' 
#' This function does not restrict the data to any subsets, nor does
#' this function compare the consistency of aggregated values. 
#' This is a brute force row-to-row comparison, where the compared
#' rows are those found by taking the inner join on PPTV viewership
#' dimensions (chinaAirDate, dataDate, )
#' We have found that inconsistencies may exist in the untouched 
#' data that do not affect all or any aggregated values of interest,
#' but are still disconcerting and require discovery just in case.
#' For example, in the 2017-03-09 data set, we found that...
#' 
#' @param pptv_data1
#' PPTV data set
#' 
#' @param pptv_data2
#' PPTV data set
#' 
#' @param nulls (default: FALSE)
#' Defaults to joining on all PPTV dimensional parameters. However,
#' sometimes PPTV does not specify usAirDate ("MatchDate"), and so
#' usAirDate shows up as NULL.  By setting nulls=TRUE, we...
#' 
#' @param pcDiffs
#' ...
#' 
#' @param View (optional; {TRUE|FALSE} or {0|1})
#' By default (FALSE) data is returned to parent environment
#' (whether that is to a variable or to screen). By
#' flagging View (TRUE), the data is instead routed to 
#' View()
#' 
#' @export        
# nulls:  
#    if false, then remove all rows where usAirDate is null
#        and join by all PPTV dimensions;
#    if true, then remove all rows where usAirDate is NOT null
#        and join by all PPTV dimensions except for usAirDate
pptv.qc.ljThenNow = function(
    pptv_data1, 
    pptv_data2,
    nulls=FALSE,
    pcDiffs=FALSE, 
    View=FALSE
) {
  as_on_dt1 = as.Date(max(pptv_data1$dataDate)) + lubridate::days(1)
  as_on_dt2 = as.Date(max(pptv_data2$dataDate)) + lubridate::days(1)
  
  # CHECK DATES:  For consistency ensure that as_on_dt1 > as_on_dt2
  #   The reason is that we are see if any changes are in the
  #   "now" file vs the "then" file.
  if(as_on_dt1 < as_on_dt2) {
    as_on_dt_now = as_on_dt2
    as_on_dt_then = as_on_dt1
    now = pptv_data2
    then = pptv_data1
  } else {
    as_on_dt_now = as_on_dt1
    as_on_dt_then = as_on_dt2
    now = pptv_data1
    then = pptv_data2
  }
  
  colnames(now)=c("usAirDate","chinaAirDate","dataDate", "show",
                  "showTitle", "game", "type", "audio", "version", 
                  "subtitle", "payment", "totViewNow", "totUniqNow", "totMinNow",
                  "vpuNow", "mpvNow", "mpuNow")
  colnames(then)=c("usAirDate", "chinaAirDate", "dataDate", "show",
                   "showTitle", "game", "type", "audio", "version", 
                   "subtitle", "payment", "totViewThen", "totUniqThen", "totMinThen",
                   "vpuThen", "mpvThen", "mpuThen")
  
  # (then) LJ (now):  This will force the comparison table to consider all rows
  #   in the previous data, which means that if they do not show up in the new
  #   data set, we can detect that.  
  # (now) LJ (then):  This will force the comparison table to consider all rows
  #   in the recent data, which means that if they do not show up in the previous
  #   data set, we can detect that. Obviously diffs exist for all dates in the
  #   recent data that are not covered in the previous data.  To avoid reporting
  #   this, only dates covered in the previous data set are considered.
  
  # [1] Filter out usAirDate==NULL or usAirDate!=NULL?
  if (nulls==FALSE) {
      now = now %>%
          dplyr::filter(!is.na(usAirDate))
      then = then %>%
          dplyr::filter(!is.na(usAirDate))
  } else {
      now = now %>%
          dplyr::filter(is.na(usAirDate))
      then = then %>%
          dplyr::filter(is.na(usAirDate))
  }
  
  LJ = dplyr::left_join(then, now,
         by=c("usAirDate","chinaAirDate","dataDate", "show","showTitle","game","type",
              "audio","version","subtitle","payment"))
       
  diffs = LJ %>%
      dplyr::mutate(
          totViewNow  = dplyr::coalesce(totViewNow, 0),
          totViewThen = dplyr::coalesce(totViewThen,0),
          totUniqNow  = dplyr::coalesce(totUniqNow, 0),
          totUniqThen = dplyr::coalesce(totUniqThen,0),
          totMinNow   = dplyr::coalesce(totMinNow,  0),
          totMinThen  = dplyr::coalesce(totMinThen, 0),
          vpuNow      = dplyr::coalesce(vpuNow,  0),
          vpuThen     = dplyr::coalesce(vpuThen, 0),
          mpvNow      = dplyr::coalesce(mpvNow,  0),
          mpvThen     = dplyr::coalesce(mpvThen, 0),
          mpuNow      = dplyr::coalesce(mpuNow,  0),
          mpuThen     = dplyr::coalesce(mpuThen, 0),
          diffView    = totViewNow - totViewThen,
          diffUniq    = totUniqNow - totUniqThen,
          diffMin     = totMinNow  - totMinThen,
          diffVpu     = vpuNow     - vpuThen,    
          diffMpv     = mpvNow     - mpvThen,    
          diffMpu     = mpuNow     - mpuThen,
          pcDiffView  = round(100 * diffView / totViewThen, 2),
          pcDiffUniq  = round(100 * diffUniq / totUniqThen, 2),
          pcDiffMin   = round(100 * diffMin  / totMinThen,  2),
          pcDiffVpu   = round(100 * diffVpu  / vpuThen,     2),
          pcDiffMpv   = round(100 * diffMpv  / mpvThen,     2),
          pcDiffMpu   = round(100 * diffMpu  / mpuThen,     2)
          ) %>%
      dplyr::filter(
          diffView > 0 | diffUniq > 0 | diffMin > 1e-7 | diffVpu > 0 |  diffMpv > 1e-7 | diffMpu > 1e-7
          ) %>%
      dplyr::select(
          usAirDate, chinaAirDate, dataDate, show, showTitle, 
          game, type, audio, version, subtitle, payment,
          totViewNow, totViewThen, diffView, pcDiffView,
          totUniqNow, totUniqThen, diffUniq, pcDiffUniq,
          totMinNow, totMinThen, diffMin, pcDiffMin,
          vpuNow, vpuThen, diffVpu, pcDiffVpu,
          mpvNow, mpvThen, diffMpv, pcDiffMpv,
          mpuNow, mpuThen, diffMpu, pcDiffMpu)
  
  if (pcDiffs == TRUE) {
    diffs = diffs %>%
    select(usAirDate, chinaAirDate, dataDate, show, showTitle, 
           game, type, audio, version, subtitle, payment, pcDiffView, 
           pcDiffUniq, pcDiffMin, pcDiffVpu, pcDiffMpv, pcDiffMpu)
  }
  
  if (nrow(diffs) == 0) {
    return(data.frame(Result="The two data sets are consistent!"))
  } else {
    if(View == FALSE) { return(as.data.frame(diffs)) } else {View(diffs)}
  } 
}





#===================================================================
#  pptv.qc.live
#===================================================================
#      2017-02-09, Kevin Urban (created)
#===================================================================
#' Check whether the LIVE metrics and KPIs in the inner join between
#' as_on_dt1 and as_on_dt2 are the same, or if they have changed.
#' 
#' This function restricts its attention to just Raw and 
#' Smackdown because, ultimately, it is a check on metrics and KPIs
#' included in the report generated by the offshore EXL team.  
#' For this reason, it also restricted to LIVE measures
#' with the hope that such modularization might help us more quickly 
#' identify the "what" of "when something is wrong."
#' 
#' ATTRIBUTES OF LIVE VIEWERSHIP:
#'
#'   (a) show=={'Mon Night Raw'|'Smackdown'}
#'   
#'   (b) version=='Full Show'
#'       -- clips are analyzed elsewhere in the PPTV 
#'          report
#'   
#'   (c) audio=={'Mandarin'|'English'}
#'       -- audio=='NULL' in the raw data is a placeholder
#'          for version=='Others', which do not currently
#'          distinguish which language was viewed; i.e.,
#'          version=='Full Show' should have no audio=='NULL'
#'          by definition in the data guide provided by the
#'          PPTV team, so we can safely discard
#'   
#'   (d) type=='LIVE'
#'       -- LIVE always has dataDate == chinaAirDate == usAirDate+1
#'       -- however, there also exists type=='VOD' on this date,
#'          so it is necessary to restrict type to 'LIVE' here
#'       -- setting type=='LIVE' automatically constrains the
#'          dataDate, however I have constraints on both type and 
#'          dataDate for assurance
#'   
#'   (e) dataDate == chinaAirDate
#'       -- we only want to consider rows that have data
#'          recorded on chinaAirDate (i.e., 
#'          dataDate==chinaAirDate) 
#'    
#'  
#' @param pptv_data1
#' PPTV data set
#' 
#' @param pptv_data2
#' PPTV data set
#' 
#' @param trail (optional; INTEGER)
#' By default, all live data is  retrieved.  Restrict 
#' to trailing N weeks by specifying integer N.  Note
#' that any decimal are automatically floored.
#' 
#' @param View (optional; {TRUE|FALSE} or {0|1})
#' By default (FALSE) data is returned to parent environment
#' (whether that is to a variable or to screen). By
#' flagging View (TRUE), the data is instead routed to 
#' View()
#' 
#' @export        
pptv.qc.live= function(
  pptv_data1,
  pptv_data2,
  trail = 0,
  View = FALSE
) {
  
  as_on_dt1 = as.Date(max(pptv_data1$dataDate)) + lubridate::days(1)
  as_on_dt2 = as.Date(max(pptv_data2$dataDate)) + lubridate::days(1)
  
  # CHECK DATES:  For consistency ensure that as_on_dt1 > as_on_dt2
  #   The reason is that we are see if any changes are in the
  #   "now" file vs the "then" file.
  if(as_on_dt1 < as_on_dt2) {
    as_on_dt_now = as_on_dt2
    as_on_dt_then = as_on_dt1
    now = pptv_data2
    then = pptv_data1
  } else {
    as_on_dt_now = as_on_dt1
    as_on_dt_then = as_on_dt2
    now = pptv_data1
    then = pptv_data2
  }
  
  live_now  = pptv.live( now, trail=trail)
  live_then = pptv.live(then, trail=trail)
  
  # Want to JOIN on liveAir, show, audio, 
  #   subtitle (in case its implemented in future)
  #
  # [1] Changes totUniq and totMin colnames to avoid JOIN
  #     giving arbitrary names to replicated colnames
  colnames(live_now)=c("usAirDate","chinaAirDate","show","audio","subtitle",
                       "totUniqNow", "totMinNow", "totViewNow")
  colnames(live_then)=c("usAirDate","chinaAirDate","show","audio","subtitle",
                       "totUniqThen", "totMinThen", "totViewThen")
  # [2] INNER JOIN Now w/ Then:  (Now) IJ (Then)
  ij = dplyr::inner_join(live_now, live_then,by=c("usAirDate","chinaAirDate",
                                                  "show","audio","subtitle"))
       
  diffs = ij %>%
      dplyr::mutate(
          diffUniq = dplyr::coalesce(totUniqNow,0.0) - dplyr::coalesce(totUniqThen,0.0),
          diffMin  = dplyr::coalesce(totMinNow,0.0)  - dplyr::coalesce(totMinThen,0.0),
          diffView  = dplyr::coalesce(totViewNow,0.0)  - dplyr::coalesce(totViewThen,0.0)
          ) %>%
      dplyr::filter(diffUniq > 0 | diffMin > 1e-7 | diffView > 0)
  
  if (nrow(diffs)==0) {
      print("The two data sets are consistent!")
  } else {
      if(View==FALSE) { return(diffs) } else {View(diffs)}
  } 
}




#===================================================================
#  pptv.qc.lp7
#===================================================================
#      2017-02-16, Kevin Urban (created)
#===================================================================
#' Check whether the LIVE+7 metrics and KPIs in the inner join between
#' as_on_dt1 and as_on_dt2 are the same, or if they have changed.
#' 
#' This function restricts its attention to just Raw and 
#' Smackdown because, ultimately, it is a check on metrics and KPIs
#' included in the report generated by the offshore EXL team.  
#' For this reason, it also restricted to LIVE+7 measures
#' with the hope that such modularization might help us more quickly 
#' identify the "what" of "when something is wrong."
#' 
#' ATTRIBUTES OF LIVE+7 VIEWERSHIP:
#'   (a) show=={'Mon Night Raw'|'Smackdown'}
#'   
#'   (b) version=='Full Show'
#'       -- clips are analyzed elsewhere in the PPTV 
#'          report
#'   
#'   (c) audio=={'Mandarin'|'English'}
#'       -- audio=='NULL' in the raw data is a placeholder
#'          for version=='Others', which do not currently
#'          distinguish which language was viewed; i.e.,
#'          version=='Full Show' should have no audio=='NULL'
#'          by definition in the data guide provided by the
#'          PPTV team, so we can safely discard
#'   
#'   (d) dataDate >= chinaAirDate+days(6)
#'       -- we only want to consider rows that have data
#'          recorded in a 7-day interval: the LIVE date
#'          for type == {'LIVE' | 'VOD'} (i.e., 
#'          dataDate==chinaAirDate) and the 6 days thereafter 
#'          (chinaAirData + seq(6), which on has type='VOD')
#'   
#'   (*) subtitles: No Restrictions (i.e., 'NULL' or 'QF')
#'       -- for audio=='Mandarin', subtitles=='NULL', however
#'          for audio=='English', subtitles=={'NULL'|'QF'},
#'          which we will refer to as eng0 and eng1 for 
#'          "English w/ no subtitles" and "English w/ subtitles"
#'   
#'   (*) type: No Restrisctions ('LIVE' or 'VOD')
#'       -- LIVE is always has dataDate == chinaAirDate ==usAirDate+1,
#'          however internally to PPTV it must literally reference
#'          the exact datetime the show was LIVE b/c there also exists
#'          VOD viewership on the LIVE date
#'       -- VOD has any dataDate 
#'       -- so, technically, we want count both together
#'
#'  
#' @param pptv_data1
#' PPTV data set
#'  
#' @param pptv_data2
#' PPTV data set
#'  
#' @param trail (optional; INTEGER)
#' By default, all live data is  retrieved.  Restrict 
#' to trailing N weeks by specifying integer N.  Note
#' that any decimal are automatically floored.
#' 
#' @param View (optional; {TRUE|FALSE} or {0|1})
#' By default (FALSE) data is returned to parent environment
#' (whether that is to a variable or to screen). By
#' flagging View (TRUE), the data is instead routed to 
#' View()
#' 
#' @param more (optional)
#'
#' @export        
pptv.qc.lp7 = function(
  pptv_data1,
  pptv_data2,
  trail = 0,
  View = FALSE
) {
  
  as_on_dt1 = as.Date(max(pptv_data1$dataDate)) + lubridate::days(1)
  as_on_dt2 = as.Date(max(pptv_data2$dataDate)) + lubridate::days(1)
  
  # CHECK DATES:  For consistency ensure that as_on_dt1 > as_on_dt2
  #   The reason is that we are see if any changes are in the
  #   "now" file vs the "then" file.
  if(as_on_dt1 < as_on_dt2) {
    as_on_dt_now = as_on_dt2
    as_on_dt_then = as_on_dt1
    now = pptv_data2
    then = pptv_data1
  } else {
    as_on_dt_now = as_on_dt1
    as_on_dt_then = as_on_dt2
    now = pptv_data1
    then = pptv_data2
  }
  
  live_now  = pptv.lp7( now, trail=trail)
  live_then = pptv.lp7(then, trail=trail)
  
  # Want to JOIN on liveAir, show, audio, 
  #   subtitle (in case its implemented in future)
  #
  # [1] Changes totUniq and totMin colnames to avoid JOIN
  #     giving arbitrary names to replicated colnames
  colnames(live_now) = c("usAirDate","chinaAirDate","dataDate",
                       "show","type","audio","subtitle",
                       "totUniqNow", "totMinNow", "totViewNow")
  colnames(live_then) = c("usAirDate","chinaAirDate","dataDate",
                        "show","type","audio","subtitle",
                       "totUniqThen", "totMinThen", "totViewThen")
  
  # [2] INNER JOIN Now w/ Then:  (Now) IJ (Then)
  ij = dplyr::inner_join(live_now, live_then,  by=c("usAirDate","chinaAirDate","dataDate",
          "show","type","audio","subtitle"))
       
  diffs = ij %>%
      dplyr::mutate(
          diffUniq = dplyr::coalesce(totUniqNow,0) - dplyr::coalesce(totUniqThen,0),
          diffMin  = dplyr::coalesce(totMinNow,0)  - dplyr::coalesce(totMinThen,0),
          diffView  = dplyr::coalesce(totViewNow,0)  - dplyr::coalesce(totViewThen,0)
          ) %>%
      dplyr::filter(diffUniq > 0 | diffMin > 1e-7 | diffView > 0) 
  
  if (nrow(diffs)==0) {
      print("The two data sets are consistent!")
  } else {
      if(View==FALSE) { return(as.data.frame(diffs)) } else {View(diffs)}
  } 
}



#===================================================================
#  pptv.qc.nulls
#===================================================================
#     2017-01-27, Kevin Urban (created)
#===================================================================
#' Checks for nulls in the metrics/KPIs in a PPTV data set.
#' 
#' The metrics/KPIs are:  
#'     totView,  totUniq,  totMin, vpu,  mpv,  mpu
#' 
#' NOTE: pptv.nullcheck only looks for NULLs in the metrics/KPIs.
#' This is because sometimes a dimension parameter, like usAirDate,
#' is assigned a NULL value (e.g., clips that did not air in 
#' the U.S. do not have finite usAirDate values).
#'  
#' We found that data with finite values in the 2017-01-19 
#' data set no showed up with NULL values in the 2017-01-26
#' data set.  In other data sets, we have found extraneous 
#' rows with all NULL values.  
#'      
#' @param pptv_data
#' PPTV data set
#'  
#' @param View (optional; {TRUE|FALSE} or {0|1})
#' By default (FALSE) data is returned to parent environment
#' (whether that is to a variable or to screen). By
#' flagging View (TRUE), the data is instead routed to 
#' View()
#'          
#' @export        
pptv.qc.nulls = function(
  pptv_data,
  View = FALSE
){
  
  # Get Data from thsWk ("This Week") and lstWk ("Last Week")
  as_on_dt = as.Date(max(pptv_data$dataDate)) + lubridate::days(1)
  
  # When checking for nulls, we are looking for them in the metrics
  #   and KPIs only.  In this view, we take out the columns that could
  #   accidentally affect our goal.  For example, oftentimes usAirDate
  #   is not filled in, e.g., for some kind of clip.  We do not want to
  #   flag those!
  rowsWithNull = pptv_data %>% 
      dplyr::select(
          -chinaAirDate,-usAirDate,-show,-showTitle,
          -audio,-game,-subtitle
          ) %>%
      is.na() %>%
      rowSums() > 0  # Make Logical Vector for Subsetting
  
  nulls = pptv_data[rowsWithNull,]
  #nulls = thsWk[rowSums(is.na(thsWk%>%select(matchDate)))>0,]
  
  if(View==TRUE) {View(nulls)} else {return(as.data.frame(nulls))}
  
} # endFcn



#===================================================================
#  pptv.qc.clipsVsFull
#===================================================================
#' Analyze show titles in PPTV data sets.
#' 
#' This function figures out if show titles are consistent between
#' content versions full (version=='Full Show') and clip (version!='Full Show').
#' 
#' @param pptvData 
#' This function only takes pptvData.
#' 
#' @return
#' Show titles...
#' 
#' @export
pptv.qc.clipVsFull = function(pptvData) {
    clip = pptvData %>% dplyr::filter(version!='Full Show') %>% dplyr::distinct(showTitle)
    full = pptvData %>% dplyr::filter(version=='Full Show') %>% dplyr::distinct(showTitle)
    list(
        clip_minus_full = setdiff(clip, full),
        full_minus_clip = setdiff(full, clip)
    )
}
