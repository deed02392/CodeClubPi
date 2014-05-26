#!/bin/bash
# @author: George Hafiz <georgehafiz-at-gmail-dot-com>
# Created: 24/05/14

# Modify the following to match your system
NGINX_CONFIG='/etc/nginx/sites-available'
NGINX_SITES_ENABLED='/etc/nginx/sites-enabled'
NGINX_INIT='/etc/init.d/nginx'
# --------------END

if [ -z $1 ]; then
    echo "No name given"
    exit 1
fi
USERNAME=$1
DOMAIN=$USERNAME".code.club"

# Check the domain is valid
PATTERN="^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$";
if [[ "$DOMAIN" =~ $PATTERN ]]; then
    DOMAIN=`echo $DOMAIN | tr '[A-Z]' '[a-z]'`
    echo "Removing hosting for:" $DOMAIN
else
    echo "Invalid domain name"
    exit 1 
fi

# Remove the user account
rm -rf /home/$USERNAME
userdel $USERNAME

# Disable the domain in nginx
rm $NGINX_SITES_ENABLED/$DOMAIN.conf $NGINX_CONFIG/$DOMAIN.conf
$NGINX_INIT reload

echo "Site removed:" $DOMAIN
sleep 10
exit 0
