import psycopg2

conexion1 = psycopg2.connect(database="Base_Oficial_Factura", 
                             user="postgres", 
                             password="Coco", 
                             host="localhost",
                             port="5432")



cursor1=conexion1.cursor()