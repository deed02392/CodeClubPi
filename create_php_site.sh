#!/bin/bash
# @author: Seb Dangerfield <http://www.sebdangerfield.me.uk/?p=513>
# @author: George Hafiz <georgehafiz-at-gmail-dot-com>
# Created:   11/08/2011

# Modify the following to match your system
NGINX_CONFIG='/etc/nginx/sites-available'
NGINX_SITES_ENABLED='/etc/nginx/sites-enabled'
WEB_SERVER_GROUP='www-data'
NGINX_INIT='/etc/init.d/nginx'
# --------------END

SED=`which sed`
CURRENT_DIR=`dirname $0`

if [ -z $1 ]; then
    echo "No domain name given"
    exit 1
fi
DOMAIN=$1

# check the domain is valid!
PATTERN="^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$";
if [[ "$DOMAIN" =~ $PATTERN ]]; then
    DOMAIN=`echo $DOMAIN | tr '[A-Z]' '[a-z]'`
    echo "Creating hosting for:" $DOMAIN
else
    echo "invalid domain name"
    exit 1 
fi

# Create a new user!
echo "Please specify the username for this site?"
read USERNAME
HOME_DIR=$USERNAME

mkdir --mode=755 /home/$USERNAME
useradd -d /home/$USERNAME -M -N -g sftp-only -G $WEB_SERVER_GROUP -s /usr/sbin/nologin $USERNAME
chown root:root /home/$USERNAME

PUBLIC_HTML_DIR='/public_html'

# Now we need to copy the virtual host template
CONFIG=$NGINX_CONFIG/$DOMAIN.conf
cp $CURRENT_DIR/nginx.vhost.conf.template $CONFIG
$SED -i "s/@@HOSTNAME@@/$DOMAIN/g" $CONFIG
$SED -i "s#@@PATH@@#\/home\/"$USERNAME$PUBLIC_HTML_DIR"#g" $CONFIG
$SED -i "s/@@LOG_PATH@@/\/home\/$USERNAME\/_logs/g" $CONFIG
chmod 644 $CONFIG

# Set file perms and create required directories
mkdir --mode=750 /home/$HOME_DIR$PUBLIC_HTML_DIR
mkdir --mode=770 /home/$HOME_DIR/_logs

# Enable the domain in nginx
ln -s $CONFIG $NGINX_SITES_ENABLED/$DOMAIN.conf
$NGINX_INIT reload

echo "Site created for:" $DOMAIN
