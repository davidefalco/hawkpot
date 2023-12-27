# hawkpot<br>
## A dynamic honeypot

#### Installation guide
1. `manager.py` creates the content for `default.conf` file.<br>
2. If `default.conf` file does not exist, it is created and populated by the manager. (If you edit `default.conf` file and you want to reset it, just delete it from `/proxy/conf/`). (**Note**: the manager creates automatically `/proxy/conf/`.)<br>
3. The manager prints on stdout the configuration file (you can use `python3 manager.py > compose.yml` for redirecting on a compose file).<br>
4. The reverse proxy use SSL, you must provide SSL certificates. You have to copy them inside `/proxy/ssl/` and you should name them `nginx-selfsigned.crt` and `nginx-selfsigned.key`. If you are an expert, you can edit `default.conf` for changing names for your key pair. (**Warn**: put SSL certificates in the right place before compose your deployment, so inside _proxy_ folder create _ssl_ folder and copy there your keys.)<br>
5. Now you can compose your deployment.<br>

#### `config.json` file
`config.json` file can be used for customizing your Wordpress installations and subnetting.<br>
Check the example in this repo.

#### `.env` file
`config.json` file can be used for customizing authentication information about the database and Wordpress.<br>
Check the example in this repo.