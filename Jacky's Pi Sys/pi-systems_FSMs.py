# Written by Noah Caleanu for Mars Colony's Airlock Project
# This is the most updated FSM code.

# ________________________SECTION 1_______________________________________

# INITIALIZATION OF EVERYTHING.  Some things may be redundant bc already
# in pi-main_primary.py.  Comment out the duplicates if necessary

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

ON = 1
OFF = 0

# Import the subsystems & relevant modules
#subsys_inter = importlib.import_module('pi-systems_interface-subsystem')  # UNCOMMENT THIS TO RUN ON PI
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
    door_close_butt = subsys_inter.InputComponent(name='Cl', pin=35, subtype='Button')
    emergency_butt = subsys_inter.InputComponent(name='E', pin=36, subtype='Button')
    SPST_toggle = subsys_inter.InputComponent(name='Enable P/D/H', pin=37, subtype='Switch')
    pause_butt = subsys_inter.InputComponent(name='H', pin=38, subtype='Button')
    confirm_butt = subsys_inter.InputComponent(name='C', pin=40, subtype='Button')
    # Add to inputs list
    inputs.append(emergency_butt)
    inputs.append(pressure_butt)
    inputs.append(depressure_butt)
    inputs.append(lights_toggle)
    inputs.append(door_open_butt)
    inputs.append(door_close_butt)
    inputs.append(power_toggle)
    inputs.append(pause_butt)
    inputs.append(confirm_butt)

except NameError:
    print("Skipping input component declarations.")


outputs = []

try:
    led1 = subsys_inter.OutputComponent(name='Pressurized LED',
                                        pin=11,
                                        subtype='LED')  # LEDs initial state OFF
    led2 = subsys_inter.OutputComponent(name='In Progress LED',
                                        pin=12,
                                        subtype='Depressurized LED')
    led3 = subsys_inter.OutputComponent(name='LED_3',
                                        pin=13,
                                        subtype='LED')
    led4 = subsys_inter.OutputComponent(name='STSD Active LED',
                                        pin=15,
                                        subtype='LED')
    led5 = subsys_inter.OutputComponent(name='Confirm LED',
                                        pin=16,
                                        subtype='LED')
    led6 = subsys_inter.OutputComponent(name='Emergency LED',
                                        pin=18,
                                        subtype='LED')
    led7 = subsys_inter.OutputComponent(name='Hold LED',
                                        pin=19,
                                        subtype='LED')
    # Add outputs to the list
    outputs.append(led1)
    outputs.append(led2)
    outputs.append(led3)
    outputs.append(led4)
    outputs.append(led5)
    outputs.append(led6)
    outputs.append(led7)

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

# ________________END OF SECTION 1_______________________________________


# ________________________SECTION 2_______________________________________

# For debugging purposes bc i cant use an interface components remotely
# COMMENT OUT SECTION 2 AND USE SECTION 1 CODE ON THE PI

# this is for debugging purposes only.
inputs = [1,  # E
          1,  # P
          0,  # D
          0,  # L
          0,  # O
          0,  # Cl
          1,  # SPST
          0,  # H
          0]  # C


class led:                          # this is for debugging purposes only.
    def __init__(self, name, initial=False):
        self.name = name
        self.state = initial

    def write(self, value):
        self.state = value

# this is for debugging purposes only.
led1 = led(name="Pressurized LED")
led2 = led(name="IP LED")
led3 = led(name="Depressurized LED")
led4 = led(name='SPST Active')
led5 = led(name="Confirm LED")
led6 = led(name="Emergency LED")
led7 = led(name="Pause LED")

outputs = [led1, led2, led3, led4, led5, led6, led7]

# ________________END OF SECTION 2_____________________________________________

#  Create an instance of the FSMs
fsm_pressure = FSM.PressureFSM()
fsm_lights = FSM.LightFSM()
fsm_door = FSM.DoorFSM()

# Integer Target pressures for pressurizing and depressurizing
target_p = 1013  # Earth atmosphere roughly 101.3kPa
target_d = 6     # Martian Atmosphere 600 Pascals

# ________________________SECTION 3_______________________________________
# loop that checks the inputs and takes the appropriate actions.
# IMPORTANT NOTE: Replace "inputs[0].state", etc., etc.
#  with "emergency_butt", etc. etc. for more readable code.


