import glob
import os
import sys
import time
import math
import random
import argparse
import numpy as np
import pygame
import json

import carla
from carla import ColorConverter as cc

import weakref

from utils.color import *
from utils.start_screen import StartScreen
from utils.map_select_screen import MapSelectScreen
from utils.hud_manager import HUDManager
from utils.record_manager import RecordManager
from utils.steer_wheel_force_control import ForceFeedbackThread
from utils.sound import EngineSoundPlayer

if sys.version_info >= (3, 0):
    from configparser import ConfigParser
else:
    from ConfigParser import RawConfigParser as ConfigParser

try:
    import pygame
    from pygame.locals import K_DOWN
    from pygame.locals import K_LEFT
    from pygame.locals import K_RIGHT
    from pygame.locals import K_SPACE
    from pygame.locals import K_UP
    from pygame.locals import K_RETURN
    from pygame.locals import K_BACKSPACE
    from pygame.locals import K_r
    from pygame.locals import K_e
    from pygame.locals import K_p
    from pygame.locals import K_F11
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

# 초기화
pygame.init()
screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
pygame.display.set_caption("CARLA HUD")
clock = pygame.time.Clock()

def get_scaled_font(size_ratio):
    return pygame.font.SysFont(None, max(16, int(screen.get_width() * size_ratio)))

def resize_screen(w, h):
    global screen
    screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)

def show_countdown(world):
    beep = pygame.mixer.Sound("assets/sound/beep.wav")
    beeep = pygame.mixer.Sound("assets/sound/beeep.wav")
    # 화면 복사
    base = screen.copy()

    for i in range(3, 0, -1):
        # if i % 2 == 0: World.reset_vehicle(world.ego, world.ego_spawn)
        # World.reset_vehicle(world.ego, world.ego_spawn)

        screen.blit(base, (0, 0))

        # 텍스트 준비
        font = get_scaled_font(0.1)
        text_surface = font.render(str(i), True, WHITE)
        text_rect = text_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))

        # 검정 배경 사각형
        bg_rect = text_rect.inflate(40, 20)  # 글자보다 약간 크게
        pygame.draw.rect(screen, (0, 0, 0), bg_rect)

        # 글자 그리기
        screen.blit(text_surface, text_rect)

        pygame.display.flip()
        if i < 4: beep.play()
        time.sleep(1)

    # 마지막 START 표시
    World.reset_vehicle(world.ego, world.ego_spawn)
    screen.blit(base, (0, 0))
    start_font = get_scaled_font(0.08)
    start_surface = start_font.render("START!", True, RED)
    start_rect = start_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))

    bg_rect = start_rect.inflate(50, 30)
    pygame.draw.rect(screen, (0, 0, 0), bg_rect)

    screen.blit(start_surface, start_rect)
    pygame.display.flip()
    beeep.play()
    time.sleep(1)

class Joystick(object):
    def __init__(self):
        # initialize steering wheel
        pygame.joystick.init()

        joystick_count = pygame.joystick.get_count()
        if joystick_count == 0:
            raise RuntimeError("No joystick found. Please connect a Logitech G29.")
        elif joystick_count > 1:
            raise ValueError("Please connect only one joystick.")

        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        self.last_hat = (0, 0)  # D-Pad 상태 저장용

    def simple_parse_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                return False
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 2:
                    return False
        return True
    
    def simple_select_events(self):
        dx, dy = 0, 0 
        select, cancel = False, False

        for event in pygame.event.get():
            if event.type == pygame.JOYHATMOTION:
                hat = self.joystick.get_hat(0)
                if hat != self.last_hat:
                    dx, dy = hat[0], hat[1]
                    self.last_hat = hat
                else:
                    dx, dy = 0, 0

            elif event.type == pygame.JOYBUTTONDOWN:
                if self.joystick.get_button(2):  # O 버튼 → 글자 입력/기능
                    select = True
                elif self.joystick.get_button(0):  # X 버튼 → 글자 삭제
                    cancel = True

            elif event.type == pygame.KEYUP:
                if event.key == K_DOWN:
                    dy = -1
                if event.key == K_UP:
                    dy = 1
                if event.key == K_RIGHT:
                    dx = 1
                if event.key == K_LEFT:
                    dx = -1
                if event.key == K_RETURN:
                    select = True
                if event.key == K_BACKSPACE:
                    cancel = True
                    
        if select: cancel = False

        return dx, dy, select, cancel

