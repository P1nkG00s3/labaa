from fractions import Fraction
from warnings import warn


class Simplex(object):
    def __init__(self, count_vars, constraints, objective_fun, text, char):
        """
                Инициализация класса Simplex.
                count_vars: количество переменных.
                constraints: список ограничений.
                objective_fun: целевая функция (минимизация или максимизация).
        """
        self.coloumn_pivot = []
        self.char = char
        self.check_eq = True
        self.hod_simplex = text
        self.count_vars = count_vars
        self.constraints = constraints
        self.objective = objective_fun[0]
        self.objective_fun = objective_fun[1]
        self.coeff_matrix, self.r_rows, self.num_s_vars, self.num_r_vars = self.construct_matrix_from_constraints()
        del self.constraints
        self.basic_vars = [0 for i in range(len(self.coeff_matrix))]
        self.phase1()
        r_index = self.num_r_vars + self.num_s_vars

        # for i in self.basic_vars:
        #     if i > r_index:
        #         raise ValueError("Решения не существует")

        self.delete_r_vars()

        if 'min' in self.objective.lower():
            self.solution = self.objective_minimize()

        else:
            self.solution = self.objective_maximize()
        self.solution["val"] = self.coeff_matrix[0][-1]
        self.optimize_val = self.coeff_matrix[0][-1]

    def construct_matrix_from_constraints(self):
        """
            Строит матрицу коэффициентов из системы ограничений.

            Цель:
            1. Преобразовать ограничения в симплекс-таблицу.
            2. Добавить дополнительные переменные (избыточные, резервные и искусственные), чтобы преобразовать все неравенства в равенства.
            3. Инициализировать базисные переменные для начала симплексного метода.

            Аргументы:
            - self.constraints: список ограничений, каждое из которых содержит строки вида "2_x1 + 3_x2 <= 5".
            - self.count_vars: количество исходных переменных задачи.

            Шаги:
            1. Определить количество избыточных переменных (slack variables) и искусственных переменных (artificial variables).
            2. Создать матрицу коэффициентов (начальная симплекс-таблица) с учётом всех переменных.
            3. Для каждого ограничения обновить соответствующую строку матрицы, добавляя коэффициенты переменных и дополнительные переменные.

            Возвращает:
            - coeff_matrix: симплекс-таблица, готовая для использования в симплекс-методе.
            - r_rows: список строк, которые связаны с искусственными переменными.
            - num_s_vars: количество избыточных переменных.
            - num_r_vars: количество искусственных переменных.
        """
        num_s_vars = 0  # количество резервных и избыточных переменных
        num_r_vars = 0  # количество дополнительных переменных, чтобы сбалансировать равенство и меньше, чем равно
        for expression in self.constraints:
            if '>=' in expression:
                num_s_vars += 1
                self.check_eq = False

            elif '<=' in expression:
                num_s_vars += 1
                num_r_vars += 1
                self.check_eq = False

            elif '=' in expression:
               num_r_vars += 1

        total_vars = self.count_vars + num_s_vars + num_r_vars

        coeff_matrix = [[Fraction("0/1") for i in range(total_vars+1)] for j in range(len(self.constraints)+1)]
        s_index = self.count_vars
        r_index = self.count_vars + num_s_vars
        r_rows = [] # хранит ненулевой индекс r
        for i in range(1, len(self.constraints)+1):
            constraint = self.constraints[i-1].split(' ')
            # построение начальной матрицы
            for j in range(len(constraint)):

                if '_' in constraint[j]:
                    coeff, index = constraint[j].split('_')
                    if constraint[j-1] is '-':
                        coeff_matrix[i][int(index)-1] = Fraction("-" + coeff[:-1])
                    else:
                        coeff_matrix[i][int(index)-1] = Fraction(coeff[:-1])

                elif constraint[j] == '<=':
                    coeff_matrix[i][s_index] = Fraction("1/1")  # добавить избыточную переменную
                    s_index += 1

                elif constraint[j] == '>=':
                    coeff_matrix[i][s_index] = Fraction("-1/1")  # резервная переменная
                    coeff_matrix[i][r_index] = Fraction("1/1")
                    s_index += 1
                    r_index += 1
                    r_rows.append(i)

                elif constraint[j] == '=':
                    coeff_matrix[i][r_index] = Fraction("1/1")
                    r_index += 1
                    r_rows.append(i)

            coeff_matrix[i][-1] = Fraction(constraint[-1])

        return coeff_matrix, r_rows, num_s_vars, num_r_vars

    def phase1(self):
        """
            Первая фаза симплекс-метода.

            Цель:
            Минимизировать сумму искусственных переменных для получения допустимого базиса.
            Это необходимо, если в задаче есть ограничения с неравенствами вида '>=' или '='.

            Шаги:
            1. Устанавливаем целевую функцию как сумму искусственных переменных (r1 + r2 + ...).
            2. Проводим симплексные итерации до тех пор, пока все элементы целевой строки не будут неотрицательными.
            3. Обновляем симплекс-таблицу и переменные.

        """
        # Целевая функция здесь минимизирует r1+ r2 + r3 + ... + rn
        r_index = self.count_vars + self.num_s_vars
        for i in range(r_index, len(self.coeff_matrix[0])-1):
            self.coeff_matrix[0][i] = Fraction("-1/1")
        coeff_0 = 0
        for i in self.r_rows:
            self.coeff_matrix[0] = add_row(self.coeff_matrix[0], self.coeff_matrix[i])
            self.basic_vars[i] = r_index
            r_index += 1
        s_index = self.count_vars
        for i in range(1, len(self.basic_vars)):
            if self.basic_vars[i] == 0:
                self.basic_vars[i] = s_index
                s_index += 1

        # Запускает симплексные итерации
        key_column = max_index(self.coeff_matrix[0])
        condition = self.coeff_matrix[0][key_column] > 0
        nl_char = '\n'
        probel = ' '
        while condition is True:
            self.print_matrix(check=self.check_eq)

            key_row = self.find_key_row(key_column = key_column)

            self.basic_vars[key_row] = key_column
            self.coloumn_pivot.append(key_column)
            pivot = self.coeff_matrix[key_row][key_column]
            self.hod_simplex.insert(self.char, nl_char + f"Следующий опорный элемент строка/столбец({key_row},{key_column + 1}) {pivot}: {nl_char}")
            self.normalize_to_pivot(key_row, pivot)
            self.make_key_column_zero(key_column, key_row)

            key_column = max_index(self.coeff_matrix[0])
            condition = self.coeff_matrix[0][key_column] > 0


        self.print_matrix(check=self.check_eq)

    def find_key_row(self, key_column):
        """
               Поиск строки с опорным элементом (min положительное соотношение).
               Возвращает индекс строки с минимальным отношением свободного члена
               к элементу ключевого столбца.
               key_column: индекс ключевого столбца.
        """
        min_val = float("inf")
        min_i = 0
        for i in range(1, len(self.coeff_matrix)):
            if self.coeff_matrix[i][key_column] > 0:
                val = self.coeff_matrix[i][-1] / self.coeff_matrix[i][key_column]
                if val <  min_val:
                    min_val = val
                    min_i = i
        if min_val == float("inf"):
            raise ValueError("Решение неограниченно")
        return min_i

    def normalize_to_pivot(self, key_row, pivot):
        """
                Нормализация строки к опорному элементу (pivot).
                Делит все элементы строки на значение опорного элемента.
                key_row: индекс строки с опорным элементом.
                pivot: значение опорного элемента.
        """
        for i in range(len(self.coeff_matrix[0])):
            self.coeff_matrix[key_row][i] /= pivot

    def make_key_column_zero(self, key_column, key_row):
        """
               Обнуление ключевого столбца, кроме опорного элемента.
               Для всех строк делается вычитание с учетом коэффициентов.
               key_column: индекс ключевого столбца.
               key_row: индекс строки с опорным элементом.
        """
        num_columns = len(self.coeff_matrix[0])
        for i in range(len(self.coeff_matrix)):
            if i != key_row:
                factor = self.coeff_matrix[i][key_column]
                for j in range(num_columns):
                    self.coeff_matrix[i][j] -= self.coeff_matrix[key_row][j] * factor

    def delete_r_vars(self):
        """
        Удаляет искусственные переменные (R-variables) из симплекс-таблицы.

        Симплекс-таблица может содержать дополнительные переменные, которые были введены
        для задач с неравенствами "больше или равно" (>=) или "равно" (=). Эти переменные
        являются искусственными и должны быть удалены, когда их больше не требуется для вычислений.

        Процесс удаления происходит следующим образом:
        1. Для каждой строки симплекс-таблицы (coeff_matrix) вычисляется длина строки (количество элементов).
        2. Определяется "нормальная" длина строки — это количество переменных в задаче (count_vars) плюс количество
           дополнительных переменных (num_s_vars) и один столбец для свободного члена.
        3. Если текущая длина строки превышает нормальную длину (из-за искусственных переменных), из строки удаляются
           последние элементы до тех пор, пока длина не станет равной нормальной.

        Аргументы:
        - self.coeff_matrix: симплекс-таблица с коэффициентами, где строки представляют собой ограничения задачи.
        - self.count_vars: количество исходных переменных задачи.
        - self.num_s_vars: количество дополнительных переменных (например, для приведения неравенств к равенствам).
        """
        for i in range(len(self.coeff_matrix)):
            non_r_length = self.count_vars + self.num_s_vars + 1
            length = len(self.coeff_matrix[i])
            while length != non_r_length:
                del self.coeff_matrix[i][non_r_length-1]
                length -= 1

    def update_objective_fun(self):
        """
               Обновляет целевую функцию для соответствия текущему базису. Добавляет новые переменные,
               которые вошли в базис, и обновляет коэффициенты в целевой строке.
        """
        objective_fun_coeffs = self.objective_fun.split()
        for i in range(len(objective_fun_coeffs)):
            if '_' in objective_fun_coeffs[i]:
                coeff, index = objective_fun_coeffs[i].split('_')
                if objective_fun_coeffs[i-1] is '-':
                    self.coeff_matrix[0][int(index)-1] = Fraction(coeff[:-1] + "/1")
                else:
                    self.coeff_matrix[0][int(index)-1] = Fraction("-" +coeff[:-1] + "/1")


    def objective_minimize(self):

        """
                Функция для минимизации целевой функции. Аналогична objective_maximize, но
                используется для задач минимизации.
        """
        self.update_objective_fun()

        self.hod_simplex.insert(self.char,"*****************\n")
        for row, column in enumerate(self.basic_vars[1:]):
            if self.coeff_matrix[0][column] != 0:
                self.coeff_matrix[0] = add_row(self.coeff_matrix[0], multiply_const_row(-self.coeff_matrix[0][column], self.coeff_matrix[row+1]))

        key_column = max_index(self.coeff_matrix[0])
        condition = self.coeff_matrix[0][key_column] > 0

        while condition is True:
            self.print_matrix(check=False)
            key_row = self.find_key_row(key_column = key_column)
            self.basic_vars[key_row] = key_column
            pivot = self.coeff_matrix[key_row][key_column]
            nl_char = '\n'
            probel = ' '
            self.hod_simplex.insert(self.char, nl_char + f"Следующий опорный элемент строка/столбец({key_row },{key_column + 1}) {pivot}: {nl_char}")
            self.normalize_to_pivot(key_row, pivot)
            self.make_key_column_zero(key_column, key_row)

            key_column = max_index(self.coeff_matrix[0])
            condition = self.coeff_matrix[0][key_column] > 0

        self.print_matrix(check=False)
        solution = {}
        for i, var in enumerate(self.basic_vars[1:]):
            if var < self.count_vars:
                solution['x_'+str(var+1)] = self.coeff_matrix[i+1][-1]

        for i in range(0, self.count_vars):
            if i not in self.basic_vars[1:]:
                solution['x_'+str(i+1)] = Fraction("0/1")
    
        return solution

    def objective_maximize(self):
        """
            Максимизация целевой функции с помощью симплекс-метода.
            Алгоритм выполняется до тех пор, пока в целевой строке (первой строке таблицы) есть отрицательные значения.

            Шаги:
            1. Обновление целевой функции (выражение целевой функции через новые базисные переменные).
            2. Коррекция целевой строки с учетом текущих базисных переменных.
            3. Определение ключевого столбца (столбца с минимальным отрицательным значением в целевой строке).
            4. Итерация по симплексу: выбор ключевой строки, нормализация по опорному элементу, обнуление остальных элементов в ключевом столбце.
            5. Повторение до тех пор, пока все значения в целевой строке не будут неотрицательными (условие оптимальности).
            6. Возврат оптимального решения в виде словаря с переменными и их значениями.

            Возвращает:
            Словарь с оптимальными значениями переменных.
        """
        self.update_objective_fun()

        for row, column in enumerate(self.basic_vars[1:]):
            if self.coeff_matrix[0][column] != 0:
                self.coeff_matrix[0] = add_row(self.coeff_matrix[0], multiply_const_row(-self.coeff_matrix[0][column], self.coeff_matrix[row+1]))

        key_column = min_index(self.coeff_matrix[0])
        self.print_matrix()
        condition = self.coeff_matrix[0][key_column] < 0

        while condition is True:

            key_row = self.find_key_row(key_column = key_column)
            self.basic_vars[key_row] = key_column
            pivot = self.coeff_matrix[key_row][key_column]
            self.normalize_to_pivot(key_row, pivot)
            self.make_key_column_zero(key_column, key_row)

            key_column = min_index(self.coeff_matrix[0])
            condition = self.coeff_matrix[0][key_column] < 0

        solution = {}
        for i, var in enumerate(self.basic_vars[1:]):
            if var < self.count_vars:
                solution['x_'+str(var+1)] = self.coeff_matrix[i+1][-1]

        for i in range(0, self.count_vars):
            if i not in self.basic_vars[1:]:
                solution['x_'+str(i+1)] = Fraction("0/1")

        return solution
    
    def print_matrix(self,check = True):
        """
            Выводит текущую симплекс-таблицу.

            Аргументы:
            check: если True, то выводится отформатированная таблица для промежуточных шагов.
                   Если False, то таблица выводится в "сыром" виде.

            Эта функция отображает таблицу с учетом базисных переменных и опорных элементов,
            форматируя ее для более удобного восприятия. Вывод также может быть использован для интерфейса программы.
        """
        nl_char = '\n'
        probel = ' '
        if check :
            for row in self.coeff_matrix:
                if row == self.coeff_matrix[0]:
                    last = f"{''.join([str( -1 * row[coloumni]) + probel if coloumni not in self.coloumn_pivot and coloumni + 1 <= self.count_vars or coloumni == len(row)- 1  else '' for coloumni in range(0,len(row))])} {nl_char}"
                else:     
                    self.hod_simplex.insert(self.char, f"{''.join([str(row[coloumni]) + probel if coloumni not in self.coloumn_pivot and coloumni + 1 <= self.count_vars or coloumni == len(row)- 1 else ''  for coloumni in range(0,len(row))])} {nl_char}") 
        else:
            for row in self.coeff_matrix:
                if row == self.coeff_matrix[0]:
                    last = f"{''.join([str(coloumn) + probel for coloumn in row])} {nl_char}"
                else:    
                    self.hod_simplex.insert(self.char, f"{''.join([str(coloumn) + probel for coloumn in row])} {nl_char}") 
        self.hod_simplex.insert(self.char,last)

