#!/usr/bin/env python3

from PyHT6022.LibUsbScope import Oscilloscope
import time
import h5py as h5
import sys
from tqdm import tqdm

fs = 1e6
voltage_range = 1
data_points = 3 * 1024
outstanding_transfers = 10
num_channels = 2
rec_time = int(sys.argv[1])*60

scope = Oscilloscope()
scope.setup()
scope.open_handle()
if (not scope.is_device_firmware_present):
    scope.flash_firmware()
calibration = scope.get_calibration_values()
scope.set_interface(0)
scope.set_num_channels(2)
if fs < 1e6:
    sample_id = int(100 + fs/10e3)
else:
    sample_id = int(fs/1e6)
scope.set_sample_rate( sample_id )

scope.set_ch1_voltage_range(voltage_range)
scope.set_ch2_voltage_range(voltage_range)
time.sleep(1)

maxsize = rec_time * fs
size = 0

with h5.File(sys.argv[2], 'w') as f:
    data = f.create_dataset("data", (2, maxsize), maxshape=(2, maxsize),
                            dtype='uint8')

    print("Clearing FIFO and starting data transfer...")
    with tqdm(total=maxsize) as t:
        def extend_callback(ch1_data, ch2_data):
            global size
            dsize = len(ch1_data)
            if (len(ch1_data) > 0 and len(ch2_data) > 0) and\
                    (max(ch1_data) > 255 or max(ch2_data) > 255):
                raise ValueError("Value too big for uint8")
            if size < maxsize - dsize:
                data[0, size:(size + dsize)] = ch1_data
                data[1, size:(size + dsize)] = ch2_data
                size += dsize
                t.update(dsize)
            return size < maxsize - dsize

        scope.start_capture()
        shutdown_event = scope.read_async(extend_callback, data_points,
                                          outstanding_transfers=outstanding_transfers,
                                          raw=True)
        stime = time.time()
        while size < maxsize - data_points//num_channels:
            scope.poll()
    print("Time:", time.time() - stime)
    scope.stop_capture()
    print("Stopping new transfers.")
    shutdown_event.set()
    print("Snooze 1")
    time.sleep(1)
    print("Closing handle")
    scope.close_handle()
    print("Handle closed.")
    data.resize(size, 1)

print("Points saved:", size, "of", maxsize)

