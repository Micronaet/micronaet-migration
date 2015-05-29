<?php
ini_set('display_errors', 1); 

$username="root";
$password="30mcrt983";
$database="gpb";
$prefix="jgpb_";

function delete_all($table) {
    global $username, $password, $database;
    mysql_connect("localhost", $username, $password);
    mysql_select_db($database) or die( "Unable to select database");
    
    echo "DELETE FROM $table<br>";
    $record = mysql_query("DELETE FROM $table;");
}

/*function delete_custom($table) {
    global $username, $password, $database;
    mysql_connect("localhost", $username, $password);
    mysql_select_db($database) or die( "Unable to select database");
    
    echo "DELETE FROM $table WHERE id > '2'<br>";
    $record = mysql_query("DELETE FROM $table WHERE id > '2';");
}*/

delete_all($prefix."virtuemart_manufacturers");    
delete_all($prefix."virtuemart_manufacturers_en_gb");    
delete_all($prefix."virtuemart_manufacturers_it_it");    
delete_all($prefix."virtuemart_manufacturer_medias");    
    
delete_all($prefix."virtuemart_categories");    
delete_all($prefix."virtuemart_categories_it_it");    
delete_all($prefix."virtuemart_categories_en_gb");    

delete_all($prefix."virtuemart_medias");    

delete_all($prefix."virtuemart_products");    
delete_all($prefix."virtuemart_products_en_gb");    
delete_all($prefix."virtuemart_products_it_it");    
delete_all($prefix."virtuemart_product_categories");    
delete_all($prefix."virtuemart_product_customfields");    
delete_all($prefix."virtuemart_product_manufacturers");    
delete_all($prefix."virtuemart_product_medias");    
delete_all($prefix."virtuemart_product_prices");    
delete_all($prefix."virtuemart_product_relations");    

?>    
