import json
import yaml
import subprocess
import os
import time
import sys
import configuration_parser as parser
from threading import Thread

def log_manager():
    subprocess.call(['python3', 'log_manager.py'])

def intrusion_detector():
    subprocess.call(['python3', 'intrusion_detector.py'])

# checking for -s flag (save to file)
user_filename = ''
redirection_flag = False
if '-s' in sys.argv:
    index = sys.argv.index('-s')
    if len(sys.argv) >= index + 2:
        user_filename = sys.argv[index + 1]
        redirection_flag = True
    else: 
        print("Place a name for your file redirection, use: python3 manager.py -s <filename>")
        sys.exit()

# checking for --no-save-rules flag (to not backup old iptables rules)
user_saveipt_config = False
if not '--no-save-rules' in sys.argv:
    parser.save_rules()
        
# configuration file from user
with open("./config.json", "r") as conf:
    conf_j = json.loads(conf.read())

sub_ip = conf_j["subnets_ip_address_start"]
subnets = conf_j["subnets"]
start_port = conf_j["start_port"]
dns = conf_j["dns"]
ip = sub_ip.split(".")

networks_list = []
title_list = []
for i in range(1, subnets + 1):
    networks_list.append(f'lan{str(i)}')
    title_list.append(conf_j[f"{i}"]["title"])


ipt_rules = parser.create_rules(subnets, ip)
with open('rules.sh', 'w') as file:
    file.write(ipt_rules)

#sys.exit()
    
template_yaml = {
    'version':'3',
    'services':{},
    'networks':{}
}

# make reverse proxy service
revproxy = parser.make_rev_proxy_service(networks_list, ip)
template_yaml['services'].update(revproxy)

# default.conf configuration for the proxy
if not os.path.exists("./proxy/conf/default.conf"):
    default_conf = parser.proxy_configuration(dns, subnets, ip, start_port)
    with open('./proxy/conf/default.conf', 'w') as proxyconf:
        proxyconf.write(default_conf)   

# make wp, mysql, wpcli services
for i in range(1, subnets + 1):
    plg_command = parser.plugins_command(conf_j, i)
    thm_command = parser.themes_command(conf_j, i)

    wp_service_name = 'wp' + str(i)                         # name for wp services
    db_service_name = 'db' + str(i)                         # name for db services
    wpcli_service_name = 'wpcli' + str(i)                   # name for wpcli services
    volume_name = f'./hp{str(i)}/wp-content' + str(i) + '/' # volume for wp services
    lan_name = 'lan' + str(i)                               # name for lans
    port = str(start_port + i)                              # port for wp services
    db_port = str(3305 + i)                                 # port for db services

    ip = sub_ip.split(".")
    subnet = str(ip[0])+'.'+str(ip[1])+'.'+str(int(ip[2]) + i)+'.'+str(ip[3])+'/24'
    wp_ip = str(ip[0])+'.'+str(ip[1])+'.'+str(int(ip[2]) + i)+'.5' # last byte of each ip address for each wp service is 5

    update_service_wp = parser.make_wp_service(wp_service_name, db_service_name, lan_name, wp_ip, port, volume_name, i)
    update_service_db = parser.make_db_service(wp_service_name, lan_name, db_port)
    update_service_wpcli = parser.make_wpcli_service(wpcli_service_name, db_service_name, wp_service_name, lan_name, i, dns, port, title_list, plg_command, thm_command)
    update_net = parser.make_network(lan_name, subnet)

    template_yaml['services'].update(update_service_db)
    template_yaml['services'].update(update_service_wp)
    template_yaml['services'].update(update_service_wpcli)
    template_yaml['networks'].update(update_net)

out = yaml.dump(template_yaml, sort_keys=False)

if redirection_flag:
    with open(user_filename, 'w') as f:
        f.write(out)
else: 
    if '--no-verbose' not in sys.argv:
        print(out)

if '--no-apply-rules' not in sys.argv:
    subprocess.call(['sudo', 'sh', './rules.sh'])

log_manager_thread = Thread(target = log_manager)
intrusion_detector_thread = Thread(target = intrusion_detector)
log_manager_thread.daemon = True
intrusion_detector_thread.daemon = True
log_manager_thread.start()
intrusion_detector_thread.start()

try:
    time.sleep(1)
    subprocess.call(['tail', '-f', 'log_manager.log', 'intrusions.log'])
except KeyboardInterrupt:
    print('Exiting...')
    sys.exit()