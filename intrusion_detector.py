import time
import os
import sys

def follow(file):
    file.seek(0, os.SEEK_END)
    while True:
        try:
            line = file.readline()
            if not line or not '\n':
                time.sleep(0.5)
                continue
            yield line
        except KeyboardInterrupt:
            print('\nExiting...\n')
            sys.exit()

if __name__ == '__main__':
    logfile = open('/var/log/kern.log', 'r')
    loglines = follow(logfile)
    print('Intrustion detector started...\n')

    for line in loglines:
        # print(line)
        if 'WARN' in line:
            splitted_line = line.split(" ")
            for word in splitted_line:
                if 'WARN' in word:
                    print('Intrusion detected in ' + word[5:] + '\n')
                    print(line)