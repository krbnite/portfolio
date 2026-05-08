#' LIVE+7 for Raw and Smackdown
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
pptv.viz.lp7 = function(
    pptv_data,
    width=9,
    height=6,
    legend=FALSE,
    to_png="",
    to_pdf=""
){
    library(tidyr)
    library(scales)
    
    #===========================================================================
    #      GET DATA
    #===========================================================================
    lp7 = pptv.lp7(pptv_data, agg=1) 
    
    #===========================================================================
    #      SUBSET DATA INTO RAW/SD LIVE/LIVE+7
    #===========================================================================
    # NOTE:  This plot does not actually use the TrlAvg Stff
    #   -- maybe take out at one point
    sd_lp7 = lp7 %>%
        dplyr::filter(show=="Smackdown", audio!="--") %>%
        dplyr::ungroup() %>%
        dplyr::mutate(
            minTrlAvg  = mean(c(lag(totMin) , lag(totMin,2),  lag(totMin,3),  lag(totMin,4)),  na.rm=TRUE),
            viewTrlAvg = mean(c(lag(totView), lag(totView,2), lag(totView,3), lag(totView,4)), na.rm=TRUE),
            diffMin = (totMin-minTrlAvg)/minTrlAvg,
            diffView = (totView-viewTrlAvg)/viewTrlAvg,
            subtitle = ifelse(subtitle=="--", "No Subtitles", "Subtitles"),
            asset = interaction(audio, subtitle, sep=", ")
        ) 
    raw_lp7 = lp7 %>%
        dplyr::filter(show=="Mon Night Raw", audio!="--") %>%
        dplyr::ungroup() %>%
        dplyr::mutate(
            minTrlAvg  = mean(c(lag(totMin) , lag(totMin,2),  lag(totMin,3),  lag(totMin,4)),  na.rm=TRUE),
            viewTrlAvg = mean(c(lag(totView), lag(totView,2), lag(totView,3), lag(totView,4)), na.rm=TRUE),
            diffMin = (totMin-minTrlAvg)/minTrlAvg,
            diffView = (totView-viewTrlAvg)/viewTrlAvg,
            subtitle = ifelse(subtitle=="--", "No Subtitles", "Subtitles"),
            asset = interaction(audio, subtitle, sep=", ")
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
    mx_view_lp7  = 1e4*round(max(c(raw_lp7$totView,  raw_lp7$totView))/1e4)
    mx_mins_lp7  = 1e5*round(max(c(raw_lp7$totMin,   raw_lp7$totMin))/1e5 )
    
    
    #===========================================================================
    #    Construct Plots
    #===========================================================================
    lp7_sd_view =   ggplot2::ggplot(data=sd_lp7) +
        ggplot2::geom_line(ggplot2::aes(x=usAirDate, y=totView, group=asset, color=asset)) +
        ggplot2::coord_cartesian(ylim = c(0, mx_view_lp7)) +
        ggplot2::scale_y_continuous(labels=kiloFormat) +
        ggplot2::scale_x_date(labels = scales::date_format("%b-%y")) +
        ggplot2::ggtitle("Smackdown Live") +
        ggplot2::labs(x="Air Date", y="Views") +
        ggplot2::guides(color=FALSE)
    lp7_sd_min = ggplot2::ggplot(data=sd_lp7) +
        ggplot2::geom_line(ggplot2::aes(x=usAirDate, y=totMin, group=asset, color=asset)) +
        ggplot2::coord_cartesian(ylim = c(0, mx_mins_lp7)) +
        ggplot2::scale_y_continuous(labels=megaFormat) +
        ggplot2::scale_x_date(labels = scales::date_format("%b-%y")) +
        ggplot2::ggtitle("Smackdown Live") +
        ggplot2::labs(x="Air Date", y="Minutes")+
        ggplot2::guides(color=FALSE)
    lp7_raw_view = ggplot2::ggplot(data=raw_lp7) +
        ggplot2::geom_line(ggplot2::aes(x=usAirDate, y=totView, group=asset, color=asset)) +
        ggplot2::coord_cartesian(ylim = c(0, mx_view_lp7)) +
        ggplot2::scale_y_continuous(labels=kiloFormat) +
        ggplot2::scale_x_date(labels = scales::date_format("%b-%y")) +
        ggplot2::ggtitle("Monday Night Raw") +
        ggplot2::labs(x="Air Date", y="Views")+
        ggplot2::guides(color=FALSE)
    lp7_raw_min = ggplot2::ggplot(data=raw_lp7) +
        ggplot2::geom_line(ggplot2::aes(x=usAirDate, y=totMin, group=asset, color=asset)) +
        ggplot2::coord_cartesian(ylim = c(0, mx_mins_lp7)) +
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
        lgnd =  ggplot2::ggplot(data=sd_lp7) +
            ggplot2::geom_line(ggplot2::aes(x=usAirDate, y=totView, group=asset, color=asset)) +
            ggplot2::guides(color=ggplot2::guide_legend(title=NULL))
        legend <- g_legend(lgnd)
        pptv.viz(legend, cols=1, 
                  width=2.5, height=1.5, 
                  to_png=to_png, to_pdf=to_pdf, newWay=TRUE)
    } else {
        pptv.viz(lp7_raw_view, lp7_sd_view, 
                  lp7_raw_min, lp7_sd_min, cols=2, 
                  width=width,  height=height, 
                  to_png=to_png, to_pdf=to_pdf, newWay=TRUE)
    }
}


