#' Retrieve PPTV aggregated to the LIVE level.
#' 
#' PPTV seems to have changed the way they denote 
#' usAirDate ("matchDate"). This new version seems to capture
#' that.  (For more details on this function in general,
#' see pptv.lp7 notes.)
#' 
#' ATTRIBUTES OF RECENT L+7 VIEWERSHIP:
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
#' @param pptv_data
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
#' @param agg 
#' Return all results that meet "LIVE+7" restrictions, or
#' just the "LIVE+7" aggregated form?
#'
#' @export        

pptv.lp7 = function(
  pptv_data,
  trail = 0,
  View  = FALSE,
  more  = FALSE,
  agg   = FALSE,
  info  = FALSE
) {
    
  if (info == TRUE) {
    print("Filters PPTV data by: ")
    print("    * show in ('mon night raw', 'smackdown') ")
    print("    * version = 'full show' ")
      
  }
  
  #-------------------------------------------
  #--------        Get Data       ------------
  #-------------------------------------------
  # PPTV Features:
  #   usAirDate,  chinaAirDate,  dataDate,  show,
  #   showTitle,  game,  type,  audioVersion,
  #   version,  subtitle,  totalViews, 
  #   totalUniques,  totalMins, avgViewsPerUnique,
  #   avgMinsPerView, avgMinsPerUnique
    
  as_on_dt = as.Date(max(pptv_data$dataDate, na.rm=TRUE)) + lubridate::days(1)
  
  
  #-------------------------------------------
  #--------     Transform Data     -----------
  #-------------------------------------------
  if(trail==0) {
    pptv_lp7 = pptv_data %>% 
      dplyr::filter(
          tolower(show) %in% c('mon night raw','smackdown'),
          tolower(version) == 'full show',
          dataDate <= chinaAirDate + lubridate::days(6),
          chinaAirDate <= as_on_dt - lubridate::weeks(1))
  } else {
    pptv_lp7 = pptv_data %>% 
      dplyr::filter(
          tolower(show) %in% c('mon night raw','smackdown'),
          tolower(version) == 'full show',
          dataDate <= chinaAirDate + lubridate::days(6),
          chinaAirDate <= as_on_dt - lubridate::weeks(1),
          chinaAirDate >= as_on_dt - lubridate::weeks(trail+1)
          )
  }
  

  #-------------------------------------------
  #--------     Quick View or More?  ---------
  #-------------------------------------------
  if(more==FALSE) {
      pptv_lp7 = pptv_lp7 %>% 
          dplyr::select(
              usAirDate, chinaAirDate, dataDate, show, 
              showTitle, type, audio, subtitle, 
              totUniq, totMin, totView) %>%
          dplyr::arrange(
              usAirDate, show, dplyr::desc(audio))
  } else {
      pptv_lp7 = pptv_lp7 %>% 
          dplyr::select(
              usAirDate, chinaAirDate, dataDate, 
              show, showTitle, type, 
              audio, version, subtitle,
              totUniq, totMin, totView, 
              vpu, mpv, mpu) %>%
          dplyr::arrange(
              usAirDate, show, dplyr::desc(audio))
  }
  
  #-------------------------------------------
  #----   Aggregate by Episode, or Not?   ----
  #-------------------------------------------
  if(agg==TRUE) { 
    pptv_lp7 = temp2 =pptv_lp7 %>%
          dplyr::mutate(
              year = lubridate::year(chinaAirDate),
              week = lubridate::week(chinaAirDate),
              wday = ifelse(
                  show=='Mon Night Raw', 
                  'Monday',
                  'Tuesday'),
              usAirDate = as.Date(paste(year, week, wday), format="%Y %U %A"),
              ggg = as.Date(paste(year, week, wday), format="%Y %U %A"),
              chinaAirDate = usAirDate + lubridate::days(1)
          ) %>%
        dplyr::group_by(
            usAirDate,  chinaAirDate, show, audio, subtitle
            #show,showTitle,audio,subtitle           #
            #year, week, show, audio, subtitle
            ) %>% 
        dplyr::summarize(
            totUniq=sum(totUniq),
            totMin=sum(totMin),
            totView=sum(totView)
            ) %>% 
        dplyr::arrange(
            usAirDate, show, desc(audio))
  }
  
  
  #-------------------------------------------
  #---   Look at it in a spreadsheet?   ------
  #-------------------------------------------
  if(View==FALSE) { return(pptv_lp7) } else {View(pptv_lp7)}
  
} # endFcn 
