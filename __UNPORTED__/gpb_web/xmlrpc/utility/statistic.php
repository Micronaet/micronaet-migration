<?php
ini_set('display_errors', 1); 

$username="root";
$password="30mcrt983";
$database="gpb";
$prefix="jgpb_";

function total($table) {
    global $username, $password, $database;
    mysql_connect("localhost", $username, $password);
    mysql_select_db($database) or die( "Unable to select database");
    
    $record = mysql_query("SELECT * FROM $table;");
    if ($record) {
       $tot = mysql_numrows($record);  
       echo '<tr><td>'.$table.'</td><td><b>'.$tot.'</b></td></tr>';
       }
    else {
       echo '<tr><td>'.$table.'</td><td>0</td></tr>';
    }
}
echo '<table><tr><td><b>TABLE</b></td><td><b>TOTAL</b></td></tr>';
echo '<tr><td>MANUFACTURER</td></tr>';
total($prefix."virtuemart_manufacturers");    
total($prefix."virtuemart_manufacturers_en_gb");    
total($prefix."virtuemart_manufacturers_it_it");    
total($prefix."virtuemart_manufacturer_medias");    
    
echo "<tr><td>CATEGORY</td></tr>";
total($prefix."virtuemart_categories");    
total($prefix."virtuemart_categories_it_it");    
total($prefix."virtuemart_categories_en_gb");    

echo "<tr><td>MEDIA</td></tr>";
total($prefix."virtuemart_medias");    

echo "<tr><td>CUSTOMFIELDS</td></tr>";
total($prefix."virtuemart_customs");    

echo "<tr><td>PRODUCT</td></tr>";
total($prefix."virtuemart_products");    
total($prefix."virtuemart_products_en_gb");    
total($prefix."virtuemart_products_it_it");    
total($prefix."virtuemart_product_categories");    
total($prefix."virtuemart_product_customfields");    
total($prefix."virtuemart_product_manufacturers");    
total($prefix."virtuemart_product_medias");    
total($prefix."virtuemart_product_prices");    
total($prefix."virtuemart_product_relations");    

echo "<tr><td>VENDOR</td></tr>";
total($prefix."virtuemart_vendors");    
total($prefix."virtuemart_vendors_en_gb");    
total($prefix."virtuemart_vendors_it_it");    
echo "</table>";

?>    
