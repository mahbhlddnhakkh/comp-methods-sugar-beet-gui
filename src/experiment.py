import math
import numpy as np
from src.algorithms import algs
from src.util import exp_res_props

def do_experiment(m: np.ndarray, exp_res: exp_res_props, exp_i: int) -> None:

    def do_experiment_iteration(exp_res: exp_res_props, exp_i: int, i: int, func, m: np.ndarray, *args) -> None:
        n = m.shape[0]
        tmp_res = func(m, *args)
        exp_res.last_res[i] = tmp_res
        row_ind = np.argsort(tmp_res[0])
        col_ind = np.arange(n, dtype=int)
        phases = [None] * n
        phases[0] = m[row_ind[0]][col_ind[0]] / exp_res.exp_count
        exp_res.phase_averages[i][0] += phases[0]
        for k in range(1, n):
           phases[k] = phases[k-1] + m[row_ind[k]][col_ind[k]] / exp_res.exp_count
           exp_res.phase_averages[i][k] += phases[k]

    for i in range(len(algs)):
        if (exp_res.chosen_algs[i]):
            algs_params = None
            if (i in exp_res.params_algs_specials):
                algs_params = exp_res.params_algs_specials[i]
            else:
                algs_params = tuple()
            do_experiment_iteration(exp_res, exp_i, i, algs[i]["func"], m, *algs_params)
