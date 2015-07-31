@echo off
@net use o: \\192.168.100.181\easylabel /persistent:yes
@copy o:\purchase.cmd "C:\Programmi\Tharo\EASYLABEL4"
@copy o:\purchase.dbf "C:\Programmi\Tharo\EASYLABEL4"
@cd "C:\Programmi\Tharo\EASYLABEL4"
@cls
@echo Start printing... PO00089 [EUROTESSUTI S.R.L.]
@echo Print note: No note!
@echo Job detail:
@echo Code TESALY140BE  -  Tot. 100 (1/1) 
@echo Code TESALY140BL  -  Tot. 100 (1/1) 
@echo Code TESALY140GO  -  Tot. 100 (1/1) 
@echo Code TESALY140MA  -  Tot. 100 (1/1) 
@echo Code TESALY140MC  -  Tot. 100 (1/1) 
@echo Code TESALY140RO  -  Tot. 100 (1/1) 
@echo Code TESALY140VE  -  Tot. 100 (1/1) 
@echo Code TESPAN140BI  -  Tot. 100 (1/1) 
@echo Code TESPAN140MR  -  Tot. 100 (1/1) 
@echo Code TESPAN140TA  -  Tot. 100 (1/1) 
@echo Code TESMAL140FT  -  Tot. 50 (1/1) 

@pause
@"C:\Programmi\Tharo\EASYLABEL4\easy.exe" purchase
