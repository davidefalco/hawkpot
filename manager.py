import json
import yaml

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

out = yaml.dump(conf_template, sort_keys=False)
with open('./compose.yml',"w") as compose:
    compose.write(out)

# configuration file from user
#with open("./config.json", "r") as conf:
#    conf_j = json.loads(conf.read())

#subnets = conf_j["subnets"]
# the first subnet and nginx system already exists
"""
for i in range(2, subnets + 1):
    service_name = 'proxy' + str(i)
    lan_name = 'lan' + str(i)
    port = str(8080 + i)
    subnet = '10.0.'+str(i)+'.0/24'

    update_service = {
        service_name:{'image':'nginx',
                      'networks':[lan_name], 'ports':[port+str(':80')]}
    }
    
    conf_template['services'].update(update_service)

    update_net = {
        lan_name:
            {'ipam':
                {'driver':'default',
                    'config':
                        [{'subnet':subnet}]
                }
            }
    }

    conf_template['networks'].update(update_net)

out = yaml.dump(conf_template, sort_keys=False)

with open('./compose_NEW.yml',"w") as compose:
    compose.write(out)
"""

    



