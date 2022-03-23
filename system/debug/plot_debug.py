import matplotlib.pyplot as plt
import csv
  
unixTime = []
current = []

fileName = "/home/che/Documents/pi_logs/4.csv"
  
with open(fileName,'r') as handle:
    lines = csv.reader(handle, delimiter=',')
    for row in lines:
        unixTime.append(int(row[0]))
        current.append(float(row[1]))


plt.plot(unixTime, current)
plt.xlabel('Time')
plt.ylabel('Current (A)')
plt.title('Washing Cycle (Current Draw Over Time)', fontsize = 20)
plt.show()