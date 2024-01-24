import dearpygui.dearpygui as dpg
import os
from src.config import CFG
from src.themes import highlight_cell_theme, plot_theme_1
from src.util import generate_matrix_main, generate_matrix_main_ripening, convert_to_p_matrix
from src.algorithms import algs
from typing import Tuple, Dict, List
import numpy as np
from matplotlib import pyplot as plt
import matplotlib
matplotlib.use("agg")
from tkinter import filedialog
import csv

def dpg_add_input(dtype=str, **kwargs):
    '''
    dpg.add_input_*** but looks for type from argument
    float -> double because why not?
    '''
    if (dtype is int):
        return dpg.add_input_int(**kwargs)
    elif (dtype is float):
        return dpg.add_input_double(**kwargs)
    elif (dtype is str):
        return dpg.add_input_text(**kwargs)

def center_pos_popup(_popup):
    viewport_width = dpg.get_viewport_client_width()
    viewport_height = dpg.get_viewport_client_height()
    width = dpg.get_item_width(_popup)
    height = dpg.get_item_height(_popup)
    dpg.set_item_pos(_popup, [viewport_width // 2 - width // 2, viewport_height // 2 - height // 2])

def dpg_add_separator():
    '''
    This separator sometimes looks better than dpg.add_separator()
    '''
    dpg.add_text("")
    dpg.add_separator()

def dpg_get_values(items):
    '''
    Useful when unsure if argument is list or single value
    '''
    if (type(items) is list or type(items) is tuple):
        return dpg.get_values(items)
    else:
        return dpg.get_value(items)

class matrix_table:
    '''
    GUI table to fill matrix in manual tab
    '''
    _n: int = 0
    _table = None
    _columns = None
    # _rows == dpg.get_item_children(self._table)[1]
    _rows = None
    _readonly = None

    def __init__(self, readonly = True):
        self._n = 0
        self._table = dpg.add_table(header_row=False, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True)
        self._columns = []
        self._rows = []
        self._readonly = readonly

    def set_n(self, n) -> int:

        def create_float_input(parent):
            dpg.add_input_double(min_value=0.0, min_clamped=True, step=0, parent=parent, width=-1, readonly=self._readonly)

        if (not isinstance(n, int) or n <= 0):
            print(n, "is not correct value")
            return -1
        if (n > self._n):
            for i in range(n - self._n):
                self._columns.append(dpg.add_table_column(parent=self._table))
            for i in range(self._n):
                for j in range(n):
                    create_float_input(self._rows[i])
            for i in range(n - self._n):
                self._rows.append(dpg.add_table_row(parent=self._table))
                for j in range(n):
                    create_float_input(self._rows[-1])
        if (n < self._n):
            for i in range(self._n):
                rows_children = dpg.get_item_children(self._rows[i])[1]
                for j in range(n, self._n):
                    dpg.delete_item(rows_children[j])
            for i in range(n, self._n):
                dpg.delete_item(self._rows[i])
                dpg.delete_item(self._columns[i])
            self._rows = self._rows[:n]
            self._columns = self._columns[:n]
        self._n = n
        return 0

    def get_matrix(self) -> np.ndarray:
        '''
        Returns matrix with floats
        '''
        m: np.ndarray = np.zeros((self._n, self._n), dtype=float)
        for i in range(self._n):
            rows_children = dpg.get_item_children(self._rows[i])[1]
            for j in range(self._n):
                m[i, j] = dpg.get_value(rows_children[j])
        return m

    def set_matrix(self, m: np.ndarray) -> None:
        self.set_n(m.shape[1])
        for i in range(self._n):
            rows_children = dpg.get_item_children(self._rows[i])[1]
            for j in range(self._n):
                dpg.set_value(rows_children[j], m[i, j])

    def set_from_file(self, file_path: str) -> None:
        '''
        Fills matrix from txt file
        '''
        if (file_path == () or file_path == ""):
            return
        lines = None
        with open(file_path, "r") as f:
            lines = [e.strip() for e in f.readlines()]
        err = self.set_n(int(lines[0]))
        if (err == -1):
            return
        lines.pop(0)
        m = np.fromstring(string=' '.join(lines), dtype=float, count=self._n*self._n, sep=' ').reshape(self._n, self._n)
        self.set_matrix(m)

    def paint_cols(self, col_ind: np.array) -> None:
        '''
        Paints result
        '''
        for i in range(self._n):
            rows_children = dpg.get_item_children(self._rows[i])[1]
            dpg.bind_item_theme(rows_children[col_ind[i]], highlight_cell_theme)

    def reset_paint_cols(self) -> None:
        # TODO: work in progress
        pass

    def randomize(self, a_i, b_i_j) -> None:
        # TODO: work in progress
        pass

    def randomize_ripening(self, a_i, b_i_j_1, b_i_j_2) -> None:
        # TODO: work in progress
        pass

class select_algs:
    '''
    Creates buttons and interface for selecting algorithms and their parameters
    '''
    # https://github.com/hoffstadt/DearPyGui/issues/1513
    _algs_group = None
    _selected_algs = None
    _params = None
    _exp_res = None
    _params_launched_once = None
    _checkbox_default_value = None

    def __init__(self, exp_res=None):
        self._exp_res = exp_res
        self._selected_algs = [True]*len(algs)
        self.run_default_params()
        self._params_launched_once = False
        self._algs_group = dpg.add_group(horizontal=True)
        self._checkbox_default_value = False
        dpg.add_button(label="Выбрать алгоритмы", parent=self._algs_group, callback=self.create_select_algs_popup)
        dpg.add_button(label="Выбрать параметры алгоритмов", parent=self._algs_group, callback=self.create_select_params_popup)
        dpg.add_checkbox(label="Параметры алгоритмов по умолчанию", parent=self._algs_group, user_data=dpg.last_item(), callback=self.checkbox_always_default_callback, default_value=True)
        self.checkbox_always_default_callback(dpg.last_item(), dpg.get_value(dpg.last_item()), dpg.get_item_user_data(dpg.last_item()))
        with dpg.tooltip(dpg.last_item()):
            dpg.add_text("Некоторые параметры по умолчанию зависят от n. Используйте, чтобы n 'подтягивалось' за параметрами автоматически.")
            dpg.add_text("При включении блокируется выбор параметров алгоритмов")
        self.set_exp_res()

    def checkbox_always_default_callback(self, sender, app_data, user_data):
        if (app_data):
            self._checkbox_default_value = True
            dpg.configure_item(user_data, enabled=False)
        else:
            self._checkbox_default_value = False
            dpg.configure_item(user_data, enabled=True)

    def create_select_algs_popup(self):
        with dpg.window(label="Выбрать алгоритмы", modal=True, no_close=True) as popup:
            with dpg.group():
                for i in range(len(algs)):
                    dpg.add_checkbox(label=algs[i]["name"], default_value=self._selected_algs[i])
            with dpg.group(horizontal=True):
                dpg.add_button(label="ОК", user_data=(popup,), callback=lambda sender, app_data, user_data: self.on_ok_select_algs(user_data[0]))
                dpg.add_button(label="Отмена", user_data=(popup,), callback=lambda sender, app_data, user_data: self.on_close_popup(user_data[0]))
            center_pos_popup(popup)

    def create_select_params_popup(self):
        self._params_launched_once = True
        with dpg.window(label="Выбрать параметры алгоритмов", modal=True, no_close=True) as popup:
            self.generate_params_on_popup(popup)
    
    def generate_params_on_popup(self, popup, do_center=True):

        def default_all_btn_callback(self, _popup):
            self.run_default_params()
            dpg.delete_item(_popup, children_only=True)
            dpg.push_container_stack(_popup)
            self.generate_params_on_popup(_popup, False)
            dpg.pop_container_stack()
        done_once = False
        tmp_btn = dpg.add_button(label="Все по умолчанию", user_data=popup, callback=lambda sender, app_data, user_data: default_all_btn_callback(self, user_data))
        with dpg.group():
            for i in self._params:
                if (self._selected_algs[i]):
                    done_once = True
                    with dpg.group(user_data=i):
                        dpg.add_text(algs[i]["name"])
                        for j in range(len(algs[i]["params"])):
                            p = algs[i]["params"][j]
                            with dpg.group(horizontal=True, user_data=j):
                                dpg.add_text(p["name"])
                                dpg_add_input(p["type"], default_value=self._params[i][j], width=150)
                                dpg.add_button(label="По умолчанию", user_data=(dpg.last_item(), p["default"]), callback=lambda sender, app_data, user_data: dpg.set_value(user_data[0], user_data[1](self._exp_res)))
        if (not done_once):
            dpg.add_text("Параметры алгоритмов не найдены")
            dpg.configure_item(tmp_btn, show=False)
        with dpg.group(horizontal=True):
            if (done_once):
                dpg.add_button(label="ОК", user_data=(popup,), callback=lambda sender, app_data, user_data: self.on_ok_select_params(user_data[0]))
            dpg.add_button(label="Отмена", user_data=(popup,), callback=lambda sender, app_data, user_data: self.on_close_popup(user_data[0]))
        if (do_center):
            center_pos_popup(popup)

    def on_ok_select_algs(self, _popup):
        checkboxes = dpg.get_item_children(dpg.get_item_children(_popup)[1][0])[1]
        self._selected_algs = dpg.get_values(checkboxes)
        self.set_exp_res()
        self.on_close_popup(_popup)

    def on_ok_select_params(self, _popup):
        params_groups = dpg.get_item_children(dpg.get_item_children(_popup)[1][1])[1]
        for a in params_groups:
            i = dpg.get_item_user_data(a)
            param_group = dpg.get_item_children(a)[1][1:]
            for p in param_group:
                j = dpg.get_item_user_data(p)
                p_value = dpg.get_value(dpg.get_item_children(p)[1][1])
                self._params[i][j] = p_value
        self.set_exp_res()
        self.on_close_popup(_popup)

    def on_close_popup(self, _popup):
        dpg.delete_item(_popup)

    def set_exp_res(self):
        self._exp_res.chosen_algs = self._selected_algs
        self._exp_res.params_algs_specials = self._params

    def run_default_params(self):
        self._params = {}
        for i in range(len(algs)):
            if ("params" in algs[i]):
                self._params[i] = []
                for p in algs[i]["params"]:
                    self._params[i].append(p["default"](self._exp_res))
        self.set_exp_res()
    
    def run_default_if_params_popup_not_opened(self):
        if (not self._params_launched_once or self._checkbox_default_value):
            self.run_default_params()

def download_plot_matplotlib(exp_res, _save_path=None):
    '''
    Downloads plot
    https://matplotlib.org/stable/users/explain/figure/backends.html#static-backends
    '''
    plt.title(CFG.plot_title)
    plt.xlabel(CFG.plot_x_label)
    plt.ylabel(CFG.plot_y_label)
    x_arr = np.arange(1, exp_res.n+1)
    for i in range(len(algs)):
        if (exp_res.chosen_algs[i]):
            plt.plot(x_arr, exp_res.phase_averages[i], label=algs[i]["name"], marker='o')
    plt.legend()
    #plt.show()
    save_path = _save_path
    if (save_path == None):
        dpg.lock_mutex()
        save_path = filedialog.asksaveasfilename(filetypes=[("Изображение", ".png")], initialfile=exp_res.evaluate_exp_name(), initialdir=exp_res.working_directory)
        dpg.unlock_mutex()
    if (save_path != "" and save_path != ()):
        plt.savefig(save_path)

def save_table_as_csv(exp_res, tb, _save_path=None, _ignored_columns=None):
    '''
    Saves table as csv for whatever reason
    '''
    tb_ch = dpg.get_item_children(tb)
    ignored_columns = None
    if (_ignored_columns != None):
        ignored_columns = sorted(_ignored_columns, reverse=True)
    if (ignored_columns != None):
        for i in ignored_columns:
            del tb_ch[0][i]
    save_path = _save_path
    if (save_path == None):
        dpg.lock_mutex()
        save_path = filedialog.asksaveasfilename(filetypes=[("Таблица", ".csv")], initialfile=exp_res.evaluate_exp_name(), initialdir=exp_res.working_directory)
        dpg.unlock_mutex()
    if (save_path == "" or save_path == ()):
        return
    with open(save_path, 'w') as f:
        writer = csv.writer(f)
        first_row = []
        for e in tb_ch[0]:
            first_row.append(dpg.get_item_label(e))
        writer.writerow(first_row)
        for e in tb_ch[1]:
            r_ch = dpg.get_item_children(e)[1]
            if (ignored_columns != None):
                for i in ignored_columns:
                    del r_ch[i]
            writer.writerow(dpg.get_values(r_ch))
        #writer.writerow(dpg.get_values(dpg.get_item_children(tb_ch[1][0])[1]))

def generate_result_table_columns(tb, is_manual=False):
    '''
    Generates result table's columns
    '''
    if (not is_manual):
        for e in ("Название", "Параметры", "Кол-во экспериментов"):
            dpg.add_table_column(label=e, parent=tb)
    for e in ("n", "Параметры алгоритмов"):
        dpg.add_table_column(label=e, parent=tb)
    for i in range(len(algs)):
        dpg.add_table_column(label=algs[i]["name"] + " (S / Error)", parent=tb)

def generate_result_table_row(exp_res, tb, is_manual=False):
    '''
    Generates result table's row from exp_res
    '''
    with dpg.table_row(parent=tb, user_data=exp_res) as r:
        if (not is_manual):
            dpg.add_text(exp_res.evaluate_exp_name())
            tmp = ""
            for key in exp_res.params.keys():
                p = exp_res.params[key]
                tmp += key
                if (p == None):
                    tmp += "\n"
                    continue
                tmp += " = "
                if (type(p) is tuple or type(p) is list):
                    if (p[2] != 0):
                        tmp += "("
                    else:
                        tmp += "["
                    tmp += f'{p[0]}, {p[1]}'
                    if (p[3] != 0):
                        tmp += ")"
                    else:
                        tmp += "]"
                else:
                    tmp += str(p)
                tmp += "\n"
            tmp = tmp[:len(tmp)-1]
            dpg.add_text(tmp)
            dpg.add_text(str(exp_res.exp_count))
        dpg.add_text(str(exp_res.n))
        tmp = ""
        for e in exp_res.params_algs_specials:
            if (exp_res.chosen_algs[e]):
                tmp += algs[e]["name"] + ":\n"
                cur_params = algs[e]["params"]
                for ee in range(len(cur_params)):
                    tmp += cur_params[ee]["name"] + " = " + str(exp_res.params_algs_specials[e][ee]) + '\n'
        dpg.add_text(tmp)
        for i in range(len(algs)):
            if (exp_res.chosen_algs[i]):
                dpg.add_text(f'{exp_res.phase_averages[i][-1]}\n{exp_res.average_error[i]}')
            else:
                dpg.add_text("")
    return r

def generate_result_plot(exp_res, add_save_button=True, legend_outside=True):
    '''
    Generates result plot from exp_res
    '''
    with dpg.plot(label=CFG.plot_title + '\n' + exp_res.evaluate_exp_name(), width=-1, anti_aliased=True) as dpg_plot:
        if (legend_outside):
            dpg.add_plot_legend(outside=True, location=dpg.mvPlot_Location_East)
        else:
            dpg.add_plot_legend()
        x = dpg.add_plot_axis(dpg.mvXAxis, label=CFG.plot_x_label)
        y = dpg.add_plot_axis(dpg.mvYAxis, label=CFG.plot_y_label)
        x_arr = np.arange(1, exp_res.n+1, dtype=int)
        for i in range(len(algs)):
            if (exp_res.chosen_algs[i]):
                dpg.bind_item_theme(dpg.add_line_series(x_arr, exp_res.phase_averages[i], label=algs[i]["name"], parent=y), plot_theme_1)
    if (add_save_button):
        dpg.add_button(label="Сохранить график", user_data=(exp_res, None), callback=lambda sender, app_data, user_data: download_plot_matplotlib(*user_data))
    return dpg_plot

def generate_result_plot_table(exp_res, is_manual=False) -> tuple:
    '''
    Generates results and plot table
    '''
    with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True, resizable=True, policy=dpg.mvTable_SizingStretchProp) as tb:
        generate_result_table_columns(tb, is_manual)
        generate_result_table_row(exp_res, tb, is_manual)
    dpg.add_button(label="Сохранить таблицу (csv)", user_data=(exp_res, tb, None), callback=lambda sender, app_data, user_data: save_table_as_csv(*user_data))
    dpg.add_text("")
    dpg_plot = generate_result_plot(exp_res, True)
    return (tb, dpg_plot)

def generate_input_for_exp(param):
    '''
    Generates input for experiment params
    '''

    def generate_input_range(param) -> tuple:
        '''
        Generates input with special 'range'
        E.g. to type range for a_i
        Return tuple of 2 dpg inputs: min and max
        '''
        def manage_range(sender, app_data, user_data):
            param = user_data[2]
            if (user_data[0] and ("range_min" in param and param["range_min"]["type"] != "include" and app_data <= param["range_min"]["min"] or "range_max" in param and param["range_max"]["type"] != "include" and app_data >= param["range_max"]["max"])):
                # left
                dpg.set_value(user_data[1], "(")
            elif (user_data[0]):
                dpg.set_value(user_data[1], "[")
            if (not user_data[0] and ("range_max" in param and param["range_max"]["type"] != "include" and app_data >= param["range_max"]["max"] or "range_min" in param and param["range_min"]["type"] != "include" and app_data <= param["range_min"]["min"])):
                # right
                dpg.set_value(user_data[1], ")")
            elif (not user_data[0]):
                dpg.set_value(user_data[1], "]")

        res = [None, None]
        range_text = "Диапазон: "
        bracket_left = dpg.add_text("[")
        kwargs = ({}, {})
        if ("range_min" in param):
            kwargs[0]["default_value"] = param["range_min"]["min"]
            kwargs[1]["default_value"] = param["range_min"]["min"]
            kwargs[0]["min_value"] = param["range_min"]["min"]
            kwargs[0]["min_clamped"] = True
            kwargs[1]["min_value"] = param["range_min"]["min"]
            kwargs[1]["min_clamped"] = True
            if (param["range_min"]["type"] == "include"):
                range_text += "["
            else:
                range_text += "("
            range_text += f'{param["range_min"]["min"]}'
        else:
            range_text += "(inf"
        range_text += ", "
        if ("range_max" in param):
            kwargs[1]["default_value"] = param["range_max"]["max"]
            kwargs[1]["max_value"] = param["range_max"]["max"]
            kwargs[1]["max_clamped"] = True
            kwargs[0]["max_value"] = param["range_max"]["max"]
            kwargs[0]["max_clamped"] = True
            range_text += f'{param["range_max"]["max"]}'
            if (param["range_max"]["type"] == "include"):
                range_text += "]"
            else:
                range_text += ")"
        else:
            range_text += "inf)"
        res[0] = dpg_add_input(param["type"], user_data=(True, bracket_left, param), width=100, step=0, callback=manage_range, on_enter=True, **(kwargs[0]))
        dpg.add_text(",")
        bracket_right = dpg.add_text("]")
        res[1] = dpg_add_input(param["type"], user_data=(False, bracket_right, param), width=100, step=0, callback=manage_range, before=bracket_right, on_enter=True, **(kwargs[1]))
        dpg.add_text("")
        dpg.add_text(range_text)
        for e in res:
            manage_range(e, dpg.get_value(e), dpg.get_item_user_data(e))
        return res

    if ("special" in param and "special" == "empty"):
        return None
    res = None
    with dpg.group(horizontal=True):
        if (not "special" in param):
            kwargs = {}
            if ("max" in params):
                kwargs["max_value"] = params["max"]
                kwargs["max_clamped"] = True
                kwargs["default_value"] = params["max"]
            if ("min" in params):
                kwargs["min_value"] = params["min"]
                kwargs["min_clamped"] = True
                kwargs["default_value"] = params["min"]
            if ("default" in params):
                kwargs["default_value"] = params["default"]
            dpg.add_text(param["title"])
            with dpg.tooltip(dpg.last_item()):
                dpg.add_text(param["name"])
            res = dpg_add_input(param["type"], **kwargs)
        else:
            if (param["special"] == "range"):
                dpg.add_text(param["title"])
                with dpg.tooltip(dpg.last_item()):
                    dpg.add_text(param["name"])
                res = generate_input_range(param)
    if (res != None):
        param["dpg"] = res
    return res

def fix_range_min_max_input_exp(params: List[dict]):
    '''
    Fixes incorrect range parameters.
    When min > max, we just swap them. 
    '''
    for p in params:
        if (p.get("special") == "range" and "dpg" in p):
            vals = dpg.get_values(p["dpg"])
            if (vals[0] > vals[1]):
                dpg.set_value(p["dpg"][0], vals[1])
                dpg.set_value(p["dpg"][1], vals[0])
                for e in p["dpg"]:
                    dpg.get_item_configuration(e)["callback"](e, dpg.get_value(e), dpg.get_item_user_data(e))
