plane = "FA-18C"

from os import listdir
from os.path import isfile, join
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import json

data = []
finalData = {}
cycleIndex = 0
DI = 0

def onclick(event):
    global cycleIndex, data, DI
    ix, iy = event.xdata, event.ydata
    if cycleIndex <= 1:
        data.append(float(input('Mach number: ')))
        data.append(float(input('Specific fuel consumption: ')))
        data.append((ix, iy))
        if cycleIndex == 0:
            print("Click on the upper right corner of the plot")
        else:
            DI = float(input('Drag index: '))
            print("Start entering data points, right click to change drag index")
    else:
        if event.button == 3:
            DI = float(input('Drag index: '))
            print("Start entering data points, right click to change drag index")
        else:
            data.append((ix, iy, DI))
    cycleIndex += 1

plotsFolder = join("fuelGraphs", plane)
plots = [f for f in listdir(plotsFolder) if isfile(join(plotsFolder, f))]

for plot in plots:
    sp1 = plot.split("_")
    altitude = float(sp1[0])
    weight = float(sp1[1].split(".")[0])
    img = mpimg.imread(join(plotsFolder, plot))
    fig = plt.figure()
    imgplot = plt.imshow(img)
    cid = fig.canvas.mpl_connect('button_press_event', onclick)
    print("Click on the bottom left corner of the plot")
    plt.show()
    fig.canvas.mpl_disconnect(cid)

    #Extract the data
    minMach = data[0]
    minSF = data[1]
    minX = data[2][0]
    minY = data[2][1]
    maxMach = data[3]
    maxSF = data[4]
    maxX = data[5][0]
    maxY = data[5][1]

    if altitude not in finalData:
        finalData[altitude] = {}
    if weight not in finalData[altitude]:
        finalData[altitude][weight] = {}
    for dataPoint in data[6:]:
        mach = (dataPoint[0] - minX) / (maxX - minX) * (maxMach - minMach) + minMach 
        SF = (dataPoint[1] - minY) / (maxY - minY) * (maxSF - minSF) + minSF
        DI = dataPoint[2]
        if DI not in finalData[altitude][weight]:
            finalData[altitude][weight][DI] = []
        finalData[altitude][weight][DI].append((mach, SF))

    fileName = join("fuelGraphs", plane + ".json")
    with open(fileName, 'w') as fp:
        json.dump(finalData, fp)

    data.clear()
    cycleIndex = 0