class DualControl(object):
    def __init__(self, world:carla.World, joystick:Joystick):
        self._autopilot_enabled = False
        if isinstance(world.player, carla.Vehicle):
            self._control = carla.VehicleControl()
            # world.player.set_autopilot(self._autopilot_enabled)
        else:
            raise NotImplementedError("Actor type not supported")
        self._steer_cache = 0.0

        # initialize steering wheel
        self.joystick = joystick

        self._parser = ConfigParser()
        self._parser.read('config/wheel_config.ini')
        self._steer_idx = int(
            self._parser.get('G29 Racing Wheel', 'steering_wheel'))
        self._throttle_idx = int(
            self._parser.get('G29 Racing Wheel', 'throttle'))
        self._brake_idx = int(self._parser.get('G29 Racing Wheel', 'brake'))
        self._reverse_idx1 = int(self._parser.get('G29 Racing Wheel', 'reverse1'))
        self._reverse_idx2 = int(self._parser.get('G29 Racing Wheel', 'reverse2'))
        self._restart_player_pose_button_idx = int(
            self._parser.get('G29 Racing Wheel', 'reset_player_pose_button'))
        self._restart_ego_pose_button_idx = int(
            self._parser.get('G29 Racing Wheel', 'reset_ego_pose_button'))
        self._help_button_idx = int(
            self._parser.get('G29 Racing Wheel', 'help_button'))

        self._gear_states = [-1, 1]
        self._current_gear_index = 0
        self._control.manual_gear_shift = True

    def simple_parse_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                return False
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 2:
                    return False
        return True

    def parse_events(self, world):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == self._reverse_idx1 or event.button == self._reverse_idx2:
                    self.toggle_gear()
                elif event.button == self._restart_player_pose_button_idx:
                    world.reset_vehicle_pose(world.player)
                elif event.button == self._restart_ego_pose_button_idx:
                    world.reset_vehicle_pose(world.ego)
                elif event.button == self._help_button_idx:
                    world.hud.set_help_text(self._help_text())
            elif event.type == pygame.KEYUP:
                if event.key == K_r:
                    return "RESTART"
                elif event.key == K_p:
                    world.reset_vehicle_pose(world.player)
                elif event.key == K_e:
                    world.reset_vehicle_pose(world.ego)
                elif event.key == K_F11:
                    pygame.display.toggle_fullscreen()

        self._parse_vehicle_wheel()
        self._control.reverse = self._control.gear < 0
        if world.player.is_alive:
            world.player.apply_control(self._control)
        return False

    def _help_text(self):
        print("help")
        return [
            "G29 Steering Wheel Help:",
            f"Button {self._reverse_idx1}: 기어 전환",
            f"Button {self._help_button_idx}: 도움말 표시",
            "페달: 가속 / 브레이크",
            "휠: 핸들 조향"
        ]

    def _parse_vehicle_wheel(self):
        numAxes = self.joystick.joystick.get_numaxes()
        jsInputs = [float(self.joystick.joystick.get_axis(i)) for i in range(numAxes)]

        # Custom function to map range of inputs [1, -1] to outputs [0, 1] i.e 1 from inputs means nothing is pressed
        # For the steering, it seems fine as it is
        K1 = 1.0  # 0.55
        steerCmd = K1 * math.tan(1.1 * jsInputs[self._steer_idx])

        K2 = 1.6  # 1.6
        throttleCmd = K2 + (2.05 * math.log10(
            -0.7 * jsInputs[self._throttle_idx] + 1.4) - 1.2) / 0.92
        if throttleCmd <= 0:
            throttleCmd = 0
        elif throttleCmd > 1:
            throttleCmd = 1

        brakeCmd = 1.6 + (2.05 * math.log10(
            -0.7 * jsInputs[self._brake_idx] + 1.4) - 1.2) / 0.92
        if brakeCmd <= 0:
            brakeCmd = 0
        elif brakeCmd > 1:
            brakeCmd = 1

        self._control.steer = steerCmd
        self._control.brake = brakeCmd
        self._control.throttle = throttleCmd

    def toggle_gear(self):
        self._current_gear_index = (self._current_gear_index + 1) % len(self._gear_states)
        gear_value = self._gear_states[self._current_gear_index]
        self._control.gear = gear_value
        self._control.reverse = (gear_value == -1)

