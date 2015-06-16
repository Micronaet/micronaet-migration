#!/bin/bash
# Importazione elenco ordini per dashboard Fiam:
# DA ELIMINARE
#######################################python import.py ocdetoerp.FIA
#python import.py ocdetoerp.GPB

# DA ATTIVARE:
python import_order.py ocdetoerp1.FIA

# Importazione scadenze:
python import_scad.py scadoerp.FIA

# Importazione Trend anno attuale e anno precedente:
#python import_trend.py trendoerp1.FIA S
#python import_trend.py  trendoerp2.FIA N

python import_fatturato.py fatmeseoerp.FIA

python import_product.py fatmesartoerp.FIA
