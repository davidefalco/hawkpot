import subprocess

def clear_rules():
    with open('./.clear-rules') as clear:
        subprocess.run(['sudo', 'iptables-restore'], stdin = clear)
    # it is supposed that if user start manager he does not start composition yet
    subprocess.call(['sudo', 'service', 'docker', 'restart'])

def create_rules(subnets : int, ip : list):
    ipt_rules = '#!/bin/sh\nsudo iptables -D DOCKER-USER 1\n'
    for i in range(1, subnets + 1):
        # filling the bash file for iptables rules
        ipt_rules = ''.join([ipt_rules, f'sudo iptables -N COUNT_HP{i}\n', 
                            f'sudo iptables -A COUNT_HP{i} -m limit --limit 50/day --limit-burst 50 -j ACCEPT\n', 
                            f'sudo iptables -A COUNT_HP{i} -j LOG --log-prefix \' WARN_HP{i} \'\n',
                            f'sudo iptables -A COUNT_HP{i} -j REJECT --reject-with icmp-port-unreachable\n',
                            f'sudo iptables -A DOCKER-USER -s {str(ip[0])+"."+str(ip[1])+"."+str(int(ip[2]) + i)+".5"} ! -d {str(ip[0])+"."+str(ip[1])+"."+str(int(ip[2]) + i)+".10"} -p tcp --dport 443 -j COUNT_HP{i}\n'])
    return ipt_rules

'''
def save_rules():
    # saving current docker iptables' rules
    ipt_command = ['sudo', 'iptables-save']
    print('Saving current docker iptables\' rules. Plase be sure your docker service is started.')
    subprocess.run(ipt_command, stdout = open('current-iptables.save', 'w'), check = True)
'''

def make_rev_proxy_service(networks_list : list, ip : list):
    net_rev_proxy = {}
    j = 1
    for net in networks_list:
        # ip address for each interface of reverse proxy is x.x.x.10
        inner_net = {
            f'{net}':{
                'ipv4_address': str(ip[0])+'.'+str(ip[1])+'.'+str(int(ip[2]) + j)+'.10'
            }
        }
        net_rev_proxy.update(inner_net)
        j += 1
    
    # reverse proxy services
    revproxy = {
        'rev':{
            'image':'nginx',
            'ports':['443:443'],
            'volumes':['./proxy/log:/var/log/nginx/', './proxy/ssl:/etc/nginx/ssl', './proxy/conf:/etc/nginx/conf.d'],
            'networks': net_rev_proxy
        }
    }
    return revproxy

def make_wp_service(wp_service_name : str, db_service_name : str, lan_name : str, wp_ip : str, port : str, volume_name : str, i : int, conf_j : dict):
    update_service_wp = {
        wp_service_name:{
            'depends_on':[db_service_name],
            'image':f'wordpress:{conf_j[f"{i}"]["WORDPRESS_VERSION"]}',
            #'user':'33:33',
            'networks':{
                f'{lan_name}':{
                    'ipv4_address': f'{wp_ip}'
                }
            },
            'ports':[port + str(':80')],
            'working_dir': f'/var/www/html/hp{i}',
            'volumes':[volume_name + str(f':/var/www/html/hp{str(i)}/wp-content')],#, f'./site{str(i)}/apache2:/etc/apache2/apache2.conf'],
            'restart':'always',
            'environment':{
                'WORDPRESS_DB_HOST': f'{db_service_name}', #:{str(db_port)}
                'WORDPRESS_DB_USER': conf_j[f'{i}']['WORDPRESS_DB_USER'], # WORDPRESS_DB_USER
                'WORDPRESS_DB_PASSWORD':conf_j[f'{i}']['WORDPRESS_DB_PASS'], # WORDPRESS_DB_PASS
                'WORDPRESS_DB_NAME':conf_j[f'{i}']['MYSQL_DB_NAME'] # MYSQL_DB_NAME                
            }
        }
    }
    return update_service_wp

def make_db_service(db_service_name : str, lan_name : str, db_port : str, i : int, conf_j : dict):
    update_service_db = {
        db_service_name:{
            'image':'mysql:5.7',
            'networks':[lan_name], 
            'ports':[f'{db_port}:{str(3306)}'],
            'restart':'always', 
            'environment':{
                'MYSQL_ROOT_PASSWORD': conf_j[f'{i}']['MYSQL_ROOT_PASS'], # MYSQL_ROOT_PASS
                'MYSQL_DATABASE': conf_j[f'{i}']['MYSQL_DB_NAME'], # MYSQL_DB_NAME 
                'MYSQL_USER': conf_j[f'{i}']['MYSQL_USER'], # MYSQL_USER
                'MYSQL_PASSWORD': conf_j[f'{i}']['MYSQL_PASS'] # MYSQL_PASS
            }
        }
    }
    return update_service_db

