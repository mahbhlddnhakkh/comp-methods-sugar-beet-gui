import dearpygui.dearpygui as dpg
if (__name__ == "__main__"):
    dpg.create_context()
from src.themes import create_theme_imgui_light
from src.tabs import tab_manual, tab_experiment

def create_gui():
    with dpg.window(tag="Primary window"):
        dpg.add_text("Лабораторная работа по сахарной свекле")
        with dpg.tab_bar():
            with dpg.tab(label="Вручную"):
                tab_manual()
            with dpg.tab(label="Эксперименты"):
                tab_experiment()
            with dpg.tab(label="Анализ экспериментов"):
                pass

def main():
    dpg.bind_theme(create_theme_imgui_light())
    with dpg.font_registry():
        with dpg.font("fonts/notomono-regular.ttf", 15, default_font=True, tag="Default font") as f:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)

    create_gui()
    dpg.bind_font("Default font")

    dpg.create_viewport(title='comp-methods-sugar-beet-gui', width=1400, height=800, min_width=1080, min_height=500)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("Primary window", True)
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()
