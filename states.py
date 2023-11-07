from queue import Queue
import time
import random
from enum import Enum, auto
from abc import ABC, abstractmethod


# Define the possible states for the Pump as an Enum
class PumpState(Enum):
    IDLE = auto()
    RUNNING = auto()

    def __str__(self):
        return self.name.capitalize()


class ReservoirState(Enum):
    INIT = auto()
    FULL = auto()
    EMPTY = auto()

    def __str__(self):
        return self.name.capitalize()


# Base abstract class for state machines
class StateMachine(ABC):
    def __init__(self, initial_state):
        self.state = initial_state
        self.transitions = {}

    def add_transition(self, from_state, to_state):
        if from_state not in self.transitions:
            self.transitions[from_state] = set()
        self.transitions[from_state].add(to_state)

    def set_state(self, new_state):
        if new_state in self.transitions.get(self.state, {}):
            print(f"{self.__class__.__name__}: Transition from {self.state} to {new_state}")
            self.state = new_state
            self.on_transition(new_state)
        else:
            print(f"{self.__class__.__name__}: Invalid transition from {self.state} to {new_state}")

    def display_transitions(self):
        for start_state, new_states in self.transitions.items():
            print(f"{start_state} to: {', '.join(str(x) for x in new_states)}")

    @abstractmethod
    def on_transition(self, new_state):
        """ Implement this method in subclasses to handle any additional actions on state transition """
        pass

    @abstractmethod
    def tick(self):
        pass


# PumpStateMachine now inherits from StateMachine and must implement tick and on_transition methods
class PumpStateMachine(StateMachine):
    def __init__(self):
        super().__init__(PumpState.IDLE)
        self.is_running = False
        # Define valid transitions
        self.add_transition(PumpState.IDLE, PumpState.RUNNING)
        self.add_transition(PumpState.RUNNING, PumpState.IDLE)
        self.name = "Pump"

    def on_transition(self, new_state):
        # Handle any additional actions on state transition
        if new_state == PumpState.RUNNING:
            self.is_running = True
        elif new_state == PumpState.IDLE:
            self.is_running = False

    def start_pump(self):
        print("Pump: Starting")
        self.set_state(PumpState.RUNNING)

    def stop_pump(self):
        print("Pump: Stopped")
        self.set_state(PumpState.IDLE)

    def tick(self):
        # Implement the tick behavior specific to the PumpStateMachine
        if self.state == PumpState.RUNNING:
            print('Pump: Running')
            if not self.is_running:
                self.start_pump()

        elif self.state == PumpState.IDLE:
            print('Pump: Idle')
            if self.is_running:
                self.stop_pump()


class ReservoirStateMachine(StateMachine):
    EMPTY_THRESHOLD = 49  # Define a threshold for when the reservoir is considered empty

    def __init__(self):
        # initial_state = self.determine_state_by_weight(initial_weight)
        super().__init__(ReservoirState.INIT)
        self.name = "Reservoir"
        self.add_transition(ReservoirState.INIT, ReservoirState.FULL)
        self.add_transition(ReservoirState.INIT, ReservoirState.EMPTY)
        self.add_transition(ReservoirState.EMPTY, ReservoirState.FULL)
        self.add_transition(ReservoirState.FULL, ReservoirState.EMPTY)

        initial_weight = self.read_initial_weight()
        self.weight = initial_weight
        self.set_state_by_weight()
        print(f'Reservoir: Starting with {self.weight} in res')

    # def determine_state_by_weight(self, weight):
    #     return ReservoirState.EMPTY if self.is_empty_by_weight(weight) else ReservoirState.FULL

    def set_state_by_weight(self):
        self.set_state(ReservoirState.EMPTY) if self.is_empty_by_weight(self.read_weight()) else self.set_state(
            ReservoirState.FULL)

    def read_initial_weight(self):
        return random.randrange(70, 75)  # Initial weight can range from 0 to 74

    def is_empty_by_weight(self, weight):
        return weight <= self.EMPTY_THRESHOLD

    def on_transition(self, new_state):
        pass

    def read_weight(self):
        self.weight = self.weight
        return self.weight  # random.randrange(0, self.weight + 1)

    def tick(self):
        self.weight = self.read_weight()
        # Check if the state needs to be changed based on the weight
        if self.state == ReservoirState.FULL and self.is_empty_by_weight(self.weight):
            print('Reservoir: New weight under threshold, now empty')
            self.set_state(ReservoirState.EMPTY)
        elif self.state == ReservoirState.EMPTY:
            print("Reservoir: I'm empty!!")


class CommandStatus(Enum):
    ACKNOWLEDGED = auto()
    REJECTED = auto()
    PENDING = auto()
    COMPLETED = auto()
    FAILED = auto()

    def __str__(self):
        return self.name.capitalize()


