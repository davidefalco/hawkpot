import json
import yaml

"""
conf_template = {
    'version':'3',
    'services':
        {'db1':
                {'image':'mysql:5.7',
                 'networks':['lan1'], 
                 'ports':['3306:3306'],
                 'restart':'always', 
                 'environment':{'MYSQL_ROOT_PASSWORD':'${MYSQL_ROOT_PASS}',
                                'MYSQL_DATABASE':'${MYSQL_DB_NAME}', 
                                'MYSQL_USER':'${MYSQL_USER}',
                                'MYSQL_PASSWORD':'${MYSQL_PASS}'
                                }                
                },
         'wp1':{
             'depends_on':['db1'],
             'image':'wordpress:${WORDPRESS_VERSION}',
             'networks':['lan1'],
             'ports':['8001:80'],
             'working_dir':'/var/www/html',
             'volumes':['./wp-content1/:/var/www/html/wp-content'],
             'restart':'always',
             'environment':{'WORDPRESS_DB_HOST':'db1:3306',
                            'WORDPRESS_DB_USER':'${WORDPRESS_DB_USER}',
                            'WORDPRESS_DB_PASSWORD':'${WORDPRESS_DB_PASS}',
                            'WORDPRESS_DB_NAME':'${MYSQL_DB_NAME}'                 
                            },
            },
         'wpcli1':{
                'depends_on':['db1', 'wp1'],
                'image':'wordpress:cli',
                'networks':['lan1'],
                'volumes_from':['wp1'],
                'environment':{'WORDPRESS_DB_HOST':'db1:3306',
                            'WORDPRESS_DB_USER':'${WORDPRESS_DB_USER}',
                            'WORDPRESS_DB_PASSWORD':'${WORDPRESS_DB_PASS}',
                            'WORDPRESS_DB_NAME':'${MYSQL_DB_NAME}'                 
                            },
                'command':''' 
                    /bin/sh -c '
                    sleep 30;
                    wp core install --url=localhost:8001 --title=\"${BLOG_TITLE}\" --admin_name=${WORDPRESS_ADMIN} --admin_password=${WORDPRESS_ADMIN_PSW} --admin_email=${WORDPRESS_MAIL}
                    '
                    '''
                }
        },
    'networks':
        {'lan1':
            {'ipam':
                {'driver':'default',
                 'config':
                    [{'subnet':'10.0.1.0/24'}]
                }
            }
        }
}
"""

#with open('./.template', 'r') as template:
#    template_yaml = yaml.safe_load(template)

#out = yaml.dump(template_yaml, sort_keys=False)
#with open('./compose.yml',"w") as compose:
#    compose.write(out)

# configuration file from user
with open("./config.json", "r") as conf:
    conf_j = json.loads(conf.read())

subnets = conf_j["subnets"]
# the first subnet and nginx system already exists

template_yaml = {
    'version':'3',
    'services':{},
    'networks':{}
}

for i in range(1, subnets + 1):
    plg_command = ''
    thm_command = ''

    if conf_j[f'{i}']['plugin']['name'] is not None and conf_j[f'{i}']['plugin']['version'] is not None:
        plugin_name = conf_j[f'{i}']['plugin']['name']
        plugin_version = conf_j[f'{i}']['plugin']['version']
        plg_command = f'wp plugin install {plugin_name} --version={plugin_version} --activate --allow-root'

    if conf_j[f'{i}']['theme']['name'] is not None and conf_j[f'{i}']['theme']['version'] is not None:
        theme_name = conf_j[f'{i}']['theme']['name']
        theme_version = conf_j[f'{i}']['theme']['version']
        thm_command = f'wp theme install {theme_name} --version={theme_version} --activate --allow-root'
    

    wp_service_name = 'wp' + str(i)
    db_service_name = 'db' + str(i)
    volume_name = './wp-content' + str(i) + '/'
    wpcli_service_name = 'wpcli' + str(i)

    lan_name = 'lan' + str(i)
    db_port = str(3305 + i)
    port = str(8000 + i)
    subnet = '10.0.'+str(i)+'.0/24'

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

with open('./compose_NEW.yml',"w") as compose:
    compose.write(out)


    



