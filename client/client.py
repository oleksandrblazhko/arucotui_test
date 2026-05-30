from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

import pygame
import threading
import time
import math

# ==========================================
# CONFIG
# ==========================================

OSC_IP = "127.0.0.1"
OSC_PORT = 9000

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

MARKER_TIMEOUT = 0.5

SCALE = 500

# ==========================================
# MARKER CLASS
# ==========================================

class Marker:

    def __init__(self, marker_id):

        self.id = marker_id

        self.tx = 0
        self.ty = 0
        self.tz = 0

        self.roll = 0
        self.pitch = 0
        self.yaw = 0

        self.corners = []

        self.last_seen = time.time()

    @property
    def visible(self):
        return (time.time() - self.last_seen) < MARKER_TIMEOUT


# ==========================================
# STORAGE
# ==========================================

markers = {}
lock = threading.Lock()

# ==========================================
# OSC CALLBACK
# ==========================================

def marker_handler(address, *args):

    marker_id = int(args[0])

    with lock:

        if marker_id not in markers:
            markers[marker_id] = Marker(marker_id)

        m = markers[marker_id]

        m.tx = args[1]
        m.ty = args[2]
        m.tz = args[3]

        m.roll = args[4]
        m.pitch = args[5]
        m.yaw = args[6]

        m.corners = args[7:]

        m.last_seen = time.time()


# ==========================================
# OSC SERVER THREAD
# ==========================================

dispatcher = Dispatcher()
dispatcher.map("/marker", marker_handler)

server = ThreadingOSCUDPServer(
    (OSC_IP, OSC_PORT),
    dispatcher
)

osc_thread = threading.Thread(
    target=server.serve_forever,
    daemon=True
)

osc_thread.start()

print(f"OSC listening on {OSC_IP}:{OSC_PORT}")

# ==========================================
# PYGAME
# ==========================================

pygame.init()

screen = pygame.display.set_mode(
    (WINDOW_WIDTH, WINDOW_HEIGHT)
)

pygame.display.set_caption(
    "ArUCo TUI Visualizer"
)

font = pygame.font.SysFont(
    "Arial",
    18
)

clock = pygame.time.Clock()

# ==========================================
# MAIN LOOP
# ==========================================

running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

    screen.fill((30, 30, 30))

    center_x = WINDOW_WIDTH // 2
    center_y = WINDOW_HEIGHT // 2

    # coordinate axes

    pygame.draw.line(
        screen,
        (80,80,80),
        (0, center_y),
        (WINDOW_WIDTH, center_y),
        1
    )

    pygame.draw.line(
        screen,
        (80,80,80),
        (center_x, 0),
        (center_x, WINDOW_HEIGHT),
        1
    )

    active_count = 0

    with lock:

        for marker in markers.values():

            if not marker.visible:
                continue

            active_count += 1

            x = center_x + int(marker.tx * SCALE)
            y = center_y + int(marker.ty * SCALE)

            radius = max(
                10,
                int(100 / (marker.tz + 0.1))
            )

            # marker body

            pygame.draw.circle(
                screen,
                (0,255,0),
                (x,y),
                radius,
                2
            )

            # orientation arrow

            arrow_len = radius + 20

            dx = math.cos(marker.yaw) * arrow_len
            dy = math.sin(marker.yaw) * arrow_len

            pygame.draw.line(
                screen,
                (255,0,0),
                (x,y),
                (x + dx, y + dy),
                3
            )

            # marker label

            label = (
                f"ID={marker.id} "
                f"X={marker.tx:.2f} "
                f"Y={marker.ty:.2f} "
                f"Z={marker.tz:.2f}"
            )

            txt = font.render(
                label,
                True,
                (255,255,255)
            )

            screen.blit(
                txt,
                (x + radius + 5, y - 10)
            )

    # info panel

    txt1 = font.render(
        f"Active markers: {active_count}",
        True,
        (255,255,0)
    )

    screen.blit(txt1, (10,10))

    txt2 = font.render(
        "Green circle = marker position",
        True,
        (200,200,200)
    )

    screen.blit(txt2, (10,40))

    txt3 = font.render(
        "Red line = yaw orientation",
        True,
        (200,200,200)
    )

    screen.blit(txt3, (10,70))

    pygame.display.flip()

    clock.tick(60)

# ==========================================
# SHUTDOWN
# ==========================================

server.shutdown()

pygame.quit()