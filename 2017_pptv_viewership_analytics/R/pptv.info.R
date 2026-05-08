#' Get info on pptvR usage.
#' 
#' Bla, bla
#' 
#' @param type
#' 
#' @export
#$
pptv.info = function(type="")
{
    if (type=="") {
        cat("\n",
            "    # Get PPTV data from RedShift",
            "    #  -- not yet fully debugged, so just do from Excel file",
            "    con = rsConnect()",
            "    pptv_data1 = pptv.query(as_on_dt, con)",
            "    pptv_data2 = pptv.query(as_on_dt - lubridate::weeks(1), con)",
            "    #  -- Get PPTV data from Excel files (installed w/ package)",
            "    pptv_data1 = pptv.query(as_on_dt)",
            "    pptv_data2 = pptv.query(as_on_dt - lubridate::weeks(1))",
            "",
            "    # Generate list of quality check results",
            "    qc = pptv.qc(pptv_data1, pptv_data2)",
            "",
            "    # Generate tables computed by Offshore Team",
            "    offshore = pptv.offshore(pptv_data1)",
            "",
            "    # Look at the Offshore Tables, e.g.:",
            "    offshore$topNmatches",
            "",
            "    # Generate vizualizations used in report",
            "    #  -- saves to current working director ",
            "    pptv.viz.live(pptv_data1, to_pdf='live')", 
            "    pptv.viz.lp7(pptv_data1,  to_pdf='lp7')", 
            "    pptv.viz.short(pptv_data1, to_pdf='shortform')",
            "",
            "    # Look at other plots (not currently used in report)",
            "    pptv.viz.ubound(pptv_data1)   # optional: to_pdf='ubound'",
            "    pptv.viz.webcal(as_on_dt)     # mutlipe device, type options",
            "",
            sep="\n")
    }
}


#=============================================================================
#' Get info on pptvR usage (alias for pptv.info).
#' 
#' Bla, bla
#' 
#' @param type
#' 
#' @export
pptv.help = pptv.info