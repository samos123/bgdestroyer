#!/usr/bin/env bash

set -x

curl --header "X-Forwarded-For: 192.168.0.5" -F 'file=@demo.jpg' http://localhost:8080/remove
