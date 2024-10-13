from tkinter import *
from tkinter import messagebox
from tkinter import scrolledtext
from tkinter import ttk 
from Services.simplex import Simplex
from tkinter.filedialog import *
from tkinter.messagebox import *
import re
import json
from fractions import Fraction
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use( 'tkagg' )
from sympy import symbols, plot_implicit, plot, Matrix,solve
from Services.graph import GaussAlgorithm

class App:
        constraints = []

        def add_ogr(self):
            self.constraints.append(ttk.Entry(self.task, validate="key",width=60))
            if len(self.constraints) <= 16:
                for index, ogr in enumerate(self.constraints):
                    ogr.grid(column=4,row = index + 7)
            else :
                print("TODO error")


        def del_ogr(self):
            """
                Удаляет последнее добавленное ограничение из списка и пользовательского интерфейса.

                Шаги:
                1. Если список ограничений не пустой, удаляет графический элемент (ограничение) из интерфейса с помощью `grid_remove`.
                2. Удаляет последнее ограничение из списка `constraints`.
            """
            if len(self.constraints) > 0:
                self.constraints[-1].grid_remove() 
                self.constraints.pop(-1)
        

        def save_as_file(self):
            """
                Сохраняет текущую задачу линейного программирования в файл формата `.bars`.

                Шаги:
                1. Открывает диалоговое окно для выбора имени и места сохранения файла.
                2. Создаёт словарь, содержащий целевую функцию, тип задачи (минимизация или максимизация), и список ограничений.
                3. Преобразует этот словарь в строку формата JSON.
                4. Сохраняет строку в файл.
            """
            save_as = asksaveasfilename(filetypes = (("bars files" , "*.bars"),))
            save_dict = {}
            save_dict["objective"] = self.objective.get()
            save_dict["min"] = self.enabled.get() 
            save_dict["constraints"] = [ constraint.get().lower() for constraint in self.constraints]
            json_save = json.dumps(save_dict)
            f = open(save_as, "w")
            f.write(json_save)
            f.close()
            

        def open_file(self):
            """
                Открывает файл формата `.bars` и восстанавливает состояние задачи.

                Шаги:
                1. Открывает диалоговое окно для выбора файла.
                2. Загружает данные из выбранного файла в формате JSON.
                3. Восстанавливает целевую функцию, ограничения и тип задачи в пользовательском интерфейсе.
                4. Если возникнет ошибка во время загрузки, она выводится в консоль.
            """
            open_file = askopenfilename(filetypes = (("bars files" , "*.bars"),))
            with open(open_file) as f:
                data = json.load(f)
            try:   
                self.objective.delete(0, END)
                self.objective.insert(0,data["objective"])
                for constraint in  self.constraints:
                    constraint.grid_remove() 

                self.constraints.clear()
                for constraint in data["constraints"]:
                    self.constraints.append(ttk.Entry(self.task, validate="key",width=60))
                    self.constraints[-1].insert(0,constraint)

                for index, ogr in enumerate(self.constraints):
                    ogr.grid(column=4,row = index + 7)
                
                self.enabled.set(data["min"])

            except Exception as ex:
                print(ex)


        def __init__(self, window):
            """
                   Инициализация графического интерфейса приложения.
                   window: главное окно приложения.
            """
            window.title('Лабораторная работа по методам оптимизации')
            window.geometry('700x700')
            menu = Menu(window)  
            
            
            # Добавление меню
            menu_items = Menu(menu)   
            menu_items = Menu(menu, tearoff=0)
            
            
            # Команды меню
            menu_items.add_command(label='Открыть',command=self.open_file)
            menu_items.add_command(label='Сохранить',command=self.save_as_file)
            menu.add_cascade(label='Файл', menu=menu_items)


            # Вкладки
            tab_control = ttk.Notebook(window)
            self.task = Frame(tab_control)
            self.spravka = Frame(tab_control)  
            self.simplex = Frame(tab_control) 
            tab_control.add(self.task, text='Задача') 
            tab_control.add(self.simplex, text='Симплекс')
            tab_control.add(self.spravka, text='Cправка')
 
            # Отображение ввода
            name_task = ttk.Label(self.task, text="Целевая функция:",anchor=NW)
            self.objective= ttk.Entry(self.task, validate="key",width=60,) 
            self.objective.grid(column=4, row=2)
            self.max = False  
            self.enabled = IntVar()
            self.max_button = Checkbutton(self.task, text="Max", variable=self.enabled)
            self.max_button.grid(column=4, row=3)
            name_task.grid(column=0, row=1)

            self.text = scrolledtext.ScrolledText(self.simplex, state='disable')
            self.spravka_text = scrolledtext.ScrolledText(self.spravka, state='disable')
            self.spravka_text_get()

            ogranichenie_task = ttk.Label(self.task, text="Ограничения:",anchor=NW)  
            ogranichenie_task.grid(column=0, row=5)
            
            
            btn_add= Button(self.task, text="Добавить ограничение", command=self.add_ogr)
            btn_del= Button(self.task, text="Удалить ограничение", command=self.del_ogr)
            btn_add.grid(column=3,row=6)
            btn_del.grid(column=5,row=6)
            btn_solve= Button(self.task, text="Решить графически", command=self.solve_graph)
            btn_solve_simplex= Button(self.task, text="Решить Симплексом", command=self.simplex_solve)
            btn_solve.grid(column=3,row=9)
            btn_solve_simplex.grid(column=3,row=12)
            # Добавление на экран
            tab_control.pack(expand=1, fill='both')
            window.config(menu=menu)
                        

        def solve_graph(self):
            """
                Графическое решение задачи линейного программирования для двух переменных.
                Если переменных больше, используется симплекс-метод.
            """
            if (self.objective.get().lower().count('x') == 2):

                if self.check_constraint():
                    
                    xn,yn = self.get_gradient()
                    if self.enabled.get() == 0:
                        objective = ('min',self.objective.get())
                        xn = -1 * xn
                        yn = -1 * yn
                    else : 
                        objective = ('max',self.objective.get())

                    # plot
                    
                    x_1 , x_2 = symbols("x y")
                    expr = self.create_constuct(x_1 , x_2)
                    p1 = plot_implicit(expr , show=False,color="r",label = r'Искомая область')

                    fig, ax = plt.subplots()
                    self.move_sympyplot_to_axes(p1, ax)
                   
                    ax.arrow(0, 0, float(xn), float(yn), width = 0.005,color="g",label= rf'Нормаль ({xn},{yn})')
                    
                    constraints_str = []
                    for constraint in self.constraints:
                        constraints_str.append(constraint.get().lower())
                    try:
                        Lp = Simplex(count_vars=2, constraints=constraints_str, objective_fun=objective,text =self.text, char = END)
                        solution = Lp.solution
                        
                        x_1s = solution["x_1"]
                        x_2s = solution["x_2"]
                        #plt.plot(float(x_1s), float(x_2s), color = 'r')
                        plt.scatter( float(x_1s), float(x_2s), color='orange', s=40, marker='o',label = rf"Точка: ({x_1s};{x_2s})")
                        ax.text(0.18, -1.18, f"Ответ: x_1 = {x_1s}; x_2 = {x_2s} f({x_1s};{x_2s}) = {Lp.optimize_val}", color="C0")
                    except Exception as ex:
                        solution = ex
                        ax.text(0.18, -1.18, f"Ответ {solution}", color="C0")

                    plt.title("Графическое решение")

                    plt.xlabel(r'($x_1$)')
                    plt.ylabel(r'($x_2$)')
                    
                    plt.legend(bbox_to_anchor=(1, 1), loc=1, borderaxespad=0.)

                    plt.show()
            else:
                    m,b,f = self.get_graphmehod()
                    dsa = GaussAlgorithm(Matrix(m),Matrix(b),Matrix(f))
                    dsa.doit()
                    if dsa.check_matrix():
                        dsa.podstanovka()
                        print(dsa.f0)
                        print(dsa.symbolsList)
                        p1 = plot_implicit(dsa.recursion() , show=False,color="r",label = r'Искомая область')
                        fig, ax = plt.subplots()
                        
                        self.move_sympyplot_to_axes(p1, ax)
                        # TODO перписать так как это не верно
                        xn = dsa.f0.diff(dsa.expressions[-2])
                        yn = dsa.f0.diff(dsa.expressions[-1])
                        if self.enabled.get() == 0:
                            objective = ('min',self.objective.get())
                            xn = -1 * xn
                            yn = -1 * yn
                        else : 
                            objective = ('max',self.objective.get())

                        ax.arrow(0, 0, float(xn), float(yn), width = 0.050,color="g",label= rf'Нормаль ({xn,yn})')
                        plt.title("Графическое решение")
                        plt.show()
                    
        def get_graphmehod(self):
            """Возвращает начальные значения для использования в симплекс-методе"""

            return   [[1,2,5,-1],[1,-1,-1,2]] , [4,1], [-2,-1,-3,-1]
            
        def create_constuct(self, x_1 , x_2):
            """
               Создает символьное выражение для всех ограничений задачи.
            """
            exprs = '(x_1 >=0) & (x_2 >=0)'
            for  constraint1 in  self.constraints:
                 constraint = constraint1.get().split(' ')
                 ax1,ax2,bx = Fraction("0/1"), Fraction("0/1"), Fraction("1/1")
                 for i in range(0, len(constraint)):
                    
                    # построение начальной матрицы 
                    if '_' in constraint[i]:
                            coeff, index = constraint[i].split('_')
                            if constraint[i-1] is '-':
                                if index == '1':
                                    ax1 = Fraction("-" + coeff[:-1])
                                else:
                                    ax2 = Fraction("-" + coeff[:-1])
                            else:
                                if index == '1':
                                    ax1 = Fraction(coeff[:-1])
                                else:
                                    ax2 = Fraction(coeff[:-1])

                    elif constraint[i] == '>=':
                            ax1 *= -1
                            ax2 *= -1
                            bx *= -1
                 bx *=  Fraction(constraint[-1])
                 exprs += f'&({ax1} * x_1 + {ax2} *  x_2 <= {bx})'

            return eval(exprs)


        def move_sympyplot_to_axes(self, p, ax):
            """Переносит график SymPy на оси Matplotlib."""
            backend = p.backend(p)
            backend.ax = ax
            backend._process_series(backend.parent._series, ax, backend.parent)
            backend.ax.spines['right'].set_color('none')
            backend.ax.spines['top'].set_color('none')
            backend.ax.spines['bottom'].set_position('zero')
            plt.close(backend.fig)


        def get_gradient(self):
            """Возвращает коэффициенты градиента для целевой функции."""
            xn,yn = Fraction("0/1"), Fraction("0/1")
            constraint = self.objective.get().split(' ')
            i=0
            for j in range(len(constraint)):

                if '_' in constraint[j]:
                    coeff, index = constraint[j].split('_')
                    i+=1
                    if constraint[j-1] is '-':
                        if i is 1:
                            xn = Fraction("-" + coeff[:-1])
                        else: 
                            yn = Fraction("-" + coeff[:-1])
                    else: 
                        if i is 1:
                            xn = Fraction(coeff[:-1])
                        else: 
                            yn = Fraction(coeff[:-1])

            return xn, yn


        def draw_constraint(self, x_1, x_2):
            """Эта функция строит графические представления ограничений. Используются линии для обозначения границ допустимой области решения."""
            plt.axvline(0, color='k', label=r'$x_1$ = 0')
            plt.axhline(0, color='k', label=r'$x_2$ = 0')
            plt.axvline(7, label=r'$x_1 \geq 7$') # constraint 1
            plt.axhline(8, label=r'$x_2 \geq 8$') # constraint 2
            plt.plot(x_1, (2*(x_1)), label=r'$x_2 \leq 2x_1$') # constraint 3
            plt.plot(x_2, 25 - (1.5*x_1), label=r'$1.5x_1 + x_2 \leq 25$') # constraint 4


        def check_constraint(self):
            """Эта функция служит для проверки ограничений. Пока она всегда возвращает True, что значит, что ограничения всегда считаются валидными. Вероятно, её нужно доработать для реальной валидации"""
            return True


        def spravka_text_get(self):
            """
                просто справка
            """
            self.spravka_text.grid(column=2,row=2)
            self.spravka_text.configure(state='normal')
            
            text = """Описание работы программы: \n
                    Программа работает в двух режимах гарфический и симплекс:
                    Графический целевая функция должна иметь только x_1 and x_2 
                        * Количество ограничений не более 16
                        * Целевая функция должна быть в каноническом виде
                        * Ограничения должны быть >= или <=, 
                        так как валидировать это можно бесконечно ради безопасной работы программы лучше не использовать = .
                    Симплекс-метод : 
                        работает, к соажелнию только в одном режим с искуственным базисом и в автоматическом решении.
                        Особоенности данного режима:
                            Решает все уравнения с <= и >= и =
                            * Количество ограничений не более 16
                    Правила работы с программой:
                            Знак перед С всегда должен быть разделен пробелом с С.
                            С пишется слитно вместе с x_num, в независимоти дробь или целое.
                            Если коээфицент 0 можно упустить x_num
                            каждое слово по сути должно быть разделено пробелом 
                            По умолчению без нажатия на кнопку Max ищется Min
                        Пример вида ввода:
                                Целевая функция:
                                    2x_1 + 4x_3 + 5x_2 --> min
                                Ограничения:
                                    1x_1 + 2x_2 >= 4  
                                    2x_3 + 3x_1 <= 5 
                                    1x_3 + 3x_2 = 6
                        Обратите внимание, что в x_num число не должно быть больше, чем кол-во x_num в целевой функции.
                        В каждой строке ограничения должно быть только 1 ограничение
                    
                    """
            self.spravka_text.insert(END,  text)

            self.spravka_text.configure(state='disabled')

        def simplex_solve(self):
            """
                Эта функция решает задачу линейного программирования с помощью симплекс-метода. Она:

                Считывает целевую функцию и ограничения из интерфейса.
                Форматирует вывод для показа пользователю.
                Запускает симплекс-метод, обрабатывая исключения, если возникают ошибки.
                Выводит результат (решение или ошибку).
            """
            constraints_str = []
            self.text.delete('1.0', END)
            for constraint in self.constraints:
                constraints_str.append(constraint.get().lower())
            if self.enabled.get() == 0:
                objective = ('min',self.objective.get())
            else : 
                objective = ('max',self.objective.get())
           
            tabs = '\t' * 2
            nl_char = '\n'
            self.text.configure(state='normal') 
            self.text.insert(END, f"Целевая функция:   {objective[1]} --> {objective[0]} {nl_char}")
            self.text.grid(column=2,row=2)
          
            self.text.insert(END, f"Ограничения: {nl_char} {''.join([ tabs+constraint+ nl_char for constraint in constraints_str])} {nl_char}")
            try:
                Lp = Simplex(count_vars=self.objective.get().lower().count('x'), constraints=constraints_str, objective_fun=objective,text =self.text, char = END)
                solution = Lp.solution
                print(Lp.optimize_val)
            except Exception as ex:
                solution = ex
            
            #text.insert(END, Lp.hod_simplex)
            self.text.insert(END, f"Ответ: {solution} {nl_char}")
            self.text.configure(state='disabled')
            


if __name__ == "__main__":
        window = Tk()
        app = App(window)
        window.mainloop()