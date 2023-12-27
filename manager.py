import json
import yaml
import subprocess
import os
import sys

# configuration file from user
with open("./config.json", "r") as conf:
    conf_j = json.loads(conf.read())

sub_ip = conf_j["subnets_ip_address_start"]
subnets = conf_j["subnets"]
start_port = conf_j["start_port"]
dns = conf_j["dns"]

template_yaml = {
    'version':'3',
    'services':{},
    'networks':{}
}

networks_list = []
for i in range(1, subnets + 1):
    networks_list.append(f'lan{str(i)}')

# reverse proxy service
revproxy = {
    'rev':{
        'image':'nginx',
        'ports':['443:443'],
        'volumes':['./proxy/log:/var/log/nginx/', './proxy/ssl:/etc/nginx/ssl', './proxy/conf:/etc/nginx/conf.d'],
        'networks':networks_list
    }
}

template_yaml['services'].update(revproxy)

ip = sub_ip.split(".")

# default.conf configuration for the proxy
if not os.path.exists("./proxy/conf/default.conf"):
    subprocess.call(["mkdir", "-p", "./proxy/conf"])
    default_conf = 'server{\n\tlisten 443 ssl;\n\tserver_name '+dns+';\n\n\tssl_certificate /etc/nginx/ssl/nginx-selfsigned.crt;\n\tssl_certificate_key /etc/nginx/ssl/nginx-selfsigned.key;\n\n\t'
    for i in range (1, subnets + 1):
        wp_ip = str(ip[0])+'.'+str(ip[1])+'.'+str(int(ip[2]) + i)+'.1'
        default_conf = ''.join([default_conf, f'location /hp{i}'+' {\n\t\t'+'proxy_set_header Host $host;\n\t\tproxy_set_header X-Real-IP $remote_addr;\n\t\tproxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\t\tproxy_set_header X-Forwarded-Proto $scheme;\n\t\tproxy_set_header X-Forwarded-URI $request_uri;\n\t\tproxy_redirect http:// https://;\n\t\t'+f'proxy_pass http://{wp_ip}:{start_port+i}/hp{i};\n\t'+'}'])

    default_conf = ''.join([default_conf, '\n}'])
    with open('./proxy/conf/default.conf', 'w') as proxyconf:
        proxyconf.write(default_conf)   

#sys.exit()

for i in range(1, subnets + 1):
    plg_command = ''
    thm_command = ''

    for plugin in conf_j[f'{i}']['plugin']:
        if plugin['name'] is not None and plugin['version'] is not None:
            plugin_name = plugin['name']
            plugin_version = plugin['version']
            plg_command = ''.join([plg_command, f'wp plugin install --path=/var/www/html/hp{i} {plugin_name} --version={plugin_version} --activate --allow-root\n'])

    for theme in conf_j[f'{i}']['theme']:
        if theme['name'] is not None and theme['version'] is not None:
            theme_name = theme['name']
            theme_version = theme['version']
            thm_command = ''.join([thm_command, f'wp theme install --path=/var/www/html/hp{i} {theme_name} --version={theme_version} --activate --allow-root\n'])
    

    wp_service_name = 'wp' + str(i)
    db_service_name = 'db' + str(i)
    volume_name = f'./hp{str(i)}/wp-content' + str(i) + '/'
    wpcli_service_name = 'wpcli' + str(i)

    lan_name = 'lan' + str(i)
    db_port = str(3305 + i)
    port = str(start_port + i)
    ip = sub_ip.split(".")
    subnet = str(ip[0])+'.'+str(ip[1])+'.'+str(int(ip[2]) + i)+'.'+str(ip[3])+'/24'
    wp_ip = str(ip[0])+'.'+str(ip[1])+'.'+str(int(ip[2]) + i)+'.5' # fixed ip address for all wp services

    update_service_db = {
        db_service_name:{
            'image':'mysql:5.7',
            'networks':[lan_name], 
            'ports':[f'{db_port}:{str(3306)}'],
            'restart':'always', 
            'environment':{
                'MYSQL_ROOT_PASSWORD':'${MYSQL_ROOT_PASS}',
                'MYSQL_DATABASE':'${MYSQL_DB_NAME}', 
                'MYSQL_USER':'${MYSQL_USER}',
                'MYSQL_PASSWORD':'${MYSQL_PASS}'
            }
        }
    }

    update_service_wp = {
        wp_service_name:{
            'depends_on':[db_service_name],
            'image':'wordpress:${WORDPRESS_VERSION}',
#            'user':'33:33',
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
                'WORDPRESS_DB_USER':'${WORDPRESS_DB_USER}',
                'WORDPRESS_DB_PASSWORD':'${WORDPRESS_DB_PASS}',
                'WORDPRESS_DB_NAME':'${MYSQL_DB_NAME}'                 
            }
        }
    }

    update_service_wpcli = {
        wpcli_service_name:{
            'depends_on':[db_service_name, wp_service_name],
            'image':'wordpress:cli',
            'user':'33:33',
            'networks':[lan_name],
            'volumes_from':[wp_service_name],
            'environment':{
                'WORDPRESS_DB_HOST': f'{db_service_name}', #:{str(db_port)}
                'WORDPRESS_DB_USER':'${WORDPRESS_DB_USER}',
                'WORDPRESS_DB_PASSWORD':'${WORDPRESS_DB_PASS}',
                'WORDPRESS_DB_NAME':'${MYSQL_DB_NAME}'                 
                },
            'command':f''' 
                    /bin/sh -c '
                    sleep 60;
                    wp core install --path=/var/www/html/hp{i} --url={dns}:{port}/hp{i} --title=\"${{BLOG_TITLE}}\" --admin_name=${{WORDPRESS_ADMIN}} --admin_password=${{WORDPRESS_ADMIN_PSW}} --admin_email=${{WORDPRESS_MAIL}}
                    wp search-replace --path=/var/www/html/hp{i} 'http://{dns}:{port}/hp{i}' 'http://{dns}/hp{i}'
                    {plg_command}
                    {thm_command}
                    '
                    '''
        }
    }

    update_net = {
        lan_name:
            {'ipam':
                {'driver':'default',
                    'config':
                        [{'subnet':subnet}]
                }
            }
    }

    template_yaml['services'].update(update_service_db)
    template_yaml['services'].update(update_service_wp)
    template_yaml['services'].update(update_service_wpcli)
    template_yaml['networks'].update(update_net)

out = yaml.dump(template_yaml, sort_keys=False)

print(out)


    



