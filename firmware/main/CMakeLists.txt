idf_component_register(SRCS "adc_unit.c" "sensor_raindrop.c" "app_main.c" 
                            "edge_station.c" 
                            "main_station.c" 
                            "sensor_dht22.c"
                            "sensor_ds18b20.c"
                            "sensor_hd38.c"
                            "sensor_dfrobot_rainfall.c"
                           
                    INCLUDE_DIRS ".")
spiffs_create_partition_image(storage ../data FLASH_IN_PROJECT)                    
