import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import math
import numpy as np
import csv

style.use('fivethirtyeight')


class Sensor:
    # Get figure objects from sensor to the

    # Store information
    def __init__(self, n_sec=0.25, scaling=200):
        self.n_sec = n_sec
        self.interval = 0.0
        self.scaling = scaling
        self.values = list() # Voltage values on the y-axis
        self.mapped_data = list() # The mapped values from the delta voltage values
        self.mapped_time = list() # The ms values converted to seconds
        self.time = list()  # Time values on the x-axis
        self.fig = plt.figure()
        self.ax1 = self.fig.add_subplot(1,1,1)

        self.handValues = ()
    # OLD FUNCTION
    # def mapData(self):
    #     slope = 0
    #     mapped_val = 0
    #     loop_interval = self.calc_interval()
    #     loop_interval = math.ceil(loop_interval)
    #     loop_interval = int(loop_interval)
    #
    #     for i in range(0, len(self.values)-1, loop_interval):
    #         if i >= len(self.values) or i+loop_interval >= len(self.values):
    #             break
    #         else:
    #             slope = (self.values[i+loop_interval] - self.values[i]) / loop_interval
    #             slope /= self.scaling
    #
    #             if slope < 0:
    #                 slope = math.floor(slope)
    #             elif slope > 0:
    #                 slope = math.ceil(slope)
    #
    #             if slope > 4:
    #                 slope = 4
    #             elif slope < -4:
    #                 slope = -4
    #             self.mapped_data.append(int(slope))

    # Implement regression analysis, create a "moving window" for data to stream in and recalculate the regression each
    #   time window moves
    # Hopefully, passing in data writes to an output file that is read dynamically, can just do "write line" after each
    #   calculation sequence.
    # Write new line at the end.

    def mapData(self):
        window_size = 20

        # loop interval creates a new line based on update times?
        loop_interval = self.calc_interval()
        loop_interval = math.ceil(loop_interval)
        loop_interval = int(loop_interval)

        # Loop through the GSR values
        for i in range(window_size, len(self.values)-1, 1):
            mapped_val = self.calcGSR(i, window_size)

            self.mapped_data.append(int(mapped_val))

            # Call write function after this.

    def calcGSR(self, index, window_size):
        # Get the sample window size
        window_low = index - window_size
        window_high = index
        if window_low < 0:
            window_low = 0;

        window_sample_time = self.time[window_low: window_high]
        window_sample_values = self.values[window_low: window_high]

        # Get linear approximation of the slope of window data
        slope, intercept = np.polyfit(window_sample_time, window_sample_values, 1)
        mapped_val = slope * self.scaling

        if mapped_val < 0:
            mapped_val = -(math.exp(-mapped_val) - 1)
            print(window_low, ",", window_high, ",", slope, ",", mapped_val)
            mapped_val = math.ceil(mapped_val)

        elif mapped_val > 0:
            mapped_val = math.exp(mapped_val) - 1
            print(window_low, ",", window_high, ",", slope, ",", mapped_val)
            mapped_val = math.floor(mapped_val)

        if mapped_val > 4:
            mapped_val = 4
        elif mapped_val < -4:
            mapped_val = -4

        return mapped_val

    # This calculates the total length of the recording
    def mapTime(self):
        if len(self.time) > 0:
            return self.time[len(self.time)-1] / 1000
        return 1

    # send 3 bools for positive/negative quadrants of position
    # send 3 bools for each speed of the velocity

    def calc_hand_stuff(self, in_file):
        out = []
        for line in in_file:
            hand_data = line.strip('\n').replace('(', '').replace(')', '').replace(' ', '').split(',')
            # print(hand_data)
            left_hand = hand_data[2:5]
            right_hand = hand_data[5:8]
            left_velocity = hand_data[8:11]
            right_velocity = hand_data[11:]

            print("-------------------------")
            print(left_hand)
            print(right_hand)
            print(left_velocity)
            print(right_velocity)
            sum_left = sum_right = rV = lV = 0
            if left_hand and not left_hand[0] == '':
                sum_left = float(left_hand[0]) + float(left_hand[1]) + float(left_hand[2])
            if right_hand and not right_hand[0] == '':
                sum_right = float(right_hand[0]) + float(right_hand[1]) + float(right_hand[2])

            pTolerance = 500
            vTolerance = 300
            lV, rV = self.calc_hand_velocity(left_velocity, right_velocity, vTolerance)

            if sum_left < pTolerance:
                out.append(-1)
            elif sum_left > pTolerance:
                out.append(1)
            else:
                out.append(0)

            if sum_right < pTolerance:
                out.append(-1)
            elif sum_right > pTolerance:
                out.append(1)
            else:
                out.append(0)

            out.append(lV)
            out.append(rV)
        return out

    def calc_hand_velocity(self, left_velocity, right_velocity, vTolerance):
        tolerance = vTolerance
        lV = rV = 0

        if not left_velocity:
            sum = 0
            for v in left_velocity:
                v += sum
            if sum > tolerance:
                lV = 1
            elif sum < tolerance:
                lV = -1
        if not right_velocity:
            sum = 0
            for v in right_velocity:
                v += sum
            if sum > tolerance:
                rV = 1
            elif sum < tolerance:
                rV = -1
        return lV, rV

    def calc_interval(self):
        print(self.n_sec)
        print((len(self.values)/self.mapTime()))
        self.interval = self.n_sec * (len(self.values)/self.mapTime())
        return self.interval

    # Making two "add data" objects for the moment. Need to adjust object-oriented nature in the future
    def addGSRData(self, time_stamp, data):
        self.values.append(data)
        self.time.append(time_stamp)
        # We won't calculate data until we hit certain intervals of the list
        # if len(self.values) <= self.interval:
        #     self.values.append(data)
        #     self.time.append(time_stamp)
        # else:
        #     self.values.append(data)
        #     self.time.append(time_stamp)
        #     self.mapped_data.append(self.mapData(data))
        #     self.mapped_time.append(self.mapTime(time_stamp))

    # In future iterations, merge addHandData and addGSRData to one method
    def addHandData(self, data):
        self.handValues = data

    def readData(self, file_name):
        f = open(file_name, 'r')
        for line in f:
            cols = line.split(',')
            print(cols)
            cols[0].strip('\n').replace(' ', '').replace('(', '').replace(')', '')
            cols[1].strip('\n').replace(' ', '').replace('(', '').replace(')', '')
            self.addGSRData(int(cols[1]), int(cols[0]))
            self.addHandData(cols[2])
        self.mapData()
        print(self.handValues)

    def process_data(self, file_in):
        retval = []
        self.readData(file_in)
        retval.append(self.mapped_data)
        retval.append(self.calc_hand_stuff(open(file_in, 'r')))

        return retval

    def output_data(self, fIn, fOut):
        processed = self.process_data(fIn)
        print(processed[0])
        with open(fOut, 'w') as f:
            for i in range(len(processed[0])):
                f.write("{0}, {1}, {2}\n".format(processed[0][i],processed[1][i], processed[1][i+1]))
        f.close()

    def animate(self,i):
        xs = self.mapped_time
        ys = self.mapped_data
        self.ax1.clear()
        self.ax1.plot(xs, ys)

    def makeFigure(self):
        ani = animation.FuncAnimation(self.fig, self.animate, interval=1000)
        plt.show()


# Test Code
s = Sensor()
# s.readData("test1.csv")
# #s.makeFigure()
# #print(len(s.values))
# print(s.mapped_data)
# print(s.mapTime())
# print(s.calc_interval())
s.output_data("output.txt", "fancy-out.txt")
