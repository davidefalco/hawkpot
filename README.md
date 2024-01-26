# hawknet
### A dynamic honeynet
##### Installation guide
1. Run `install.py` script, it will create `hawkpot.service` for you.
2. Populate `config.json` as you want. (There is a `config.json` sample file in this repo).
3. Run `hp_parser.py > compose.yml` to configure your honeynet. In addition to `compose.yml` it will create `default.conf` file (for the reverse proxy) inside `./proxy/conf/` directory and `rules.sh` file to set `iptables` rules (for intrusions detecting). Rules will be set automatically. Furthermore reverse proxy use SSL, so you have to provide SSL certificates. You have to copy them inside `./proxy/ssl/` and you should name them `nginx-selfsigned.crt` and `nginx-selfsigned.key`. If you are an expert, you can edit `default.conf` to change names for your keys. Do it before run your composition. You may have to create `ssl` folder inside `./proxy/`, put here your keys.
4. Run `systemctl start hawkpot.service`. It will start `log_manager.py` and `intrusion_detector.py`, they will write logs, respectively, inside `log_manager.log` and `intrusions.log` (follow this file with `tail` to gain information about intrusions).
5. Start your composition: `docker compose start`.

##### Notes
If you change your compose (manually or by `hp_parser.py`) you need to restart `hawkpot.service`.<br>
Some commands will require elevated privileges so it might be useful add some lines to `sudoers` file if you don't want to use `root` user:
- run `sudo visudo`
- add at the end of the file the follow lines: <br>
```
<your_user> ALL=(ALL) NOPASSWD: /usr/sbin/iptables
<your_user> ALL=(ALL) NOPASSWD: /usr/sbin/iptables-restore
<your_user> ALL=(ALL) NOPASSWD: /bin/systemctl restat docker
```


