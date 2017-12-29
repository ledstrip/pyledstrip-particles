#!/usr/bin/env python3
import argparse
import time
import collections
import math
import random
import sys
import webserver
from pyledstrip import LedStrip

__LED_PER_METER = 60
__LED_DIST = 1 / __LED_PER_METER
__DEFAULT_TTL = 2


class Particle:
	pos = None
	v = None
	hue = None
	ttl = None
	mass = None

	def __init__(self, pos, v, hue, ttl, mass):
		self.pos = pos
		self.v = v
		self.hue = hue
		self.ttl = ttl
		self.mass = mass


def get_metric_nodes(nodes):
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
	f = __LED_DIST / max_dist_per_led / 1.5

	i = 0
	for key, value in nodes.items():
		nodes[key] = (nodes[key][0] * f, (y_max - y_values[i]) * f)
		i = i + 1
	return nodes


def within(a, b, tolerance=1.0):
	if not abs(a.pos - b.pos) < tolerance:
		return False
	return math.copysign(1, a.v) != math.copysign(1, b.v)


def collide(a, b):
	# v1' = (m1*v1 + m2 * (2*v2 - v1)) / (m1 + m2)
	# v2' = (m2*v2 + m1 * (2*v1 - v2)) / (m1 + m2)
	v1, v2 = a.v, b.v
	a.v = (a.mass * v1 + b.mass * (2 * v2 - v1)) / (a.mass + b.mass)
	b.v = (b.mass * v2 + a.mass * (2 * v1 - v2)) / (a.mass + b.mass)


