#' Specify as_on_dt to load most recent PPTV daily data.
#'  
#' EXCEL:  For the first several months, we received PPTV data
#' in Excel files only.  This was the original data
#' importation function used to bring PPTV data into R.
#' 
#' REDSHIFT:  At one point, we got things into RedShift,
#' however there were several hiccups.  The early stuff
#' might not be trustworthy (unless DE went back and
#' fixed those).  However, anything after say 2017-04-xx
#' is probably good!
#' 
#' NOTE:  pptv.query.excel, pptv.redshift, and other helper functions
#'   are available to view and edit in the pptv.query text file.
#'      
#' @param as_on_dt (character or Date)
#' User may provide any date in the form YYYY-MM-DD, 
#' however it will be converted to the nearest, 
#' previous as_on_dt for which PPTV provided a data 
#' set.
#' 
#' @param sdstar
#' If TRUE, then "Smackdown" and "Smackdown*" are distinguishable 
#' show titles.  By default, "Smackdown*" is converted to "Smackdown".
#'          
#' @return All PPTV data with given as_on_dt.         
#' 
#' @examples 
#' data = pptv.query.excel("2017-03-09")
#'          
#' @importFrom magrittr "%>%"
#' @export        
#' 
#============================================================
#  HISTORY
# 
#      2017-04-20, Kevin Urban (created)
#
#============================================================
#$
pptv.query = function(
    as_on_dt, 
    con=NA, 
    web=FALSE,
    sdstar=FALSE
) {
    which_db = class(con)[1]
    if (web==FALSE) {
        if (which_db != "PostgreSQLConnection") {
            print("Extracting viewership data from Excel...")
            pptv_data = pptv.query.excel(as_on_dt, sdstar=sdstar)
        } else {
            print("Extracting viewership data from RedShift...")
            pptv_data = pptv.query.redshift(as_on_dt, con, sdstar=sdstar)
        }
    } else {
        print("Extracting web data from Excel...")
        pptv_data = pptv.query.webdata(as_on_dt)
    }
    # Output
    pptv_data
}
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


