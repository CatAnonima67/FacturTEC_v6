import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox,QTableWidgetItem
from interfazMenu import Ui_MainWindow
import datetime
import psycopg2
from conexionDB import cursor1, conexion1
from fpdf import FPDF
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices

class Menu(QMainWindow):
    def __init__(self, user=None, fecha_inicio=None, cargo=None):  # Aceptar user y fecha_inicio como parámetros
        super(Menu, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.is_logged = False

        # Variables para el usuario y las fechas de inicio y cierre de sesión
        self.user = user
        self.fecha_inicio = fecha_inicio
        self.fecha_cierre = None
        self.cargo = cargo
        self.ui.label_NombreEmisor.setText(user) 
        self.ui.label_CargoEmisor.setText(cargo)

        print(f"Usuario: {self.user}, Fecha de inicio: {self.fecha_inicio}")

        self.ui.stackedWidget.setCurrentWidget(self.ui.page_Principal)
        
        #Cambiar de página
        self.ui.pushButton_Alumno.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.page_Alumno))
        self.ui.pushButton_Padre.clicked.connect(lambda:self.ui.stackedWidget.setCurrentWidget(self.ui.page_Padre))
        self.ui.pushButton_NuevaFactura.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.page_Factura))
        self.ui.pushButton_Bitacora.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.page_Bitacora))
       # self.ui.pushButton_Respaldo.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.page_ModificarUsuario))
        
        #MIO

        #Función para verificar el rol del usuario
        def abrir_modificar_usuario(cargo):
            if cargo == "DIRECTOR":
                # Cambia a la página de modificar usuario
                self.ui.stackedWidget.setCurrentWidget(self.ui.page_ModificarUsuario)
            else:
                 # Muestra un mensaje de advertencia si el usuario no es Director
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.setWindowTitle("Acceso denegado")
                msg_box.setText("Solo el director tiene acceso.")
                msg_box.exec()

        # Asumiendo que tienes un botón llamado pushButton_Respaldo
        self.ui.pushButton_Respaldo.clicked.connect(lambda: abrir_modificar_usuario(cargo))
        #MIO

        #Cerrar sesión
        self.ui.pushButton_Cerrarsesion.clicked.connect(self.cerrarSesion)
        
        
        self.ui.lineEdit_RFCPadre.setMaxLength(12)
        self.ui.lineEdit_CURPalumno.setMaxLength(18)
        self.ui.lineEdit_RFCtutorAlumno.setMaxLength(12)

        self.ui.PushBoton_Insertar_Alumno.clicked.connect(self.guardar_datos_alumno)
        self.ui.PushBoton_Insertar_Padre.clicked.connect(self.guardar_datos_padre)

         # Conectar el botón a la función que abre el PDF
        self.ui.pushButton_2.clicked.connect(self.open_pdf)

        self.ui.BotonInsertarAlta.clicked.connect(self.guardar_datos_usuarios)

        self.ui.comboBoxAlta.activated.connect(self.cargar_datos_usuario)

        self.ui.BotonModificarAlta.clicked.connect(self.modificar_datos)
        
        self.ui.BotonEliminarAlta.clicked.connect(self.confirmar_eliminacion)


        self.obtener_nivel_educativo()
        self.obtener_regimen_fiscal()
        self.vizualizar_Bitacora()
        self.cargar_usuarios()
        

    def cerrarSesion(self):
        # Mensaje de salida
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Confirmar Cierre de Sesión")
        msg_box.setText("¿Estás seguro de que deseas cerrar sesión?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        # Cambiar texto de los botones (opcional)
        yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
        no_button = msg_box.button(QMessageBox.StandardButton.No)

        yes_button.setText("Sí")
        no_button.setText("No")

        # Mostrar el cuadro de diálogo
        respuesta = msg_box.exec()

        # Comprobar la respuesta del usuario
        if respuesta == QMessageBox.StandardButton.Yes:
            # Registrar la hora de cierre de sesión
            self.fecha_cierre = datetime.datetime.now().replace(microsecond=0)
            self.is_logged=True
            # Mostrar mensaje de información
            QMessageBox.information(self, "Cerrar Sesión", "La aplicación se cerrará.")
            
            # Cerrar la ventana
            self.close()
        else:
            # No hacer nada si el usuario elige "No"
            pass

        
    def guardar_datos_alumno(self):
        nombreAlumno = self.ui.lineEdit_NombreAlumno.text()
        curpAlumno = self.ui.lineEdit_CURPalumno.text()
        apellidoPalumno = self.ui.lineEdit_ApellidoPalumno.text()
        apellidoMalumno = self.ui.lineEdit_ApellidoMAlumno.text()
        rfcReceptor = self.ui.lineEdit_RFCtutorAlumno.text()
        claveTrabajo = self.ui.lineEdit_ClaveTrabajoAlumno.text()
        nivelEscolar = self.ui.comboBox_NivelEducativo.currentData()

        if not nombreAlumno or not curpAlumno or not apellidoMalumno or not apellidoPalumno or not claveTrabajo or not rfcReceptor or not nivelEscolar:
            QMessageBox.warning(self, "Error", "Campos no pueden estar vacíos.")
            return
        
        # Obtener el ID del nivel educativo seleccionado en el QComboBox
        id_nivel_escolar = self.ui.comboBox_NivelEducativo.currentData()
    
        # Verificar que se haya seleccionado un nivel educativo
        if id_nivel_escolar is None:
            QMessageBox.warning(self, "Error", "Debe seleccionar un nivel educativo.")
            return

        cursor1.execute("INSERT INTO alumno (curp,nombre,apellido_paterno,apellido_materno) VALUES (%s,%s,%s,%s)", (curpAlumno,nombreAlumno,apellidoPalumno,apellidoMalumno))
        #cursor1.execute("INSERT INTO alumno (curp) VALUES (%s)", (curpAlumno,))
        

        cursor1.execute("insert into alumno_nivel_escolar (curp,id_nivel_escolar) values (%s,%s)",(curpAlumno,id_nivel_escolar))

        conexion1.commit()


    def guardar_datos_padre(self):

        nombrePadre = self.ui.lineEdit_NombreAlumno.text()
        apellidoPpadre = self.ui.lineEdit_ApellidoPpadre.text()
        apellidoPpadre = self.ui.lineEdit_ApellidoMpadre.text()
        rfcPadre = self.ui.lineEdit_RFCPadre.text()
        correoElectronico = self.ui.lineEdit_CorreoElectronicoPadre.text()

        cursor1.execute("INSERT INTO padre (rfc_padre, nombre, apellido_paterno, apellido_materno,correo_electronico) VALUES (%s)", ())
    
    

    def obtener_nivel_educativo(self):
        cursor1.execute("SELECT id_nivel_escolar, nivel FROM costo_nivel_escolar")

        niveles = cursor1.fetchall()

        for id_nivel, nombre_nivel in niveles:  # Cambié el orden de los valores
            self.ui.comboBox_NivelEducativo.addItem(nombre_nivel, id_nivel)

    def obtener_regimen_fiscal(self):
        cursor1.execute("SELECT nombre_regimen FROM regimen_fiscal")
        regimenes  = cursor1.fetchall()

        for regimen in regimenes:
            self.ui.comboBox_Regimen.addItem(regimen[0])

    def guardar_log_sesion(self):
        """Función para guardar el log de sesión en la base de datos"""
        try:
            sql = "INSERT INTO log_sesiones (usuario, cargo, fecha_inicio, fecha_cierre) VALUES (%s, %s, %s, %s)"
            cursor1.execute(sql, (self.user, self.cargo, self.fecha_inicio, self.fecha_cierre))
            conexion1.commit()

            print(f"Log de sesión guardado para el usuario {self.user} desde {self.fecha_inicio} hasta {self.fecha_cierre}")
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Error", 
                                 f"Error en la conexión con la base de datos: {e}",
                                 QMessageBox.StandardButton.Close, 
                                 QMessageBox.StandardButton.Close)
    def GuardarLog(self):
        try:
            class PDF(FPDF):
                def header(self):
                    # No agregamos encabezado porque el membrete está en el archivo base
                    pass

            cursor1.execute("SELECT * FROM log_sesiones;")
            registros = cursor1.fetchall()

            # Crear el PDF con el contenido dinámico
            pdf = PDF()
            pdf.add_page()

            # Establecer una fuente más pequeña
            pdf.set_font("Arial", size=8)

            # Ajustar la posición de la tabla en la página, para que esté sobre el membrete
            pdf.set_y(60)  # Ajusta este valor según el diseño del membrete

            # Título del PDF
            pdf.set_font("Arial", "B", 12)
            pdf.cell(200, 10, txt="Reporte de Registros", ln=True, align='C')
            pdf.ln(10)

            # Definir color de fondo para las celdas del encabezado (color azul rey)
            pdf.set_fill_color(65, 105, 225)  # Azul rey en RGB
            pdf.set_text_color(255, 255, 255)  # Texto blanco para contraste

            # Cabeceras de la tabla
            columnas = ['ID', 'Nombre', 'Cargo', 'Fecha de entrada', 'Fecha de salida']
            for columna in columnas:
                pdf.cell(40, 10, columna, border=1, fill=True)  # Fondo azul y borde

            pdf.ln()  # Salto de línea después de la fila de encabezado

            # Restaurar color de texto para los datos y establecer un tamaño de fuente más pequeño
            pdf.set_text_color(0, 0, 0)  # Texto en color negro
            pdf.set_font("Arial", size=8)

            # Añadir los datos obtenidos de la base de datos al PDF
            for registro in registros:
                for dato in registro:
                    pdf.cell(40, 10, str(dato), border=1)
                pdf.ln()

            # Guardar el PDF temporal
            pdf.output("contenido_temporal.pdf")

            # 2. Combinar el contenido dinámico con el membrete

            # Leer la plantilla de membrete
            membrete_pdf = PdfReader(open("pdf/membrete.pdf", "rb"))
            contenido_pdf = PdfReader(open("pdf/contenido_temporal.pdf", "rb"))

            # Crear el escritor de PDF
            writer = PdfWriter()

            # Tomar la página del membrete
            pagina_membrete = membrete_pdf.pages[0]

            # Superponer el contenido dinámico en la página del membrete
            contenido_pagina = contenido_pdf.pages[0]
            pagina_membrete.merge_page(contenido_pagina)

            # Agregar la página combinada al nuevo PDF
            writer.add_page(pagina_membrete)

            # Guardar el resultado final
            with open("reporte_final_membrete.pdf", "wb") as f:
                writer.write(f)
            # Cerrar la conexión
        except psycopg2.Error:
            QMessageBox.critical(self, "Error", 
                                 "Error en la conexión con la base de datos",
                                 QMessageBox.StandardButton.Close, 
                                 QMessageBox.StandardButton.Close)
        except FPDF.error as e:
            QMessageBox.critical(self, "Error", 
                                 f"Error en la generación del PDF: {e}",
                                 QMessageBox.StandardButton.Close, 
                                 QMessageBox.StandardButton.Close)
    def closeEvent(self, event):
        """Función que maneja el cierre de la ventana (cuando el usuario cierra el programa)"""
        # Registrar la hora de cierre de sesión
        
        self.fecha_cierre = datetime.datetime.now().replace(microsecond=0)
        self.guardar_log_sesion()
        self.GuardarLog()
        cursor1.close()
        conexion1.close()  # Generar el PDF del log antes de cerrar el programa
        event.accept()  # Aceptar el cierre del programa

    def vizualizar_Bitacora (self):
        try:
            cursor1.execute("SELECT * FROM log_sesiones")
            rows = cursor1.fetchall()
        
            # Verificar si rows tiene datos
            if rows:
                self.ui.tableWidget.setRowCount(len(rows))
                self.ui.tableWidget.setColumnCount(len(rows[0]))
            
                # Llenar la tabla en Qt con los datos
                for i, row in enumerate(rows):
                    for j, value in enumerate(row):
                        self.ui.tableWidget.setItem(i, j, QTableWidgetItem(str(value)))
            else:
                 # Si no hay datos, establece las filas y columnas en cero
                self.ui.tableWidget.setRowCount(0)
                self.ui.tableWidget.setColumnCount(0)
            #print("La tabla 'log_sesiones' está vacía o no tiene datos.")
        except psycopg2.Error as e:
        # Capturar errores de la base de datos, como cuando la tabla no existe
            print("Error al ejecutar la consulta:", e)
            self.ui.tableWidget.setRowCount(0)
            self.ui.tableWidget.setColumnCount(0)

    def open_pdf(self):
        # Ruta del archivo PDF
        pdf_path = "reporte_final_membrete.pdf"  # Cambia a la ruta de tu archivo PDF
        
        if os.path.isfile(pdf_path):
            try:
            # Abrir el PDF en el navegador
             QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))
            except Exception as e:
            # Mostrar un mensaje de error si ocurre un problema al abrir el PDF
             QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo '{pdf_path}'.\nError: {str(e)}")
        else:
        # Mostrar un mensaje de error si el archivo no existe
            QMessageBox.critical(self, "Error", f"El archivo '{pdf_path}' no se encontró.")

    def guardar_datos_usuarios(self):
        # Obtener los valores de los QLineEdit
        rfc = self.ui.RFCAlta.text()
        usuario = self.ui.usuarioAlta.text()
        contraseña = self.ui.contraseAlta.text()
        nombre = self.ui.nombreAlta.text()
        apellido_paterno = self.ui.apellidoPAlta.text()
        apellido_materno = self.ui.apellidoMAlta.text()    
        cargo = self.ui.cargoAlta.text()
        no_serie = self.ui.serialAlta.text()

        try:
            # Script SQL combinado en un solo flujo
            # Supongamos que tienes las variables `usuario`, `contraseña`, `cargo`, `rfc`, `nombre`, `apellido_paterno`, `apellido_materno`, y `no_serie`

            cursor1.execute("""
                -- Insertar en emisor y obtener el rfc_emisor
                INSERT INTO emisor (rfc_emisor, nombre, apellido_paterno, apellido_materno, no_serie_cer_emisor)
                VALUES (%s, %s, %s, %s, %s) 
                RETURNING rfc_emisor;
            """, (rfc, nombre, apellido_paterno, apellido_materno, no_serie))

            # Obtener el valor de `rfc_emisor` recién insertado
            rfc_insertado = cursor1.fetchone()[0]

            cursor1.execute("""
                -- Insertar en cuenta_emisor y obtener el usuario
                INSERT INTO cuenta_emisor (usuario, contrasena, cargo, rfc_emisor)
                VALUES (%s, %s, %s) 
                RETURNING usuario;
            """, (usuario, contraseña, cargo, rfc))

