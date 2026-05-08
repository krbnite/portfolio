import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import re
import bs4
from tabulate import tabulate


def simple_email(
    subject,
    body,
    sender,
    pswd,
    recipient=None,
    etype='plain'
):
    """Basic single-recipient email — the simplest possible wrapper around smtplib."""
    if recipient is None:
        recipient = sender
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, etype))
    domain = sender.split('@')[1]
    server = smtplib.SMTP('smtp.' + domain, 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(sender, pswd)
    server.sendmail(sender, recipient, msg.as_string())


def send_email(
    subject,
    body,
    sender,
    password,
    recipients=None,
    images=None,
    tables=None,
    attach_html=True
):
    """Full-featured email: HTML body, inline images, pandas table rendering, attachments.

    Usage with tables:
        html = "<p>Here is your data:</p>{0}<p>And more:</p>{1}"
        send_email(..., tables=[df1, df2])

    Inline images (referenced in HTML body via cid):
        html = '<img src="cid:path/to/image.png">'
        send_email(..., body=html)
    """
    recipients = [] if recipients is None else recipients
    images = [] if images is None else images
    tables = [] if tables is None else tables

    COMMASPACE = ', '
    msg = MIMEMultipart()
    msg['From'] = sender

    if isinstance(recipients, str):
        recipients = [recipients]
    if len(recipients) == 0:
        recipients = [sender]
    msg['To'] = COMMASPACE.join(recipients)
    msg['Subject'] = subject

    html = body
    text = bs4.BeautifulSoup(html, 'lxml').text
    if len(tables) > 0:
        html_tables = [tabulate(tbl, headers=tbl.columns, tablefmt='html') for tbl in tables]
        html = html.format(*html_tables)
        text_tables = [tabulate(tbl, headers=tbl.columns, tablefmt='grid') for tbl in tables]
        text = text.format(*text_tables)
    if attach_html:
        msg.attach(MIMEText(html, 'html'))
    msg.attach(MIMEText(text))

    if isinstance(images, str):
        images = [images]
    for image in images:
        with open(image, 'rb') as fp:
            img = MIMEImage(fp.read())
        msg.attach(img)

    # Scan HTML body for inline image references (cid:...) and attach them.
    start = 0
    while True:
        match = re.search("""img src=["']cid:""", html[start:])
        if match is None:
            break
        # NOTE 2017-10-24: attaching inline and as-attachment simultaneously
        #   doesn't work cleanly — the image goes one way or the other, not both.
        pos1 = start + match.end()
        pos2 = pos1 + re.search("""["']""", html[pos1:]).start()
        filename = html[pos1:pos2].strip()
        with open(filename, 'rb') as fp:
            img = MIMEImage(fp.read())
        img.add_header('Content-ID', '<' + filename + '>')
        msg.attach(img)
        start = pos2

    domain = sender.split('@')[1]
    server = smtplib.SMTP('smtp.' + domain, 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(sender, password)
    server.sendmail(sender, recipients, msg.as_string())


def commatize(num):
    return '{:,}'.format(int(round(num)))