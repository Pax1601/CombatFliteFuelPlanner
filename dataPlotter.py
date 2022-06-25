plane = "FA-18C"

import json
from os.path import join
import matplotlib.pyplot as plt
plt.rcParams['axes.grid'] = True

styleDragIndex = {0: "-", 100: "--", 300: "-."}
plotAltitude = {0: 0, 15000: 1, 30000: 2}
typeWeight = {26000: "b", 50000: "k"}
fileName = join("fuelGraphs", plane + ".json")

f = open(fileName)
finalData = json.load(f)
f.close()

fig, axs = plt.subplots(3)

for i, ax in enumerate(axs):
    ax.set_title(f'Altitude {list(plotAltitude.keys())[i]}ft')
    if i != 2:
        ax.set(ylabel="Specific range [nm / lbs]")
    else:
        ax.set(xlabel="Mach number [-]", ylabel="Specific range [nm / lbs]")

for altitude in finalData:
    for weight in finalData[altitude]:
        for dragIndex in finalData[altitude][weight]:
            x = [value[0] for value in finalData[altitude][weight][dragIndex]]
            y = [value[1] for value in finalData[altitude][weight][dragIndex]]
            axs[plotAltitude[float(altitude)]].plot(x, y, typeWeight[float(weight)] +  styleDragIndex[float(dragIndex)])

plt.show()