class World(object):
    def __init__(self, carla_world, hud, map_name):
        World.destroy_all(carla_world)
        self.world = carla_world
        self.hud = hud
        self.player = None
        self.ego = None
        self.obs_list = []
        self.player_spawn = World.load_spawn_points("config/" + map_name + "/spawn_player.json")
        self.ego_spawn = World.load_spawn_points("config/" + map_name + "/spawn_ego.json")
        self.obs_spawn_list = World.load_obs_spawn_list(self.world, "config/" + map_name + "/spawn_obs.json")
        self.player_sensors = []
        self.ego_sensors = []
        self.player_sensor_config = World.load_sensor_config("config/" + map_name + "/sensor_player.json")
        self.ego_sensor_config = World.load_sensor_config("config/" + map_name + "/sensor_ego.json")

    def restart(self):
        # Spawn actors
        if self.player is None:
            self.player = self.set_blueprint(None, "erp42player", "hero", self.player_spawn)
            for name, spec in self.player_sensor_config.items():
                if name == "camera": self.player_sensors.append(CameraManager(self.player, self.hud, spec, target="player"))
                else: self.player_sensors.append(CarlaSensor(self.player, spec))
        World.reset_vehicle(self.player, self.player_spawn)

        if self.ego is None:
            self.ego = self.set_blueprint(None, "erp42", "ego_vehicle", self.ego_spawn)
            for name, spec in self.ego_sensor_config.items():
                if name == "camera": self.ego_sensors.append(CameraManager(self.ego, self.hud, spec, target="ego"))
                else: self.ego_sensors.append(CarlaSensor(self.ego, spec))
        World.reset_vehicle(self.ego, self.ego_spawn)

        # obs
        if len(self.obs_list) == 0:
            for _spawn_point, _speed in self.obs_spawn_list:
                self.obs_list.append(self.set_blueprint(None, 'erp42npc' + _speed, 'obs' + _speed, _spawn_point))
        else:
            _new_obs_list = []
            for _actor, _actor_data in zip(self.obs_list, self.obs_spawn_list):
                if not _actor.is_alive:
                    _actor = None
                    _actor = self.set_blueprint(None, 'erp42npc' + _actor_data[1], 'obs' + _actor_data[1], _actor_data[0])
                else:
                    World.reset_vehicle(_actor, _actor_data[0])
                _new_obs_list.append(_actor)
            self.obs_list = _new_obs_list

    def set_blueprint(self, role, vehicle_type, role_name, spawn_point):
        # Get a erp blueprint for player.
        blueprint = self.world.get_blueprint_library().find("vehicle.unmannedsolution." + vehicle_type)
        blueprint.set_attribute('role_name', role_name)
        if blueprint.has_attribute('driver_id'):
            driver_id = random.choice(blueprint.get_attribute('driver_id').recommended_values)
            blueprint.set_attribute('driver_id', driver_id)

        # Spawn the vehicle.
        while role is None:
            role = self.world.try_spawn_actor(blueprint, spawn_point)
        return role

    def start_obs_autopilot(self, ego_autopilot = False):
        if ego_autopilot != "False":
            self.ego.apply_control(carla.VehicleControl(throttle=0.0, steer=0.0, brake=0.0))
            self.ego.set_autopilot(True)

        for obs in self.obs_list:
            obs.apply_control(carla.VehicleControl(throttle=0.0, steer=0.0, brake=0.0))
            obs.set_autopilot(True)

    def stop_obs_autopilot(self):
        self.ego.set_autopilot(False)
        self.ego.apply_control(carla.VehicleControl(throttle=0.0, steer=0.0, brake=1.0))

        for obs in self.obs_list:
            obs.set_autopilot(False)
            obs.apply_control(carla.VehicleControl(throttle=0.0, steer=0.0, brake=1.0))

    def load_ego_sensor_config(json_path):
        with open(json_path, "r") as f:
            return json.load(f)

    def get_topology_line_waypoints(self, sampling_resolution=1.0):
        lines = []
        for segment in self.world.get_map().get_topology():
            wp_start, wp_end = segment
            waypoints = [wp_start]
            current = wp_start
            while current.transform.location.distance(wp_end.transform.location) > sampling_resolution:
                next_wps = current.next(sampling_resolution)
                if not next_wps:
                    break
                current = next_wps[0]
                waypoints.append(current)
            lines.append(waypoints)  # <-- Location 아님!
        return lines

    def load_spawn_points(json_path):
        with open(json_path, "r") as f:
            data = json.load(f)
        return carla.Transform(
            carla.Location(**data["location"]),
            carla.Rotation(**data["rotation"])
        )
    
    def load_obs_spawn_list(world, json_path):
        spawn_points = world.get_map().get_spawn_points()
        
        with open(json_path, "r") as f:
            npc_list = json.load(f)
        result = []
        for name, spec in npc_list.items():
        # for obs_key in npc_list["npc list"]:
            if spec["point"] < 0:
                result.append([
                        carla.Transform(
                            carla.Location(**spec["location"]),
                            carla.Rotation(**spec["rotation"])
                        ),
                        str(spec["speed"])
                    ]
                )
            else:
                result.append([
                        spawn_points[spec["point"]],
                        str(spec["speed"])
                    ]
                )

        return result

    def load_sensor_config(json_path):
        with open(json_path, "r") as f:
            return json.load(f)
    
    def reset_vehicle(actor, transform):
        if actor is not None and actor.is_alive:
            actor.apply_control(carla.VehicleControl(throttle=0.0, steer=0.0, brake=1.0))
            time.sleep(0.01)
            actor.set_autopilot(False)
            time.sleep(0.01)
            actor.set_target_velocity(carla.Vector3D(0.0, 0.0, 0.0))
            time.sleep(0.01)
            actor.set_target_angular_velocity(carla.Vector3D(0.0, 0.0, 0.0))
            time.sleep(0.01)
            actor.set_transform(transform)
            time.sleep(0.01)

    def reset_vehicle_pose(self, vehicle):
        if vehicle is None or not vehicle.is_alive:
            return

        current_transform = vehicle.get_transform()
        map = self.world.get_map()

        # 현재 차량 위치에서 가장 가까운 차선 waypoint
        closest_wp = map.get_waypoint(current_transform.location, project_to_road=True, lane_type=carla.LaneType.Driving)

        if closest_wp is not None:
            reset_transform = carla.Transform(
                carla.Location(
                    x=closest_wp.transform.location.x,
                    y=closest_wp.transform.location.y,
                    z=closest_wp.transform.location.z + 3.0  # 공중으로 3m 위로 띄워서 소환
                ),
                closest_wp.transform.rotation
            )
            print(f"Resetting player to elevated lane at {reset_transform.location}")
            World.reset_vehicle(vehicle, reset_transform)
        else:
            print("No valid waypoint found for player reset.")
        return

    def destroy(self):
        actor_list = self.world.get_actors()
        for actor in actor_list:
            try:
                actor.destroy()
            except:
                continue

    def destroy_all(world):
        actor_list = world.get_actors()
        for actor in actor_list:
            try:
                actor.destroy()
            except:
                continue

