import os
import base64
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
from collections import defaultdict

def image_to_base64(image_path):
    """Конвертирует изображение в Base64"""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def file_to_base64(file_path):
    """Конвертирует любой файл в Base64"""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def parse_task_number(filename):
    """
    Извлекает номер задания из имени файла
    Поддерживает форматы:
    - Вариант  (13).png
    - 13.png
    - 13_1.png
    - 13_A.png
    - Задание_13.png
    
    Returns:
        tuple: (номер_задания, суффикс) или (None, None)
    """
    # Убираем расширение
    base_name = os.path.splitext(filename)[0]
    
    # Паттерны для разных форматов
    patterns = [
        r'Вариант\s*\((\d+)\)',  # Вариант  (13)
        r'Задание[_\s]*(\d+)',   # Задание_13 или Задание 13
        r'^(\d+)$',               # 13
        r'^(\d+)_(\w+)$',         # 13_1 или 13_A
        r'^(\d+)-(\w+)$',         # 13-1 или 13-A
    ]
    
    for pattern in patterns:
        match = re.match(pattern, base_name)
        if match:
            task_num = int(match.group(1))
            suffix = match.group(2) if match.lastindex > 1 else None
            return (task_num, suffix)
    
    return (None, None)

def find_task_images(task_num):
    """
    Находит все изображения для конкретного задания
    Ищет файлы вида: 13.png, 13_1.png, 13_2.png, 13_A.png и т.д.
    
    Returns:
        list: список путей к найденным изображениям
    """
    images = []
    
    # Паттерны имён файлов для поиска
    patterns = [
        f'Вариант  ({task_num}).png',
        f'{task_num}.png',
        f'Задание_{task_num}.png',
        f'Задание {task_num}.png',
    ]
    
    # Проверяем основные варианты
    for pattern in patterns:
        if os.path.exists(pattern):
            images.append(pattern)
    
    # Ищем файлы с суффиксами (13_1, 13_2, 13_A, и т.д.)
    for file in os.listdir('.'):
        if not file.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        
        parsed_num, suffix = parse_task_number(file)
        if parsed_num == task_num and suffix is not None:
            images.append(file)
    
    # Сортируем для предсказуемого порядка
    images.sort()
    return images

def find_additional_files(task_num):
    """
    Ищет дополнительные файлы для задания
    Поддерживает форматы: 13.txt, 13_A.txt, 13_B.csv и т.д.
    
    Returns:
        list: список путей к найденным дополнительным файлам
    """
    additional_files = []
    
    # Список расширений для поиска
    extensions = ['.txt', '.csv', '.xlsx', '.xls', '.doc', '.docx', '.pdf', 
                  '.zip', '.rar', '.json', '.xml', '.html', '.py', '.cpp', '.pas']
    
    # Ищем файлы с основным номером задания
    base_patterns = [
        f'{task_num}',
        f'Вариант  ({task_num})',
        f'Задание_{task_num}',
    ]
    
    for base_pattern in base_patterns:
        for ext in extensions:
            potential_file = base_pattern + ext
            if os.path.exists(potential_file) and potential_file not in additional_files:
                additional_files.append(potential_file)
                print(f"   📎 Найден дополнительный файл: {potential_file}")
    
    # Ищем файлы с суффиксами (13_A.txt, 13_B.csv и т.д.)
    for file in os.listdir('.'):
        if not any(file.lower().endswith(ext) for ext in extensions):
            continue
        
        parsed_num, suffix = parse_task_number(file)
        if parsed_num == task_num and suffix is not None:
            if file not in additional_files:
                additional_files.append(file)
                print(f"   📎 Найден дополнительный файл: {file}")
    
    additional_files.sort()
    return additional_files

