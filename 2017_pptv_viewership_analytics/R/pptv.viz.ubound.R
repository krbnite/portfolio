#' For LIVE+7, generate ribbon plot that bounds the uniques.
#' 
#' Since a "unique" in the PPTV is actually only unique up
#' to the particular asset and day (e.g., show, showTitle, 
#' audio, subtitle, device, day), we cannot truly get an 
#' estimate of total unique viewers.  However, we can bound
#' that estimate.  
#' 
#' The count of total uniques itself represents
#' and overshoot --- an upper bound.  Depending on how many
#' people decide to watch a particular episode of Raw on
#' more than one device, on more than one day, in multiple
#' languages, etc, this can be an extremely bad upper bound.
#' However, for a given day and asset, the total views are never 
#' too much more than the total uniques, so it seems likely 
#' that this is not too bad of an upper bound. 
#' 
#' For a lower bound, we used Nielsen data to get an estimate
#' of how long people typically watch Raw or Smackdown.  Specifically,
#' we were provided with the average viewing duration for each episode
#' over the lifetime of PPTV.  We took the median of these averages for
#' each show:  64 minutes for Raw and 46 minutes for Smackdown.
#' By default, the lower bound in this figure is the total number of
#' minutes divided by this number, giving a curve that represents
#' the number of viewers given all viewers watched for the typical
#' duration.
#' 
#' @param pptv_data
#' 
#' @param ymax
#' 
#' @param rmv
#' 
#' @param smv
#' 
#' @param width
#' 
#' @param height
#' 
#' @export
#$
pptv.viz.ubound = function(
    pptv_data,
    t0 = as.Date("2016-06-27"),
    tf = as.Date(Sys.time()),
    yscale=5e5,
    ymax=NULL,
    rmv=64.,
    smv=46.,
    width=9,
    height=6,
    to_png="",
    to_pdf="",
    v2=TRUE
) {
    
    #===========================================================================
    #      GET DATA
    #===========================================================================
    # WARNING:  Still need to make this fcn accept data sets...
    if (v2==TRUE) lp7 = pptv.lp7.v2(pptv_data, agg=1) else lp7 = pptv.lp7(pptv_data, agg=1) 
    
    #===========================================================================
    #      SUBSET DATA INTO RAW/SD LIVE/LIVE+7
    #===========================================================================
    sd = lp7 %>%
        dplyr::filter(show=="Smackdown", audio!="--", 
                      usAirDate >= t0, usAirDate <= tf) %>%
        dplyr::ungroup() %>%
        dplyr::mutate(
            subtitle = ifelse(subtitle=="--", "No Subtitles", "Subtitles"),
            asset = interaction(audio, subtitle, sep=", ")
        )  %>% 
        dplyr::group_by(usAirDate) %>% 
        dplyr::summarize(upperBound=sum(totUniq), lowerBound=sum(totMin)/smv) 
    
    raw = lp7 %>%
        dplyr::filter(show=="Mon Night Raw", audio!="--",
                      usAirDate >= t0, usAirDate <= tf) %>%
        dplyr::ungroup() %>%
        dplyr::mutate(
            subtitle = ifelse(subtitle=="--", "No Subtitles", "Subtitles"),
            asset = interaction(audio, subtitle, sep=", ")
        ) %>% 
        dplyr::group_by(usAirDate) %>% 
        dplyr::summarize(upperBound=sum(totUniq), lowerBound=sum(totMin)/rmv)
    
    #===========================================================================
    #     PLOTTING PARAMETERS
    #===========================================================================
    kiloFormat = function(x) {
        paste0(as.character(x/1e3), "K")
    }
    megaFormat = function(x) {
        paste0(as.character(x/1e6), "M")
    }
    if (yscale < 1e6)  yFormat = kiloFormat else yFormat = megaFormat
    
    if (is.null(ymax)) {
        ymax  = 1e5*round(max(c(raw$upperBound,  sd$upperBound))/1e5)
    }
    
    
    #===========================================================================
    #    Construct Plots
    #===========================================================================
    p1 = 
        ggplot2::ggplot(data=raw) +
        ggplot2::geom_ribbon(ggplot2::aes(x=usAirDate, ymin=lowerBound, ymax=upperBound))+
        ggplot2::geom_smooth(
            method=lm, se=FALSE,
            ggplot2::aes(x=usAirDate, y=(lowerBound+upperBound)/2.0, color="red")) +
        ggplot2::theme(legend.position="none") +
        ggplot2::coord_cartesian(ylim = c(0, ymax)) +
        ggplot2::scale_y_continuous(labels=yFormat) +
        ggplot2::scale_x_date(labels = scales::date_format("%b-%y")) +
        ggplot2::ggtitle("Monday Night Raw (LIVE+7)") +
        ggplot2::labs(x="Air Date", y="Upper and Lower Bounds on Uniques")
    p2 = ggplot2::ggplot(data=sd) +
        ggplot2::geom_ribbon(ggplot2::aes(x=usAirDate, ymin=lowerBound, ymax=upperBound))+
        ggplot2::geom_smooth(
            method=lm, se=FALSE,
            ggplot2::aes(x=usAirDate, y=(lowerBound+upperBound)/2.0, color="red")) +
        ggplot2::theme(legend.position="none") +
        ggplot2::coord_cartesian(ylim = c(0, ymax)) +
        ggplot2::scale_y_continuous(labels=yFormat) +
        ggplot2::scale_x_date(labels = scales::date_format("%b-%y")) +
        ggplot2::ggtitle("Smackdown Live (LIVE+7)") +
        ggplot2::labs(x="Air Date", y="Upper and Lower Bounds on Uniques")
    
    
    pptv.viz(p1, p2, cols=2, width=width, height=height, to_png=to_png, to_pdf=to_pdf)
    # save as 800w x 600h
    
}

       # ggplot2::geom_ribbon(ggplot2::aes(x=usAirDate, ymin=lowerBound, ymax=0.55*(lowerBound+upperBound)), alpha=0.75)+
       # ggplot2::geom_ribbon(ggplot2::aes(x=usAirDate, ymin=0.45*(lowerBound+upperBound), ymax=upperBound), alpha=0.75)+
