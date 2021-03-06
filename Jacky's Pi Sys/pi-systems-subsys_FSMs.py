# Written by Noah Caleanu for Mars Colony's Airlock Project
#

# ____________________________________________________________________________________________________
# SET UP

import time
from enum import Enum
from abc import ABC, abstractmethod
import threading
from threading import Lock
import struct
import importlib
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!")
except ModuleNotFoundError:
    print("Running on non-pi machine")

# Import the subsystems & relevant modules
# subsys_inter = importlib.import_module('pi-systems_interface-subsystem')
subsys_pool = importlib.import_module("pi-systems_subsystem-pool")
pressure_ss = importlib.import_module('pi-systems_pressure-manager')
light_ss = importlib.import_module('pi-systems_lights-manager')
door_ss = importlib.import_module('pi-systems_door-subsystem')
comms = importlib.import_module('pi-systems_communications')
subsys_base = importlib.import_module('pi-systems_subsystem-base')
sensor_ss = importlib.import_module('pi-systems_sensor-reader')
FSM = importlib.import_module('pi-systems-defn-FSMs')

inputs = []

#  Define the pins used for the following butt/switch
#  inputs to the FSM interface
try:
    pressure_butt = subsys_inter.InputComponent(name='P', pin=29, subtype='Button')
    depressure_butt = subsys_inter.InputComponent(name='D', pin=31, subtype='Button')
    lights_toggle = subsys_inter.InputComponent(name='L', pin=32, subtype='Switch')
    door_open_butt = subsys_inter.InputComponent(name='O', pin=33, subtype='Button')
    door_close_butt = subsys_inter.InputComponent(name='C', pin=35, subtype='Button')
    emergency_butt = subsys_inter.InputComponent(name='E', pin=36, subtype='Button')
    power_toggle = subsys_inter.InputComponent(name='Power', pin=37, subtype='Switch')
    # Add to inputs list
    inputs.append(emergency_butt)
    inputs.append(pressure_butt)
    inputs.append(depressure_butt)
    inputs.append(lights_toggle)
    inputs.append(door_open_butt)
    inputs.append(door_close_butt)
    inputs.append(power_toggle)

except NameError:
    print("Skipping input component declarations.")


outputs = []

try:
    led1 = subsys_inter.OutputComponent(name='LED_1',
                                        pin=11,
                                        subtype='LED')  # LED initial state OFF
    led2 = subsys_inter.OutputComponent(name='LED_2',
                                        pin=12,
                                        subtype='LED')
    led3 = subsys_inter.OutputComponent(name='LED_3',
                                        pin=13,
                                        subtype='LED')
    led4 = subsys_inter.OutputComponent(name='LED_4',
                                        pin=15,
                                        subtype='LED')
    led5 = subsys_inter.OutputComponent(name='LED_5',
                                        pin=16,
                                        subtype='LED')
    led6 = subsys_inter.OutputComponent(name='LED_6',
                                        pin=18,
                                        subtype='LED')
    # Add outputs to the list                        
    outputs.append(led1)
    outputs.append(led2)
    outputs.append(led3)
    outputs.append(led4)
    outputs.append(led5)
    outputs.append(led6)
except NameError:
        print("Skipping output declarations")

#  Now create the interface where the buttons are pooled
try:
    interface = subsys_inter.InterfaceSubsystem(name="Airlock-Colony",
                                                thread_id=49,
                                                inputs=inputs,
                                                outputs=outputs)
    interface.start()
except NameError:
    print("Interface not initialized. Ensure GPIO installed on this device\n")

# Create an array to store all subsystems
subsystems = []

# Initiate PressureSubsystem
airlock_press_ss = pressure_ss.PressureSubsystem(name="Airlock Pressure",
                                                 thread_id=50)
subsystems.append(airlock_press_ss)
airlock_press_ss.start()

# Initiate the DoorSubsystem
airlock_door_ss = door_ss.DoorSubsystem(name="Airlock Door",
                                        thread_id=51)
subsystems.append(airlock_door_ss)
airlock_door_ss.start()

# Initiate the LightingSubsystem.
# Throws an exception while not running on RaspPi machine
try:
    airlock_light_ss = light_ss.LightingSubsystem(name="Airlock Lights",
                                                  thread_id=52)
    subsystems.append(airlock_light_ss)
    airlock_light_ss.start()

except NameError:
    print("GPIO not defined. Skipping...")
