#!/usr/bin/python3

from PyHT6022.LibUsbScope import Oscilloscope
import time
import h5py as h5

sample_rate_index = 1
voltage_range = 0x02
data_points = 3 * 1024
outstanding_transfers = 10
num_channels = 2
rec_time = 30*60
fs = sample_rate_index*(10**(6 if sample_rate_index < 50 else 3))

scope = Oscilloscope()
scope.setup()
scope.open_handle()
scope.flash_firmware()
scope.set_interface(1)  # choose ISO
scope.set_num_channels(2)
scope.set_sample_rate(sample_rate_index)
scope.set_ch1_voltage_range(voltage_range)
scope.set_ch2_voltage_range(voltage_range)
time.sleep(1)

maxsize = rec_time * fs
size = 0

with h5.File('rec.h5', 'w') as f:
    data = f.create_dataset("data", (2, maxsize), maxshape=(2, maxsize),
                            dtype='uint8')

    def extend_callback(ch1_data, ch2_data):
        global size
        dsize = len(ch1_data)
        if size < maxsize - dsize:
            data[0, size:(size + dsize)] = ch1_data
            data[1, size:(size + dsize)] = ch2_data
            size += dsize
        return size < maxsize - dsize

    print("Clearing FIFO and starting data transfer...")
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

