import time
import collections
import math
import random
import sys
# import webserver
from pyledstrip import LedStrip

#strip = LedStrip(power_limit=0.2)
strip = LedStrip(power_limit=0.2, ip='127.0.0.1')

__LED_PER_METER = 60
__LED_DIST = 1 / __LED_PER_METER

Particle = collections.namedtuple('Particle', ['pos', 'v', 'hue', 'ttl'])


def get_metric(nodes):
	y_values = [value[1] for value in nodes.values()]
	k = [key for key in nodes.keys()]
	y_max = max(y_values)

	max_dist_per_led = 0
	for i in range(1, len(nodes)):
		key_dist = k[i] - k[i - 1]
		x_diff = nodes[k[i]][0] - nodes[k[i - 1]][0]
		y_diff = nodes[k[i]][1] - nodes[k[i - 1]][1]
		dist = math.sqrt(pow(x_diff, 2) + pow(y_diff, 2))
		dist_per_led = dist / key_dist
		max_dist_per_led = max(dist_per_led, max_dist_per_led)
	f = __LED_DIST / max_dist_per_led

	i = 0
	for key, value in nodes.items():
		nodes[key] = (nodes[key][0] * f, (y_max - y_values[i]) * f)
		i = i + 1
	return nodes


def main():
	node_dict = {
		94: (159.0, 69.0), 98: (159.0, 74.5), 100: (158.5, 77.5), 101: (157.5, 79.0), 102: (158.5, 80.5),
		103: (157.0, 82.0), 104: (156.0, 83.0), 105: (158.0, 85.0), 106: (157.0, 86.0), 107: (157.0, 88.0),
		108: (156.5, 89.0), 109: (154.0, 90.0), 110: (154.0, 91.0), 111: (153.5, 92.0), 112: (151.0, 93.0),
		113: (152.5, 95.0), 114: (151.0, 96.0), 115: (150.0, 97.0), 116: (149.5, 98.0), 117: (147.5, 99.0),
		118: (146.0, 100.0), 119: (145.5, 101.0), 120: (146.5, 103.0), 121: (143.0, 102.5), 122: (142.5, 103.5),
		123: (141.5, 105.0), 124: (141.0, 106.0), 125: (140.0, 107.5), 126: (139.0, 108.0), 127: (137.0, 109.0),
		128: (137.0, 110.0), 129: (135.0, 109.5), 130: (134.0, 111.5), 131: (132.5, 111.5), 132: (131.5, 113.0),
		133: (130.0, 112.5), 134: (128.0, 113.0), 135: (127.0, 111.5), 136: (125.0, 114.0), 137: (124.0, 112.5),
		138: (122.0, 113.0), 139: (121.0, 112.0), 140: (119.0, 111.0), 141: (118.0, 111.0), 142: (118.0, 109.0),
		143: (115.5, 110.0), 144: (114.0, 109.0), 145: (112.5, 109.0), 146: (111.5, 108.0), 147: (111.0, 107.0),
		148: (110.0, 106.0), 149: (108.0, 104.5), 150: (107.5, 103.5), 151: (106.0, 102.0), 152: (105.0, 101.0),
		153: (105.0, 100.0), 154: (104.0, 99.0), 155: (102.5, 97.5), 156: (102.0, 96.0), 157: (101.0, 95.0),
		158: (100.5, 94.0), 159: (99.5, 92.5), 160: (99.0, 91.0), 161: (98.0, 89.0), 162: (97.0, 88.0),
		163: (97.5, 87.0), 164: (96.5, 85.0), 165: (96.0, 84.0), 166: (96.0, 83.0), 167: (100.0, 81.0),
		168: (96.0, 79.0), 169: (94.0, 79.0), 170: (93.5, 77.0), 171: (95.0, 75.0), 172: (95.5, 74.0),
		173: (95.0, 72.0), 174: (95.0, 71.0), 175: (93.0, 70.0), 184: (105.0, 66.0), 185: (107.0, 65.0),
		186: (108.0, 66.0), 187: (110.0, 66.0), 188: (111.0, 67.0), 189: (112.0, 67.0), 190: (114.0, 67.0),
		191: (115.0, 67.0), 192: (116.0, 70.0), 193: (117.0, 72.0), 194: (119.5, 68.5), 195: (117.0, 69.5),
		196: (122.5, 69.5), 197: (123.5, 71.0), 198: (125.0, 73.0), 199: (125.0, 74.5), 201: (124.0, 78.0),
		202: (124.0, 79.0), 203: (123.0, 80.0), 204: (122.0, 81.5), 205: (121.5, 83.0), 207: (120.0, 85.0),
		208: (118.0, 86.5), 209: (117.0, 87.0), 210: (116.0, 87.5), 211: (114.0, 88.0), 212: (113.0, 89.0),
		213: (111.0, 88.5), 216: (105.0, 64.0), 232: (96.5, 62.5), 233: (94.0, 64.5), 234: (93.0, 64.0),
		235: (91.0, 65.5), 236: (90.0, 66.0), 237: (88.0, 66.5), 238: (87.0, 67.0), 239: (85.0, 67.0),
		240: (84.0, 68.0), 241: (82.0, 68.5), 242: (81.0, 68.0), 243: (80.0, 69.0), 244: (78.0, 70.0),
		245: (77.0, 71.0), 246: (76.0, 72.0), 247: (74.0, 70.0), 248: (73.0, 70.0), 249: (71.0, 70.0),
		250: (70.0, 70.5), 251: (68.0, 71.0), 252: (67.0, 68.0), 253: (65.0, 71.0), 254: (63.5, 70.0),
		255: (62.5, 69.0), 256: (61.0, 68.0), 257: (60.0, 68.0), 258: (58.0, 67.0), 259: (57.5, 66.0),
		260: (56.5, 65.0), 261: (56.0, 64.0), 262: (55.0, 62.0), 263: (53.0, 61.0), 264: (53.0, 60.0),
		265: (53.0, 58.5), 266: (51.5, 57.0), 267: (51.0, 56.0), 268: (51.0, 54.0), 269: (51.5, 53.0),
		270: (51.0, 51.0), 271: (50.5, 50.0), 272: (50.5, 49.0), 273: (49.5, 47.5), 274: (49.0, 46.0),
		275: (50.0, 44.0), 276: (49.0, 43.0), 277: (49.0, 41.5), 278: (48.5, 40.0), 279: (50.0, 39.0),
		280: (48.0, 38.0), 281: (47.5, 36.0), 282: (46.0, 35.0), 283: (47.5, 33.0), 284: (47.5, 32.0),
		285: (45.0, 31.0), 287: (44.5, 28.0), 288: (44.0, 27.0), 292: (45.0, 21.0), 293: (47.0, 19.0),
		294: (46.5, 18.0), 296: (46.0, 15.0), 297: (44.5, 14.0), 298: (42.0, 12.0)
	}

	nodes = collections.OrderedDict(sorted(node_dict.items()))
	nodes = get_metric(nodes)

	particles = [Particle(300, 0, 60, 15)]

	last_time = time.perf_counter()

	while True:
		strip.clear()
		if len(sys.argv) > 1 and sys.argv[1] == 'm':
			min_val = 5000
			max_val = 0
			for value in nodes.values():
				min_val = min(value[1], min_val)
				max_val = max(value[1], max_val)
			for key, value in nodes.items():
				strip.add_hsv(key, value[1] / (max_val - min_val), 1, 1)

		# create particle
		if random.randrange(0, 50) < 1:
			particles.append(Particle(300, random.randrange(0, 200) / 100, random.randrange(0, 360), 15))
		web_particles = []  # webserver.step()
		for web_particle in web_particles:
			if web_particle.pos is not None and web_particle.v is not None:
				if web_particle.hue:
					particles.append(Particle(300, web_particle.v * 2, web_particle.pos, 15))
				else:
					particles.append(Particle(1, -web_particle.v * 2, web_particle.pos, 15))

		now = time.perf_counter()
		for i, particle in enumerate(particles):
			radius = 0
			height = 0

			next_key = next(iter(nodes.keys()))
			for key in nodes.keys():
				prev_key = next_key
				next_key = key
				if next_key >= particle.pos > prev_key:
					height = (nodes[next_key][1] - nodes[prev_key][1])
					radius = abs(prev_key - next_key) * __LED_DIST
					break

			if radius == 0:
				radius = 0.00001

			a = (9.81 * max(min(height / radius, 1), -1)) if radius is not 0 else 0
			# friction
			# a = a - min(0.02*9.81 * wagon[1], 0.02*9.81)
			if particle[1] > 0:
				a = a - 0.088 * 9.81 * math.cos(math.asin(max(min(height / radius, 1), -1)))
			elif particle[1] < 0:
				a = a + 0.088 * 9.81 * math.cos(math.asin(max(min(height / radius, 1), -1)))
			t = now - last_time

			v = particle.v + a * t
			# v = v - v * 0.05 * t

			new_pos = particle.pos - (v * t) * __LED_PER_METER

			if not 300 >= new_pos >= 0 or particle.hue <= 0:
				del particles[i]
			else:
				strip.add_hsv(new_pos, particle.hue / 360, 1, particle.ttl / 3)
				particles[i] = Particle(new_pos, v, particle.hue, particle.ttl - t)

		last_time = now
		strip.transmit()
		time.sleep(0.01)


if __name__ == '__main__':
	main()
