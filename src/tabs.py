import dearpygui.dearpygui as dpg
from src.gui_util import matrix_table, select_algs, generate_result_plot_table, generate_result_table_columns, generate_result_table_row, generate_input_for_exp, generate_result_plot, fix_range_min_max_input_exp, download_plot_matplotlib, save_table_as_csv
from src.config import CFG, mu_div
from src.util import exp_res_props, convert_to_p_matrix
from src.experiment import do_experiment
from src.user_config import algs, exp_modes, exp_modes_func
from tkinter import filedialog
import sys
import os
import re

big_result_table = None

exp_inputs = {}

exp_modes_keys = tuple(exp_modes.keys())

last_exp_mode = 0

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
        if (file_path == "" or file_path == ()):
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
    exp_res.exp_name = "Эксперимент"
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
        n_input = dpg.add_input_int(min_value=mu_div, max_value=20, default_value=5, min_clamped=True, max_clamped=True, callback=set_n, on_enter=True)
        dpg.add_text("(для подтверждения ввода нажмите enter)")
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
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("Любые", "*.*")], initialdir=exp_res.working_directory)
        dpg.unlock_mutex()
        if (path == "" or path == ()):
            return
        exp_res.get_from_file(path)
        #choose_working_directory_callback(os.path.dirname(path))
        fill_experiment_tab(exp_res)

    def save_btn_callback():
        '''
        Button "Сохранить"
        '''
        #fill_exp_res_name()
        path = exp_res.evaluate_exp_filename()
        fill_exp_res()
        exp_res.dump_to_file(os.path.join(exp_res.working_directory, path))
        check_json_exp_exist_callback()

    def set_n(sender, app_data):
        '''
        As name implies, sets exp_res n
        '''
        exp_res.n = app_data

    def restore_exp_name_i_callback():
        '''
        Calculate correct ${i}
        '''
        #fill_exp_res_name()
        if (not "${i}" in exp_res.exp_name):
            reset_exp_name_i_callback()
            return
        r = re.compile(exp_res.evaluate_exp_filename_regex())
        exp_name_parts = exp_res.get_exp_filename_without_evaluation().split("${i}", 1)
        cur_exp_files_ind = [int(f.replace(exp_name_parts[0], "", 1).replace(exp_name_parts[1], "", 1)) for f in os.listdir(exp_res.working_directory) if os.path.isfile(os.path.join(exp_res.working_directory, f)) and r.match(f)]
        cur_exp_files_ind.sort()
        if (big_result_table != None):
            tb_ch = dpg.get_item_children(big_result_table)[1]
            if (len(tb_ch) > 0):
                cur_exp_table_ind = []
                for row in tb_ch:
                    tmp = dpg.get_item_user_data(row).evaluate_exp_filename()
                    if (r.match(tmp)):
                        cur_exp_files_ind.append(int(tmp.replace(exp_name_parts[0], "", 1).replace(exp_name_parts[1], "", 1)))
                cur_exp_table_ind.sort()
                cur_exp_files_ind = list(set(cur_exp_files_ind).union(set(cur_exp_table_ind)))
        i = 1
        while (i <= len(cur_exp_files_ind) and cur_exp_files_ind[i-1] == i):
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
        tmp_exp_res_name = exp_res.exp_name
        tmp_exp_res_name_i = exp_res.exp_name_i
        fill_exp_res_name()
        filename = exp_res.evaluate_exp_filename()
        exp_res.exp_name = tmp_exp_res_name
        exp_res.exp_name_i = tmp_exp_res_name_i
        path = os.path.join(exp_res.working_directory, filename)
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
        exp_res.init(len(algs))
        for i in range(exp_res.exp_count):
            m: np.ndarray = exp_modes_func[last_exp_mode](exp_res.n, **exp_res.params)
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
            save_table_as_csv(exp_res, tb, os.path.join(exp_res.working_directory, exp_res.evaluate_exp_name()+".csv"))
        if (dpg.get_value(save_plot_checkbox)):
            download_plot_matplotlib(exp_res, os.path.join(exp_res.working_directory, exp_res.evaluate_exp_name()+".png"))
        if (dpg.get_value(add_exp_checkbox)):
            add_to_experiment_analysis(exp_res)
        i_increment_type = dpg.get_value(i_increment_type_radio_btn)
        if (i_increment_type == i_increment_types[0]):
            restore_exp_name_i_callback()
        elif (i_increment_type == i_increment_types[1]):
            dpg.set_value(exp_name_i_input, dpg.get_value(exp_name_i_input)+1)
        check_json_exp_exist_callback()

    def choose_working_directory_callback(_path = None):
        '''
        Chooses current working directory (to automatically save things)
        '''
        tmp = _path
        if (tmp == None):
            dpg.lock_mutex()
            tmp = filedialog.askdirectory(initialdir=exp_res.working_directory)
            dpg.unlock_mutex()
        if (tmp == "" or tmp == ()):
            return
        exp_res.working_directory = tmp
        dpg.set_value(working_directory_input, exp_res.working_directory)

    exp_res = exp_res_props()
    exp_inputs["exp_res"] = exp_res
    exp_res.working_directory = os.getcwd()
    with dpg.group(horizontal=True):
        dpg.add_text("Рабочая директория")
        working_directory_input = dpg.add_input_text(default_value=exp_res.working_directory, user_data=choose_working_directory_callback, readonly=True)
        exp_inputs["working_directory_input"] = working_directory_input
        dpg.add_button(label="Изменить", user_data=None, callback=lambda sender, app_data, user_data: choose_working_directory_callback(user_data))
    dpg.add_separator()
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
        fill_exp_res_name()
        with dpg.tooltip(dpg.last_item()):
            dpg.add_text("Значение ${i} станет таким, что имя эксперимента будет уникальным")
        dpg.add_button(label="Сбросить ${i}", callback=reset_exp_name_i_callback)
        with dpg.tooltip(dpg.last_item()):
            dpg.add_text("Значение ${i} станет 1")
        exp_json_exists_text = dpg.add_text("(будет перезаписан)", show=False)
        with dpg.tooltip(exp_json_exists_text, show=False) as exp_json_exists_tooltip:
            dpg.add_text("")
        restore_exp_name_i_callback()
        fill_exp_res_name()
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
    save_csv_checkbox = dpg.add_checkbox(label="Автоматически сохранять таблицу (csv)", default_value=False)
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
    if (not exp_inputs["exp_res"] is exp_res):
        exp_inputs["exp_res"].copy(exp_res)
    tab_bar = dpg.get_item_parent(dpg.get_item_parent(big_result_table))
    dpg.set_value(tab_bar, dpg.get_item_children(tab_bar)[1][1])
    dpg.set_value(exp_inputs["exp_name_input"], exp_res.exp_name)
    dpg.set_value(exp_inputs["exp_name_i_input"], exp_res.exp_name_i)
    dpg.get_item_configuration(exp_inputs["working_directory_input"])["user_data"](exp_res.working_directory)
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

    def get_index_input_from_tb_ch(tb_ch, i):
        '''
        Get index input from table's children
        '''
        return dpg.get_item_children(dpg.get_item_children(tb_ch[i])[1][0])[1][1]

    def set_index_input_i(_index_input, i) -> None:
        '''
        Sets i in index input
        '''
        dpg.configure_item(_index_input, user_data=(dpg.get_item_user_data(_index_input)[0], i))
        dpg.set_value(_index_input, i)

    def index_button_callback(_index_input, add):
        '''
        Callback for 2 index buttons: up or down
        '''
        _index_input_value = dpg.get_value(_index_input) + add
        dpg.set_value(_index_input, _index_input_value)
        dpg.get_item_configuration(_index_input)["callback"](_index_input, _index_input_value, dpg.get_item_user_data(_index_input))

    def index_callback(sender, app_data, user_data):
        '''
        Callback for index input for each row
        '''
        ind = app_data
        if (app_data < 1):
            ind = 1
            dpg.set_value(sender, ind)
        tb_ch: list = dpg.get_item_children(big_result_table)[1]
        if (app_data > len(tb_ch)):
            ind = len(tb_ch)
            dpg.set_value(sender, ind)
        if (ind == user_data[1]):
            return
        start = 0
        end = 0
        delta = 0
        if (ind > user_data[1]):
            start = user_data[1] - 1
            end = ind
        else:
            start = ind
            end = user_data[1]
        tb_ch.insert(ind-1, tb_ch.pop(user_data[1]-1))
        for i in range(start, end):
            _index_input = get_index_input_from_tb_ch(tb_ch, i)
            _ind = i + 1
            set_index_input_i(_index_input, _ind)
        dpg.reorder_items(big_result_table, 1, tb_ch)
        dpg.configure_item(sender, user_data=(user_data[0], ind))

    def delete_row(r):
        '''
        Deletes row and fixes order
        '''
        tb_ch: list = dpg.get_item_children(big_result_table)[1]
        ind = tb_ch.index(r)
        for i in range(ind+1, len(tb_ch)):
            _index_input = get_index_input_from_tb_ch(tb_ch, i)
            set_index_input_i(_index_input, i)
        dpg.delete_item(r)

    def show_plot_popup(exp_res):
        '''
        Creates popup with plot
        '''
        with dpg.window(label="График "+exp_res.evaluate_exp_name(), width=800):
            generate_result_plot(exp_res, True)

    # TODO: better tooltips
    tmp_exp_res = exp_res.spawn_copy()
    r = generate_result_table_row(tmp_exp_res, big_result_table, False)
    with dpg.table_cell(parent=r):
        dpg.add_button(label="Э", callback=lambda sender: fill_experiment_tab(dpg.get_item_user_data(dpg.get_item_parent(dpg.get_item_parent(sender)))))
        with dpg.tooltip(dpg.last_item()):
            dpg.add_text("Записать в эксперименты")
        dpg.add_button(label="Г", callback=lambda sender: show_plot_popup(dpg.get_item_user_data(dpg.get_item_parent(dpg.get_item_parent(sender)))))
        with dpg.tooltip(dpg.last_item()):
            dpg.add_text("Показать график")
        dpg.add_button(label="У", callback=lambda sender: delete_row(dpg.get_item_parent(dpg.get_item_parent(sender))))
        with dpg.tooltip(dpg.last_item()):
            dpg.add_text("Удалить строку")
    with dpg.table_cell(parent=r, before=dpg.get_item_children(r)[1][0]):
        index_width = 20
        default_index = len(dpg.get_item_children(big_result_table)[1])
        index_input = dpg.add_input_int(default_value=len(dpg.get_item_children(big_result_table)[1]), user_data=(r, default_index), width=index_width, step=0, callback=index_callback, on_enter=True)
        dpg.add_button(label="-", width=index_width, before=index_input, user_data=index_input, callback=lambda sender, app_data, user_data: index_button_callback(user_data, -1))
        dpg.add_button(label="+", width=index_width, user_data=index_input, callback=lambda sender, app_data, user_data: index_button_callback(user_data, 1))

