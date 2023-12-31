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
            print("Backup created at " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            time.sleep(300)
        except KeyboardInterrupt:
            print("\nExiting..\n")
            sys.exit()
else:
    print("./proxy/log/ directory does not exists, check your hawkpot installation")