class DeviceCommand:
    def __init__(self, action, target=None, on_completion=None, on_failure=None):
        self.action = action
        self.target = target
        self.on_completion = on_completion
        self.on_failure = on_failure
        self.status = CommandStatus.ACKNOWLEDGED
        self.result = 0

    def update_status(self, new_status):
        self.status = new_status
        if new_status == CommandStatus.COMPLETED and self.on_completion:
            self.on_completion(self)
        elif new_status == CommandStatus.FAILED and self.on_failure:
            self.on_failure(self)

    def __repr__(self):
        return f"Command: Action: {self.action}. Target: {self.target}. Status: {self.status}"


class BaseController:
    def __init__(self):
        self.is_running = False
        self.active_command = None
        self.state = "Idle"

    def set_state(self, new_state):
        print(f"{self.__class__.__name__}: from {self.state} to {new_state}")
        self.state = new_state
        self.is_running = (new_state != "Idle")

    def enqueue_command(self, command):
        if self.is_running or self.active_command is not None:
            # Reject the command because we are already processing one
            command.update_status(CommandStatus.REJECTED)
            print(f"Command rejected for {self.__class__.__name__}: {command}")
        else:
            # Accept the command
            self.active_command = command
            command.update_status(CommandStatus.ACKNOWLEDGED)
            print(f"Command accepted for {self.__class__.__name__}: {command}")

    def execute_command(self):
        if self.active_command and not self.is_running:
            self.active_command.update_status(CommandStatus.PENDING)
            self.set_state("Processing")
            self.process_command(self.active_command)

    def process_command(self, command):
        # This should be overridden by subclasses to provide specific command processing logic
        raise NotImplementedError("Subclasses should implement this method.")

    def tick(self):
        # Base tick functionality. Override in subclass if necessary, but be sure to call super().
        if self.state != "Idle":
            # ... perform actions based on the state ...
            pass
        else:
            self.execute_command()

    # Other methods can be defined here...


# Now you can define Irrigator as a subclass of BaseController
class Irrigator(BaseController):
    def __init__(self, pump, reservoir):
        super().__init__()
        self.pump = pump
        self.reservoir = reservoir
        self.target_weight = 0
        self.water_out = 0

    def process_command(self, command):
        # Here, we'll interpret the command and start actions accordingly.
        if command.action == 'water' and command.target is not None:
            self.set_target_weight(command.target)
            self.start_watering()
        else:
            print(f"{self.__class__.__name__}: Unknown command action {command.action}")
            command.update_status(CommandStatus.FAILED)

    def start_watering(self):
        print(f"{self.__class__.__name__}: Starting watering to target of {self.target_weight} grams")
        self.pump.start_pump()  # Assuming the pump has a start method
        self.set_state("Watering")

    def stop_watering(self):
        print(f"{self.__class__.__name__}: Stopped watering")
        self.pump.stop_pump()  # Assuming the pump has a stop method
        self.set_state("Idle")

    def set_target_weight(self, target_weight):
        if target_weight > 0:
            self.target_weight = self.reservoir.weight - target_weight
            print(f"Irrigator: Target weight set to {self.target_weight} grams")
        else:
            print(f"Irrigator: can stop")
            self.target_weight = 0

    def tick(self):
        super().tick()  # Make sure to call the base class tick method
        # print(self.reservoir.weight)
        self.reservoir.tick()
        if self.state == "Watering":
            print(f'Irrigator: Watering Plants to target of {self.target_weight}')

            if not self.is_running:
                self.is_running = True
                self.start_watering()

            if self.reservoir.state == ReservoirState.EMPTY:
                print('Refill Reservoir')
                self.stop_watering()
                self.set_target_weight(0)
                if self.active_command:
                    print(f'Irrigator: Water out = {self.water_out}')
                    self.active_command.result = self.water_out
                    self.active_command.update_status(CommandStatus.FAILED)
                    self.active_command = None

            if self.pump.state == PumpState.RUNNING:  # simulate water coming out
                self.reservoir.weight -= 1
                self.water_out += 1

            if self.target_weight >= self.reservoir.weight:
                print(f"Irrigator: Reached target Weight of {self.target_weight} with {self.reservoir.weight}")
                # self.pump.stop_pump()
                self.set_target_weight(0)
                self.stop_watering()
                if self.active_command:
                    print(f'Irrigator: Water out = {self.water_out}')
                    self.active_command.result = self.water_out
                    self.active_command.update_status(CommandStatus.COMPLETED)
                    self.active_command = None

            self.pump.tick()


        elif self.state == "Idle":
            print(f'Irrigator: {self.state} , Pump: {self.pump.state}')
            if self.is_running:
                self.stop_watering()


def on_command_completion(command):
    print(f"Command completed: {command.action}. Result: {command.result}")

#
# irrigator = Irrigator(PumpStateMachine(), ReservoirStateMachine())
# irrigator.enqueue_command(DeviceCommand('water', target=40, on_completion=on_command_completion))
# irrigator.enqueue_command(DeviceCommand('water', target=4, on_completion=on_command_completion))
#
# # in a loop
# while True:
#     irrigator.tick()
#     time.sleep(0.25)
#     print('end of loop \n')
