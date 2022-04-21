from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QLabel
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import ui
import sys
import serial
import serial.tools.list_ports
import warnings
import time
from PyQt5.QtCore import pyqtSignal, QThread, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtGui import QIntValidator
from struct import *
import random


ports = [
    p.device
    for p in serial.tools.list_ports.comports()
    if 'USB' in p.description
]

# if not ports:
    # raise IOError("There is no device exist on serial port!")

command_list = ["NOP", "INIT", "GET_ADC_1", "GET_ADC_2", "PWM_C","GET_CURRENT", "SET_CURRENT", "LOOP_BACK"]

plots_command = []
plots_command_names = []

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
            cmd, arg = unpack("<Bh",line)
            time.sleep(0.01)
            self.intReady.emit(cmd,arg)
        self.finished.emit()


class ExampleApp(QtWidgets.QMainWindow, ui.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self) 
        self.comboBox_port.addItems(ports)
        self.thread = None
        self.worker = None
        self.comboBox.addItems(command_list)
        self.comboBox_2.addItems(command_list)
        self.intValidator = QIntValidator(0,255)
        self.lineEdit.setValidator (self.intValidator)
        self.timeValidator = QIntValidator(0,1000)
        self.lineEdit_2.setValidator (self.timeValidator)
        self.start_btn.clicked.connect(self.start)
        self.n_data = 100
        self.xdata = [[]] * 5#list(range(self.n_data))
        self.ydata = [[]] * 5#[0 for i in range(self.n_data)]
        self.canva_widget.setBackground('w')
        self.canva_widget.addLegend()
        self.pen = pg.mkPen(color=(255, 0, 0))
        self.plots = []
        # self.plot = self.canva_widget.plot(self.xdata,self.ydata, pen = self.pen)
        # self.plot = self.canva_widget.plot(self.xdata,self.ydata, pen = pg.mkPen(color=(255, 255, 0)))

        self.show()

    def addplot(self):
        plots_command.append(self.comboBox_2.currentIndex())
        index = len(plots_command)-1
        plots_command_names.append(command_list[self.comboBox_2.currentIndex()])
        self.xdata[index]=(list(range(self.n_data)))
        self.ydata[index]=([0 for i in range(self.n_data)])
        self.plots.append(self.canva_widget.plot(self.xdata[index],self.ydata[index], pen=(index,5), name = command_list[self.comboBox_2.currentIndex()]))
        self.comboBox_plot.addItem(command_list[self.comboBox_2.currentIndex()])
        
    def removeplot(self):
        name = self.comboBox_plot.currentText()
        index = plots_command_names.index(name)
        plots_command.pop(index)
        plots_command_names.pop(index)
        self.xdata[index]=(list(range(self.n_data)))
        self.ydata[index]=([0 for i in range(self.n_data)])
        self.plots[index].clear()
        self.canva_widget.removeItem(self.plots[index])
        self.plots.pop(index)
        self.comboBox_plot.removeItem(self.comboBox_plot.currentIndex())
        print("remove")

    def Conect_clicked(self):
        port = ports[self.comboBox_port.currentIndex()]
        self.ser = serial.Serial(ports[0],self.baudrate_edit.text())            
        self.worker = Worker(self.ser)  
        self.thread = QThread()  
        self.worker.moveToThread(self.thread)  

        self.thread.started.connect(self.worker.work) 

        self.worker.intReady.connect(self.onIntReady)
        self.start_btn.clicked.connect(self.start)  
        self.worker.finished.connect(self.loop_finished)       
        self.worker.finished.connect(self.thread.quit)         
        self.worker.finished.connect(self.worker.deleteLater)  
        self.thread.finished.connect(self.thread.deleteLater)  
        self.thread.start()
        print("conected");

    def onIntReady(self, cmd,arg):
        for commands in plots_command:
            if(cmd == commands):
                self.update_plot(arg,cmd)
                return
        if(cmd<=self.comboBox.count()):
            self.textEdit.append(">>" + command_list[cmd] + " " + str(arg) )
        else:
            self.textEdit.append(">> malformed " + str(cmd) + " " +str(arg) )
        print(cmd,arg)
    
    def loop_finished(self):
        print('Loop Finished')

    def stop_loop(self):
        self.worker.working = False

    def Send(self):
        cmd = self.comboBox.currentIndex()
        arg = int(self.lineEdit.text())
        buf = pack("<BH",cmd,arg)
        try:
            self.ser.write(buf)
        except:
            print("Connect to com port")
        
        self.textEdit.append("<<" + command_list[cmd] + " " +str(arg))
    def update_plot(self,arg,cmd):
        index = plots_command.index(cmd)
        ydata = self.ydata[index]
        ydata = ydata[1:] + [arg]
        self.ydata[index] = ydata
        self.plots[index].setData(self.xdata[index],self.ydata[index])

    def send_to_plot(self):
        for comand in plots_command:
            cmd = comand
            arg = int(0)
            buf = pack("<BH",cmd,arg)
            try:
                self.ser.write(buf)
            except:
                print("Connect to com port")
                self.timer.stop()
    def changing(self):
        cmd = 4
        arg = int(self.horizontalSlider.value())
        buf = pack("<BH",cmd,arg)
        try:
            self.ser.write(buf)
        except:
            print("Connect to com port")

        # self.textEdit.append("<<" + command_list[cmd] + " " +str(arg) )

    def start(self):
        print("Start")
        # self.ydata = [0 for i in range(self.n_data)]
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