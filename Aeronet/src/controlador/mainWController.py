'''
Created on 28 ene. 2020

@author: Jesus Brezmes Gil-Albarellos
'''
import pymysql
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMessageBox

#Modificaciones: quitar src
import src.modelo.globales as g
import src.vista.mainWindow as v
import src.modelo.consultasBBDD as c
from src.controlador.graphController import graphController
import src.modelo.phStationObject as objecto

class mainWController:
    
    def __init__(self):
        super().__init__()
        self.fechaMin = ""
        self.fechaMax = ""
        
    def start(self):
        self.main_controller = self
        self.db = pymysql.connect(g.database_host, g.user, g.password, g.database_name)
        self.cursor = self.db.cursor()
        app = QApplication(sys.argv)
        datosDistinct = self.getDatosPhStation("")
        self.datosCompletos = self.getDatosCompletos("", "")
        fechaMin = self.getFechaMin("")
        fechaMax = self.getFechaMax("")
        self.screen = v.mainWindow(self.main_controller)
        self.screen.plotUsoPh(datosDistinct, self.datosCompletos, fechaMin, fechaMax, "")
        self.screen.setDatosTabla(datosDistinct)
        self.screen.show()
        sys.exit(app.exec_())
    
    #Devuelve una lista de distict fotometros y estaciones   
    def getDatosPhStation(self, filtro):
        if (filtro == ""):
            datos=c.consultaBBDD.getPhStation(self, self.cursor)
        else:
            datos=c.consultaBBDD.getPhStation101(self, self.cursor, filtro)
        return datos
    
    #Devuelve una lista de objetos con el n de fotometro, la estación, el conjunto de fechas que estáactivo y con los eprom type y subtype
    def getDatosCompletos(self, filtro, cloudLevel):
        if (filtro == ""):
            datos=c.consultaBBDD.getPhStationDates(self, self.cursor)
        else:
            datos=c.consultaBBDD.getPhStationDates21(self, self.cursor, filtro)
        if (cloudLevel == "1.5"):
            datosCompletos = self.toPhStationObjectCloudL(datos, cloudLevel)
        else:
            datosCompletos = self.toPhStationObject(datos)
        return datosCompletos
    
    #Devuelve la fecha minima de uso de los fotometros, para establecer limite inferior eje x de la grafica
    def getFechaMin(self, filtro):
        if (filtro == ""):
            return c.consultaBBDD.minFecha(self, self.cursor)
        else:
            return c.consultaBBDD.minFechaFiltro(self, self.cursor, filtro)
        
    #Devuelve la fecha maxima de uso de los fotometros, para establecer limite superior eje x de la grafica
    def getFechaMax(self, filtro):
        if (filtro == ""):    
            return c.consultaBBDD.maxFecha(self, self.cursor)
        else:
            return c.consultaBBDD.maxFechaFiltro(self, self.cursor, filtro)
    
    #Devuelve la fecha minima con datos y filtro cloud level 1.0 o 1.5
    def getMinFechaCloudL(self, ph, minFecha, maxFecha, cloudLevel):
        if (cloudLevel == "1.0"):
            return c.consultaBBDD.minFechaFiltroL1(self, self.cursor, ph, minFecha, maxFecha)
        elif (cloudLevel == "1.5"):
            return c.consultaBBDD.minFechaFiltroL15(self, self.cursor, ph, minFecha, maxFecha)
        
    #Devuelve la fecha maxima con datos y filtro cloud level 1.0 o 1.5
    def getMaxFechaCloudL(self, ph, minFecha, maxFecha, cloudLevel):
        if (cloudLevel == "1.0"):
            return c.consultaBBDD.maxFechaFiltroL1(self, self.cursor, ph, minFecha, maxFecha)
        elif (cloudLevel == "1.5"):
            return c.consultaBBDD.maxFechaFiltroL15(self, self.cursor, ph, minFecha, maxFecha)
    
    #Determina el filtro    
    def tipoFiltro(self, tipo, station, ph):
        if (tipo == "Standard"):
            filtro = g.standard
        elif (tipo == "Digital Extended"):
            filtro = g.digitalExtended
        elif (tipo == "Triple"):
            filtro = g.triple
        elif (tipo == "Dualpolar"):
            filtro = g.dualpolar
        else:
            filtro = ""
        if (ph!=""):
            aux = ph+"%"
            if (filtro!=""):   
                filtro = filtro + " && "+g.device % aux
            else:
                filtro = g.device % aux
        if (station!=""):
            aux = station+"%"
            if (filtro!=""):
                filtro = filtro + " && "+g.station % aux
            else:
                filtro = g.station % aux                
        return filtro
    
    #Recupera los datos de los fotometros con filtro eprom_type/subtype, device, site   
    def filtroEpromPhSite(self, tipo, station, ph, cloudLevel):
        filtro = self.tipoFiltro(tipo, station, ph)
        datosDistinct = self.getDatosPhStation(filtro)
        self.screen.limpiaPlot()
        if (any(map(len, datosDistinct))):
            if (cloudLevel == "1.5"):
                datosCompletos = self.getDatosCompletos(filtro, cloudLevel)
                fechaMin = self.fechaMin
                fechaMax = self.fechaMax
            else:
                datosCompletos = self.getDatosCompletos(filtro, "")
                fechaMin = self.getFechaMin(filtro)
                fechaMax = self.getFechaMax(filtro)
                cloudLevel = ""
            if (datosCompletos):    
                self.screen.plotUsoPh(datosDistinct, datosCompletos, fechaMin, fechaMax, cloudLevel)
            else:
                self.screen.limpiaTabla()
                self.screen.reiniciaCloudLevel()
                #self.mensajeNoDatosCloudL15(tipo, ph, station)    
        else:
            self.screen.limpiaTabla()
            #self.mensajeNoDatos()
    
    #Método para tranformar la lista de fotometros consultada para su tratamiento
    def toPhStationObject(self, data):
        indices =[]
        datosCompletos=[]
        contador=0
        for row in data:
            fechas = []
            aux = str(row[0])+" "+ str(row[1])
            if aux not in indices:
                indices.append(aux)
                o = objecto.phStationObject(aux, row[4], row[5])
                fechas.append(row[2])
                fechas.append(row[3])
                o.setDateOfUse(fechas)
                datosCompletos.append(o)
                contador+=1
            else:
                o=datosCompletos[contador-1]
                datosCompletos.remove(o)
                fechas.append(row[2])
                fechas.append(row[3])
                o.setDateOfUse(fechas)
                datosCompletos.append(o)
        return datosCompletos
    
    #Método para tranformar la lista de fotometros consultada para su tratamiento
    def toPhStationObjectCloudL(self, data, cloudLevel):
        indices =[]
        datosCompletos=[]
        contador=0
        for row in data:
            fechas = []
            #Comprobar antes de insertar fechas, si son datos con cloud level 1.0 o 1.5, sino no se insertan
            fMin = self.getMinFechaCloudL(str(row[0]), row[2], row[3], cloudLevel)
            fMax = self.getMaxFechaCloudL(str(row[0]), row[2], row[3], cloudLevel)
            if ((fMin != "") & (fMax != "")):
                #Comprobaciones para obtener Fmin y Fmax, para los limites del eje x de la grafica 
                if (self.fechaMin == ""):
                    self.fechaMin = fMin
                if (self.fechaMin > fMin):
                    self.fechaMin = fMin
                if (self.fechaMax == ""):
                    self.fechaMax = fMax
                if (self.fechaMax < fMax):
                    self.fechaMax = fMax
                aux = str(row[0])+" "+ str(row[1])
                if aux not in indices:
                    indices.append(aux)
                    o = objecto.phStationObject(aux, row[4], row[5])
                    fechas.append(fMin)
                    fechas.append(fMax)
                    o.setDateOfUse(fechas)
                    datosCompletos.append(o)
                    contador+=1
                else:
                    o=datosCompletos[contador-1]
                    datosCompletos.remove(o)
                    fechas.append(fMin)
                    fechas.append(fMax)
                    o.setDateOfUse(fechas)
                    datosCompletos.append(o)
        return datosCompletos
    
    #Invoca el graphController, el cual se encarga de gestionar la respectiva graphWindow
    def graphWindow(self, phStation, fechaMin, fechaMax):
        fot = phStation.split()
        nFotometro = fot[0]
        station = fot[1]
        self.graphController = graphController()
        self.graphController.start(nFotometro, station, fechaMin, fechaMax)
    
    #Mensaje no hay datos   
    def mensajeNoDatosCloudL15(self, tipo, ph, station):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("No hay datos AOD(1.5) para la búsqueda:\n"+ph+" "+station+"\ndel tipo:\n"+tipo)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
        
    #Mensaje no hay datos   
    def mensajeNoDatos(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("No hay datos disponibles que concuerden con este filtro")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
    
    #Terminar la ejecucion    
    def salir(self):
        self.db.close()
        sys.exit(1)
        
