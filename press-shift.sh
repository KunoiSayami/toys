#!/usr/bin/env bash
sleep 5
while true; do
	sleep 0.05
	xdotool keydown shift
	sleep 0.05
	xdotool keyup shift
done
