import dearpygui.dearpygui as dpg
from src.gui_util import matrix_table, select_algs, convert_to_p_matrix, generate_result_plot_table, generate_input_for_exp, fix_range_min_max_input_exp, download_plot_matplotlib, save_table_as_csv
from src.config import CFG, mu_div
from src.util import exp_res_props, generate_matrix_main, generate_matrix_main_ripening, convert_to_p_matrix
from src.experiment import do_experiment
from src.algorithms import algs
from tkinter import filedialog
import sys
import os
import re

big_result_table = None
exp_res_big_result_table = None

exp_inputs = {}

exp_modes = {
    "Без дозаривания": [
        {
            "title": "",
            "name": "Без дозаривания",
            "special": "empty",
        },
        {
            "title": "a_i",
            "name": "a_i",
            "type": float,
            "special": "range",
            "range_min": {
                "type": "exclude", # can be include
                "min": 0
            },
            "range_max": {
                "type": "exclude",
                "max": 1
            }
        },
        {
            "title": "b_ij",
            "name": "b_ij",
            "type": float,
            "special": "range",
            "range_min": {
                "type": "exclude",
                "min": 0
            },
            "range_max": {
                "type": "exclude",
                "max": 1
            }
        },
    ],
    "С дозариванием": [
        {
            "title": "",
            "name": "С дозариванием",
            "special": "empty",
        },
        {
            "title": "a_i",
            "name": "a_i",
            "type": float,
            "special": "range",
            "range_min": {
                "type": "exclude",
                "min": 0
            },
            "range_max": {
                "type": "exclude",
                "max": 1
            }
        },
        {
            "title": "b_ij во время дозаривания",
            "name": "b_ij_1",
            "type": float,
            "special": "range",
            "range_min": {
                "type": "exclude",
                "min": 1
            },
        },
        {
            "title": "b_ij после дозаривания",
            "name": "b_ij_2",
            "type": float,
            "special": "range",
            "range_min": {
                "type": "exclude",
                "min": 0
            },
            "range_max": {
                "type": "exclude",
                "max": 1
            }
        },
    ],
}

exp_modes_keys = tuple(exp_modes.keys())

last_exp_mode = 0

working_directory = os.getcwd()

def tab_manual() -> None:
    '''
    Вкладка "Вручную"
    '''

    def choose_from_file_btn_callback(sender, app_data):
        '''
        Get matrix from file
        '''
        dpg.lock_mutex()
        file_path = filedialog.askopenfilename()
        dpg.unlock_mutex()
        if (path == "" or path == ()):
            return
        m_table.set_from_file(file_path)
        dpg.set_value(n_input, m_table._n)
        exp_res.n = m_table._n

    def set_n(sender, app_data):
        '''
        As name implies, sets n
        '''
        exp_res.n = app_data
        m_table.set_n(app_data)

    def calc_btn_callback():
        '''
        Let's calculate everything
        '''
        dpg.delete_item(res_group, children_only=True)
        m_algs.run_default_if_params_popup_not_opened()
        m = m_table.get_matrix()
        if (not dpg.get_value(m_is_p)):
            convert_to_p_matrix(m)
        exp_res.init(len(algs))
        do_experiment(m, exp_res, 0)
        exp_res.calculate_average_error(len(algs))
        dpg.push_container_stack(res_group)
        generate_result_plot_table(exp_res, True)
        dpg.add_text("")
        for i in range(len(algs)):
            if (exp_res.chosen_algs[i]):
                dpg.add_separator()
                dpg.add_text(f'{algs[i]["name"]}')
                dpg.add_text(f'S = {exp_res.last_res[i][1]}')
                dpg.add_text(f'Погрешность = {exp_res.average_error[i]}')
                dpg.add_text(f'Выбор: {exp_res.last_res[i][0]+1}')
                if ("params" in algs[i]):
                    for j in range(len(algs[i]["params"])):
                        dpg.add_text(f'{algs[i]["params"][j]["name"]} = {exp_res.params_algs_specials[i][j]}')
                res_table = matrix_table(True)
                res_table.set_matrix(m)
                res_table.paint_cols(exp_res.last_res[i][0])
        dpg.pop_container_stack()

    exp_res = exp_res_props()
    exp_res.exp_count = 1
    m_is_p = dpg.add_checkbox(label="Преобразованная матрица P", default_value=True)
    dpg.add_separator()
    dpg.add_button(label="Выбрать из файла", callback=choose_from_file_btn_callback)
    dpg.add_separator()
    # TODO: add randomize button
    # in randomize popup user_data in callback will be really useful: https://dearpygui.readthedocs.io/en/latest/documentation/item-callbacks.html#user-data
    # TODO: save matrix as txt file button
    with dpg.group(horizontal=True):
        dpg.add_text("Введите n")
        n_input = dpg.add_input_int(min_value=mu_div, max_value=20, default_value=CFG.manual_matrix_default_n, min_clamped=True, max_clamped=True, callback=set_n)
    m_table = matrix_table(False)
    set_n(None, dpg.get_value(n_input))
    m_algs = select_algs(exp_res)
    dpg.add_button(label="Вычислить", callback=calc_btn_callback)
    # Cool padding
    dpg.add_text("")
    res_group = dpg.add_group()