class CameraManager:
    def __init__(self, parent_actor, hud, config, target="player"):
        self._parent = parent_actor
        self.hud = hud
        self._target = target

        world = self._parent.get_world()
        bp_library = world.get_blueprint_library()
        bp = bp_library.find(config["type"])

        _transform = carla.Transform(
            carla.Location(**config["transform"]["location"]),
            carla.Rotation(**config["transform"]["rotation"])
        )

        for k, v in config.get("attributes", {}).items():
            bp.set_attribute(k, v)

        self.sensor = world.spawn_actor(bp, _transform, attach_to=self._parent)
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda image: CameraManager._parse_image(weak_self, image))

    @staticmethod
    def _parse_image(weak_self, image):
        self = weak_self()
        if not self:
            return

        image.convert(cc.Raw)
        array = np.frombuffer(image.raw_data, dtype=np.uint8)
        array = np.reshape(array, (image.height, image.width, 4))[:, :, :3]
        array = array[:, :, ::-1]  # BGR → RGB
        surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
        if self._target == "player":
            self.hud.set_player_camera_image(surface)
        elif self._target == "ego":
            self.hud.set_ego_camera_image(surface)

    def destroy(self):
        if self.sensor is not None:
            self.sensor.stop()
            self.sensor.destroy()

class CarlaSensor(object):
    def __init__(self, parent_actor, config):
        self.sensor = None
        world = parent_actor.get_world()
        bp = world.get_blueprint_library().find(config["type"])

        for k, v in config.get("attributes", {}).items():
            bp.set_attribute(k, v)

        transform = carla.Transform(
            carla.Location(**config["transform"]["location"]),
            carla.Rotation(**config["transform"]["rotation"])
        )

        self.sensor = world.spawn_actor(bp, transform, attach_to=parent_actor)

    def destroy(self):
        if self.sensor is not None:
            self.sensor.destroy()

