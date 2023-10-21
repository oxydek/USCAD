# Импортируем
import random
from tkinter import *
import tkinter as tk
from tkinter import messagebox
# import sys можно включить чтобы после копирования, программа сразу закрывалась

# Определение функции для генерации пароля
def generate_password():
    # Строки букв и цифр
    letters = "abcdefghijklmnopqrstuvwxyz"
    numbers = "0123456789"
    # Начальное значение пароля - пустая строка
    password = ""
    # Цикл генерации 8-ми символьного пароля
    for i in range(8):
        # Если символ порядковый номер меньше 2, то выбирается буква в верхнем регистре
        if i < 2:
            password += random.choice(letters).upper()
        # В противном случае выбирается символ из букв и цифр
        else:
            password += random.choice(letters + numbers)
    return password

root = Tk()
root.title("USСAD")
# Установить значок окна 
#root.iconbitmap('D:\Программирование\Переводчик\Пре версии\main.ico')
# Задание размеров окна и его минимального размера
root.geometry("465x670")
root.minsize(465, 670)
root.maxsize(465, 670)

# функция транслита
def transliterate(text):
    exceptions = {"ъ": "", "ь": ""}
    translit_table = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i", "й": "i", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch","ы": "y", "э": "e", "ю": "yu", "я": "ia"}
    result = ""
    for char in text:
        if char.lower() in exceptions:
            result += exceptions[char.lower()]
        elif char.lower() in translit_table:
            result += translit_table[char.lower()]
        else:
            result += char
    return result.lower()

# Определение функции для кнопки
def generate_info():
    # Получение значений из текстовых полей и флажков
    first_name = first_name_field.get().strip()
    last_name = last_name_field.get().strip()
    npt_checked = npt_var.get()
    wheil_checked = wheil_var.get()
    albacore_checked = albacore_var.get()


    email_firstpart = f"{transliterate(first_name[0].lower())}.{transliterate(last_name.lower())}"

    # Генерация пароля 
    password = generate_password() 

    output_field.delete('1.0', END) 
    output_field.insert('1.0', f"{last_name.capitalize()} {first_name.capitalize()}\n") 
    output_field.insert('end', transliterate(f"{first_name[0].lower()}.{last_name.lower()}\n")) 
    output_field.insert('end', (f"{password}\n\n"))


    
    # Генерация электронной почты в зависимости от состояния флажков
    if npt_checked:
        output_this_shit(email_firstpart + "@npt-c.ru", password)
    if wheil_checked:
        output_this_shit(email_firstpart + "@wheil.com", password)
    if albacore_checked:
        output_this_shit(email_firstpart + "@albacore.ru", password)

def output_this_shit(email, password):
    # Вывод информации в текстовое поле, переведенную на русский язык 
    output_field.insert('end', email + "\n")
    output_field.insert('end', (f"{password}\n\n")) 


# Добавление меток и текстовых полей
Label(root, text="Фамилия:", font=("Arial", 14)).grid(row=0, column=0, sticky=W, padx=10, pady=10)
last_name_field = Entry(root, font=("Arial", 14))
last_name_field.grid(row=0, column=1, padx=10, pady=10)
Label(root, text="Имя:", font=("Arial", 14)).grid(row=1, column=0, sticky=W, padx=10, pady=10)
first_name_field = Entry(root, font=("Arial", 14))
first_name_field.grid(row=1, column=1, padx=10, pady=10)
output_field = Text(root, font=("Arial", 14), height=15, width=40)
output_field.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

def copy_info():
    info = output_field.get("1.0", END)
    if info.strip() != "":
        root.clipboard_clear()
        root.clipboard_append(info)
        messagebox.showinfo("Скопировано", "Информация скопирована в буфер обмена!")
        # sys.exit()  можно включить чтобы после копирования, программа сразу закрывалась
    else:
        messagebox.showerror("Ошибка", "Сначала сгенерируйте информацию!")
        
Button(root, text="Копировать", command=copy_info, font=("Arial", 14), bg="#2196F3", fg="white").grid(row=3, column=0, sticky=W, padx=10, pady=10)


# Добавление кнопки для генерации информации
Button(root, text="Сгенерировать", command=generate_info, font=("Arial", 14), bg="#4CAF50", fg="white").grid(row=3, column=1, sticky=E, padx=10, pady=10)

# Логика галочек
npt_var = BooleanVar()
npt_checkbox = Checkbutton(root, text='npt-c.ru', font=("Arial", 14), variable=npt_var)
npt_checkbox.grid(row=4, column=0, sticky=W, padx=10, pady=10)

wheil_var = BooleanVar()
wheil_checkbox = Checkbutton(root, text='wheil.com', font=("Arial", 14), variable=wheil_var)
wheil_checkbox.grid(row=5, column=0, sticky=W, padx=10, pady=10)

albacore_var = BooleanVar()
albacore_checkbox = Checkbutton(root, text='albacore.ru', font=("Arial", 14), variable=albacore_var)
albacore_checkbox.grid(row=6, column=0, sticky=W, padx=10, pady=10)

# Обновление функции generate_info() для проверки состояния флажков и изменения домена почты

root.mainloop()

#⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⣧⡑⢄⡀⠀⠀⠀⠀⠀⠀⢀⡴⣪⠁⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⣽⡨⠆⠉⠊⠉⠀⠈⠉⠐⠉⠮⣰⡇⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⢠⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢃⠀⠀⠀⠀
#⠀⠀⠐⠠⠄⡀⡈⠀⠀⡰⠂⡄⠀⠀⠀⠀⡔⢢⡄⠀⠘⣀⡀⠤⠒
#⠀⠀⠠⠤⠤⠤⡯⢥⡆⠑⠛⠁⢀⣻⣃⡀⠙⠛⠁⣶⢭⡧⠤⠤⠤
#⠀⠀⢀⡠⠄⠒⠙⡅⠀⠀⠀⠀⠈⠉⠉⠀⠀⠀⠀⠀⡝⠁⠒⠠⠄
#⠀⠀⠀⠀⠀⠀⠀⡨⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢺⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⡰⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠱⡀⠀⠀⠀
#⠀⠀⠀⠀⠀⢰⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢡⠀⠀⠀
#⠀⠀⠀⠀⠀⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡆⠀⠀
#⢀⠖⠐⢢⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀
#⡆⠀⠀⠀⡄⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀
#⢡⠀⠀⠀⡇⢡⠀⠀⠰⡄⠀⠀⠀⠀⡀⠀⠀⠀⡆⠀⠀⢠⠓⡀⠀
#⠈⡄⠀⠀⠸⡀⠣⡀⠀⡇⠀⠀⠀⠀⡇⠀⠀⢠⠁⠀⡠⡇⠀⢡⠀
#⠀⠈⢄⠀⠀⠑⢄⠈⠢⢴⡀⠀⢠⠀⡇⠀⠀⣌⠠⠚⣡⠃⠀⣸⠀
#⠀⠀⠀⠳⣀⠀⠀⠑⠂⠤⢙⣛⡋⠉⢙⣣⣊⠀⠤⠊⠁⠀⡠⠃⠀
#⠀⠀⠀⠀⠀⠑⠠⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡠⠐⠁⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠒⠒⠂⠀⠀⠐⠒⠂⠉⠀⠀⠀⠀⠀⠀