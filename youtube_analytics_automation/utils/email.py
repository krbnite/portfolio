# we will update this last
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def simple_email(
    subject,
    body,
    sender,
    pswd,
    recipient = None,
    etype = 'plain'
):
    if recipient is None: recipient=sender
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, etype))
    domain = sender.split('@')[1]
    server = smtplib.SMTP('smtp.'+domain, 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(sender, pswd)
    text = msg.as_string()
    server.sendmail(sender, recipient, text)