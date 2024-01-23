import subprocess
import os
import time
import sys
import configuration_parser as parser
import log_manager
import intrusion_detector as detector
import hashlib
import signal
from threading import Thread

def sigterm_handler(_signo, _stack_frame):
    sys.exit(0)

signal.signal(signal.SIGTERM, sigterm_handler)

# clear current iptables rules
parser.clear_rules()

compose_filename = 'not found'
compose_filenames = ['./compose.yml', './compose.yaml']
for filename in compose_filenames:
    if os.path.exists(filename):
        compose_filename = filename

if compose_filename == 'not found':
    # compose file does not found
    sys.exit()

with open(compose_filename, 'r') as compose_file:
    data = compose_file.read()

# hash calculation for compose file
compose_file_digest = hashlib.sha256(data.encode('utf-8')).hexdigest()

if '--no-apply-rules' not in sys.argv:
    subprocess.run(['sh', './rules.sh'])

log_manager_thread = Thread(target = log_manager.start_log_manager, args = [compose_file_digest, compose_filename])
intrusion_detector_thread = Thread(target = detector.start_detector)
log_manager_thread.daemon = True
intrusion_detector_thread.daemon = True
log_manager_thread.start()
intrusion_detector_thread.start()

# send stdout to /dev/null for non verbose mode (> /dev/null 2>&1 &)
# having a service version of hp_manager use:
# - StandardOutput=null
# - StandardError=null

try:
    time.sleep(3)
    subprocess.call(['tail', '-f', 'log_manager.log', 'intrusions.log'])
except KeyboardInterrupt:
    sys.exit()