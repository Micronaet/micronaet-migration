#!/bin/bash

rsync -avh -ssh administrator@192.168.1.181:/home/administrator/photo/log/dashboard/statistic.partner.FIA.* ./data
# scp administrator@192.168.1.181:/home/administrator/photo/log/statistic.partner.FIA.* ./data/
# sftp://administrator@192.168.1.181/home/administrator/photo/log/dashboard
