#!/bin/bash
# @author: George Hafiz <georgehafiz-at-gmail-dot-com>

USERNAME=$1
PASSWORD=$2

echo $USERNAME:$PASSWORD | chpasswd
if [ $? -ne 0 ]; then
    echo "Failed to change the user password"
    exit 1
fi

echo "Password changed for:" $USERNAME
exit 0
