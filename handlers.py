# handlers.py
#TODO: триггеры для БД


#import asyncio
from aiogram import Bot, Dispatcher
from aiogram import Dispatcher, types
#rom aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.types import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from aiogram import F
import phonenumbers
from datetime import timedelta
#from datetime import datetime


from config import init_db
conn, cursor = init_db()
dp = Dispatcher()


# Машина состояний
class register(StatesGroup):
    reg = State()

    menu = State()
    choose_option = State()
    get_book = State()
    back = State()
    choose_back = State()
    book_filter = State()

    rbook_filter = State()
    rbook_create = State()
    bmenu = State()
    bselect_reader = State()
    bedit_data = State()

#----------------------------------------------------------------------
#Keybords
select_act = InlineKeyboardMarkup(inline_keyboard=[

    [
        InlineKeyboardButton(
            text="Получить книгу",
            callback_data="Получить книгу" # Отработано
        )
    ],
    [
        InlineKeyboardButton(
            text="Вернуть книгу", 
            callback_data="Вернуть книгу"
        )
    ],
    [
        InlineKeyboardButton(
            text="Связаться с библиотекарем",
            callback_data="Связь"
        )
    ]

])

double_select_act = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text="Библиотекарь",
            callback_data="Библиотекарь"
        )
    ],
    [
        InlineKeyboardButton(
            text="Читатель",
            callback_data="Читатель"
        )
    ],
    
])

getting_or_not = InlineKeyboardMarkup(inline_keyboard=[

    [
        InlineKeyboardButton(
            text="Беру!",
            callback_data="Беру"
        )
    ],
    [
        InlineKeyboardButton(
            text="Не то, поищем еще!",
            callback_data="Меню"
        )
    ]
])

choose_search_option = InlineKeyboardMarkup(inline_keyboard=[
        [
        InlineKeyboardButton(
            text="Поиск по названию книги",
            callback_data="name"
        )
    ],
    [
        InlineKeyboardButton(
            text="Поиск по автору книги",
            callback_data="autor"
        )
    ],
    [
        InlineKeyboardButton(
            text="Список доступной литературы",
            callback_data="list"
        )
    ],
])

bselect_act = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text="Редактировать читательский билет",
            callback_data="redit"
        )
    ],
    [
        InlineKeyboardButton(
            text="Редактировать книги",
            callback_data="redbook"
        )
    ],
    [
        InlineKeyboardButton(
            text="Просмотреть список взятых книг",
            callback_data="list_of_books"
        )
    ]  
])

bselect_redbook = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text="Добавить книгу",
            callback_data="create"
        )
    ],
    [
        InlineKeyboardButton(
            text="Удалить книгу",
            callback_data="delete"
        )
    ],     
])

###################### приоритетные обработчики ######################
@dp.message(Command("menu")) # команда возарата в начальное меню
async def command_menu(message: types.Message, state = FSMContext):
    #F.data = "menu"
    current_state = await state.get_state()
    print("Current state:", current_state)
    #user_id = callback.from_user.id
    #sql_query = f"""
    #                UPDATE "Книга"
    #                SET "Статус" = null, "Дата выдачи" = null
    #                WHERE "Номер читательского билета" = '{user_id}' AND "Статус" = 'Бронь';
    #            """
    #cursor.execute(sql_query)
    #conn.commit()
    #print(sql_query)"""
    await to_menu(message, state)


