from evdev import ecodes, InputDevice, list_devices
import threading
import time
import select

def find_device_by_name(name_keyword="G29"):
    devices = [InputDevice(path) for path in list_devices()]
    for device in devices:
        if name_keyword.lower() in device.name.lower():
            print(f"Found device: {device.name} @ {device.path}")
            return device.path
    raise RuntimeError(f"No device with name containing '{name_keyword}' found.")

class ForceFeedbackThread:
    def __init__(self, device_name='G29'):
        device_path = find_device_by_name(device_name)
        self.device = InputDevice(device_path)
        self.running = True

        # Force feedback 초기화
        self.device.write(ecodes.EV_FF, ecodes.FF_AUTOCENTER, 0)
        self.axis_code = ecodes.ABS_X

    def calc_autocenter_force(self, axis_val):
        # axis_val -= 32768
        normalized = min(max(abs(axis_val / 32767.0 - 1), 0.25), 0.75)
        strength = int(normalized * 0x9000)# max: 0xFFFF
        return strength

    def run(self):
        while self.running:
            r, _, _ = select.select([self.device.fd], [], [], 0.1)
            if r:
                for event in self.device.read():
                    if event.type == ecodes.EV_ABS and event.code == self.axis_code:
                        force = self.calc_autocenter_force(event.value)
                        self.device.write(ecodes.EV_FF, ecodes.FF_AUTOCENTER, force)

    def start(self):
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.device.write(ecodes.EV_FF, ecodes.FF_AUTOCENTER, 0)
        self.device.close()

# 👇 단독 실행 시 작동하는 블록 추가
if __name__ == "__main__":
    try:
        print("Start ForceFeedbackThread. Ctrl+C to stop.")
        ff_thread = ForceFeedbackThread('G29')
        ff_thread.start()

        while True:
            time.sleep(1)  # 유지용 루프

    except KeyboardInterrupt:
        print("\nFinishing ForceFeedbackThread...")
        ff_thread.stop()
        print("Finished.")
    except Exception as e:
        print(f"error: {e}")
