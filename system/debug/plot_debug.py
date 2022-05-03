import matplotlib.pyplot as plt
import csv
from glob import glob
from time import sleep

MAX_LIMIT = 1500

logDir = "/home/che/Documents/pi_logs/*.csv"
logs = glob(logDir)

for log in logs:
    unixTime = []
    current = []
    with open(log, 'r') as handle:
        lines = csv.reader(handle, delimiter=',')
        limit = 0
        for row in lines:
            limit += 1
            # unixTime.append(int(row[0]))
            unixTime.append(limit)
            current.append(float(row[1]))
            if limit > MAX_LIMIT:
                break

    plt.plot(unixTime, current)
    plt.xlabel('Time')
    plt.ylabel('Current (A)')
    plt.title('Washing Cycle (Current Draw Over Time)', fontsize=20)
    plt.savefig(f'{log}.png')
    plt.close()
