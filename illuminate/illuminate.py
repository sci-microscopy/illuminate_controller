import serial
import os
import glob
import time
import json
import numpy as np


class IlluminateController():
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
        """Unload and load the device."""

        # Unload device
        self.unload()

        # Create new device and set baud rate
        self.interface = serial.Serial(self.com_port)
        self.interface.baudrate = self.baud_rate

    def unload(self):
        """Close device if it is open."""
        if self.interface is not None and self.interface.is_open:
            self.interface.close()

    def reset(self):
        """Reset the device."""
        self.command('reset')

    def clear(self):
        self.command('x')

    def printTriggerSettings(self):
        print(self.command('ptr'))

    def setupTriggering(self, channel, trigger_pulse_width_us, trigger_start_delay_us):
        self.command('trs.' + str(int(channel)) + '.' + str(int(trigger_pulse_width_us)) + '.' + str(int(trigger_start_delay_us)))

    def getLedArrayParametersDict(self):
        # Get parameters
        raw = self.command('pprops')

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
    def led_position_list_cart(self, append_led_numbers=False):

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

        # Remove LED number if requested
        if not append_led_numbers:
            source_list_cart = [list(source_list_cart[i][1:]) for i in range(len(source_list_cart))]

        # Return
        return source_list_cart

    @property
    def led_position_list_na(self, append_led_numbers=False):

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


    def setSequenceBitDepth(self, bit_depth=8):
        allowed_bit_depths = [1, 8]
        if bit_depth in allowed_bit_depths:
            self.illumination_sequence_bit_depth = bit_depth
            self.command('ssbd.' + str(bit_depth))
        else:
            raise ValueError('Invalid bit depth (%d)' % bit_depth)

    def sequenceReset(self):
        """Reset a sequence."""
        self.command('x')
        time.sleep(0.01)
        self.command('reseq')
        self.state_index = 0

    def sequenceStep(self):
        '''
        Triggers represents the trigger output from each trigger pin on the teensy. The modes can be:
        0 : No triggering
        1 : Trigger at start of frame
        2 : Trigger each update of pattern
        '''
        cmd = 'sseq.' + str(self.trigger_output_settings[0]) + '.' + str(self.trigger_output_settings[1])
        self.command(cmd)

    def runSequence(self, n_acquisitions=1):
        ''' Wrapper class for fast and normal (Serial) sequences '''

        # Determine sequence_dt_ms
        self.sequence_dt_ms = np.mean(np.diff(np.append(0, self.time_sequence_s_preload))) * 1000.
        if self.use_fast_sequence:
            self._runSequenceFast(n_acquisitions=n_acquisitions)
        else:
            self._runSequence(n_acquisitions=n_acquisitions)

    def _runSequence(self, n_acquisitions=1):
        '''
        Triggers represents the trigger output from each trigger pin on the teensy. The modes can be:
        0 : No triggering
        1 : Trigger at start of frame
        2 : Trigger each update if pattern
        3 : Exposure control of camera
        '''
        if self.trigger_input_settings[0] + self.trigger_input_settings[1] > 0:
            sequence_dt_ms_to_use = self.min_sequence_dt_ms
            print('Using mininum sequence dt because of trigger feedback')
        else:
            sequence_dt_ms_to_use = self.sequence_dt_ms

        cmd = 'rseq.' + str(int(np.round(sequence_dt_ms_to_use))) + "." + str(n_acquisitions) + "." + str(self.trigger_output_settings[0]) + '.' + str(self.trigger_output_settings[1]) + '.' + str(self.trigger_input_settings[0]) + '.' + str(self.trigger_input_settings[1]) + '.' + str(self.trigger_frame_time_s[0]) + '.' + str(self.trigger_frame_time_s[1])

        self.command(cmd, wait_for_response=False)

    def _runSequenceFast(self, n_acquisitions=1):
        '''
        Triggers represents the trigger output from each trigger pin on the teensy. The modes can be:
        0 : No triggering
        1 : Trigger at start of frame
        2 : Trigger each update if pattern
        3 : Exposure control of camera
        '''
        # Convert to us
        sequence_dt = int(self.sequence_dt_ms * 1000)
        frame_dt = str(int(max(self.trigger_frame_time_s[0], self.trigger_frame_time_s[1])))

        cmd = 'rseqf.' + str(sequence_dt) + '.' + str(frame_dt) + '.' + str(n_acquisitions) + "." + str(self.trigger_output_settings[0]) + '.' + str(self.trigger_output_settings[1]) + '.' + str(self.trigger_input_settings[0]) + '.' + str(self.trigger_input_settings[1])

        # Send command
        self.command(cmd, wait_for_response=False)

    def preloadSequence(self, frame_index=-1, state_sequence=None, time_sequence_s=None):

        # Preload whole sequence
        if state_sequence is None:
            self.state_sequence_preload = self.state_sequence
            self.time_sequence_s_preload = self.time_sequence_s
        else:
            self.state_sequence_preload = state_sequence
            self.time_sequence_s_preload = time_sequence_s

        if type(frame_index) is list:
            tmp = [self.state_sequence_preload[index] for index in frame_index]
            tmp_t = [self.time_sequence_s_preload[index] for index in frame_index]
            self.state_sequence_preload = [[item for sublist in tmp for item in sublist]]
            time_sequence_s_preload = [[item for sublist in tmp_t for item in sublist]]
        else:
            # Select subset of preload if it's provided
            if frame_index >= 0:
                self.state_sequence_preload = [self.state_sequence_preload[frame_index]]
                self.time_sequence_s_preload = [self.time_sequence_s_preload[frame_index]]

            else:
                self.state_sequence_preload = [[item for sublist in self.state_sequence_preload for item in sublist]]
                self.time_sequence_s_preload = [[item for sublist in self.time_sequence_s_preload for item in sublist]]

        # Determine sequence length
        led_sequence_length = 0
        for frame_sequence in self.state_sequence_preload:
            led_sequence_length += len(frame_sequence['states'])

        # Set sequence length (ssl)
        self.command('ssl.' + str(led_sequence_length))

        pattern_count = 0
        contiguous_zero_count = 0
        # Send each sequence to led array
        for frame_sequence in self.state_sequence_preload:

            # Loop over all time points
            for pattern_index, time_point_pattern in enumerate(frame_sequence['states']):

                # Define command
                cmd = ''

                # loop over all LEDs in this sequence
                led_count = 0
                for led_pattern in time_point_pattern:
                    if sum(list(led_pattern['value'].values())) > 0:
                        cmd += '.' + str(led_pattern['index'])
                        led_count += 1
                        for color_channel_name in self.color_channels:
                            if self.illumination_sequence_bit_depth > 1:
                                cmd += '.' + str(int(led_pattern['value'][color_channel_name])) # numerical (8 or 16 bit) sequence
                            else:
                                cmd += '.' + str(int(led_pattern['value'][color_channel_name] > 0)) # Binary sequence

                if led_count == 0:
                    contiguous_zero_count += 1
                    if pattern_index == len(frame_sequence['states']) - 1:
                        cmd_z = 'ssz.' + str(contiguous_zero_count)
                        contiguous_zero_count = 0
                        print(self.command(cmd_z))
                else:
                    if contiguous_zero_count > 0:
                        cmd_z = 'ssz.' + str(contiguous_zero_count)
                        contiguous_zero_count = 0
                        self.command(cmd_z)
                    cmd = 'ssv.' + str(led_count) + cmd

                    # Send command
                    self.command(cmd)

                # Incriment pattern counr
                pattern_count += 1

if __name__ == "__main__":
    # execute only if run as a script
    import sys

    if len(sys.argv) > 1:
        port = sys.argv[1]
        led = LedArrayController(port)
        if len(sys.argv) > 2:
            print(led.command(sys.argv[2]))
