#-*- encoding: utf-8 -*-
#require installation of ghostscript on linux PC:
# sudo apt-get install ghostscript

import subprocess
import os
 
path_org = '/home/administrator/Launchpad/openerp/bin/addons/quotation_photo_fiam/images/fiam/org/'
path_def = '/home/administrator/Launchpad/openerp/bin/addons/quotation_photo_fiam/images/fiam/default/'

for infile in os.listdir(path_org):
    if infile[-3:].lower()=="eps"
       orig_file=os.path.join(path_org, infile) 
       dest_file=os.path.join(path_def, infile[-4:] + ".jpg") 
       command="gs -sDEVICE=jpeg -dJPEGQ=100 -dNOPAUSE -dBATCH -dSAFER -r300 -sOutputFile=%s %s"%(dest_file,orig_file)
       subprocess.call([command,],shell=True)
       
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
