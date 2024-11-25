import psycopg2

conexion1 = psycopg2.connect(database="baseFactuAPP", 
                             user="postgres", 
                             password="Coco")

cursor1=conexion1.cursor()