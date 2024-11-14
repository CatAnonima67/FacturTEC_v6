import sys
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox
from login_view import Ui_MainWindow
import datetime
import psycopg2

from conexionDB import cursor1  
class logins(QMainWindow):
    def __init__(self):
        super(logins, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.is_logged = False
        self.FechaIncioSession = None
        self.ui.loginButton.clicked.connect(self.inicios)
        
      
    def inicios(self):
        try:
            password = self.ui.passwordInput.text()
            sql = "select * from cuenta_emisor where usuario = %s"
            self.user = self.ui.userImput.text()
            print(self.user)
            cursor1.execute(sql, (self.user,))
            resultado = cursor1.fetchone()

            if resultado is None:
                QMessageBox.warning(self, "Error", 
                                "El usuario no existe",
                                QMessageBox.StandardButton.Close, 
                                QMessageBox.StandardButton.Close)
            else:
         
                if resultado[1] == password:
                    QMessageBox.information(self, "Login", 
                                        "Login Correcto", 
                                        QMessageBox.StandardButton.Ok, 
                                        QMessageBox.StandardButton.Ok)
                    
                    self.is_logged = True
                    self.FechaIncioSession = datetime.datetime.now().replace(microsecond=0)
                    self.cargo = resultado[2]
                    print(self.FechaIncioSession)
                    self.close()
                    self.openMainWindow()
                else:
                    QMessageBox.warning(self, "Error", 
                                    "Credenciales incorrectas",
                                    QMessageBox.StandardButton.Close, 
                                    QMessageBox.StandardButton.Close)
        except psycopg2.Error:
            QMessageBox.critical(self, "Error", 
                             "Error en la conexión con la base de datos",
                             QMessageBox.StandardButton.Close, 
                             QMessageBox.StandardButton.Close)
                

    def openMainWindow(self):
        from principal import Menus
        self.main_window = Menus(user=self.user, fecha_inicio=self.FechaIncioSession, cargo=self.cargo)
        self.main_window.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ventana = logins()
    ventana.show()
    sys.exit(app.exec())
