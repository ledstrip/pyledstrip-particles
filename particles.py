#!/usr/bin/env python3
import argparse
import time
import math
import random
import webserver
from pyledstrip import LedStrip

from pyledstrip-detector.ledworld import LedWorld, Led

_LED_PER_METER = 60
_PHYSICAL_LED_DIST = 1 / _LED_PER_METER
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
        self.mass = 2 * radius


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


def main(args):
    strip = LedStrip(args=args)
    ledworld = LedWorld.from_json_file(args.heightmap)
    ledworld.to_metric(physical_led_dist=_PHYSICAL_LED_DIST)
    ledworld_np = ledworld.to_np()

    # initialize particles with one particle
    particles = [Particle(pos=strip.led_count, v=1, hue=0.4)]

    last_time = time.perf_counter()

    while True:
        strip.clear()
        if args.show:
            y_stretch = max(ledworld_np[2]) - min(ledworld_np[2])

            for i in range(len(ledworld_np[0])):
                strip.add_hsv(ledworld_np[0][i], ledworld_np[2][i] / y_stretch, 1, 0.2)

        # create particle
        spawn = random.random()
        if spawn < 0.005:
            particles.append(
                Particle(pos=0, v=random.uniform(-2.5, -1), hue=random.random(), radius=random.uniform(0.5, 2))
            )
        elif spawn >= 0.995:
            particles.append(
                Particle(pos=strip.led_count, v=random.uniform(0.05, 0.5), hue=random.random(),
                         radius=random.uniform(0.5, 2))
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

            for idx in range(1, len(ledworld_np[0])):
                prev_id = ledworld_np[0][idx - 1]
                next_id = ledworld_np[0][idx]

                if next_id >= particle.pos > prev_id:
                    height = (ledworld_np[2][idx] - ledworld_np[2][idx - 1])
                    radius = abs(prev_id - next_id) * _PHYSICAL_LED_DIST
                    break

            if radius == 0:
                radius = 0.00001

            a_slope = (9.81 * max(min(height / radius, 1), -1)) if radius is not 0 else 0
            a_friction = math.copysign(0.01 * 9.81 * math.cos(math.asin(max(min(height / radius, 1), -1))),
                                       particle.v) * 1.01

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
    parser.add_argument('heightmap', metavar='HEIGHTMAP', type=str, help='hightmap file (json)')
    parser.add_argument('--show', action='store_true', help='display hightmap on ledstrip')
    main(parser.parse_args())
