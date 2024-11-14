import sys
import dns.resolver
import re
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
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtCore import QRegularExpression
from login_main import logins



class Menus(QMainWindow):
    def __init__(self, user=None, fecha_inicio=None, cargo=None):  # Aceptar user y fecha_inicio como parámetros
        super(Menus, self).__init__()
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
        self.cp_seleccionado = ''


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
                self.mostrar_mensaje("Acceso denegado","advertencia","Solo el director tiene acceso.")

        self.ui.pushButton_Respaldo.clicked.connect(lambda: abrir_modificar_usuario(cargo))
        #MIO

        #Cerrar sesión
        self.ui.pushButton_Cerrarsesion.clicked.connect(self.cerrarSesion)
        
        
        self.ui.lineEdit_RFCPadre.setMaxLength(13)
        self.ui.lineEdit_CURPalumno.setMaxLength(18)
        self.ui.lineEdit_RFCtutorAlumno.setMaxLength(13)

        self.ui.PushBoton_Insertar_Alumno.clicked.connect(self.guardar_datos_alumno)
        self.ui.PushBoton_Eliminar_Alumno.clicked.connect(self.confirmar_eliminacion_alumno)

        self.ui.PushBoton_Eliminar_Padre.clicked.connect(self.confirmar_eliminacion_padre)
        
        self.ui.PushBoton_Insertar_Padre.clicked.connect(self.guardar_datos_padre)

         # Conectar el botón a la función que abre el PDF
        self.ui.pushButton_2.clicked.connect(self.open_pdf)

        self.ui.BotonInsertarAlta.clicked.connect(self.guardar_datos_usuarios)
        self.ui.PushBoton_Modificar_Alumno.clicked.connect(self.modificar_alumno)
        self.ui.PushBoton_Modificar_Padre.clicked.connect(self.modificar_padre)

        self.ui.comboBoxAlta.activated.connect(self.cargar_datos_usuario)
        self.ui.comboBox_BuscarAlumno.activated.connect(self.mostrar_datos_alumno)
        self.ui.comboBox_BuscarPadre.activated.connect(self.mostrar_datos_padre)


        self.ui.BotonModificarAlta.clicked.connect(self.modificar_datos)
        
        self.ui.BotonEliminarAlta.clicked.connect(self.confirmar_eliminacion)

        self.configurar_validacion_alfabeto([self.ui.lineEdit_NombreAlumno, self.ui.lineEdit_ApellidoPalumno, self.ui.lineEdit_ApellidoMalumno])
        self.configurar_validacion_alfabeto([self.ui.lineEdit_NombrePadre, self.ui.lineEdit_ApellidoPpadre, self.ui.lineEdit_ApellidoMpadre,self.ui.lineEdit_Municipio, self.ui.lineEdit_Estado, self.ui.comboBox_Colonia])
        self.configurar_validacion_alfanumerico([self.ui.lineEdit_CURPalumno, self.ui.lineEdit_RFCPadre, self.ui.lineEdit_ClaveTrabajoAlumno,self.ui.lineEdit_RFCtutorAlumno])
        self.validacacion_numerica([self.ui.comboBox_CP])
        self.ui.comboBox_CP.activated.connect(self.mostrar_datos_CP)
        self.ui.comboBox_Colonia.activated.connect(self.mostrar_datos_Colonia)


        self.obtener_nivel_educativo()
        self.obtener_regimen_fiscal()
        self.vizualizar_Bitacora()
        self.cargar_usuarios()
        self.cargar_alumnos()
        self.cargar_padres()
        self.cargar_CP()
        self.cargar_Colonia()
        
        #self.generar_curp()
        
        

        self.configurar_mayusculas([self.ui.lineEdit_RFCPadre,
        self.ui.lineEdit_CURPalumno,
        self.ui.lineEdit_NombreAlumno,
        self.ui.lineEdit_ApellidoPalumno,
        self.ui.lineEdit_ApellidoMalumno,
        self.ui.lineEdit_ClaveTrabajoAlumno,
        self.ui.lineEdit_RFCtutorAlumno,
        self.ui.lineEdit_ApellidoPpadre,
        self.ui.lineEdit_ApellidoMpadre,
        self.ui.lineEdit_NombrePadre,
        self.ui.lineEdit_CorreoElectronicoPadre,
        self.ui.lineEdit_Estado,
        self.ui.lineEdit_Municipio,
        self.ui.lineEdit_Calle,
        ])

    def configurar_mayusculas(self, line_edits):
        """Conecta la función convertir_mayusculas a los QLineEdit especificados."""
        for line_edit in line_edits:
            line_edit.textChanged.connect(lambda _, le=line_edit: self.convertir_mayusculas(le))

    def convertir_mayusculas(self, line_edit):
        """Convierte el texto a mayúsculas en el QLineEdit proporcionado."""
        texto = line_edit.text()
        line_edit.setText(texto.upper())

    def openLoginWindow(self):
        self.main_window = logins()
        self.main_window.show()
        self.destroy()
    
     #Funcion Ventana Personalizable Prueba
    def mostrar_mensaje(self, titulo, tipo_ventana, mensaje):
        msg_box = QMessageBox(self) 
        msg_box.setWindowTitle(titulo)
        msg_box.setText(mensaje)
        msg_box.setStyleSheet("QLabel { color: black; }")

        if tipo_ventana == "critico":
         msg_box.setIcon(QMessageBox.Icon.Critical)

        elif tipo_ventana == "informacion":
            msg_box.setIcon(QMessageBox.Icon.Information)

        elif tipo_ventana == "advertencia":
            msg_box.setIcon(QMessageBox.Icon.Warning)

        elif tipo_ventana == "pregunta":
            msg_box.setIcon(QMessageBox.Icon.Question)

        else:
         msg_box.setIcon(QMessageBox.Icon.NoIcon)

        msg_box.exec()

    def cerrarSesion(self):
        # Mensaje de salida
        self.mostrar_mensaje("Confirmar Cierre de Sesion","advertencia","¿Estás seguro de que deseas cerrar sesión?")
        self.mostrar_mensaje.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) #checar si funciona
        
        # Cambiar texto de los botones (opcional) chechar si no pa quitarlo
        yes_button = self.mostrar_mensaje.button(QMessageBox.StandardButton.Yes)
        no_button = self.mostrar_mensaje.button(QMessageBox.StandardButton.No)

        yes_button.setText("Sí") #checar esto porque creo se repite
        no_button.setText("No")

        # Mostrar el cuadro de diálogo
        respuesta = self.mostrar_mensaje.exec()#hechar esto otro

        # Comprobar la respuesta del usuario
        if respuesta == QMessageBox.StandardButton.Yes:
            self.fecha_cierre = datetime.datetime.now().replace(microsecond=0)   # Registrar la hora de cierre de sesión
            self.is_logged=True
            # Mostrar mensaje de información
            self.mostrar_mensaje("Cerrar sesion","informacion","Cerrará el sistema")
            # Regresar al login
            self.openLoginWindow()
            
        else:
            pass #no hace nada si es nope
    

    def guardar_datos_alumno(self):
    # Obtener los datos de los campos
        nombreAlumno = self.ui.lineEdit_NombreAlumno.text().strip()
        curpAlumno = self.ui.lineEdit_CURPalumno.text().strip()
        apellidoPalumno = self.ui.lineEdit_ApellidoPalumno.text().strip()
        apellidoMalumno = self.ui.lineEdit_ApellidoMalumno.text().strip()
        rfcReceptor = self.ui.lineEdit_RFCtutorAlumno.text().strip()
        claveTrabajo = self.ui.lineEdit_ClaveTrabajoAlumno.text().strip()
        fechaNacAlum = self.ui.dateEdit.date().toString("ddMMyyyy")
        id_nivel_escolar = self.ui.comboBox_NivelEducativo.currentData()[0]
    

        fecha_invertida = fechaNacAlum[4:] + fechaNacAlum[2:4] + fechaNacAlum[:2]
        nombre_completo =self.ui.lineEdit_ApellidoPalumno.text().strip() + " " + self.ui.lineEdit_ApellidoMalumno.text().strip()+ " " + self.ui.lineEdit_NombreAlumno.text().strip()

        if  len(curpAlumno)<18:
            self.mostrar_mensaje("Error","informacion","El tamaño del campo CURP no está completo.")
            return
        
        if not self.validar_curp(curpAlumno, nombre_completo, fecha_invertida):
            self.mostrar_mensaje("CURP inválida","advertencia", "La CURP no coincide con el nombre y fecha proporcionados.")
        else:
            self.mostrar_mensaje("Éxito","informacion", "La CURP es válida para el nombre y fecha ingresados.")

        if len(rfcReceptor)<13:
            self.mostrar_mensaje("Error","advertencia", "El tamaño del campo RFC del tutor no está completo.")
            return
        
        if not self.validar_rfc1(rfcReceptor):
            self.mostrar_mensaje("RFC inválido","advertencia", "Por favor, ingresa un RFC válido.")

        if len(claveTrabajo)<10:
             
            self.mostrar_mensaje("Error","advertencia", "El tamaño del campo Clave de trabajo no está completo.")
            return
        
        # Verificar que los campos no estén vacíos
        if not nombreAlumno or not curpAlumno or not apellidoMalumno or not apellidoPalumno or not claveTrabajo or not rfcReceptor or not id_nivel_escolar:
            
            self.mostrar_mensaje("Error","critico","Campos no pueden estar vacíos")  
            return
        try:
            id_nivel_escolar = int(id_nivel_escolar)
        except (TypeError, ValueError):

            self.mostrar_mensaje("Error","critico","El nivel escolar no es válido.")  
            return
        # Verificar si el RFC del padre ya existe en la base de datos
        cursor1.execute("SELECT rfc_padre FROM padre WHERE rfc_padre = %s;", (rfcReceptor,))
        if cursor1.fetchone() is None:

            self.mostrar_mensaje("Error","critico","RFC del padre no existente.") 
            return

        try:
            # Insertar datos en la tabla 'alumno'
            cursor1.execute(
                "INSERT INTO alumno (curp, nombre, apellido_paterno, apellido_materno, fecha_nacimiento) VALUES (%s, %s, %s, %s,%s)",
                (curpAlumno, nombreAlumno, apellidoPalumno, apellidoMalumno,fechaNacAlum)
            )

            # Insertar datos en la tabla 'alumno_nivel_escolar'
            cursor1.execute(
                "INSERT INTO alumno_nivel_escolar (curp, id_nivel_escolar) VALUES (%s, %s)",
                (curpAlumno, id_nivel_escolar)
            )

            # Insertar datos en la tabla 'alumno_padre'
            cursor1.execute(
                "INSERT INTO alumno_padre (curp, rfc_padre) VALUES (%s, %s)",
                (curpAlumno, rfcReceptor)
            )
            
            # Insertar datos en la tabla 'alumno_instituto'
            cursor1.execute(
                "INSERT INTO alumno_instituto (curp, clave_centro_trabajo) VALUES (%s, %s)",
                (curpAlumno, claveTrabajo)
            )

            # Confirmar cambios en la base de datos
            conexion1.commit()
            self.mostrar_mensaje("Exito","informacion","Datos guardados correctamente.") 

        except psycopg2.Error as e:
            conexion1.rollback()  # Revertir cambios si ocurre un error
            self.mostrar_mensaje("Error","critico",f"Error al guardar datos del alumno: {e}") 
    
    def modificar_alumno(self):
        nombreAlumno = self.ui.lineEdit_NombreAlumno.text().strip()
        curpAlumno = self.ui.lineEdit_CURPalumno.text().strip()
        apellidoPalumno = self.ui.lineEdit_ApellidoPalumno.text().strip()
        apellidoMalumno = self.ui.lineEdit_ApellidoMalumno.text().strip()
        rfcReceptor = self.ui.lineEdit_RFCtutorAlumno.text().strip()
        claveTrabajo = self.ui.lineEdit_ClaveTrabajoAlumno.text().strip()
        id_nivel_escolar = self.ui.comboBox_NivelEducativo.currentData()[0]
        fechaNacAlum = self.ui.dateEdit.date().toString("ddMMyyyy")
        curpAlumnoaf1 = self.curpaf


        if  len(curpAlumno)<18:
            self.mostrar_mensaje("Error","advertencia","El tamaño del campo CURP no está completo.")
            
        if len(rfcReceptor)<13:
            self.mostrar_mensaje("Error","advertencia","El tamaño del campo RFC del tutor no está completo.")
            return
        
        if len(claveTrabajo)<10:
            self.mostrar_mensaje("Error","advertencia","El tamaño del campo Clave de trabajo no está completo.")
            return
        
        if not nombreAlumno or not curpAlumno or not apellidoMalumno or not apellidoPalumno or not claveTrabajo or not rfcReceptor or not id_nivel_escolar:
           
            self.mostrar_mensaje("Error","critico","Campos no pueden estar vacíos.")
            return
        
        try:
        
            cursor1.execute("SELECT rfc_padre FROM padre WHERE rfc_padre = %s;", (rfcReceptor,))
            if cursor1.fetchone() is None:
                self.mostrar_mensaje("Error","critico","RFC del Padre no existe.")
                return
            
            cursor1.execute("ALTER TABLE alumno_instituto DISABLE TRIGGER ALL;")
            cursor1.execute("ALTER TABLE alumno_nivel_escolar DISABLE TRIGGER ALL;")
            cursor1.execute("ALTER TABLE alumno DISABLE TRIGGER ALL;")

            # Actualizar las claves externas en las tablas relacionadas
            cursor1.execute("UPDATE alumno_instituto SET curp = %s WHERE curp = %s;", (curpAlumno, curpAlumnoaf1))
            cursor1.execute("UPDATE alumno_nivel_escolar SET curp = %s WHERE curp = %s;", (curpAlumno, curpAlumnoaf1))
            cursor1.execute("UPDATE alumno SET curp = %s, nombre = %s, apellido_paterno = %s, apellido_materno = %s, fecha_nacimiento = %s WHERE curp = %s", (curpAlumno, nombreAlumno, apellidoPalumno, apellidoMalumno, fechaNacAlum, curpAlumnoaf1))

            # Actualizar la clave primaria en la tabla principal
            cursor1.execute("UPDATE alumno_padre SET curp = %s, rfc_padre = %s WHERE curp = %s;", (curpAlumno, rfcReceptor, curpAlumnoaf1))

            # Reactivar las restricciones de clave externa
            cursor1.execute("ALTER TABLE alumno_instituto ENABLE TRIGGER ALL;")
            cursor1.execute("ALTER TABLE alumno_nivel_escolar ENABLE TRIGGER ALL;")
            cursor1.execute("ALTER TABLE alumno ENABLE TRIGGER ALL;")

            # Confirmar los cambios
            conexion1.commit()

            self.mostrar_mensaje("Exito","informacion","Datos modificados correctamente.")
            self.actualizar_contenido_alumno()

        except psycopg2.Error as e:
            conexion1.rollback()
            self.mostrar_mensaje("Error","critico", f"Error al modificar datos del alumno: {e}")
            
    def cargar_alumnos(self):
        """Función para cargar todos los alumnos en el ComboBox"""
        try:
            # Obtener todos los alumnos de la tabla
            cursor1.execute("SELECT curp, nombre, apellido_paterno, apellido_materno FROM alumno;")
            alumnos = cursor1.fetchall()

            # Limpiar el ComboBox y agregar la opción "Buscar"
            self.ui.comboBox_BuscarAlumno.clear()
            self.ui.comboBox_BuscarAlumno.addItem("Buscar alumno")  # Placeholder

            # Agregar alumnos al ComboBox
            for alumno in alumnos:
                #curp, nombre, apellido_paterno, apellido_materno = alumno
                #texto_combobox = f"{curp} {apellido_paterno} {apellido_materno} {nombre}"
                self.ui.comboBox_BuscarAlumno.addItem(alumno[0])  # Agregar CURP como dato asociado
            
            # Seleccionar el placeholder para que se muestre al inicio
            self.ui.comboBox_BuscarAlumno.setCurrentIndex(0)

        except psycopg2.Error as e:
            self.mostrar_mensaje("Error","critico", f"Error al cargar alumnos: {e}")
    
    def mostrar_datos_alumno(self):
        """Función para mostrar los datos del alumno seleccionado en los QLineEdit"""
        # Obtener el CURP seleccionado en el ComboBox
        curp_seleccionado = self.ui.comboBox_BuscarAlumno.currentText()
        print(curp_seleccionado)

        # Verificar que se haya seleccionado un CURP válido
        if curp_seleccionado is None:
            return  # Si no hay CURP, no hacemos nada

        try:
            # Consultar datos del alumno desde la tabla 'alumno'
            cursor1.execute("SELECT nombre, apellido_paterno, apellido_materno, curp, fecha_nacimiento FROM alumno WHERE curp = %s;", (curp_seleccionado,))
            alumno_datos = cursor1.fetchone()

            cursor1.execute("SELECT rfc_padre FROM alumno_padre WHERE curp = %s;", (curp_seleccionado,))
            alumno_padre_datos = cursor1.fetchone()

            cursor1.execute("SELECT clave_centro_trabajo FROM alumno_instituto WHERE curp = %s;", (curp_seleccionado,))
            alumno_instituto_datos = cursor1.fetchone()

            cursor1.execute("SELECT id_nivel_escolar FROM alumno_nivel_escolar WHERE curp = %s;", (curp_seleccionado,))
            alumno_nivel_datos = cursor1.fetchone()
            
            # Si se encuentran datos en la tabla 'alumno'
            if alumno_datos:
                nombre, apellido_paterno, apellido_materno, curp, fechaNacimiento = alumno_datos
                rfc_padre, = alumno_padre_datos
                clave_centro_trabajo, = alumno_instituto_datos
                id_alumno_nivel, = alumno_nivel_datos
                print("ID Nivel Educativo obtenido:", id_alumno_nivel)
                # Obtener el nombre del nivel educativo basado en el id_alumno_nivel
                cursor1.execute("SELECT nivel FROM costo_nivel_escolar WHERE id_nivel_escolar = %s;", (id_alumno_nivel,))
                nivel_educativo_dato = cursor1.fetchone()
                print(nivel_educativo_dato)
                if nivel_educativo_dato:
                    nombre_nivel_educativo = nivel_educativo_dato[0]
                    print(nivel_educativo_dato)
                    self.ui.comboBox_NivelEducativo.setCurrentText(nombre_nivel_educativo)
                else:
                    self.ui.comboBox_NivelEducativo.setCurrentText("")  # Si no se encuentra el nivel, limpiar

                # Actualizar el resto de los campos
                self.ui.lineEdit_ClaveTrabajoAlumno.setText(clave_centro_trabajo)
                self.ui.lineEdit_RFCtutorAlumno.setText(rfc_padre)
                self.ui.lineEdit_NombreAlumno.setText(nombre)
                self.ui.lineEdit_ApellidoPalumno.setText(apellido_paterno)
                self.ui.lineEdit_ApellidoMalumno.setText(apellido_materno)
                self.ui.lineEdit_CURPalumno.setText(curp)
                self.ui.dateEdit.setDate(fechaNacimiento)
                self.curpaf = curp

        except psycopg2.Error as e:
            self.mostrar_mensaje("Error","critico", f"Error al mostrar datos del alumno: {e}")

    
    def eliminar_alumno(self):
        
        alumno_a_eliminar = self.ui.lineEdit_CURPalumno.text()

        try:
        
            cursor1.execute("""
                DELETE FROM alumno_instituto
                WHERE curp = %s;
            """, (alumno_a_eliminar,))

            
            cursor1.execute("""
                DELETE FROM alumno_padre 
                WHERE curp = %s;
            """, (alumno_a_eliminar,))

            cursor1.execute("""
                DELETE FROM alumno_nivel_escolar 
                WHERE curp = %s;
            """, (alumno_a_eliminar,))

            cursor1.execute("""
                DELETE FROM alumno
                WHERE curp = %s;
            """, (alumno_a_eliminar,))

            #Confirmar la transacción
            conexion1.commit()
            self.mostrar_mensaje("Exito","informacion","Alumno eliminado exitosamente.")

            self.actualizar_contenido_alumno()      

        except psycopg2.Error as e:
            conexion1.rollback()
            self.mostrar_mensaje("Error Eliminación de Usuario","critico", f"Error al eliminar el usuario: {e}")
    
    def confirmar_eliminacion_alumno(self):
        
        respuesta = self.mostrar_mensaje("Confirmar Eliminación","pregunta","¿Estás seguro de que deseas eliminar este alumno?")
        respuesta.setStandardButtons(respuesta.StandardButton.Yes | respuesta.StandardButton.No)

        # Ejecutar el cuadro de diálogo y capturar la respuesta
        resultado = respuesta.exec()
        if resultado == QMessageBox.StandardButton.Yes:
            self.eliminar_alumno()
            self.ui.lineEdit_ApellidoPalumno.clear()
            self.ui.lineEdit_NombreAlumno.clear()
            self.ui.lineEdit_ApellidoMalumno.clear()
            self.ui.lineEdit_CURPalumno.clear()
            self.ui.lineEdit_ClaveTrabajoAlumno.clear()
            self.ui.lineEdit_RFCtutorAlumno.clear()
            
            
    def actualizar_contenido_alumno(self):
        self.ui.comboBox_BuscarAlumno.clear()
        self.cargar_alumnos()
        self.mostrar_datos_alumno()
    
    def validacion_correo(self,correo_electronico):
        correo_electronico = self.ui.lineEdit_CorreoElectronicoPadre.text()
        patron = re.compile(r"\"?([-a-zA-Z0-9.`?{}]+@\w+\.\w+)\"?")
        
        ## msg_box = QMessageBox()
        ##msg_box.setIcon(QMessageBox.Icon.Warning)
        ##msg_box.setWindowTitle("Error")

        if not re.fullmatch(patron, correo_electronico):
            self.mostrar_mensaje("Error","critico", "Correo electrónico inválido.")
        else:
            dominio = correo_electronico.rsplit("@", 1)[-1]
            try:
                respuestas = dns.resolver.resolve(dominio, "MX")
                if bool(respuestas):
                    pass
            except dns.exception.DNSException: #dns libreria dominios
                self.mostrar_mensaje("Error","critico", "Dominio inválido")
    
    def guardar_datos_padre(self):
        nombrePadre = self.ui.lineEdit_NombrePadre.text().strip()
        apellidoPpadre = self.ui.lineEdit_ApellidoPpadre.text().strip()
        apellidoMpadre = self.ui.lineEdit_ApellidoMpadre.text().strip()
        rfcPadre = self.ui.lineEdit_RFCPadre.text().strip()
        correoElectronico = self.ui.lineEdit_CorreoElectronicoPadre.text().strip()
        clave_regimen = self.ui.comboBox_Regimen.currentData()
        fechaNacimiento = self.ui.dateEdit_FechaNacimientoPadre.date().toString()

        if not clave_regimen:
            self.mostrar_mensaje("Error Régimen Inválido","advertencia", "Seleccione un régimen válido.")
            return
        codigoPostal = self.ui.comboBox_CP.currentText().strip()
        calle = self.ui.lineEdit_Calle.text().strip()
        municipio = self.ui.lineEdit_Municipio.text().strip()
        estado = self.ui.lineEdit_Estado.text().strip()
        colonia = self.ui.comboBox_Colonia.currentText().strip()

        nombre_completo =self.ui.lineEdit_ApellidoPpadre.text().strip() + " " + self.ui.lineEdit_ApellidoMpadre.text().strip()+ " " + self.ui.lineEdit_NombrePadre.text().strip()
        print(nombre_completo)
        if self.validar_rfc(rfcPadre, nombre_completo):
            self.mostrar_mensaje("Éxito","informacion", "El RFC es válido para el nombre ingresado.")
            rfcinco = False
        else:
            self.mostrar_mensaje("RFC inválido","advertencia", "El RFC no coincide con el nombre proporcionado.")
            rfcinco = True


        if not rfcPadre or not correoElectronico or not nombrePadre or not apellidoMpadre or not apellidoPpadre:
            self.mostrar_mensaje("Error","critico", "Campos no pueden estar vacíos.")
            return
        if rfcinco:
            self.mostrar_mensaje("Error","critico", "RFC Incorrecto Ingrese el RFC Correcto")
            return

        try:
            # Insertar en la tabla padre
            cursor1.execute("INSERT INTO padre (rfc_padre, nombre, apellido_paterno, apellido_materno, correo_electronico,fecha_nacimiento) VALUES (%s, %s, %s, %s, %s,%s)",
                            (rfcPadre, nombrePadre, apellidoPpadre, apellidoMpadre, correoElectronico,fechaNacimiento,))

            # Insertar en la tabla padre_regimen_fiscal
            cursor1.execute("INSERT INTO padre_regimen_fiscal (rfc_padre, clave_regimen) VALUES (%s, %s)", (rfcPadre, clave_regimen))

            # Insertar en la tabla domicilio_padre y obtener el id_domicilio
            cursor1.execute("INSERT INTO domicilio_padre (estado, municipio, colonia, codigo_postal, calle, rfc_padre) VALUES (%s, %s, %s, %s, %s,%s)",
                            (estado, municipio, colonia, codigoPostal, calle,rfcPadre))
            
            # Confirmar cambios en la base de datos
            conexion1.commit()
            self.mostrar_mensaje("Éxito","informacion", "Datos guardados correctamente.")

            self.actualizar_contenido_padre()
        
        except psycopg2.Error as e:
            conexion1.rollback()
            self.mostrar_mensaje("Error al Guardar Padre","critico", f"Error al guardar datos del padre correctamente: {e}")
          

    

    def cargar_padres(self):
        """Función para cargar todos los alumnos en el ComboBox"""
        try:
            # Obtener todos los alumnos de la tabla
            cursor1.execute("SELECT rfc_padre FROM padre;")
            padres = cursor1.fetchall()

            # Limpiar el ComboBox y agregar la opción "Buscar"
            self.ui.comboBox_BuscarPadre.clear()
            self.ui.comboBox_BuscarPadre.addItem("Buscar Padre")  # Placeholder

            # Agregar alumnos al ComboBox
            for padre in padres:
                #curp, nombre, apellido_paterno, apellido_materno = alumno
                #texto_combobox = f"{curp} {apellido_paterno} {apellido_materno} {nombre}"
                self.ui.comboBox_BuscarPadre.addItem(padre[0])  # Agregar CURP como dato asociado
            
            # Seleccionar el placeholder para que se muestre al inicio
                self.ui.comboBox_BuscarPadre.setCurrentIndex(0)

        except psycopg2.Error as e:
            QMessageBox.critical(self, "Error Cargar Padre", f"Error al cargar padres: {e}")
    
    
    def mostrar_datos_padre(self):
        """Función para mostrar los datos del padre seleccionado en los QLineEdit"""
        # Obtener el RFC seleccionado en el ComboBox
        rfc_seleccionado = self.ui.comboBox_BuscarPadre.currentText()
        print(rfc_seleccionado)

        # Verificar que se haya seleccionado un RFC válido
        if rfc_seleccionado is None:
            print(rfc_seleccionado)
            return  # Si no hay RFC, no hacemos nada

        try:
            # Consultar datos del padre desde la tabla 'padre'
            cursor1.execute("SELECT nombre, apellido_paterno, apellido_materno, correo_electronico FROM padre WHERE rfc_padre = %s;",(rfc_seleccionado,))
            padre_datos = cursor1.fetchone()
            print(rfc_seleccionado)

            cursor1.execute("SELECT clave_regimen FROM padre_regimen_fiscal WHERE rfc_padre = %s;", (rfc_seleccionado,))
            padre_regimen_datos = cursor1.fetchone()
            print(padre_regimen_datos)

            cursor1.execute("SELECT estado, municipio, colonia, codigo_postal, calle FROM domicilio_padre WHERE rfc_padre = %s;", (rfc_seleccionado,))
            padre_domicilio_datos = cursor1.fetchone()
            print(padre_domicilio_datos)
            
            if padre_datos:
                nombre, apellido_paterno, apellido_materno, correo_electronico = padre_datos
                estado, municipio, colonia, codigo_postal, calle = padre_domicilio_datos
                print(estado,municipio,colonia,codigo_postal,calle)
                cursor1.execute("SELECT nombre_regimen FROM regimen_fiscal WHERE clave_regimen = %s;",(padre_regimen_datos))
                regimen_padre = cursor1.fetchone()
                print(regimen_padre)
                if regimen_padre:
                    regimen_padre = regimen_padre[0]
                    self.ui.comboBox_Regimen.setCurrentText(str(regimen_padre))
                else:
                    self.ui.comboBox_Regimen.setCurrentText("")

                self.ui.lineEdit_Estado.setText(estado)
                self.ui.lineEdit_Municipio.setText(municipio)
               # self.ui.lineEdit_CodigoPostal.setText(str(codigo_postal))
                self.ui.lineEdit_Calle.setText(calle)
                #self.ui.lineEdit_Colonia.setText(colonia)
                
                self.ui.lineEdit_ApellidoMpadre.setText(apellido_materno)
                self.ui.lineEdit_NombrePadre.setText(nombre)
                self.ui.lineEdit_ApellidoPpadre.setText(apellido_paterno)
                self.ui.lineEdit_CorreoElectronicoPadre.setText(correo_electronico)
                self.ui.lineEdit_RFCPadre.setText(rfc_seleccionado)
                self.rfcaf = rfc_seleccionado

        except psycopg2.Error as e:
            QMessageBox.critical(self, "Error Mostrar Padre", f"Error al mostrar datos del padre: {e}")

    def modificar_padre(self):
        nombrePadre = self.ui.lineEdit_NombrePadre.text().strip()
        apellidoPpadre = self.ui.lineEdit_ApellidoPpadre.text().strip()
        apellidoMpadre = self.ui.lineEdit_ApellidoMpadre.text().strip()
        rfcPadre = self.ui.lineEdit_RFCPadre.text().strip()
        correoElectronico = self.ui.lineEdit_CorreoElectronicoPadre.text().strip()
        clave_regimen = self.ui.comboBox_Regimen.currentData()
        if not clave_regimen:
            QMessageBox.warning(self, "Error Régimen Inválido", "Seleccione un régimen válido.")
            return
        codigoPostal = self.ui.lineEdit_CodigoPostal.text().strip()
        calle = self.ui.lineEdit_Calle.text().strip()
        municipio = self.ui.lineEdit_Municipio.text().strip()
        estado = self.ui.lineEdit_Estado.text().strip()
        colonia = self.ui.lineEdit_Colonia.text().strip()
        rfcPadreaf1 = self.rfcaf

        if not rfcPadre or not correoElectronico or not nombrePadre or not apellidoMpadre or not apellidoPpadre:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Error")
            msg_box.setText("Campos no pueden estar vacíos.")
            msg_box.exec() 
            return
        if not self.validacion_correo(correoElectronico):
            return

        try:
            
            

            cursor1.execute("ALTER TABLE alumno_padre DISABLE TRIGGER ALL;")
            cursor1.execute("ALTER TABLE domicilio_padre DISABLE TRIGGER ALL;")
            cursor1.execute("ALTER TABLE padre_regimen_fiscal DISABLE TRIGGER ALL;")

            # Actualizar las claves externas en las tablas relacionadas
            cursor1.execute("UPDATE alumno_padre SET rfc_padre = %s WHERE rfc_padre = %s;", (rfcPadre, rfcPadreaf1))
            cursor1.execute("UPDATE domicilio_padre SET estado = %s, municipio = %s, colonia = %s, codigo_postal = %s, calle = %s, rfc_padre = %s WHERE rfc_padre = %s;", (estado, municipio, colonia, codigoPostal, calle, rfcPadre, rfcPadreaf1))
            cursor1.execute("UPDATE padre_regimen_fiscal SET rfc_padre = %s, clave_regimen = %s WHERE rfc_padre = %s;", (rfcPadre, clave_regimen, rfcPadreaf1))

            # Actualizar la clave primaria en la tabla principal
            cursor1.execute("UPDATE padre SET rfc_padre = %s, nombre = %s, apellido_paterno = %s, apellido_materno = %s, correo_electronico = %s WHERE rfc_padre = %s;", (rfcPadre, nombrePadre, apellidoPpadre, apellidoMpadre, correoElectronico, rfcPadreaf1))

            # Reactivar las restricciones de clave externa
            cursor1.execute("ALTER TABLE alumno_padre ENABLE TRIGGER ALL;")
            cursor1.execute("ALTER TABLE domicilio_padre ENABLE TRIGGER ALL;")
            cursor1.execute("ALTER TABLE padre_regimen_fiscal ENABLE TRIGGER ALL;")

            # Confirmar los cambios
            conexion1.commit()
            
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("Éxito")
            msg_box.setText("Datos modificados correctamente.")
            msg_box.exec()
            self.actualizar_contenido_padre()
        except psycopg2.Error as e:
            conexion1.rollback()
            QMessageBox.critical(self,"Error", f"Error al modificar datos del padre: {e}")



    def eliminar_padre(self):
        padre_a_eliminar = self.ui.lineEdit_RFCPadre.text().strip()  # Asegúrate de quitar espacios en blanco

        try:
            # Primero, obtener los CURPs de los alumnos relacionados con el rfc_padre
            cursor1.execute("""
                SELECT curp FROM alumno_padre
                WHERE rfc_padre = %s;
            """, (padre_a_eliminar,))

            # Obtener todos los CURPs relacionados
            alumnos_relacionados = cursor1.fetchall()

            # Si hay alumnos relacionados, eliminarlos
            if alumnos_relacionados:
                for alumno in alumnos_relacionados:
                    curp_alumno = alumno[0]

                    # Eliminar de las tablas relacionadas al alumno
                    cursor1.execute("""
                        DELETE FROM alumno_nivel_escolar
                        WHERE curp = %s;
                    """, (curp_alumno,))

                    cursor1.execute("""
                        DELETE FROM alumno_instituto
                        WHERE curp = %s;
                    """, (curp_alumno,))

                    cursor1.execute("""
                        DELETE FROM alumno_padre
                        WHERE curp = %s;
                    """, (curp_alumno,))

                    cursor1.execute("""
                        DELETE FROM alumno
                        WHERE curp = %s;
                    """, (curp_alumno,))

            # Ahora, proceder a eliminar el padre y sus relaciones
            cursor1.execute("""
                DELETE FROM padre_regimen_fiscal 
                WHERE rfc_padre = %s;
            """, (padre_a_eliminar,))

            cursor1.execute("""
                DELETE FROM domicilio_padre 
                WHERE rfc_padre = %s;
            """, (padre_a_eliminar,))

            # Eliminar de la tabla padre
            cursor1.execute("""
                DELETE FROM padre
                WHERE rfc_padre = %s;
            """, (padre_a_eliminar,))

            # Confirmar la transacción
            conexion1.commit()

            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("Éxito")
            msg_box.setText("Padre e hijos eliminados exitosamente.")
            msg_box.exec() 
            self.actualizar_contenido_padre()
            
        except psycopg2.Error as e:
            conexion1.rollback()  # Revertir cambios en caso de error
            QMessageBox.critical(self, "Error", f"Error al eliminar el padre: {e}")


    def confirmar_eliminacion_padre(self):

        respuesta = QMessageBox()
        respuesta.setIcon(QMessageBox.Icon.Question)
        respuesta.setWindowTitle("Confirmar Eliminación")
        respuesta.setText("¿Estás seguro de que deseas eliminar este Padre?")
        respuesta.setStandardButtons(respuesta.StandardButton.Yes | respuesta.StandardButton.No)
        # Ejecutar el cuadro de diálogo y capturar la respuesta
        resultado = respuesta.exec()
        
        if resultado == QMessageBox.StandardButton.Yes:
            self.eliminar_padre()
            self.ui.lineEdit_ApellidoMpadre.clear()
            self.ui.lineEdit_ApellidoPpadre.clear()
            self.ui.lineEdit_NombrePadre.clear()
            self.ui.lineEdit_RFCPadre.clear()
            self.ui.lineEdit_CodigoPostal.clear()
            self.ui.lineEdit_CorreoElectronicoPadre.clear()
            self.ui.lineEdit_Calle.clear()
            self.ui.lineEdit_Colonia.clear()
            self.ui.lineEdit_Estado.clear()
            self.ui.lineEdit_Municipio.clear()
    
    def configurar_validacion_alfabeto(self, line_edits):
        # Crear un validador que solo permite letras y espacios
        regex = QRegularExpression("^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$")
        validador = QRegularExpressionValidator(regex)

        # Asignar el validador a cada QLineEdit en la lista
        for line_edit in line_edits:
            line_edit.setValidator(validador)

    def configurar_validacion_alfabeto1(self, comboboxs):
        # Crear un validador que solo permite letras y espacios
        regex = QRegularExpression("^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$")
        validador = QRegularExpressionValidator(regex)

        # Asignar el validador a cada QLineEdit en la lista
        for combobox in comboboxs:
            comboboxs.setValidator(validador)
    
    def configurar_validacion_alfanumerico(self, line_edits):

        regex = QRegularExpression("^[a-zA-Z0-9]+$")
        validador = QRegularExpressionValidator(regex)

        for line_edit in line_edits:
            line_edit.setValidator(validador)

    def validacacion_numerica(self, comboboxs):
        regex = QRegularExpression("^[0-9]+$")
        validador = QRegularExpressionValidator(regex)

        for combobox in comboboxs:
            combobox.setValidator(validador)
        

    def actualizar_contenido_padre(self):
        self.ui.comboBox_BuscarPadre.clear()
        self.cargar_padres()
        self.mostrar_datos_padre()
    
    def obtener_nivel_educativo(self):
        cursor1.execute("SELECT id_nivel_escolar, nivel, costo FROM costo_nivel_escolar")

        niveles = cursor1.fetchall()

        for id_nivel, nombre_nivel, costo in niveles:  # Cambié el orden de los valores
            self.ui.comboBox_NivelEducativo.addItem(nombre_nivel,(id_nivel,costo) )
    
        self.ui.comboBox_NivelEducativo.currentIndexChanged.connect(self.actualizar_costo_nivel)

    def actualizar_costo_nivel(self):
        """Función para actualizar el costo en labelCosto cuando se cambia el nivel educativo."""
        # Obtener los datos asociados al nivel seleccionado (id_nivel, costo)
        datos_nivel = self.ui.comboBox_NivelEducativo.currentData()
        
        if datos_nivel:
            _, costo = datos_nivel  # Extraer solo el costo de los datos del nivel
            self.ui.label_CantidadPago.setText(f"${costo:.2f}")  # Mostrar el costo en formato monetario
        else:
            self.ui.label_CantidadPago.setText("")  # Limpiar el costo si no se selecciona ningún nivel

        

    def obtener_regimen_fiscal(self):
        cursor1.execute("SELECT clave_regimen, nombre_regimen FROM regimen_fiscal")
        regimenes  = cursor1.fetchall()

        for clave_regimen, regimen in regimenes:
            self.ui.comboBox_Regimen.addItem(regimen,clave_regimen)


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
        #"""Función que maneja el cierre de la ventana (cuando el usuario cierra el programa)"""
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
                VALUES (%s, %s, %s,%s) 
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

                if existe_usuario is None:
                    QMessageBox.warning(self, "Advertencia", "El nuevo usuario no existe en cuenta_emisor.")
                    return
                
                
                cursor1.execute("ALTER TABLE emisor_cuenta_emisor DISABLE TRIGGER ALL;")
                cursor1.execute("ALTER TABLE emisor DISABLE TRIGGER ALL;")
                cursor1.execute("ALTER TABLE cuenta_emisor DISABLE TRIGGER ALL;")
                
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

                cursor1.execute("ALTER TABLE emisor_cuenta_emisor ENABLE TRIGGER ALL;")
                cursor1.execute("ALTER TABLE emisor ENABLE TRIGGER ALL;")
                cursor1.execute("ALTER TABLE cuenta_emisor ENABLE TRIGGER ALL;")
                
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
        #self.vizualizar_Bitacora()  # Refrescar la tabla de bitácora, si es necesario

    # Función para generar las primeras letras del RFC basado en el nombre
    def generar_rfc_inicial(self, nombre_completo):
        nombres = nombre_completo.split()
        print(nombres)
        
        if len(nombres) < 3:
            return None  # Necesitamos al menos un nombre y dos apellidos
        
        apellido1, apellido2, nombre = nombres[0], nombres[1], nombres[2]
        
        # Obtener la primera letra y primera vocal interna del primer apellido
        primera_letra_apellido1 = apellido1[0].upper()
        vocal_apellido1 = self.obtener_vocal(apellido1[1:])
        
        # Primera letra del segundo apellido
        primera_letra_apellido2 = apellido2[0].upper()
        
        # Primera letra del primer nombre
        primera_letra_nombre = nombre[0].upper()
        
        # Construimos la parte inicial del RFC
        return f"{primera_letra_apellido1}{vocal_apellido1}{primera_letra_apellido2}{primera_letra_nombre}"

    def obtener_vocal(self, texto):
        for letra in texto:
            if letra.upper() in "AEIOU":
                return letra.upper()
        return "X"  # Si no hay vocales, se usa "X"

    # Función para validar RFC contra el nombre
    def validar_rfc(self, rfc, nombre_completo):
        rfc_generado = self.generar_rfc_inicial(nombre_completo)
        if not rfc_generado:
            return False  # No se pudo generar RFC inicial
        if rfc.startswith(rfc_generado):
            return True
        return False

        
    #def mostrar_mensaje(self, titulo, mensaje):
     #   mensaje_box = QMessageBox()
      #  mensaje_box.setWindowTitle(titulo)
       # mensaje_box.setText(mensaje)
        #mensaje_box.exec()

    def validar_correo(self, correo):
        patron = r"^[\w\.-]+@[a-zA-Z\d-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(patron, correo))
    
    def generar_curp_inicial(self, nombre_completo, fecha_nacimiento):
        nombres = nombre_completo.split()
        print(nombres)
        estado = "xx"  # Si no hay estado, dejar vacío
        sexo = "x" 
        
        if len(nombres) < 3:
            return None  # Necesitamos al menos un nombre y dos apellidos
        if len(nombres) == 4:
            apellido1, apellido2, nombre, snombre = nombres[0], nombres[1], nombres[3], nombres[2]
        if len(nombres) == 3:
             apellido1, apellido2, nombre = nombres[0], nombres[1], nombres[2]
        
        # Obtener la primera letra y primera vocal interna del primer apellido
        primera_letra_apellido1 = apellido1[0].upper()
        vocal_apellido1 = self.obtener_vocal(apellido1[1:])
        
        # Primera letra del segundo apellido
        primera_letra_apellido2 = apellido2[0].upper()
        
        # Primera letra del primer nombre
        primera_letra_nombre = nombre[0].upper()
        
        # Parte de la fecha en formato AAMMDD
        fecha_curp = fecha_nacimiento[2:4] + fecha_nacimiento[4:7] + fecha_nacimiento[7:9]

        # Primera consonante interna del primer apellido, segundo apellido y nombre
        consonante1 = self.obtener_consonante(apellido1[1:])
        consonante2 = self.obtener_consonante(apellido2[1:])
        consonante_nombre = self.obtener_consonante(nombre[1:])

        # Construimos la parte inicial de la CURP
        return f"{primera_letra_apellido1}{vocal_apellido1}{primera_letra_apellido2}{primera_letra_nombre}{fecha_curp}{sexo}{estado}{consonante1}{consonante2}{consonante_nombre}"

    def obtener_vocal(self, texto):
        for letra in texto:
            if letra.upper() in "AEIOU":
                return letra.upper()
        return "X"  # Si no hay vocales, se usa "X"

    def obtener_consonante(self, texto):
        for letra in texto:
            if letra.upper() not in "AEIOU":
                return letra.upper()
        return "X"  # Si no hay consonante interna, se usa "X"

    # Función para validar CURP contra el nombre y fecha de nacimiento
    def validar_curp(self, curp, nombre_completo, fecha_nacimiento):
        curp_generada = self.generar_curp_inicial(nombre_completo, fecha_nacimiento)
        
        if not curp_generada:
            return False  # No se pudo generar CURP inicial
        # Comparar solo la parte relevante (sin sexo ni estado)
        curp_relevante = curp_generada[:10] + curp_generada[13:16]  # Incluimos las consonantes internas (14, 15, 16)
        curp_ingresada_relevante = curp[:10] + curp[13:16]  # Tomamos solo la parte relevante de la CURP ingresada
        
        print(curp_relevante)
        print(curp_ingresada_relevante)

        # Validamos si las partes relevantes coinciden
        if curp_ingresada_relevante == curp_relevante:
            return True
        return False

    def validar_rfc1(self, rfc):
        patron = r"^[A-ZÑ&]{3,4}\d{6}[A-Z\d]{3}$"
        return bool(re.match(patron, rfc))
    
    
    def cargar_CP(self):
        """Función para cargar todos los CP en el ComboBox"""
        try:
            # Obtener todos los alumnos de la tabla
            cursor1.execute("SELECT codigo_postal FROM cp_g GROUP BY codigo_postal ORDER BY codigo_postal ASC;")
            cps = cursor1.fetchall()

            # Limpiar el ComboBox y agregar la opción "Buscar"
            self.ui.comboBox_CP.clear()

            # Agregar cp al ComboBox
            for cp in cps:
                cp_postal = str(cp[0])
                #curp, nombre, apellido_paterno, apellido_materno = alumno
                #texto_combobox = f"{curp} {apellido_paterno} {apellido_materno} {nombre}"
                self.ui.comboBox_CP.addItem(cp_postal)  # Agregar CURP como dato asociado
            
            # Seleccionar el placeholder para que se muestre al inicio
            self.ui.comboBox_CP.setCurrentIndex(0)

        except psycopg2.Error as e:
            self.mostrar_mensaje("Error","critico",f"Error al cargar Codigos Postales: {e}") 
            #QMessageBox.critical(self, "Error", f"Error al cargar Codigos Postales: {e}")

    def mostrar_datos_CP(self):
        self.cp_seleccionado = self.ui.comboBox_CP.currentText()
        """Función para mostrar los datos del alumno seleccionado en los QLineEdit"""
        # Obtener el CURP seleccionado en el ComboBox

        print(self.cp_seleccionado)

        # Verificar que se haya seleccionado un CURP válido
        if self.cp_seleccionado is None:
            return  # Si no hay CURP, no hace nada

        try:
            # Consultar datos del alumno desde la tabla 'alumno'
            cursor1.execute("SELECT colonia, municipio, estado FROM cp_g WHERE codigo_postal = %s ;",(self.cp_seleccionado,))
            cp_info = cursor1.fetchone()
            
            # Si se encuentran datos en la tabla 'alumno'
            if cp_info:
                self.cargar_Colonia()
                estado = cp_info[2]
                # Actualizar el resto de los campos
                self.ui.lineEdit_Estado.setText(estado)

        except psycopg2.Error as e:
            QMessageBox.critical(self, "Error", f"Error al mostrar datos del cp: {e}")

    def cargar_Colonia(self):
        cp = self.ui.comboBox_CP.currentText()
        cp_entero = int(cp)
        print(cp)
        try:
            # Obtener todos los alumnos de la tabla
            cursor1.execute("SELECT colonia FROM cp_g WHERE codigo_postal = %s;", (cp_entero,))
            colonias = cursor1.fetchall()

            # Limpiar el ComboBox y agregar la opción "Buscar"
            self.ui.comboBox_Colonia.clear()
            self.ui.comboBox_Colonia.addItem("Buscar Colonia")  # Placeholder

            # Agregar alumnos al ComboBox
            for colonia in colonias:
                colonia1 = colonia[0]
                #curp, nombre, apellido_paterno, apellido_materno = alumno
                #texto_combobox = f"{curp} {apellido_paterno} {apellido_materno} {nombre}"
                self.ui.comboBox_Colonia.addItem(colonia1)  # Agregar CURP como dato asociado
            
            # Seleccionar el placeholder para que se muestre al inicio
            self.ui.comboBox_Colonia.setCurrentIndex(0)

        except psycopg2.Error as e:
            QMessageBox.critical(self, "Error", f"Error al cargar Colonia: {e}")


    def mostrar_datos_Colonia(self):
        colonia = self.ui.comboBox_Colonia.currentText()
        """Función para mostrar los datos del alumno seleccionado en los QLineEdit"""
        # Obtener el CURP seleccionado en el ComboBox

        print(colonia)

        # Verificar que se haya seleccionado un CURP válido
        if colonia is None:
            return  # Si no hay CURP, no hacemos nada
    


if __name__ == "__main__":#

    app = QApplication(sys.argv)
    window = Menus()  # Crear una instancia de la clase Menu
    window.setWindowTitle("FACTURTEC")
    window.show()
    sys.exit(app.exec())