def add_row(row1, row2):
    """
        Складывает два вектора (строки симплекс-таблицы) элемент за элементом.

        Аргументы:
        row1: первая строка.
        row2: вторая строка.

        Возвращает:
        Новый вектор, где каждый элемент является суммой соответствующих элементов row1 и row2.
    """
    row_sum = [0 for i in range(len(row1))]
    for i in range(len(row1)):
        row_sum[i] = row1[i] + row2[i]
    return row_sum

def max_index(row):
    """
        Находит индекс максимального элемента в строке.

        Аргументы:
        row: строка, в которой ищется максимальное значение.

        Возвращает:
        Индекс максимального элемента в строке.
    """
    max_i = 0
    for i in range(0, len(row)-1):
        if row[i] > row[max_i]:
            max_i = i

    return max_i

def multiply_const_row(const, row):
    """
        Умножает все элементы строки на заданную константу.

        Аргументы:
        const: константа, на которую умножается строка.
        row: строка для умножения.

        Возвращает:
        Новый вектор, где каждый элемент строки умножен на константу.
    """
    mul_row = []
    for i in row:
        mul_row.append(const*i)
    return mul_row

def min_index(row):
    """
       Находит индекс минимального элемента в строке.

       Аргументы:
       row: строка, в которой ищется минимальное значение.

       Возвращает:
       Индекс минимального элемента в строке.
    """
    min_i = 0
    for i in range(0, len(row)):
        if row[min_i] > row[i]:
            min_i = i

    return min_i

