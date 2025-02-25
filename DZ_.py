import pickle
from collections import UserDict
from datetime import datetime, timedelta

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Контакт не знайдено."
        except ValueError as e:
            return f"Помилка: {e}"
        except IndexError:
            return "Неправильна кількість аргументів."
    return inner

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    pass

class Phone(Field):
    def __init__(self, value):
        super().__init__(value)
        if not self.validate(value):
            raise ValueError("Телефонний номер має складатися з 10 цифр.")

    @staticmethod
    def validate(value):
        return value.isdigit() and len(value) == 10

class Birthday(Field):
    def __init__(self, value):
        super().__init__(value)
        try:
            self.value = datetime.strptime(value, '%d.%m.%Y').date()
        except ValueError:
            raise ValueError("Невірний формат дати. Використовуйте DD.MM.YYYY")

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        phone_obj = Phone(phone)
        self.phones.append(phone_obj)

    def remove_phone(self, phone):
        phone_obj = self.find_phone(phone)
        if phone_obj:
            self.phones.remove(phone_obj)
        else:
            raise ValueError(f"Телефон {phone} не знайдено у контакту {self.name.value}.")

    def edit_phone(self, old_phone, new_phone):
        old_phone_obj = self.find_phone(old_phone)
        if old_phone_obj:
            self.remove_phone(old_phone)
            self.add_phone(new_phone)
        else:
            raise ValueError(f"Телефон {old_phone} не знайдено у контакту {self.name.value}.")

    def find_phone(self, phone):
        for phone_obj in self.phones:
            if phone_obj.value == phone:
                return phone_obj
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def days_to_birthday(self):
        if self.birthday:
            today = datetime.today().date()
            next_birthday = datetime(today.year, self.birthday.value.month, self.birthday.value.day).date()
            if next_birthday < today:
                next_birthday = datetime(today.year + 1, self.birthday.value.month, self.birthday.value.day).date()
            return (next_birthday - today).days
        else:
            return None

    def __str__(self):
        phones = ', '.join(p.value for p in self.phones)
        birthday = self.birthday.value.strftime('%d.%m.%Y') if self.birthday else "Немає"
        return f"Ім'я: {self.name.value}, Телефони: {phones}, День народження: {birthday}"

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name, None)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
            raise KeyError(f"Запис з ім'ям {name} не знайдено.")

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming_birthdays = []
        for record in self.data.values():
            if record.birthday:
                next_birthday = datetime(today.year, record.birthday.value.month, record.birthday.value.day).date()
                if next_birthday < today:
                    next_birthday = datetime(today.year + 1, record.birthday.value.month, record.birthday.value.day).date()
                days_until = (next_birthday - today).days
                if days_until <= 7:
                    day_of_week = next_birthday.weekday()
                    if day_of_week >= 5:  # Якщо вихідний, переносимо на понеділок
                        next_birthday += timedelta(days=(7 - day_of_week))
                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "birthday": next_birthday.strftime('%d.%m.%Y')
                    })
        return upcoming_birthdays

    def __str__(self):
        if not self.data:
            return "Адресна книга порожня."
        result = ""
        for record in self.data.values():
            result += f"{record}\n"
        return result.strip()

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено

def parse_input(user_input):
    user_input = user_input.strip()
    if not user_input:
        return "", []
    parts = user_input.split()
    cmd = parts[0].lower()
    args = parts[1:]
    return cmd, args

@input_error
def add_contact(args, book: AddressBook):
    if len(args) < 2:
        raise ValueError("Введіть ім'я та номер телефону.")
    name = args[0]
    phone = args[1]
    record = book.find(name)
    message = "Контакт оновлено."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Контакт додано."
    record.add_phone(phone)
    return message

@input_error
def change_contact(args, book: AddressBook):
    if len(args) < 3:
        raise ValueError("Введіть ім'я, старий та новий номер телефону.")
    name = args[0]
    old_phone = args[1]
    new_phone = args[2]
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return f"Телефон для контакту {name} змінено."
    else:
        raise KeyError("Контакт не знайдено.")

@input_error
def show_phone(args, book: AddressBook):
    if len(args) < 1:
        raise ValueError("Введіть ім'я контакту.")
    name = args[0]
    record = book.find(name)
    if record:
        phones = ', '.join(p.value for p in record.phones)
        return f"Телефони контакту {name}: {phones}"
    else:
        raise KeyError("Контакт не знайдено.")

def show_all(args, book: AddressBook):
    return str(book)

@input_error
def add_birthday(args, book: AddressBook):
    if len(args) < 2:
        raise ValueError("Введіть ім'я та дату народження у форматі DD.MM.YYYY.")
    name = args[0]
    birthday = args[1]
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return f"День народження для контакту {name} додано/оновлено."
    else:
        raise KeyError("Контакт не знайдено.")

@input_error
def show_birthday(args, book: AddressBook):
    if len(args) < 1:
        raise ValueError("Введіть ім'я контакту.")
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        birthday = record.birthday.value.strftime('%d.%m.%Y')
        return f"День народження контакту {name}: {birthday}"
    else:
        return "Дата народження не встановлена."

def birthdays(args, book: AddressBook):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if not upcoming_birthdays:
        return "Немає днів народжень на наступний тиждень."
    result = "Дні народження на наступний тиждень:\n"
    for item in upcoming_birthdays:
        result += f"{item['name']}: {item['birthday']}\n"
    return result.strip()

def main():
    book = load_data()
    print("Ласкаво просимо до бота-помічника!")
    while True:
        user_input = input("Введіть команду: ")
        command, args = parse_input(user_input)
        if command in ["close", "exit"]:
            print("Good bye!")
            save_data(book)
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            response = add_contact(args, book)
            print(response)
        elif command == "change":
            response = change_contact(args, book)
            print(response)
        elif command == "phone":
            response = show_phone(args, book)
            print(response)
        elif command == "all":
            response = show_all(args, book)
            print(response)
        elif command == "add-birthday":
            response = add_birthday(args, book)
            print(response)
        elif command == "show-birthday":
            response = show_birthday(args, book)
            print(response)
        elif command == "birthdays":
            response = birthdays(args, book)
            print(response)
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()
