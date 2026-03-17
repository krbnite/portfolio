import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import re
import bs4
from tabulate import tabulate

#---------------------
# Regular Text
#---------------------
# text = "Hi!\nHow are you?\nHere is the link you wanted:\nhttps://www.python.org"
#
#---------------------
# HTML
#---------------------
# html = """\
# <html>
#   <head></head>
#   <body>
#     <p>Hi!<br>
#        How are you?<br>
#        Here is the <a href="https://www.python.org">link</a> you wanted.
#     </p>
#   </body>
# </html>
#
#------------------------------
# How to add tables
#----------------------------
# 
# html = """\
# <html>
#   <head></head>
#   <body>
#     <p>Here is your data:</p>
#     {0}
#     <p>And here is some more:</p>
#     {1}
#   </body>
# </html>
# send_email(..., tables=[tbl1,tbl2], ...)
#

def send_email(
    subject,
    body,
    sender,
    password,
    recipients = None,
    images = None,
    tables = None,
    attach_html=True
):
    """Send an email with optional HTML content, images, and tables."""

    recipients = [] if recipients is None else recipients
    images = [] if images is None else images
    tables = [] if tables is None else tables

    COMMASPACE = ', '
    msg = MIMEMultipart()

    #---------------------------------------------------------
    # HEADER
    #---------------------------------------------------------
    msg['From'] = sender

    #---------------------------------------------------------
    # RECIPIENTS
    #---------------------------------------------------------
    #  -- ensure list type
    if isinstance(recipients, str):
        # Give benefit of doubt: single email address passed as string
        #  --- wait...can't I just accept "email1, email2, ..."?
        recipients = [recipients]
    if len(recipients) == 0:
        recipients = [sender]
    msg['To'] = COMMASPACE.join(recipients)

    #---------------------------------------------------------
    # SUBJECT 
    #---------------------------------------------------------
    msg['Subject'] = subject

    #---------------------------------------------------------
    # BODY
    #---------------------------------------------------------
    # -- if body is not in HTML, 2 copies of text are attached
    html = body
    text = bs4.BeautifulSoup(html,'lxml').text
    if len(tables) > 0:
        # HTML
        html_tables = [tabulate(tbl, headers=tbl.columns, tablefmt="html") for tbl in tables]
        html = html.format(*html_tables)
        text_tables = [tabulate(tbl, headers=tbl.columns, tablefmt="grid") for tbl in tables]
        text = text.format(*text_tables)
    if attach_html == True:
        # Provides attached copy
        msg.attach(MIMEText(html,'html'))
    msg.attach(MIMEText(text))

    #---------------------------------------------------------
    # IMAGE ATTACHMENTS
    #---------------------------------------------------------
    #  -- ensure list type
    if isinstance(images, str):
        # Give benefit of doubt: single email address passed as string
        images = [images]

    if len(images) > 0:
        for image in images:
            fp = open(image, 'rb')
            img= MIMEImage(fp.read())
            fp.close()
            msg.attach(img)

    #---------------------------------------------------------
    # INLINE IMAGES
    #---------------------------------------------------------
    #  -- if message is in html, check for image references and
    #     append to images list
    start=0
    while True:
        match = re.search("""img src=["']cid:""", html[start:])
        if match is not None:
            # NOTE FROM 2017-10-24:
            # For some reason this is not attaching images to attachments... No biggie, but weird.
            #  -- seems I can get it to attach, or go inline, but not both.
            pos1 = start + match.end()
            pos2 = pos1 + re.search("""["']""", html[pos1:]).start()
            filename = html[pos1:pos2].strip()
            fp = open(filename, 'rb')
            img= MIMEImage(fp.read())
            img.add_header('Content-ID', '<'+filename+'>')
            msg.attach(img)
            start = pos2
            fp.close()
        else:
            break


    #---------------------------------------------------------
    # SEND IT OUT!
    #---------------------------------------------------------
    domain = sender.split('@')[1]
    server = smtplib.SMTP('smtp.'+domain, 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(sender, password)
    text = msg.as_string()
    server.sendmail(sender, recipients, text)

#-----------------------------------------------------------
def commatize(num):
    output = "{:,}".format(int(round(num)))
    return output