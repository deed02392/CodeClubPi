## Description ##

CodeClubPi is a set of scripts and software that enables anyone to turn a Raspberry Pi into a complete web server solution for students practising HTML/CSS/JS in a class room environment.

It enables:

* Managing user/student accounts by creating locked down system accounts thus providing SFTP access
* Adjusting `nginx` configuration automatically so that every student gets their own vhost (e.g. [http://georgehafiz.code.club](http://georgehafiz.code.club))

## Usage ##

### Software Requirements ###

* python-dev
* python-pip
* python-tornado
* pip install lockfile
* pip install passlib
* sqlite3

### Environmental Requirements ###

* `/etc/nginx` needs special configuration (TBC)
* `/etc/ssh` needs special configuration (TBC)
* Install the provided init-script (`code-club`) with `insserv`


* Reboot or start with `/etc/init.d/code-club start`

Note that the server will run as `root`. This is unavoidable due to the need to manipulate user accounts, however great care has been put into ensuring the privileged scripts are very secure.


Thanks
------

The below contributed to the purchase of the hardware needed to support this project:

* Daniel J Woolridge
* Emma Longhurst-Gent
* Christopher Copper
* Adnan Shammout
* Cath Longhurst

Nginx and PHP-FPM
http://www.sebdangerfield.me.uk/2012/05/nginx-and-php-fpm-bash-script-for-creating-new-vhosts-under-separate-fpm-pools/
  for helpful reference on generating users and templates etc.. for new vhosts using bash