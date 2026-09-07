import numpy
import scipy.optimize
from itertools import combinations
import matplotlib.pyplot as plt

anchors = numpy.array([
    [0, 0],
    [100, 0],
    [50, 87],
    [90, 80]
])

rover_pos = numpy.array([40, 30])
ranges = numpy.sqrt(numpy.sum((anchors - rover_pos) ** 2, axis=1))

# Spoof anchor 2
spoofed_anchors = anchors.copy()
spoofed_anchors[2] = [150, 87]

def distance_cost(candidate, anchors, ranges):
    total = 0
    for i in range(len(anchors)):
        dist = numpy.sqrt((candidate[0] - anchors[i][0])**2 + (candidate[1] - anchors[i][1])**2)
        total += (dist - ranges[i]) ** 2
    return total

subsets = list(combinations(range(4), 3))



spoof_distances = [10, 25, 50, 100, 150, 200, 300, 500]
num_trials = 500
detection_rates = []

for spoof_dist in spoof_distances:
    detections = 0
    for trial in range(num_trials):
        noisy_ranges = ranges + numpy.random.normal(0, 6, len(ranges))
        
        spoofed = anchors.copy()
        spoofed[2] = anchors[2] + [spoof_dist * 0.7, spoof_dist * 0.7]
        
        costs = []
        excluded_list = []
        for subset in subsets:
            sub_anchors = spoofed[list(subset)]
            sub_ranges = noisy_ranges[list(subset)]
            result = scipy.optimize.minimize(distance_cost, [0, 0], args=(sub_anchors, sub_ranges))
            excluded = [i for i in range(4) if i not in subset][0]
            costs.append(result.fun)
            excluded_list.append(excluded)
        
        detected_spoofer = excluded_list[numpy.argmin(costs)]
        if detected_spoofer == 2:
            detections += 1
    
    rate = detections / num_trials
    detection_rates.append(rate)
    print(f"Spoof distance: {spoof_dist}m, detection rate: {rate*100:.0f}%")

plt.figure()
plt.plot(spoof_distances, [r * 100 for r in detection_rates], 'o-')
plt.xlabel('Spoofing Magnitude (m)')
plt.ylabel('Detection Probability (%)')
plt.title('RAIM Spoofing Detection Performance')
plt.ylim(0, 105)
plt.grid(True)
plt.savefig('raim_detection.png')