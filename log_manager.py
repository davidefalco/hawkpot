import os
import time
import subprocess
import datetime
import sys
import shutil

def get_latest_subdir(dir : str):
    all_subdirs = os.listdir(dir)
    max_date = None
    for subdir in all_subdirs:
        if max_date is None:
            max_date = os.path.getmtime(dir + subdir)
            max_pos = all_subdirs.index(subdir)
        
        if os.path.getmtime(dir) > max_date:
            max_date = os.path.getmtime(dir + subdir)
            max_pos = all_subdirs.index(subdir)

    return all_subdirs[max_pos]

def create_log(compose_file_digest):
    while(True):
        try:
            if not os.path.exists('./log_manager.log'):
                with open('./log_manager.log', 'a+') as log:
                    log.write('Backup file created for logging ingormation about log_manager actions\n')

            today_datetime = datetime.datetime.today()
            today_date = today_datetime.strftime('%Y-%m-%d')
            today_time = today_datetime.strftime('%H:%M:%S')
            goal_time = datetime.time(12, 37, 00).strftime('%H:%M:%S')
            if today_time == goal_time:
                if os.path.exists("./proxy/log/access.log") and os.path.exists("./proxy/log/error.log"):
                    shutil.move('./proxy/log/access.log', './logbak/' + compose_file_digest + "/access.log." + str(today_date))
                    shutil.move('./proxy/log/error.log', './logbak/' + compose_file_digest + '/error.log.' + str(today_date))
                    #subprocess.run(["sudo", "mv", "./proxy/log/access.log", "./logbak/" + compose_file_digest + "/access.log." + str(today_date)], input = (sudo_pass + '\n'), text = True)
                    #subprocess.run(["sudo", "mv", "./proxy/log/error.log", "./logbak/" + compose_file_digest + "/error.log." + str(today_date)], input = (sudo_pass + '\n'), text = True)
                    subprocess.run(["docker", "compose", "exec", "rev", "service", "nginx", "reload"])
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

def start_log_manager(compose_file_digest : str, compose_filename : str):
    if not os.path.exists("./logbak"):
        # print("logbak folder does not exist, creating it...")
        subprocess.call(["mkdir", "./logbak"])
    
    if not os.path.exists('./logbak/' + compose_file_digest):
        # if ./logbak/latest_hashed_composition does not exist
        # composition is changed, so before create bak folder
        # for current composition, access.log and error.log
        # should be moved inside the latest bak folder created
        if os.path.exists('./proxy/log/access.log') and os.path.exists('./proxy/log/error.log'):
            today_datetime = datetime.datetime.today()
            today_date = today_datetime.strftime('%Y-%m-%d')
            latest_subdir = get_latest_subdir('./logbak/')
            logs_in_dir = [dir for dir in os.listdir('./logbak/' + latest_subdir)]
            i = 0
            if 'access.log.' + str(today_date) in logs_in_dir:
                while('access.log.' + str(today_date) + f'.{i}' in logs_in_dir):
                    i += 1

                shutil.move('./proxy/log/access.log', './logbak/' + latest_subdir + "/access.log." + str(today_date) + f'.{i}')
                shutil.move('./proxy/log/error.log', './logbak/' + latest_subdir + '/error.log.' + str(today_date) + f'.{i}')
            else:
                shutil.move('./proxy/log/access.log', './logbak/' + latest_subdir + "/access.log." + str(today_date))
                shutil.move('./proxy/log/error.log', './logbak/' + latest_subdir + '/error.log.' + str(today_date))

        subprocess.call(["mkdir", "-p", "./logbak/" + compose_file_digest])
        subprocess.call(['cp', compose_filename, './logbak/' + compose_file_digest])
    
    create_log(compose_file_digest)

    
