import matplotlib.pyplot as plt

class Plot:

    color = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
             '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

    def __init__(self):
        pass

    def show(self):
        plt.show()

    def plot_ohlc(self):
        pass

    def plot_profit(self, day, groups, means, gmeans):
        '''
        Set plot about profit mean and geometric mean
        day : x-axis
        means, gmeans : y-axis
        '''
        plt.figure('Profit Graph')
        plt.title('Profit Graph')
        plt.xlabel('Days')
        plt.legend()
        for i, mean, gmean, group in enumerate(zip(means, gmeans, groups)):
            plt.plot(day, mean, color=Plot.color[i], label=f"[G_{group}] mean", linestyle='-')
            plt.plot(day, gmean, color=Plot.color[i], label=f"[G_{group}] g_mean", linestyle='-.')

    def plot_profit_stddev(self, day, groups, stddevs):
        '''
        Set plot about profit standard deviation
        '''
        plt.figure('Stddev Graph')
        plt.title('Stddev Graph')
        plt.xlabel('Days')
        plt.legend()
        for i, stddev, group in enumerate(zip(stddevs, groups))
            plt.plot(day, stddev, color=Plot.color[i], label=f"[G_{group}] stddev")