def game_loop(world, hud, controller, hz, ego_autopilot):
    hud.set_player_location(world.player.get_transform())
    hud.set_ego_location(world.ego.get_transform())
    hud.set_obs_location([
        obs.get_transform()
        for obs in world.obs_list
    ])

    hud.draw()
    
    pygame.display.flip()

    show_countdown(world)

    world.ego.disable_constant_velocity()
    time.sleep(0.01)
    world.constant_velocity_enabled = False
    time.sleep(0.01)

    world.start_obs_autopilot(ego_autopilot)

    prev_pos = world.player.get_transform()

    hud.start_clock()

    while True:
        world.ego.disable_constant_velocity()
        world.constant_velocity_enabled = False
        # 차량 상태 정보 가져오기
        _control = world.player.get_control()
        velocity = world.player.get_velocity()
        speed = math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2) * 3.6  # m/s -> km/h
        _gear = 1 if _control.reverse else -1

        # HUD 갱신
        hud.set_player_location(world.player.get_transform())
        hud.set_ego_location(world.ego.get_transform())
        hud.set_obs_location([
            obs.get_transform()
            for obs in world.obs_list
            if obs.is_alive
        ])

        hud.update(
            throttle=_control.throttle,
            brake=_control.brake,
            steering=_control.steer,
            speed=speed,
            gear=_gear,
        )

        # G29 조작 처리 전용
        result = controller.parse_events(world)
        if result == "RESTART":
            return False
        elif result == True:
            return True
        
        if hud.is_crossing_finish_line(prev_pos, world.player.get_transform()):
            game_finish_loop(world, hud, controller, hz)
            return True

        prev_pos = world.player.get_transform()

        hud.draw()
        pygame.display.flip()
        clock.tick_busy_loop(hz)

def game_finish_loop(world, hud, controller, hz):
    finish_time = 3.0
    finish_timer = time.time()
    hud.stop_clock()
    hud.show_banner("Finished", RED, 3.0)
    
    while time.time() - finish_timer < finish_time:
        clock.tick_busy_loop(hz)

        # 차량 상태 정보 가져오기
        _control = world.player.get_control()
        velocity = world.player.get_velocity()
        speed = math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2) * 3.6  # m/s -> km/h
        _gear = 1 if _control.reverse else -1

        # HUD 갱신
        hud.set_player_location(world.player.get_transform())
        hud.set_ego_location(world.ego.get_transform())
        hud.set_obs_location([
            obs.get_transform()
            for obs in world.obs_list
            if obs.is_alive
        ])

        hud.update(
            throttle=_control.throttle,
            brake=_control.brake,
            steering=_control.steer,
            speed=speed,
            gear=_gear,
        )

        # G29 조작 처리 전용
        _ = controller.parse_events(world)

        hud.draw()
        pygame.display.flip()
        clock.tick(hz)

    return

