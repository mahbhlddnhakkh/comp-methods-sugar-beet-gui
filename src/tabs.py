import dearpygui.dearpygui as dpg
from src.gui_util import matrix_table, select_algs, convert_to_p_matrix, generate_result_plot_table
from src.config import CFG, mu_div
from src.util import exp_res_props
from src.experiment import do_experiment
from src.algorithms import algs
from tkinter import filedialog

big_result_table = None

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

    def experiment_simple():
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


    m_table = None
    exp_res = exp_res_props()
    exp_res.exp_count = 1
    m_is_p = dpg.add_checkbox(label="Преобразованная матрица P", default_value=True)
    dpg.add_separator()
    dpg.add_button(label="Выбрать из файла", callback=choose_from_file_callback)
    dpg.add_separator()
    # TODO: add randomize
    # in randomize popup user_data in callback will be really useful: https://dearpygui.readthedocs.io/en/latest/documentation/item-callbacks.html#user-data
    n_input = None
    with dpg.group(horizontal=True):
        dpg.add_text("Введите n")
        n_input = dpg.add_input_int(min_value=mu_div, max_value=20, default_value=CFG.manual_matrix_default_n, min_clamped=True, max_clamped=True, callback=set_n)
    m_table = matrix_table(False)
    set_n(None, dpg.get_value(n_input))
    m_algs = select_algs(exp_res)
    dpg.add_button(label="Вычислить", callback=experiment_simple)
    # Cool padding
    dpg.add_text("")
    res_group = dpg.add_group()
