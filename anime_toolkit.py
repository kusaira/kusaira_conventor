import os
import sys
import subprocess
import glob
import re

def get_tool_path(tool_name):
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    if hasattr(sys, '_MEIPASS'):
        path = os.path.join(sys._MEIPASS, tool_name)
        if os.path.exists(path):
            return path
            
    # Try current directory
    if os.path.exists(tool_name):
        return tool_name
        
    # Default fallback to assuming it's in PATH
    return tool_name

def mp4_convert():
    ffmpeg = get_tool_path('ffmpeg.exe')
    print("Автоматическая конвертация ВСЕХ видео в MP4 (HEVC + AAC) с удалением оригиналов...")
    if not os.path.exists("temp_converted"):
        os.makedirs("temp_converted")
    
    extensions = ('*.mp4', '*.mkv', '*.avi', '*.mov', '*.m4v', '*.flv')
    files = []
    for ext in extensions:
        files.extend(glob.glob(ext))
        
    for f in files:
        print(f"\n--------------------------------------------------")
        print(f"Обрабатывается: {f}")
        print(f"--------------------------------------------------")
        
        name, _ = os.path.splitext(f)
        out_path = os.path.join("temp_converted", f"{name}.mp4")
        
        cmd = [ffmpeg, "-i", f, "-c:v", "hevc_nvenc", "-preset", "fast", "-b:v", "8000k", "-maxrate", "10000k", "-bufsize", "16000k", "-c:a", "aac", "-b:a", "192k", out_path]
        res = subprocess.run(cmd)
        
        if res.returncode != 0:
            print(f"[ОШИБКА] Не удалось конвертировать {f}. Оригинал сохранен.")
            if os.path.exists(out_path):
                os.remove(out_path)
        else:
            print(f"[УСПЕХ] Конвертация завершена. Удаляю старый файл...")
            os.remove(f)
            
    print("\nПеремещаю новые файлы в текущую папку...")
    new_files = glob.glob("temp_converted/*.mp4")
    for nf in new_files:
        dest = os.path.basename(nf)
        if os.path.exists(dest):
            os.remove(dest)
        os.rename(nf, dest)
        
    try:
        os.rmdir("temp_converted")
    except:
        pass
    print("Все готово!")



def safe_mode():
    mkvmerge = get_tool_path('mkvmerge.exe')
    print("1. Удалить аудио и сабы (оставить только видео)")
    print("2. Оставить только выбранные видео и аудио дорожки")
    print("3. Слить с внешним аудио (.mka или .ac3)")
    choice = input("Выберите действие (например 1 2 3): ")
    
    valid_choices = [c for c in choice.split() if c in ['1', '2', '3']]
    if not valid_choices:
        print("Неверный выбор!")
        return
        
    video_id = ""
    audio_ids = ""
    if '2' in valid_choices:
        video_id = input("Введите ID видеодорожки: ")
        audio_ids = input("Введите ID аудиодорожек (через запятую): ")
        audio_ids = audio_ids.replace(' ', ',').replace(',,', ',')
        if audio_ids.endswith(','): audio_ids = audio_ids[:-1]
        
    exts = ('*.mkv', '*.mp4', '*.hevc', '*.avi', '*.h264', '*.m2ts', '*.ogm', '*.mpg')
    files = []
    for e in exts: files.extend(glob.glob(e))
    
    for f in files:
        name, ext = os.path.splitext(f)
        output = f"{name}_processed.mkv"
        print(f"\nОбработка: {f}")
        
        if not os.path.exists("temp"):
            os.makedirs("temp")
            
        tempfile = f"temp\\{name}.mkv"
        subprocess.run(f'copy "{f}" "{tempfile}"', shell=True, stdout=subprocess.DEVNULL)
        
        if '1' in valid_choices:
            print("[ШАГ 1] Удаляем аудио, сабы и другие теги...")
            cmd = [mkvmerge, "--output", f"temp\\{name}_step1.mkv", "--no-audio", "--no-subtitles", "--no-attachments", "--no-chapters", "--no-track-tags", "--no-global-tags", tempfile]
            res = subprocess.run(cmd)
            if res.returncode != 0:
                print("Ошибка шаг 1")
                continue
            os.replace(f"temp\\{name}_step1.mkv", tempfile)
            
        if '2' in valid_choices:
            print(f"[ШАГ 2] Оставляем видео {video_id} и аудио {audio_ids}...")
            cmd = [mkvmerge, "--output", f"temp\\{name}_step2.mkv", "--video-tracks", video_id, "--audio-tracks", audio_ids, "--no-subtitles", "--no-chapters", "--no-attachments", "--no-track-tags", "--no-global-tags", tempfile]
            res = subprocess.run(cmd)
            if res.returncode != 0:
                print("Ошибка шаг 2")
                continue
            os.replace(f"temp\\{name}_step2.mkv", tempfile)
            
        if '3' in valid_choices:
            print("[ШАГ 3] Слияние с внешним аудио...")
            audio_added = False
            mka_path = f"{name}.mka"
            if os.path.exists(mka_path):
                print(f"Добавляем аудиофайл: {mka_path}")
                cmd = [mkvmerge, "--output", f"temp\\{name}_step3.mkv", tempfile, mka_path]
                res = subprocess.run(cmd)
                if res.returncode == 0:
                    os.replace(f"temp\\{name}_step3.mkv", tempfile)
                    audio_added = True
                    
            ac3_path = f"{name}.ac3"
            if os.path.exists(ac3_path):
                print(f"Добавляем аудиофайл: {ac3_path}")
                cmd = [mkvmerge, "--output", f"temp\\{name}_step3b.mkv", tempfile, ac3_path]
                res = subprocess.run(cmd)
                if res.returncode == 0:
                    os.replace(f"temp\\{name}_step3b.mkv", tempfile)
                    audio_added = True
                    
            if not audio_added:
                print("[!] Внешние аудиофайлы не найдены, пропускаем.")
                
        os.replace(tempfile, output)
        subprocess.run("rd /s /q temp", shell=True)
        
    print("\nОчистка старых файлов...")
    for f in files:
        name, _ = os.path.splitext(f)
        if os.path.exists(f"{name}_processed.mkv"):
            print(f"Удаляю старое видео: {f}")
            os.remove(f)
            if '3' not in valid_choices:
                if os.path.exists(f"{name}.mka"):
                    os.remove(f"{name}.mka")
                    
    print("Успешно!")

