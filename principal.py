#LIBRERIAS
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
from PyPDF2 import PdfMerger, PdfReader, PdfWriter, PageObject
from PyQt6.QtCore import QUrl,QDate
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtCore import QRegularExpression
from login_main import logins


class Menus(QMainWindow):
    def __init__(self, user=None, fecha_inicio=None, cargo=None): 
        super(Menus, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.is_logged = False

################################## USUARIO #####################################################################################################################################
        # Variables para el usuario y las fechas de inicio y cierre de sesión
        self.user = user
        self.fecha_inicio = fecha_inicio
        self.fecha_cierre = None
        self.cargo = cargo
        self.ui.label_NombreEmisor.setText(user) 
        self.ui.label_CargoEmisor.setText(cargo)
        self.cp_seleccionado = ''
        print(f"Usuario: {self.user}, Fecha de inicio: {self.fecha_inicio}")
        #Función para verificar el rol del usuario
        def abrir_modificar_usuario(cargo):
            if cargo == "DIRECTOR":
                # Cambia a la página de modificar usuario
                self.ui.stackedWidget.setCurrentWidget(self.ui.page_ModificarUsuario)
            else:
                self.mostrar_mensaje("Acceso denegado","advertencia","Solo el director tiene acceso.")

        self.ui.pushButton_Respaldo.clicked.connect(lambda: abrir_modificar_usuario(cargo))

        self.ui.BotonModificarAlta.clicked.connect(self.modificar_datos)
        self.ui.comboBoxAlta.activated.connect(self.cargar_datos_usuario)
        self.vizualizar_Bitacora()
        self.cargar_usuarios()
        self.cargar_alumnos()
        self.cargar_Cargo()
        #BOTONES ACCION USUARIO
        self.ui.BotonInsertarAlta.clicked.connect(self.guardar_datos_usuarios)
        self.ui.BotonEliminarAlta.clicked.connect(self.confirmar_eliminacion)

################################################## PAGINAS ###########################################################################################################################
       
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_Principal)
        #Cambiar de página
        self.ui.pushButton_Alumno.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.page_Alumno))
        self.ui.pushButton_Padre.clicked.connect(lambda:self.ui.stackedWidget.setCurrentWidget(self.ui.page_Padre))
        self.ui.pushButton_NuevaFactura.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.page_Factura))
        self.ui.pushButton_Bitacora.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.page_Bitacora))
        #Cerrar sesión
        self.ui.pushButton_Cerrarsesion.clicked.connect(self.cerrarSesion)
        #CONFIGURAR MAYUSCULAS
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

############################################### ABRIR PDF ####################################################################################################################3
    
     # Conectar el botón a la función que abre el PDF
        self.ui.pushButton_2.clicked.connect(self.abrir_Pdf_Usuario)
        self.ui.pushButton_Preevisualizar.clicked.connect(self.abrir_Pdf_Factura)
          
############################################ PADRE ######################################################################################################################################
       
        self.ui.lineEdit_RFCPadre.setMaxLength(13)
        self.ui.lineEdit_RFCtutorAlumno.setMaxLength(13)
        lineEditcp = self.ui.comboBox_CP.lineEdit()
        lineEditcp.setMaxLength(5)

        self.ui.comboBox_BuscarPadre.activated.connect(self.mostrar_datos_padre)
        self.ui.comboBox_SeleccionarPadre.activated.connect(self.mostrar_datos_padre_factura)
        #BONOTES ACCION PADRE
        self.ui.PushBoton_Insertar_Padre.clicked.connect(self.guardar_datos_padre) #INSERTAR
        self.ui.PushBoton_Modificar_Padre.clicked.connect(self.modificar_padre) #MODIFICAR
        self.ui.PushBoton_Eliminar_Padre.clicked.connect(self.confirmar_eliminacion_padre) #ELIMINAR

        self.obtener_regimen_fiscal()
        self.validacacion_numerica([self.ui.comboBox_CP])
        self.cargar_padres()
        self.cargar_CP()
        self.cargar_Colonia()
        self.configurar_validacion_alfabeto([self.ui.lineEdit_NombrePadre, self.ui.lineEdit_ApellidoPpadre, self.ui.lineEdit_ApellidoMpadre,self.ui.lineEdit_Municipio, self.ui.lineEdit_Estado, self.ui.comboBox_Colonia])
        self.ui.comboBox_CP.activated.connect(self.mostrar_datos_CP)
        self.ui.comboBox_Colonia.activated.connect(self.mostrar_datos_Colonia)

# ############################################# ALUMNO ################################################################################################################################       
      
        self.ui.lineEdit_CURPalumno.setMaxLength(18)
        #BOTONES ACCION ALUMNO
        self.ui.PushBoton_Insertar_Alumno.clicked.connect(self.guardar_datos_alumno) #INSERTAR
        self.ui.PushBoton_Eliminar_Alumno.clicked.connect(self.confirmar_eliminacion_alumno) #ELIMINAR
        self.ui.PushBoton_Modificar_Alumno.clicked.connect(self.modificar_alumno) #MODIFICAR

        self.ui.dateEdit.dateChanged.connect(self.cargar_nivel_escolar)
        self.ui.comboBox_BuscarAlumno.activated.connect(self.mostrar_datos_alumno)
        self.configurar_validacion_alfabeto([self.ui.lineEdit_NombreAlumno, self.ui.lineEdit_ApellidoPalumno, self.ui.lineEdit_ApellidoMalumno])
        
######################################### FACTURA ###############################################################################################################################################
        self.ui.comboBox_SeleccionarAlumno.activated.connect(self.mostrar_datos_alumnoFact)
        self.configurar_validacion_alfanumerico([self.ui.lineEdit_CURPalumno, self.ui.lineEdit_RFCPadre, self.ui.lineEdit_ClaveTrabajoAlumno,self.ui.lineEdit_RFCtutorAlumno])
        self.cargar_seleecion_padre()
        self.cargar_seleccion_alumno()
        self.cargar_cfdi()
        self.cargar_forma_pago()

############################# FUNCIONES COMUNES #########################################################################################
 #VALIDA RFC
    def validar_rfc1(self, rfc):
        patron = r"^[A-ZÑ&]{3,4}\d{6}[A-Z\d]{3}$"
        return bool(re.match(patron, rfc))
    
 ##ABRIR PDF Global
    def abrir_Pdf_Usuario(self): #pdf USURIO
        self.open_pdf("reporte_final_membrete.pdf")

    def abrir_Pdf_Factura(self):#pdf FACTURA
        self.open_pdf("Factura_Sin_SELLOS.pdf")

    #abrir un PDF
    def open_pdf(self,Nombre_pdf):
    
        pdf_path = Nombre_pdf
        
        if os.path.isfile(pdf_path):
            try:
             QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))
            except Exception as e:
             self.mostrar_mensaje("Error","critico",f"No se pudo abrir el archivo '{pdf_path}'.\nError: {str(e)}")
        else:
            self.mostrar_mensaje("Error","critico", f"El archivo '{pdf_path}' no se encontró.")

   #CONFIGURAR MAYUSCULAS
    def configurar_mayusculas(self, line_edits):
        """Conecta la función convertir_mayusculas a los QLineEdit especificados."""
        for line_edit in line_edits:
            line_edit.textChanged.connect(lambda _, le=line_edit: self.convertir_mayusculas(le))
   
    #CONVERTIR MAYUSCULAS
    def convertir_mayusculas(self, line_edit):
        """Convierte el texto a mayúsculas en el QLineEdit proporcionado."""
        texto = line_edit.text()
        line_edit.setText(texto.upper())

    #ABRIR VENTANA
    def openLoginWindow(self):
        self.main_window = logins()
        self.main_window.show()
        self.destroy()
    
     #MONSTRAR MENSAJE PERSONALIZADO
    def mostrar_mensaje(self, titulo, tipo_ventana, mensaje):
        msg_box = QMessageBox() 
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
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
            no_button = msg_box.button(QMessageBox.StandardButton.No)

            yes_button.setText("Sí")
            no_button.setText("No")
        else:
         msg_box.setIcon(QMessageBox.Icon.NoIcon)

        return msg_box.exec()
    
    #CONFIGURAR VALIDACION ALFABETO
    def configurar_validacion_alfabeto(self, line_edits):
        # Crear un validador que solo permite letras y espacios
        regex = QRegularExpression("^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$")
        validador = QRegularExpressionValidator(regex)
        # Asignar el validador a cada QLineEdit en la lista
        for line_edit in line_edits:
            line_edit.setValidator(validador)

    #CONFIGURAR VALIDACION ALFANUMERICO
    def configurar_validacion_alfanumerico(self, line_edits):
        regex = QRegularExpression("^[a-zA-ZáéíóúÁÉÍÓÚñÑ0-9]+$")
        validador = QRegularExpressionValidator(regex)

        for line_edit in line_edits:
            line_edit.setValidator(validador)

    #VALIDACION NUMERIO
    def validacacion_numerica(self, comboboxs):
        regex = QRegularExpression("^[0-9]+$")
        validador = QRegularExpressionValidator(regex)
        for combobox in comboboxs:
            combobox.setValidator(validador)
     
    
    #VALIDAR PADRE - HIJO
    def validarPadreHijo(self, curps, rfcs, apellidop, apellidom, apellidopH, apellidomH):
        curp_relevante = curps[:10] + curps[13:16]
        curpCMama = curps[2]
        
        if (curp_relevante[:2] == rfcs[:2] or curpCMama == rfcs[0])and(apellidom == apellidomH or apellidop == apellidopH or apellidom == apellidopH or apellidop == apellidomH ) :
                es_valido = True
        else:
            es_valido = False
        return es_valido

    #CERRAR SESION
    def cerrarSesion(self):
        respuesta = self.mostrar_mensaje("Confirmar cierre de sesión","pregunta","¿Estás seguro que desear cerrar sesión?")
        if respuesta == QMessageBox.StandardButton.Yes:
            self.fecha_cierre = datetime.datetime.now().replace(microsecond=0)   # Registrar la hora de cierre de sesión
            self.is_logged=True
            self.mostrar_mensaje("Cerrar sesion","informacion","Volverá al login")
            self.GuardarLog()
            self.openLoginWindow()     
        else:
            pass #no hace nada si es nope

 #GENERAR RFC INICAL
    def generar_rfc_inicial(self, nombre_completo):
        nombres = nombre_completo.split()
        print(nombres)
        if len(nombres) < 3:
            return None 
        if len(nombres) == 4:
            apellido1, apellido2, nombre, snombre = nombres[0], nombres[1], nombres[3], nombres[2]
        if len(nombres) == 3:
             apellido1, apellido2, nombre = nombres[0], nombres[1], nombres[2]
                
        primera_letra_apellido1 = apellido1[0].upper()
        vocal_apellido1 = self.obtener_vocal(apellido1[1:])
        
        primera_letra_apellido2 = apellido2[0].upper()
        
        primera_letra_nombre = nombre[0].upper()
        
        return f"{primera_letra_apellido1}{vocal_apellido1}{primera_letra_apellido2}{primera_letra_nombre}"

    #OBTENER VOCAL
    def obtener_vocal(self, texto):
        for letra in texto:
            if letra.upper() in "AEIOU":
                return letra.upper()
        return "X"  

    #VALIDAR RFC
    def validar_rfc(self, rfc, nombre_completo):
        rfc_generado = self.generar_rfc_inicial(nombre_completo)
        print(rfc_generado)
        if not rfc_generado:
            return False  
        if rfc.startswith(rfc_generado):
            return True
        return False

    #VALIDAR CORREO
    def validar_correo(self, correo):
        patron = r"^[\w\.-]+@[a-zA-Z\d-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(patron, correo))

