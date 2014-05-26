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
NGINX_VHOST_TEMPLATE=$CURRENT_DIR/nginx.vhost.conf.template
DEFAULT_INDEX=$CURRENT_DIR/index.htm.template
PUBLIC_HTML_DIR='/public_html'
RESTRICTED_GROUP='sftp-only'

FULLNAME=$1
USERNAME=$2
PASSWORD=$3
DOMAIN=$4".code.club"


# Check the domain is valid
PATTERN="^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$";
if [[ "$DOMAIN" =~ $PATTERN ]]; then
    DOMAIN=`echo $DOMAIN | tr '[A-Z]' '[a-z]'`
    echo "Creating hosting for:" $DOMAIN
else
    echo "Invalid domain name"
    exit 1 
fi

# Create a new user
HOME_DIR=/home/$USERNAME

mkdir --mode=755 $HOME_DIR
groupadd -f $RESTRICTED_GROUP
useradd -d $HOME_DIR -M -N -g $RESTRICTED_GROUP -G $WEB_SERVER_GROUP -s /usr/sbin/nologin -c "Code Club student" $USERNAME
if [ $? -ne 0 ]; then
    exit 1
fi
echo $USERNAME:$PASSWORD | chpasswd
chown root:root $HOME_DIR

# Copy the virtual host template
CONFIG=$NGINX_CONFIG/$DOMAIN.conf
cp $NGINX_VHOST_TEMPLATE $CONFIG
$SED -i "s/@@HOSTNAME@@/$DOMAIN/g" $CONFIG
$SED -i "s#@@PATH@@#"$HOME_DIR$PUBLIC_HTML_DIR"#g" $CONFIG
$SED -i "s#@@LOG_PATH@@#"$HOME_DIR\/_logs"#g" $CONFIG
chmod 644 $CONFIG

# Set file perms and create required directories
mkdir --mode=750 $HOME_DIR$PUBLIC_HTML_DIR
mkdir --mode=770 $HOME_DIR/_logs

INDEX=$HOME_DIR$PUBLIC_HTML_DIR/index.htm
cp $DEFAULT_INDEX $INDEX
$SED -i "s#@@USERNAME@@#"$USERNAME"#g" $INDEX

chown -R $USERNAME:$WEB_SERVER_GROUP $HOME_DIR/*

# Enable the domain in nginx
ln -s $CONFIG $NGINX_SITES_ENABLED/$DOMAIN.conf
$NGINX_INIT reload

echo "Site created for:" $DOMAIN
sleep 10
exit 0
