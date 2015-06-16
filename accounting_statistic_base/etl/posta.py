#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# I find this on site: http://snippets.dzone.com/posts/show/2038
# sorry but, as the publisher, I don't know the origin and the owner of this code
# Let me tell him thank you, very useful code ;)
# 
# The procedure send an E-mail to recipient list with recipient attachment
# The server provider use standard 25 port and no autentication
#
# Ex.:send_mail("riolini@micronaet.it",["info@micronaet.it",],"Prova","Messaggio di prova",["/home/administrator/example.log",],"192.168.100.254")

import smtplib, os
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders

def send_mail(send_from, send_to, subject, text, files=[], server="localhost", username = '', password = '', TLS = False):
    ''' Funzione per inviare mail attraverso un server SMTP (con auth o no)
    '''
    # --------------------------
    # - Preparazione messaggio -
    # --------------------------
    
    assert type(send_to)==list
    assert type(files)==list

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach( MIMEText(text) )

    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(f,"rb").read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)

    # --------------
    # - Invio mail -
    # --------------
    
    if not username: # invio senza autenticazione:
        smtp = smtplib.SMTP(server)
        #smtp.login(user, password)
        smtp.sendmail(send_from, send_to, msg.as_string())
        smtp.close()
    elif TLS: # invio con autenticazione TLS
        smtp = smtplib.SMTP("%s:%s" % (server, port))
        smtp.starttls()
        smtp.login(username, password)
        smtp.sendmail(fromaddr, send_to, msg)
        smtp.quit()
    else:
        pass # per adesso non necessario

def raise_error(text, file_name):
    print text
    file_name.write(text + "\n")                          
    return