def tab_experiment() -> None:
    '''
    Вкладка "Эксперименты"
    '''

    def fill_exp_res_name():
        '''
        Fills only exp_res's name and name_i
        '''
        exp_res.exp_name_i = dpg.get_value(exp_name_i_input)
        exp_res.exp_name = dpg.get_value(exp_name_input)

    def fill_exp_res():
        '''
        As name implies, fill out exp_res_props from inputs
        '''
        cur_exp_mode = exp_modes_keys[last_exp_mode]
        fix_range_min_max_input_exp(exp_modes[cur_exp_mode])
        fill_exp_res_name()
        exp_res.n = dpg.get_value(n_input)
        exp_res.exp_count = dpg.get_value(exp_count_input)
        exp_res.exp_mode = last_exp_mode
        exp_res.params = {}
        for p in exp_modes[cur_exp_mode]:
            if ("special" in p):
                if (p["special"] == "empty"):
                    exp_res.params[p["name"]] = None
                elif (p["special"] == "range"):
                    tmp = [None]*4
                    tmp[:2] = dpg.get_values(p["dpg"])
                    brackets = "()"
                    for i in range(2):
                        tmp[2+i] = 0
                        if (dpg.get_value(dpg.get_item_user_data(p["dpg"][i])[1]) == brackets[i]):
                            tmp[2+i] = sys.float_info.epsilon
                    if (tmp[0] == tmp[1] and tmp[2] != 0):
                        if ("range_min" in p and tmp[0] <= p["range_min"]["min"]):
                            tmp[3] = -tmp[3]
                        if ("range_max" in p and tmp[1] >= p["range_max"]["max"]):
                            tmp[2] = -tmp[2]
                    exp_res.params[p["name"]] = tuple(tmp)
            else:
                exp_res.params[p["name"]] = dpg.get_value(p["dpg"])
        m_algs.run_default_if_params_popup_not_opened()

    def choose_from_file_btn_callback():
        '''
        Button "Выбрать из файла"
        '''
        dpg.lock_mutex()
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("Любые", "*.*")])
        dpg.unlock_mutex()
        if (path == "" or path == ()):
            return
        exp_res.get_from_file(path)
        fill_experiment_tab(exp_res)

    def save_btn_callback():
        '''
        Button "Сохранить"
        '''
        fill_exp_res_name()
        path = exp_res.evaluate_exp_filename()
        # TODO: ask if okay to replace if exists?
        fill_exp_res()
        exp_res.dump_to_file(path)

    def set_n(sender, app_data):
        '''
        As name implies, sets exp_res n
        '''
        exp_res.n = app_data

    def restore_exp_name_i_callback():
        '''
        Calculate correct ${i}
        '''
        # TODO: pay attention to experiment analysis? can't do for now tho
        fill_exp_res_name()
        if (not "${i}" in exp_res.exp_name):
            reset_exp_name_i_callback()
        r = re.compile(exp_res.evaluate_exp_filename_regex())
        exp_name_parts = exp_res.get_exp_filename_without_evaluation().split("${i}", 1)
        cur_exp_files = [int(f.replace(exp_name_parts[0], "", 1).replace(exp_name_parts[1], "", 1)) for f in os.listdir(working_directory) if os.path.isfile(os.path.join(working_directory, f)) and r.match(f)]
        cur_exp_files.sort()
        i = 1
        while (i <= len(cur_exp_files) and cur_exp_files[i-1] == i):
            i += 1
        dpg.set_value(exp_name_i_input, i)
        check_json_exp_exist_callback()
    
    def reset_exp_name_i_callback():
        '''
        Resets ${i} (sets to 1)
        '''
        dpg.set_value(exp_name_i_input, 1)
        check_json_exp_exist_callback()

    def check_json_exp_exist_callback():
        '''
        If json experiment exists and puts a sign
        '''
        fill_exp_res_name()
        filename = exp_res.evaluate_exp_filename()
        path = os.path.join(working_directory, filename)
        if os.path.isfile(path):
            dpg.configure_item(exp_json_exists_text, show=True)
            dpg.configure_item(exp_json_exists_tooltip, show=True)
            dpg.set_value(dpg.get_item_children(exp_json_exists_tooltip)[1][0], "json файл с экспериментом существует в " + path)
        else:
            dpg.configure_item(exp_json_exists_text, show=False)
            dpg.configure_item(exp_json_exists_tooltip, show=False)

    def switch_mode(sender, app_data):
        '''
        Switches "Без дозаривания" / "С дозариванием"
        '''
        global last_exp_mode
        dpg.configure_item(mode_groups[last_exp_mode], show=False)
        last_exp_mode = exp_modes_keys.index(app_data)
        dpg.configure_item(mode_groups[last_exp_mode], show=True)

    def calc_btn_callback():
        '''
        Let's do the experiment
        '''
        cur_exp_mode = exp_modes_keys[last_exp_mode]
        fill_exp_res()
        dpg.delete_item(res_group, children_only=True)
        matrix_generators = (generate_matrix_main, generate_matrix_main_ripening)
        exp_res.init(len(algs))
        for i in range(exp_res.exp_count):
            m: np.ndarray = matrix_generators[last_exp_mode](exp_res.n, **exp_res.params)
            convert_to_p_matrix(m)
            do_experiment(m, exp_res, i)
        # VERY IMPORTANT LINE! Because can't json.dump this (numpy array).
        exp_res.last_res = None
        exp_res.calculate_average_error(len(algs))
        dpg.push_container_stack(res_group)
        tb, dpg_plot = generate_result_plot_table(exp_res, False)
        dpg.add_button(label="Добавить в 'Анализ экспериментов'", callback=lambda: add_to_experiment_analysis(exp_res))
        dpg.pop_container_stack()
        if (dpg.get_value(save_exp_checkbox)):
            save_btn_callback()
        if (dpg.get_value(save_csv_checkbox)):
            save_table_as_csv(exp_res, True, tb, os.path.join(working_directory, exp_res.evaluate_exp_name()+".csv"))
        if (dpg.get_value(save_plot_checkbox)):
            download_plot_matplotlib(exp_res, os.path.join(working_directory, exp_res.evaluate_exp_name()+".png"))
        if (dpg.get_value(add_exp_checkbox)):
            add_to_experiment_analysis(exp_res)
        i_increment_type = dpg.get_value(i_increment_type_radio_btn)
        if (i_increment_type == i_increment_types[0]):
            restore_exp_name_i_callback()
        elif (i_increment_type == i_increment_types[1]):
            dpg.set_value(exp_name_i_input, dpg.get_value(exp_name_i_input)+1)
            check_json_exp_exist_callback()

    exp_res = exp_res_props()
    #exp_inputs["exp_res"] = exp_res
    dpg.add_button(label="Выбрать из файла", callback=choose_from_file_btn_callback)
    dpg.add_separator()
    with dpg.group(horizontal=True):
        dpg.add_text("Название эксперимента")
        with dpg.tooltip(dpg.last_item()):
            dpg.add_text("Используйте ${i} для автоматической индексации экспериментов")
        exp_name_input = dpg.add_input_text(default_value="Эксперимент_${i}", width=500, callback=check_json_exp_exist_callback)
        exp_inputs["exp_name_input"] = exp_name_input
        dpg.add_text("${i}=")
        exp_name_i_input = dpg.add_input_int(min_value=1, min_clamped=True, width=75, callback=check_json_exp_exist_callback)
        exp_inputs["exp_name_i_input"] = exp_name_i_input
        dpg.add_button(label="Восстановить ${i}", callback=restore_exp_name_i_callback)
        with dpg.tooltip(dpg.last_item()):
            dpg.add_text("Значение ${i} станет таким, что имя эксперимента будет уникальным")
        dpg.add_button(label="Сбросить ${i}", callback=lambda: dpg.set_value(exp_name_i_input, 1))
        with dpg.tooltip(dpg.last_item()):
            dpg.add_text("Значение ${i} станет 1")
        exp_json_exists_text = dpg.add_text("(будет перезаписан)", show=False)
        with dpg.tooltip(exp_json_exists_text, show=False) as exp_json_exists_tooltip:
            dpg.add_text("")
        restore_exp_name_i_callback()
    i_increment_types = ("Умный", "+1", "Нет")
    with dpg.group(horizontal=True):
        dpg.add_text("Режим инкремента ${i}")
        with dpg.tooltip(dpg.last_item()):
            dpg.add_text("'%s': при вычислении эксперимента подставится такое значение ${i}, при котором имя эксперимента будет уникальным" % i_increment_types[0])
            dpg.add_text("'%s': при вычислении эксперимента следующее значение ${i} будет на 1 больше" % i_increment_types[1])
            dpg.add_text("'%s': при вычислении эксперимента значение ${i} не изменится" % i_increment_types[2])
        i_increment_type_radio_btn = dpg.add_radio_button(items=i_increment_types, horizontal=True)
        dpg.set_value(i_increment_type_radio_btn, i_increment_types[0])
    save_exp_checkbox = dpg.add_checkbox(label="Сохранять эксперимент автоматически в корневой папке", default_value=True)
    add_exp_checkbox = dpg.add_checkbox(label="Добавить в 'Анализ экспериментов' автоматически", default_value=True)
    save_csv_checkbox = dpg.add_checkbox(label="Автоматически сохранять таблицу", default_value=True)
    save_plot_checkbox = dpg.add_checkbox(label="Автоматически сохранять график", default_value=True)
    dpg.add_separator()
    with dpg.group(horizontal=True):
        dpg.add_text("Введите n")
        n_input = dpg.add_input_int(min_value=mu_div, default_value=20, min_clamped=True, callback=set_n)
        exp_inputs["n_input"] = n_input
        set_n(n_input, dpg.get_value(n_input))
    with dpg.group(horizontal=True):
        dpg.add_text("Введите кол-во экспериментов")
        exp_count_input = dpg.add_input_int(min_value=1, default_value=100, min_clamped=True)
        exp_inputs["exp_count_input"] = exp_count_input
        exp_res.exp_count = dpg.get_value(exp_count_input)
    with dpg.group(horizontal=True):
        dpg.add_text("Режим")
        mode_radio_btn = dpg.add_radio_button(items=exp_modes_keys, horizontal=True, callback=switch_mode)
        exp_inputs["mode_radio_btn"] = mode_radio_btn
    mode_groups = tuple([dpg.add_group(show=False) for key in exp_modes_keys])
    for i in range(len(mode_groups)):
        key = exp_modes_keys[i]
        params = exp_modes[key]
        dpg.push_container_stack(mode_groups[i])
        for p in params:
            generate_input_for_exp(p)
        dpg.pop_container_stack()
    switch_mode(mode_radio_btn, exp_modes_keys[0])
    m_algs = select_algs(exp_res)
    exp_inputs["m_algs"] = m_algs
    with dpg.group(horizontal=True):
        dpg.add_button(label="Вычислить", callback=calc_btn_callback)
        dpg.add_button(label="Сохранить", callback=save_btn_callback)
    dpg.add_text("")
    res_group = dpg.add_group()
    exp_inputs["res_group"] = res_group

