#!/usr/bin/python3

__author__ = 'rcope'

from PyHT6022.LibUsbScope import Oscilloscope
import time
import numpy as np
from collections import deque

sample_rate_index = 24
voltage_range = 0x01
data_points = 3 * 1024

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

ch1_dq = deque(maxlen=2*1024*1024)
ch2_dq = deque(maxlen=2*1024*1024)


def extend_callback(ch1_data, ch2_data):
    ch1_dq.extend(ch1_data)
    ch2_dq.extend(ch2_data)


rec_time = 5

start_time = time.time()
print("Clearing FIFO and starting data transfer...")
scope.start_capture()
shutdown_event = scope.read_async(extend_callback, data_points,
                                  outstanding_transfers=10, raw=True)
while time.time() - start_time < rec_time:
    scope.poll()
scope.stop_capture()
print("Stopping new transfers.")
shutdown_event.set()
print("Snooze 1")
time.sleep(1)
print("Closing handle")
scope.close_handle()
print("Handle closed.")
print("Points in buffer:", len(ch1_dq))

scaled_ch1 = scope.scale_read_data(ch1_dq, voltage_range)
scaled_ch2 = scope.scale_read_data(ch2_dq, voltage_range)

np.save("./ch1.npy", scaled_ch1)
np.save("./ch2.npy", scaled_ch2)

