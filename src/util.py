from src.config import CFG
from typing import Tuple, Dict, List
import numpy as np
from matplotlib import pyplot as plt
import os
import json

class exp_res_props:
    '''
    Represents props of advanced experiment
    '''
    n: int = 0
    exp_count: int = 0
    # index of chosen algs. Should be sorted, size must be <= len(algs), each element must be from 0 to len(algs)
    chosen_algs: List[int] = None
    # contain basic information. string: string
    params: dict = None
    # contain arguments for some algorithms. E.g. theta for lean greedy and greedy lean. alg_ind: [param1, param2, ...] . already checked
    params_algs_specials: List[list] = None
    # stores average S (for every experiment) for each algorithm on each phase ; alg_ind: [s_avg_phase_1, ..., s_avg_phase_n]
    phase_averages: List[List[float]] = None
    # stores results for each algorithm on the last experiment (useful in manual)
    last_res: List[tuple] = None

    def init(self, algs_len):
        self.params = {}
        self.phase_averages = [[0.0]*self.n for i in range(algs_len)]
        self.last_res = [None]*algs_len

    def dump_to_file(self, path: str) -> None:
        '''
        Dumps properties to json file
        '''
        with open(os.path.join(path, CFG.exp_res_data_file), "w") as f:
            json.dump(self.__dict__, f, indent=2, ensure_ascii=False)

    def get_from_file(self, path: str) -> None:
        '''
        Gets properties from json file
        '''
        with open(os.path.join(path, CFG.exp_res_data_file), "r") as f:
            self.__dict__ = json.load(f)
    
    def __str__(self):
        return json.dumps(dict(self.__dict__, **{"last_res": None}), ensure_ascii=False)


def do_rand(shape: tuple, v_min, v_max) -> np.ndarray:
    '''
    Return random ndarray with values from v_min to v_max
    shape is a size tuple. E.g. shape=(2, 3) is matrix with sizes (2, 3)
    '''
    return (np.random.rand(*shape) * (v_max - v_min) + v_min)

def convert_to_p_matrix(m: np.ndarray) -> None:
    '''
    Converts vector 'a' and matrix B, where 'a' in the first row of the matrix 'm' and the rest of the 'm' is B
    Elements of B must be between 0 and 1 (exceeding 1 is possible though)
    It modifies 'm'
    '''
    n: int = m.shape[0]
    for i in range(1, n):
        m[:, i] = m[:, i] * m[:, i-1]

def generate_matrix_main_ripening(n: int, a_i: Tuple[float, float], b_i_j_1: Tuple[float, float], b_i_j_2: Tuple[float, float]) -> np.ndarray:
    '''
    Generates matrix with ripening
    Uses parameters a_i, b_i_j_1, b_i_j_2 <- tuples with min and max values for each
    '''
    mu: int = int(math.floor(n / mu_div))
    m: np.ndarray = np.zeros((n, n), dtype=float)
    m[:, 0] = do_rand((n, ), *a_i)
    m[:, 1:mu+1] = do_rand((n, mu), *b_i_j_1)
    m[:, mu+1:n] = do_rand((n, n-1-mu), *b_i_j_2)
    return m

def generate_matrix_main(n: int, a_i: Tuple[float, float], b_i_j: Tuple[float, float]) -> np.ndarray:
    '''
    Generates matrix without ripening
    Uses parameters a_i, b_i_j <- tuples with min and max values for each
    '''
    m: np.ndarray = np.zeros((n, n), dtype=float)
    m[:, 0] = do_rand((n, ), *a_i)
    m[:, 1:n] = do_rand((n, n-1), *b_i_j)
    return m

def test_file_write(file_path: str) -> bool:
    '''
    Tests if able to write to file
    '''
    f = open(file_path, "a")
    res: bool = f.writable()
    f.close()
    return res

def test_read_file(file_path: str) -> bool:
    '''
    Tests if able to read file
    '''
    return os.access(file_path, os.R_OK)