#' @export
pptv.query.redshift = function(
    as_on_dt,
    con,
    sdstar=FALSE
) {
# https://stat.ethz.ch/R-manual/R-devel/library/base/html/Encoding.html
  as_on_dt = as.Date(as_on_dt)
  data = RPostgreSQL::dbGetQuery(con, paste0("
      SELECT 
        match_date,  gmt_plus_8,  date,  show,  
        show_title,  game,  type,  audio_version,  
        version,  subtitle,  payment,
        total_views,  total_uniques,  total_mins,
        avg_views_per_unique,  avg_mins_per_view,  avg_mins_per_unique
      FROM raw_china_pptv
        WHERE as_on_date='",as_on_dt,"';"))
      
  #-------------------------------------------
  #--------      Clean Up Data    ------------
  #-------------------------------------------
  # vpu: avg views per unique
  # mpv: avg minutes per view
  # mpu: avg minutes per unique
  colnames(data) = c("usAirDate","chinaAirDate","dataDate","show", 
                     "showTitle","game","type","audio",
                     "version","subtitle","payment",
                     "totView", "totUniq","totMin",
                     "vpu","mpv","mpu")
  data$usAirDate=as.Date(data$usAirDate)
  data$chinaAirDate=as.Date(data$chinaAirDate)
  data$dataDate=as.Date(data$dataDate)
  data$show = enc2utf8(data$show)
  data$showTitle = enc2utf8(data$showTitle)
  data$game = enc2utf8(data$game)
  # Should probably go through and just use NULLs again in all the other code...
  data$subtitle[data$subtitle=="NULL"]="--"
  data$audio[data$audio=="NULL"]="--"
  if (sdstar==FALSE) {
      data$show[data$show=="Smackdown*"] = "Smackdown"
  } 
  
  # Seems like this ShowTitle formatter is still necessary for RedShift data
  data = pptv.showTitle(data)
  data$totMin = as.numeric(data$totMin)
  data$totUniq = as.numeric(data$totUniq)
  data$totView = as.numeric(data$totView)
  data$mpv = as.numeric(data$mpv)
  data$mpu = as.numeric(data$mpu)
  return(dplyr::as.tbl(data))
}
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


#' @export
pptv.query.excel = function(
    as_on_dt,
    sdstar=FALSE
) {
    
    #************* BEGIN BODY ******************
    as_on_dt = as.Date(as_on_dt)
    
    #-------------------------------------------
    #--------        Get Data       ------------
    #-------------------------------------------
    # NOTES: http://r-pkgs.had.co.nz/data.html
    filename = paste0(as_on_dt,"__PPTV-Daily-CSV.xlsx")
    path2data=system.file(filename, package = "pptvR")
    if (path2data=="") warning("No file found.")
    data = readxl::read_excel(path2data, 
                              sheet="Daily Data",
                              col_types=c("date","date","date","text",
                                          "text","text","text","text","text","text","text", 
                                          "numeric","numeric","numeric","numeric","numeric","numeric"))
    #na=NA)
    #-------------------------------------------
    #--------      Clean Up Data    ------------
    #-------------------------------------------
    # vpu: avg views per unique
    # mpv: avg minutes per view
    # mpu: avg minutes per unique
    colnames(data) = c("usAirDate","chinaAirDate","dataDate","show",
                       "showTitle","game","type","audio","version","subtitle","payment",
                       "totView", "totUniq","totMin","vpu","mpv","mpu")
    data$show=trimws(data$show)
    data$showTitle=trimws(data$showTitle)
    data$game=trimws(data$game)
    data$type=trimws(data$type)
    data$audio=trimws(data$audio)
    data$version=trimws(data$version)
    data$subtitle=trimws(data$subtitle)
    data$payment=trimws(data$payment)
    data$usAirDate=as.Date(data$usAirDate)
    data$chinaAirDate=as.Date(data$chinaAirDate)
    data$dataDate=as.Date(data$dataDate)
    data$subtitle[data$subtitle=="NULL"]="--"
    data$audio[data$audio=="NULL"]="--"
    
    if (sdstar==FALSE) {
        data$show[data$show=="Smackdown*"] = "Smackdown"
    } 
    
    data = pptv.showTitle(data)
    
    #setwd(old_dir)
    return(data) 
}
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# SHOW TITLES
#' Clean up Chinese characters in Show Titles.
#' 
#' This function ensures readability of the Show Titles.
#' 
#' @param pptv_data 
#' This function only takes pptv_data.
#' 
#' @param sdstar
#' Defaults to FALSE. If true, the SD* shows are separated
#' from the SD shows.  For some reason within the first month
#' or so of PPTV data, this was a thing.  I'm pretty sure you won't
#' have to ever set this keyword to TRUE, but it's there just in
#' case.
#' 
#' @return
#' pptv_data w/ formatted showTitles data.
#' 
#' @export
pptv.showTitle = function(
    pptv_data
) {
    show = tolower(pptv_data$show)
    showTitle = tolower(pptv_data$showTitle)
    # game = pptv_data$game
    
    # NXT
    # 2017-04-20:  
    # At one point, PPTV stopped including the word "takeover" in their
    #   takeover shorts, so we've got to do this.
    nxt_index = (show=="nxt") & !is.na(show)
    nxt = showTitle[nxt_index] 
    temp = sapply(nxt, function(x) {stringr::str_extract(x,'[NXTnxt]{3}[0-9]{3}|takeover[ ][A-z]+')})
    nxt[!is.na(temp)] = temp[!is.na(temp)]
    nxt[is.na(temp)] = "takeover"
    showTitle[nxt_index] = nxt
    
    #-------------------------------------------------
    # CWC
    #-------------------------------------------------
    cwc_index = (show=="cwc") & !is.na(show)
    cwc = showTitle[cwc_index]
    showTitle[cwc_index] =  
        sapply(cwc, function(x) {stringr::str_extract(x,'[CWcw]{3}[0-9]{3}')})
    
    #-------------------------------------------------
    # Raw
    #-------------------------------------------------
    mnr_index = (show=="mon night raw") & !is.na(show)
    mnr = showTitle[mnr_index]
    temp1 =  sapply(mnr, function(x) {stringr::str_extract(x,'raw.+[0-9]{3,4}')})
    temp2 = paste0(substring(temp1,1,3),  substring(temp1,5))
    showTitle[mnr_index] = temp2 
    
    
    #-------------------------------------------------
    # SmackDown
    #-------------------------------------------------
    #temp =  sapply(showTitle[show=="Smackdown"], 
    sd_index = stringr::str_detect(show,"smackdown") & !is.na(show)
    sd = showTitle[sd_index]
    temp1 =  sapply(sd, function(x) {stringr::str_extract(x,'smackdown.+[0-9]{3,4}')})
    temp2 = paste0(substring(temp1,1,9),  substring(temp1,11))
    # This way takes way longer...
    #temp2 = paste0(sapply(temp, function(x) {stringr::str_extract(x,'smackdown')}),
    #              sapply(temp, function(x) {stringr::str_extract(x,'[0-9]{3,4}$')}))
    showTitle[sd_index] = temp2
    
    #-------------------------------------------------
    # PPV TLC
    #-------------------------------------------------
    ppv_tlc_index = (show=="ppv-tlc") & !is.na(show)
    showTitle[ppv_tlc_index] =  
        sapply(showTitle[ppv_tlc_index], 
               function(x) {paste0('tlc ', stringr::str_extract(x,'[0-9]{4}'))})
    
    #-------------------------------------------------
    # PPV Slam
    #-------------------------------------------------
    ppv_ss_index = (show=="ppv-survivor series") & !is.na(show)
    showTitle[ppv_ss_index] =  
        sapply(showTitle[ppv_ss_index], 
               function(x) {paste0('slam ', stringr::str_extract(x,'[0-9]{4}'))})
    
    #-------------------------------------------------
    # PPV Rumble
    #-------------------------------------------------
    ppv_rr_index = (show=="ppv-royal rumble") & !is.na(show)
    showTitle[ppv_rr_index] =  
        sapply(showTitle[ppv_rr_index], 
               function(x) {paste0('rumble ', stringr::str_extract(x,'[0-9]{4}'))})
    
    #-------------------------------------------------
    # PPV Fastlane
    #-------------------------------------------------
    ppv_fl_index = (show=="ppv-fastlane") & !is.na(show)
    showTitle[ppv_fl_index] =  
        sapply(showTitle[ppv_fl_index], 
               function(x) {paste0('fastlane ', stringr::str_extract(x,'[0-9]{4}'))})
    
    #-------------------------------------------------
    # PPV Fastlane
    #-------------------------------------------------
    ppv_wm_index = (show=="ppv-wrestlemania") & !is.na(show)
    showTitle[ppv_wm_index] =  
        sapply(showTitle[ppv_wm_index], 
               function(x) {paste0('wrestlemania ', stringr::str_extract(x,'[3-9][0-9]'))})
    
    #===================================================
    #  Return Output
    #===================================================
    pptv_data$showTitle = showTitle
    pptv_data
} 




#===================================================================
#  pptv.query.webdata
#===================================================================
#      2017-04-20, Kevin Urban (created)
#===================================================================
#' Specify as_on_dt to load most recent PPTV data set.
#'  
#' For the first several months, we received PPTV data
#' in Excel files only.  This was the original data
#' importation function used to bring PPTV data into R.
#'      
#' @param as_on_dt 
#' Defaults to Sys.Date(), which is converted to nearest
#' valid as_on_dt previous to Sys.Date().
#' User may provide any date in the form YYYY-MM-DD, 
#' which will be converted to the nearest valid
#' as_on_dt, if necessary.
#'          
#' @return All PPTV web data with given as_on_dt (or nearest valid 
#' as_on_dt previous to provided as_on_dt).         
#' 
#' @examples 
#' data = pptv.webdata("2017-03-09")
#'          
#' @importFrom magrittr "%>%"
#' @export        
#' 
#$
# NOTE:
# You will notice that we compute Date + agg_day-wdata.
#  -- this is b/c EXL has traditionally labeled their columns by
#     the "week ending on" date
#  -- i.e., they were computing aggs for the "week starting on"
#     the previous Monday
pptv.query.web = function(
    as_on_dt=Sys.Date(),
    agg=FALSE,
    day1="Monday"  # Other days not yet implemented
) {
  # Find nearest valid as_on_dt previous to provided as_on_dt
  as_on_dt = as.Date(as_on_dt)
  list_of_dataset_dates = system.file(package="pptvR") %>% 
      list.files(pattern="Webpage") %>% 
      substring(1,10) %>% 
      as.Date()
  valid_index = sort.int(as.numeric(as_on_dt - list_of_dataset_dates), index=1)$ix[1]
  valid_as_on_dt = list_of_dataset_dates[valid_index]

  
  #-------------------------------------------
  #--------        Get Data       ------------
  #-------------------------------------------
  print(paste0("Extracting Web Data from ",valid_as_on_dt,"__Webpage-Data.xlsx..."))
  filename = paste0(valid_as_on_dt,"__Webpage-Data.xlsx")
  path2data=system.file(filename, package = "pptvR")
  data = readxl::read_excel(path2data, 
           skip=2,
           col_types=c("date","numeric","numeric","numeric","numeric","numeric","numeric"))
           #na=NA)
  #-------------------------------------------
  #--------      Clean Up Data    ------------
  #-------------------------------------------
  # vpu: avg views per unique
  # mpv: avg minutes per view
  # mpu: avg minutes per unique
  colnames(data) = c("Date", "Web_PV", "Web_UV", "App_PV", "App_UV", "Total_PV", "Total_UV")
  
  if (agg==TRUE) {
      day1_1 = substring(toupper(day1),1,1)
      day1_2 = substring(tolower(day1),2,3)
      day1 = paste0(day1_1, day1_2)
      day1 = dplyr::recode(day1, Sun=1, Mon=2, Tues=3, Wed=4,
                              Thurs=5, Fri=6, Sat=7)
      nudge = (day1+1) %% 7
      ### Actually... no other days beside "Monday" are supported yet.
      data = data %>%
          dplyr::mutate(
              wday = lubridate::wday(Date),
              Date = dplyr::recode(wday, 
                     "1" = Date - lubridate::days((wday-day1) %% 7),
                     "2" = Date - lubridate::days((wday-day1) %% 7),
                     "3" = Date - lubridate::days((wday-day1) %% 7),
                     "4" = Date - lubridate::days((wday-day1) %% 7),
                     "5" = Date - lubridate::days((wday-day1) %% 7),
                     "6" = Date - lubridate::days((wday-day1) %% 7),
                     "7" = Date - lubridate::days((wday-day1) %% 7) )
          ) %>%
          dplyr::group_by(Date) %>%
          dplyr::summarize(
              Web_PV=sum(Web_PV), 
              Web_UV=sum(Web_UV),
              App_PV=sum(App_PV),
              App_UV=sum(App_UV),
              Total_PV=sum(Total_PV),
              Total_UV=sum(Total_UV)
          ) 
  }
  return(as.data.frame(data))
}
