# bitbucket-repo-downloader
Clone/Update all  user repositories from bitbucket.

###Requirements
* python3.6+
* git
* ssh

###Installation
* Because the clone is done using ssh, you need to add your ssh key to bitbucket (https://bitbucket.org/account/settings/ssh-keys/)
* Clone this repo ```git clone https://github.com/ivaano/bitbucket-repo-downloader.git```
* Create a new virtual environment ```python3.7 -m venv venv```
* Activate virtual environment ```source venv/bin/activate```
* Go to project directory ```cd bitbucket-repo-downloader```
* Install dependencies ```pip install -r requirements.txt```
* Copy `config/config.sample` to `config/config.ini` and put your settings there.

###Usage
If you have set your settings in the config.ini file
just run the program ```python main.py```
Alternatively you can run the interactive mode by adding the `python main.py -i` argument
and it will ask for user/password workspace and destination dir.

