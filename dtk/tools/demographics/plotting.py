import math
import matplotlib.pyplot as plt

def adjust_spines(ax,spines):
    for loc, spine in ax.spines.items():
        if loc in spines:
            spine.set_position(('outward',10)) # outward by 10 points
            spine.set_smart_bounds(True)
        else:
            spine.set_color('none') # don't draw spine

    # turn off ticks where there is no spine
    if 'left' in spines:
        ax.yaxis.set_ticks_position('left')
    elif 'right' in spines:
        ax.yaxis.set_ticks_position('right')
    else:
        # no yaxis ticks
        ax.yaxis.set_ticks([])

    if 'bottom' in spines:
        ax.xaxis.set_ticks_position('bottom')
    else:
        # no xaxis ticks
        ax.xaxis.set_ticks([])

    ax.tick_params(direction='out')

def plot_nodes(nodes, title=None):
    pops = [n.pop for n in nodes]
    max_pop = max(pops)

    plt.scatter(x=[n.lon for n in nodes],
                y=[n.lat for n in nodes],
                s=[300*p/float(max_pop) for p in pops],
                c=[math.log10(n.density) for n in nodes],
                alpha=0.5,
                cmap='RdYlBu_r',
                vmin=1, vmax=4)

    ax=plt.gca()
    ax.set(aspect=1)
    adjust_spines(ax,['left','bottom'])
    if title:
        plt.title(title)
    cb=plt.colorbar()
    cb.set_ticks(range(1,5))
    cb.set_ticklabels(('10','100','1k','10k'))
    cb.ax.set_ylabel(r'population density ($\mathrm{km}^{-2}$)', rotation=270, labelpad=15)