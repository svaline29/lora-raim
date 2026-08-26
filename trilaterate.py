import numpy
import scipy.optimize

anchors = numpy.array([
    [0, 0],
    [100, 0],
    [50, 87]
])

rover_pos = numpy.array([40, 30])

ranges = numpy.array([
    numpy.sqrt((rover_pos[0] - anchors[0][0])**2 + (rover_pos[1] - anchors[0][1])**2),
    numpy.sqrt((rover_pos[0] - anchors[1][0])**2 + (rover_pos[1] - anchors[1][1])**2),
    numpy.sqrt((rover_pos[0] - anchors[2][0])**2 + (rover_pos[1] - anchors[2][1])**2),
])

def distance_cost(candidate,anchors,ranges):
    total = 0
    for i in range(len(anchors)):
        dist = numpy.sqrt((candidate[0]-anchors[i][0])**2 + (candidate[1]-anchors[i][1])**2)
        total += (dist-ranges[i]) ** 2
    return total
    
noisy_ranges = ranges + numpy.random.normal(0, 5, len(ranges))
result = scipy.optimize.minimize(distance_cost, [0, 0], args=(anchors, noisy_ranges))
print(result.x)
