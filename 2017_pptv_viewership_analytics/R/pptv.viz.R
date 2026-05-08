#' Multiple plot function
#'
#' Plot multiple ggplot objects in the same figure.  Pass as manu
#' ggplot objects in as individual inputs (...), or use the plotlist
#' keyboard to input them in a list.  
#' 
#' @param ...
#' Pass in N ggplot objects as the first N positional parameters.
#' 
#' @param plotlist (default: NULL)
#' Pass in a list of ggplot objects using this named parameter.
#' Note: You can use this indpendently of or in conjunction with
#' the first N positional parameters.
#' 
#' @param cols
#' Number of columns in layout
#' 
#' @param layout 
#' A matrix specifying the layout. If present, 'cols' is ignored.
#' If the layout is something like matrix(c(1,2,3,3), nrow=2, byrow=TRUE),
#' then plot 1 will go in the upper left, 2 will go in the upper right, and
#' 3 will go all the way across the bottom.
#' 
#' @param file
#' Not Yet Used in Code. In Future: Option to save figure automatically.
#' 
#' @param width
#' Defaults to 480.
#' 
#' @param height
#' Defaults to 480.
#' 
#' @param to_png
#' 
#' @export
#$
pptv.viz = function(
    ..., 
    plotlist=NULL, 
    file, 
    cols=1, 
    layout=NULL,
    width=4.8,  # inches
    height=4.8, # inches
    to_png="",
    to_pdf="",
    newWay=TRUE
) {
    #library(grid)
    # Plotting to File?
    if (nchar(to_png) > 0) {
        width = 100*width
        height = 100*height
        if (substring(to_png, nchar(to_png)-2) != "png") to_png=paste0(to_png,".png")
        png(to_png, width=width, height=height)
    } else if (nchar(to_pdf) > 0) {
        if (substring(to_pdf, nchar(to_pdf)-2) != "pdf") to_pdf=paste0(to_pdf,".pdf")
        pdf(to_pdf, width=width, height=height)
    }
    
    # Make a list from the ... arguments and plotlist
    plots <- c(list(...), plotlist)
    
    numPlots = length(plots)
    
    # If layout is NULL, then use 'cols' to determine layout
    if (is.null(layout)) {
        # Make the panel
        # ncol: Number of columns of plots
        # nrow: Number of rows needed, calculated from # of cols
        layout <- matrix(seq(1, cols * ceiling(numPlots/cols)),
                         ncol = cols, nrow = ceiling(numPlots/cols))
    }
    
    
    #-------------------------------------------------------------
    #  NEW WAY
    #-------------------------------------------------------------
    if (newWay==TRUE) {
        gridExtra::grid.arrange(..., ncol=cols)
        
    #-------------------------------------------------------------
    #  OLD WAY
    #-------------------------------------------------------------
    } else { 
        
        if (numPlots==1) {
            print(plots[[1]])
            
        } else {
            # Set up the page
            grid::grid.newpage()
            grid::pushViewport(grid::viewport(layout = grid::grid.layout(nrow(layout), ncol(layout))))
            
            # Make each plot, in the correct location
            for (i in 1:numPlots) {
                # Get the i,j matrix positions of the regions that contain this subplot
                matchidx <- as.data.frame(which(layout == i, arr.ind = TRUE))
                
                print(plots[[i]], vp = grid::viewport(layout.pos.row = matchidx$row,
                                                      layout.pos.col = matchidx$col))
            }
        }
    }
    
    # Plotting to File? -- Take 2!
    if(nchar(to_png) > 0 | nchar(to_pdf) > 0) dev.off()
}
