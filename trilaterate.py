import numpy
import scipy.optimize
from itertools import combinations
import matplotlib.pyplot as plt

anchors = numpy.array([[0, 0], [100, 0], [50, 87], [90, 80]])
rover_pos = numpy.array([40, 30])
ranges = numpy.sqrt(numpy.sum((anchors - rover_pos) ** 2, axis=1))

SIGMA_R = 6.0  # meters, from measured 6dB RSSI noise
# honest 3-anchor cost ~ chi2(1 dof)*sigma_r^2, so use a multiple of sigma_r^2
# as the "this subset is clean" ceiling, and require the other subsets be well above it
CLEAN_CEILING = 4 * SIGMA_R**2   # ~144
DIRTY_FLOOR = 15 * SIGMA_R**2    # ~540

def distance_cost(candidate, anchors, ranges):
    total = 0
    for i in range(len(anchors)):
        dist = numpy.sqrt((candidate[0]-anchors[i][0])**2 + (candidate[1]-anchors[i][1])**2)
        total += (dist - ranges[i]) ** 2
    return total

def trilaterate(anchors, ranges):
    result = scipy.optimize.minimize(distance_cost, [0, 0], args=(anchors, ranges))
    return result.x, result.fun

def raim(anchors, ranges):
    subsets = list(combinations(range(4), 3))
    costs, fixes, excluded = [], [], []
    for subset in subsets:
        fix, cost = trilaterate(anchors[list(subset)], ranges[list(subset)])
        costs.append(cost)
        fixes.append(fix)
        excluded.append([i for i in range(4) if i not in subset][0])
    best = numpy.argmin(costs)
    others = [c for i, c in enumerate(costs) if i != best]
    if costs[best] < CLEAN_CEILING and min(others) > DIRTY_FLOOR:
        return excluded[best], fixes[best], costs
    return None, fixes[best], costs

# false positive rate on honest data
numpy.random.seed(0)
num_trials = 500
fp = sum(1 for _ in range(num_trials)
         if raim(anchors, ranges + numpy.random.normal(0, SIGMA_R, 4))[0] is not None)
print(f"False positive rate: {fp/num_trials*100:.1f}%")

# detection sweep
spoof_distances = [10, 25, 50, 75, 100, 150, 200, 250]
detection_rates = []
for d in spoof_distances:
    hits = 0
    for _ in range(num_trials):
        noisy = ranges + numpy.random.normal(0, SIGMA_R, 4)
        spoofed = anchors.copy()
        spoofed[2] = anchors[2] + [d*0.7, d*0.7]
        suspect, fix, costs = raim(spoofed, noisy)
        if suspect == 2:
            hits += 1
    rate = hits / num_trials
    detection_rates.append(rate)
    print(f"Spoof {d}m: {rate*100:.0f}% detected")

plt.figure()
plt.plot(spoof_distances, [r*100 for r in detection_rates], 'o-', label='Detection rate')
plt.axhline(y=fp/num_trials*100, color='red', linestyle='--', label=f'False positive rate ({fp/num_trials*100:.1f}%)')
plt.xlabel('Spoofing Magnitude (m)')
plt.ylabel('Probability (%)')
plt.title('RAIM Detection — Absolute Cost Threshold')
plt.ylim(0, 105)
plt.grid(True, alpha=0.3)
plt.legend()
plt.savefig('raim_detection.png')