oben_gefiltert = {
	0: (69.625, 231.0625), 1: (71.625, 229.6875), 2: (74.5625, 228.0), 3: (77.8125, 226.8125), 4: (81.3125, 225.875),
	5: (84.96875, 224.65625), 6: (88.486111111111114, 223.07986111111111), 7: (91.697916666666671, 221.26041666666669),
	8: (94.826388888888886, 219.23263888888889), 9: (98.055555555555571, 217.05555555555554),
	10: (101.33333333333334, 214.83333333333331), 11: (104.61111111111111, 212.61111111111111),
	12: (107.8888888888889, 210.38888888888889), 13: (111.16666666666667, 208.16666666666666),
	14: (114.44444444444444, 205.94444444444446), 15: (117.67361111111111, 203.79861111111111),
	16: (120.55208333333334, 202.02083333333331), 17: (122.67013888888889, 200.88888888888889),
	18: (124.3125, 200.09375), 19: (126.28125, 199.03125), 20: (128.6875, 197.78125), 21: (131.125, 196.84375),
	22: (133.5, 196.25), 23: (135.875, 195.75), 24: (138.28125, 195.25), 25: (140.625, 194.75), 26: (142.625, 194.3125),
	27: (144.65625, 194.09375), 28: (148.125, 194.1875), 29: (153.375, 194.5), 30: (157.65625, 194.8125),
	31: (157.71875, 195.34375), 32: (154.125, 196.9375), 33: (149.8125, 199.5), 34: (145.90625, 201.75),
	35: (142.0, 203.3125), 36: (138.0625, 204.75), 37: (134.28125, 206.3125), 38: (130.5625, 207.9375),
	39: (126.6875, 209.375), 40: (122.625, 210.625), 41: (118.59375, 212.0), 42: (114.71875, 213.125),
	43: (110.8125, 213.25), 44: (106.8125, 212.625), 45: (102.875, 212.125), 46: (99.09375, 212.0),
	47: (95.65625, 212.09375), 48: (92.5, 212.53125), 49: (89.21875, 213.34375), 50: (86.15625, 213.9375),
	51: (84.15625, 213.53125), 52: (83.25, 211.96875), 53: (83.40625, 209.78125), 54: (85.15625, 207.53125),
	55: (88.125, 205.3125), 56: (91.1875, 203.0), 57: (94.03125, 200.625), 58: (96.8125, 198.28125),
	59: (99.46875, 196.03125), 60: (102.0625, 193.75), 61: (104.84375, 191.1875), 62: (107.875, 188.5),
	63: (110.84375, 186.03125), 64: (113.375, 183.6875), 65: (115.625, 181.3125), 66: (118.0625, 179.0),
	67: (120.6875, 176.6875), 68: (123.25, 174.28125), 69: (125.625, 171.78125), 70: (127.75, 169.0625),
	71: (129.9375, 166.3125), 72: (132.453125, 163.921875), 73: (134.96875, 161.6875), 74: (137.234375, 159.203125),
	75: (139.3125, 156.5), 76: (141.203125, 153.734375), 77: (142.9375, 151.0), 78: (144.640625, 148.43229166666666),
	79: (146.34375, 145.90625), 80: (147.96875, 143.05208333333334), 81: (149.53125, 139.91666666666669),
	82: (151.09375, 136.96875), 83: (152.49652777777777, 134.43402777777777),
	84: (153.57291666666669, 132.19791666666666), 85: (154.47222222222223, 130.14930555555554),
	86: (155.38888888888889, 128.22222222222223), 87: (156.33333333333331, 126.33333333333334),
	88: (157.27777777777777, 124.44444444444444), 89: (158.22222222222223, 122.55555555555556),
	90: (159.16666666666666, 120.66666666666667), 91: (160.11111111111111, 118.77777777777777),
	92: (160.99652777777777, 117.00694444444444), 93: (161.64583333333331, 115.82552083333334),
	94: (161.94097222222223, 115.82118055555556), 95: (162.0, 116.9921875), 96: (162.0, 118.75),
	97: (162.0, 120.6484375), 98: (162.0, 122.640625), 99: (161.97916666666666, 124.84114583333334),
	100: (161.875, 127.40625), 101: (161.64583333333334, 130.40104166666666),
	102: (161.35416666666669, 133.64583333333331), 103: (161.125, 136.875),
	104: (161.05208333333334, 140.01041666666666), 105: (161.15625, 143.125), 106: (161.34375, 146.25),
	107: (161.46875, 149.5), 108: (161.53125, 153.03125), 109: (161.71875, 156.6875), 110: (162.3125, 160.25),
	111: (163.59375, 163.6875), 112: (165.625, 166.9375), 113: (168.125, 170.0), 114: (170.65625, 173.0625),
	115: (173.0, 176.28125), 116: (175.4375, 179.5), 117: (178.3125, 182.4375), 118: (181.4375, 185.0625),
	119: (184.5625, 187.40625), 120: (187.8125, 189.5625), 121: (191.3125, 191.65625), 122: (195.0625, 193.375),
	123: (198.9375, 194.4375), 124: (202.6875, 195.125), 125: (206.3125, 195.65625), 126: (210.0625, 195.9375),
	127: (213.9375, 196.0625), 128: (217.625, 196.375), 129: (220.9375, 197.125), 130: (224.0625, 198.25),
	131: (227.3125, 199.3125), 132: (230.78125, 199.84375), 133: (234.5, 199.78125), 134: (238.5, 199.3125),
	135: (242.5, 198.6875), 136: (246.28125, 198.03125), 137: (250.0625, 197.03125), 138: (253.9375, 195.5),
	139: (257.6875, 193.75), 140: (261.25, 191.875), 141: (264.59375, 189.59375), 142: (267.375, 186.75),
	143: (269.4375, 183.5), 144: (271.0625, 180.1875), 145: (272.28125, 177.03125), 146: (272.84375, 173.9375),
	147: (272.8125, 170.6875), 148: (272.4375, 167.25), 149: (271.75, 163.75), 150: (270.65625, 160.3125),
	151: (269.25, 157.0625), 152: (267.6875, 153.96875), 153: (265.9375, 150.84375), 154: (264.0, 147.625),
	155: (262.0, 144.375), 156: (260.0, 141.21875), 157: (258.0, 138.34375), 158: (256.0, 135.6875),
	159: (254.0, 132.9375), 160: (252.0, 130.0), 161: (250.0, 127.0), 162: (248.0, 124.0), 163: (246.03125, 121.0625),
	164: (244.15625, 118.3125), 165: (242.3125, 115.6875), 166: (240.375, 112.96875), 167: (238.46875, 110.125),
	168: (236.71875, 107.25), 169: (234.9375, 104.4375), 170: (233.0, 101.78125), 171: (231.03125, 99.25),
	172: (229.125, 96.6875), 173: (227.25, 93.96875), 174: (225.4375, 91.1875), 175: (223.71875, 88.5),
	176: (221.9375, 85.84375), 177: (220.0, 83.15625), 178: (218.0, 80.5), 179: (216.0, 77.875),
	180: (213.9375, 75.34375), 181: (211.6875, 73.125), 182: (209.25, 71.4375), 183: (206.75, 70.53125),
	184: (204.3125, 70.6875), 185: (202.03125, 71.96875), 186: (199.90625, 74.09375), 187: (197.8125, 76.59375),
	188: (195.4375, 79.0625), 189: (192.75, 81.40625), 190: (190.40625, 83.8125), 191: (188.75, 86.4375),
	192: (187.3125, 89.25), 193: (185.90625, 92.25), 194: (184.59375, 95.5), 195: (182.90625, 98.625),
	196: (180.8125, 101.40625), 197: (178.875, 104.3125), 198: (177.125, 107.28125), 199: (175.53125, 109.96875),
	200: (174.3125, 112.65625), 201: (173.40625, 115.53125), 202: (172.34375, 118.5), 203: (170.4375, 121.28125),
	204: (167.78125, 123.71875), 205: (165.2890625, 126.265625), 206: (163.203125, 129.0625),
	207: (161.0703125, 131.671875), 208: (158.75, 134.0), 209: (156.3359375, 136.203125), 210: (153.765625, 138.25),
	211: (150.9609375, 140.078125), 212: (148.0, 141.65625), 213: (145.0, 143.0), 214: (141.9375, 144.3125),
	215: (138.6875, 145.625), 216: (135.3125, 146.59375), 217: (132.0625, 147.125), 218: (129.0, 147.5),
	219: (125.9375, 147.75), 220: (122.71875, 147.65625), 221: (119.4375, 147.28125), 222: (116.25, 146.875),
	223: (113.125, 146.5), 224: (110.03125, 146.0), 225: (107.0, 144.96875), 226: (104.0625, 143.25),
	227: (101.3125, 141.375), 228: (98.75, 139.625), 229: (96.25, 137.625), 230: (93.75, 135.25),
	231: (91.3125, 132.75), 232: (89.0625, 130.25), 233: (87.0, 127.71875), 234: (85.0, 125.125), 235: (83.0, 122.5),
	236: (81.03125, 119.8125), 237: (79.1875, 116.96875), 238: (77.5, 114.0), 239: (75.875, 111.0),
	240: (74.21875, 108.0), 241: (72.5, 105.03125), 242: (71.0, 102.1875), 243: (70.375, 99.625), 244: (71.1875, 97.5),
	245: (73.5, 95.84375), 246: (76.6875, 95.0625), 247: (79.9375, 96.0), 248: (83.0, 98.0), 249: (86.0, 99.0),
	250: (89.03125, 98.78125), 251: (92.1875, 99.0), 252: (95.4375, 100.25), 253: (98.5, 101.75),
	254: (101.34375, 102.9375), 255: (104.375, 103.8125), 256: (107.6875, 104.40625), 257: (110.96875, 104.625),
	258: (114.1875, 104.4375), 259: (117.53125, 103.875), 260: (120.875, 102.65625), 261: (123.84375, 100.4375),
	262: (126.34375, 97.59375), 263: (128.53125, 94.75), 264: (130.59375, 92.03125), 265: (132.9375, 89.5625),
	266: (135.625, 87.3125), 267: (138.03125, 84.53125), 268: (139.71875, 81.03125), 269: (141.25, 77.8125),
	270: (143.84375, 75.4375), 271: (147.40625, 73.28125), 272: (150.3125, 70.5625), 273: (152.0, 67.28125),
	274: (153.375, 63.875), 275: (155.0, 60.46875), 276: (156.6875, 57.0625), 277: (158.375, 53.84375),
	278: (160.4375, 51.0), 279: (163.125, 48.71875), 280: (166.375, 47.09375), 281: (170.0, 45.875),
	282: (173.65625, 44.84375), 283: (177.125, 44.03125), 284: (180.5, 43.21875), 285: (183.8125, 41.9375),
	286: (186.96875, 40.09375), 287: (189.9375, 37.96875), 288: (192.625, 35.625), 289: (195.0, 32.9375),
	290: (197.34375, 30.0), 291: (199.875, 27.0), 292: (202.4375, 24.0), 293: (204.875, 21.0),
	294: (207.34375, 18.0625), 295: (210.09375, 15.4375), 296: (213.15625, 13.4375), 297: (216.375, 12.125),
	298: (219.4375, 11.375), 299: (221.5, 11.0625)
}


