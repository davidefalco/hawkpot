import os
import time
import subprocess
import datetime
import sys

if not os.path.exists("./logbak"):
    print("logbak folder does not exist, creating it...")
    subprocess.call(["mkdir", "./logbak"])

if os.path.exists("./proxy/log/access.log") and os.path.exists("./proxy/log/error.log"):
    while(1):
        try:
            subprocess.call(["cp", "./proxy/log/access.log", "./logbak/"])
            subprocess.call(["cp", "./proxy/log/error.log", "./logbak/"])
            with open('log_manager.log', 'a+') as log:
                log.write('Backup created at ' + str(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')))
                log.write('\n')
            time.sleep(100)
        except KeyboardInterrupt:
            print("\nExiting...\n")
            sys.exit()
else:
    print("./proxy/log/ directory does not exists, check your hawkpot installation")