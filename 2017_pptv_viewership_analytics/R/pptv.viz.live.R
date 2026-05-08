#' LIVE for Raw and Smackdown
#' 
#' @param pptv_data
#' 
#' @param width
#' Defaults to 9 inches (fits PowerPoint template well)
#' 
#' @param height
#' Defaults to 6 inches (fits PowerPoint template well)
#' 
#' @param to_png
#' 
#' @param to_pdf
#' Looks the best!
#' 
#' @export
#$
pptv.viz.live = function(
    pptv_data,
    width=9,
    height=6,
    legend=FALSE,
    to_png="",
    to_pdf=""
) {
    
    library(tidyr)
    
    #===========================================================================
    #      GET DATA
    #===========================================================================
    live = pptv.live(pptv_data)
    
    #===========================================================================
    #      SUBSET DATA INTO RAW/SD LIVE/LIVE+7
    #===========================================================================
    sd_live = live %>%
        dplyr::filter(show=="Smackdown") %>%
        dplyr::ungroup() %>%
        dplyr::mutate(
            minTrlAvg  = mean(c(lag(totMin) , lag(totMin,2),  lag(totMin,3),  lag(totMin,4)),  na.rm=TRUE),
            uniqTrlAvg = mean(c(lag(totUniq), lag(totUniq,2), lag(totUniq,3), lag(totUniq,4)), na.rm=TRUE),
            diffMin = (totMin-minTrlAvg)/minTrlAvg,
            diffUniq = (totUniq-uniqTrlAvg)/uniqTrlAvg
        ) 
    raw_live = live %>%
        dplyr::filter(show=="Mon Night Raw") %>%
        dplyr::ungroup() %>%
        dplyr::mutate(
            minTrlAvg  = mean(c(lag(totMin) , lag(totMin,2),  lag(totMin,3),  lag(totMin,4)),  na.rm=TRUE),
            uniqTrlAvg = mean(c(lag(totUniq), lag(totUniq,2), lag(totUniq,3), lag(totUniq,4)), na.rm=TRUE),
            diffMin = (totMin-minTrlAvg)/minTrlAvg,
            diffUniq = (totUniq-uniqTrlAvg)/uniqTrlAvg
        ) 
    #===========================================================================
    #     PLOTTING PARAMETERS
    #===========================================================================
    kiloFormat = function(x) {
        paste0(as.character(x/1e3), "K")
    }
    megaFormat = function(x) {
        paste0(as.character(x/1e6), "M")
    }
    mx_uniq = 1e4*round(max(c(raw_live$totUniq, raw_live$totUniq))/1e4)
    mx_mins = 1e5*round(max(c(raw_live$totMin,  raw_live$totMin))/1e5 )
    
    
    #===========================================================================
    #    Construct Plots
    #===========================================================================
    live_sd_uniq = ggplot2::ggplot(data=sd_live) +
        ggplot2::geom_line(ggplot2::aes(x=usAirDate, y=totUniq, group=audio, color=audio)) +
        ggplot2::coord_cartesian(ylim = c(0, mx_uniq)) +
        ggplot2::scale_y_continuous(labels=kiloFormat) +
        ggplot2::scale_x_date(labels = scales::date_format("%b-%y")) +
        ggplot2::ggtitle("Smackdown Live") +
        ggplot2::labs(x="Air Date", y="Uniques") +
        ggplot2::guides(color=FALSE)
    live_sd_min = ggplot2::ggplot(data=sd_live) +
        ggplot2::geom_line(ggplot2::aes(x=usAirDate, y=totMin, group=audio, color=audio)) +
        ggplot2::coord_cartesian(ylim = c(0, mx_mins)) +
        ggplot2::scale_y_continuous(labels=megaFormat) +
        ggplot2::scale_x_date(labels = scales::date_format("%b-%y")) +
        ggplot2::ggtitle("Smackdown Live") +
        ggplot2::labs(x="Air Date", y="Minutes") +
        ggplot2::guides(color=FALSE)
    live_raw_uniq = ggplot2::ggplot(data=raw_live) +
        ggplot2::geom_line(ggplot2::aes(x=usAirDate, y=totUniq, group=audio, color=audio)) +
        ggplot2::coord_cartesian(ylim = c(0, mx_uniq)) +
        ggplot2::scale_y_continuous(labels=kiloFormat) +
        ggplot2::scale_x_date(labels = scales::date_format("%b-%y")) +
        ggplot2::ggtitle("Monday Night Raw") +
        ggplot2::labs(x="Air Date", y="Uniques") +
        ggplot2::guides(color=FALSE)
    live_raw_min = ggplot2::ggplot(data=raw_live) +
        ggplot2::geom_line(ggplot2::aes(x=usAirDate, y=totMin, group=audio, color=audio)) +
        ggplot2::coord_cartesian(ylim = c(0, mx_mins)) +
        ggplot2::scale_y_continuous(labels=megaFormat) +
        ggplot2::scale_x_date(labels = scales::date_format("%b-%y")) +
        ggplot2::ggtitle("Monday Night Raw") +
        ggplot2::labs(x="Air Date", y="Minutes") +
        ggplot2::guides(color=FALSE)
    
    
    
    #===========================================================================
    #    Final Figure
    #===========================================================================
    if (legend==TRUE) {
        g_legend<-function(a.gplot){
            tmp <- ggplot2::ggplot_gtable(ggplot2::ggplot_build(a.gplot))
            leg <- which(sapply(tmp$grobs, function(x) x$name) == "guide-box")
            legend <- tmp$grobs[[leg]]
            legend
        }
        lgnd =  ggplot2::ggplot(data=sd_live) +
            ggplot2::geom_line(ggplot2::aes(x=usAirDate, y=totView, group=audio, color=audio)) +
            ggplot2::guides(color=ggplot2::guide_legend(title=NULL))
        legend <- g_legend(lgnd)
        pptv.viz(legend, cols=1, 
                  width=2.5, height=1.5, 
                  to_png=to_png, to_pdf=to_pdf, newWay=TRUE)
    } else {
        pptv.viz(live_raw_uniq, live_sd_uniq, 
                  live_raw_min, live_sd_min,  cols=2, 
                  width=width, height=height, 
                  to_png=to_png, to_pdf=to_pdf, newWay=TRUE)
    }
    
    
}