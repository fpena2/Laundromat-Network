import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

df = pd.read_csv("./a.csv")
xs = list(df.loc[:, 'sample'])
ys = list(df.loc[:, 'value'])

xdata = []
ydata = []

fig = plt.figure()
ax = plt.axes(xlim=(0, 45), ylim=(0, 7))
line, = ax.plot([], [], lw=2)
plt.ylabel('Current (A)')
plt.xlabel('Sample')


def init():
    line.set_data([], [])
    return line,


def animate(i):
    # print(i)
    xdata.append(xs[i])
    ydata.append(ys[i])
    line.set_data(xdata, ydata)
    return line,


ani = animation.FuncAnimation(fig, animate, init_func=init,
                              interval=100, blit=True, save_count=50, frames=60, repeat=False)

# To save the animation, use e.g.
#
ani.save("movie.mp4")
#
# or
#
# writer = animation.FFMpegWriter(
#     fps=15, metadata=dict(artist='Me'), bitrate=1800)
# ani.save("movie.mp4", writer=writer)
# ani.event_source.stop()

plt.show()
