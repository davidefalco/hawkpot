import os

dir = os.getcwd()

service = f'''[Unit]
Description=Hawkpot service
After=multi-user.target

[Service]
Type=simple
Restart=no
User=root
ExecStart=/usr/bin/python3 {dir}/hp_manager.py
WorkingDirectory={dir}
StandardOutput=null

[Install]
WantedBy=multi-user.target
'''

with open('/etc/systemd/system/hawkpot.service', 'w') as service_file:
    service_file.write(service)
