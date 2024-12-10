#!/bin/bash

#will try to consantly write to disc as to avoid unplugging device and losing uncommitted data

while :
do
    sync
    sleep 0.3s
done