except ModuleNotFoundError:
    print("GPIO could not be found. Skipping...")

# Having issues initializing the sensor subsystem.  Name error?
try:
    airlock_sensor_ss = sensor_ss.SensorSubsystem(name='Airlock Sensors',
                                                  thread_id=53,
                                                  address=10)  # check address for repeats?
    subsystems.append(airlock_sensor_ss)                      
    airlock_sensor_ss.start()
except TypeError:
    print("Unexpected name occured.")

# __END OF SETUP ______________________________________________________________

#  Create an instance of the FSMs
fsm_pressure = FSM.PressureFSM()
fsm_lights = FSM.LightFSM()
fsm_door = FSM.DoorFSM()

#  Target pressures for Pressurizing and depressurizing
target_p = 1013  # Earth atmosphere roughly 101.3kPa
target_d = 6     # Martian Atmosphere 600 Pascals


class inputs:
    def __init__(self, state):
        self.state = state

    def return_state(self):
        return self.state

inputs = inputs([0, 0, 1, 0, 0, 0, 1])  # this is for debugging purposes only.
state = inputs.return_state()
print(state)

# Improved code with the button interface incorporated and FSM for subsys.
# Do i need to put outputs here if subsys already in
def loop_FSMs(subsystems,
              inputs):
    #pressure = sensor_ss.sensor_data[3]  # Replace the initialization of pressure  
    pressure = 0  # Take this out when sensors implemented

    #Run loop when Power switch is in ON position
    while(inputs.state[6] == 1):
        # i and j are used for mock door state ...
        # ...Change to sensor data as well
        i = 0   # Col_Airlock_door = door_ss.get_current_door_state(airlock_door_ss)
        j = 0   # Represents same thing as i but for closing door so just delete when sensors implemented

        # Comment this out for now 
        '''
        print("E button: ", inputs[0].state)
        print("P button: ", inputs[1].state)
        print("D button: ", inputs[2].state)
        print("L switch: ", inputs[3].state)
        print("O button: ", inputs[4].state)
        print("C button: ", inputs[5].state)
        print("Power switch ", inputs[6].state)
        '''

        # Check if user pressed E
        # EMERG LOGIC IS ACTIVE LOW
        if inputs[0].state == 0:
            emergency = True  # theres really no point in this besides an easier way to display Emergencies to user
            if(fsm_pressure.current_state.name == 'idle'):
                fsm_pressure.detected_emerg_3(airlock_press_ss)
            elif(fsm_pressure.current_state.name == 'Emergency'):
                fsm_pressure.emerg_unresolved(airlock_press_ss)
            if(fsm_door.current_state.name == 'Idle'):
                fsm_door.detected_emerg_3(airlock_door_ss)
            elif(fsm_door.current_state.name == 'Emergency'):
                fsm_door.emerg_unresolved(airlock_door_ss)

        # Check if user pressed P
        # CHANGE THIS TO READ SENSOR DATA NOT MOCK DATA
        if (inputs[1] == 1 and inputs[0] == 1):
            # if command is to pressurize, change states
            fsm_pressure.start_pressurize(airlock_press_ss)
            # while not done pressurizing and no emergency...
            #while (sensor_ss.sensor_data[3] < target_p):  # REPLACE LINE BELOW WITH THIS FOR SENSORS
            while (pressure < target_p):
                if inputs[0].state == 1:
                    # ... we loop back into our current state
                    fsm_pressure.keep_pressurize(airlock_press_ss)
                    time.sleep(0.001)           # Take this out when sensors implemented
                    pressure = pressure + 1  # Take this out when sensors implemented
                    #sensor_ss.__update_sensor_data()  # Not sure if the sensors are read continuously but update the sensor value
                    print("PRESSURIZING...")
                else:
                    if(fsm_pressure.current_state == fsm_pressure.Emergency):
                        fsm_pressure.emerg_unresolved(airlock_press_ss)
                    else:
                        fsm_pressure.detected_emerg_1(airlock_press_ss)

            fsm_pressure.done_pressurize(airlock_press_ss)
        else:
            if(fsm_pressure.current_state == fsm_pressure.Emergency):
                fsm_pressure.emerg_unresolved(airlock_press_ss)
            else:
                fsm_pressure.keep_idling(airlock_press_ss)

        # Check if user pressed D
        # CHANGE THIS TO READ SENSOR DATA NOT MOCK DATA
        if inputs[2].state == 1 and inputs[0] == 1:
            fsm_pressure.start_depressurize(airlock_press_ss)  
          
            #while (sensor_ss.sensor_data[3] < target_d):  # REPLACE LINE BELOW WITH THIS FOR SENSORS
            while(pressure > target_d):
                if inputs[0].state == 1:
                    fsm_pressure.keep_depressurize(airlock_press_ss)
                    time.sleep(0.001)            # Take this out when sensors implemented
                    pressure = pressure - 1  # Take this out when sensors implemented
                    print("DEPRESSURIZING")
                else:
                    if(fsm_pressure.current_state == fsm_pressure.Emergency):
                        fsm_pressure.emerg_unresolved(airlock_press_ss)
                    else:
                        fsm_pressure.detected_emerg_2(airlock_press_ss)    
                # sensor_ss.__update_sensor_data()  # Might need to manually update. check how sensors are read
            fsm_pressure.done_depressurize(airlock_press_ss)
        else:
            if(fsm_pressure.current_state == fsm_pressure.Emergency):
                fsm_pressure.emerg_unresolved(airlock_press_ss)
            else:
                fsm_pressure.keep_idling(airlock_press_ss)

        print("I am in idle again? ",
              fsm_pressure.current_state == fsm_pressure.idle)

        # Check if user pressed L
        if inputs[3].state == 0:
            # we want the lights off and theyre on
            if(fsm_lights.current_state.name == "ON"):
                try:
                    fsm_lights.turn_off(airlock_light_ss)
                except NameError:
                    print("Subsys doesnt exist")
            # else the light switch is ON
            else:
                print("Lights already off")
        else:
            if(fsm_lights.current_state.name == "OFF"):
                try:
                    fsm_lights.turn_on(airlock_light_ss)
                except NameError:
                    print("Subsys doesnt exist")
            else:
                print("Lights already on")
        print("we idling? ", fsm_door.current_state == fsm_door.idle)

        #Check if user pressed O button
        # CHANGE THIS TO READ SENSOR DATA NOT MOCK DATA
        if inputs[4].state == 1 and inputs[0] == 1:
            fsm_door.start_open(airlock_door_ss)
            #door_state, door_angle = door_ss.get_current_door_state(airlock_door_ss)

            # While the door is not open
            #while door_state is not 111:  # replace the line below when sensors implemeneted
            while i is not 1:
                if inputs[0] == 1:
                    fsm_door.keep_opening(airlock_door_ss)
                    i = 1  # Delete once sensor data is implemented & replace with line below to get updated door_state every loop
                    #door_state, door_angle = door_ss.get_current_door_state(airlock_door_ss)
                else:
                    if fsm_door.current_state.name == "Open":
                        fsm_door.detected_emerg_1(airlock_door_ss)
                    elif fsm_door.current_state.name == "Emergency":
                        fsm_door.emerg_unresolved(airlock_door_ss)
            fsm_door.done_open(airlock_door_ss)
        else:
            if(fsm_door.current_state == fsm_door.Emergency):
                fsm_door.emerg_unresolved(airlock_door_ss)
            else:
                # no code red so keep idling
                fsm_door.keep_idling(airlock_door_ss)

        # Check if user pressed C
        if inputs[5].state == 1:  # change to interface logic
            fsm_door.start_close(airlock_door_ss)
            #door_state, door_angle = door_ss.get_current_door_state(airlock_door_ss)

            #while door_state is not 99:  # replace line below with this
            while(j is 0):
                if inputs[0].state == 1:
                    fsm_door.keep_closing(airlock_door_ss)
                    # j var represents when the door is in the processs of closing
                    j = 1
                    #door_state, door_angle = door_ss.get_current_door_state(airlock_door_ss)
                else:
                    if(fsm_door.current_state == fsm_door.Emergency):
                        fsm_door.emerg_unresolved(airlock_door_ss)
                    else:
                        fsm_door.detected_emerg_2(airlock_door_ss)
            fsm_door.done_close(airlock_door_ss)
        else:
            if(fsm_door.current_state == fsm_door.Emergency):
                fsm_door.emerg_unresolved(airlock_door_ss)
            else:
                fsm_door.keep_idling(airlock_door_ss)
        print("Current Pressure State: ", fsm_pressure.current_state.name)
        print("Current Door State: ", fsm_door.current_state.name)
        print("Current Light State: ", fsm_lights.current_state.name, "\n")

loop_FSMs(subsystems,
          inputs)
