import sys
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox
from bienvenidaSistema_view import Ui_MainWindow
from login_main import login

class Bienvenida(QMainWindow):
    
    def __init__(self):
        super(Bienvenida, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.pushButton_IniciarApp.clicked.connect(self.openLoginWindow)
        self.ui.pushButton_SalirBienvenida.clicked.connect(self.closeApp)

    def openLoginWindow(self):
        
        self.main_window = login()
        self.main_window.show()
        self.close()  

    def closeApp(self):

        QApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ventana = Bienvenida()
    ventana.show()
    sys.exit(app.exec())