def fill_experiment_tab(exp_res):
    '''
    Fill out experiment tab's content from exp_res_props. Useful when filling from file or from experiment analysis
    '''
    dpg.set_value(exp_inputs["exp_name_input"], exp_res.exp_name)
    dpg.set_value(exp_inputs["exp_name_i_input"], exp_res.exp_name_i)
    dpg.get_item_configuration(exp_inputs["exp_name_input"])["callback"]()
    dpg.set_value(exp_inputs["n_input"], exp_res.n)
    dpg.set_value(exp_inputs["exp_count_input"], exp_res.exp_count)
    dpg.set_value(exp_inputs["mode_radio_btn"], exp_res.exp_mode)
    dpg.get_item_configuration(exp_inputs["mode_radio_btn"])["callback"](exp_inputs["mode_radio_btn"], exp_modes_keys[exp_res.exp_mode])
    for p in exp_modes[exp_modes_keys[last_exp_mode]]:
        if (p["name"] in exp_res.params):
            if ("special" in p):
                if (p["special"] == "range"):
                    for i in range(2):
                        p_dpg_i = p["dpg"][i]
                        dpg.set_value(p_dpg_i, exp_res.params[p["name"]][i])
                        dpg.get_item_configuration(p_dpg_i)["callback"](p_dpg_i, dpg.get_value(p_dpg_i), dpg.get_item_user_data(p_dpg_i))
            else:
                dpg.set_value(p["dpg"], exp_res.params[p["name"]])
    res_group = exp_inputs["res_group"]
    dpg.delete_item(res_group, children_only=True)
    if ("phase_averages" in exp_res.__dict__ and exp_res.phase_averages != None):
        dpg.push_container_stack(res_group)
        generate_result_plot_table(exp_res, False)
        dpg.add_button(label="Добавить в 'Анализ экспериментов'", callback=lambda: add_to_experiment_analysis(exp_res))
        dpg.pop_container_stack()


def add_to_experiment_analysis(exp_res):
    '''
    Adds this experiment to experiment analysis tab
    '''
    # TODO: do it

def tab_experiment_analysis() -> None:
    '''
    Вкладка "Анализ экспериментов"
    '''
    # TODO: do it
