#' Total shortform viewership for Raw, Smackdown, and Total
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
pptv.viz.short = function(
    pptv_data,
    width=9,
    height=5,
    to_png="",
    to_pdf=""
) {
    
    shortform = pptv_data %>% 
        dplyr::filter(version %in% c('Other','Cut')) %>% 
        dplyr::mutate(
            year = lubridate::year(dataDate),
            week = lubridate::week(dataDate),
            wday = 'Monday',
            dataWeek = as.Date(paste(year,week,wday), format="%Y %U %A"),
            #show = ifelse(stringr::str_detect(show,'PPV'), 'PPV', show),
            show = ifelse(show=='Smackdown*', 'Smackdown', show),
            #show = ifelse(show %in% c('Mon Night Raw', 'Smackdown', 'PPV'), show, 'Other')
            show = ifelse(show %in% c('Mon Night Raw', 'Smackdown'), show, 'Other')
        ) %>%
        dplyr::filter(show != "Other")  %>%
        dplyr::group_by(dataWeek, show) %>% 
        dplyr::summarize(totMin=round(sum(totMin))) 
    
    totals = shortform %>%
        dplyr::group_by(dataWeek) %>%
        dplyr::summarize(show='Total', totMin=round(sum(totMin)))
    
    shortform = rbind(dplyr::ungroup(shortform), dplyr::ungroup(totals))
    
    
    megaFormat = function(x) {
        paste0(as.character(x/1e6), "M")
    }
    
    plt = ggplot2::ggplot(data=shortform) +
        ggplot2::geom_smooth(ggplot2::aes(x=dataWeek, y=totMin, group=show, color=show), na.rm=TRUE, span=0.3, se=FALSE) +
        ggplot2::geom_point(ggplot2::aes(x=dataWeek, y=totMin, group=show, color=show), alpha=0.5)+
        ggplot2::scale_y_continuous(labels=megaFormat) +
        ggplot2::scale_x_date(labels = scales::date_format("%b-%y")) +
        ggplot2::labs(x="Week", y="Weekly Minutes Viewed")
    
    pptv.viz(plt, width=width, height=height, to_png=to_png, to_pdf=to_pdf)
    
}
