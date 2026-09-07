import numpy
import csv
import scipy.optimize
import matplotlib.pyplot as plt
from itertools import combinations

# path loss params from the calibration calculations, (see analyze.py)
A = -43.16
n = 2.55

# anchor layout from the field, converted to meters.
# From_IDS: 5903 north, b12b east, 820e south, 85e4 west
# assumes anchors are on exact cardinal bearings from center, which is roughly true
anchor_ids = ['!f96f5903', '!05c8b12b', '!cae6820e', '!d1da85e4']
anchor_names = ['North', 'East', 'South', 'West']
anchors = numpy.array([
    [0, 40],
    [27, 0],
    [0, -39],
    [-27.4, 0]
])

# rover positions. verified via rangefinder but there is some degree of error in those measurements given that i was shooting a small bucket with a radio on top.
rover_windows = {
    'Position 1 (center)': ('19:54:00', '19:57:00', [0, 0]),
    'Position 2 (north, est.)': ('19:58:00', '20:00:30', [0, 15]),
    'Position 3 (SE, est.)': ('20:02:00', '20:05:00', [12, -12]),
}

# threshold for RAIM detection — if the best subset is this many times better than the second best, call it spoofing. 
# without this the algorithm always flags somebody even when everyone's honest
RAIM_THRESHOLD = 3.0

def estimate_range(rssi):
    # inverse of the path loss model
    return 10 ** ((A - rssi) / (10 * n))

def distance_cost(candidate, anchors, ranges):
    total = 0
    for i in range(len(anchors)):
        dist = numpy.sqrt((candidate[0] - anchors[i][0])**2 + (candidate[1] - anchors[i][1])**2)
        total += (dist - ranges[i]) ** 2
    return total

def get_ranges(start, end):
    rssi_by_anchor = {aid: [] for aid in anchor_ids}
    with open('trilatlog.csv', 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            time = row[0][11:19]
            if start < time < end and row[1] in rssi_by_anchor:
                rssi_by_anchor[row[1]].append(int(row[2]))
    ranges = []
    for aid in anchor_ids:
        mean_rssi = numpy.mean(rssi_by_anchor[aid])
        ranges.append(estimate_range(mean_rssi))
        print(f"  {aid}: mean RSSI={mean_rssi:.1f}, est range={ranges[-1]:.1f}m, n={len(rssi_by_anchor[aid])}")
    return numpy.array(ranges)

def trilaterate(anchors, ranges):
    result = scipy.optimize.minimize(distance_cost, [0, 0], args=(anchors, ranges))
    return result.x, result.fun

def raim(anchors, ranges):
    # trilaterate with every 3-of-4 subset. the subset that excludes the liar
    # has three honest anchors that agree, so it has the lowest cost.
    # only flag if that subset is clearly better than the rest.
    subsets = list(combinations(range(4), 3))
    costs = []
    fixes = []
    excluded = []
    for subset in subsets:
        fix, cost = trilaterate(anchors[list(subset)], ranges[list(subset)])
        exc = [i for i in range(4) if i not in subset][0]
        costs.append(cost)
        fixes.append(fix)
        excluded.append(exc)
    
    sorted_costs = sorted(costs)
    ratio = sorted_costs[1] / sorted_costs[0]
    best = numpy.argmin(costs)
    
    if ratio > RAIM_THRESHOLD:
        return fixes[best], excluded[best], costs, ratio
    else:
        return fixes[best], None, costs, ratio


# ---- trilateration on real data ----
print("--- TRILATERATION ---")
plt.figure(figsize=(8, 8))
plt.scatter(anchors[:, 0], anchors[:, 1], c='blue', s=150, marker='^', label='Anchors', zorder=3)
for i, name in enumerate(anchor_names):
    plt.annotate(name, (anchors[i, 0], anchors[i, 1]), textcoords="offset points", xytext=(8, 8))

errors = []
for label, (start, end, true_pos) in rover_windows.items():
    print(f"\n{label}:")
    ranges = get_ranges(start, end)
    est, cost = trilaterate(anchors, ranges)
    error = numpy.sqrt((est[0] - true_pos[0])**2 + (est[1] - true_pos[1])**2)
    errors.append(error)
    print(f"  true={true_pos}  est=[{est[0]:.1f}, {est[1]:.1f}]  error={error:.1f}m")
    plt.scatter(true_pos[0], true_pos[1], c='green', s=100, marker='o', zorder=3)
    plt.scatter(est[0], est[1], c='red', s=100, marker='x', zorder=3)
    plt.plot([true_pos[0], est[0]], [true_pos[1], est[1]], 'k--', alpha=0.5)

plt.scatter([], [], c='green', marker='o', label='True position')
plt.scatter([], [], c='red', marker='x', label='Estimated position')
plt.xlabel('East (m)')
plt.ylabel('North (m)')
plt.title(f'Trilateration on Real Hardware\nMean error: {numpy.mean(errors):.1f}m')
plt.legend()
plt.axis('equal')
plt.grid(True, alpha=0.3)
plt.savefig('trilateration_field.png')
print(f"\nmean error: {numpy.mean(errors):.1f}m")


# ---- RAIM on real RSSI ----
# the spoofed positions here are applied in post-processing. the RSSI is real but the fake anchor position is typed in, not captured from a position packet.
# RSSI doesn't change when a node lies about its GPS so this is mathematically the same as an over-the-air spoof, but it's not the full end-to-end demo.
print("\n--- RAIM (real RSSI from Position 1, spoof applied in post) ----")
ranges = get_ranges('19:54:00', '19:57:00')

print("\nbaseline, everyone honest:")
fix, suspect, costs, ratio = raim(anchors, ranges)
print(f"  costs: {[f'{c:.1f}' for c in costs]}  ratio={ratio:.2f}")
if suspect is None:
    print(f"  no spoofing detected (ratio below {RAIM_THRESHOLD})")
else:
    print(f"  FALSE POSITIVE: flagged {anchor_names[suspect]}")

for spoof_dist in [25, 50, 100, 200]:
    print(f"\nnorth anchor lies by {spoof_dist}m:")
    spoofed = anchors.copy()
    spoofed[0] = anchors[0] + [spoof_dist, 0]
    fix, suspect, costs, ratio = raim(spoofed, ranges)
    print(f"  costs: {[f'{c:.1f}' for c in costs]}  ratio={ratio:.2f}")
    if suspect == 0:
        print(f"  DETECTED — flagged North")
    elif suspect is None:
        print(f"  MISSED — ratio below threshold")
    else:
        print(f"  WRONG — flagged {anchor_names[suspect]}")