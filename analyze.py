import scipy
import numpy
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

distances = numpy.array([10, 25, 50, 100, 250])
rssi_values = numpy.array([-45, -55, -65, -75, -88])
d_smooth = numpy.linspace(1, 300, 500)

def path_loss_model(d, A, n):
    return A - 10 * n * numpy.log10(d)

def estimate_range(RSSI,A,n):
    return 10 ** ((A-RSSI) / (10*n))

popt, pcov = curve_fit(path_loss_model,distances,rssi_values)

print(popt)
print(pcov)

predicted_rssi = path_loss_model(d_smooth,popt[0],popt[1])

print(estimate_range(-65, popt[0], popt[1]))

plt.figure()
plt.scatter(distances, rssi_values, label='Measured')
plt.plot(d_smooth, predicted_rssi, label='Fitted model')
plt.xlabel('Distance (m)')
plt.ylabel('RSSI (dBm)')
plt.title('Path Loss Model')
plt.legend()
plt.savefig('path_loss.png')
