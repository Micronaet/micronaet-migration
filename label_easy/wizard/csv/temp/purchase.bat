@echo off
@net use o: \\192.168.100.181\easylabel /persistent:yes
@copy o:\purchase.cmd "C:\Programmi\Tharo\EASYLABEL4"
@copy o:\purchase.dbf "C:\Programmi\Tharo\EASYLABEL4"
@cd "C:\Programmi\Tharo\EASYLABEL4"
@cls
@echo Start printing... PO00090 [DALE F.LLI S.R.L.]
@echo Print note: No note!
@echo Job detail:
@echo Code IIRIPOFE-BI--S  -  Tot. 10 (1/1) 

@pause
@"C:\Programmi\Tharo\EASYLABEL4\easy.exe" purchase