def smart_rename():
    prefix = input("Введите префикс (например 'Наруто', получится '1_Наруто.mp4'). Оставьте пустым, чтобы были только цифры: ").strip()
    
    exts = ('*.mp4', '*.mkv', '*.avi', '*.mov', '*.m4v')
    files = []
    for e in exts: files.extend(glob.glob(e))
    
    if not files:
        print("Нет видеофайлов для переименования.")
        return

    ignore_list = {'1080', '720', '480', '2160', '264', '265', '10', '8'}
    files_with_nums = []
    
    for filename in files:
        name, ext = os.path.splitext(filename)
        numbers = re.findall(r'\d+', name)
        valid_numbers = [num for num in numbers if num not in ignore_list and not (1990 <= int(num) <= 2030)]
        if valid_numbers:
            files_with_nums.append((filename, valid_numbers, ext))
            
    if not files_with_nums:
        print("Не найдено чисел ни в одном файле.")
        return
        
    first_file, first_nums, _ = files_with_nums[0]
    print(f"\nАнализ первого файла: {first_file}")
    print("Найденные числа:")
    for i, num in enumerate(first_nums):
        print(f"{i + 1}: {num}")
        
    while True:
        try:
            choice = int(input("\nКакой по счету блок цифр является номером серии? (введите цифру): "))
            if 1 <= choice <= len(first_nums):
                index_to_use = choice - 1
                break
            print("Неверный номер, попробуйте снова.")
        except ValueError:
            print("Пожалуйста, введите число.")
            
    rename_plan = []
    for filename, nums, ext in files_with_nums:
        if index_to_use < len(nums):
            ep_num = nums[index_to_use]
            if prefix:
                new_name = f"[{ep_num}]_{prefix}{ext}"
            else:
                new_name = f"[{ep_num}]{ext}"
                
            if filename != new_name:
                rename_plan.append((filename, new_name))
                print(f"Будет: {filename} --> {new_name}")
        else:
            print(f"[!] В файле {filename} недостаточно числовых блоков, пропускаем.")
            
    if not rename_plan:
        print("\nНет файлов для переименования.")
        return
        
    if input("\nПереименовать эти файлы? (y/n): ").lower() in ('y', 'yes', 'д', 'да'):
        for old_name, new_name in rename_plan:
            counter = 1
            final_new_name = new_name
            while os.path.exists(final_new_name):
                n, e = os.path.splitext(new_name)
                final_new_name = f"{n}_{counter}{e}"
                counter += 1
            os.rename(old_name, final_new_name)
        print("Успешно!")

def main():
    # Fix console encoding for Windows
    if os.name == 'nt':
        os.system('chcp 65001 >nul')
        
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=============================================")
        print("             MEDIA TOOLKIT                   ")
        print("=============================================")
        print("1. Конвертация всех видео в MP4 (HEVC + AAC)")
        print("2. Safe Mode (Удалить/Извлечь/Добавить аудио)")
        print("3. Умное переименование серий")
        print("0. Выход")
        print("=============================================")
        
        choice = input("Выберите действие: ").strip()
        
        if choice == '1':
            mp4_convert()
        elif choice == '2':
            safe_mode()
        elif choice == '3':
            smart_rename()
        elif choice == '0':
            break
            
        input("\nНажмите Enter для продолжения...")

if __name__ == '__main__':
    main()