def tab_experiment_analysis() -> None:
    '''
    Вкладка "Анализ экспериментов"
    '''

    def save_csv():
        '''
        Saves whole table as csv
        '''
        temp_exp_res = exp_res_props()
        temp_exp_res.exp_name = "Анализ экспериментов"
        ignored_columns = [0, len(dpg.get_item_children(big_result_table)[0])-1]
        save_table_as_csv(temp_exp_res, big_result_table, None, ignored_columns)
    
    def add_multiple_experiments_files() -> None:
        '''
        Get multiple experiments from files
        '''
        dpg.lock_mutex()
        paths = filedialog.askopenfilenames(filetypes=[("JSON", "*.json"), ("Любые", "*.*")])
        dpg.unlock_mutex()
        if (paths == ""):
            return
        for p in paths:
            temp_exp_res = exp_res_props()
            temp_exp_res.get_from_file(p)
            add_to_experiment_analysis(temp_exp_res)

    global big_result_table
    with dpg.group(horizontal=True):
        dpg.add_button(label="Добавить эксперименты", callback=add_multiple_experiments_files)
        dpg.add_button(label="Сохранить в CSV", callback=lambda: save_csv())
        dpg.add_button(label="Очистить", callback=lambda: dpg.delete_item(big_result_table, children_only=True, slot=1))
    dpg.add_text("")
    big_result_table = dpg.add_table(header_row=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True, resizable=True, policy=dpg.mvTable_SizingStretchProp)
    dpg.add_table_column(label="Индекс", parent=big_result_table, init_width_or_weight=0.15)
    generate_result_table_columns(big_result_table, False)
    dpg.add_table_column(label="Управление", parent=big_result_table, init_width_or_weight=0.15)