def main(args):
	strip = LedStrip(args=args)

	node_dict = oben_gefiltert

	nodes = collections.OrderedDict(sorted(node_dict.items()))
	nodes = get_metric_nodes(nodes)

	# initialize particles with one particle
	particles = [Particle(300, 1, 0.4, __DEFAULT_TTL, 1)]

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
				strip.add_hsv(key, value[1] / (max_val - min_val), 1, 0.2)

		# create particle
		spawn = random.random()
		if spawn < 0.005:
			particles.append(
				Particle(pos=0, v=random.uniform(-2.5, -1), hue=random.random(), ttl=__DEFAULT_TTL, mass=1)
			)
		elif spawn >= 0.995:
			particles.append(
				Particle(pos=300, v=random.uniform(0.05, 0.5), hue=random.random(), ttl=__DEFAULT_TTL, mass=1)
			)
		web_particles = webserver.step()
		for web_particle in web_particles:
			if web_particle[0] is not None and web_particle[1] is not None:
				if web_particle[2]:
					particles.append(
						Particle(pos=300, v=web_particle[1], hue=web_particle[0], ttl=__DEFAULT_TTL, mass=1)
					)
				else:
					particles.append(
						Particle(pos=1, v=-web_particle[1], hue=web_particle[0], ttl=__DEFAULT_TTL, mass=1)
					)

		now = time.perf_counter()
		particles = sorted(particles, key=lambda p: p.pos)
		for i, particle in enumerate(particles):
			radius = 0
			height = 0

			# Collision detection
			if i > 0 and i < (len(particles) - 1):
				left = particles[i - 1]
				right = particles[i + 1]
				if within(left, particle):
					collide(left, particle)
				if within(right, particle):
					collide(particle, right)

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

			a_slope = (9.81 * max(min(height / radius, 1), -1)) if radius is not 0 else 0
			a_friction = math.copysign(0.01 * 9.81 * math.cos(math.asin(max(min(height / radius, 1), -1))), particle.v)

			a = a_slope - a_friction
			t = now - last_time
			v = particle.v + a * t

			new_pos = particle.pos - (v * t) * __LED_PER_METER

			if not 300 >= new_pos >= 0 or particle.ttl <= 0:
				del particles[i]
			else:
				strip.add_hsv(new_pos, #min(math.pow(abs(v) / 2, 2), 0.9), 1,
						particle.hue, 1,
							  max(math.pow(abs(v) / 2, 2), 0.1) * min(particle.ttl / 3, 1))
				if abs(v) < 0.1:
					new_ttl = particle.ttl - t
					particles[i] = Particle(pos=new_pos, v=v, hue=particle.hue, ttl=new_ttl, mass=particle.mass)
				else:
					particles[i] = Particle(pos=new_pos, v=v, hue=particle.hue, ttl=__DEFAULT_TTL, mass=particle.mass)

		last_time = now
		strip.transmit()
		time.sleep(0.01)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Gravity-based LED particle simulation')
	LedStrip.add_arguments(parser)
	main(parser.parse_args())