# Obtener el valor de `usuario` recién insertado
            usuario_insertado = cursor1.fetchone()[0]

            # Finalmente, insertar en la tabla intermedia usando los valores obtenidos
            cursor1.execute("""
                INSERT INTO emisor_cuenta_emisor (rfc_emisor, usuario) 
                VALUES (%s, %s);
            """, (rfc_insertado, usuario_insertado))

            # Confirma la transacción si todo fue exitoso
            conexion1.commit()

            QMessageBox.information(self, "Éxito", "Los datos fueron guardados exitosamente.")
            self.actualizar_contenido()


        except psycopg2.Error as e:
            conexion1.rollback()  # Revertir cambios en caso de error
            QMessageBox.critical(self, "Error", f"Error al guardar los datos: {e}")
        finally:
            cursor1.close()
            conexion1.close()

    def cargar_usuarios(self):
        """Función para cargar todos los usuarios en el ComboBox"""
        try:
            # Obtener todos los usuarios de la tabla cuenta_emisor
            cursor1.execute("SELECT usuario FROM cuenta_emisor;")
            usuarios = cursor1.fetchall()

            # Agregar usuarios al ComboBox
            self.ui.comboBoxAlta.clear()  # Limpiar el ComboBox
            for usuario in usuarios:
                # Insertar cada usuario en el ComboBox con su ID como dato
                self.ui.comboBoxAlta.addItem(usuario[0])

           # cursor1.close()
            #conexion1.close()

        except psycopg2.Error as e:
            QMessageBox.critical(self, "Error", f"Error al cargar usuarios: {e}")

    def cargar_datos_usuario(self):
        """Función para cargar los datos del usuario seleccionado en los QLineEdit"""
        # Obtener el ID del usuario seleccionado en el ComboBox
        usuario = self.ui.comboBoxAlta.currentText().strip()
        print(usuario)
        if usuario is None:
            return  # No hacer nada si no hay un usuario seleccionado

        try:
            # Obtener los datos del usuario seleccionado
            sql="SELECT usuario, contrasena, cargo, rfc_emisor FROM cuenta_emisor WHERE usuario = %s;"
            cursor1.execute(sql, (usuario,))
            resultado = cursor1.fetchone()
            rfc_emisorl = resultado[3]
            print(rfc_emisorl)

            cursor1.execute("SELECT nombre, apellido_paterno, apellido_materno, no_serie_cer_emisor FROM emisor WHERE rfc_emisor = %s;", (rfc_emisorl,))
            resultado1 = cursor1.fetchone()

            if resultado:
                usuario, contraseña, cargo , rfc_emisor = resultado
                nombre, apellido_paterno, apellido_materno, no_serie = resultado1
                self.ui.RFCAlta.setText(rfc_emisor)
                self.ui.usuarioAlta.setText(usuario)
                self.ui.contraseAlta.setText(contraseña)
                self.ui.cargoAlta.setText(cargo)
                self.ui.nombreAlta.setText(nombre)
                self.ui.apellidoPAlta.setText(apellido_paterno)
                self.ui.apellidoMAlta.setText(apellido_materno)
                self.ui.serialAlta.setText(no_serie)

                self.usuarioaf = usuario
                self.rfcaf = rfc_emisor

                print(self.usuarioaf)
                print(self.rfcaf)
            
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Error", f"Error al cargar datos del usuario: {e}")
            

    def modificar_datos(self):
        """Función para guardar los cambios en la base de datos"""
        # Obtener el ID del usuario seleccionado y los valores de los QLineEdit
        rfc = self.ui.RFCAlta.text()
        usuario = self.ui.usuarioAlta.text()
        contraseña = self.ui.contraseAlta.text()
        nombre = self.ui.nombreAlta.text()
        apellido_paterno = self.ui.apellidoPAlta.text()
        apellido_materno = self.ui.apellidoMAlta.text()    
        cargo = self.ui.cargoAlta.text()
        no_serie = self.ui.serialAlta.text()
        usuarioaf1 = self.usuarioaf
        rfcaf1 = self.rfcaf

        if not usuario or not contraseña:
            QMessageBox.warning(self, "Advertencia", "Por favor, completa todos los campos.")
            return

        try:
                # Primero, actualizar en la tabla intermedia `emisor_cuenta_emisor`
            # 1. Verificar si el nuevo usuario existe en cuenta_emisor
                cursor1.execute("""
                    SELECT COUNT(*) FROM cuenta_emisor WHERE usuario = %s;
                """, (usuario,))
                existe_usuario = cursor1.fetchone()[0]

                if existe_usuario == 0:
                    QMessageBox.warning(self, "Advertencia", "El nuevo usuario no existe en cuenta_emisor.")
                    return

                # 2. Actualizar en `cuenta_emisor` (cambia el usuario y los demás campos)
                cursor1.execute("""
                    UPDATE cuenta_emisor 
                    SET usuario = %s, contrasena = %s, cargo = %s
                    WHERE usuario = %s;  -- Cambiar usuario en `cuenta_emisor`
                """, (usuario, contraseña, cargo, usuarioaf1))

                # 3. Actualizar en la tabla intermedia `emisor_cuenta_emisor`
                cursor1.execute("""
                    UPDATE emisor_cuenta_emisor
                    SET usuario = %s
                    WHERE usuario = %s AND rfc_emisor = %s;  -- Cambiar usuario en la tabla intermedia
                """, (usuario, usuarioaf1, rfcaf1))

                # 4. Actualizar en `emisor`
                cursor1.execute("""
                    UPDATE emisor 
                    SET rfc_emisor = %s, nombre = %s, apellido_paterno = %s, apellido_materno = %s, no_serie_cer_emisor = %s
                    WHERE rfc_emisor = %s;  -- Cambiar los detalles del emisor
                """, (rfc, nombre, apellido_paterno, apellido_materno, no_serie, rfcaf1))

                # Confirmar la transacción si todo fue exitoso
                conexion1.commit()

                QMessageBox.information(self, "Éxito", "Los datos fueron modificados correctamente.")
                self.actualizar_contenido()


        except psycopg2.Error as e:
            conexion1.rollback()
            print(f"Error al actualizar los datos: {e}")

    def confirmar_eliminacion(self):
        respuesta = QMessageBox.question(self, "Confirmar Eliminación",
                                          "¿Estás seguro de que deseas eliminar este usuario?",
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if respuesta == QMessageBox.StandardButton.Yes:
            self.eliminar_usuario()

    def eliminar_usuario(self):
        # Obtener el usuario a eliminar, por ejemplo, desde un QLineEdit
        usuario_a_eliminar = self.ui.usuarioAlta.text()

        try:
         # Primero, eliminar de la tabla intermedia emisor_cuenta_emisor
            cursor1.execute("""
                DELETE FROM emisor_cuenta_emisor 
                WHERE usuario = %s;
            """, (usuario_a_eliminar,))

            # Luego, eliminar de la tabla cuenta_emisor
            cursor1.execute("""
                DELETE FROM cuenta_emisor 
                WHERE usuario = %s;
            """, (usuario_a_eliminar,))

            # Eliminar de la tabla emisor (opcional, según la lógica de tu aplicación)
            cursor1.execute("""
                DELETE FROM emisor 
                WHERE rfc_emisor = (
                    SELECT rfc_emisor 
                    FROM emisor_cuenta_emisor 
                    WHERE usuario = %s
                );
            """, (usuario_a_eliminar,))

            # Confirmar la transacción
            conexion1.commit()

            QMessageBox.information(self, "Éxito", "Usuario eliminado exitosamente.")

            self.actualizar_contenido()


        except psycopg2.Error as e:
            conexion1.rollback()  # Revertir cambios en caso de error
            QMessageBox.critical(self, "Error", f"Error al eliminar el usuario: {e}")

    def actualizar_contenido(self):
        # Limpiar el comboBox
        self.ui.comboBoxAlta.clear()

        self.cargar_usuarios()
        # Volver a cargar los datos de la base de datos
        self.cargar_datos_usuario()  # Asegúrate de tener una función que cargue los datos en el comboBox

        # Si necesitas refrescar otros elementos, agrégales aquí
        self.vizualizar_Bitacora()  # Refrescar la tabla de bitácora, si es necesario


if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = Menu()  # Crear una instancia de la clase Menu
    window.setWindowTitle("FACTURTEC")
    window.show()
    sys.exit(app.exec())
