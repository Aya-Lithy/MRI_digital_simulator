
from PyQt5 import QtCore, QtGui, QtWidgets
import copy
from PyQt5.QtWidgets import QInputDialog,QGraphicsView, QFileDialog ,QApplication, QProgressBar , QComboBox , QMessageBox, QAction, QLineEdit
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import pyqtSlot
from Digital_phantom2 import Ui_MainWindow
import sys
import time
import math
import cv2
import pyqtgraph as pg
import numpy as np
from PIL.ImageQt import ImageQt
from PIL import Image, ImageEnhance
import PIL
from qimage2ndarray import gray2qimage
from imageio import imsave, imread
from shapeloggin import phantom 
from matplotlib import pyplot as plt
import cythonfile
# cythonfile.SpinEchoForLoops , cythonfile.SSFPForLoops, cythonfile.GREForLoops


class PhotoViewer(QtWidgets.QGraphicsView):
    photoClicked = QtCore.pyqtSignal(QtCore.QPoint)

    def __init__(self, parent):
        super(PhotoViewer, self).__init__(parent)
        self._zoom = 0
        self._empty = True
        self._scene = QtWidgets.QGraphicsScene(self)
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setFixedSize(350,350)
        self.wheelEvent = self.zoom
        #self.setSceneRect(0, 0, 400, 400)
        self.wheelEvent = self.zoom
        #self.fitInView(0,0, 400, 400, QtCore.Qt.KeepAspectRatio)

        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def hasPhoto(self):
        return not self._empty

    def fitInVieww(self, scale=True):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                viewrect = self.viewport().rect()
                print (viewrect)
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                print(factor)
                self.scale(factor, factor)
            self._zoom = 0

    def setPhoto(self, pixmap):
        self._zoom = 0
        if pixmap :
            self._empty = False
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
            
        else:
            self._empty = True
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self._photo.setPixmap(QPixmap())
        self.fitInVieww()

    def zoom(self, event):
        if self.hasPhoto():
            print (event.angleDelta().y())
            if event.angleDelta().y() > 0:
                factor = 1.25
                self._zoom += 1
            else:
                factor = 0.8
                self._zoom -= 1
            if self._zoom > 0:
                self.scale(factor, factor)
            elif self._zoom == 0:
                self.fitInVieww()
                print('hi')
            else:
                self._zoom = 0



