
import math
import numpy as np



cpdef rotationAroundYaxisMatrix(theta,vector):
            vector = vector.transpose()
            theta = (math.pi / 180) * theta
            R = np.matrix ([[np.cos(theta), 0, np.sin(theta)], [0, 1, 0], [-np.sin(theta), 0, np.cos(theta)]] )
            R = np.dot(R, vector)
            R = R.transpose()
            return np.matrix(R)

cpdef rotationAroundZaxisMatrixXY(TR,speed,vector,time): 
            vector = vector.transpose()
            theta = speed * (time/ TR)
            theta = (math.pi / 180) * theta
            XY = np.matrix([[np.cos(theta),-np.sin(theta),0], [np.sin(theta), np.cos(theta),0],[0, 0, 1]])
            XY = np.dot(XY,vector)
            XY = XY.transpose()
            return np.matrix(XY) 


cpdef DecayRecoveryEquation(T1,T2,PD,vector,time):
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

cpdef SpinEchoForLoops(Kspace,size,signal,f,t1,t2,te,tr,AliasingFactor):           
        

        for Ki in range(Kspace.shape[0]):
            print('Ki: ',Ki)

            for i in range(size):
                    for j in range(size):
                        signal[i][j] = rotationAroundYaxisMatrix(f,np.matrix(signal[i][j]))
                        signal[i][j] = DecayRecoveryEquation(t1[i,j],t2[i,j],1,np.matrix(signal[i][j]),(te/2))
                        signal[i][j] = rotationAroundYaxisMatrix((f*2),np.matrix(signal[i][j]))
                        signal[i][j] = DecayRecoveryEquation(t1[i,j],t2[i,j],1,np.matrix(signal[i][j]),(te/2))

            # for kspace column
            for Kj in range (Kspace.shape[1]):
                print('Kj: ',Kj)
                GxStep = ((2 * math.pi) /  Kspace.shape[0]) * Kj
                GyStep = ((AliasingFactor * math.pi) / Kspace.shape[1]) * Ki            
                
                for i in range(size):
                    for j in range(size):
                        totalTheta = (GxStep*j)+ (GyStep*i)
                        z = abs(complex(np.ravel(signal[i][j])[0],np.ravel(signal[i][j])[1]))
                        Kspace[Ki,Kj]= Kspace[Ki,Kj] + (z * np.exp(1j*totalTheta))
            
            for i in range(size):
                for j in range(size):
                    signal[i][j] = DecayRecoveryEquation(t1[i,j],t2[i,j],1,np.matrix(signal[i][j]),(tr))
                    signal[i][j] = [[0,0,np.ravel(signal[i][j])[2]]]


        return Kspace

cpdef SSFPForLoops(Kspace,size,signal,f,t1,t2,te,tr,AliasingFactor):    
        angle60 = True

        for i in range(size):
            for j in range(size):
                signal[i][j] =  rotationAroundYaxisMatrix((f/2),np.matrix(signal[i][j]))
                signal[i][j] =  DecayRecoveryEquation(t1[i][j],t2[i][j],1,np.matrix(signal[i][j]),tr)
                #signal[i][j] = [[0,0,np.ravel(signal[i][j])[2]]]
        
        for Ki in range(Kspace.shape[0]):
            print('Ki: ',Ki)
            #move in each image pixel            
            if angle60 :
                theta = -f
            else:
                theta = f
                
            for i in range(size):
                    for j in range(size):
                        signal[i][j] =  rotationAroundYaxisMatrix(theta,np.matrix(signal[i][j]))
                        signal[i][j] = signal[i][j] * np.exp(-te/t2[i][j])


            # for kspace column
            for Kj in range ( Kspace.shape[1]):
                print('Kj: ',Kj)
                GxStep = ((2 * math.pi) /  Kspace.shape[0]) * Kj
                GyStep = ((AliasingFactor * math.pi) / Kspace.shape[1]) * Ki            
                
                for i in range(size):
                    for j in range(size):
                        totalTheta = (GxStep*j)+ (GyStep*i)
                        z = abs(complex(np.ravel(signal[i][j])[0],np.ravel(signal[i][j])[1]))
                        Kspace[Ki,Kj]= Kspace[Ki,Kj] + (z * np.exp(1j*totalTheta))
            
            for i in range(size):
                for j in range(size):
                    signal[i][j] = DecayRecoveryEquation(t1[i,j],t2[i,j],1,np.matrix(signal[i][j]),(tr))
                    #signal[i][j] = [[0,0,np.ravel(signal[i][j])[2]]]

            angle60 = not angle60

        return Kspace 
    
cpdef GREForLoops(Kspace,size,signal,f,t1,t2,te,tr,AliasingFactor,improperSampling): 

        for Ki in range(Kspace.shape[0]):
            print('Ki: ',Ki)
            #move in each image pixel            

            for i in range(size):
                for j in range(size):
                        signal[i][j] =  rotationAroundYaxisMatrix(f,np.matrix(signal[i][j]))
                        signal[i][j] = signal[i][j] * np.exp(-te/t2[i][j])

            # for kspace column
            for Kj in range (Kspace.shape[1]):
                print('Kj: ',Kj)
                GxStep = ((2 * math.pi) / Kspace.shape[0]) * Kj
                
                if(improperSampling==1):
                    if(Ki%2==0):
                        m2somFactor = Ki
                        GyStep = ((AliasingFactor * math.pi) /Kspace.shape[1]) * Ki
                    else:
                        GyStep = ((AliasingFactor * math.pi) /Kspace.shape[1]) * m2somFactor
                else:
                    GyStep = ((AliasingFactor * math.pi) /Kspace.shape[1]) * Ki


                
                for i in range(size):
                    for j in range(size):
                        totalTheta = (GxStep*j)+ (GyStep*i)
                        z = abs(complex(np.ravel(signal[i][j])[0],np.ravel(signal[i][j])[1]))
                        Kspace[Ki,Kj]= Kspace[Ki,Kj] + (z * np.exp(1j*totalTheta))

            for i in range(size):
                for j in range(size):
                    signal[i][j] = DecayRecoveryEquation(t1[i,j],t2[i,j],1,np.matrix(signal[i][j]),(tr))
                    signal[i][j] = [[0,0,np.ravel(signal[i][j])[2]]]
        
        return Kspace