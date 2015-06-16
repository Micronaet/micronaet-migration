#!/bin/bash
# Importazione elenco ordini per dashboard Fiam:
#python import.py ../../../../ETL/fiam/ocdetoerp.FIA
#python import.py ocdetoerp.GPB
python import_order.py ../../../../ETL/fiam/ocdetoerp1.FIA

# Importazione scadenze:
python import_scad.py ../../../../ETL/fiam/scadoerp.FIA

python import_fatturato.py ../../../../ETL/fiam/fatmeseoerp.FIA
python import_product.py ../../../../ETL/fiam/fatmesartoerp.FIA
