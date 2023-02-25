#!/bin/bash

if [ -n "$1" ]; then
    sudo journalctl -u loraben.service --no-pager --follow
else
    sudo tail -F /var/log/syslog | grep loraben
fi
