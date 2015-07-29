Update ID e ID del template nella product_product
(per forzare il l'allineamento)
select 'update product_product set migration_old_id=' || id || ', migration_old_tmpl_id=' || product_tmpl_id || ' where default_code = ''' || default_code || ''';' from product_product;
