import json
import yaml

# configuration file from user
with open("./config.json", "r") as conf:
    conf_j = json.loads(conf.read())

sub_ip = conf_j["subnets_ip_address_start"]
subnets = conf_j["subnets"]

template_yaml = {
    'version':'3',
    'services':{},
    'networks':{}
}

for i in range(1, subnets + 1):
    plg_command = ''
    thm_command = ''

    for plugin in conf_j[f'{i}']['plugin']:
        if plugin['name'] is not None and plugin['version'] is not None:
            plugin_name = plugin['name']
            plugin_version = plugin['version']
            plg_command = ''.join([plg_command, f'wp plugin install {plugin_name} --version={plugin_version} --activate --allow-root\n'])

    for theme in conf_j[f'{i}']['theme']:
        if theme['name'] is not None and theme['version'] is not None:
            theme_name = theme['name']
            theme_version = theme['version']
            thm_command = ''.join([thm_command, f'wp theme install {theme_name} --version={theme_version} --activate --allow-root\n'])
    

    wp_service_name = 'wp' + str(i)
    db_service_name = 'db' + str(i)
    volume_name = './wp-content' + str(i) + '/'
    wpcli_service_name = 'wpcli' + str(i)

    lan_name = 'lan' + str(i)
    db_port = str(3305 + i)
    port = str(8000 + i)
    ip = sub_ip.split(".")
    subnet = str(ip[0])+'.'+str(ip[1])+'.'+str(int(ip[2]) + i)+'.'+str(ip[3])+'/24'

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
            'user':'33:33',
            'networks':[lan_name],
            'ports':[port + str(':80')],
            'working_dir':'/var/www/html',
            'volumes':[volume_name + str(':/var/www/html/wp-content')],
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
                    wp core install --url=localhost:{port} --title=\"${{BLOG_TITLE}}\" --admin_name=${{WORDPRESS_ADMIN}} --admin_password=${{WORDPRESS_ADMIN_PSW}} --admin_email=${{WORDPRESS_MAIL}}
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


    



