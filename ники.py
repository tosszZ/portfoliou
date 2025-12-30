import os

def get_next_number(filename):
    """Получает следующий номер для нового ника"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        max_number = 0

        for line in lines:
            line = line.strip()
            if line and line[0].isdigit() and '.' in line:
                parts = line.split('.', 1)
                if parts[0].strip().isdigit():
                    number = int(parts[0].strip())
                    if number > max_number:
                        max_number = number

        return max_number + 1

    except (FileNotFoundError, ValueError):
        return 1

def add_nickname(filename, nick):
    """Добавляет новый ник в файл с автоматической нумерацией"""
    try:
        next_number = get_next_number(filename)
        new_line = f"{next_number}. {nick}\n"

        with open(filename, 'a', encoding='utf-8') as f:
            f.write(new_line)

        print(f"✅ Ник добавлен в файл как: {new_line.strip()}")
        return True

    except Exception as e:
        print(f"❌ Ошибка при добавлении ника: {e}")
        return False


def remove_nickname(filename):
    """Удаляет конкретный ник из файла с перенумерацией"""
    try:
        if not os.path.exists(filename):
            print("📁 Файл не существует.")
            return False

        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if not lines:
            print("📄 Файл пуст.")
            return False

        # Показываем все ники с номерами
        print("\n" + "=" * 50)
        print("СПИСОК НИКОВ ДЛЯ УДАЛЕНИЯ:")
        print("=" * 50)

        numbered_nicks = []
        for line in lines:
            line = line.strip()
            if line:
                print(f"  {line}")
                if line[0].isdigit() and '.' in line:
                    parts = line.split('.', 1)
                    if len(parts) == 2:
                        numbered_nicks.append({
                            'full_line': line,
                            'number': parts[0].strip(),
                            'nick': parts[1].strip()
                        })

        if not numbered_nicks:
            print("❌ В файле нет нумерованных ников для удаления.")
            return False

        print("=" * 50)
        print("\nВы можете удалить ник:")
        print("1. По номеру (например: 1)")
        print("2. По имени (например: PlayerOne)")
        print("3. Отмена")

        choice = input("\nВыберите способ удаления (1-3): ").strip()

        if choice == '3':
            print("❌ Удаление отменено.")
            return False

        nick_to_remove = None
        removed_item = None

        if choice == '1':
            # Удаление по номеру
            try:
                num_to_remove = input("Введите номер для удаления: ").strip()
                for item in numbered_nicks:
                    if item['number'] == num_to_remove:
                        nick_to_remove = item['nick']
                        removed_item = item
                        break
                if not nick_to_remove:
                    print(f"❌ Ник с номером {num_to_remove} не найден.")
                    return False
            except ValueError:
                print("❌ Неверный номер.")
                return False

        elif choice == '2':
            # Удаление по имени
            nick_input = input("Введите ник для удаления: ").strip()
            for item in numbered_nicks:
                if item['nick'].lower() == nick_input.lower():
                    nick_to_remove = item['nick']
                    removed_item = item
                    break
            if not nick_to_remove:
                print(f"❌ Ник '{nick_input}' не найден.")
                return False
        else:
            print("❌ Неверный выбор.")
            return False

        # Подтверждение удаления
        confirm = input(f"\n⚠️  Вы уверены, что хотите удалить '{nick_to_remove}'? (да/нет): ").strip().lower()
        if confirm not in ['да', 'yes', 'y', 'д']:
            print("❌ Удаление отменено.")
            return False

        # Удаляем выбранный элемент и перезаписываем файл с перенумерацией
        new_lines = []
        current_number = 1

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Пропускаем строку, которую нужно удалить
            if line == removed_item['full_line']:
                print(f"🚫 Удаляю: {line}")
                continue

            # Переписываем строки с новой нумерацией
            if line[0].isdigit() and '.' in line:
                parts = line.split('.', 1)
                if len(parts) == 2:
                    old_number = parts[0].strip()
                    nick = parts[1].strip()
                    new_line = f"{current_number}. {nick}"
                    new_lines.append(new_line)
                    current_number += 1
            else:
                # Сохраняем строки без номеров как есть
                new_lines.append(line)

        # Записываем обновленный список обратно в файл
        with open(filename, 'w', encoding='utf-8') as f:
            for line in new_lines:
                f.write(line + '\n')

        print(f"✅ Ник '{nick_to_remove}' успешно удален.")
        print(f"📊 Удалено записей: 1, Осталось записей: {len(new_lines)}")
        return True

    except Exception as e:
        print(f"❌ Ошибка при удалении: {e}")
        return False


def find_nickname(filename, nick, show_all=False):
    """Ищет ник в файле и возвращает информацию о нем"""
    try:
        if not os.path.exists(filename):
            return None

        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        found_items = []

        for line_num, line in enumerate(lines, 1):
            clean_line = line.strip()

            if not clean_line:
                continue

            # Проверяем нумерованные строки
            if clean_line[0].isdigit() and '.' in clean_line:
                parts = clean_line.split('.', 1)
                if len(parts) == 2:
                    current_nick = parts[1].strip()
                    current_number = parts[0].strip()

                    # Если не show_all, ищем конкретный ник
                    if not show_all:
                        if current_nick.lower() == nick.lower():
                            found_items.append({
                                'line_num': line_num,
                                'full_line': clean_line,
                                'number': current_number,
                                'nick': current_nick,
                                'exact_match': current_nick == nick
                            })
                    else:
                        # Для show_all добавляем все
                        found_items.append({
                            'line_num': line_num,
                            'full_line': clean_line,
                            'number': current_number,
                            'nick': current_nick,
                            'exact_match': True
                        })

            # Проверяем строки без номеров (только если не show_all)
            elif not show_all:
                if clean_line.lower() == nick.lower():
                    found_items.append({
                        'line_num': line_num,
                        'full_line': clean_line,
                        'number': None,
                        'nick': clean_line,
                        'exact_match': clean_line == nick
                    })

        return found_items if found_items else None

    except Exception as e:
        print(f"❌ Ошибка при поиске: {e}")
        return None


def check_and_add_nickname():
    """Основная функция для проверки и добавления ника"""

    nick = input("Введи ник --> ").strip()

    if not nick:
        print("❌ Ошибка: Вы не ввели ник!")
        return False

    filename = 'D:\\МОНТАЖ\\ники.txt'

    try:
        if not os.path.exists(filename):
            print("ℹ️ Файл не существует. Будет создан новый.")
            with open(filename, 'w', encoding='utf-8') as f:
                pass

        found_items = find_nickname(filename, nick)

        print(f"\nИщем ник: '{nick}'")
        print("=" * 50)

        if found_items:
            for item in found_items:
                match_type = "точное совпадение" if item['exact_match'] else "совпадение без учета регистра"
                print(f"✓ Найден ({match_type}) в строке {item['line_num']}: {item['full_line']}")

            print("=" * 50)
            print(f'✅ Ник уже есть в списке!')
            if len(found_items) == 1:
                print(f'   Строка #{found_items[0]["line_num"]}: {found_items[0]["full_line"]}')
            else:
                print(f'   Найдено {len(found_items)} совпадений')
            return True
        else:
            print("❌ Ник не найден в списке.")
            print("=" * 50)

            add_choice = input(f"\nДобавить ник '{nick}' в список? (да/нет): ").strip().lower()

            if add_choice in ['да', 'yes', 'y', 'д']:
                return add_nickname(filename, nick)
            else:
                print("❌ Ник не добавлен.")
                return False

    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")
        return False


def show_all_nicks():
    """Показывает все ники из файла"""
    filename = 'D:\\МОНТАЖ\\ники.txt'

    try:
        if not os.path.exists(filename):
            print("📁 Файл еще не создан.")
            return

        found_items = find_nickname(filename, "", show_all=True)

        if not found_items:
            print("📄 Файл пуст или не содержит нумерованных ников.")
            return

        print("\n" + "=" * 50)
        print("ВСЕ НИКИ В СПИСКЕ:")
        print("=" * 50)

        total_count = len(found_items)

        for item in found_items:
            print(f"{item['line_num']:3}. {item['full_line']}")

        print("=" * 50)
        print(f"Всего ников: {total_count}")
        print("=" * 50)

    except Exception as e:
        print(f"❌ Ошибка при чтении файла: {e}")


def main_menu():
    """Главное меню программы"""
    print("\n" + "=" * 50)
    print("ПРОГРАММА ДЛЯ УПРАВЛЕНИЯ СПИСКОМ НИКОВ")
    print("=" * 50)
    print("1. Проверить/добавить ник")
    print("2. Показать все ники")
    print("3. Удалить ник")
    print("4. Выход")
    print("=" * 50)

    return input("Выберите действие (1-4): ").strip()


# Главная часть программы
if __name__ == "__main__":
    print("🎮 ПРОГРАММА ДЛЯ РАБОТЫ СО СПИСКОМ НИКОВ")
    print("Проверка, добавление и удаление с автоматической нумерацией")

    while True:
        choice = main_menu()

        if choice == '1':
            print("\n" + "=" * 50)
            print("ПРОВЕРКА И ДОБАВЛЕНИЕ НИКА")
            print("=" * 50)
            check_and_add_nickname()

        elif choice == '2':
            show_all_nicks()

        elif choice == '3':
            print("\n" + "=" * 50)
            print("УДАЛЕНИЕ НИКА")
            print("=" * 50)
            filename = 'D:\\МОНТАЖ\\ники.txt'
            remove_nickname(filename)

        elif choice == '4':
            print("\n👋 До свидания!")
            break

        else:
            print("❌ Неверный выбор. Попробуйте еще раз.")

        input("\nНажмите Enter для продолжения...")