@dp.message(CommandStart()) # команда заруска или перезапуска бота
async def command_start_handler(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    check_sts = check_status(user_id)
    if check_sts == None:
        ans = "Мы не знакомы! Запускаем процесс регистрации читательского билета!"
        await message.answer(ans)
        ans = "Введите Ваше ФИО, возраст и номер мобильного телефона, разделив их запятыми:"
        await message.answer(ans)
        await state.set_state(register.reg)
    else:
        if check_sts[0] != None and check_sts[1] == None: # если в систему входит читатель
            ans = "Добрый день, " + str(check_sts[0])
            await message.answer(ans, reply_markup=select_act)
        elif check_sts[1] != None and check_sts[0] == None: # если в систему входит библиотекарь
            ans = "Добрый день, " + str(check_sts[1])
            await message.answer(ans, reply_markup=bselect_act)
            await state.set_state(register.bmenu)
        elif check_sts[1] != None and check_sts[0] != None: # если в системе входит библиотекарь, являющийся читателем
            ans = "Добрый день! Выберите, кто Вы сегодня."
            await message.answer(ans, reply_markup=double_select_act)
        else:
            ans = "Что-то пошло не так..."
            await message.answer(ans)

#------------------------------------------------------------------------
################ обработчики входа ##########################
@dp.callback_query(F.data == "Читатель")
async def reader(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Выберите дальнейшее действие", reply_markup=select_act)
    await state.set_state(register.menu)

@dp.callback_query(F.data == "Библиотекарь")
async def bibl(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Выберите дальнейшее действие", reply_markup=bselect_act)
    await state.set_state(register.bmenu)

#############################################################

################ обработчики главного меню ##########################
@dp.callback_query(F.data == "Получить книгу")
async def get_book(callback: types.CallbackQuery, state: FSMContext):
    sql_query = f"""SELECT count(*) FROM "Книга" 
                    WHERE "Номер читательского билета" = '{callback.message.chat.id}'"""
    cursor.execute(sql_query)
    if cursor.fetchone()[0] >= 3:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("Вы уже взяли максимум книг (3).", reply_markup=select_act)
        await state.set_state(register.menu)
    else:
        await callback.message.edit_reply_markup(reply_markup=None)
        await state.set_state(register.choose_option)
        await callback.message.answer("Выберете тип поиска", reply_markup=choose_search_option)

@dp.callback_query(F.data == "Вернуть книгу") # callback_data="Возвращаю" обработка возврата книги
async def back(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    user_id = callback.from_user.id
    sql_query = f"""
                    SELECT "Фондовый номер", "Автор", "Название", "Дата выдачи" FROM "Книга"
                    WHERE "Номер читательского билета" = '{user_id}' AND ("Статус" = 'Взята' OR "Статус" = 'Бронь')
                    ORDER BY "Дата выдачи" ASC;
                """
    cursor.execute(sql_query)
    bookd_books = cursor.fetchall()
    formatted_result = []
    nums = []
    for row in bookd_books:
        num, author, title, issue_date = row
        # Преобразуем timestamp в объект datetime
        issue_date = issue_date + timedelta(hours=3)  # Если есть смещение часового пояса, уточните его
        
        # Рассчитываем срок сдачи (Дата выдачи + 7 суток)
        due_date = issue_date + timedelta(days=7)
        nums.append(num)
        # Форматируем результат
        formatted_result.append(f"{author}, {title}. Срок сдачи: {due_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if len(formatted_result) == 0:
        await callback.message.answer("Вы ещё не взяли ни одной книги!", reply_markup=select_act)
        await state.set_state(register.menu)

    else:
        inline_keyboard = [
                            [InlineKeyboardButton(text=f"{index + 1}. {text}", callback_data="id=" + str(nums[index]))]
                            for index, text in enumerate(formatted_result)
                        ]
        inline_keyboard.append([InlineKeyboardButton(text = "> В меню", callback_data="Меню")])
                         
        # Создаем инлайн клавиатуру
        getting_or_not = InlineKeyboardMarkup(inline_keyboard=inline_keyboard, row_width=1)    
        await callback.message.answer("Вот список ваших книг:", reply_markup=getting_or_not)
        await state.set_state(register.back)

@dp.callback_query(F.data == "Связь")
async def contact(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=None)
    sql_query = f"""
SELECT "Ник" 
FROM 
"Читательский билет" INNER JOIN "Библиотекарь" 
ON "Читательский билет"."Внутренний номер библиотекаря" = "Библиотекарь"."Внутренний номер библиотекаря"
WHERE "Читательский билет"."Номер" = '{callback.message.chat.id}';
 """
    cursor.execute(sql_query)
    result = cursor.fetchall()
    if result is None:
        await callback.message.answer("Вы ещё не зарегистрированы", reply_markup=select_act)
    else:
        await callback.message.answer("За вас отвечает наша крыса: " + str(result[0][0])+ "\nСвяжитесь с ней!", reply_markup=select_act)

#####################################################################


################ обработчики поиска ###################################
@dp.callback_query(F.data == "name") # поиск по названию
async def get_book(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Введите название книги")
    await state.set_state(register.get_book)

@dp.callback_query(F.data == "autor") # поиск по автору
async def get_book(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Введите имя автора")
    await state.set_state(register.get_book)

@dp.callback_query(F.data == "list") # список книг
async def list_of_books_filter(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Введите буквы для алфавитного поиска (по названию книги) или диапазон букв через тире (например, ав-ту).\nДля вывода всех книг можете ввести * или 0-я")
    await state.set_state(register.book_filter)

@dp.message(register.book_filter) # получаем список книг в виде фильтрованного списка
@dp.message(register.rbook_filter)
async def list_of_books(message: types.Message, state = FSMContext):
    filter_ = True
    key = "getid="
    current_state = await state.get_state()
    print("Current state:", current_state)


    if current_state  == register.rbook_filter: # если функция используется для удаления книг
        #print("rbook")
        key = "delid="
        filter_ = False
    else: # если функция используется для получения книг
        key = "getid="    
    #print(message.text)
    if "-" in message.text:
        parts = message.text.split('-')
        results = find_books(parts, filter_)
        print(results)
    elif message.text == '*':
        results = find_books('', filter_)
    else:
        results = find_books([message.text, message.text], filter_)

    if len(results) > 0:
        formatted_result = []
        nums = []
        for row in results:
            author, title, num = row
            # Форматируем результат
            nums.append(num ) 
            formatted_result.append(f"{title}, {author}")
        inline_keyboard = [
                            [InlineKeyboardButton(text=f"{index + 1}. {text}", callback_data=key + str(nums[index]))]
                            for index, text in enumerate(formatted_result)
                        ]
        inline_keyboard.append([InlineKeyboardButton(text = "> В меню", callback_data="Меню")])      
        # Создаем инлайн клавиатуру
        getting_or_not = InlineKeyboardMarkup(inline_keyboard=inline_keyboard, row_width=1)
        await message.answer("Список доступной литературы:", reply_markup=getting_or_not)
        
    else:
        if current_state  == register.rbook_filter:
            await message.answer("Ничего не найдено", reply_markup=bselect_act)
        else:
            await message.answer("Ничего не найдено", reply_markup=select_act)

    if current_state  == register.rbook_filter:
        await state.set_state(register.bmenu)
    else:
        await state.set_state(register.menu)
#######################################################################

################ обработчики меню библиотекаря ###################################
@dp.callback_query(F.data == "redit")
async def redit(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Введите фильтр для поиска пользователя по ФИО. \nЭто может быть часть имени/фамилии/отчетсва или диапазон букв для алфавитного поиска (например, ав-ту)")
    await state.set_state(register.bselect_reader)

@dp.callback_query(F.data == "redbook")
async def redit(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=bselect_redbook)

@dp.callback_query(F.data == "list_of_books") ####################################################
async def list_of_books(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=None)
    sql_query = f"""
SELECT "Читательский билет"."Номер", "Читательский билет"."ФИО читателя", "Читательский билет"."Телефон", 
"Книга"."Название", "Книга"."Автор", "Книга"."Фондовый номер", "Книга"."Дата выдачи"
FROM 
"Читательский билет" INNER JOIN "Книга" ON "Читательский билет"."Номер" = "Книга"."Номер читательского билета"
ORDER BY "Читательский билет"."Номер" ASC
                """
    cursor.execute(sql_query)
    results = cursor.fetchall()
    if not results:
        await callback.message.answer("В базе данных нет ни одной взятой книги", reply_markup=bselect_act)
    else:
        result_list = []
        current_user = None

        for row in results:
            ticket_number = row[0]
            fio = row[1]
            phone = row[2]
            stamp = row[6]
            formatted_date_time = stamp.strftime("%d.%m.%Y %H:%M")
            book_info = f'{row[4]}, "{row[3]}" ({row[5]})\n    Дата выдачи: {formatted_date_time}'
            
            if current_user is None or current_user["ticket_number"] != ticket_number:
                if current_user is not None:
                    result_list.append(current_user)
                current_user = {"ticket_number": ticket_number, "fio": fio, "phone": phone, "books": []}


            current_user["books"].append(book_info)

        # Добавляем последнего пользователя в список
        if current_user is not None:
            result_list.append(current_user)
        # Формирование массива строк вывода
        output_list = []
        for user in result_list:
            user_info = f"{user['fio']}, {user['phone']}"
            
            # books_info должен быть строкой, а не списком
            books_info = "\n".join([f"{i + 1}.    " + user["books"][i] for i in range(len(user["books"]))])
            
            output_list.append(f"{user_info}\n{books_info}\n")

        # Вывод результата
        for output in output_list:
            print(output)

        for i in range(len(output_list) - 1):
            await callback.message.answer(output_list[i])
        await callback.message.answer(output_list[-1], reply_markup=bselect_act)

        """inline_keyboard = [
                            [InlineKeyboardButton(text=f"{index + 1}. {text}", callback_data="getid=" + str(nums[index]))]
                            for index, text in enumerate(formatted_result)
                        ]
        inline_keyboard.append([InlineKeyboardButton(text = "> В меню", callback_data="Меню")])      
        # Создаем инлайн клавиатуру
        getting_or_not = InlineKeyboardMarkup(inline_keyboard=inline_keyboard, row_width=1)
        await callback.message.answer("Список доступной литературы:", reply_markup=getting_or_not)"""
##################################################################################


################ обработчики редактирования списка книг ########################################
@dp.callback_query(F.data == "delete")
async def delete(callback: types.CallbackQuery, state = FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Введите буквы для алфавитного поиска (по названию книги) или диапазон букв через тире (например, ав-ту).\nДля вывода всех книг можете ввести * или 0-я")
    await state.set_state(register.rbook_filter)
    #await callback.message.answer("Что хотите удалить?", reply_markup=bselect_redbook)

@dp.callback_query(F.data == "create")
async def create(callback: types.CallbackQuery, state = FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Введите через запятую данные для книги:\nНазвание, Автора, Год издания, Страну издания, УДК, ББК, Фондовый номер")
    await state.set_state(register.rbook_create)
################################################################################################


################## редактирования читательского билета #########################################
@dp.message(register.bselect_reader)
async def rbook_create(message: types.Message, state = FSMContext):
    if len(message.text) < 6 and "-" in message.text:
        # обрабатываем алфавитный фильтр
        bounds = message.text.split("-")
        if len(bounds) != 2:
            await message.answer("Вы использовали больше одного диапазона", reply_markup=bselect_act)
            await state.set_state(register.bmenu)
        else:
            results = find_user(bounds)
    else:
        results = find_user([message.text])
    if len(results) < 1:
        await message.answer("К сожалению, у нас такого читателя нет. Попробуйте ещё раз!", reply_markup=bselect_act)
        await state.set_state(register.bmenu)
    else:
        formatted_result = []
        nums = []
        for row in results:
            num, name, phone = row
            # Форматируем результат
            nums.append(num) 
            formatted_result.append(f"{name}, {phone}")
        

        inline_keyboard = [
                            [InlineKeyboardButton(text=f"{index + 1}. {text}", callback_data="usrid=" + str(nums[index]))]
                            for index, text in enumerate(formatted_result)
                        ]
        inline_keyboard.append([InlineKeyboardButton(text = "> В меню", callback_data="Меню")])
                    
        # Создаем инлайн клавиатуру
        getting_or_not = InlineKeyboardMarkup(inline_keyboard=inline_keyboard, row_width=1)    
        await message.answer("У нас зарегистированы следующие читатели, удовлетворяющие вашему запросу:", reply_markup=getting_or_not)
        await state.set_state(register.bmenu)

@dp.callback_query(F.data.startswith("usrid="))
async def edit_user(callback: types.CallbackQuery, state = FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    user_id = callback.data[6:]
    await callback.message.answer("id пользователя в базе: " + user_id)
    await callback.message.answer("Введите через запятую данные для читательского билета: текущий id пользователя в базе (см. предыдущее сообщение),\nФИО, Возраст, Телефон")
    await state.set_state(register.bedit_data)

@dp.message(register.bedit_data)
async def edit_user_push(message: types.Message, state = FSMContext):
    data = message.text.split(", ")
    if len(data) != 4:
        await message.answer("Вы ввели некорректные данные. Повторим попытку", reply_markup=bselect_act)
        await state.set_state(register.bedit_data)
    else:
        id, name, age, phone = data
        ans = data_check([name, age, phone])
        if ans[0] != "E":
            try:
                sql_query = f"""
                                UPDATE "Читательский билет"
                                SET "ФИО читателя" = '{name}', "Возраст" = '{age}', "Телефон" = '{phone}'
                                WHERE "Номер" = '{id}'
                                RETURNING *
                                ;
                            """
                cursor.execute(sql_query)
                conn.commit()
                updated_row = cursor.fetchone()
                if updated_row is None or len(updated_row) < 1:
                    raise Exception
                await message.answer("Читательский билет успешно обновлен", reply_markup=bselect_act)
                await state.set_state(register.bmenu)
            except:
                await message.answer("Вы ввели неверный id. Попробуйте еще раз")
                await state.set_state(register.bedit_data)
        else:
            await message.answer(ans)
            await state.set_state(register.bedit_data)
def find_user(bounds):
    if len(bounds) == 1:
        sql_query = f"""
                        SELECT "Номер", "ФИО читателя", "Телефон"
                        FROM "Читательский билет"
                        WHERE 
                            LOWER("ФИО читателя") ILIKE '%{bounds[0]}%'
                        ORDER BY "ФИО читателя";
                    """
    elif len(bounds) == 2:
        low, high = bounds
        sql_query = f"""
                        SELECT "Номер", "ФИО читателя", "Телефон"
                        FROM "Читательский билет"
                        WHERE 
                            LOWER("ФИО читателя") BETWEEN LOWER('{low}%') AND LOWER('{high}%')
                            OR LOWER("ФИО читателя") ILIKE '{high}%'
                            OR LOWER("ФИО читателя") ILIKE '{low}%'
                        ORDER BY "ФИО читателя";
                    """
    else:
        return []
    print(sql_query)
    cursor.execute(sql_query)
    return cursor.fetchall()

################################################################################################
    


################ обработчики создания списка книг ##############################################
@dp.message(register.rbook_create)
async def list_of_books(message: types.Message, state = FSMContext):
    data = message.text.split(", ")
    if len(data) != 7:
        await message.answer("Вероятно, данные введены некорректно. Попробуем еще разок:")
    else:
        try:
            name, author, year, country, udk, bbk, fund_number = [str(i) for i in data]
            print(name, author, year, country, udk, bbk, fund_number)
            if name == "" or author == "" or year == "" or udk == "" or bbk == "" or fund_number == "":
                await message.answer("Некорректные данные. Повторите попытку")
            elif int(year) < 0:
                await message.answer("Некорректный год. Повторите попытку")
            
            sql_query = """
                        INSERT INTO "Книга" ("Название", "Автор", "Год издания и страна издания", "УДК", "ББК", "Фондовый номер", "Внутренний номер библиотекаря")
                        VALUES (%s, %s, %s, %s, %s, %s, %s);
                        """
            try:
                print(sql_query)

                cursor.execute(sql_query, (name, author, str(year) + ", " + str(country), udk, bbk, int(fund_number), message.from_user.id))
                conn.commit()
                await message.answer("Книга успешно добавлена", reply_markup=bselect_act)
                await state.set_state(register.bmenu)
            except:
                await message.answer("Некорректные данные. Вероятно, неуникальный фондовый номер.\nПовторите попытку")
        except:
            await message.answer("Некорректные данные. Повторите попытку")

def find_books(text, filter_ = True):    
    if filter_ == True:
        command = "AND \"Статус\" IS NULL"
    else:
        command = ""
    """
                    SELECT *
                    FROM "Книга"
                    WHERE (
                    CHAR_LENGTH("Автор") >= 0 AND "Автор" ILIKE '%{autor}%'
                    )
                    AND (
                    CHAR_LENGTH("Название") >= 0 AND "Название" ILIKE '%{book}%'
                    )
                    AND "Статус" IS NULL
                """
    if isinstance(text, str):
        sql_query = f"""
                        SELECT "Автор", "Название", MIN("Фондовый номер") AS "Первый Фондовый номер"
                        FROM "Книга"
                        WHERE 
                        ((CHAR_LENGTH("Название") >= 0 AND "Название" ILIKE '%{text}%')
                        OR (CHAR_LENGTH("Автор") >= 0 AND "Автор" ILIKE '%{text}%'))
                        {command}
                        GROUP BY "Автор", "Название"
                        ORDER BY "Название";
                    """
    else:
        low = text[0]
        high = text[1]
        sql_query = f"""
                        SELECT "Автор", "Название", MIN("Фондовый номер") AS "Первый Фондовый номер"
                        FROM "Книга"
                        WHERE 
                            (LOWER("Название") BETWEEN LOWER('{low}%') AND LOWER('{high}%')
                            AND "Статус" IS NULL)
                            OR (LOWER("Название") ILIKE '{high}%')
                            OR (LOWER("Название") ILIKE '{low}')
                        GROUP BY "Автор", "Название"
                        ORDER BY "Название";
                    """
    print(sql_query)
    try:
        cursor.execute(sql_query)
    except:
        print("02: error")
        return []
    cursor.execute(sql_query)
    return cursor.fetchall()

@dp.message(register.get_book) # callback_data="Получить книгу" обработка сообщения
async def name(message: types.Message, state = FSMContext):
    user_id = message.from_user.id
    check_sts = check_status(user_id)
    if check_sts == None:
        ans = "Мы не знакомы! Запускаем процесс регистрации читательского билета!"
        await message.answer(ans)
        ans = "Введите ваше ФИО, возраст и номер мобильного телефона, разделив их запятыми:"
        await message.answer(ans)
        await state.set_state(register.reg)
    else:
        results = find_books(message.text)
        if len(results) == 0:
            await message.answer("К сожалению, у нас такой книги нет🥺 Попробуйте ещё раз!", reply_markup=select_act)
            await state.set_state(register.menu)
        else:
  ########################################################## 
            formatted_result = []
            nums = []
            for row in results:
                author, title, num = row
                # Форматируем результат
                nums.append(num ) 
                formatted_result.append(f"{author}, {title}")
            


            inline_keyboard = [
                                [InlineKeyboardButton(text=f"{index + 1}. {text}", callback_data="getid=" + str(nums[index]))]
                                for index, text in enumerate(formatted_result)
                            ]
            inline_keyboard.append([InlineKeyboardButton(text = "> В меню", callback_data="Меню")])
                            
            # Создаем инлайн клавиатуру
            getting_or_not = InlineKeyboardMarkup(inline_keyboard=inline_keyboard, row_width=1)    
            await message.answer("У нас есть следующие книги, соответствующие вашему запросу:", reply_markup=getting_or_not)
            await state.set_state(register.menu)

###########################################################################################
@dp.callback_query(F.data == "Меню") # callback_data="Меню" возвращение в меню
async def menu(callback: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    print("Current state:", current_state)
    await callback.message.edit_reply_markup(reply_markup=None)
    await to_menu(callback.message, state)

    #user_id = callback.from_user.id
    #sql_query = f"""
    #                UPDATE "Книга"
    #                SET "Статус" = null, "Дата выдачи" = null
    #                WHERE "Номер читательского билета" = '{user_id}' AND "Статус" = 'Бронь';
    #            """
    #cursor.execute(sql_query)
    #conn.commit()
    #print(sql_query)"""
    '''if current_state == register.rbook_filter or current_state == register.bmenu or current_state == register.rbook_create:
            await callback.message.answer("Выберите действие", reply_markup=bselect_act)
            await state.set_state(register.bmenu)

    else:
        await callback.message.answer("Выберите действие", reply_markup=select_act)
        await state.set_state(register.menu)'''


async def to_menu(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state in [register.rbook_filter, register.bmenu, register.rbook_create, register.bselect_reader, register.bedit_data]:
            await message.answer("Выберите действие", reply_markup=bselect_act)
            await state.set_state(register.bmenu)

    else:
        await message.answer("Выберите действие", reply_markup=select_act)
        await state.set_state(register.menu)    


@dp.callback_query(F.data.startswith('getid=')) # callback_data="Беру" обработка взятия книги
async def take(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    num = callback.data[6:]
    user_id = callback.from_user.id

    check_query = f"""
                    SELECT "Статус" FROM "Книга"
                    WHERE "Фондовый номер" = '{num}'
                    """
    cursor.execute(check_query)
    results = cursor.fetchall()
    if results[0][0] == 'Взята':
        await callback.message.answer("Какая-то мышь вас уже опередила. \nПопробуйте ещё раз, может быть мы найдем еще одну копию :(", reply_markup=select_act)
        await state.set_state(register.menu)
    else:
        sql_query = f"""
                        UPDATE "Книга"
                        SET "Статус" = 'Взята', "Дата выдачи" = CURRENT_TIMESTAMP, "Номер читательского билета" = '{user_id}'
                        WHERE "Фондовый номер" = '{num}';
                    """
        cursor.execute(sql_query)
        conn.commit()
        print(sql_query)
        await callback.message.answer("Книга успешно записана Вам в билет, приятного чтения📖", reply_markup=select_act)
        await state.set_state(register.menu)
######################################################################

@dp.callback_query(F.data.startswith('delid=')) # обработка выбора книги для удаления библиотекарем
async def delete(callback: types.CallbackQuery, state: FSMContext):
    num = callback.data[6:]
    sql_query = f"""
                    SELECT "Фондовый номер", "Автор", "Название"
                    FROM "Книга"
                    WHERE 
                    ("Название", "Автор") = (
                        SELECT "Название", "Автор"
                        FROM "Книга"
                        WHERE "Фондовый номер" = '{num}'
                        ORDER BY "Название" DESC, "Автор" DESC
                    )
                """
    cursor.execute(sql_query)
    results = cursor.fetchall()
    formatted_result = []
    nums = []
    for row in results:
        num, author, title = row
        # Форматируем результат
        nums.append(num ) 
        formatted_result.append(f"{num}, {author}, {title}")
    inline_keyboard = [
                        [InlineKeyboardButton(text=f"{index + 1}. {text}", callback_data="bokid=" + str(nums[index]))]
                        for index, text in enumerate(formatted_result)
                    ]
    inline_keyboard.append([InlineKeyboardButton(text = "> В меню", callback_data="Меню")])      
    # Создаем инлайн клавиатуру
    todel = InlineKeyboardMarkup(inline_keyboard=inline_keyboard, row_width=1)
    print("Dfghjs")
    await callback.message.edit_reply_markup(reply_markup=todel)

    #await callback.message.answer("Выберете экземпляр, который следует изъять из архива", reply_markup=select_act)
    #await state.set_state(register.bmenu)

@dp.callback_query(F.data.startswith('bokid=')) # обработка удаления книги 
async def delete_book_by_id(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    print(callback.data)
    num = callback.data[6:]
    
    sql_query = f"""
                DELETE FROM "Книга"
                WHERE "Фондовый номер" = '{num}' AND "Номер читательского билета" IS NULL;

                SELECT "Читательский билет"."ФИО читателя", "Читательский билет"."Телефон", "Книга"."Дата выдачи"
                FROM "Книга"
                LEFT JOIN "Читательский билет" ON "Книга"."Номер читательского билета" = "Читательский билет"."Номер"
                WHERE "Книга"."Фондовый номер" = '{num}' AND "Книга"."Номер читательского билета" IS NOT NULL
                LIMIT(1);
                """
    cursor.execute(sql_query)
    conn.commit()
    result = cursor.fetchall()
    print(sql_query)
    if len(result) < 1:
        await callback.message.answer("Книга успешно удалена из архива", reply_markup=bselect_act)
        await state.set_state(register.bmenu)
    else:
        name = result[0][0]
        phone = result[0][1]
        date = result[0][2]
        await callback.message.answer("Эта книга сейчас на руках у читателя. Обратитесь к нему для возврата.\nИмя читателя: " + name + "\nТелефон: " + phone + "\nДата выдачи: " + str(date.strftime('%d.%m.%Y')) + "\n", reply_markup=bselect_act)
        await state.set_state(register.bmenu)


# Оборабтка возврата книги
@dp.callback_query(F.data.startswith('id=')) # callback_data - номер книги для возврата
async def return_book(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    print(callback.data)
    num = callback.data[3:]
    user_id = callback.from_user.id
    sql_query = f"""
                    UPDATE "Книга"
                    SET "Статус" = null, "Дата выдачи" = null, "Номер читательского билета" = null
                    WHERE "Номер читательского билета" = '{user_id}' AND "Фондовый номер" = '{num}';
                """
    cursor.execute(sql_query)
    conn.commit()
    print(sql_query)
    await callback.message.answer("Книга успешно возвращена", reply_markup=select_act)
    await state.set_state(register.menu)



#--------------------- Сторонние функции ----------------------------------------№
@dp.message(register.reg) # регистрация
async def name(message: types.Message, state = FSMContext):
    user_data  = str(message.text)
    user_data = user_data.split(', ')
    check_res = data_check(user_data)
    if(check_res[0] != 'E'):
        full_name, age, phone_number = map(str.strip, user_data)
        print("Данные введены корректно:")
        print(f"ФИО: {full_name}")
        print(f"Возраст: {age}")
        print(f"Номер телефона: {phone_number}")
        query = f"INSERT INTO \"Читательский билет\" VALUES ('{message.from_user.id}', '{full_name}', {age}, '{str(phone_number)}');"
        cursor.execute(query)
        conn.commit()
        await message.answer(check_res, reply_markup=select_act)
    else:
        await message.answer(check_res)
        await state.set_state(register.reg)

def data_check(user_data):
    ans = ""
    if len(user_data) == 3:
        full_name, age, phone_number = map(str.strip, user_data)
        # Проверка корректности возраста
        try:
            age = int(age)
            if not 0 < age < 150:
                raise ValueError("Некорректный возраст")
        except ValueError:
            ans = "Ошибка: Возраст должен быть целым числом от 1 до 149.\nПробуем еще раз!"
            #await message.answer(ans)
            #await state.set_state(register.reg)
            return "E1: " + ans
        # Проверка корректности номера телефона для РФ
        try:
            parsed_phone = phonenumbers.parse(phone_number, "RU")
            if not phonenumbers.is_valid_number(parsed_phone):
                ans = "Некорректный номер телефона для РФ\nПробуем еще раз!"
                return "E2: " + ans
        except:
            ans = "Ошибка: Некорректный формат номера телефона для РФ.\nПробуем еще раз!"
            return "E3: " + ans
        ans = "Вы успешно зарегистрированы!"
        return ans
    else:
        ans = "Ошибка ввода. Введите ФИО, возраст и номер телефона, разделив их запятыми.\nПробуем еще раз!"
        return "E4: " + ans

@dp.message() # временная заглушка, удаляет весь спам, летящий в бота
async def echo_handler(message: types.Message) -> None:
    try:
        await message.delete()
    except TypeError:
        await message.answer("Error occurred. Please, try it again.")

def check_status(user_id):
    sql_query = """
    SELECT "Читательский билет"."ФИО читателя", "Библиотекарь"."ФИО"
    FROM "Читательский билет"
    LEFT JOIN "Библиотекарь" ON "Читательский билет"."Номер" = "Библиотекарь"."Внутренний номер библиотекаря"
    WHERE "Читательский билет"."Номер" = %s OR "Библиотекарь"."Внутренний номер библиотекаря" = %s;
    """
    # Значения для параметров
    user_id_str = str(user_id)
    # Выполнение запроса с передачей параметров
    cursor.execute(sql_query, (user_id_str, user_id_str))
    # Получение результатов
    results = cursor.fetchall()
    if len(results) > 0:
        return results[0]
    else:
        return None