% This file shows some examples of how to control the LED array using the
% serial interface. Keep in mind that all commands which are used here are
% common across ALL platforms (python, Arduino terminal, Micro-Manager,
% etc.
%
% Written by:
% Z. Phillips
% SCI Microscopy, Inc.
% Berkeley, CA
% zack@sci-microscopy.com
%
% License: BSD 3-clause

% NOTE: To view help from the LED array, open the Arduino terminal and type
% the command "?" without quotes. This will list all commands and their
% usage.
%
% Arduino software settings: baud=115200, ending=Newline
% Ensure Teensyduino software is installed before running this script.
% https://www.pjrc.com/teensy/teensyduino.html
%
%
%% Set up serial interface
% Note that if this cell fails, make sure all programs which are using the
% serial port are closed. As a last resort, restart the computer.

% Define LED array port (Get this from the device manager in Windows, or
% the Arduino software (Tools -> Port).
led_array_port = 'COM10';

% close all serial connections
delete(instrfindall);

% Open new connections to arduinos
led_array = serial(led_array_port,'BaudRate',115200,'DataBits',8);
fopen(led_array);

% Set flow control to software
led_array.FlowControl = 'software';


%% Display brightfield pattern
% This pattern respects the array distance ('sad' command) and numerical 
% aperature ('na' command).

fprintf(led_array, 'bf', 'async');

%% Clear the array
fprintf(led_array, 'x', 'async');

%% Display annular pattern
% This pattern respects the array distance ('sad' command) and numerical 
% aperature ('na' command).
fprintf(led_array, 'an', 'async');

%% Display dpc pattern
% This pattern respects the array distance ('sad' command) and numerical 
% aperature ('na' command). Also see the "rdpc" command
fprintf(led_array, 'dpc.t', 'async');
pause(1)
fprintf(led_array, 'dpc.b', 'async');
pause(1)
fprintf(led_array, 'dpc.l', 'async');
pause(1)
fprintf(led_array, 'dpc.r', 'async');
pause(1)

%% Change Colors using hard-coded values

fprintf(led_array, 'sc.red', 'async');
pause(0.1)

fprintf(led_array, 'bf', 'async');
pause(1)

fprintf(led_array, 'sc.green', 'async');
pause(0.1)
fprintf(led_array, 'bf', 'async');
pause(1)

fprintf(led_array, 'sc.blue', 'async');
pause(0.1)
fprintf(led_array, 'bf', 'async');
pause(1)

fprintf(led_array, 'sc.white', 'async');
pause(0.1)
fprintf(led_array, 'bf', 'async');
pause(1)

%% Set brightness

fprintf(led_array, 'sc.green', 'async');
pause(0.1)
fprintf(led_array, 'l.0', 'async');
pause(0.5)

fprintf(led_array, 'sb.10', 'async');
pause(0.1)
fprintf(led_array, 'l.0', 'async');
pause(0.5)

fprintf(led_array, 'sb.64', 'async');
pause(0.1)
fprintf(led_array, 'l.0', 'async');
pause(0.5)

fprintf(led_array, 'sb.128', 'async');
pause(0.1)
fprintf(led_array, 'l.0', 'async');
pause(0.5)

fprintf(led_array, 'sb.255', 'async');
pause(0.1)
fprintf(led_array, 'l.0', 'async');
pause(0.5)

%% Draw individual LEDs
% The syntax to draw LEDs is l.[led#].[led#].[led#].[led#].[led#]
% The number of LEDs does not matter. Note that LED numbers start from zero
% and move outward from the center.
fprintf(led_array, 'l.0', 'async');
pause(1)
fprintf(led_array, 'l.1', 'async');
pause(1)
fprintf(led_array, 'l.2', 'async');
pause(1)
fprintf(led_array, 'l.0.1.2', 'async');
pause(1)
fprintf(led_array, 'l.51.101.0.20.50.20', 'async');
pause(1)

%% Draw a color DPC pattern
% Pattern for this paper:
% https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0171228

fprintf(led_array, 'cdpc', 'async')

%% Set numerical aperture (NA)

% Turn down brightness to limit current draw
fprintf(led_array, 'sb.32', 'async');
pause(0.1)

% NA = 0.1
fprintf(led_array, 'na.10', 'async');
pause(0.1)
fprintf(led_array, 'bf', 'async');
pause(0.5)

% NA = 0.25
fprintf(led_array, 'na.25', 'async');
pause(0.1)
fprintf(led_array, 'bf', 'async');
pause(0.5)

% NA = 0.50
fprintf(led_array, 'na.50', 'async');
pause(0.1)
fprintf(led_array, 'bf', 'async');
pause(0.5)

% NA = 0.65
fprintf(led_array, 'na.65', 'async');
pause(0.1)
fprintf(led_array, 'bf', 'async');
pause(0.5)

% NA = 0.80
fprintf(led_array, 'na.80', 'async');
pause(0.1)
fprintf(led_array, 'bf', 'async');
pause(0.5)

%% Set LED Array distance
% The led array distance is measured from the top edge of the center board
% downward to the sample plane.

% Turn down brightness to limit current draw
fprintf(led_array, 'sb.32', 'async');
pause(0.1)
fprintf(led_array, 'na.40', 'async');
pause(0.1)

% dist = 60mm
fprintf(led_array, 'sad.60', 'async');
pause(0.5)
fprintf(led_array, 'bf', 'async');
pause(0.5)

% dist = 50mm
fprintf(led_array, 'sad.50', 'async');
pause(0.5)
fprintf(led_array, 'bf', 'async');
pause(0.5)

% dist = 40mm
fprintf(led_array, 'sad.40', 'async');
pause(0.5)
fprintf(led_array, 'bf', 'async');
pause(0.5)

% dist = 30mm
fprintf(led_array, 'sad.30', 'async');
pause(0.5)
fprintf(led_array, 'bf', 'async');
pause(0.5)

% Reset to 50mm
fprintf(led_array, 'sad.50', 'async');
pause(0.5)

%% Run a DPC Sequence
% DPC sequences are hard-coded for speed and support hardware triggering
% the command format is:
%
% rdpc.[Delay between each pattern in ms].[Number of acquisitions].[trigger mode for index 0].[trigger mode for index 1].[trigger mode for index 2]
% 
% The trigger modes are defined as follows:
% mode > 0: Trigger (or wait for a trigger every "mode" frames
% mode == 0: No triggering
% mode == -1: Trigger at the start of each acquisition
% mode == -2: Trigger only once at the begenning of the command
%
% Note that this command can run multiple "Acquisitions" which means it
% will run through the full DPC sequence more than once. This is set using
% the second command.
% 
% Also note that setting the delay (first parameter) to less than ~40ms
% will result in the array doing nothing. You will see an error if you
% watch the terminal. The exact lower limit will depend on the specific
% hardware of your array, as this limit is checked based on feedback from
% the hardware (not a hard-coded limit).

% 2x DPC patterns, updating every 500ms, no triggering
fprintf(led_array, 'x', 'async');
pause(0.5)
fprintf(led_array, 'rdpc.500.2', 'async');
pause(0.5)

% 2x DPC patterns, updating every 500ms, with trigger outputs only (every
% frame
fprintf(led_array, 'x', 'async');
pause(0.5)
fprintf(led_array, 'rdpc.500.2.1.0.0', 'async');
pause(0.5)

% 2x DPC patterns, updating every 500ms, with trigger outputs and inputs 
% (every frame)
fprintf(led_array, 'x', 'async');
pause(0.5)
fprintf(led_array, 'rdpc.500.2.1.0.1', 'async');
pause(0.5)

% The above command may fail if your camera is not configured correcly.
% Check that the trigger ports and camera software are sane if you
% experience trouble.

%% Run a FPM Sequence
% FPM sequences are hard-coded for speed and support hardware triggering
% the command format is:
%
% rdpc.[Delay between each pattern in ms].[Number of acquisitions].[Maximum NA]. [trigger mode for index 0].[trigger mode for index 1].[trigger mode for index 2]
% 
% The trigger modes are defined as follows:
% mode > 0: Trigger (or wait for a trigger every "mode" frames
% mode == 0: No triggering
% mode == -1: Trigger at the start of each acquisition
% mode == -2: Trigger only once at the begenning of the command
%
% Note that this command can run multiple "Acquisitions" which means it
% will run through the full DPC sequence more than once. This is set using
% the second command.
%
% The Maximum NA parameter determines the max NA used for this acquisition.
% Note that a NA of 0.25 would result in setting this parameter to "25"
% 
% Also note that setting the delay (first parameter) to less than ~40ms
% will result in the array doing nothing. You will see an error if you
% watch the terminal. The exact lower limit will depend on the specific
% hardware of your array, as this limit is checked based on feedback from
% the hardware (not a hard-coded limit).

% 1x FPM patterns, updating every 50ms, 0.50 max NA, no triggering
fprintf(led_array, 'x', 'async');
pause(0.5)
fprintf(led_array, 'rfpm.50.1.50', 'async');
pause(0.5)

% 2x FPM patterns, updating every 50ms, 0.25 max NA, no triggering
fprintf(led_array, 'x', 'async');
pause(0.5)
fprintf(led_array, 'rfpm.50.2.25', 'async');
pause(0.5)

% 2x DPC patterns, updating every 50ms, with trigger outputs only (every
% frame), all LEDs (NA = 1.0 => 100)
fprintf(led_array, 'x', 'async');
pause(0.5)
fprintf(led_array, 'rfpm.500.2.100.1.0.0', 'async');
pause(0.5)

% 2x DPC patterns, updating every 500ms, with trigger outputs and inputs 
% (every frame)
fprintf(led_array, 'x', 'async');
pause(0.5)
fprintf(led_array, 'rfpm.500.2.100.1.0.1', 'async');
pause(0.5)

% The above command may fail if your camera is not configured correcly.
% Check that the trigger ports and camera software are sane if you
% experience trouble.







