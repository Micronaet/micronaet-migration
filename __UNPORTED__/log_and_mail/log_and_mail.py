# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields
from datetime import datetime

class logmail_log(osv.osv):
    ''' List of event logged 
    '''
        
    _name = 'logmail.log'
    _description = 'Log mail'

    # utility function:
    def _send_mail(self, cr, uid, ids, context=None):
        ''' Sent list of log elements
            Use the first SMTP server available and get all parameter from 
            log message, logging if the mail is sent or the error raised
            params: from, to (list), subject, text
        '''
        import smtplib, os
        from email.MIMEMultipart import MIMEMultipart
        from email.MIMEBase import MIMEBase
        from email.MIMEText import MIMEText
        from email.Utils import COMMASPACE, formatdate
        from email import Encoders
        import logging

        _logger = logging.getLogger('log_and_mail')
        _logger.info('Schedule event for send log mail')

        #assert type(send_to)==list; assert type(files)==list

        # Read parameter for SMTP from SMTP server list
        smtp_pool = self.pool.get('logmail.smtp')
        smtp_ids = smtp_pool.search(cr, uid, [], context=context)
        if not smtp_ids: 
            return False
            
        send_from="info@micronaet.it"

        smtp_proxy = smtp_pool.browse(cr, uid, smtp_ids, context=context)[0] # read the first
        server = smtp_proxy.address
        port = smtp_proxy.port
        need_autentication = smtp_proxy.require_user
        username = smtp_proxy.username if need_autentication else ""
        password = smtp_proxy.password if need_autentication else ""

        smtp = smtplib.SMTP(server)
        if need_autentication:
            smtp.login(username, password)

        for item in self.browse(cr, uid, ids, context=context):            
            files = item.attachment.replace(";",",").split(",") if item.attachment else [] # attachment files # NOTE no attachment for now

            # Create a MIME message:         
            to_list = item.email.replace(";",",").split(",") if item.email else ("info@micronaet.it",) # TODO gestire meglio la mancanza di indirizzo
            msg = MIMEMultipart()
            msg['From'] = send_from
            msg['To'] = COMMASPACE.join(to_list)
            msg['Date'] = formatdate(localtime=True)
            msg['Subject'] = item.name
            msg.attach(MIMEText(item.log_text))

            for f in files:
                part = MIMEBase('application', "octet-stream")
                try: 
                    part.set_payload(open(f,"rb").read())
                    Encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
                    msg.attach(part)
                except:
                    pass # no attachment file found! no warning!    
            try:
                smtp.sendmail(send_from, msg['To'], msg.as_string())
                # update element if there's error or are sent correctly!
                self.write(cr, uid, item.id, {'mail_send': True})
            except:
                # do nothing (next schedule will try again
                pass    
        smtp.close()    
        return     

    # scheduled function:
    def scheduled_logmail_event(self, cr, uid, context=None):
        ''' Event that is raised from scheduler, check the log list and send 
            messages email that is not yet sended
        '''
        log_ids=self.search(cr, uid, [('mail','=',True),('mail_send','=',False)])
        self._send_mail(cr, uid, log_ids, context=context)
            
        return True

    # public function for generate event:
    def create_logmail_event(self, cr, uid, **args):
        ''' Create a record that, with scheduler event, will be parsed and maybe
            a mail will be sent, if request
            require prameter:
            title, text, typology (info, error, warning), email (not mandatory)
            context (if present)
        '''
        import logging
        _logger = logging.getLogger('log_and_mail')

        try:
            if args['context'] is None:
                context = {}
            else:
                context = args.get('context',{})
                
            if not ('title' in args and 
                    'typology' in args and 
                    'text' in args):
                return False
                
            data = {
                    'name': args.get('title', ''),
                    'log_text': args.get('text', ''),
                    'type': args.get('typology', ''),
                    }
            
            if 'attachment' in args:
                data.update({'attachment': args.get('attachment','')})   
            
            if 'email' in args:
                data.update({
                             'email': args.get('email', ''),        
                             'mail': True,
                             'from': args.get('from', ''),   # not mandatory
                            })        
            else:                
                data.update({'mail': False,})        
            result=self.create(cr, uid, data, context=context)     
        except:
            _logger.info("Error create 'log and mail' record")                 
        return result

    _columns = {
        # General log fields:
        'name':fields.char('Description', size=100, required=False, readonly=False, help="Subject of the log and for the email"),
        'create': fields.datetime('Create'),
        'log_text': fields.text('Log text'),        
        'type': fields.selection([('info','Info'),('warning','Warning'),('error','Error')],'Type', select=True, readonly=False),
        
        # Email fields:
        'from':fields.char('From address', size=64, required=False, readonly=False),   # TODO serve?
        'email':fields.char('To addresses', size=100, required=False, readonly=False),
        'mail':fields.boolean('Need mail warn', required=False),
        'mail_send':fields.boolean('Mail sended', required=False),
        'attachment': fields.text('Attachment', required=False, readonly=False),        
        'error':fields.char('Error send mail', size=80, required=False, readonly=False),
    }    
    _defaults = {
        'create': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'mail': lambda *a: False,
    }
logmail_log()

class logmail_smtp(osv.osv):
    ''' Logmail SMTP server configurations
    '''
    _name = 'logmail.smtp'
    _description = 'SMTP server'
    
    _columns = {
        'name':fields.char('SMTP server description', size=64, required=True, readonly=False),
        'address':fields.char('SMTP server address', size=64, required=True, readonly=False, help="ex.: mail.example.it"),
        'mail_from':fields.char('Mail from', size=64, required=True, readonly=False, help="ex.: info@example.it"),
        'require_user':fields.boolean('Need autentication', required=False),
        'user':fields.char('Log in user', size=64, required=False, readonly=False, help="ex.: info@example.it"),
        'password':fields.char('Log in password', size=64, required=False, readonly=False),
        'port':fields.char('Port', size=10, required=False, readonly=False, help="ex.: 25"),        
        }
    _defaults = {
        'address': lambda *a: 'localhost',
        'port': lambda *a: '25',
        'require_user': lambda *a: False,
    }
logmail_smtp()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
