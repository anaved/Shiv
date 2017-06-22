# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__ = "naved"
__date__ = "$8 Jul, 2010 2:23:58 PM$"

from smtplib import SMTPException
import smtplib

from settings import APP_EMAIL_ID, APP_SMTP_SERVER


def send_simple_mail(receivers, message, smtp_server=APP_SMTP_SERVER, sender=APP_EMAIL_ID):
    try:
       smtpObj = smtplib.SMTP(smtp_server)
       smtpObj.sendmail(sender, receivers, message)
    except SMTPException:
       raise "Message sending failed"

