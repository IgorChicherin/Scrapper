# from time import sleep
#
# def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
#     """
#     Call in a loop to create terminal progress bar
#     @params:
#         iteration   - Required  : current iteration (Int)
#         total       - Required  : total iterations (Int)
#         prefix      - Optional  : prefix string (Str)
#         suffix      - Optional  : suffix string (Str)
#         decimals    - Optional  : positive number of decimals in percent complete (Int)
#         length      - Optional  : character length of bar (Int)
#         fill        - Optional  : bar fill character (Str)
#     """
#     percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
#     filledLength = int(length * iteration // total)
#     bar = fill * filledLength + '-' * (length - filledLength)
#     print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
#     # Print New Line on Complete
#     if iteration == total:
#         print()
#
#
# # make a list
# items = list(range(0, 57))
# i = 0
# l = len(items)
#
# # Initial call to print 0% progress
# printProgressBar(i, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
# for item in items:
#     # Do stuff...
#     sleep(0.1)
#     # Update Progress Bar
#     i += 1
#     printProgressBar(i, l, prefix = 'Progress:', suffix = 'Complete', length = 50)

from time import sleep
from random import random
from clint.textui import progress
if __name__ == '__main__':
    for i in progress.bar(range(100)):
        sleep(random() * 0.2)

    # for i in progress.dots(range(100)):
    #     sleep(random() * 0.2)