############################################# ALUMNO #######################################################################
 
    #GENERA CURP INICIAL
    def generar_curp_inicial(self, nombre_completo, fecha_nacimiento):
        nombres = nombre_completo.split()
        estado = "xx"  
        sexo = "x" 
        
        if len(nombres) < 3:
            return None  
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

        # Parte inicial de la CURP
        return f"{primera_letra_apellido1}{vocal_apellido1}{primera_letra_apellido2}{primera_letra_nombre}{fecha_curp}{sexo}{estado}{consonante1}{consonante2}{consonante_nombre}"
    
    #OBTIENE VOCAL
    def obtener_vocal(self, texto):
        for letra in texto:
            if letra.upper() in "AEIOU":
                return letra.upper()
        return "X"  

    #OBTENER CONSTANTE
    def obtener_consonante(self, texto):
        for letra in texto:
            if letra.upper() not in "AEIOU":
                return letra.upper()
        return "X" 

    # VALIDA CURP CON NOMBRE Y FECHA
    def validar_curp(self, curp, nombre_completo, fecha_nacimiento):
        curp_generada = self.generar_curp_inicial(nombre_completo, fecha_nacimiento)
        
        if not curp_generada:
            return False 
        curp_relevante = curp_generada[:10] + curp_generada[13:16]  
        curp_ingresada_relevante = curp[:10] + curp[13:16] 
        print("curp ingresada")
        print(curp_ingresada_relevante)
        print("curp generada") 
        print(curp_generada)
        print("curp relevante")
        print(curp_relevante)

        if curp_ingresada_relevante == curp_relevante:
            return True
        return False

    #GUARDAR ALUMNO
    def guardar_datos_alumno(self):
    # Obtener los datos de los campos
        nombreAlumno = self.ui.lineEdit_NombreAlumno.text().strip()
        curpAlumno = self.ui.lineEdit_CURPalumno.text().strip()
        apellidoPalumno = self.ui.lineEdit_ApellidoPalumno.text().strip()
        apellidoMalumno = self.ui.lineEdit_ApellidoMalumno.text().strip()
        rfcReceptor = self.ui.lineEdit_RFCtutorAlumno.text().strip()
        claveTrabajo = self.ui.lineEdit_ClaveTrabajoAlumno.text().strip()
        fechaNacAlum = self.ui.dateEdit.date().toString("ddMMyyyy")
        id_nivel_escolar = self.ui.lineEdit_NivelEducativo2.text().strip()

        fecha_invertida = fechaNacAlum[4:] + fechaNacAlum[2:4] + fechaNacAlum[:2]
        nombre_completo =self.ui.lineEdit_ApellidoPalumno.text().strip() + " " + self.ui.lineEdit_ApellidoMalumno.text().strip()+ " " + self.ui.lineEdit_NombreAlumno.text().strip()

        if not nombreAlumno or not curpAlumno or not apellidoMalumno or not apellidoPalumno or not claveTrabajo or not rfcReceptor or not id_nivel_escolar:  
            self.mostrar_mensaje("Error","critico","Campos no pueden estar vacíos")  
            return
        
        if not self.validar_curp(curpAlumno, nombre_completo, fecha_invertida):
            self.mostrar_mensaje("CURP inválida","advertencia", "La CURP no coincide con el nombre y fecha proporcionados.")
            return
        else:
            self.mostrar_mensaje("Éxito","informacion", "La CURP es válida para el nombre y fecha ingresados.")

            
        if  len(curpAlumno)<18:
            self.mostrar_mensaje("Error","informacion","El tamaño del campo CURP no está completo.")
            return
        
        if len(rfcReceptor)<13:
            self.mostrar_mensaje("Error","advertencia", "El tamaño del campo RFC del tutor no está completo.")
            return
        
        if not self.validar_rfc1(rfcReceptor):
            self.mostrar_mensaje("RFC inválido","advertencia", "Por favor, ingresa un RFC válido.")


        if len(claveTrabajo)<10:
             
            self.mostrar_mensaje("Error","advertencia", "El tamaño del campo Clave de trabajo no está completo.")
            return
        
        #VALIDA QUE LOS APELLIDOS COINCIDAN CON ALGUN PADRE
        cursor1.execute("SELECT apellido_paterno, apellido_materno FROM padre WHERE rfc_padre = %s;",(rfcReceptor,))
        apelldidosP = cursor1.fetchone()
        
        #APELLIDOS NO ENCONTRADOS
        if apelldidosP == None:
            self.mostrar_mensaje("Error", "critico", "Datos del padre no encontrados")
            return
        
        apellidoPa = apelldidosP[0]
        apellidoMa = apelldidosP [1]
        print("apellido paterno",apellidoPa)
        print("apellido materno",apellidoMa)

        #APELLIDOS NO VALIDOS
        if not self.validarPadreHijo(curpAlumno, rfcReceptor, apellidoPa, apellidoMa, apellidoPalumno, apellidoMalumno):
                self.mostrar_mensaje("Error", "critico", "El padre no coincide con el hijo")
                return
        
        fechaNacAlum = self.ui.dateEdit.date().toString()
        cursor1.execute("SELECT rfc_padre FROM padre WHERE rfc_padre = %s;", (rfcReceptor,))
    
        if cursor1.fetchone() is None:
            self.mostrar_mensaje("Error","critico","RFC del padre no existente.") 
            return
        
        #INSERTAR DATOS EN LA TABLA ALUMNO
        try:
            cursor1.execute(
                "INSERT INTO alumno (curp, nombre, apellido_paterno, apellido_materno, fecha_nacimiento) VALUES (%s, %s, %s, %s,%s)",
                (curpAlumno, nombreAlumno, apellidoPalumno, apellidoMalumno,fechaNacAlum)
            )

            # Insertar datos en la tabla 'alumno_nivel_escolar'
            cursor1.execute(
                "INSERT INTO alumno_nivel_escolar (curp, id_nivel_escolar) VALUES (%s, %s)",
                (curpAlumno, claveTrabajo)
            )

            # Insertar datos en la tabla 'alumno_padre'
            cursor1.execute(
                "INSERT INTO alumno_padre (curp, rfc_padre) VALUES (%s, %s)",
                (curpAlumno, rfcReceptor)
            )
            
            # Insertar datos en la tabla 'alumno_instituto'
            """cursor1.execute(
                "INSERT INTO alumno_instituto (curp, clave_centro_trabajo) VALUES (%s, %s)",
                (curpAlumno, claveTrabajo)
            )"""

            # Confirmar cambios en la base de datos
            conexion1.commit()
            self.mostrar_mensaje("Exito","informacion","Datos guardados correctamente.") 

            #LIMPIAR CAMPOS ALUMNOS
            self.ui.lineEdit_ApellidoPalumno.clear()
            self.ui.lineEdit_NombreAlumno.clear()
            self.ui.lineEdit_ApellidoMalumno.clear()
            self.ui.lineEdit_CURPalumno.clear()
            self.ui.lineEdit_ClaveTrabajoAlumno.clear()
            self.ui.lineEdit_RFCtutorAlumno.clear()
            self.actualizar_contenido_alumno()

        except psycopg2.Error as e:
            conexion1.rollback()  # Revertir cambios si ocurre un error
            self.mostrar_mensaje("Error","critico","Error al guardar alumno, CURP duplicada") 
    
    #MODIFICAR ALUMNO
    def modificar_alumno(self):
        nombreAlumno = self.ui.lineEdit_NombreAlumno.text().strip()
        curpAlumno = self.ui.lineEdit_CURPalumno.text().strip()
        apellidoPalumno = self.ui.lineEdit_ApellidoPalumno.text().strip()
        apellidoMalumno = self.ui.lineEdit_ApellidoMalumno.text().strip()
        rfcReceptor = self.ui.lineEdit_RFCtutorAlumno.text().strip()
        claveTrabajo = self.ui.lineEdit_ClaveTrabajoAlumno.text().strip()
        id_nivel_escolar = self.ui.lineEdit_NivelEducativo2.text().strip()
        fechaNacAlum = self.ui.dateEdit.date().toString("ddMMyyyy")

        fecha_invertida = fechaNacAlum[4:] + fechaNacAlum[2:4] + fechaNacAlum[:2]
        nombre_completo =self.ui.lineEdit_ApellidoPalumno.text().strip() + " " + self.ui.lineEdit_ApellidoMalumno.text().strip()+ " " + self.ui.lineEdit_NombreAlumno.text().strip()
        
        if not nombreAlumno or not curpAlumno or not apellidoMalumno or not apellidoPalumno or not claveTrabajo or not rfcReceptor or not id_nivel_escolar:
            self.mostrar_mensaje("Error","advertencia","Campos no pueden estar vacíos.")
            return

        if not self.validar_curp(curpAlumno, nombre_completo, fecha_invertida):
            self.mostrar_mensaje("CURP inválida","advertencia", "La CURP no coincide con el nombre y fecha proporcionados.")
            return
        
        else:
            self.mostrar_mensaje("Éxito","informacion", "La CURP es válida para el nombre y fecha ingresados.")

        if  len(curpAlumno)<18:
            self.mostrar_mensaje("Error","informacion","El tamaño del campo CURP no está completo.")
            return

        if len(rfcReceptor)<13:
            self.mostrar_mensaje("Error","advertencia", "El tamaño del campo RFC del tutor no está completo.")
            return
        
        if not self.validar_rfc1(rfcReceptor):
            self.mostrar_mensaje("RFC inválido","advertencia", "Por favor, ingresa un RFC válido.")


        if len(claveTrabajo)<10: 
            self.mostrar_mensaje("Error","advertencia", "El tamaño del campo Clave de trabajo no está completo.")
            return
        
        cursor1.execute("SELECT apellido_paterno, apellido_materno FROM padre WHERE rfc_padre = %s;",(rfcReceptor,))
        apelldidosP = cursor1.fetchone()

        apellidoPa = apelldidosP[0]
        apellidoMa = apelldidosP [1]

        if not self.validarPadreHijo(curpAlumno, rfcReceptor, apellidoPa, apellidoMa, apellidoPalumno, apellidoMalumno):
                self.mostrar_mensaje("Error", "critico", "El padre con coincide con el hijo")
                return
        fechaNacAlum = self.ui.dateEdit.date().toString()
        curpAlumnoaf1 = self.curpaf
        
        try:
        
            cursor1.execute("SELECT rfc_padre FROM padre WHERE rfc_padre = %s;", (rfcReceptor,))
            if cursor1.fetchone() is None:
                self.mostrar_mensaje("Error","critico","RFC del Padre no existe.")
                return
            
            cursor1.execute("ALTER TABLE alumno_nivel_escolar DISABLE TRIGGER ALL;")
            cursor1.execute("ALTER TABLE alumno DISABLE TRIGGER ALL;")

            cursor1.execute("UPDATE alumno_nivel_escolar SET curp = %s WHERE curp = %s;", (curpAlumno, curpAlumnoaf1))
            cursor1.execute("UPDATE alumno SET curp = %s, nombre = %s, apellido_paterno = %s, apellido_materno = %s, fecha_nacimiento = %s WHERE curp = %s", (curpAlumno, nombreAlumno, apellidoPalumno, apellidoMalumno, fechaNacAlum, curpAlumnoaf1))

            # Actualizar la clave primaria en la tabla principal
            cursor1.execute("UPDATE alumno_padre SET curp = %s, rfc_padre = %s WHERE curp = %s;", (curpAlumno, rfcReceptor, curpAlumnoaf1))

            # Reactivar las restricciones de clave externa
            cursor1.execute("ALTER TABLE alumno_nivel_escolar ENABLE TRIGGER ALL;")
            cursor1.execute("ALTER TABLE alumno ENABLE TRIGGER ALL;")

            # Confirmar los cambios
            conexion1.commit()
            self.mostrar_mensaje("Exito","informacion","Datos modificados correctamente.")
            self.actualizar_contenido_alumno()

        except psycopg2.Error as e:
            conexion1.rollback()
            self.mostrar_mensaje("Error","critico", f"Error al modificar datos del alumno: {e}")
    
    # CARGAR ALUMNOS        
    def cargar_alumnos(self):
        """Función para cargar todos los alumnos en el ComboBox"""
        try:
            # Obtener todos los alumnos de la tabla
            cursor1.execute("SELECT curp, nombre, apellido_paterno, apellido_materno FROM alumno ORDER BY apellido_paterno ;")
            alumnos = cursor1.fetchall()

            # Limpiar el ComboBox y agregar la opción "Buscar"
            self.ui.comboBox_BuscarAlumno.clear()
            self.ui.comboBox_BuscarAlumno.addItem("Buscar alumno") 

            # Agregar alumnos al ComboBox
            for alumno in alumnos:
                self.ui.comboBox_BuscarAlumno.addItem(alumno[0]) 
            
            # Seleccionar el placeholder para que se muestre al inicio
            self.ui.comboBox_BuscarAlumno.setCurrentIndex(0)

        except psycopg2.Error as e:
            self.mostrar_mensaje("Error","critico", f"Error al cargar alumnos: {e}")
    
    #MOSTRAR ALUMNO
    def mostrar_datos_alumno(self):
        """Función para mostrar los datos del alumno seleccionado en los QLineEdit"""
        curp_seleccionado = self.ui.comboBox_BuscarAlumno.currentText()
        print(curp_seleccionado)

        if curp_seleccionado == "Buscar alumno":
            self.ui.lineEdit_ApellidoPalumno.clear()
            self.ui.lineEdit_NombreAlumno.clear()
            self.ui.lineEdit_ApellidoMalumno.clear()
            self.ui.lineEdit_CURPalumno.clear()
            self.ui.lineEdit_ClaveTrabajoAlumno.clear()
            self.ui.lineEdit_RFCtutorAlumno.clear()
            self.ui.lineEdit_NivelEducativo2.clear()
            self.ui.label_CantidadPago.clear()
            return

        # Verificar que se haya seleccionado un CURP válido
        if curp_seleccionado is None:
            return  # Si no hay CURP, no hacemos nada

        try:
            cursor1.execute("SELECT nombre, apellido_paterno, apellido_materno, curp, fecha_nacimiento FROM alumno WHERE curp = %s;", (curp_seleccionado,))
            alumno_datos = cursor1.fetchone()

            cursor1.execute("SELECT rfc_padre FROM alumno_padre WHERE curp = %s;", (curp_seleccionado,))
            alumno_padre_datos = cursor1.fetchone()

            cursor1.execute("SELECT id_nivel_escolar FROM alumno_nivel_escolar WHERE curp = %s;", (curp_seleccionado,))
            alumno_nivel_datos = cursor1.fetchone()
            
            cursor1.execute("SELECT id_nivel_escolar FROM alumno_nivel_escolar WHERE curp = %s;", (curp_seleccionado,))
            alumno_nivel_datos = cursor1.fetchone()

            id_alumno_nivel, = alumno_nivel_datos
            print(id_alumno_nivel)


            cursor1.execute("SELECT nivel FROM costo_nivel_escolar WHERE id_nivel_escolar = %s;", (id_alumno_nivel,))
            nivel_educativo_dato = cursor1.fetchone()[0]
            print(nivel_educativo_dato)
            
            # Si se encuentran datos en la tabla 'alumno'
            if alumno_datos:
                nombre, apellido_paterno, apellido_materno, curp, fechaNacimiento = alumno_datos
                rfc_padre, = alumno_padre_datos
                nivelescolar = nivel_educativo_dato
                
                self.ui.lineEdit_NivelEducativo2.setText(nivelescolar)# Si no se encuentra el nivel, limpiar
                # Actualizar el resto de los campos
                self.ui.lineEdit_ClaveTrabajoAlumno.setText(id_alumno_nivel)
                self.ui.lineEdit_RFCtutorAlumno.setText(rfc_padre)
                self.ui.lineEdit_NombreAlumno.setText(nombre)
                self.ui.lineEdit_ApellidoPalumno.setText(apellido_paterno)
                self.ui.lineEdit_ApellidoMalumno.setText(apellido_materno)
                self.ui.lineEdit_CURPalumno.setText(curp)
                self.ui.dateEdit.setDate(fechaNacimiento)
                self.curpaf = curp

        except psycopg2.Error:
            self.mostrar_mensaje("Error","critico", "Error al mostrar datos del alumno")

    #ELIMINAR ALUMNO
    def eliminar_alumno(self):

        alumno_a_eliminar = self.ui.lineEdit_CURPalumno.text()
        try:
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

        except psycopg2.Error:
            conexion1.rollback()
            self.mostrar_mensaje("Error Eliminación de Usuario","critico", "Error al eliminar el usuario")
    
    #CONFIRMAR ELIMINACION
    def confirmar_eliminacion_alumno(self):

        if not self.ui.lineEdit_RFCtutorAlumno.text().strip() or not self.ui.lineEdit_CURPalumno.text().strip() or not self.ui.lineEdit_ApellidoMalumno.text().strip() or not self.ui.lineEdit_NombreAlumno.text().strip() or not self.ui.lineEdit_ApellidoPalumno.text().strip():
            self.mostrar_mensaje("Error","advertencia","Alumno no seleccionado aún.")
            return
        
        respuesta = self.mostrar_mensaje("Confirmar Eliminación","pregunta","¿Estás seguro de que deseas eliminar este alumno?")  
        
        if respuesta == QMessageBox.StandardButton.Yes:
            self.eliminar_alumno()
            self.ui.lineEdit_ApellidoPalumno.clear()
            self.ui.lineEdit_NombreAlumno.clear()
            self.ui.lineEdit_ApellidoMalumno.clear()
            self.ui.lineEdit_CURPalumno.clear()
            self.ui.lineEdit_ClaveTrabajoAlumno.clear()
            self.ui.lineEdit_RFCtutorAlumno.clear()
        else:
            pass

    #ACTUALIZAR CONTENIDO ALUMNO
    def actualizar_contenido_alumno(self):
        self.ui.comboBox_BuscarAlumno.clear()
        self.cargar_alumnos()
        self.cargar_seleccion_alumno()
    
    #CARGAR NIVEL ESCOLAR
    def cargar_nivel_escolar(self):
        fechaNacAlum = self.ui.dateEdit.date()

        edad = QDate.currentDate().year() - fechaNacAlum.year()
        print(edad)

        if edad <= 15 and edad > 12: #Fecha de secundaria
            cursor1.execute("SELECT id_nivel_escolar, nivel,costo from costo_nivel_escolar where nivel = 'SECUNDARIA'",)
            nivel = cursor1.fetchone()
        elif edad > 6 and edad <= 12: #Fecha de primaria
            cursor1.execute("SELECT id_nivel_escolar, nivel,costo from costo_nivel_escolar where nivel = 'PRIMARIA'",)
            nivel = cursor1.fetchone()
        elif edad >= 3 and edad <= 6: #Fecha de preescolar
            cursor1.execute("SELECT id_nivel_escolar, nivel,costo from costo_nivel_escolar where nivel = 'PREESCOLAR'",) #fecha de preescolar
            nivel = cursor1.fetchone()
        else: 
            self.mostrar_mensaje("Error", "critico", "Edad fuera de rango")
            return

        id_nivel_escolar, nivelescolar, costoNivel = nivel

        self.ui.lineEdit_ClaveTrabajoAlumno.setText(str(id_nivel_escolar))
        self.ui.lineEdit_NivelEducativo2.setText(nivelescolar)
        self.ui.label_CantidadPago.setText(str(costoNivel))    

