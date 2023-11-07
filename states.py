from queue import Queue
import time
import random
from enum import Enum, auto


class PumpState(Enum):
    IDLE = auto()
    RUNNING = auto()


class PumpStateMachine:
    def __init__(self):
        print("Pump: Init")
        self.state = PumpState.IDLE
        self.state = "Idle"
        self.is_running = False

    def set_state(self, new_state):
        print(f"Pump: from {self.state} to {new_state}")
        if new_state == "Running":
            self.is_running = True
        elif new_state == "Idle":
            self.is_running = False
        self.state = new_state

    def start_pump(self):
        print("Pump: Starting")
        self.set_state("Running")

    def stop_pump(self):
        self.set_state("Idle")
        print("Pump: Stopped")

    def tick(self):
        if self.state == "Running":
            print('Pump: Running')
            if not self.is_running:
                self.start_pump()

        elif self.state == "Idle":
            print('Pump: Idle')
            if self.is_running:
                self.stop_pump()


class ReservoirStateMachine:
    def __init__(self):
        print("Reservoir: Init")
        self.state = "Init"
        self.weight = self.read_weight()
        print(f'Reservoir: Starting with {self.weight} in res')

    def set_state(self, new_state):
        print(f"Reservoir: from {self.state} to {new_state}")
        if new_state == "Full":
            pass
        elif new_state == "Empty":
            pass
        self.state = new_state

    def read_weight(self):
        if self.state == "Init":
            fake_sense = random.randrange(50, 75)
            self.set_state('Full')
        else:
            fake_sense = self.weight  # random.randrange(0, self.weight+1)
        return fake_sense

    def tick(self):
        reading = self.read_weight()
        self.weight = reading

        if self.state == 'Full':
            if self.weight <= 49:
                print('new weight under 10')
                self.set_state('Empty')
        elif self.state == "Empty":
            print("Irrigator: Im empty!!")


class Irrigator:

    def __init__(self, pump, res):
        self.pump = pump
        self.res = res
        self.target_weight = 0
        self.cumulative_weight_dispensed = 0
        self.state = "Idle"
        self.is_running = False
        self.active_command = None

    def set_state(self, new_state):
        print(f"Irrigator: from {self.state} to {new_state}")
        if new_state == "Watering":
            self.is_running = True
        elif new_state == "Idle":
            self.is_running = False
        self.state = new_state

    def start_watering(self):
        print("Irrigator: Starting")
        if self.res.state != 'Empty':
            self.set_state("Watering")
            self.pump.start_pump()

    def stop_watering(self):
        self.set_state("Idle")
        print("Irrigator: Stopped")

    def execute_command(self, command):

        if self.active_command:
            print('Irrigator: Currently busy with another command.')
            return  # Already an active command; new commands must wait
        else:
            command.update_status(CommandStatus.PENDING)
            self.active_command = command
            if self.active_command.target:
                self.set_target_weight(target_weight=command.target)
                self.start_watering()

    def set_target_weight(self, target_weight):
        if target_weight > 0:
            self.target_weight = self.res.weight - target_weight
            print(f"Irrigator: Target weight set to {self.target_weight} grams")
        else:
            print(f"Irrigator: can stop")
            self.target_weight = 0

    def __repr__(self):
        return f"Irrigator"

    def tick(self):

        if self.state == "Watering":
            print(f'Irrigator: Watering Plants to target of {self.target_weight}')

            if not self.is_running:
                self.is_running = True
                self.start_watering()

            if self.pump.state == 'Running':  # simulate water coming out
                self.res.weight -= 1

            if self.res.state == 'Empty':
                print('Refill Reservoir')
                self.pump.stop_pump()
                self.stop_watering()
                self.set_target_weight(0)

            if self.target_weight >= self.res.weight:
                print(f"Irrigator: Reached target Weight of {self.target_weight} with {self.res.weight}")
                self.pump.stop_pump()
                self.set_target_weight(0)
                self.stop_watering()
                if self.active_command:
                    self.active_command.update_status(CommandStatus.COMPLETED)
                    self.active_command = None

            self.res.tick()
            self.pump.tick()


        elif self.state == "Idle":
            print(f'Irrigator: {self.state} , Pump: {self.pump.state}')
            if self.is_running:
                self.stop_watering()


class CommandStatus:
    ACKNOWLEDGED = 'Acknowledged'
    PENDING = 'Pending'
    COMPLETED = 'Completed'
    FAILED = 'Failed'


class DeviceCommand:
    def __init__(self, device, action, target=None, on_completion=None, on_failure=None):
        self.device = device
        self.action = action
        self.target = target
        self.on_completion = on_completion
        self.on_failure = on_failure
        self.status = CommandStatus.ACKNOWLEDGED

    def update_status(self, new_status):
        self.status = new_status
        if new_status == CommandStatus.COMPLETED and self.on_completion:
            self.on_completion(self)
        elif new_status == CommandStatus.FAILED and self.on_failure:
            self.on_failure(self)

    def __repr__(self):
        return f"Command for: {self.device}. Action: {self.action}. Target: {self.target}. Status:{self.status}"

    def set_complete(self):
        self.update_status(CommandStatus.COMPLETED)


class CommandManager:
    def __init__(self):
        self.command_queues = {}  # A dictionary of Queues, one for each device.

    def add_command(self, command):
        if command.device not in self.command_queues:
            self.command_queues[command.device] = Queue()
        self.command_queues[command.device].put(command)
        print(f"Command for {command.device} added and acknowledged.")

    def process_commands(self):
        # Iterate through all devices and process one command at a time
        for device, queue in self.command_queues.items():
            if not device.is_running and not queue.empty():
                print(f'processing command queue for {device}')
                next_command = queue.get()
                self.execute_command(device, next_command)

    def execute_command(self, device, command):
        print(f"Processing command: {command.action} for device {command.device}")
        command.status = 'Pending'
        device.execute_command(command)
        # After execution, set the command status to 'Completed' - this could be done asynchronously after the actual completion

    def report_command_status(self, command):
        print(f"Command for {command.device}: {command.action} is currently {command.status}")

    def show_queue(self):
        for device in self.command_queues:
            print(device)


# Usage in a main loop:
def on_command_completion(command):
    print(f"Command completed: {command.action} on {command.device}")


irig = Irrigator(PumpStateMachine(), ReservoirStateMachine())

command_manager = CommandManager()
# Mock commands
command_manager.add_command(DeviceCommand(irig, 'water', 8, on_completion=on_command_completion))
command_manager.add_command(DeviceCommand(irig, 'water', 8, on_completion=on_command_completion))

while True:
    command_manager.process_commands()

    irig.tick()
    time.sleep(1)