def parse_answers_file(answers_file):
    """
    Парсит файл с ответами
    Форматы, которые поддерживаются:
    - Вариант  (1).png:24
    - 13.png - 24
    - 13:42
    - 27 - текстовый ответ
    """
    answers = {}
    
    try:
        with open(answers_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Пробуем разные варианты разделителей
                task_num = None
                answer = None
                
                if ':' in line:
                    parts = line.split(':', 1)
                elif ' - ' in line:
                    parts = line.split(' - ', 1)
                elif '\t' in line:
                    parts = line.split('\t', 1)
                else:
                    # Пробуем найти последнее число/текст в строке
                    match = re.search(r'(.+?)\s+(\S+.*)$', line)
                    if match:
                        parts = [match.group(1), match.group(2)]
                    else:
                        continue
                
                if len(parts) >= 2:
                    identifier = parts[0].strip()
                    answer = parts[1].strip()
                    
                    # Проверяем, это файл или номер задания
                    if identifier.lower().endswith(('.png', '.jpg', '.jpeg')):
                        # Это имя файла
                        task_num, _ = parse_task_number(identifier)
                    else:
                        # Пробуем как номер задания
                        try:
                            task_num = int(identifier)
                        except ValueError:
                            # Может быть "Вариант (13)" или подобное
                            task_num, _ = parse_task_number(identifier)
                    
                    if task_num:
                        answers[task_num] = answer
                        print(f"✓ Найден ответ: Задание {task_num} → {answer}")
    
    except FileNotFoundError:
        print(f"❌ Файл {answers_file} не найден!")
        return {}
    
    return answers

def create_question_with_text_answer(task_num, images, correct_answer, additional_files):
    """Создает вопрос с текстовым ответом (shortanswer)"""
    question = ET.Element('question', type='shortanswer')
    
    # Название вопроса
    name = ET.SubElement(question, 'name')
    name_text = ET.SubElement(name, 'text')
    name_text.text = f'Задание {task_num}'
    
    # Текст вопроса с изображением(ями)
    questiontext = ET.SubElement(question, 'questiontext', format='html')
    text = ET.SubElement(questiontext, 'text')
    
    # Формируем HTML текст вопроса
    html_content = ''
    
    if len(images) == 1:
        # Одно изображение
        image_filename = os.path.basename(images[0])
        html_content = f'<p><img src="@@PLUGINFILE@@/{image_filename}" alt="Задание {task_num}" style="max-width: 100%;" /></p>'
    else:
        # Несколько изображений
        html_content = f'<p><strong>Задание {task_num} (несколько частей):</strong></p>'
        for idx, img_path in enumerate(images, 1):
            image_filename = os.path.basename(img_path)
            html_content += f'<p>Часть {idx}:<br><img src="@@PLUGINFILE@@/{image_filename}" alt="Задание {task_num} - часть {idx}" style="max-width: 100%;" /></p>'
    
    # Добавляем изображения в Base64
    for img_path in images:
        if os.path.exists(img_path):
            image_filename = os.path.basename(img_path)
            file_elem = ET.SubElement(questiontext, 'file', 
                                     name=image_filename, 
                                     encoding='base64')
            file_elem.text = image_to_base64(img_path)
    
    # Проверяем наличие дополнительных файлов
    if additional_files:
        html_content += '<p><strong>Дополнительные файлы для скачивания:</strong></p><ul>'
        for add_file in additional_files:
            filename = os.path.basename(add_file)
            html_content += f'<li><a href="@@PLUGINFILE@@/{filename}">{filename}</a></li>'
        html_content += '</ul>'
        
        # Добавляем дополнительные файлы в Base64
        for add_file in additional_files:
            filename = os.path.basename(add_file)
            file_elem = ET.SubElement(questiontext, 'file',
                                     name=filename,
                                     encoding='base64')
            file_elem.text = file_to_base64(add_file)
    
    text.text = html_content
    
    # Общий фидбек
    generalfeedback = ET.SubElement(question, 'generalfeedback', format='html')
    feedback_text = ET.SubElement(generalfeedback, 'text')
    feedback_text.text = f'Правильный ответ: {correct_answer}'
    
    # Настройки вопроса
    defaultgrade = ET.SubElement(question, 'defaultgrade')
    defaultgrade.text = '1.0'
    
    penalty = ET.SubElement(question, 'penalty')
    penalty.text = '0.33'
    
    hidden = ET.SubElement(question, 'hidden')
    hidden.text = '0'
    
    # Чувствительность к регистру (0 = не чувствительно)
    usecase = ET.SubElement(question, 'usecase')
    usecase.text = '0'
    
    # Правильный ответ
    answer = ET.SubElement(question, 'answer', fraction='100')
    answer_text = ET.SubElement(answer, 'text')
    answer_text.text = str(correct_answer)
    
    # Фидбек для правильного ответа
    feedback = ET.SubElement(answer, 'feedback', format='html')
    feedback_text = ET.SubElement(feedback, 'text')
    feedback_text.text = 'Правильно!'
    
    return question

def create_category(name):
    """Создает элемент категории для Moodle"""
    question = ET.Element('question', type='category')
    
    category = ET.SubElement(question, 'category')
    category_text = ET.SubElement(category, 'text')
    category_text.text = f'$course$/top/{name}'
    
    return question

def find_all_tasks():
    """
    Находит все задания в текущей папке
    
    Returns:
        set: множество номеров заданий
    """
    tasks = set()
    
    for file in os.listdir('.'):
        if not file.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        
        task_num, _ = parse_task_number(file)
        if task_num:
            tasks.add(task_num)
    
    return tasks

def generate_moodle_xml(answers_file='answers.txt', output_file='questions.xml', 
                        category_name='ЕГЭ Задания'):
    """
    Главная функция генерации Moodle XML
    
    Args:
        answers_file: путь к файлу с ответами
        output_file: имя выходного XML файла
        category_name: базовое имя категории
    """
    
    # Парсим файл с ответами
    answers = parse_answers_file(answers_file)
    
    if not answers:
        print("❌ Не удалось загрузить ответы!")
        return
    
    # Находим все задания в папке
    all_tasks = find_all_tasks()
    print(f"\n📋 Найдено заданий в папке: {len(all_tasks)}")
    print(f"Номера заданий: {sorted(all_tasks)}")
    
    # Создаем корневой элемент
    quiz = ET.Element('quiz')
    
    # Добавляем категорию
    quiz.append(create_category(category_name))
    
    # Счетчик обработанных вопросов
    processed = 0
    missing_answers = []
    
    # Обрабатываем задания в порядке номеров
    for task_num in sorted(all_tasks):
        
        # Проверяем наличие ответа
        if task_num not in answers:
            missing_answers.append(task_num)
            print(f"⚠️  Предупреждение: Нет ответа для задания {task_num}")
            continue
        
        # Находим все изображения для этого задания
        images = find_task_images(task_num)
        
        if not images:
            print(f"⚠️  Предупреждение: Не найдены изображения для задания {task_num}")
            continue
        
        # Находим дополнительные файлы
        additional_files = find_additional_files(task_num)
        
        # Получаем правильный ответ
        correct_answer = answers[task_num]
        
        # Создаем вопрос
        question = create_question_with_text_answer(
            task_num, images, correct_answer, additional_files
        )
        
        quiz.append(question)
        processed += 1
        
        images_info = f"{len(images)} изображение(ий)" if len(images) > 1 else images[0]
        files_info = f" + {len(additional_files)} файл(ов)" if additional_files else ""
        print(f"✅ Обработано задание {task_num}: {images_info}{files_info} → Ответ: {correct_answer}")
    
    # Форматируем XML
    xml_string = ET.tostring(quiz, encoding='unicode')
    dom = minidom.parseString(xml_string)
    pretty_xml = dom.toprettyxml(indent="  ")
    
    # Убираем лишнюю первую строку XML декларации
    lines = pretty_xml.split('\n')
    pretty_xml = '\n'.join(lines[1:])
    
    # Добавляем правильную XML декларацию
    final_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + pretty_xml
    
    # Сохраняем в файл
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_xml)
    
    # Итоговая статистика
    print("\n" + "="*50)
    print(f"✅ XML файл '{output_file}' успешно создан!")
    print(f"📊 Обработано заданий: {processed}")
    print(f"📁 Категория: {category_name}")
    
    if missing_answers:
        print(f"\n⚠️  Не найдены ответы для заданий ({len(missing_answers)}):")
        for task in sorted(missing_answers):
            print(f"   • Задание {task}")
    
    print("\n💡 Подсказка: Загрузите созданный XML файл в Moodle через:")
    print("   Банк вопросов → Импорт → Формат: Moodle XML")

# ============= ПРИМЕР ИСПОЛЬЗОВАНИЯ =============

if __name__ == "__main__":
    # Запускаем генерацию
    # По умолчанию ищет answers.txt в текущей папке
    generate_moodle_xml()
    
    # Можно указать свои параметры:
    # generate_moodle_xml(
    #     answers_file='my_answers.txt',
    #     output_file='my_questions.xml',
    #     category_name='ЕГЭ Информатика'
    # )
    
    input("\nНажмите Enter для выхода...")