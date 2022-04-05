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

ports = [
    p.device
    for p in serial.tools.list_ports.comports()
    if 'USB' in p.description
]

if not ports:
    raise IOError("There is no device exist on serial port!")

command_list = ["NOP", "INIT", "SET_MODE"]


class Worker(QObject):
    finished = pyqtSignal()
    intReady = pyqtSignal(int,int,int)

    @pyqtSlot()
    def __init__(self, ser):
        super(Worker, self).__init__()
        self.working = True
        self.ser = ser

    def work(self):
        while self.working:
            line = self.ser.read(3)
            cmd, arg, nop = unpack("<BBB",line)
            time.sleep(0.1)
            self.intReady.emit(cmd,arg,nop)
        self.finished.emit()


class ExampleApp(QtWidgets.QMainWindow, ui.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self) 
        self.port_label.setText(ports[0])
        self.thread = None
        self.worker = None
        self.comboBox.addItems(command_list)
        self.intValidator = QIntValidator(0,255)
        self.lineEdit.setValidator (self.intValidator)


    def Conect_clicked(self):
        self.ser = serial.Serial(ports[0],self.baudrate_edit.text())            
        self.worker = Worker(self.ser)   # a new worker to perform those tasks
        self.thread = QThread()  # a new thread to run our background tasks in
        self.worker.moveToThread(self.thread)  # move the worker into the thread, do this first before connecting the signals

        self.thread.started.connect(self.worker.work) # begin our worker object's loop when the thread starts running

        self.worker.intReady.connect(self.onIntReady)

        # self.pushButton_2.clicked.connect(self.stop_loop)      # stop the loop on the stop button click

        self.worker.finished.connect(self.loop_finished)       # do something in the gui when the worker loop ends
        self.worker.finished.connect(self.thread.quit)         # tell the thread it's time to stop running
        self.worker.finished.connect(self.worker.deleteLater)  # have worker mark itself for deletion
        self.thread.finished.connect(self.thread.deleteLater)  # have thread mark itself for deletion

        self.thread.start()
        print("conected");
    def onIntReady(self, cmd,arg,nop):
        if(cmd<=self.comboBox.count()):
            self.textEdit.append(">>" + command_list[cmd] + " " + str(arg) + " " + str(nop))
        else:
            self.textEdit.append(">> malformed " + str(cmd) + " " +str(arg) + " " + str(nop))
        print(cmd,arg,nop)
    def loop_finished(self):
        print('Loop Finished')
    def stop_loop(self):
        self.worker.working = False
    def Send(self):
        cmd = self.comboBox.currentIndex()
        arg = int(self.lineEdit.text())
        nop = 0
        buf = pack("<BBB",cmd,arg,nop)
        print(arg)
        self.ser.write(buf)
        print(buf)
        self.textEdit.append("<<" + command_list[cmd] + " " +str(arg) + " " + str(nop))
if __name__ == '__main__':
    print(ports)
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = ExampleApp()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    sys.exit(app.exec_())  # и запускаем приложение