###################################### PADRE ##########################################################################################
    
    #VALIDACION CORREO
    def validacion_correo(self,correo_electronico):
        correo_electronico = self.ui.lineEdit_CorreoElectronicoPadre.text().lower()
        patron = re.compile(r"\"?([-a-zA-Z0-9.`?{}]+@\w+\.\w+)\"?")

        if not re.fullmatch(patron, correo_electronico):
            self.mostrar_mensaje("Error","critico", "Correo electrónico inválido.")
            return False
        else:
            print("segui aqui")
            dominio_completo = correo_electronico.rsplit("@", 1)[-1]
            dominio = dominio_completo.split(".", 1)[0]
            print(dominio)
            try:
                cursor1.execute('SELECT dominio FROM dominio_correo WHERE dominio = %s;',(dominio,))
                respuestas = cursor1.fetchone()
                if (respuestas == None):
                    return False
                else:
                    return True
            except psycopg2.Error:
                self.mostrar_mensaje("Error","critico", "Dominio inválido")
                return False
    
    #GUARDAR DATOS PADRE
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


        if self.validar_rfc(rfcPadre, nombre_completo):
            self.mostrar_mensaje("Éxito","informacion", "El RFC es válido para el nombre ingresado.")
            rfcinco = False
        else:
            self.mostrar_mensaje("RFC inválido","advertencia", "El RFC no coincide con el nombre proporcionado.")
            rfcinco = True
        
        CorreoMini = correoElectronico.lower()
        if not self.validacion_correo(CorreoMini): 
            self.mostrar_mensaje("Dominio invalido","advertencia", "Dominio inválido")
            return

        if not rfcPadre or not correoElectronico or not nombrePadre or not apellidoMpadre or not apellidoPpadre:
            self.mostrar_mensaje("Error","critico", "Campos no pueden estar vacíos.")
            return
        if rfcinco:
            self.mostrar_mensaje("Error","critico", "RFC Incorrecto Ingrese el RFC Correcto")
            return
        if len(codigoPostal)<5:
            self.mostrar_mensaje("Error","advertencia", "El tamaño del código postal no está completo.")
            
        if len(rfcPadre)<13:
            self.mostrar_mensaje("Error","advertencia", "El tamaño del RFC no está completo.")
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

            #LIMPIAR DATOS PADRE
            self.ui.lineEdit_NombrePadre.clear()
            self.ui.lineEdit_ApellidoPpadre.clear()
            self.ui.lineEdit_ApellidoMpadre.clear()
            self.ui.lineEdit_CorreoElectronicoPadre.clear()
            self.ui.lineEdit_RFCPadre.clear()
            self.ui.lineEdit_Calle.clear()
            self.ui.lineEdit_Municipio.clear()
            self.ui.lineEdit_Estado.clear()

            self.actualizar_contenido_padre()
        
        except psycopg2.Error as e:
            conexion1.rollback()
            self.mostrar_mensaje("Error al Guardar Padre","critico", f"Error al guardar datos del padre correctamente: {e}")
        
    
    #CARGAR PADRES
    def cargar_padres(self):
        try:
            cursor1.execute("SELECT rfc_padre FROM padre ORDER BY apellido_paterno;")
            padres = cursor1.fetchall()

            self.ui.comboBox_BuscarPadre.clear()
            self.ui.comboBox_BuscarPadre.addItem("Buscar Padre") 

            for padre in padres:
                self.ui.comboBox_BuscarPadre.addItem(padre[0])  
                self.ui.comboBox_BuscarPadre.setCurrentIndex(0)

        except psycopg2.Error as e:
            self.mostrar_mensaje("Error Cargar Padre","critico", f"Error al cargar padres: {e}")
    
    #MOSTRAR PADRE
    def mostrar_datos_padre(self):
        """Función para mostrar los datos del padre seleccionado en los QLineEdit"""
        rfc_seleccionado = self.ui.comboBox_BuscarPadre.currentText()

        # Verificar que se haya seleccionado un RFC válido
        if rfc_seleccionado is None:
            return

        if rfc_seleccionado == "Buscar Padre":
            self.ui.lineEdit_ApellidoPpadre.clear()
            self.ui.lineEdit_NombrePadre.clear()
            self.ui.lineEdit_ApellidoMpadre.clear()
            self.ui.lineEdit_RFCPadre.clear()
            self.ui.lineEdit_Calle.clear()
            self.ui.lineEdit_Estado.clear()
            self.ui.lineEdit_Municipio.clear()
            self.ui.lineEdit_CorreoElectronicoPadre.clear()
            return

        try:
            # Consultar datos del padre desde la tabla 'padre'
            cursor1.execute("SELECT nombre, apellido_paterno, apellido_materno, correo_electronico, fecha_nacimiento FROM padre WHERE rfc_padre = %s;",(rfc_seleccionado,))
            padre_datos = cursor1.fetchone()

            cursor1.execute("SELECT clave_regimen FROM padre_regimen_fiscal WHERE rfc_padre = %s;", (rfc_seleccionado,))
            padre_regimen_datos = cursor1.fetchone()

            cursor1.execute("SELECT estado, municipio, colonia, codigo_postal, calle FROM domicilio_padre WHERE rfc_padre = %s;", (rfc_seleccionado,))
            padre_domicilio_datos = cursor1.fetchone()
            
            if padre_datos:
                nombre, apellido_paterno, apellido_materno, correo_electronico, fechaNacimiento = padre_datos
                estado, municipio, colonia, codigo_postal, calle = padre_domicilio_datos
                cursor1.execute("SELECT nombre_regimen FROM regimen_fiscal WHERE clave_regimen = %s;",(padre_regimen_datos))
                regimen_padre = cursor1.fetchone()
                if regimen_padre:
                    regimen_padre = regimen_padre[0]
                    self.ui.comboBox_Regimen.setCurrentText(str(regimen_padre))
                else:
                    self.ui.comboBox_Regimen.setCurrentText("")
                
                self.ui.lineEdit_Estado.setText(estado)
                self.ui.lineEdit_Municipio.setText(municipio)
                self.ui.comboBox_CP.setCurrentText(str(codigo_postal))
                self.ui.lineEdit_Calle.setText(calle)
                self.ui.comboBox_Colonia.setCurrentText(colonia)
                self.ui.lineEdit_ApellidoMpadre.setText(apellido_materno)
                self.ui.lineEdit_NombrePadre.setText(nombre)
                self.ui.lineEdit_ApellidoPpadre.setText(apellido_paterno)
                self.ui.lineEdit_CorreoElectronicoPadre.setText(correo_electronico)
                self.ui.lineEdit_RFCPadre.setText(rfc_seleccionado)
                self.ui.dateEdit_FechaNacimientoPadre.setDate(fechaNacimiento)
                self.rfcaf = rfc_seleccionado
                self.cargar_ColoniaEspecial()

        except psycopg2.Error as e:
            self.mostrar_mensaje("Error Mostrar Padre","critico", f"Error al mostrar datos del padre: {e}")
            
    #MODIFICAR PADRE
    def modificar_padre(self):
        #DATOS PERSONLAES
        nombrePadre = self.ui.lineEdit_NombrePadre.text().strip()
        apellidoPpadre = self.ui.lineEdit_ApellidoPpadre.text().strip()
        apellidoMpadre = self.ui.lineEdit_ApellidoMpadre.text().strip()
        rfcPadre = self.ui.lineEdit_RFCPadre.text().strip()
        correoElectronico = self.ui.lineEdit_CorreoElectronicoPadre.text().strip()
        clave_regimen = self.ui.comboBox_Regimen.currentData()

        if not clave_regimen:
            self.mostrar_mensaje("Error Régimen Inválido","advertencia", "Seleccione un régimen válido.")
            return

        #Datos FISCALES
        codigoPostal = self.ui.comboBox_CP.currentText().strip() 
        calle = self.ui.lineEdit_Calle.text().strip()
        municipio = self.ui.lineEdit_Municipio.text().strip()
        estado = self.ui.lineEdit_Estado.text().strip()
        colonia = self.ui.comboBox_Colonia.currentText().strip() 
        
        if not rfcPadre or not correoElectronico or not nombrePadre or not apellidoMpadre or not apellidoPpadre or not clave_regimen or not codigoPostal or not calle or not municipio:
            self.mostrar_mensaje("Error","advertencia", "Campos no pueden estar vacíos.")
            return
        
        CorreoMini = correoElectronico.lower()
        if not self.validacion_correo(CorreoMini): 
            self.mostrar_mensaje("Dominio invalido","advertencia", "Dominio inválido")
            return
        
        rfcPadreaf1 = self.rfcaf

        try:
            cursor1.execute("ALTER TABLE alumno_padre DISABLE TRIGGER ALL;")
            cursor1.execute("ALTER TABLE domicilio_padre DISABLE TRIGGER ALL;")
            cursor1.execute("ALTER TABLE padre_regimen_fiscal DISABLE TRIGGER ALL;")

            # Actualizar las claves externas en las tablas relacionadas
            cursor1.execute("UPDATE alumno_padre SET rfc_padre = %s WHERE rfc_padre = %s;", (rfcPadre, rfcPadreaf1))
            cursor1.execute("UPDATE domicilio_padre SET estado = %s, municipio = %s, colonia = %s, codigo_postal = %s, calle = %s, rfc_padre = %s WHERE rfc_padre = %s;", (estado, municipio, colonia, codigoPostal, calle, rfcPadre, rfcPadreaf1))
            cursor1.execute("UPDATE padre_regimen_fiscal SET rfc_padre = %s, clave_regimen = %s WHERE rfc_padre = %s;", (rfcPadre, clave_regimen, rfcPadreaf1))
            cursor1.execute("UPDATE padre SET rfc_padre = %s, nombre = %s, apellido_paterno = %s, apellido_materno = %s, correo_electronico = %s WHERE rfc_padre = %s;", (rfcPadre, nombrePadre, apellidoPpadre, apellidoMpadre, correoElectronico, rfcPadreaf1))

            # Reactivar las restricciones de clave externa
            cursor1.execute("ALTER TABLE alumno_padre ENABLE TRIGGER ALL;")
            cursor1.execute("ALTER TABLE domicilio_padre ENABLE TRIGGER ALL;")
            cursor1.execute("ALTER TABLE padre_regimen_fiscal ENABLE TRIGGER ALL;")

            # Confirmar los cambios
            conexion1.commit()

            self.mostrar_mensaje("Éxito","informacion", "Datos modificados correctamente.") 
            self.actualizar_contenido_padre()

        except psycopg2.Error as e:
            conexion1.rollback()
            self.mostrar_mensaje("Error","critico", f"Error al modificar datos del padre: {e}")
    
    #ELIMIAR PADRE
    def eliminar_padre(self):
        padre_a_eliminar = self.ui.lineEdit_RFCPadre.text().strip() 

        try:
            cursor1.execute("""
                SELECT curp FROM alumno_padre
                WHERE rfc_padre = %s;
            """, (padre_a_eliminar,))

            alumnos_relacionados = cursor1.fetchall()

            if alumnos_relacionados:
                for alumno in alumnos_relacionados:
                    curp_alumno = alumno[0]

                    cursor1.execute("""
                        DELETE FROM alumno_nivel_escolar
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

            self.mostrar_mensaje("Éxito","informacion", "Padre e hijos eliminados exitosamente.")
            self.actualizar_contenido_padre()
            
        except psycopg2.Error as e:
            conexion1.rollback()  # Revertir cambios en caso de error
            self.mostrar_mensaje("Error","critico", f"Error al eliminar el padre: {e}")

    #CONFIRMAR ELIMINACION
    def confirmar_eliminacion_padre(self):
        resultado = self.mostrar_mensaje("Confirmar Eliminación","pregunta","¿Estás seguro de que deseas eliminar este Padre?")
        
        if resultado == QMessageBox.StandardButton.Yes:
            self.eliminar_padre()
            self.actualizar_contenido_alumno()
            self.ui.lineEdit_CURPalumno.clear()
            self.ui.lineEdit_NombreAlumno.clear()
            self.ui.lineEdit_RFCtutorAlumno.clear()
            self.ui.lineEdit_ApellidoMalumno.clear()
            self.ui.lineEdit_ApellidoPalumno.clear()
            self.ui.lineEdit_ClaveTrabajoAlumno.clear()
            self.ui.dateEdit.clear()
            self.ui.lineEdit_NivelEducativo2.clear()
            self.ui.label_CantidadPago.clear()
            self.ui.lineEdit_ApellidoMpadre.clear()
            self.ui.lineEdit_ApellidoPpadre.clear()
            self.ui.lineEdit_NombrePadre.clear()
            self.ui.lineEdit_RFCPadre.clear()
            self.ui.comboBox_CP.clear()
            self.ui.lineEdit_CorreoElectronicoPadre.clear()
            self.ui.lineEdit_Calle.clear()
            self.ui.comboBox_Colonia.clear()
            self.ui.lineEdit_Estado.clear()
            self.ui.lineEdit_Municipio.clear()

    #ACTUALIZAR DATOS PADRE
    def actualizar_contenido_padre(self):
        self.ui.comboBox_BuscarPadre.clear()
        self.cargar_padres()
        self.mostrar_datos_padre()
        self.cargar_seleecion_padre()
    
    #OBTENER REGIMEN FISCAL
    def obtener_regimen_fiscal(self):
        cursor1.execute("SELECT clave_regimen, nombre_regimen FROM regimen_fiscal")
        regimenes  = cursor1.fetchall()
        for clave_regimen, regimen in regimenes:
            self.ui.comboBox_Regimen.addItem(regimen,clave_regimen)
   
    #VALIDA CP 
    def cargar_CP(self):
        try:
            cursor1.execute("SELECT codigo_postal FROM cp_g GROUP BY codigo_postal ORDER BY codigo_postal ASC;")
            cps = cursor1.fetchall()

            self.ui.comboBox_CP.clear()

            for cp in cps:
                cp_postal = str(cp[0])
           
                self.ui.comboBox_CP.addItem(cp_postal)  
            
            self.ui.comboBox_CP.setCurrentIndex(0)

        except psycopg2.Error as e:
            self.mostrar_mensaje("Error","critico",f"Error al cargar Codigos Postales: {e}") 
    
    #MONSTRAR DATOS CP
    def mostrar_datos_CP(self):
        self.cp_seleccionado = self.ui.comboBox_CP.currentText()

        if self.cp_seleccionado is None:
            return  

        try:
            cursor1.execute("SELECT colonia, municipio, estado FROM cp_g WHERE codigo_postal = %s ;",(self.cp_seleccionado,))
            cp_info = cursor1.fetchone()
            
            if cp_info:
                self.cargar_Colonia()
                estado = cp_info[2]
                municipio = cp_info[1]
                self.ui.lineEdit_Estado.setText(estado)
                self.ui.lineEdit_Municipio.setText(municipio)

        except psycopg2.Error as e:
            self.mostrar_mensaje("Exito","critico",f"Error al mostrar datos del cp: {e}") 

    #CARGAR COLONIA
    def cargar_Colonia(self):
        cp = self.ui.comboBox_CP.currentText()
        cp_entero = int(cp)
        try:
            cursor1.execute("SELECT colonia FROM cp_g WHERE codigo_postal = %s;", (cp_entero,))
            colonias = cursor1.fetchall()

            self.ui.comboBox_Colonia.clear()

            for colonia in colonias:
                colonia1 = colonia[0]
                self.ui.comboBox_Colonia.addItem(colonia1)  
            
            self.ui.comboBox_Colonia.setCurrentIndex(0)

        except psycopg2.Error as e:
            self.mostrar_mensaje("Error","critico",f"Error al cargar Colonia: {e}") 

    #CARGAR COLONIAS ESPECIFICAS
    def cargar_ColoniaEspecial(self):
        rfcparent = self.ui.lineEdit_RFCPadre.text()
        try:
            cursor1.execute("SELECT colonia FROM domicilio_padre WHERE rfc_padre = %s;", (rfcparent,))
            colonias = cursor1.fetchone()

            self.ui.comboBox_Colonia.clear()

            for colonia in colonias:
                colonia1 = colonia
                self.ui.comboBox_Colonia.addItem(colonia1)  # Agregar CURP como dato asociado
            
            self.ui.comboBox_Colonia.setCurrentIndex(0)

        except psycopg2.Error as e:
            self.mostrar_mensaje("Error","critico",f"Error al cargar Colonia: {e}") 

    #MOSTRAR DATOS COLONIAS
    def mostrar_datos_Colonia(self):
        colonia = self.ui.comboBox_Colonia.currentText()
        if colonia is None:
            return  

########################################### USUARIO ####################################################################################
   
    #GUARDAR SESIONES USUARIO
    def guardar_log_sesion(self):
        """Función para guardar el log de sesión en la base de datos"""
        try:
            sql = "INSERT INTO log_sesiones (usuario, cargo, fecha_inicio, fecha_cierre) VALUES (%s, %s, %s, %s)"
            cursor1.execute(sql, (self.user, self.cargo, self.fecha_inicio, self.fecha_cierre))
            conexion1.commit()

            print(f"Log de sesión guardado para el usuario {self.user} desde {self.fecha_inicio} hasta {self.fecha_cierre}")
        except psycopg2.Error as e:
           self.mostrar_mensaje("Error","critico",f"Error en la conexión con la base de datos: {e}")
           QMessageBox.StandardButton.Close   
    
    #GUARDA LOG
    def GuardarLog(self):
        try:
            # Clase personalizada para PDF
            class PDF(FPDF):
                def header(self):
                    pass  # Dejar el encabezado vacío porque el membrete se maneja por separado

            # Simulación de consulta a la base de datos
            cursor1.execute("SELECT * FROM log_sesiones;")
            registros = cursor1.fetchall()

            # Crear el PDF dinámico
            pdf = PDF()
            pdf.add_page()

            margen_superior = 70  # Espacio reservado para el membrete
            margen_inferior = 20  # Espacio reservado para evitar el pie de página del membrete
            altura_fila = 10  # Altura de cada fila en la tabla

            pdf.set_y(margen_superior)

            # Título del PDF
            pdf.set_font("Arial", "B", 12)
            pdf.cell(200, 10, txt="Reporte de Registros", ln=True, align='C')
            pdf.ln(10)

            # Configurar colores para encabezados de tabla
            pdf.set_fill_color(65, 105, 225)  # Azul
            pdf.set_text_color(255, 255, 255)  # Blanco

            columnas = ['ID', 'Nombre', 'Cargo', 'Fecha de entrada', 'Fecha de salida']
            ancho_columnas = [20, 50, 40, 40, 40]  # Anchos para cada columna

            # Dibujar encabezados de tabla
            for i, columna in enumerate(columnas):
                pdf.cell(ancho_columnas[i], altura_fila, columna, border=1, fill=True)
            pdf.ln()

            # Cambiar color de texto a negro para el contenido
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", size=8)

            # Añadir datos de la base de datos al PDF
            for registro in registros:
                # Verificar si hay suficiente espacio en la página actual
                if pdf.get_y() + altura_fila + margen_inferior > pdf.h:  # pdf.h es la altura de la página
                    pdf.add_page()
                    pdf.set_y(margen_superior)  # Ajustar la posición para respetar el membrete

                    # Redibujar encabezados en la nueva página
                    pdf.set_fill_color(65, 105, 225)  # Azul
                    pdf.set_text_color(255, 255, 255)  # Blanco
                    for i, columna in enumerate(columnas):
                        pdf.cell(ancho_columnas[i], altura_fila, columna, border=1, fill=True)
                    pdf.ln()
                    pdf.set_text_color(0, 0, 0)  # Cambiar a negro para el contenido

                # Dibujar los datos
                for i, dato in enumerate(registro):
                    pdf.cell(ancho_columnas[i], altura_fila, str(dato), border=1)
                pdf.ln()

            # Guardar el PDF temporal con el contenido dinámico
            pdf_path = "contenido_temporal.pdf"
            pdf.output(pdf_path)

            # Leer los PDFs: membrete y contenido dinámico
            membrete_pdf = PdfReader("membrete.pdf")
            contenido_pdf = PdfReader(pdf_path)
            writer = PdfWriter()

            # Fusionar membrete con cada página del contenido dinámico
            for pagina_contenido in contenido_pdf.pages:
                # Crear una nueva página con membrete y contenido
                pagina_membrete = PageObject.create_blank_page(
                    width=membrete_pdf.pages[0].mediabox.width,
                    height=membrete_pdf.pages[0].mediabox.height,
                )
                pagina_membrete.merge_page(membrete_pdf.pages[0])  # Añadir el membrete
                pagina_membrete.merge_page(pagina_contenido)  # Añadir el contenido dinámico
                writer.add_page(pagina_membrete)

            # Guardar el PDF final
            reporte_final = "reporte_final_membrete.pdf"
            with open(reporte_final, "wb") as f:
                writer.write(f)

            print(f"Reporte generado exitosamente: {reporte_final}")
        except psycopg2.Error:
            self.mostrar_mensaje("Error","critico","Error en la conexión con la base de datos")
            QMessageBox.StandardButton.Close,
        except FPDF.error as e:
            self.mostrar_mensaje("Error","critico", f"Error en la generación del PDF: {e}")
            QMessageBox.StandardButton.Close 

     #CIERRA SESION USUARIO
    def closeEvent(self, event):
        self.fecha_cierre = datetime.datetime.now().replace(microsecond=0)
        self.guardar_log_sesion()
        print("LOL")
        self.GuardarLog()
        cursor1.close()
        conexion1.close()  # Generar el PDF del log antes de cerrar el programa
        event.accept()  # Aceptar el cierre del programa
   
    # VIZUALIZA LA BITACORA
    def vizualizar_Bitacora (self):
        try:
            cursor1.execute("SELECT * FROM log_sesiones")
            rows = cursor1.fetchall()
    
            if rows:
                self.ui.tableWidget.setRowCount(len(rows))
                self.ui.tableWidget.setColumnCount(len(rows[0]))
            
                for i, row in enumerate(rows):
                    for j, value in enumerate(row):
                        self.ui.tableWidget.setItem(i, j, QTableWidgetItem(str(value)))
            else:
                self.ui.tableWidget.setRowCount(0)
                self.ui.tableWidget.setColumnCount(0)
          
        except psycopg2.Error as e:
        # Capturar errores de la base de datos, como cuando la tabla no existe
            print("Error al ejecutar la consulta:", e)
            self.ui.tableWidget.setRowCount(0)
            self.ui.tableWidget.setColumnCount(0)

    #GUARDAR USUARIO
    def guardar_datos_usuarios(self):
        # Obtener los valores de los QLineEdit
        rfc = self.ui.RFCAlta.text()
        usuario = self.ui.usuarioAlta.text()
        contraseña = self.ui.contraseAlta.text()
        nombre = self.ui.nombreAlta.text()
        apellido_paterno = self.ui.apellidoPAlta.text()
        apellido_materno = self.ui.apellidoMAlta.text()    
        cargo = self.ui.comboBox_Cargo.currentText()
 
        nombre_completo = self.ui.lineEdit_ApellidoPpadre.text().strip() + " " + self.ui.lineEdit_ApellidoMpadre.text().strip()+ " " + self.ui.lineEdit_NombrePadre.text().strip()

        if not rfc or not nombre or not apellido_materno or not apellido_materno or not usuario or not contraseña or not cargo:
            self.mostrar_mensaje("Error","critico","Campos no pueden estar vacíos")  
            return

        if self.validar_rfc(rfc, nombre_completo):
            self.mostrar_mensaje("Éxito","informacion", "El RFC es válido para el nombre ingresado.")
        else:
            self.mostrar_mensaje("RFC inválido","advertencia", "El RFC no coincide con el nombre proporcionado.")
        
        try:
            cursor1.execute("""
                -- Insertar en emisor y obtener el rfc_emisor
                INSERT INTO emisor (rfc_emisor, nombre, apellido_paterno, apellido_materno)
                VALUES (%s, %s, %s, %s) 
                RETURNING rfc_emisor;
            """, (rfc, nombre, apellido_paterno, apellido_materno))

            rfc_insertado = cursor1.fetchone()[0]

            cursor1.execute("""
                -- Insertar en cuenta_emisor y obtener el usuario
                INSERT INTO cuenta_emisor (usuario, contrasena, cargo, rfc_emisor)
                VALUES (%s, %s, %s,%s) 
                RETURNING usuario;
            """, (usuario, contraseña, cargo, rfc))

            usuario_insertado = cursor1.fetchone()[0]

            cursor1.execute("""
                INSERT INTO emisor_cuenta_emisor (rfc_emisor, usuario) 
                VALUES (%s, %s);
            """, (rfc_insertado, usuario_insertado))

            conexion1.commit()

            self.mostrar_mensaje("Exito","informacion","Los datos fueron guardados exitosamente.")
            self.actualizar_contenido()

        except psycopg2.Error as e:
            conexion1.rollback() 
            self.mostrar_mensaje("Error","critico",f"Error al guardar los datos: {e}")

    #CARGAR USUARIO
    def cargar_usuarios(self):
        """Función para cargar todos los usuarios en el ComboBox"""
        try:
            # Obtener todos los usuarios de la tabla cuenta_emisor
            cursor1.execute("SELECT usuario FROM cuenta_emisor;")
            usuarios = cursor1.fetchall()

            # Agregar usuarios al ComboBox
            self.ui.comboBoxAlta.clear()  #
            for usuario in usuarios:
                # Insertar cada usuario en el ComboBox con su ID como dato
                self.ui.comboBoxAlta.addItem(usuario[0])

        except psycopg2.Error as e:
            self.mostrar_mensaje("Error","critico",f"Error al cargar usuarios: {e}")

    #CARGAR USUARIO
    def cargar_datos_usuario(self):
        """Función para cargar los datos del usuario seleccionado en los QLineEdit"""
        usuario = self.ui.comboBoxAlta.currentText().strip()
        if usuario is None:
            return  
        
        try:
            sql="SELECT usuario, contrasena, cargo, rfc_emisor FROM cuenta_emisor WHERE usuario = %s;"
            cursor1.execute(sql, (usuario,))
            resultado = cursor1.fetchone()
            rfc_emisorl = resultado[3]

            cursor1.execute("SELECT nombre, apellido_paterno, apellido_materno FROM emisor WHERE rfc_emisor = %s;", (rfc_emisorl,))
            resultado1 = cursor1.fetchone()

            if resultado:
                usuario, contraseña, cargo , rfc_emisor = resultado
                nombre, apellido_paterno, apellido_materno = resultado1
                self.ui.RFCAlta.setText(rfc_emisor)
                self.ui.usuarioAlta.setText(usuario)
                self.ui.contraseAlta.setText(contraseña)
                self.ui.comboBox_Cargo.setCurrentText(cargo)
                self.ui.nombreAlta.setText(nombre)
                self.ui.apellidoPAlta.setText(apellido_paterno)
                self.ui.apellidoMAlta.setText(apellido_materno)

                self.usuarioaf = usuario
                self.rfcaf = rfc_emisor
     
        except psycopg2.Error as e:
            self.mostrar_mensaje("Error","critico",f"Error al cargar datos del usuario: {e}")
            
    #MODIFICAR DATOS USUARIOS
    def modificar_datos(self):
        """Función para guardar los cambios en la base de datos"""
        # Obtener el ID del usuario seleccionado y los valores de los QLineEdit
        rfc = self.ui.RFCAlta.text()
        usuario = self.ui.usuarioAlta.text()
        contraseña = self.ui.contraseAlta.text()
        nombre = self.ui.nombreAlta.text()
        apellido_paterno = self.ui.apellidoPAlta.text()
        apellido_materno = self.ui.apellidoMAlta.text()    
        cargo = self.ui.comboBox_Cargo.currentText()
        usuarioaf1 = self.usuarioaf
        
        if not rfc or not nombre or not apellido_materno or not apellido_materno or not usuario or not contraseña or not cargo:
            self.mostrar_mensaje("Error","critico","Campos no pueden estar vacíos")  
            return
        
        rfcaf1 = self.rfcaf
        try:
                cursor1.execute("""
                    SELECT COUNT(*) FROM cuenta_emisor WHERE usuario = %s;
                """, (usuario,))
                existe_usuario = cursor1.fetchone()[0]

                if existe_usuario is None:
                    self.mostrar_mensaje("Error","advertencia","El nuevo usuario no existe en cuenta_emisor.") 
                    return
                
                cursor1.execute("ALTER TABLE emisor_cuenta_emisor DISABLE TRIGGER ALL;")
                cursor1.execute("ALTER TABLE emisor DISABLE TRIGGER ALL;")
                cursor1.execute("ALTER TABLE cuenta_emisor DISABLE TRIGGER ALL;")
                
                cursor1.execute("""
                    UPDATE cuenta_emisor 
                    SET usuario = %s, contrasena = %s, cargo = %s, rfc_emisor = %s
                    WHERE usuario = %s;  -- Cambiar usuario en `cuenta_emisor`
                """, (usuario, contraseña, cargo, rfc, usuarioaf1))

                cursor1.execute("""
                    UPDATE emisor_cuenta_emisor
                    SET usuario = %s, rfc_emisor = %s
                    WHERE usuario = %s AND rfc_emisor = %s;  -- Cambiar usuario en la tabla intermedia
                """, (usuario, rfc, usuarioaf1, rfcaf1))

                cursor1.execute("""
                    UPDATE emisor 
                    SET rfc_emisor = %s, nombre = %s, apellido_paterno = %s, apellido_materno = %s WHERE rfc_emisor = %s;
                """, (rfc, nombre, apellido_paterno, apellido_materno, rfcaf1))

                cursor1.execute("ALTER TABLE emisor_cuenta_emisor ENABLE TRIGGER ALL;")
                cursor1.execute("ALTER TABLE emisor ENABLE TRIGGER ALL;")
                cursor1.execute("ALTER TABLE cuenta_emisor ENABLE TRIGGER ALL;")
                
                conexion1.commit()
                self.mostrar_mensaje("Exito","informacion","Los datos fueron modificados correctamente.") 
                self.actualizar_contenido()

        except psycopg2.Error as e:
            conexion1.rollback()
            print(f"Error al actualizar los datos: {e}")

    #CONFIRMAR ELIMINACION
    def confirmar_eliminacion(self):
        respuesta = self.mostrar_mensaje("Confirmar Eliminación","pregunta","¿Estás seguro de que deseas eliminar este usuario?") 

        if respuesta == QMessageBox.StandardButton.Yes:
            self.eliminar_usuario()
            self.ui.apellidoMAlta.clear()
            self.ui.apellidoPAlta.clear()
            self.ui.nombreAlta.clear()
            self.ui.RFCAlta.clear()
            self.ui.contraseAlta.clear()
            self.ui.usuarioAlta.clear()
        else:
            pass

    #ELIMINAR USUARIO
    def eliminar_usuario(self):
        usuario_a_eliminar = self.ui.usuarioAlta.text()

        try:
            cursor1.execute("""
                DELETE FROM emisor_cuenta_emisor 
                WHERE usuario = %s;
            """, (usuario_a_eliminar,))

            cursor1.execute("""
                DELETE FROM cuenta_emisor 
                WHERE usuario = %s;
            """, (usuario_a_eliminar,))

            cursor1.execute("""
                DELETE FROM emisor 
                WHERE rfc_emisor = (
                    SELECT rfc_emisor 
                    FROM emisor_cuenta_emisor 
                    WHERE usuario = %s
                );
            """, (usuario_a_eliminar,))

            conexion1.commit()

            self.mostrar_mensaje("Exito","informacion","Usuario eliminado exitosamente.") 
            self.actualizar_contenido()

        except psycopg2.Error as e:
            conexion1.rollback()  # Revertir cambios en caso de error
            QMessageBox.critical(self, "Error", f"Error al eliminar el usuario: {e}")

    #LIMPIAR DATOS DE USUARIO
    def actualizar_contenido(self):
        self.ui.comboBoxAlta.clear()

        self.cargar_usuarios()
        self.cargar_datos_usuario()  

    #CARGAR CARGO   
    def cargar_Cargo(self):
        self.ui.comboBox_Cargo.addItem("CONTADOR")
        self.ui.comboBox_Cargo.addItem("DIRECTOR")

######################################################## FACTURA ##################################################################################################
    
    #CARGAR PARA SELECCIONAR PADRE
    def cargar_seleecion_padre(self):
        try:
            cursor1.execute("SELECT rfc_padre from padre;")
            padres = cursor1.fetchall()

            self.ui.comboBox_SeleccionarPadre.clear()
            self.ui.comboBox_SeleccionarPadre.addItem("Seleccionar padre")
            for padre in padres:
                self.ui.comboBox_SeleccionarPadre.addItem(padre[0])
                self.ui.comboBox_SeleccionarPadre.setCurrentIndex(0)

        except psycopg2.Error:
            self.mostrar_mensaje("Error al seleccionar padre","critico","Error al seleccionar padre.")

    #MOSTRAR DATOS PADRE EN LA FACTURA
    def mostrar_datos_padre_factura(self):
        rfc_seleccionado = self.ui.comboBox_SeleccionarPadre.currentText()
        if rfc_seleccionado is None or rfc_seleccionado == "Seleccionar padre":
            self.ui.lineEdit_RFCpadreFactura.clear()
            self.ui.lineEdit_NombrePadreFact.clear()
            self.ui.lineEdit_ApellidoPpadreFact.clear()
            self.ui.lineEdit_ApellidoMpadreFact.clear()
            self.ui.lineEdit_DomicilioFiscalFact.clear()
            self.ui.lineEdit_RegimenFiscalFact.clear()
            self.ui.lineEdit_NombreAlumnoFactura.clear()
            self.ui.lineEdit_ApellidoMAlumFactura.clear()
            self.ui.lineEdit_ApellidoPAlumnoFactura.clear()
            self.ui.lineEdit_CURPFactura.clear()
            self.ui.lineEdit_NivelEducativo.clear()
            self.ui.lineEdit_ClavetrabajoFactura.clear()
            self.ui.textEdit_ConceptoFactura.clear()
            self.cargar_seleccion_alumno()
            return
        try:
           
           cursor1.execute("SELECT nombre, apellido_paterno, apellido_materno FROM padre WHERE rfc_padre = %s;",(rfc_seleccionado,))
           padre = cursor1.fetchone()
           print(padre)
           cursor1.execute("SELECT clave_regimen FROM padre_regimen_fiscal WHERE rfc_padre = %s;", (rfc_seleccionado,))
           padre_regimen = cursor1.fetchone()
           print(padre_regimen)
           cursor1.execute("SELECT codigo_postal FROM domicilio_padre WHERE rfc_padre = %s;", (rfc_seleccionado,))
           padre_domicilio = cursor1.fetchone()
           
           cursor1.execute("select nombre_regimen from regimen_fiscal where clave_regimen = %s;",(padre_regimen))
           regimen_padre = cursor1.fetchone()
           
           if padre:
               nombre, apellido_paterno, apellido_materno = padre
               codigo_postal = padre_domicilio[0]
               nombre_regimen = regimen_padre[0]
               print(nombre_regimen)
               self.ui.lineEdit_RegimenFiscalFact.setText((nombre_regimen))
               self.ui.lineEdit_RFCpadreFactura.setText(rfc_seleccionado)
               self.ui.lineEdit_NombrePadreFact.setText(nombre)
               self.ui.lineEdit_ApellidoPpadreFact.setText(apellido_paterno)
               self.ui.lineEdit_ApellidoMpadreFact.setText(apellido_materno)
               self.ui.lineEdit_DomicilioFiscalFact.setText(str(codigo_postal))
               #Borra los datos del alumno cuando se muestren datos del padre
               self.ui.lineEdit_NombreAlumnoFactura.clear()
               self.ui.lineEdit_ApellidoMAlumFactura.clear()
               self.ui.lineEdit_ApellidoPAlumnoFactura.clear()
               self.ui.lineEdit_CURPFactura.clear()
               self.ui.lineEdit_NivelEducativo.clear()
               self.ui.lineEdit_ClavetrabajoFactura.clear()
               self.ui.textEdit_ConceptoFactura.clear()
               self.actualizar_contenido_alumnoFact()
               self.actualizar_cfdi()
               
        except psycopg2.Error:
            self.mostrar_mensaje("Error","Critico","Error al mostrar datos del padre.")

    #ACTUALIZAR CONTENIDO ALUMNO FACTURA
    def actualizar_contenido_alumnoFact(self):
        self.cargar_seleccion_alumno()

    #CARGAR SELECCION ALUMNO
    def cargar_seleccion_alumno(self):
        rfc_padre1 = self.ui.comboBox_SeleccionarPadre.currentText()
        try:
            cursor1.execute("select curp from alumno_padre where rfc_padre = %s;",(rfc_padre1,))
            alumnos = cursor1.fetchall()

            self.ui.comboBox_SeleccionarAlumno.clear()
            self.ui.comboBox_SeleccionarAlumno.addItem("Seleccionar alumno")
            for alumno in alumnos:
                alumno1 = alumno[0]
                self.ui.comboBox_SeleccionarAlumno.addItem(alumno1)
                self.ui.comboBox_SeleccionarAlumno.setCurrentIndex(0)
        
        except psycopg2.Error:
            self.mostrar_mensaje("Error","critico","Error al cargar seleccion de alumnos.")
            return

    #CARGAR FORMA PAGO
    def cargar_forma_pago(self):  
        try:
            cursor1.execute("select forma from forma_pago;")
            formas_pago = cursor1.fetchall()
            self.ui.comboBox_FormaPago.clear()
            for forma_pago in formas_pago:
                forma1 = forma_pago[0]
                self.ui.comboBox_FormaPago.addItem(forma1)
        except psycopg2.Error:
            self.mostrar_mensaje("Error","critico","Error al cargar la forma de pago")
            return

    #CARGA CFDI
    def cargar_cfdi(self):
        rfc_seleccionado = self.ui.comboBox_SeleccionarPadre.currentText()
        try:
            cursor1.execute("select clave_regimen from padre_regimen_fiscal where rfc_padre = %s;",(rfc_seleccionado,))
            clave_regimen1 = cursor1.fetchone()
            print(clave_regimen1)

            cursor1.execute("select clave_regimen from regimen_fiscal where clave_regimen = %s;",(clave_regimen1,))
            clave_regimen2 = cursor1.fetchone()

            cursor1.execute("select clave_regimen from regimen_fiscal where nombre_regimen = %s;",("simplificado de confianza",))
            regimen = cursor1.fetchone()
            print(regimen)

            if clave_regimen2 == regimen:
                self.ui.comboBox_CFDI.clear()
                self.ui.comboBox_CFDI.addItem("GASTOS GENERALES")
            else:
                
                self.ui.comboBox_CFDI.addItem("TRANSPORTE")
                self.ui.comboBox_CFDI.addItem("COLEGIATURAS")
        except psycopg2.Error:
            self.mostrar_mensaje("Error","critico","Error, no fue posible cargar los CFDI,")
            return
  
   #ACTUALIZAR CFDI     
    def actualizar_cfdi(self):
        self.ui.comboBox_CFDI.clear()
        self.cargar_cfdi()
        return

    #MOSTRAR DATOS ALUMNO FACTURA
    def mostrar_datos_alumnoFact(self):
        curpAlumno = self.ui.comboBox_SeleccionarAlumno.currentText()
        rfc_padre = self.ui.lineEdit_RFCpadreFactura.text()
        if rfc_padre is None:
            self.mostrar_mensaje("Error","advertencia","Padre no encontrado")
            return
        if curpAlumno is None or curpAlumno == "Seleccionar alumno":
            self.ui.lineEdit_NombreAlumnoFactura.clear()
            self.ui.lineEdit_ApellidoMAlumFactura.clear()
            self.ui.lineEdit_ApellidoPAlumnoFactura.clear()
            self.ui.lineEdit_CURPFactura.clear()
            self.ui.lineEdit_NivelEducativo.clear()
            self.ui.lineEdit_ClavetrabajoFactura.clear()
            self.ui.textEdit_ConceptoFactura.clear()
            return
        try: 
            cursor1.execute("SELECT curp, nombre, apellido_paterno, apellido_materno FROM alumno where curp = %s;",(curpAlumno,))
            alumnoFact = cursor1.fetchone()
            print(alumnoFact)
            cursor1.execute("select id_nivel_escolar from alumno_nivel_escolar where curp = %s;",(curpAlumno,))
            id_nivel_escolar1 = cursor1.fetchone()
            print(id_nivel_escolar1)
            
            cursor1.execute("select nivel from costo_nivel_escolar where id_nivel_escolar = %s;",(id_nivel_escolar1))
            nivel_escolar = cursor1.fetchone()
            print(nivel_escolar)
            if alumnoFact:
                curp, nombre, apellido_Paterno, apellido_Materno = alumnoFact
                id_nivel_escolar = id_nivel_escolar1[0]
                nivel_esc = nivel_escolar[0]
                
                self.ui.lineEdit_NombreAlumnoFactura.setText(nombre)
                self.ui.lineEdit_CURPFactura.setText(curp)
                self.ui.lineEdit_ApellidoMAlumFactura.setText(apellido_Materno)
                self.ui.lineEdit_ApellidoPAlumnoFactura.setText(apellido_Paterno)
                self.ui.lineEdit_NivelEducativo.setText(nivel_esc)
                self.ui.lineEdit_ClavetrabajoFactura.setText(id_nivel_escolar)

        except psycopg2.Error:
            self.mostrar_mensaje("Error","critico","Error al mostrar datos del alumno.")

    # CREAR PDF FACTURA
    def datos_factura(self):
        try:
            from fpdf import FPDF
            from PyPDF2 import PdfReader, PdfWriter, PageObject

            # Clase personalizada para PDF
            class PDF(FPDF):
                def header(self):
                    pass

            # Crear PDF temporal
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            pdf.set_xy(50, 50)
            pdf.cell(200, 10, txt="hola mundo", ln=True)
            pdf.ln(10)

            # Guardar PDF temporal
            datos_path = "Factura_Vacia.pdf"
            pdf.output(datos_path)

            # Leer PDFs
            factura_sin_sellos = PdfReader("Factura_Sin_SELLOS.pdf")
            datos_pdf = PdfReader(datos_path)
            writer = PdfWriter()

            # Combinar páginas
            for pagina in datos_pdf.pages:
                pagina_factura = PageObject.create_blank_page(
                    width=factura_sin_sellos.pages.mediabox.width,
                    height=factura_sin_sellos.pages.mediabox.height,
                )
                pagina_factura.merge_page(factura_sin_sellos.pages[0])
                pagina_factura.merge_page(pagina)
                writer.add_page(pagina_factura)

            # Guardar archivo final
            final_path = "Factura_Completa2.pdf"
            with open(final_path, "wb") as f:
                writer.write(f)

            print(f"Factura completa generada: {final_path}")

        except FileNotFoundError as e:
            print(f"Error de archivo: {e}")
        except Exception as e:
            print(f"Error al procesar la factura: {e}")

################################################################### FIN ######################################################################################################
if __name__ == "__main__":#

    app = QApplication(sys.argv)
    window = Menus()  # Crear una instancia de la clase Menu
    window.setWindowTitle("FACTURTEC")
    window.show()
    sys.exit(app.exec())
