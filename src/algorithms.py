from src.util import do_rand
import scipy.optimize
import numpy as np
from typing import Tuple
import math

def hungarian(m: np.ndarray, maximize: bool = True) -> Tuple[np.array, float]:
    '''
    Hungarian algorithm (Венгерский алгоритм)
    return (row_ind, col_ind, sum)
    '''
    row_ind: np.array = None
    col_ind: np.array = None
    row_ind, col_ind = scipy.optimize.linear_sum_assignment(m, maximize)
    return (col_ind, m[row_ind, col_ind].sum())

def hungarian_max(m: np.ndarray) -> Tuple[np.array, float]:
    '''
    for algs
    Same as hungarian(m, True)
    '''
    return hungarian(m, True)

def hungarian_min(m: np.ndarray) -> Tuple[np.array, float]:
    '''
    for algs
    Same as hungarian(m, False)
    '''
    return hungarian(m, False)

def greedy_iteration(m: np.ndarray, reserved: np.array, col_ind: np.array, ind_offset: int = 0) -> np.array:
    '''
    Iteration for greedy algorithm
    Is important for lean-greedy and greedy-lean algorithms
    Writes result to col_ind
    reserved - shows, what delivery lot is done (bool array)
    ind_offset is used when we don't start from phase 1, but from phase ind_offset
    '''
    n: int = m.shape[1]
    sz: int = reserved.size
    for i in range(n):
        ind_sorted: np.array = np.flip(np.argsort(m[:, i]))
        j = 0
        while (j < sz and reserved[ind_sorted[j]]):
            j += 1
        col_ind[ind_sorted[j]] = i + ind_offset
        reserved[ind_sorted[j]] = True

def greedy(m: np.ndarray) -> Tuple[np.array, float]:
    '''
    Greedy algorithm (Жадный алгоритм)
    return (col_ind, sum)
    '''
    n: int = m.shape[0]
    reserved: np.array = np.zeros(n, dtype=bool)
    col_ind: np.array = np.zeros(n, dtype=int)
    greedy_iteration(m, reserved, col_ind)
    return (col_ind, m[np.arange(n, dtype=int), col_ind].sum())

def lean_iteration(m: np.ndarray, reserved: np.array, col_ind: np.array, ind_offset: int = 0) -> np.array:
    '''
    Iteration for lean algorithm
    Is important for lean-greedy and greedy-lean algorithms
    Writes result to col_ind
    reserved - shows, what delivery lot is done (bool array)
    ind_offset is used when we don't start from phase 1, but from phase ind_offset
    '''
    n: int = m.shape[1]
    sz: int = reserved.size
    for i in range(n):
        ind_sorted: np.array = np.argsort(m[:, i])
        j = 0
        while (j < sz and reserved[ind_sorted[j]]):
            j += 1
        col_ind[ind_sorted[j]] = i + ind_offset
        reserved[ind_sorted[j]] = True

def lean(m: np.ndarray) -> Tuple[np.array, float]:
    '''
    Lean algorithm (Бережливый алгоритм)
    return (col_ind, sum)
    '''
    n: int = m.shape[0]
    reserved: np.array = np.zeros(n, dtype=bool)
    col_ind: np.array = np.zeros(n, dtype=int)
    lean_iteration(m, reserved, col_ind)
    return (col_ind, m[np.arange(n, dtype=int), col_ind].sum())

def lean_greedy(m: np.ndarray, theta: int) -> Tuple[np.array, float]:
    '''
    Lean-greedy algorithm (Бережливо-жадный алгоритм)
    Lean for 1 to theta-1, greedy for theta to n
    return (col_ind, sum)
    '''
    n: int = m.shape[0]
    if (theta == 1):
        return lean(m)
    if (theta == n+1):
        return greedy(m)
    if (theta < 1 or theta > n+1):
        raise Exception("Theta must be from 1 to n+1")
    reserved: np.array = np.zeros(n, dtype=bool)
    col_ind: np.array = np.zeros(n, dtype=int)
    lean_iteration(m[:, 0:theta-1], reserved, col_ind)
    greedy_iteration(m[:, theta-1:n], reserved, col_ind, theta-1)
    return (col_ind, m[np.arange(n, dtype=int), col_ind].sum())

def greedy_lean(m: np.ndarray, theta: int) -> Tuple[np.array, float]:
    '''
    Greedy-lean algorithm (Жадно-бережливый алгоритм)
    Greedy for 1 to theta, lean for theta+1 to n
    return (col_ind, sum)
    '''
    n: int = m.shape[0]
    if (theta == 0):
        return greedy(m)
    if (theta == n):
        return lean(m)
    if (theta < 0 or theta > n):
        raise Exception("Theta must be from 0 to n")
    reserved: np.array = np.zeros(n, dtype=bool)
    col_ind: np.array = np.zeros(n, dtype=int)
    greedy_iteration(m[:, 0:theta], reserved, col_ind)
    lean_iteration(m[:, theta:n], reserved, col_ind, theta)
    return (col_ind, m[np.arange(n, dtype=int), col_ind].sum())
