import pysal as ps
import numpy as np
import dgp
import pandas as pd

data = dgp.scenario(2,10)

ycols = [x for x in data.columns if x.startswith('Y')]
dcols = [x for x in data.columns if not x.startswith('Y')]
yclean = []

for y in ycols:
    col,r,l = y.split('_')
    if len(r) > 4:
        r = '0.0'
    if len(l) > 4:
        l = '0.0'
    yclean.append('_'.join([col,r,l]))

data.columns = yclean + dcols
