<?php
ini_set('display_errors', 1); 

echo("start ********* \n");
function log_on_file($data) {
    //$file_name="ftp://administrator:30mcrt983@192.168.100.73/public_html/micronaet.log";
    $file_name="/home/administrator/public_html/micronaet.log";
    
    $f = fopen($file_name, 'a') or die("Can't open log file");
    fwrite($f, "\n".$data);
    fclose($f);    
    }
?>    
