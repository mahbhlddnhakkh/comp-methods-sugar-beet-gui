from src.config import CFG, mu_div
from typing import Tuple, Dict, List
import numpy as np
import os.path
import json
import math
import sys

class exp_res_props:
    '''
    Represents props of advanced experiment
    '''
    n: int = 0
    exp_count: int = 0
    exp_name: str = None
    exp_name_i: int = 0
    exp_mode: int = None
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
    # stores average differences for each algorithm
    average_error: List[float] = None
    # stores path to dir which contains json
    path: str = None
    # stores current working directory
    working_directory: str = None

    def init(self, algs_len):
        '''
        Call before doing experiment
        '''
        #self.params = {}
        self.phase_averages = [[0.0]*self.n for i in range(algs_len)]
        self.last_res = [None]*algs_len

    def calculate_average_error(self, algs_len):
        '''
        Call after doing experiment
        '''
        self.average_error = [None]*algs_len
        for i in range(algs_len):
            self.average_error[i] = (self.phase_averages[0][-1] - self.phase_averages[i][-1]) / self.phase_averages[0][-1]

    def dump_to_file(self, path: str) -> None:
        '''
        Dumps properties to json file
        '''
        if (path == "" or path == ()):
            return
        # since we are dumping this, we probably don't need last result anymore (we shouldn't dump in manual tab)
        self.last_res = None
        self.path = None
        self.working_directory = None
        with open(path, "w") as f:
            json.dump(self.__dict__, f, indent=2, ensure_ascii=False)
        self.path = path
        self.working_directory = os.path.dirname(path)

    def get_from_file(self, path: str) -> None:
        '''
        Gets properties from json file
        '''
        if (path == "" or path == ()):
            return
        with open(path, "r") as f:
            self.__dict__ = json.load(f)
        self.path = os.path.abspath(path)
        self.working_directory = os.path.dirname(self.path)
        self.fix_algs_params_keys()

    def copy(self, exp_res) -> None:
        self.__dict__ = json.loads(json.dumps(dict(exp_res.__dict__, **{"last_res": None}), ensure_ascii=False))
        self.fix_algs_params_keys()
        return self

    def fix_algs_params_keys(self) -> None:
        before_keys = tuple(self.params_algs_specials.keys())
        for key in before_keys:
            # for whatever reason json doesn't allow int to be keys for dict so they are strings now
            if (type(key) is str):
                self.params_algs_specials[int(key)] = self.params_algs_specials.pop(key)

    def spawn_copy(self):
        exp_res = exp_res_props()
        return exp_res.copy(self)

    def evaluate_exp_name(self) -> str:
        '''
        Replaces ${i} with corresponding value
        '''
        return self.exp_name.replace("${i}", str(self.exp_name_i), 1)

    def evaluate_regex_name(self) -> str:
        '''
        Gets regex name to test for finding correct i
        '''
        return self.exp_name.replace("${i}", r"\d+", 1)

    def get_exp_filename_without_evaluation(self) -> str:
        '''
        Gets filename but with ${i} placeholder
        '''
        return self.exp_name + ".json"

    def evaluate_exp_filename(self) -> str:
        '''
        Return json filename
        '''
        return self.evaluate_exp_name() + ".json"

    def evaluate_exp_filename_regex(self) -> str:
        '''
        Same as evaluate_exp_filename, but regex
        '''
        return self.evaluate_regex_name() + ".json"

    def __str__(self):
        #return json.dumps(dict(self.__dict__, **{"last_res": None}), ensure_ascii=False)
        return str(self.__dict__)


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

def convert_special_range_to_range(x: tuple) -> tuple:
    '''
    Converts (v_min, v_max, v_min_epsilon, v_max_epsilon) to (v_min_calc, v_max_calc)
    '''
    return (x[0] + x[2], x[1] - x[3])

def generate_matrix_main_ripening(n: int, a_i: Tuple[float, float], b_ij_1: Tuple[float, float], b_ij_2: Tuple[float, float], **kwargs) -> np.ndarray:
    '''
    Generates matrix with ripening
    Uses parameters a_i, b_i_j_1, b_i_j_2 <- tuples with min and max values for each
    '''
    mu: int = int(math.floor(n / mu_div))
    m: np.ndarray = np.zeros((n, n), dtype=float)
    m[:, 0] = do_rand((n, ), *convert_special_range_to_range(a_i))
    m[:, 1:mu+1] = do_rand((n, mu), *convert_special_range_to_range(b_ij_1))
    m[:, mu+1:n] = do_rand((n, n-1-mu), *convert_special_range_to_range(b_ij_2))
    return m

def generate_matrix_main(n: int, a_i: Tuple[float, float], b_ij: Tuple[float, float], **kwargs) -> np.ndarray:
    '''
    Generates matrix without ripening
    Uses parameters a_i, b_i_j <- tuples with min and max values for each
    '''
    m: np.ndarray = np.zeros((n, n), dtype=float)
    m[:, 0] = do_rand((n, ), *convert_special_range_to_range(a_i))
    m[:, 1:n] = do_rand((n, n-1), *convert_special_range_to_range(b_ij))
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
