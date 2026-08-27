import scipy
import numpy
import csv
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

#stores rssi values as a dictionary with distance obtained as the key and lists of measurements as the values 
#distances are in meters, converted from yards
data = {
    10: [],
    20: [],
    48: [],
    82: [],
    114: [],
    160: [],
}

with open ('log.csv', 'r') as f:
    reader = csv.reader(f)
    header = next(reader)

    for row in reader:
        time = row[0][11:19]
        if '13:22:00' < time < '13:25:00':
            data[10].append(int(row[2]))
        elif '13:25:00' < time < '13:28:00':
            data[20].append(int(row[2]))
        elif '13:30:00' < time < '13:33:00':
            data[48].append(int(row[2]))
        elif '13:35:00' < time < '13:39:00':
            data[82].append(int(row[2]))
        elif '13:40:00' < time < '13:44:00':
            data[114].append(int(row[2]))
        elif '13:45:00' < time < '13:49:00':
            data[160].append(int(row[2]))

distances = numpy.array(list(data.keys()))
rssi_values = numpy.array([numpy.mean(v) for v in data.values()])

def path_loss_model(d, A, n):
    return A - 10 * n * numpy.log10(d)

def estimate_range(RSSI,A,n):
    return 10 ** ((A-RSSI) / (10*n))

popt, pcov = curve_fit(path_loss_model,distances,rssi_values)

print(popt)
print(pcov)

d_smooth = numpy.linspace(1, 200, 500)
predicted_rssi = path_loss_model(d_smooth,popt[0],popt[1])

print(estimate_range(-65, popt[0], popt[1]))

for d in data:
    print(f"{d}m: mean={numpy.mean(data[d]):.1f} std={numpy.std(data[d]):.1f} ({len(data[d])} samples)")

A, n = popt[0], popt[1]

for d in data:
    mean_rssi = numpy.mean(data[d])
    estimated = estimate_range(mean_rssi, A, n)
    error = abs(estimated - d)
    print(f"True: {d}m | Estimated: {estimated:.1f}m | Error: {error:.1f}m ({error/d*100:.0f}%)")

plt.figure()
plt.scatter(distances, rssi_values, label='Measured')
plt.plot(d_smooth, predicted_rssi, label='Fitted model')
plt.xlabel('Distance (m)')
plt.ylabel('RSSI (dBm)')
plt.title('Path Loss Model')
plt.legend()
plt.savefig('path_loss.png')
