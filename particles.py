#!/usr/bin/env python3
import argparse
import time
import collections
import math
import random
import sys
import webserver
from pyledstrip import LedStrip

_LED_PER_METER = 60
_LED_DIST = 1 / _LED_PER_METER
_DEFAULT_TTL = 2


class Particle:
	pos = None
	v = None
	hue = None
	ttl = None
	mass = None
	width = None

	def __init__(self, pos, v, hue, ttl=_DEFAULT_TTL, radius=1):
		self.pos = pos
		self.v = v
		self.hue = hue
		self.ttl = ttl
		self.radius = radius
		self.mass = 2*radius


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
	f = _LED_DIST / max_dist_per_led / 1.5

	i = 0
	for key, value in nodes.items():
		nodes[key] = (nodes[key][0] * f, (y_max - y_values[i]) * f)
		i = i + 1
	return nodes


def within(a, b, tolerance=1.0):
	if not abs(a.pos - b.pos) < (a.radius + b.radius):
		return False
	return math.copysign(1, a.v) != math.copysign(1, b.v)


def collide(a, b):
	# v1' = (m1*v1 + m2 * (2*v2 - v1)) / (m1 + m2)
	# v2' = (m2*v2 + m1 * (2*v1 - v2)) / (m1 + m2)
	v1, v2 = a.v, b.v
	a.v = (a.mass * v1 + b.mass * (2 * v2 - v1)) / (a.mass + b.mass)
	b.v = (b.mass * v2 + a.mass * (2 * v1 - v2)) / (a.mass + b.mass)


