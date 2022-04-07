from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QLabel
import ui
import sys
import serial
import serial.tools.list_ports
import warnings
import time
from PyQt5.QtCore import pyqtSignal, QThread, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtGui import QIntValidator
from struct import *
from canva import MplCanvas
import random

ports = [
    p.device
    for p in serial.tools.list_ports.comports()
    if 'USB' in p.description
]

if not ports:
    raise IOError("There is no device exist on serial port!")

command_list = ["NOP", "INIT", "GET_ADC_1", "GET_ADC_2", "PWM_C","GET_CURRENT"]


class Worker(QObject):
    finished = pyqtSignal()
    intReady = pyqtSignal(int,int)

    @pyqtSlot()
    def __init__(self, ser):
        super(Worker, self).__init__()
        self.working = True
        self.ser = ser

    def work(self):
        while self.working:
            line = self.ser.read(3)
            cmd, arg = unpack("<BH",line)
            time.sleep(0.1)
            self.intReady.emit(cmd,arg)
        self.finished.emit()


class ExampleApp(QtWidgets.QMainWindow, ui.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self) 
        self.port_label.setText(ports[0])
        self.thread = None
        self.worker = None
        self.comboBox.addItems(command_list)
        self.comboBox_2.addItems(command_list)
        self.intValidator = QIntValidator(0,255)
        self.lineEdit.setValidator (self.intValidator)
        self.timeValidator = QIntValidator(0,1000)
        self.lineEdit_2.setValidator (self.timeValidator)
        self.start_btn.clicked.connect(self.start)
        self.canvas = MplCanvas(self.canva_widget, width=4, height=2, dpi=100)

        self.n_data = 50
        self.xdata = list(range(self.n_data))
        self.ydata = [0 for i in range(self.n_data)]
        # self.update_plot()

        self.show()



    def Conect_clicked(self):
        self.ser = serial.Serial(ports[0],self.baudrate_edit.text())            
        self.worker = Worker(self.ser)  
        self.thread = QThread()  
        self.worker.moveToThread(self.thread)  

        self.thread.started.connect(self.worker.work) 

        self.worker.intReady.connect(self.onIntReady)
        self.start_btn.clicked.connect(self.start)
        # self.pushButton_2.clicked.connect(self.stop_loop)      
        self.worker.finished.connect(self.loop_finished)       
        self.worker.finished.connect(self.thread.quit)         
        self.worker.finished.connect(self.worker.deleteLater)  
        self.thread.finished.connect(self.thread.deleteLater)  

        self.thread.start()
        print("conected");
    def onIntReady(self, cmd,arg):
        if(cmd<=self.comboBox.count()):
            self.textEdit.append(">>" + command_list[cmd] + " " + str(arg) )
        else:
            self.textEdit.append(">> malformed " + str(cmd) + " " +str(arg) )
        if(cmd == self.comboBox_2.currentIndex()):
            self.update_plot(arg)
        print(cmd,arg)
    def loop_finished(self):
        print('Loop Finished')
    def stop_loop(self):
        self.worker.working = False
    def Send(self):
        cmd = self.comboBox.currentIndex()
        arg = int(self.lineEdit.text())
        buf = pack("<BH",cmd,arg)
        print(arg)
        self.ser.write(buf)
        print(buf)
        self.textEdit.append("<<" + command_list[cmd] + " " +str(arg))
    def update_plot(self,arg):
        print("update")
        self.ydata = self.ydata[1:] + [arg]
        self.canvas.axes.cla()  # Clear the canvas.
        self.canvas.axes.plot(self.xdata, self.ydata, 'ro-')

        self.canvas.draw()
    def send_to_plot(self):
        cmd = self.comboBox_2.currentIndex()
        arg = int(self.lineEdit.text())
        buf = pack("<BH",cmd,arg)
        print(arg)
        self.ser.write(buf)
        print(buf)
        self.textEdit.append("<<" + command_list[cmd] + " " +str(arg) )

    def start(self):
        print("Start")
        self.ydata = [0 for i in range(self.n_data)]
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.send_to_plot)
        self.timer.start()
        self.start_btn.clicked.disconnect(self.start)
        self.start_btn.clicked.connect(self.stop)
        self.start_btn.setText("Stop")
    def stop(self):
        print("stop")
        self.timer.stop()
        self.start_btn.clicked.disconnect(self.stop)
        self.start_btn.clicked.connect(self.start)
        self.start_btn.setText("Start")
if __name__ == '__main__':
    print(ports)
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = ExampleApp()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    sys.exit(app.exec_())  # и запускаем приложение