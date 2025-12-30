import os
from pathlib import Path


def get_folder_size(folder_path):
    """Рекурсивно вычисляет размер папки в байтах"""
    total_size = 0
    try:
        for entry in os.scandir(folder_path):
            if entry.is_file():
                total_size += entry.stat().st_size
            elif entry.is_dir():
                total_size += get_folder_size(entry.path)
    except (PermissionError, OSError):
        # Пропускаем папки, к которым нет доступа
        return 0
    return total_size


def format_size(size_bytes):
    """Форматирует размер в удобочитаемый вид"""
    for unit in ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} ПБ"


def analyze_folders(path):
    """Анализирует папки и сортирует их по размеру"""
    if not os.path.exists(path):
        print(f"Ошибка: путь '{path}' не существует!")
        return

    if not os.path.isdir(path):
        print(f"Ошибка: '{path}' не является папкой!")
        return

    print(f"Анализируем папки в: {path}")
    print("-" * 50)

    folders = []

    # Собираем информацию о всех подпапках
    for entry in os.scandir(path):
        if entry.is_dir():
            print(f"Вычисляем размер: {entry.name}...")
            size_bytes = get_folder_size(entry.path)
            folders.append({
                'name': entry.name,
                'path': entry.path,
                'size_bytes': size_bytes,
                'size_formatted': format_size(size_bytes)
            })

    if not folders:
        print("В указанной папке нет подпапок.")
        return

    # Сортируем папки по размеру (от большего к меньшему)
    folders.sort(key=lambda x: x['size_bytes'], reverse=True)

    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ (отсортировано по убыванию размера):")
    print("=" * 60)

    # Выводим результаты
    for i, folder in enumerate(folders, 1):
        if i == 1:
            print(f"▶ САМАЯ БОЛЬШАЯ ПАПКА: {folder['name']}")
            print(f"  Размер: {folder['size_formatted']}")
            print(f"  Путь: {folder['path']}")
            print("-" * 60)
        else:
            print(f"{i:2}. {folder['name']:40} {folder['size_formatted']:>15}")

    # Выводим статистику
    print("\n" + "=" * 60)
    print(f"Всего проанализировано папок: {len(folders)}")
    total_size = sum(f['size_bytes'] for f in folders)
    print(f"Общий размер всех папок: {format_size(total_size)}")

    if len(folders) > 1:
        ratio = folders[0]['size_bytes'] / folders[1]['size_bytes'] if folders[1]['size_bytes'] > 0 else 0
        if ratio > 1:
            print(f"Самая большая папка в {ratio:.1f} раз больше следующей по размеру")


def main():
    # Запрашиваем путь у пользователя
    path_input = input("Введите путь к папке для анализа: ").strip()

    # Если путь не введен, используем текущую папку
    if not path_input:
        path_input = os.getcwd()

    # Заменяем тильду на домашнюю директорию (для Linux/Mac)
    if path_input.startswith('~'):
        path_input = os.path.expanduser(path_input)

    analyze_folders(path_input)


if __name__ == "__main__":
    main()