def main():
    argparser = argparse.ArgumentParser(description='CARLA Manual Control Client')
    argparser.add_argument('--ego_autopilot', default='False')
    argparser.add_argument('--hz', default=60)

    args = argparser.parse_args()

    ffb = ForceFeedbackThread('G29')
    ffb.start()
    
    joystick = Joystick()

    try:
        client = carla.Client('127.0.0.1', 2000)
        client.set_timeout(2.0)
    except Exception as e:
        print("CARLA 서버 연결 실패:", e)
        sys.exit(1)

    map_list = [m.split("/")[-1] for m in client.get_available_maps()]

    start_screen = StartScreen(screen, get_scaled_font, resize_screen, clock)
    map_select_screen = MapSelectScreen(screen, get_scaled_font, resize_screen, clock, map_list, joystick)
    record_manager = RecordManager(screen, get_scaled_font, joystick, clock)

    while(joystick.simple_parse_events()):
        start_screen.show()

    selected_map = map_select_screen.show()

    world = client.get_world()
    if selected_map != world.get_map().name.split("/")[-1]:
        world = client.load_world(selected_map)
        time.sleep(0.1)

    settings = world.get_settings()
    settings.no_rendering_mode = True
    settings.fixed_delta_seconds = 1.0 / args.hz
    world.apply_settings(settings)

    while True:

        hud = HUDManager(screen, os.path.abspath("config/" + selected_map + "/finish_line.json"))
        world = World(client.get_world(), hud, selected_map)

        world.constant_velocity_enabled = True
        world.restart()
        time.sleep(0.01)
        world.ego.enable_constant_velocity(carla.Vector3D(0, 0, 0))
        world.ego.set_target_velocity(carla.Vector3D(-0.01, 0, 0))
        time.sleep(0.01)
        world.ego.apply_control(carla.VehicleControl(throttle=0.0, steer=0.0, brake=1.0))
        # world.constant_velocity_enabled = True
        world.ego.set_target_velocity(carla.Vector3D(-0.01, 0, 0))


        hud.initialize_time()
        time.sleep(0.1)
        hud.update(throttle=0.0, brake=0.0, steering=0.0, speed=0.0, gear = 0)
        world.ego.set_target_velocity(carla.Vector3D(-0.01, 0, 0))

        controller = DualControl(world, joystick)

        hud.set_topology_lines(world.get_topology_line_waypoints())

        world.restart()
        world.ego.apply_control(carla.VehicleControl(throttle=0.0, steer=0.0, brake=1.0))
        controller.toggle_gear()

        try:
            time.sleep(0.1)
            success = game_loop(world, hud, controller, args.hz, args.ego_autopilot)
            world.restart()
            if success:
                record_manager.input_name(hud.get_time_spent(), selected_map)              # 휠 D-Pad로 입력
                while(joystick.simple_parse_events()):
                    record_manager.display_leaderboard()
                continue
            else:
                continue
        except KeyboardInterrupt:
            break
        finally:
            while(joystick.simple_parse_events()):
                start_screen.show()

            selected_map = map_select_screen.show()

            world.destroy()
            del controller
            del world
            del hud

            if selected_map != client.get_world().get_map().name.split("/")[-1]:
                world = client.load_world(selected_map)
                time.sleep(0.5)
                settings = world.get_settings()
                settings.no_rendering_mode = True
                settings.fixed_delta_seconds = 1.0 / args.hz
                world.apply_settings(settings)
    
    ffb.stop()


if __name__ == "__main__":
    main()
