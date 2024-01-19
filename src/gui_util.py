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
#from threading import Thread

def dpg_add_input(dtype=str, **kwargs):
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
    dpg.add_text("")
    dpg.add_separator()

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
        dpg.add_checkbox(label="Параметры алгоритмов по умолчанию", parent=self._algs_group, user_data=dpg.last_item(), callback=self.checkbox_always_default_callback)
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

def generate_result_plot_table(exp_res, is_manual=False):
    '''
    Generates results and plot table
    '''

    def download_plot_matplotlib(exp_res):
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
        save_path = filedialog.asksaveasfilename(filetypes=[("Изображение", ".png")])
        if (save_path != "" and save_path != ()):
            plt.savefig(save_path)
    
    def save_as_csv(exp_res, is_manual, tb):
        '''
        Saves table as csv for whatever reason
        '''
        tb_ch = dpg.get_item_children(tb)
        save_path = filedialog.asksaveasfilename(filetypes=[("Таблица", ".csv")])
        if (save_path == "" or save_path == ()):
            return
        with open(save_path, 'w') as f:
            writer = csv.writer(f)
            first_row = []
            for e in tb_ch[0]:
                first_row.append(dpg.get_item_label(e))
            writer.writerow(first_row)
            writer.writerow(dpg.get_values(dpg.get_item_children(tb_ch[1][0])[1]))

    with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True, resizable=True, policy=dpg.mvTable_SizingStretchProp) as tb:
        if (not is_manual):
            dpg.add_table_column(label="Параметры")
            dpg.add_table_column(label="Кол-во экспериментов")
        for e in ["n", "Параметры алгоритмов"]:
            dpg.add_table_column(label=e)
        for i in range(len(algs)):
            dpg.add_table_column(label=algs[i]["name"] + " (S / Error)")
        with dpg.table_row():
            if (not is_manual):
                dpg.add_text("sample text")
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
    dpg.add_button(label="Сохранить таблицу (csv)", user_data=(exp_res, is_manual, tb), callback=lambda sender, app_data, user_data: save_as_csv(*user_data))
    dpg.add_text("")

    with dpg.plot(label=CFG.plot_title, width=-1, anti_aliased=True):
        dpg.add_plot_legend(outside=True, location=dpg.mvPlot_Location_East)
        x = dpg.add_plot_axis(dpg.mvXAxis, label=CFG.plot_x_label)
        y = dpg.add_plot_axis(dpg.mvYAxis, label=CFG.plot_y_label)
        x_arr = np.arange(1, exp_res.n+1)
        for i in range(len(algs)):
            if (exp_res.chosen_algs[i]):
                dpg.bind_item_theme(dpg.add_line_series(x_arr, exp_res.phase_averages[i], label=algs[i]["name"], parent=y), plot_theme_1)
    # TODO: in multithreading seems not to work and multiprocessing crashes gnome. Too bad!
    # Instead we can add "save plot" button
    #dpg.add_button(label="Посмотреть график в matplotlib", user_data=exp_res, callback=lambda sender, app_data, user_data: show_matplotlib_plot(user_data))
    dpg.add_button(label="Сохранить график", user_data=exp_res, callback=lambda sender, app_data, user_data: download_plot_matplotlib(user_data))
