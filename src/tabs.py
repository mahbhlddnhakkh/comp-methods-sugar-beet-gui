import dearpygui.dearpygui as dpg
from src.gui_util import matrix_table, select_algs, convert_to_p_matrix, generate_result_plot_table, generate_input_for_exp, fix_range_min_max_input_exp
from src.config import CFG, mu_div
from src.util import exp_res_props, generate_matrix_main, generate_matrix_main_ripening, convert_to_p_matrix
from src.experiment import do_experiment
from src.algorithms import algs
from tkinter import filedialog
import sys

big_result_table = None

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

exp_name_i = 1

def tab_manual() -> None:
    '''
    Вкладка "Вручную"
    '''

    def choose_from_file_callback(sender, app_data):
        dpg.lock_mutex()
        m_table.set_from_file(filedialog.askopenfilename())
        dpg.unlock_mutex()
        dpg.set_value(n_input, m_table._n)
        exp_res.n = m_table._n

    def set_n(sender, app_data):
        exp_res.n = app_data
        m_table.set_n(app_data)

    def calc_btn_callback():
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
    dpg.add_button(label="Выбрать из файла", callback=choose_from_file_callback)
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
    global exp_name_i

    def choose_from_file_callback():
        pass

    def set_n(sender, app_data):
        exp_res.n = app_data

    def restore_exp_name_i_callback():
        pass

    def switch_mode(sender, app_data):
        global last_exp_mode
        dpg.configure_item(mode_groups[last_exp_mode], show=False)
        last_exp_mode = exp_modes_keys.index(app_data)
        dpg.configure_item(mode_groups[last_exp_mode], show=True)

    def calc_btn_callback():
        cur_exp_mode = exp_modes_keys[last_exp_mode]
        fix_range_min_max_input_exp(exp_modes[cur_exp_mode])
        # TODO: exp name? Can't evaluate ${i} without big_result_table
        exp_name_i = dpg.get_value(exp_name_i_input)
        exp_res.exp_name = dpg.get_value(exp_name_inp)
        exp_res.n = dpg.get_value(n_input)
        exp_res.exp_count = dpg.get_value(exp_count_input)
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
        dpg.delete_item(res_group, children_only=True)
        m_algs.run_default_if_params_popup_not_opened()
        matrix_generators = (generate_matrix_main, generate_matrix_main_ripening)
        exp_res.init(len(algs))
        for i in range(exp_res.exp_count):
            m: np.ndarray = matrix_generators[last_exp_mode](exp_res.n, **exp_res.params)
            convert_to_p_matrix(m)
            do_experiment(m, exp_res, i)
        exp_res.last_res = None
        exp_res.calculate_average_error(len(algs))
        dpg.push_container_stack(res_group)
        generate_result_plot_table(exp_res, False)
        dpg.pop_container_stack()

    exp_res = exp_res_props()
    dpg.add_separator()
    dpg.add_button(label="Выбрать из файла", callback=choose_from_file_callback)
    dpg.add_separator()
    with dpg.group(horizontal=True):
        dpg.add_text("Название эксперимента")
        with dpg.tooltip(dpg.last_item()):
            dpg.add_text("Используйте ${i} для %sample_text%")
        exp_name_inp = dpg.add_input_text(default_value="Эксперимент_${i}", width=500)
        dpg.add_text("${i}=")
        exp_name_i_input = dpg.add_input_int(default_value=exp_name_i, min_value=1, min_clamped=True, width=75)
        dpg.add_button(label="Восстановить ${i}", callback=restore_exp_name_i_callback)
        dpg.add_button(label="Сбросить ${i}", callback=lambda: dpg.set_value(exp_name_i_input, 1))
    save_exp_checkbox = dpg.add_checkbox(label="Сохранять эксперимент автоматически в корневой папке", default_value=True)
    add_exp_checkbox = dpg.add_checkbox(label="Добавить в 'Анализ экспериментов' автоматически", default_value=True)
    dpg.add_separator()
    with dpg.group(horizontal=True):
        dpg.add_text("Введите n")
        n_input = dpg.add_input_int(min_value=mu_div, default_value=20, min_clamped=True, callback=set_n)
        set_n(n_input, dpg.get_value(n_input))
    with dpg.group(horizontal=True):
        dpg.add_text("Введите кол-во экспериментов")
        exp_count_input = dpg.add_input_int(min_value=1, default_value=100, min_clamped=True)
        exp_res.exp_count = dpg.get_value(exp_count_input)
    with dpg.group(horizontal=True):
        dpg.add_text("Режим")
        mode_radio_btn = dpg.add_radio_button(items=exp_modes_keys, horizontal=True, callback=switch_mode)
    mode_groups = tuple([dpg.add_group(show=False) for key in exp_modes_keys])
    # TODO: move this creation do a different function so we can restore values
    for i in range(len(mode_groups)):
        key = exp_modes_keys[i]
        params = exp_modes[key]
        dpg.push_container_stack(mode_groups[i])
        for p in params:
            generate_input_for_exp(p)
        dpg.pop_container_stack()
    switch_mode(mode_radio_btn, exp_modes_keys[0])
    m_algs = select_algs(exp_res)
    with dpg.group(horizontal=True):
        dpg.add_button(label="Вычислить", callback=calc_btn_callback)
        dpg.add_button(label="Сохранить")
    dpg.add_text("")
    res_group = dpg.add_group()
