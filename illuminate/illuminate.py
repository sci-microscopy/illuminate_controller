import serial
import os
import glob
import time
import json
import numpy as np


class LedArrayController():
    '''
    This is a class for controlling a LED array device
    '''

    def __init__(self, com_port, baud_rate=115200):

        # Store parameters
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.interface = None

        # Define trigger constants
        self.TRIGGER_MODE_NONE = 0
        self.TRIGGER_MODE_START = 1      # Triggering at the start of each acquisition
        self.TRIGGER_MODE_ITERATION = 2  # Triggering each illumination change

        # Misc
        self.sequence_dt_ms = None
        self.color_channels = ['r', 'g', 'b']
        self.color_channel_center_wavelengths = None
        self.use_fast_sequence = False
        self.command_debug = False

        # Initialize device variables
        self.trigger_output_settings = None
        self.trigger_input_settings = None
        self.bit_depth = None
        self.device_name = None
        self.led_count = None
        self.color_channels = None
        self.color_channel_center_wavelengths = None

        # Serial command and response terminators
        self.response_terminator = '-==-\n'
        self.command_terminator = '\n'
        self.serial_read_timeout_s = 5
        self.serial_write_timeout_s = 5

        # Load device
        self.reload()

        # Set mode to machine
        self.command('machine')

        # Get relevent parameters
        time.sleep(0.1)  # ensures the reset command is not still running from the previous line
        self.getLedArrayParameters()

    @property
    def na(self):
        return float(self.command('na', wait_for_response=True).split('NA.')[1].split('\n')[0]) / 100.0

    @na.setter
    def na(self, new_na):
        self.command('na.%d' % int(new_na * 100.0))

    @property
    def array_distance(self):
        return float(self.command('sad', wait_for_response=True).split('DZ.')[1].split('\n')[0])

    @array_distance.setter
    def array_distance(self, new_na):
        self.command('sad.%d' % int(new_na))

    def command(self, cmd, wait_for_response=True):
        '''
        Sends a command to serial device and then waits for any response, then returns it
        '''
        # Flush buffer
        self.flush()

        # Send command
        if self.command_debug > 0:
            print(cmd)

        if self.interface.is_open:
            self.interface.write(str.encode(cmd) + str.encode(str(self.command_terminator)))
        else:
            raise ValueError('Serial port not open!')

        # Get response
        if wait_for_response:
            response = self.response()

            # Print the response, for debugging
            if self.command_debug > 1:
                print(response)

            # Return response
            return(response)


    def response(self, timeout_s=5):
        '''
        Gets response from device
        '''
        if self.interface.is_open:
            response = self.interface.read_until(str.encode(str(self.response_terminator))).decode("utf-8")

            # Remove response_terminator
            response.replace(self.response_terminator, '')

            if 'ERROR' in response:
                raise ValueError(response.split('ERROR'))
            elif len(response) == 0:
                return None
            else:
                return response
        else:
            raise ValueError('Serial port not open!')

    def flush(self):
        '''
        Flushes serial buffer
        '''
        if self.interface.is_open:
            self.interface.read_all()
        else:
            raise ValueError('Serial port not open!')

    def reload(self):
        # Close device if it is open
        if self.interface is not None and self.interface.is_open:
            self.interface.close()

        # Create new device and set baud rate
        self.interface = serial.Serial(self.com_port)
        self.interface.baudrate = self.baud_rate

    def clear(self):
        self.command('x')

    def printTriggerSettings(self):
        print(self.command('ptr'))

    def setupTriggering(self, channel, trigger_pulse_width_us, trigger_start_delay_us):
        self.command('trs.' + str(int(channel)) + '.' + str(int(trigger_pulse_width_us)) + '.' + str(int(trigger_start_delay_us)))

    def getLedArrayParametersDict(self):
        # Get parameters
        raw = self.command('pp')

        # Filter serial stream
        filtered = str(raw).replace('\\n', ' ').replace('\\r', '').replace('-==-', '').replace('     ', ' ').replace("'", "\"")[0:-1]

        # Convert to dict using json package
        try:
            params_dict = json.loads(filtered)
        except ValueError:
            print('Parse error! String:')
            print(filtered)
            params_dict = None

        return(params_dict)

    def getLedArrayParameters(self):
        # Ask LED array for system parameters
        params_dict = self.getLedArrayParametersDict()
        if params_dict is not None:
            self.trigger_output_settings = (0,) * int(params_dict['trigger_output_count'])
            self.trigger_input_settings = (0,) * int(params_dict['trigger_input_count'])
            self.bit_depth = int(params_dict['bit_depth'])
            self.device_name = str(params_dict['device_name'])
            self.led_count = int(params_dict['led_count'])
            self.color_channels = params_dict['color_channels']
            self.color_channel_center_wavelengths = params_dict['color_channel_center_wavelengths']

    @property
    def led_positions_cart(self, append_led_numbers=False):

        # Send serial command
        lines = self.command('pledpos').replace(self.response_terminator, '').replace('\n', '')

        # Parse Serial string
        led_positions = json.loads(lines)

        # Convert to cartesian source list
        source_list_cart = []
        for led in led_positions['led_position_list_cartesian']:
            source_list_cart.append([int(led),
                                     led_positions['led_position_list_cartesian'][led][0],
                                     led_positions['led_position_list_cartesian'][led][1],
                                     led_positions['led_position_list_cartesian'][led][2]])

        # Sort by first led number
        source_list_cart = sorted(source_list_cart, key=lambda x: x[0])

        # Remove LED number if requested
        if not append_led_numbers:
            source_list_cart = [list(source_list_cart[i][1:]) for i in range(len(source_list_cart))]

        # Return
        return source_list_cart

    @property
    def led_positions_na(self, append_led_numbers=False):

        # Send serial command
        lines = self.command('pledposna').replace(self.response_terminator, '').replace('\n', '')

        # Parse Serial string
        led_positions = json.loads(lines)

        # Convert to cartesian source list
        source_list_cart = []
        for led in led_positions['led_position_list_na']:
            source_list_cart.append([int(led),
                                     led_positions['led_position_list_na'][led][0],
                                     led_positions['led_position_list_na'][led][1]])

        # Sort by first led number
        source_list_cart = sorted(source_list_cart, key=lambda x: x[0])

        # Remove LED number if requested
        if not append_led_numbers:
            source_list_cart = [list(source_list_cart[i][1:]) for i in range(len(source_list_cart))]

        # Return
        return source_list_cart

    def setNa(self, new_na):
        '''
        Sets numerical aperture of led array
        '''
        self.command("na." + str(int(np.round(new_na * 100))))

    def setArrayDistance(self, new_distance):
        self.command("sad." + str(int(np.round(new_distance * 100))))

    def setColor(self, new_color):
        cmd = "sc"
        if type(new_color) is str:
            cmd += new_color
        elif type(new_color) is dict:
            for color_channel_name in self.color_channels:
                cmd += '.' + str(new_color[color_channel_name])
        else:
            raise ValueError("Color %s is not valid." % str(new_color))
            return
        self.command(cmd)

    def setAutoClear(self, auto_clear_tf):
        if auto_clear_tf:
            self.command('ac.1')
        else:
            self.command('ac.0')

    def bf(self):
        self.command('bf')
