# Subsurface Modeling Kits
import random
import numpy as np
import matplotlib.pyplot as plt
from ipywidgets import IntSlider, interact, Layout

def tmake(init_thick, last_depth, nlayer, scale):
    if scale == 'log':
        depth = np.logspace(np.log10(init_thick), np.log10(last_depth), nlayer-1)
        depth = np.append([0], depth)
        thicks = []
        for i in range(nlayer-1):
            thicks.append(depth[i+1]-depth[i])
    elif scale == 'linear':
        depth = np.linspace(init_thick, last_depth, nlayer-1)
        depth = np.append([0], depth)
        thicks = []
        for i in range(nlayer-1):
            thicks.append(depth[i+1]-depth[i])
    return thicks

def dmake(thicks):
    depth = np.hstack([[0], np.cumsum(thicks)])
    return depth

def show_structure(thickness, depth):
    print('Layer Boundary Depth (m)')
    for i in range(len(depth)):
        if (i+1) % 10 == 0:
            eol = ' | \n'
        else:
            eol = ' | '
        char = "{:7,.3f}".format(depth[i])
        print(char ,end=eol)
    print('Layer Thickness (m)')
    for i in range(len(thickness)):
        if (i+1) % 10 == 0:
            eol = ' | \n'
        else:
            eol = ' | '
        char = "{:7,.3f}".format(thickness[i])
        print(char ,end=eol)
    print('infinity|')

def resistivity1D(thicks, brlim, generate_mode):
    """
    thicks : list, array-like
        list of thickness in each layer
    brlim : list [min, max]
        limits of resistivity range (Ohm-m)
    """
    if generate_mode == "normal":
        size = len(thicks) + 1
        lower = np.log10(brlim[0])
        upper = np.log10(brlim[1])
        baseres = [np.random.rand() * (upper - lower) + lower] * size
        baseres = np.array(baseres)
        altres = np.array([])

        m = int(size//12) + 1
        k = np.exp(3/5*np.exp(-1/size))

        sigma = np.sqrt(2/3*np.log(k))
        mu = np.log(m*k**(2/3))
        n = int(size//50) + 1

        smooth_iter = np.random.choice([1, 1, 2]) * int(n ** 1.5)
        abnormal_std = [0.8, 1.0, 1.2]
        natural_std = [0.1]
        while True:
            count = len(altres)
            empty = size - count
            if empty <= size*.05:
                fill = empty
            else:
                fill = int(np.random.lognormal(mu, sigma))
            if fill == 0:
                continue
            if fill <= empty:
                abnormal = np.random.choice([False, True], p=[0.8, 0.2])
                if abnormal:
                    normal_std = np.random.choice(abnormal_std)
                else:
                    normal_std = np.random.choice(natural_std)
                exp_add = np.ones(fill) * (np.random.normal(0, normal_std))
                altres = np.append(altres, exp_add)
                empty -= fill
            else:
                continue
            if empty == 0:
                break
        exponent = baseres + altres
        for i in range(smooth_iter):
            exponent = movearg(exponent)
        res = 10 ** exponent
        return res

    elif generate_mode == 'ymtmt':
        layer_num = len(thicks) + 1
        # 実質、何層構造か決める
        def random_resistivity_logscale(num):
            """
            対数間隔でランダムに乱数を生成する
            :return:
            """
            res_index = np.log10(brlim[1] / brlim[0]) * np.random.rand(num) + np.log10(brlim[0])
            res = 10 ** res_index
            return list(res)
        
        def random_int_nolap(divider_num, layer_num):
            """
            ダブりなしのint型乱数を生成する
            :param num:
            :return:
            """
            random_list = []
            list_num = 0
            while list_num < divider_num:
                random = np.random.randint(1, layer_num+1)
                if random not in random_list:
                    random_list.append(random)
                list_num = len(random_list)
            random_list.sort()
            return random_list
        
        thickness_num = np.random.randint(1, 4)
        if thickness_num == 1:
            res = random_resistivity_logscale(1) * layer_num
        elif thickness_num == 2:
            divider = np.random.randint(1, layer_num, 1)
            res = random_resistivity_logscale(1) * divider[0] + random_resistivity_logscale(1) * (layer_num - divider[0])
        elif thickness_num == 3:
            divider = random_int_nolap(thickness_num, layer_num)
            res = random_resistivity_logscale(1) * divider[0]\
                + random_resistivity_logscale(1) * (divider[1] - divider[0])\
                + random_resistivity_logscale(1) * (layer_num - divider[1])
        else:
            print('layer num error!')
            res = None
        return res

    elif generate_mode == 'default':
        # ©︎　20211108 tnishino
        layer_num = len(thicks) + 1
        L = np.arange(layer_num)
        res = np.zeros(L.shape)

        resmin = np.log10(brlim[0])
        resmax = np.log10(brlim[1])

        cut = np.random.randint(1,7)
        brval = (resmax-resmin)*np.random.rand(cut+1) + resmin

        Lnum = [i+1 for i in range(len(res))]
        bound = np.random.choice(Lnum, cut)
        bound.sort()

        bi = 0
        for i in range(layer_num):
            res[i] = brval[bi]
            if i in bound:
                bi += 1

        res0 = res.copy()
        for i in range(layer_num):
            res = movearg(res)

        smooth = np.random.rand()
        resexp = smooth*res+(1-smooth)*res0
        res_arr = 10 ** resexp
        return res_arr

    
def movearg(x):
    span = 3
    length = len(x)
    y = x.copy()
    edge = span // 2

    y[0] = (y[0]*3 + y[1]*2 + y[2]) / 6
    y[-1] = (y[-1]*3 + y[-2]*2 + y[-3]) /6
    if span - length >= 1:
        pass
    elif span % 2 == 0:
        for i in range(edge, length-edge):
            y[i] = (sum(x[i-edge:i+edge])/span + sum(x[i-edge+1:i+edge+1])/span)/2
    else:
        for i in range(edge, length-edge):
            y[i] = sum(x[i-edge:i+edge+1])/span
    return y
