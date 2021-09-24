import mplfinance as mpf
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import math
import os


class Plot:

    color = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
             '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

    def __init__(self):
        self._save_path = ''
        self._suffix = '.png'

    def set_save_path(self, save_path):
        self._save_path = save_path

    def plot_ohlc_all(self, data, block=True, save=False):
        """
        :param data: [{code:code0, df:dataframe0(ohlc)}, {code:code1, df:dataframe1(ohlc)}, ...]
        :param block: if block is False when plot shows, plot run backend
        :param save: if save is True, plot is saved, don't show
        """
        if save:
            if os.path.exists(self._save_path):
                save_path_names = []
                for i in range(len(data)):
                    save_path_name = self._save_path + '\\chart' + f"_{i}" + self._suffix
                    save_path_names.append(save_path_name)
                    mpf.plot(data[i]['df'], style='yahoo', type='candle', title=data[i]['code'],
                             savefig=save_path_name)
                return save_path_names
            else:
                raise Exception('Save path {} does not exist.'.format(self._save_path))

        else:
            page, limit = 0, min(8, len(data))  # page starts 0
            max_page = math.ceil(len(data) / limit)
            fig = mpf.figure(figsize=(12, 9), style='yahoo')
            fig.subplots_adjust(left=0.03, bottom=0.2, right=0.95, top=0.95, hspace=0.2)
            axes = []

            for i in range(limit):
                ax = fig.add_subplot(2, 4, i+1)
                axes.append(ax)
                mpf.plot(data[i]['df'], ax=ax, type='candle', axtitle=data[i]['code'])

            def button_prev(event):
                nonlocal page, limit, max_page
                nonlocal data
                nonlocal axes, axtext
                page = (page - 1) if page > 0 else max_page - 1
                replot_ohlc(data, axes, page, limit, axtext)

            def button_next(event):
                nonlocal page, limit, max_page
                nonlocal data
                nonlocal axes, axtext
                page = (page + 1) % max_page
                replot_ohlc(data, axes, page, limit, axtext)

            def replot_ohlc(data, axes, page, limit, axtext):
                axtext.clear()
                axtext.text(0.4, 0.2, '{:2d} / {:2d}'.format(page+1, max_page))

                for ax in axes:
                    ax.clear()
                for i, ax in enumerate(axes):
                    idx = i + (page * limit)
                    if idx >= len(data):
                        break
                    mpf.plot(data[idx]['df'], ax=ax, type='candle', axtitle=data[idx]['code'])

            # make prev or next button
            axprev = fig.add_axes([0.7, 0.05, 0.1, 0.075])
            axnext = fig.add_axes([0.81, 0.05, 0.1, 0.075])
            bprev = Button(axprev, '◀')
            bnext = Button(axnext, '▶')
            bnext.on_clicked(button_next)
            bprev.on_clicked(button_prev)

            # make current page representation
            axtext = fig.add_axes([0.5, 0.05, 0.1, 0.075])
            axtext.text(0.4, 0.2, '{:2d} / {:2d}'.format(page+1, max_page))

            mpf.show(block=block)

    def plot_profit(self, groups, means, gmeans, stddevs, block=True, save=False):
        """
        Set plot about profit mean, geometric mean and standard deviation.
        day : x-axis
        means, gmeans, stddev : y-axis
        """
        day = [i for i in range(1, len(means[0])+1)]
        plt.figure('Profit Graph')
        plt.subplot(2, 2, 1)
        plt.title('Profit Graph')
        plt.xlabel('Days')
        plt.ylabel('Profit')
        plt.legend()
        for i, (mean, gmean, group) in enumerate(zip(means, gmeans, groups)):
            plt.plot(day, mean, color=Plot.color[i], label=f"[G_{group}] mean", linestyle='-')
            plt.plot(day, gmean, color=Plot.color[i], label=f"[G_{group}] g_mean", linestyle='-.')

        plt.subplot(2, 1, 1)
        plt.title('Stddev Graph')
        plt.xlabel('Days')
        plt.ylabel('StdDev')
        plt.legend()
        for i, (stddev, group) in enumerate(zip(stddevs, groups)):
            plt.plot(day, stddev, color=Plot.color[i], label=f"[G_{group}] stddev")

        if save:
            if os.path.exists(self._save_path):
                save_path_name = self._save_path + '\\profit' + self._suffix
                plt.savefig(save_path_name)
                return save_path_name
            else:
                raise Exception('Save path {} does not exist.'.format(self._save_path))
        else:
            plt.show(block=block)