def loop_FSMs(subsystems,
              inputs,
              outputs):
    #pressure = sensor_ss.sensor_data[3]  # Replace the line below once sensors
    pressure = 0

    while(True):
        # i and j are used for very general mock door state ...
        # i = 0 represents door not in desired state
        # i = 1 represents door in desired state
        i = 0   # door_state, door_angle = door_ss.get_current_door_state(airlock_door_ss)  #  Might give Attribute Error?
        j = 0   # Represents same thing as i but for closing door so just delete when sensors implemented

        # Comment this out for now bc interface inputs cannot be used
        '''
        print("E button: ", inputs[0].state)
        print("P button: ", inputs[1].state)
        print("D button: ", inputs[2].state)
        print("L switch: ", inputs[3].state)
        print("O button: ", inputs[4].state)
        print("Cl button: ", inputs[5].state)
        print("SPST Enable", inputs[6].state)
        '''

        # Check if user pressed Emergency button
        # NOTE EMERG LOGIC IS ACTIVE LOW
        if inputs[0].state == 0:
            emergency = True  # theres really no point in this besides an easier way to display Emergencies to user
            if(fsm_pressure.current_state.name == 'idle'):
                fsm_pressure.detected_emerg_3(airlock_press_ss, outputs)
            elif(fsm_pressure.current_state.name == 'Emergency'):
                fsm_pressure.emerg_unresolved(airlock_press_ss, outputs)
            if(fsm_door.current_state.name == 'Idle'):
                fsm_door.detected_emerg_3(airlock_door_ss)
            elif(fsm_door.current_state.name == 'Emergency'):
                fsm_door.emerg_unresolved(airlock_door_ss)

        # Check if the STSD switch enables the P/D/H buttons
        if inputs[6].state == 1:
            led4.write(ON)

            # Check if user pressed P
            # CHANGE THIS TO READ SENSOR DATA NOT MOCK DATA: pressure
            if (inputs[1].state == 1 and inputs[0].state == 1):
                fsm_pressure.start_pressurize(airlock_press_ss, outputs)

                # While not done pressurizing to targer...
                #while (sensor_ss.sensor_data[3] < target_p):  # REPLACE LINE BELOW WITH THIS FOR SENSORS
                while (pressure < target_p):
                    if inputs[0].state is 1:  # check for emerg. while pressurizing
                        if inputs[7].state == 1:  # check if user wants to pause
                            if fsm_pressure.current_state.name == "pressurize":
                                fsm_pressure.pause_press(airlock_press_ss, outputs)
                                while inputs[7].state is 1:
                                    fsm_pressure.keep_pausing(airlock_press_ss)
                                fsm_pressure.resume_press(airlock_press_ss, outputs)
                        else:
                            # This is for no pausing & no emergencies.
                            fsm_pressure.keep_pressurize(airlock_press_ss, outputs)
                            time.sleep(0.001)           # Take this out when sensors implemented
                            pressure = pressure + 1     # Take this out when sensors implemented
                            #sensor_ss.__update_sensor_data()  # Not sure if the sensors are read continuously but update the sensor value
                            print("PRESSURIZING...")
                    else:
                        if(fsm_pressure.current_state == fsm_pressure.Emergency):
                            fsm_pressure.emerg_unresolved(airlock_press_ss, outputs) # Emerg to Emerg
                        else:
                            fsm_pressure.detected_emerg_1(airlock_press_ss, outputs) # Press to Emerg
                fsm_pressure.done_pressurize(airlock_press_ss, outputs)
            else:
                if(fsm_pressure.current_state == fsm_pressure.Emergency):
                    fsm_pressure.emerg_unresolved(airlock_press_ss, outputs)
                else:
                    fsm_pressure.keep_idling(airlock_press_ss)

            # Check if user pressed D
            # CHANGE THIS TO READ SENSOR DATA NOT MOCK DATA
            if inputs[2].state == 1 and inputs[0].state == 1:
                pressure = 1013  # For debugging. Delete when sensors implemented
                fsm_pressure.start_depressurize(airlock_press_ss, outputs)
                #while (sensor_ss.sensor_data[3] < target_d):  # REPLACE LINE BELOW WITH THIS FOR SENSORS
                while(pressure > target_d):
                    if inputs[0].state == 1:
                        if inputs[7].state == 1:
                            if fsm_pressure.current_state.name == 'depressurize':
                                fsm_pressure.pause_depress(airlock_press_ss, outputs)
                                while inputs[7].state is 1:
                                    fsm_pressure.keep_pause(airlock_press_ss)
                                fsm_pressure.resume_depress(airlock_press_ss, outputs)
                        else:
                            fsm_pressure.keep_depressurize(airlock_press_ss, outputs)
                            time.sleep(0.001)            # Take this out when sensors implemented
                            pressure = pressure - 1  # Take this out when sensors implemented
                            print("DEPRESSURIZING")
                    else:
                        if(fsm_pressure.current_state == fsm_pressure.Emergency):
                            fsm_pressure.emerg_unresolved(airlock_press_ss, outputs)
                        else:
                            fsm_pressure.detected_emerg_2(airlock_press_ss, outputs)    
                    # sensor_ss.__update_sensor_data()  # Might need to manually update. check how sensors are read
                fsm_pressure.done_depressurize(airlock_press_ss, outputs)
            else:
                if(fsm_pressure.current_state == fsm_pressure.Emergency):
                    fsm_pressure.emerg_unresolved(airlock_press_ss, outputs)
                else:
                    fsm_pressure.keep_idling(airlock_press_ss)

            print("I am in idle again? ",
                  fsm_pressure.current_state == fsm_pressure.idle)
        else:
            led4.write(OFF)

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
        if inputs[4].state == 1 and inputs[0].state == 1:
            fsm_door.start_open(airlock_door_ss)
            #door_state, door_angle = door_ss.get_current_door_state()

            # While the door is not open
            #while door_state is not 111:  # replace the line below when sensors implemeneted
            while i is not 1:
                if inputs[0].state == 1:
                    fsm_door.keep_opening(airlock_door_ss)
                    #inputs = [0, 0, 0, 0, 1, 0, 1]
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

        # Check if user pressed Cl for close door
        if inputs[5].state == 1 and inputs[0].state == 1:  # change to interface logic
            fsm_door.start_close(airlock_door_ss)

            while(j is 0):
                if inputs[0].state == 1:
                    fsm_door.keep_closing(airlock_door_ss)
                    # j var represents when the door is in the processs of closing
                    j = 1
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

        # Check if the user has confirmed the Door Action
        # This should be moved up into the inputs[4] and inputs[5] loops.
        # CHANGE LATER ^^^ for now it just turns on/off LED
        if inputs[8].state == 1:
            led5.write(ON)
        else:
            led5.write(OFF)

        print("Current Pressure State: ", fsm_pressure.current_state.name)
        print("Current Door State: ", fsm_door.current_state.name)
        print("Current Light State: ", fsm_lights.current_state.name, "\n")

loop_FSMs(subsystems,
          inputs,
          outputs)