oben_gefiltert = {0: (86.0, 217.125), 1: (84.1875, 215.9375), 2: (81.348214285714278, 214.43303571428572), 3: (78.651785714285708, 213.41071428571431), 4: (76.669642857142861, 212.98660714285717), 5: (75.142857142857139, 212.85714285714283), 6: (73.714285714285708, 212.78571428571428), 7: (72.285714285714278, 212.71428571428572), 8: (70.857142857142861, 212.64285714285714), 9: (69.517857142857139, 212.45089285714286), 10: (68.848214285714292, 211.68303571428572), 11: (69.683035714285722, 209.91071428571428), 12: (71.65625, 207.59375), 13: (73.5625, 205.84375), 14: (75.375, 205.09375), 15: (77.65625, 204.78125), 16: (80.25, 204.28125), 17: (82.875, 203.34375), 18: (85.4375, 201.84375), 19: (87.96875, 200.03125), 20: (90.65625, 198.40625), 21: (93.3125, 196.6875), 22: (95.75, 194.4375), 23: (98.34375, 192.125), 24: (101.0625, 189.9375), 25: (103.46875, 187.46875), 26: (105.6875, 184.875), 27: (108.25, 182.71875), 28: (111.5, 181.3125), 29: (114.90625, 180.125), 30: (117.5625, 177.8125), 31: (119.75, 174.28125), 32: (122.4375, 171.4375), 33: (125.6875, 170.5), 34: (128.9375, 170.75), 35: (131.9375, 171.28125), 36: (134.59375, 171.9375), 37: (136.84375, 172.78125), 38: (139.03125, 173.65625), 39: (141.5, 174.1875), 40: (144.03125, 174.15625), 41: (146.46875, 173.90625), 42: (149.03125, 174.09375), 43: (151.625, 174.78125), 44: (153.9375, 175.40625), 45: (156.0625, 175.875), 46: (158.3125, 176.5625), 47: (160.6875, 177.5), 48: (162.96875, 178.375), 49: (165.1875, 178.90625), 50: (167.53125, 179.1875), 51: (170.0, 179.5), 52: (172.5625, 179.875), 53: (175.3125, 180.28125), 54: (178.21875, 180.6875), 55: (181.125, 180.9375), 56: (184.03125, 180.9375), 57: (187.0, 180.625), 58: (189.9375, 179.875), 59: (192.5625, 178.625), 60: (194.4375, 176.9375), 61: (195.21875, 174.9375), 62: (194.9375, 172.625), 63: (193.9375, 170.0), 64: (193.0, 167.3125), 65: (193.09375, 164.6875), 66: (194.03125, 162.0), 67: (194.625, 159.375), 68: (194.3125, 157.0), 69: (193.4375, 154.65625), 70: (192.84375, 152.125), 71: (193.0, 149.5), 72: (193.4375, 146.8125), 73: (193.75, 144.03125), 74: (193.9375, 141.25), 75: (193.875, 138.4375), 76: (193.3125, 135.625), 77: (192.3125, 133.0625), 78: (191.375, 130.625), 79: (190.75, 127.9375), 80: (190.3125, 125.0), 81: (189.96875, 122.0), 82: (189.53125, 119.0), 83: (188.9375, 116.0), 84: (188.40625, 113.0625), 85: (187.53125, 110.25), 86: (185.34375, 107.375), 87: (182.375, 104.25), 88: (180.71875, 101.0), 89: (181.25, 97.6875), 90: (182.6875, 94.3125), 91: (183.4375, 91.0625), 92: (183.3125, 88.0), 93: (183.0, 84.9375), 94: (182.6875, 81.6875), 95: (182.25, 78.0), 96: (181.375, 73.6875), 97: (179.4375, 69.46875), 98: (177.0625, 66.34375), 99: (176.28125, 64.28125), 100: (178.0, 63.1875), 101: (181.25, 63.40625), 102: (184.75, 64.5625), 103: (187.96875, 65.75), 104: (191.0, 66.59375), 105: (194.0, 67.25), 106: (197.0, 67.9375), 107: (200.0, 68.78125), 108: (203.0, 69.78125), 109: (206.0625, 70.875), 110: (209.375, 71.90625), 111: (213.0, 72.5625), 112: (216.625, 72.375), 113: (219.9375, 71.0625), 114: (223.03125, 69.6875), 115: (226.125, 70.125), 116: (229.21875, 72.125), 117: (232.25, 73.625), 118: (235.21875, 73.9375), 119: (238.0625, 73.6875), 120: (240.65625, 73.125), 121: (242.8125, 71.8125), 122: (244.15625, 69.375), 123: (244.3125, 66.75), 124: (243.375, 65.28125), 125: (241.6875, 64.8125), 126: (239.28125, 64.53125), 127: (236.25, 64.375), 128: (232.96875, 64.90625), 129: (229.6875, 66.78125), 130: (226.90625, 69.65625), 131: (225.25, 72.21875), 132: (224.53125, 74.0625), 133: (224.0625, 75.84375), 134: (223.34375, 77.9375), 135: (222.25, 80.25), 136: (221.09375, 82.625), 137: (220.21875, 85.0625), 138: (219.625, 87.59375), 139: (219.0, 90.125), 140: (218.15625, 92.6875), 141: (217.40625, 95.375), 142: (217.1875, 98.28125), 143: (218.0, 101.53125), 144: (220.3125, 104.75), 145: (223.5, 107.4375), 146: (226.3125, 109.75), 147: (228.5, 112.0), 148: (230.5625, 114.3125), 149: (232.71875, 116.71875), 150: (234.75, 119.21875), 151: (236.53125, 121.9375), 152: (238.3125, 124.75), 153: (240.09375, 127.46875), 154: (241.3125, 130.34375), 155: (241.53125, 133.3125), 156: (240.9375, 135.875), 157: (239.875, 137.875), 158: (238.1875, 138.625), 159: (235.5625, 136.625), 160: (232.375, 132.3125), 161: (229.4375, 128.1875), 162: (227.0625, 125.25), 163: (225.0625, 122.75), 164: (223.25, 120.3125), 165: (221.375, 118.09375), 166: (219.25, 116.125), 167: (217.09375, 114.125), 168: (215.125, 111.8125), 169: (213.1875, 109.34375), 170: (211.1875, 107.0625), 171: (209.375, 104.9375), 172: (207.875, 102.65625), 173: (206.4375, 100.125), 174: (204.8125, 97.5625), 175: (202.96875, 95.15625), 176: (201.0, 92.90625), 177: (199.0625, 90.6875), 178: (197.25, 88.3125), 179: (195.4375, 85.84375), 180: (193.53125, 83.5), 181: (191.65625, 81.25), 182: (189.9375, 79.0), 183: (188.40625, 76.8125), 184: (186.96875, 74.875), 185: (185.375, 71.90625), 186: (183.28125, 65.21875), 187: (180.5625, 56.40625), 188: (177.375, 52.1875), 189: (173.90625, 56.46875), 190: (170.90625, 65.84375), 191: (169.03125, 73.96875), 192: (167.4375, 78.25), 193: (165.5625, 80.1875), 194: (164.46875, 81.9375), 195: (164.78125, 84.6875), 196: (165.25, 87.9375), 197: (164.0, 90.625), 198: (161.40625, 92.9375), 199: (159.78125, 95.4375), 200: (159.6875, 98.0), 201: (159.75, 100.5625), 202: (158.9375, 103.125), 203: (157.1875, 105.625), 204: (155.1875, 108.375), 205: (153.6875, 111.4375), 206: (152.625, 114.5), 207: (151.25, 117.375), 208: (149.3125, 119.84375), 209: (147.375, 121.9375), 210: (145.8125, 124.1875), 211: (144.4375, 127.0), 212: (142.71875, 130.15625), 213: (140.25, 132.875), 214: (137.25, 134.4375), 215: (134.0625, 135.03125), 216: (130.71875, 135.375), 217: (127.3125, 135.46875), 218: (124.0625, 134.875), 219: (121.0, 133.71875), 220: (118.0, 132.3125), 221: (115.03125, 130.90625), 222: (112.125, 129.6875), 223: (109.25, 127.9375), 224: (106.4375, 124.75), 225: (103.71875, 121.0625), 226: (101.0, 118.75), 227: (98.1875, 117.9375), 228: (95.1875, 117.03125), 229: (92.1875, 114.875), 230: (89.59375, 111.9375), 231: (87.3125, 109.125), 232: (85.0, 106.65625), 233: (82.375, 104.6875), 234: (78.90625, 103.1875), 235: (74.875, 101.6875), 236: (71.8125, 99.8125), 237: (70.4375, 97.625), 238: (70.0, 95.875), 239: (69.75, 94.875), 240: (69.625, 93.75), 241: (70.625, 92.8125), 242: (74.364583333333329, 94.104166666666671), 243: (79.9375, 97.437500000000014), 244: (84.010416666666671, 100.14583333333333), 245: (85.614583333333343, 101.29166666666666), 246: (86.34375, 101.875), 247: (87.416666666666671, 102.64583333333333), 248: (89.3125, 103.78125), 249: (91.875, 105.125), 250: (94.625, 106.53125), 251: (97.375, 108.0), 252: (100.09375, 109.46875), 253: (102.71875, 110.84375), 254: (105.3125, 112.15625), 255: (108.0, 113.5), 256: (110.6875, 114.84375), 257: (113.3125, 116.09375), 258: (116.0625, 117.1875), 259: (118.96875, 118.1875), 260: (121.8125, 119.3125), 261: (124.4375, 120.5), 262: (126.8125, 121.40625), 263: (129.0, 121.96875), 264: (131.1875, 122.09375), 265: (133.375, 121.1875), 266: (135.0, 119.03125), 267: (135.40625, 116.34375), 268: (134.5625, 113.78125), 269: (133.0, 111.4375), 270: (131.28125, 109.28125), 271: (129.625, 107.25), 272: (128.03125, 105.34375), 273: (126.3125, 103.75), 274: (124.09375, 102.21875), 275: (121.625, 100.0), 276: (119.71875, 97.25), 277: (118.3125, 94.8125), 278: (116.375, 92.625), 279: (113.4375, 90.25), 280: (110.375, 87.75), 281: (108.0625, 85.3125), 282: (106.0, 83.0625), 283: (103.40625, 81.0625), 284: (100.21875, 79.3125), 285: (96.65625, 77.75), 286: (93.375, 76.0625), 287: (91.15625, 73.6875), 288: (89.78125, 70.625), 289: (88.28125, 67.8125), 290: (86.25, 65.6875), 291: (84.0625, 63.625), 292: (81.9375, 61.375), 293: (79.75, 59.3125), 294: (77.625, 57.4375), 295: (75.5625, 55.6875), 296: (73.03125, 54.28125), 297: (70.1875, 52.8125), 298: (68.125, 50.8125), 299: (67.28125, 49.15625), 300: (69.625, 49.15625), 301: (71.625, 47.78125), 302: (74.5625, 46.09375), 303: (77.8125, 44.90625), 304: (81.3125, 43.96875), 305: (84.96875, 42.75), 306: (88.486111111111114, 41.173611111111114), 307: (91.697916666666671, 39.354166666666686), 308: (94.826388888888886, 37.326388888888886), 309: (98.055555555555571, 35.149305555555543), 310: (101.33333333333334, 32.927083333333314), 311: (104.61111111111111, 30.704861111111114), 312: (107.8888888888889, 28.482638888888886), 313: (111.16666666666667, 26.260416666666657), 314: (114.44444444444444, 24.038194444444457), 315: (117.67361111111111, 21.892361111111114), 316: (120.55208333333334, 20.114583333333314), 317: (122.67013888888889, 18.982638888888886), 318: (124.3125, 18.1875), 319: (126.28125, 17.125), 320: (128.6875, 15.875), 321: (131.125, 14.9375), 322: (133.5, 14.34375), 323: (135.875, 13.84375), 324: (138.28125, 13.34375), 325: (140.625, 12.84375), 326: (142.625, 12.40625), 327: (144.65625, 12.1875), 328: (148.125, 12.28125), 329: (153.375, 12.59375), 330: (157.65625, 12.90625), 331: (157.71875, 13.4375), 332: (154.125, 15.03125), 333: (149.8125, 17.59375), 334: (145.90625, 19.84375), 335: (142.0, 21.40625), 336: (138.0625, 22.84375), 337: (134.28125, 24.40625), 338: (130.5625, 26.03125), 339: (126.6875, 27.46875), 340: (122.625, 28.71875), 341: (118.59375, 30.09375), 342: (114.71875, 31.21875), 343: (110.8125, 31.34375), 344: (106.8125, 30.71875), 345: (102.875, 30.21875), 346: (99.09375, 30.09375), 347: (95.65625, 30.1875), 348: (92.5, 30.625), 349: (89.21875, 31.4375), 350: (86.15625, 32.03125), 351: (84.15625, 31.625), 352: (83.25, 30.0625), 353: (83.40625, 27.875), 354: (85.15625, 25.625), 355: (88.125, 23.40625), 356: (91.1875, 21.09375), 357: (94.03125, 18.71875), 358: (96.8125, 16.375), 359: (99.46875, 14.125), 360: (102.0625, 11.84375), 361: (104.84375, 9.28125), 362: (107.875, 6.59375), 363: (110.84375, 4.125), 364: (113.375, 1.78125), 365: (115.625, -0.59375), 366: (118.0625, -2.90625), 367: (120.6875, -5.21875), 368: (123.25, -7.625), 369: (125.625, -10.125), 370: (127.75, -12.84375), 371: (129.9375, -15.59375), 372: (132.453125, -17.984375), 373: (134.96875, -20.21875), 374: (137.234375, -22.703125), 375: (139.3125, -25.40625), 376: (141.203125, -28.171875), 377: (142.9375, -30.90625), 378: (144.640625, -33.473958333333343), 379: (146.34375, -36.0), 380: (147.96875, -38.854166666666657), 381: (149.53125, -41.989583333333314), 382: (151.09375, -44.9375), 383: (152.49652777777777, -47.472222222222229), 384: (153.57291666666669, -49.708333333333343), 385: (154.47222222222223, -51.756944444444457), 386: (155.38888888888889, -53.684027777777771), 387: (156.33333333333331, -55.572916666666657), 388: (157.27777777777777, -57.461805555555557), 389: (158.22222222222223, -59.350694444444443), 390: (159.16666666666666, -61.239583333333329), 391: (160.11111111111111, -63.128472222222229), 392: (160.99652777777777, -64.899305555555557), 393: (161.64583333333331, -66.080729166666657), 394: (161.94097222222223, -66.085069444444443), 395: (162.0, -64.9140625), 396: (162.0, -63.15625), 397: (162.0, -61.2578125), 398: (162.0, -59.265625), 399: (161.97916666666666, -57.065104166666657), 400: (161.875, -54.5), 401: (161.64583333333334, -51.505208333333343), 402: (161.35416666666669, -48.260416666666686), 403: (161.125, -45.03125), 404: (161.05208333333334, -41.895833333333343), 405: (161.15625, -38.78125), 406: (161.34375, -35.65625), 407: (161.46875, -32.40625), 408: (161.53125, -28.875), 409: (161.71875, -25.21875), 410: (162.3125, -21.65625), 411: (163.59375, -18.21875), 412: (165.625, -14.96875), 413: (168.125, -11.90625), 414: (170.65625, -8.84375), 415: (173.0, -5.625), 416: (175.4375, -2.40625), 417: (178.3125, 0.53125), 418: (181.4375, 3.15625), 419: (184.5625, 5.5), 420: (187.8125, 7.65625), 421: (191.3125, 9.75), 422: (195.0625, 11.46875), 423: (198.9375, 12.53125), 424: (202.6875, 13.21875), 425: (206.3125, 13.75), 426: (210.0625, 14.03125), 427: (213.9375, 14.15625), 428: (217.625, 14.46875), 429: (220.9375, 15.21875), 430: (224.0625, 16.34375), 431: (227.3125, 17.40625), 432: (230.78125, 17.9375), 433: (234.5, 17.875), 434: (238.5, 17.40625), 435: (242.5, 16.78125), 436: (246.28125, 16.125), 437: (250.0625, 15.125), 438: (253.9375, 13.59375), 439: (257.6875, 11.84375), 440: (261.25, 9.96875), 441: (264.59375, 7.6875), 442: (267.375, 4.84375), 443: (269.4375, 1.59375), 444: (271.0625, -1.71875), 445: (272.28125, -4.875), 446: (272.84375, -7.96875), 447: (272.8125, -11.21875), 448: (272.4375, -14.65625), 449: (271.75, -18.15625), 450: (270.65625, -21.59375), 451: (269.25, -24.84375), 452: (267.6875, -27.9375), 453: (265.9375, -31.0625), 454: (264.0, -34.28125), 455: (262.0, -37.53125), 456: (260.0, -40.6875), 457: (258.0, -43.5625), 458: (256.0, -46.21875), 459: (254.0, -48.96875), 460: (252.0, -51.90625), 461: (250.0, -54.90625), 462: (248.0, -57.90625), 463: (246.03125, -60.84375), 464: (244.15625, -63.59375), 465: (242.3125, -66.21875), 466: (240.375, -68.9375), 467: (238.46875, -71.78125), 468: (236.71875, -74.65625), 469: (234.9375, -77.46875), 470: (233.0, -80.125), 471: (231.03125, -82.65625), 472: (229.125, -85.21875), 473: (227.25, -87.9375), 474: (225.4375, -90.71875), 475: (223.71875, -93.40625), 476: (221.9375, -96.0625), 477: (220.0, -98.75), 478: (218.0, -101.40625), 479: (216.0, -104.03125), 480: (213.9375, -106.5625), 481: (211.6875, -108.78125), 482: (209.25, -110.46875), 483: (206.75, -111.375), 484: (204.3125, -111.21875), 485: (202.03125, -109.9375), 486: (199.90625, -107.8125), 487: (197.8125, -105.3125), 488: (195.4375, -102.84375), 489: (192.75, -100.5), 490: (190.40625, -98.09375), 491: (188.75, -95.46875), 492: (187.3125, -92.65625), 493: (185.90625, -89.65625), 494: (184.59375, -86.40625), 495: (182.90625, -83.28125), 496: (180.8125, -80.5), 497: (178.875, -77.59375), 498: (177.125, -74.625), 499: (175.53125, -71.9375), 500: (174.3125, -69.25), 501: (173.40625, -66.375), 502: (172.34375, -63.40625), 503: (170.4375, -60.625), 504: (167.78125, -58.1875), 505: (165.2890625, -55.640625), 506: (163.203125, -52.84375), 507: (161.0703125, -50.234375), 508: (158.75, -47.90625), 509: (156.3359375, -45.703125), 510: (153.765625, -43.65625), 511: (150.9609375, -41.828125), 512: (148.0, -40.25), 513: (145.0, -38.90625), 514: (141.9375, -37.59375), 515: (138.6875, -36.28125), 516: (135.3125, -35.3125), 517: (132.0625, -34.78125), 518: (129.0, -34.40625), 519: (125.9375, -34.15625), 520: (122.71875, -34.25), 521: (119.4375, -34.625), 522: (116.25, -35.03125), 523: (113.125, -35.40625), 524: (110.03125, -35.90625), 525: (107.0, -36.9375), 526: (104.0625, -38.65625), 527: (101.3125, -40.53125), 528: (98.75, -42.28125), 529: (96.25, -44.28125), 530: (93.75, -46.65625), 531: (91.3125, -49.15625), 532: (89.0625, -51.65625), 533: (87.0, -54.1875), 534: (85.0, -56.78125), 535: (83.0, -59.40625), 536: (81.03125, -62.09375), 537: (79.1875, -64.9375), 538: (77.5, -67.90625), 539: (75.875, -70.90625), 540: (74.21875, -73.90625), 541: (72.5, -76.875), 542: (71.0, -79.71875), 543: (70.375, -82.28125), 544: (71.1875, -84.40625), 545: (73.5, -86.0625), 546: (76.6875, -86.84375), 547: (79.9375, -85.90625), 548: (83.0, -83.90625), 549: (86.0, -82.90625), 550: (89.03125, -83.125), 551: (92.1875, -82.90625), 552: (95.4375, -81.65625), 553: (98.5, -80.15625), 554: (101.34375, -78.96875), 555: (104.375, -78.09375), 556: (107.6875, -77.5), 557: (110.96875, -77.28125), 558: (114.1875, -77.46875), 559: (117.53125, -78.03125), 560: (120.875, -79.25), 561: (123.84375, -81.46875), 562: (126.34375, -84.3125), 563: (128.53125, -87.15625), 564: (130.59375, -89.875), 565: (132.9375, -92.34375), 566: (135.625, -94.59375), 567: (138.03125, -97.375), 568: (139.71875, -100.875), 569: (141.25, -104.09375), 570: (143.84375, -106.46875), 571: (147.40625, -108.625), 572: (150.3125, -111.34375), 573: (152.0, -114.625), 574: (153.375, -118.03125), 575: (155.0, -121.4375), 576: (156.6875, -124.84375), 577: (158.375, -128.0625), 578: (160.4375, -130.90625), 579: (163.125, -133.1875), 580: (166.375, -134.8125), 581: (170.0, -136.03125), 582: (173.65625, -137.0625), 583: (177.125, -137.875), 584: (180.5, -138.6875), 585: (183.8125, -139.96875), 586: (186.96875, -141.8125), 587: (189.9375, -143.9375), 588: (192.625, -146.28125), 589: (195.0, -148.96875), 590: (197.34375, -151.90625), 591: (199.875, -154.90625), 592: (202.4375, -157.90625), 593: (204.875, -160.90625), 594: (207.34375, -163.84375), 595: (210.09375, -166.46875), 596: (213.15625, -168.46875), 597: (216.375, -169.78125), 598: (219.4375, -170.53125), 599: (221.5, -170.84375)}

