#! /bin/bash

kubectl taint node cirno nvidia.com/gpu=true:NoSchedule
