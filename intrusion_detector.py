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
    #print('Intrustion detector started...\n')

    if not os.path.exists('./intrusions.log'):
        open('./intrusions.log', 'a+').close()

    for line in loglines:
        if 'WARN' in line:
            splitted_line = line.split(" ")
            for word in splitted_line:
                if 'WARN' in word:
                    with open('intrusions.log', 'a+') as log:
                        log.write('Intrusion detected in ' + word[5:] + '\n')
                        log.write(line)