def main(args):
	strip = LedStrip(args=args)

	node_dict = oben_gefiltert

	nodes = collections.OrderedDict(sorted(node_dict.items()))
	nodes = get_metric_nodes(nodes)

	# initialize particles with one particle
	particles = [Particle(pos=strip.led_count, v=1, hue=0.4)]

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
				Particle(pos=0, v=random.uniform(-2.5, -1), hue=random.random(), radius=random.uniform(0.5, 2))
			)
		elif spawn >= 0.995:
			particles.append(
				Particle(pos=strip.led_count, v=random.uniform(0.05, 0.5), hue=random.random(), radius=random.uniform(0.5, 2))
			)
		web_particles = webserver.step()
		for web_particle in web_particles:
			if web_particle[0] is not None and web_particle[1] is not None:
				if web_particle[2]:
					particles.append(
						Particle(pos=strip.led_count, v=web_particle[1], hue=web_particle[0])
					)
				else:
					particles.append(
						Particle(pos=1, v=-web_particle[1], hue=web_particle[0])
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
					radius = abs(prev_key - next_key) * _LED_DIST
					break

			if radius == 0:
				radius = 0.00001

			a_slope = (9.81 * max(min(height / radius, 1), -1)) if radius is not 0 else 0
			a_friction = math.copysign(0.01 * 9.81 * math.cos(math.asin(max(min(height / radius, 1), -1))), particle.v) * 1.01

			a = a_slope - a_friction
			t = now - last_time
			v = particle.v + (a - particle.v * 0.22) * t

			new_pos = particle.pos - (v * t) * _LED_PER_METER

			if not strip.led_count >= new_pos >= 0 or particle.ttl <= 0:
				del particles[i]
			else:
				velocity_based_hue = min(math.pow(abs(v) / 2, 2), 0.9)
				velocity_based_brightness = max(math.pow(abs(v) / 2, 2), 0.1) * min(particle.ttl / 3, 1)
				strip.add_hsv(new_pos - particle.radius, particle.hue, 1, velocity_based_brightness)
				strip.add_hsv(new_pos, particle.hue, 1, velocity_based_brightness)
				strip.add_hsv(new_pos + particle.radius, particle.hue, 1, velocity_based_brightness)

				particles[i].pos = new_pos
				particles[i].v = v
				if abs(v) < 0.2:
					particles[i].ttl = particle.ttl - t
				else:
					particles[i].ttl = _DEFAULT_TTL

		last_time = now
		strip.transmit()
		time.sleep(0.01)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Gravity-based LED particle simulation')
	LedStrip.add_arguments(parser)
	main(parser.parse_args())
