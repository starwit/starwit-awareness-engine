#!/bin/bash

# This scripts purpose is to copy all the files in /weights into /weights_target

cp /weights/* /weights_target/ && echo -e "Successfully copied weights:\n$(ls /weights)"