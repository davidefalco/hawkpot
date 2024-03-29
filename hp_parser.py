import sys
import json
import configuration_parser as parser
import yaml

# configuration file from user (comf.json)
try:
    with open("./config.json", "r") as conf:
        conf_j = json.loads(conf.read())
except IOError:
    print('file config.json does not found\n')
    sys.exit()
    
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

template_yaml = {
    'version':'3',
    'services':{},
    'networks':{}
}

# make reverse proxy service
revproxy = parser.make_rev_proxy_service(networks_list, ip)
template_yaml['services'].update(revproxy)

# default.conf configuration for the proxy
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

    update_service_wp = parser.make_wp_service(wp_service_name, db_service_name, lan_name, wp_ip, port, volume_name, i, conf_j)
    update_service_db = parser.make_db_service(db_service_name, lan_name, db_port, i, conf_j)
    update_service_wpcli = parser.make_wpcli_service(wpcli_service_name, db_service_name, wp_service_name, lan_name, i, port, plg_command, thm_command, conf_j)
    update_net = parser.make_network(lan_name, subnet)

    template_yaml['services'].update(update_service_db)
    template_yaml['services'].update(update_service_wp)
    template_yaml['services'].update(update_service_wpcli)
    template_yaml['networks'].update(update_net)

out = yaml.dump(template_yaml, sort_keys=False)

print(out)