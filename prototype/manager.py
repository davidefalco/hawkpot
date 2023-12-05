import json
import yaml

conf_template = {
    'version':'3',
    'services':{
            'proxy1':{
            'image':'nginx',
            'networks':['lan1'], 'ports':['8081:80'],
            }
        },
    'hostname':'serv1',
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

#echo "page3" >> /usr/share/nginx/html/index.html

# configuration file from user
with open("./config.json", "r") as conf:
    conf_j = json.loads(conf.read())

subnets = conf_j["subnets"]
# the first subnet and nginx system already exists

for i in range(2, subnets + 1):
    service_name = 'proxy' + str(i)
    lan_name = 'lan' + str(i)
    port = str(8080 + i)
    subnet = '10.0.'+str(i)+'.0/24'

    update_service = {
        service_name:{
            'image':'nginx',
            'hostname':f'serv{i}',
            'networks':[lan_name], 'ports':[port+str(':80')],
            }
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

with open('./compose.yml',"w") as compose:
    compose.write(out)


    



