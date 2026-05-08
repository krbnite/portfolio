#' Plot data from Webpage data file on a calendar.
#' 
#' Look at PPTV webpage activity in the familiar setting
#' of a calendar.  The calendar shows one device ("Web", 
#' "App", or "Total") and one metric ("UV" or "PV" for 
#' unique views or page views, respectively).  The default
#' is to display the most recent 3 calendar months, but 
#' this can be tweaked with the N parameter.
#' 
#' @param as_on_dt
#' ....
#' 
#' @param N (default: 3)
#' Specify the number N of most recent months to display.
#' 
#' @param device (default: "Web")
#' Specify the device of interest: "Web", "App", or 
#' "Total".  Note that this parameter is not case
#' sensitive and dependent only on first 3 characters
#' of device name.
#' 
#' @param type (default: unique)
#' Specify the type of data: "Page Views" or "Unique Views".
#' Note that this parameter is not case sensitive and is
#' only dependent on the first character (e.g., type="u"
#' and type="UNIQUE" both specify "Unique Views").
#' 
#' @export
#' 
#===================================================
#  Kevin Urban:  2017-04-20 (Created)
#
pptv.viz.webcal = function(
    as_on_dt, 
    N = 3,
    device = "Web",
    type = "Unique"
) {
    #library(ggplot2)
    #library(dplyr)
    #library(scales)
    #library(zoo)
    
    # Get Web Data
    as_on_dt = as.Date(as_on_dt)
    dat = pptv.query.webdata(as_on_dt)
    
    
    # Compute Minimum Date on Calendar
    min_date =  (as_on_dt - months(N-1)) %>% 
        (function(x) paste(lubridate::year(x), ifelse(lubridate::month(x) < 10, paste0(0,lubridate::month(x)), lubridate::month(x)), "01",  sep="-"))
    dat = dat %>% filter(Date >= min_date)
    
    # Format Data, Create Necessary Cols
    dat$year<-as.numeric(as.POSIXlt(dat$Date)$year+1900)
    # the month too 
    dat$month<-as.numeric(as.POSIXlt(dat$Date)$mon+1)
    # but turn months into ordered facors to control the appearance/ordering in the presentation
    dat$monthf<-factor(dat$month,levels=as.character(1:12),labels=c("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"),ordered=TRUE)
    # the day of week is again easily found
    #dat$weekday = as.POSIXlt(dat$Date)$wday
    dat$weekday = strftime(dat$Date, format="%a")
    # again turn into factors to control appearance/abbreviation and ordering
    # I use the reverse function rev here to order the week top down in the graph
    # you can cut it out to reverse week order
    dat$weekdayf<-factor(dat$weekday,levels=c("Sun","Mon","Tue","Wed","Thu","Fri","Sat"),ordered=TRUE)
    # the monthweek part is a bit trickier 
    # first a factor which cuts the data into month chunks
    dat$yearmonth<-zoo::as.yearmon(dat$Date)
    dat$yearmonthf<-factor(dat$yearmonth)
    # then find the "week of year" for each day
    dat$week <- as.numeric(format(dat$Date,"%W"))
    # and now for each monthblock we normalize the week to start at 1 
    dat<-plyr::ddply(
        dat,plyr::.(yearmonthf),
        transform,
        monthweek=1+week-min(week))
    
    device = substring(tolower(device), 1, 3)
    type   = substring(tolower(type), 1, 1)
    if (device=="web") {
        if (type=="u") {
            plt = ggplot2::ggplot(dat, ggplot2::aes(weekdayf, desc(monthweek), fill=Web_UV))
            fill1="Web"
            fill2="UV"
        } else {
            plt = ggplot2::ggplot(dat, ggplot2::aes(weekdayf, desc(monthweek), fill=Web_PV))
            fill1="Web"
            fill2="PV"
        }
    }
    if (device=="app") {
        if (type=="u") {
            plt = ggplot2::ggplot(dat, ggplot2::aes(weekdayf, desc(monthweek), fill=App_UV))
            fill1="App"
            fill2="UV"
        } else {
            plt = ggplot2::ggplot(dat, ggplot2::aes(weekdayf, desc(monthweek), fill=App_PV))
            fill1="App"
            fill2="PV"
        }
    }
    if (device=="tot") {
        if (type=="u") {
            plt = ggplot2::ggplot(dat, ggplot2::aes(weekdayf, desc(monthweek), fill=Tot_UV))
            fill1="Tot"
            fill2="UV"
        } else {
            plt = ggplot2::ggplot(dat, ggplot2::aes(weekdayf, desc(monthweek), fill=Tot_PV))
            fill1="Tot"
            fill2="PV"
        }
    }
    
   plt + ggplot2::geom_tile(colour = "white") + 
        #facet_grid(year~monthf) + 
        ggplot2::facet_wrap(~year+month) +
        ggplot2::scale_fill_gradient(low="red", high="yellow") +
        ggplot2::theme(axis.text.x = ggplot2::element_text(angle = 90, hjust = 1)) +
        ggplot2::labs(
            title = "Web Unique Views Calendar", 
            subtitle="",
            x="Week of Month", 
            y="",
            fill=paste(fill1,fill2))
} # endPlotFcn

