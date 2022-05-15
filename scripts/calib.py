import numpy as np
from scipy import interpolate
import matplotlib.pyplot as plt

setc = np.array([0,2,4,6,8,10,15,20,25,30,35,40,50,60,70,80,90,100,110,120,130,140,150,170,190,200])

current = np.array([2.39,2.39,2.39,2.9,4.85,6.81,11.71,16.61,21.5,26.3,31.18,36.4,45.8,55.6,65.4,75.1,84.9,94.7,104,114,123.9,133.7,143,162.9,182.3,191.9])


app = current*1.02+4

plt.plot(setc, current, 'o')
plt.plot(setc, setc)
plt.show()