def make_wpcli_service(wpcli_service_name : str, db_service_name : str, wp_service_name : str, lan_name : str, i : int, port : str, plg_command : str, thm_command : str, conf_j):
    dns = conf_j['dns']
    title = conf_j[f'{i}']['title']
    update_service_wpcli = {
        wpcli_service_name:{
            'depends_on':[db_service_name, wp_service_name],
            'image':'wordpress:cli',
            'user':'33:33',
            'networks':[lan_name],
            'volumes_from':[wp_service_name],
            'environment':{
                'WORDPRESS_DB_HOST': f'{db_service_name}', #:{str(db_port)}
                'WORDPRESS_DB_USER': conf_j[f'{i}']['WORDPRESS_DB_USER'], # WORDPRESS_DB_USER
                'WORDPRESS_DB_PASSWORD': conf_j[f'{i}']['WORDPRESS_DB_PASS'], # WORDPRESS_DB_PASS
                'WORDPRESS_DB_NAME': conf_j[f'{i}']['MYSQL_DB_NAME'] # MYSQL_DB_NAME                 
                },
            'command':f''' 
                    /bin/sh -c '
                    sleep 60;
                    wp core install --path=/var/www/html/hp{i} --url={dns}:{port}/hp{i} --title=\"{title}\" --admin_name={conf_j[f'{i}']["WORDPRESS_ADMIN"]} --admin_password={conf_j[f'{i}']["WORDPRESS_ADMIN_PSW"]} --admin_email={conf_j[f'{i}']["WORDPRESS_MAIL"]}
                    wp search-replace --path=/var/www/html/hp{i} 'http://{dns}:{port}/hp{i}' 'http://{dns}/hp{i}'
                    {plg_command}
                    {thm_command}
                    '
                    '''
        }
    }
    return update_service_wpcli

def make_network(lan_name : str, subnet):
    update_net = {
        lan_name:
            {'ipam':
                {'driver':'default',
                    'config':
                        [{'subnet':subnet}]
                }
            }
    }
    return update_net

def proxy_configuration(dns : str, subnets : int, ip : list, start_port : str):
    subprocess.call(["mkdir", "-p", "./proxy/conf"])
    default_conf = 'server{\n\tlisten 443 ssl;\n\tserver_name '+dns+';\n\n\tssl_certificate /etc/nginx/ssl/nginx-selfsigned.crt;\n\tssl_certificate_key /etc/nginx/ssl/nginx-selfsigned.key;\n\n\t'
    for i in range (1, subnets + 1):
        # wp_ip is ip address for gateway of each honeypot
        wp_ip = str(ip[0])+'.'+str(ip[1])+'.'+str(int(ip[2]) + i)+'.1'
        default_conf = ''.join([default_conf, f'location /hp{i}'+' {\n\t\t'+'proxy_set_header Host $host;\n\t\tproxy_set_header X-Real-IP $remote_addr;\n\t\tproxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\t\tproxy_set_header X-Forwarded-Proto $scheme;\n\t\tproxy_set_header X-Forwarded-URI $request_uri;\n\t\tproxy_redirect http:// https://;\n\t\t'+f'proxy_pass http://{wp_ip}:{start_port+i}/hp{i};\n\t'+'}'])

    default_conf = ''.join([default_conf, '\n}'])
    return default_conf

def plugins_command(conf_j : dict, i : int):
    plg_command = ''
    for plugin in conf_j[f'{i}']['plugin']:
        if plugin['name'] is not None and plugin['version'] is not None:
            plugin_name = plugin['name']
            plugin_version = plugin['version']
            plg_command = ''.join([plg_command, f'wp plugin install --path=/var/www/html/hp{i} {plugin_name} --version={plugin_version} --activate --allow-root\n'])
    return plg_command

def themes_command(conf_j : dict, i : int):
    thm_command = ''
    for theme in conf_j[f'{i}']['theme']:
        if theme['name'] is not None and theme['version'] is not None:
            theme_name = theme['name']
            theme_version = theme['version']
            thm_command = ''.join([thm_command, f'wp theme install --path=/var/www/html/hp{i} {theme_name} --version={theme_version} --activate --allow-root\n'])
    return thm_command