m=0
class ApplicationWindow (QtWidgets.QMainWindow):
    @pyqtSlot()        
    def __init__(self):
        self.count=0
        self.count1=0
        self.n=0
        
        super(ApplicationWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.browse.clicked.connect (self.browse)
        self.ui.label.mousePressEvent =self.getpos
        self.ui.PhantomShape.currentTextChanged.connect(self.shape)
        self.ui.Preb.currentTextChanged.connect(self.preb)
        self.ui.aquise.currentTextChanged.connect(self.acquisition)
        self.ui.Zoom.currentTextChanged.connect(self.zoomComBox)
        #self.ui.maxErnstAngl.clicked.connect (self.maxErnestAngleCalculated)
        self.ui.PhantomSize.currentTextChanged.connect(self.phantom_size)
        self.ui.createPhantom.clicked.connect (self.create)
        self.ui.ernstAngle.clicked.connect (self.drawErnstAngle)
        self.ui.start.clicked.connect (self.Start)
        #self.ui.horizontalSlider.valueChanged.connect(self.slider)
        self.plotWindow = self.ui.T1
        self.plotWindow2 = self.ui.T2
        self.Acquisition = 0
        self.Prepration = 0
        self.viewer = PhotoViewer(self.ui.graphicsView_Image)
        self.viewer1 = PhotoViewer(self.ui.graphicsView_Phantom)
        self.ui.Artifacts.currentTextChanged.connect(self.ArtifactFun)
        self.AliasingFactor = 2
        self.improperSampling = 0

    
    def ArtifactFun(self,text):
        if text =="Normal":
            self.AliasingFactor=2
            self.improperSampling = 0
        
        elif text=="Aliasing": 
            self.AliasingFactor=3
            self.improperSampling = 0
            
        elif text=="ImproperSampling":
            self.improperSampling = 1
            self.AliasingFactor=2



        
    

    def browse(self):
        fileName,_Filter = QtWidgets.QFileDialog.getOpenFileName(None, "Select phantom","","self.data Files(*.dat)")
        if fileName:
            self.data=np.load(fileName)
            self.size=len(self.data)
            self.scale=np.asarray(self.data,dtype=np.uint8)
            image=Image.fromarray(self.scale)
            #print (self.scale)
            self.img= ImageQt(image)
            self.img.save("2.png")

            self.viewer.setPhoto(QPixmap.fromImage(self.img))

            self.ui.label.setPixmap(QPixmap.fromImage(self.img).scaled(512,512))
            self.ui.label.setAlignment(QtCore.Qt.AlignCenter)
            self.PD=np.asarray(np.load(fileName),dtype=np.uint8)
            self.t1=np.asarray(np.load(fileName),dtype=np.uint8)
            self.t2=np.asarray(np.load(fileName),dtype=np.uint8)
            
            #for i in range (self.size):
            #    self.scale[i] = self.mappingToIntensity(self.scale[i])

            self.Mo=[[[0 for k in range(3)] for j in range(self.size)] for i in range(self.size)]
       
            for i in range (self.size):
               for j in range (self.size):
                   self.Mo[i][j][2]=1
                   if self.scale[i][j]>=0 and self.scale[i][j]<=50 :
                        self.t1[i][j]=10
                        self.t2[i][j]=10
                   elif self.scale[i][j]<=100 and self.scale[i][j] >=50:
                        self.t1[i][j]=1200
                        self.t2[i][j]=100
                   elif self.scale[i][j] <=150 and self.scale[i][j] >=100 :
                        self.t1[i,j]=1300
                        self.t2[i,j]=120
                   elif self.scale[i,j] <=200 and self.scale[i,j] >=150:
                        self.t1[i,j]=1500
                        self.t2[i,j]=150
                   elif self.scale[i,j] <=255 and self.scale[i,j] >=200:
                        self.t1[i,j]=2000
                        self.t2[i,j]=200
                   else:
                        break


            #self.t1 = self.mappingToIntensity(self.t1)
            #self.t2 = self.mappingToIntensity(self.t2)

            self.T1_img= gray2qimage(self.t1)
            self.T2_img= gray2qimage(self.t2)
            self.PD_img= gray2qimage(self.scale)

            self.ui.plainTextEdit.clear()
            self.ui.plainTextEdit.appendPlainText(str(np.unique(self.t1)))
            self.ui.plainTextEdit.appendPlainText(str(np.unique(self.t2)))

            self.ui.labelT1.clear()
            self.ui.labelT1.setPixmap(QPixmap.fromImage(self.T1_img).scaled(512,512))
            self.ui.LabelT2.clear()
            self.ui.LabelT2.setPixmap(QPixmap.fromImage(self.T2_img).scaled(512,512))

    
    def mappingToIntensity(self,array):
        maxx = np.max(array)
        minn = np.min(array)
        if(maxx>255 and min <0): 
            array = (((255-2)/(maxx-minn))*(array-minn+2))
        return array

    def phantom_size(self, text):
        print(text)
        self.n=int(text) 
        
        
    def shape(self, text):
        print(text)
        #self.phantom_type
        if text=="Shepp-Logan":
            self.phantom_type=1
        elif text=="Phantom 1": #squares
            self.phantom_type=2
        elif text=="phantom 2": #circles
            self.phantom_type=3
        else: 
            self.phantom_type=0
    
    
    def create(self):
        if self.n==0 or self.phantom_type==0 :
             QMessageBox.about(self, "Error", "you should choose the size and shape of the phantom first.")
        else :
            print ("create done ")
        if self.phantom_type==1 and self.n==32:
            elipse4=(phantom(n=32))*1000
            elipse4.dump("shepplogan(32).dat")
            QMessageBox.about(self, "Done", "phantom 'shepplogan(32)'  created and saved ")
        elif self.phantom_type==1 and self.n==9:
            elipse4=(phantom(n=9))*1000
            elipse4.dump("shepplogan(9).dat")
            QMessageBox.about(self, "Done", "phantom 'shepplogan(9)'  created and saved ")
        elif self.phantom_type==1 and self.n==20:
            elipse4=(phantom(n=20))*1000
            elipse4.dump("shepplogan(20).dat")
            QMessageBox.about(self, "Done", "phantom 'shepplogan(20)'  created and saved ")
        elif self.phantom_type==1 and self.n==64:
            elipse4=(phantom(n=64))*1000
            elipse4.dump("shepplogan(64).dat")
            QMessageBox.about(self, "Done", "phantom 'shepplogan(64)'  created and saved ")
        elif self.phantom_type==1 and self.n==512:
            elipse4= phantom(n=512) *1000 
            elipse4.dump("shepplogan(512).dat")
            QMessageBox.about(self, "Done", "phantom 'shepplogan(512)'  created and saved ")    
        elif self.phantom_type==2 and self.n==128:
            self.img1 = np.zeros((128,128), np.uint8)
            reactangle1=cv2.rectangle(self.img1,(25,25),(75,62),(42,42,42),-3)
            reactangle2=cv2.rectangle(reactangle1,(62,87),(100,50),(32,32,32),-3)
            reactangle3=cv2.rectangle(reactangle2,(12,75),(50,45),(26,26,26),-3)
            phantom1=cv2.rectangle(reactangle3,(42,55),(72,30),(128,128,128),-3)
            print(type(phantom1))
            phantom1.dump("squares(128).dat")
            QMessageBox.about(self, "Done", "phantom 'squares(128)'  created and saved ")
        elif self.phantom_type==2 and self.n==256:
            self.img1 = np.zeros((256,256), np.uint8)
            reactangle1=cv2.rectangle(self.img1,(50,50),(150,120),(169,169,169),-3)
            reactangle2=cv2.rectangle(reactangle1,(124,180),(200,100),(128,128,128),-3)
            reactangle3=cv2.rectangle(reactangle2,(25,150),(100,90),(105,105,105),-3)
            phantom1=cv2.rectangle(reactangle3,(80,100),(290,120),(255,255,255),-3)
            phantom1.dump("squares(256).dat")
            print(type(phantom1))
            QMessageBox.about(self, "Done", "phantom 'squares(256)'  created and saved ")
        elif self.phantom_type==2 and self.n==512:
            self.img1 = np.zeros((512,512), np.uint8)
            reactangle1=cv2.rectangle(self.img1,(100,100),(300,150),(169,169,169),-3)
            reactangle2=cv2.rectangle(reactangle1,(250,350),(400,200),(128,128,128),-3)
            reactangle3=cv2.rectangle(reactangle2,(50,300),(200,180),(105,105,105),-3)
            phantom1=cv2.rectangle(reactangle3,(170,220),(290,120),(255,255,255),-3)
            phantom1.dump("squares(512).dat")
            print(type(phantom1))
            QMessageBox.about(self, "Done", "phantom 'squares(512)'  created and saved ")
        elif self.phantom_type==3 and self.n==128:
            self.img = np.zeros((128,128), np.uint8)
            line1=cv2.line(self.img,(100,0),(100,128),(255, 255, 255),15)
            line2=cv2.line(self.img,(0,100),(128,100),(200, 200, 200),30)
            circle= cv2.circle(self.img,(64,64), 30, (169,169,169),-1)
            ellipse=cv2.ellipse(self.img,(50,25),(30, 15),0,0,360,(255, 255, 255),-1)
            print(type(self.img))
            self.img.dump("circles(128).dat")
            QMessageBox.about(self, "Done", "phantom 'circles(128)'  created and saved ")
        elif self.phantom_type==3 and self.n==256:
            self.img = np.zeros((256,256), np.uint8)
            line1=cv2.line(self.img,(200,0),(200,256),(255, 255, 255),15)
            line2=cv2.line(self.img,(0,200),(256,200),(200, 200, 200),30)
            circle= cv2.circle(self.img,(128,128), 60, (169,169,169),-1)
            ellipse=cv2.ellipse(self.img,(100,50),(60,30),0,0,360,(255, 255, 255),-1)
            print(type(self.img))
            self.img.dump("circles(256).dat")
            QMessageBox.about(self, "Done", "phantom 'circles(256)'  created and saved ")
        elif self.phantom_type==3 and self.n==512:
            self.img = np.zeros((512,512), np.uint8)
            line1=cv2.line(self.img,(400,0),(400,512),(255, 255, 255),15)
            line2=cv2.line(self.img,(0,400),(512,400),(200, 200, 200),30)
            circle= cv2.circle(self.img,(256,256), 120, (169,169,169),-1)
            ellipse=cv2.ellipse(self.img,(200,100),(120,60),0,0,360,(255, 255, 255),-1)
            print(type(self.img))
            self.img.dump("circles(512).dat")
            QMessageBox.about(self, "Done", "phantom 'circles(512)'  created and saved ")

    def linkedZoom(self,event):
        self.viewer.zoom(event)
        self.viewer1.zoom(event)
    

    def zoomComBox(self):
       if (self.ui.Zoom.currentText()=="Linked"):
           self.viewer.wheelEvent = self.linkedZoom
           self.viewer1.wheelEvent = self.linkedZoom

       elif (self.ui.Zoom.currentText()=="NonLinked"):
           self.viewer.wheelEvent =self.viewer.zoom
           self.viewer2.wheelEvent =self.viewer1.zoom

    def slider(self):
        self.img2=PIL.Image.open("2.png")
        b=self.ui.horizontalSlider.value()
        print(b)
        enhancer = ImageEnhance.Brightness(self.img2).enhance(b/10)
        enhancer.save("out.png")
        self.ui.label.setPixmap(QPixmap("out.png").scaled(512,512)) 
    
    def getpos (self , event):
         self.x=math.floor((event.pos().x()*self.size)/self.ui.label.frameGeometry().width())
         self.y=math.floor((event.pos().y()*self.size) /self.ui.label.frameGeometry().width())
         self.count=self.count+1
         self.count1=self.count1+1
         self.plot()
         if self.count1==1 :
            self.ui.label.clear
            frame=cv2.rectangle(self.scale , (self.x,self.y),(self.x+3,self.y+3),(0,255,0), 1)
            image=Image.fromarray(frame)
            self.img= ImageQt(image)
            self.ui.label.setPixmap(QPixmap.fromImage(self.img).scaled(512,512))
            self.ui.label.setAlignment(QtCore.Qt.AlignCenter)
         elif self.count1==2:
            self.ui.label.clear
            frame=cv2.rectangle(self.scale , (self.x,self.y),(self.x+3,self.y+3),(0,0,255), 1)
            image=Image.fromarray(frame)
            self.img= ImageQt(image)
            self.ui.label.setPixmap(QPixmap.fromImage(self.img).scaled(512,512))
            self.ui.label.setAlignment(QtCore.Qt.AlignCenter)
         elif self.count1==3:
            self.ui.label.clear
            frame=cv2.rectangle(self.scale , (self.x,self.y),(self.x+3,self.y+3),(255,0,0), 1)
            image=Image.fromarray(frame)
            self.img= ImageQt(image)
            self.ui.label.setPixmap(QPixmap.fromImage(self.img).scaled(512,512))
            self.ui.label.setAlignment(QtCore.Qt.AlignCenter)
         elif self.count1==4:
            self.ui.label.clear
            frame=cv2.rectangle(self.scale , (self.x,self.y),(self.x+3,self.y+3),(100,255,0), 1)
            image=Image.fromarray(frame)
            self.img= ImageQt(image)
            self.ui.label.setPixmap(QPixmap.fromImage(self.img).scaled(512,512))
            self.ui.label.setAlignment(QtCore.Qt.AlignCenter)
         elif self.count1==5:
            self.ui.label.clear
            frame=cv2.rectangle(self.scale , (self.x,self.y),(self.x+3,self.y+3),(0,100,100), 1)
            image=Image.fromarray(frame)
            self.img= ImageQt(image)
            self.ui.label.setPixmap(QPixmap.fromImage(self.img).scaled(512,512))
            self.ui.label.setAlignment(QtCore.Qt.AlignCenter)
            self.count1=0
         else :
            print ('end')
    
    def plot(self):
        arr1 = []
        arr2 = []
        self.FA() 
        self.Time_span()
        fa=(np.pi)*self.f/180 
        for t in range (self.T):
            self.Mz=(1-np.exp(-t/self.t1[self.x,self.y]))
            Rx=np.array([[1, 0, 0] ,[0, (np.cos(fa)), (np.sin(fa))], [0 ,(-np.sin(fa)) ,(np.cos(fa))]])
            M=np.matmul(Rx,self.Mo[self.x][self.y])
            M=np.sum(M)
            Mxy=np.exp(-t/self.t2[self.x,self.y])*M
            arr1.append(self.Mz)
            arr2.append(Mxy)
#            QtGui.QApplication.processEvents()
        if self.count==1 :
            self.plotWindow.clear()
            self.plotWindow2.clear()
            self.plotWindow.plot(arr1, pen=pg.mkPen('b', width=2))
            self.plotWindow2.plot(arr2, pen=pg.mkPen('b', width=2))
        elif self.count==2:
            self.plotWindow.plot(arr1, pen1=pg.mkPen('r', width=2))
            self.plotWindow2.plot(arr2, pen1=pg.mkPen('r', width=2))
        elif self.count==3:
            self.plotWindow.plot(arr1, pen2=pg.mkPen('g', width=2))
            self.plotWindow2.plot(arr2, pen2=pg.mkPen('g', width=2))
        elif self.count==4:
            self.plotWindow.plot(arr1, pen=pg.mkPen('l', width=2))
            self.plotWindow2.plot(arr2, pen=pg.mkPen('l', width=2))
        elif self.count==5:
            self.plotWindow.plot(arr1, pen=pg.mkPen('w', width=2))
            self.plotWindow2.plot(arr2, pen=pg.mkPen('w', width=2))
            self.count=0
        else :
            print ('end') 
        self.readInputParameters() 

    def readInputParameters(self):
        self.TE() 
        self.TR()
        self.FA()  

    def IR (self,t):
        self.ui.preparationGraph.clear() 
        tx=np.arange(0,t,.001)
        T3=(2*np.sin(0.75*(tx-20))/(tx-20)) #RF 180 shifted 2
        self.ui.preparationGraph.plot(tx,T3,pen = pg.mkPen('b', width=2))
        #self.ui.preparationGraph.setText("Prepration:IR")

    def T2_PREP (self,t):
            self.ui.preparationGraph.clear() 
            tx=np.arange(0,t+(2*10),.001)
            T1=(np.sin((tx-10))/(tx-10))
            T2=(np.sin(-(tx-(t+10)))/(tx-(t+10)))
            self.ui.preparationGraph.plot(tx,T1,pen = [255,0,0])
            self.ui.preparationGraph.plot(tx,T2,pen = [255,0,0])
            #self.ui.lbl_prep.setText("Prepration:T2_PREP")

    def Tagging(self):
            self.ui.preparationGraph.clear() 
            tx=np.arange(0,15,.001)
            T3=(0.5*np.sin(2*tx))  #RF 180 shifted 2
            self.ui.preparationGraph.plot(tx,T3,pen = [255,0,0])
            #self.ui.preparationGraph.setText("Prepration:Tagging") 



    def ernstAngleFun(self):
            self.TR()

            try:
                data = np.average(self.PD)
            except:
                QMessageBox.about(self, "Error", "Please browse a phantom")

            data = np.average(self.PD)
            vector= np.dot (data,np.matrix ([0,0,1])) 
            self.step = 5
            self.intensity = np.zeros(int(180/self.step))
            j =0
            self.Simulation=[]
            for theta in range ( 0, 180,5 ):
                for i in range(10):
                    vector = self.rotationAroundYaxisMatrix(theta,vector)
                    vector = self.DecayRecoveryEquation(2600,50,1,vector,self.tr)
                x = np.ravel(vector)[0]
                y = np.ravel(vector)[1]
                self.intensity[j] = math.sqrt((x*x)+(y*y))
                j=j+1
            
            
    def drawErnstAngle(self):
        self.lb = QGraphicsView()
        self.lb=pg.PlotWidget()
        self.ernstAngleFun()
        array = np.arange(0,180,self.step)

        self.lb.plot(array,self.intensity)
        self.lb.show()

    def maxErnestAngleCalculated(self):
        self.step = 5
        try:
            if self.Acquisition==3:
                self.TR()
                print(self.tr)
                maxFlipAngle = math.acos( np.exp(-self.tr / 1200) )
                maxFlipAngle = (maxFlipAngle*180)/math.pi
                print(maxFlipAngle)
            else:
                result = np.where(self.intensity == np.max(self.intensity))
                maxFlipAngleIndex = result[0][0]
                maxFlipAngle = self.step*maxFlipAngleIndex
            
            self.ui.plainTextEdit_3.clear()
            self.ui.plainTextEdit_3.appendPlainText(str(int(maxFlipAngle)))
        except:
            self.ernstAngleFun()
            self.maxErnestAngleCalculated()



    def rotationAroundYaxisMatrix(self,theta,vector):
            vector = vector.transpose()
            theta = (math.pi / 180) * theta
            R = np.matrix ([[np.cos(theta), 0, np.sin(theta)], [0, 1, 0], [-np.sin(theta), 0, np.cos(theta)]] )
            R = np.dot(R, vector)
            R = R.transpose()
            return np.matrix(R)

    def rotationAroundZaxisMatrixXY(self,TR,speed,vector,time): #time = self.time
            vector = vector.transpose()
            theta = speed * (time/ TR)
            theta = (math.pi / 180) * theta
            XY = np.matrix([[np.cos(theta),-np.sin(theta),0], [np.sin(theta), np.cos(theta),0],[0, 0, 1]])
            XY = np.dot(XY,vector)
            XY = XY.transpose()
            return np.matrix(XY) 


    def DecayRecoveryEquation(self,T1,T2,PD,vector,time):
            vector = vector.transpose()
            Decay =np.matrix([[np.exp(-time/T2),0,0],[0,np.exp(-time/T2),0],[0,0,np.exp(-time/T1)]])
            Decay = np.dot(Decay,vector)
        
            Rec= np.dot(np.matrix([[0,0,(1-(np.exp(-time/T1)))]]),PD)
            Rec = Rec.transpose()
            Decay = np.matrix(Decay)
            Rec =  np.matrix(Rec)    
        
            RD  = Decay + Rec
            RD = RD.transpose()
            return RD

    def TR(self):    
        self.tr=self.ui.TR.value()

        
    def TE(self):
        self.te=self.ui.TE.value()
       
        
    def FA(self):
        self.f=self.ui.FA.value()
        
    def Time_span(self):
        self.T=self.ui.time_span.value()
        print(self.T)
    
    def SE (self):
    
        te = round(self.te/3)
        self.ui.AcquisionGraph.clear()
        tx=np.arange(0,self.tr)
        Rf1=(np.sin(((self.f*2)/180)*(tx-te))/(tx-te)+10)
        Rf2=(2*np.sin(((self.f*2)/180)*(tx-(te*2)))/(tx-(te*2))+10)

        Gx = self.RectangularGraph(self.tr,8,(te*3),1,te)
        Gy = self.RectangularGraph(self.tr,6,(te*4),1,te)
        Readout = self.RectangularGraph(self.tr,4,(te*4),1,te)
        
        self.ui.AcquisionGraph.plot(tx,Rf1,pen = [255,0,0])
        self.ui.AcquisionGraph.plot(tx,Rf2,pen = [255,0,0])

        self.ui.AcquisionGraph.plot(tx,Gx,pen = [255,0,0])
        self.ui.AcquisionGraph.plot(tx,Gy,pen = [255,0,0])
        self.ui.AcquisionGraph.plot(tx,Readout,pen = [255,0,0])


    def GRE (self):

        te = round(self.te/3)
        self.ui.AcquisionGraph.clear()
        tx=np.arange(0,self.tr)
        Rf=(np.sin(((self.f*2)/180)*(tx-te))/(tx-te)+10)
        Gx = self.RectangularGraph(self.tr,8,(te*2),1,te)
        Gy = self.RectangularGraph(self.tr,6,(te*3),1,te)
        Readout = self.RectangularGraph(self.tr,4,(te*3),1,te)
        
        self.ui.AcquisionGraph.plot(tx,Rf,pen = [255,0,0])
        self.ui.AcquisionGraph.plot(tx,Gx,pen = [255,0,0])
        self.ui.AcquisionGraph.plot(tx,Gy,pen = [255,0,0])
        self.ui.AcquisionGraph.plot(tx,Readout,pen = [255,0,0])


    def SSFP (self):

        te = round(self.te/3)
        self.ui.AcquisionGraph.clear()
        tx=np.arange(0,self.tr)
        Rf=(np.sin(((self.f*2)/180)*(tx-te))/(tx-te)+10)
        Gx = self.RectangularGraph(self.tr,8,(te*2),1,te)
        Gy = self.RectangularGraph(self.tr,6,(te*3),1,te)
        Readout = self.RectangularGraph(self.tr,4,(te*3),1,te)
        GxReversed = self.RectangularGraph(self.tr,8,(te*5+30),-1,te)
        GyReversed = self.RectangularGraph(self.tr,6,(te*5+30),-1,te)

        self.ui.AcquisionGraph.plot(tx,Rf,pen = [255,0,0])
        self.ui.AcquisionGraph.plot(tx,Gx,pen = [255,0,0])
        self.ui.AcquisionGraph.plot(tx,Gy,pen = [255,0,0])
        self.ui.AcquisionGraph.plot(tx,Readout,pen = [255,0,0])
        self.ui.AcquisionGraph.plot(tx,GxReversed,pen = [255,0,0])
        self.ui.AcquisionGraph.plot(tx,GyReversed,pen = [255,0,0])





    def RectangularGraph(self,tR,shiftDown,shiftRight,step,width):
        z = []
        
        for i in range (0,tR):
            if i < int(shiftRight):
                z.append(shiftDown) 
            elif i >= int(shiftRight) and i < int(width+shiftRight):
                z.append(shiftDown+(step*1)) 
            else:
                z.append(shiftDown) 
        return z

    def acquisition (self,text):
        self.readInputParameters() 
        if text =="SSFP":
            self.Acquisition=1
            self.SSFP()
        elif text=="SpinEcho": 
            self.Acquisition=2
            self.SE()
        elif text=="GRE": 
            self.Acquisition=3
            self.GRE()
        else: 
            self.Acquisition = 0
    
    def preb (self,text):
        if text=="T1IR": 
            self.Prepration=1
            self.nullTissue, ok = QInputDialog.getInt(self,"integer input dialog","enter Null Tissue T1")
            self.IR(self.nullTissue * np.log(2))
            print(self.nullTissue)
        elif text=="T2Preb": 
            self.Prepration=2
            self.T2prebtime, ok = QInputDialog.getInt(self,"integer input dialog","enter time inteval for preb")
            self.T2_PREP(self.T2prebtime)
            print(self.T2prebtime)
        elif text=="Tagging":
            self.Tagging()
            self.step, ok = QInputDialog.getInt(self,"integer input dialog","enter step for tagging preparation")
            self.Prepration=3
        else: 
            self.Prepration =0
            self.ui.preparationGraph.clear() 
 

    def prepration(self):
        if (self.Prepration==1):
            t = self.nullTissue * np.log(2)
            for i in range(self.size):
                    for j in range(self.size):
                        self.signal[i][j] = self.rotationAroundYaxisMatrix(180,np.matrix(self.signal[i][j])) 
                        self.signal[i][j] = self.DecayRecoveryEquation(self.t1[i,j],self.t2[i,j],1,np.matrix(self.signal[i][j]),t)
                        self.signal[i][j] = [[0,0,np.ravel(self.signal[i][j])[2]]]
        
        elif (self.Prepration==2):
            for i in range(self.size):
                    for j in range(self.size):
                        self.signal[i][j] = self.rotationAroundYaxisMatrix(90,np.matrix(self.signal[i][j])) 
                        self.signal[i][j] = self.DecayRecoveryEquation(self.t1[i,j],self.t2[i,j],1,np.matrix(self.signal[i][j]),self.T2prebtime)
                        self.signal[i][j] = [[0,0,np.ravel(self.signal[i][j])[2]]]
                        self.signal[i][j] = self.rotationAroundYaxisMatrix(-90,np.matrix(self.signal[i][j])) 
        elif (self.Prepration==0):
            print("nrg3 normal tany")
            self.ui.preparationGraph.clear() 

        
        elif (self.Prepration==3):
            for i in range(self.size):
                    for j in range(0 ,self.size, self.step):
                        self.signal[i][j][2] = np.dot ( np.ravel(self.signal[i][j])[2],  np.sin((np.pi*j)/(2*self.size)))
        else:
            QMessageBox.about(self, "Error", "you should choose the Preperation sequence first")

        
      

    def startUpCycle(self):
        self.StartUpCycle=self.ui.StartUpCycle_2.value()
        self.signal = [[[0 for k in range(3)] for j in range(self.size)] for i in range(self.size)]
        for i in range(self.size):
                for j in range(self.size):
                    self.signal[i][j][2] =1
       
        for loop in range(self.StartUpCycle):
                    for i in range(self.size):
                        for j in range(self.size):
                            self.signal[i][j] = self.rotationAroundYaxisMatrix(self.f,np.matrix(self.signal[i][j])) 
                            self.signal[i][j] = self.DecayRecoveryEquation(self.t1[i,j],self.t2[i,j],1,np.matrix(self.signal[i][j]),self.tr)
                            self.signal[i][j] = [[0,0,np.ravel(self.signal[i][j])[2]]]
       

    def Start(self):
        
        self.readInputParameters() 
        self.Kspace =  np.zeros((self.size,self.size),dtype=np.complex_)
        self.startUpCycle()
        self.prepration()
        if (self.Acquisition==1):
            self.Kspace = cythonfile.SSFPForLoops(self.Kspace,self.size,self.signal,self.f,self.t1,self.t2,self.te,self.tr,self.AliasingFactor)
            self.ReconstructionImageAndKspace()    
        elif (self.Acquisition==2):
            self.Kspace = cythonfile.SpinEchoForLoops(self.Kspace,self.size,self.signal,self.f,self.t1,self.t2,self.te,self.tr,self.AliasingFactor)
            self.ReconstructionImageAndKspace()    

        elif (self.Acquisition==3):
            self.Kspace = cythonfile.GREForLoops(self.Kspace,self.size,self.signal,self.f,self.t1,self.t2,self.te,self.tr,self.AliasingFactor,self.improperSampling)
            self.ReconstructionImageAndKspace()    

        else:
            QMessageBox.about(self, "Error", "you should choose the acquisition sequence first")
    

    
    def ReconstructionImageAndKspace(self):
        print(self.Kspace)
        KspaceSave =abs(copy.deepcopy(self.Kspace))
        print("Done")
        imsave('kspace.png', KspaceSave)
        self.ui.label_2.setPixmap(QtGui.QPixmap('kspace.png').scaled(512,512))
        Kspacefft = np.fft.fft2(self.Kspace)
        #Kspaceifft = np.fft.ifft2(self.Kspace)
        Kspacefft = abs(Kspacefft)
        Kspacefft = np.array(np.round_(Kspacefft))
        imsave("image.png", Kspacefft)

        pixmap = QtGui.QPixmap("image.png")
        self.viewer1.setPhoto(pixmap)

        pixmap = pixmap.scaled(512,512)
        
        self.ui.label_3.setPixmap(pixmap)

            
def main():
    app = QtWidgets.QApplication(sys.argv)
    application = ApplicationWindow()
    application.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()