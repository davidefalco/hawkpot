import os
import time
import subprocess
import datetime
import sys

def create_log(compose_file_digest, sudo_pass):
    while(True):
        try:
            if not os.path.exists('./log_manager.log'):
                with open('./log_manager.log', 'a+') as log:
                    log.write('Backup file created for ' + compose_file_digest + '\n')

            today_datetime = datetime.datetime.today()
            today_date = today_datetime.strftime('%Y-%m-%d')
            today_time = today_datetime.strftime('%H:%M:%S')
            goal_time = datetime.time(18, 10, 00).strftime('%H:%M:%S')
            if today_time == goal_time:
                if os.path.exists("./proxy/log/access.log") and os.path.exists("./proxy/log/error.log"):
                    subprocess.run(["sudo", "mv", "./proxy/log/access.log", "./logbak/" + compose_file_digest + "/access.log." + str(today_date)], input = (sudo_pass + '\n'), text = True)
                    subprocess.run(["sudo", "mv", "./proxy/log/error.log", "./logbak/" + compose_file_digest + "/error.log." + str(today_date)], input = (sudo_pass + '\n'), text = True)
                    subprocess.run(["sudo", "docker", "compose", "exec", "rev", "service", "nginx", "reload"], input = (sudo_pass + '\n'), text = True)
                    with open('log_manager.log', 'a+') as log:
                        log.write('Backup created at ' + str(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')) + ' for configuration: ' + compose_file_digest)
                        log.write('\n')
                
                    time.sleep(100)
                else:
                    with open('log_manager.log', 'a+') as log:
                        log.write('Failed to create backup at ' + str(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')) + ' for configuration: ' + compose_file_digest)
                        log.write('\n')
        except KeyboardInterrupt:
            # print("\nExiting...\n")
            sys.exit()

def start_log_manager(compose_file_digest : str, compose_filename : str, sudo_pass):
    if not os.path.exists("./logbak"):
        # print("logbak folder does not exist, creating it...")
        subprocess.call(["mkdir", "./logbak"])
    
    if not os.path.exists('./logbak/' + compose_file_digest):
        subprocess.call(["mkdir", "-p", "./logbak/" + compose_file_digest])
        subprocess.call(['cp', compose_filename, './logbak/' + compose_file_digest])
    
    create_log(compose_file_digest)

    