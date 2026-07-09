import os
import sys
import subprocess
import glob
import re

import json

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
    import shutil
    ffmpeg = get_tool_path('ffmpeg.exe')
    if not shutil.which(ffmpeg) and not os.path.exists(ffmpeg):
        print("\n[КРИТИЧЕСКАЯ ОШИБКА] Не найден файл ffmpeg.exe!")
        print("Скопируйте ffmpeg.exe в ту же папку, где находится anime_toolkit.exe и ваше видео.")
        return
    print("Автоматическая конвертация ВСЕХ видео в MP4 (HEVC + AAC) с удалением оригиналов...")
    print("\nВыберите кодировщик для конвертации:")
    print("1. NVIDIA (hevc_nvenc) - Видеокарты GeForce (Быстро)")
    print("2. AMD (hevc_amf) - Видеокарты Radeon")
    print("3. Intel (hevc_qsv) - Встроенная/дискретная графика Intel")
    print("4. Процессор (libx265) - Медленно, универсально")
    enc_choice = input("Ваш выбор (по умолчанию 1): ").strip()
    
    if enc_choice == '2':
        vcodec = "hevc_amf"
    elif enc_choice == '3':
        vcodec = "hevc_qsv"
    elif enc_choice == '4':
        vcodec = "libx265"
    else:
        vcodec = "hevc_nvenc"
        
    print(f"\nВыбран кодек: {vcodec}")
    
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
        
        # Проверяем формат аудио
        probe_cmd = [ffmpeg, "-i", f]
        probe_res = subprocess.run(probe_cmd, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
        
        audio_codec = "unknown"
        for line in probe_res.stderr.split('\n'):
            if "Stream" in line and "Audio:" in line:
                if "aac" in line.lower():
                    audio_codec = "aac"
                break
                
        if audio_codec == "aac":
            print("[ИНФО] Звуковая дорожка уже в AAC. Перекодировка звука не требуется (прямое копирование).")
            audio_args = ["-c:a", "copy"]
        else:
            print("[ИНФО] Звуковая дорожка будет перекодирована в AAC (192 kbps).")
            audio_args = ["-c:a", "aac", "-b:a", "192k"]
        
        name, _ = os.path.splitext(f)
        out_path = os.path.join("temp_converted", f"{name}.mp4")
        
        v_args = []
        if vcodec == "libx265":
            v_args = ["-c:v", vcodec, "-preset", "fast", "-crf", "20"]
        elif vcodec == "hevc_nvenc":
            v_args = ["-c:v", vcodec, "-preset", "fast", "-b:v", "8000k", "-maxrate", "8000k", "-bufsize", "8000k"]
        elif vcodec == "hevc_amf":
            v_args = ["-c:v", vcodec, "-quality", "speed", "-rc", "cqp", "-qp_p", "20", "-qp_i", "20"]
        elif vcodec == "hevc_qsv":
            v_args = ["-c:v", vcodec, "-preset", "fast", "-global_quality", "20"]
            
        cmd = [ffmpeg, "-i", f] + v_args + audio_args + ["-movflags", "+faststart", out_path]
            
        res = subprocess.run(cmd)
        
        if res.returncode != 0:
            print(f"[ОШИБКА] Не удалось конвертировать {f}. Оригинал сохранен.")
            if os.path.exists(out_path):
                os.remove(out_path)
        else:
            print(f"[УСПЕХ] Конвертация завершена. Удаляю старый файл...")
            import time
            deleted = False
            for _ in range(5):
                try:
                    os.remove(f)
                    deleted = True
                    break
                except:
                    time.sleep(1)
            if not deleted:
                print(f"[ОШИБКА] Файл '{f}' занят другой программой. Не удалось удалить.")
                
    print("\nПеремещаю новые файлы в текущую папку...")
    new_files = glob.glob("temp_converted/*.mp4")
    for nf in new_files:
        dest = os.path.basename(nf)
        try:
            if os.path.exists(dest):
                os.remove(dest)
            os.rename(nf, dest)
        except Exception as e:
            print(f"[ОШИБКА] Не удалось переместить {nf} -> {dest}: {e}")
        
    try:
        os.rmdir("temp_converted")
    except:
        pass
    print("Все готово!")
    input("\nНажмите Enter для возврата в меню...")



def safe_mode():
    import shutil
    mkvmerge = get_tool_path('mkvmerge.exe')
    if not shutil.which(mkvmerge) and not os.path.exists(mkvmerge):
        print("\n[КРИТИЧЕСКАЯ ОШИБКА] Не найден файл mkvmerge.exe!")
        print("Скопируйте mkvmerge.exe в ту же папку, где находится anime_toolkit.exe и ваше видео.")
        return
    print("1. Удалить аудио и сабы (оставить только видео)")
    print("2. Оставить только выбранные видео и аудио дорожки")
    print("3. Слить с внешним аудио (.mka или .ac3)")
    choice = input("Выберите действие (например 1 2 3): ")
    
    valid_choices = [c for c in choice.split() if c in ['1', '2', '3']]
    if not valid_choices:
        print("Неверный выбор!")
        return
        
    exts = ('*.mkv', '*.mp4', '*.hevc', '*.avi', '*.h264', '*.m2ts', '*.ogm', '*.mpg')
    files = []
    for e in exts: files.extend(glob.glob(e))
    
    if not files:
        print("В папке нет подходящих видеофайлов.")
        return
        
    video_id = ""
    audio_ids = ""
    if '2' in valid_choices:
        print("\n=== Дорожки в первом файле ===")
        try:
            res = subprocess.run([mkvmerge, "-J", files[0]], capture_output=True, text=True, encoding='utf-8', errors='ignore')
            data = json.loads(res.stdout)
            tracks = data.get('tracks', [])
            if not tracks:
                print("Дорожки не найдены.")
            else:
                for track in tracks:
                    tid = track.get('id', '?')
                    ttype = track.get('type', 'unknown').upper()
                    codec = track.get('codec', '')
                    
                    props = track.get('properties', {})
                    lang = props.get('language', '')
                    name = props.get('track_name', '')
                    
                    info = f"ID: {tid} | {ttype}"
                    if codec: info += f" | {codec}"
                    if lang: info += f" | Яз: {lang}"
                    if name: info += f" | '{name}'"
                    print(info)
        except Exception as e:
            print("Не удалось распарсить дорожки:", e)
        print("==============================\n")
        
        video_id = input("Введите ID видеодорожки: ")
        audio_ids = input("Введите ID аудиодорожек (через запятую): ")
        audio_ids = audio_ids.replace(' ', ',').replace(',,', ',')
        if audio_ids.endswith(','): audio_ids = audio_ids[:-1]
    
    used_audios = []
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
            
            core_name = name
            for suffix in ['_processed', '_deep', '_raw', '_clean', '_audio', '_voice']:
                if core_name.lower().endswith(suffix):
                    core_name = core_name[:-len(suffix)]
                    
            possible_audios = []
            for ext_audio in ['*.mka', '*.ac3', '*.m4a', '*.mp3', '*.wav', '*.flac']:
                possible_audios.extend(glob.glob(ext_audio))
                
            matched_audio = None
            for audio_f in possible_audios:
                audio_core = os.path.splitext(audio_f)[0]
                for suffix in ['_processed', '_deep', '_raw', '_clean', '_audio', '_voice']:
                    if audio_core.lower().endswith(suffix):
                        audio_core = audio_core[:-len(suffix)]
                
                if core_name == audio_core or audio_core.startswith(core_name) or core_name.startswith(audio_core):
                    matched_audio = audio_f
                    break
                    
            if matched_audio:
                print(f"Добавляем внешний аудиофайл: {matched_audio}")
                cmd = [mkvmerge, "--output", f"temp\\{name}_step3.mkv", tempfile, matched_audio]
                res = subprocess.run(cmd)
                if res.returncode == 0:
                    os.replace(f"temp\\{name}_step3.mkv", tempfile)
                    audio_added = True
                    used_audios.append(matched_audio)
            
            if not audio_added:
                print(f"[!] Внешние аудиофайлы для '{name}' не найдены, пропускаем.")
                
        os.replace(tempfile, output)
        subprocess.run("rd /s /q temp", shell=True)
        
    import time
    print("\nОчистка старых файлов...")
    for f in files:
        name, _ = os.path.splitext(f)
        processed = f"{name}_processed.mkv"
        if os.path.exists(processed):
            print(f"Удаляю старое видео: {f}")
            deleted = False
            for _ in range(5):
                try:
                    os.remove(f)
                    deleted = True
                    break
                except:
                    time.sleep(1)
            
            if deleted:
                try:
                    os.rename(processed, f"{name}.mkv")
                except Exception as e:
                    print(f"[ОШИБКА] Не удалось переименовать обработанный файл: {e}")
            else:
                print(f"[ОШИБКА] Файл '{f}' занят другой программой (возможно, открыт в плеере).")
                print(f"Из-за этого новый файл сохранен рядом как: '{processed}'")
                
            # Если мы сливали аудио, удаляем исходные внешние дорожки
            if '3' in valid_choices:
                for ext_audio in used_audios:
                    if os.path.exists(ext_audio):
                        try:
                            os.remove(ext_audio)
                            print(f"Удален исходный аудиофайл: {ext_audio}")
                        except:
                            pass
                    
    print("Успешно!")
    input("\nНажмите Enter для возврата в меню...")

def smart_rename():
    prefix = input("Введите префикс (например 'Наруто', получится '1_Наруто.mp4'). Оставьте пустым, чтобы были только цифры: ").strip()
    
    exts = ('*.mp4', '*.mkv', '*.avi', '*.mov', '*.m4v')
    files = []
    for e in exts: files.extend(glob.glob(e))
    
    if not files:
        print("Нет видеофайлов для переименования.")
        return

    ignore_list = {'720', '480', '2160', '264', '265', '10-bit', '8-bit'}
    files_with_nums = []
    
    for filename in files:
        name, ext = os.path.splitext(filename)
        # Ищем числа, игнорируем -bit
        name_clean = name.replace('10-bit', '').replace('8-bit', '').replace('10bit', '').replace('8bit', '')
        numbers = re.findall(r'\d+', name_clean)
        valid_numbers = [num for num in numbers if num not in ignore_list and int(num) < 1080]
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
        
    ans = input("\nПереименовать эти файлы? (Нажмите Enter для 'Да', или введите 'n' для 'Нет'): ").strip().lower()
    if ans not in ('n', 'no', 'н', 'нет', '0', 'т', 'ytr'):
        for old_name, new_name in rename_plan:
            counter = 1
            final_new_name = new_name
            while os.path.exists(final_new_name) and old_name.lower() != final_new_name.lower():
                n, e = os.path.splitext(new_name)
                final_new_name = f"{n}_{counter}{e}"
                counter += 1
                
            try:
                os.rename(old_name, final_new_name)
            except Exception as e:
                print(f"[ОШИБКА] Не удалось переименовать {old_name}: {e}")
                print("Возможно, файл открыт в торренте или видеоплеере!")
        print("\nПроцесс переименования завершен!")
    else:
        print("\nПереименование отменено пользователем.")

def split_video():
    import shutil
    mkvmerge = get_tool_path('mkvmerge.exe')
    if not shutil.which(mkvmerge) and not os.path.exists(mkvmerge):
        print("\n[КРИТИЧЕСКАЯ ОШИБКА] Не найден файл mkvmerge.exe!")
        print("Скопируйте mkvmerge.exe в ту же папку, где находится anime_toolkit.exe.")
        return
        
    print("\n=== Нарезка видео на части (Без потери качества) ===")
    print("Идеально для обхода лимитов в Telegram (до 2000 МБ).")
    size_input = input("Укажите максимальный размер одной части в Мегабайтах (по умолчанию 1900): ").strip()
    
    if not size_input:
        size_input = "1900"
        
    if not size_input.isdigit():
        print("Ошибка: нужно ввести число.")
        return
        
    exts = ('*.mkv', '*.mp4', '*.hevc', '*.avi', '*.m2ts', '*.mov')
    files = []
    for e in exts: files.extend(glob.glob(e))
    
    if not files:
        print("Нет видеофайлов для нарезки.")
        return
        
    for f in files:
        name, ext = os.path.splitext(f)
        # Игнорируем уже порезанные файлы (с "-001" на конце)
        if re.search(r'-\d{3}$', name):
            continue
            
        print(f"\nРежем файл: {f}")
        output = f"{name}_part.mkv"
        cmd = [mkvmerge, "-o", output, "--split", f"size:{size_input}M", f]
        res = subprocess.run(cmd)
        
        if res.returncode == 0:
            print(f"[УСПЕХ] Файл {f} успешно порезан на части!")
            
            # Если оригинал был не mkv (например, mp4), быстро возвращаем ему родной контейнер
            if ext.lower() != '.mkv':
                print(f"Возвращаем формат {ext} (без потери качества)...")
                ffmpeg = get_tool_path('ffmpeg.exe')
                parts = glob.glob(f"{name}_part-*.mkv")
                for part in parts:
                    part_name, _ = os.path.splitext(part)
                    final_part = f"{part_name}{ext}"
                    subprocess.run([ffmpeg, "-y", "-i", part, "-c", "copy", final_part], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    os.remove(part)
                    
            ans = input(f"Удалить оригинальный файл '{f}'? (y/n): ").strip().lower()
            if ans in ('y', 'yes', 'д', 'да'):
                try:
                    os.remove(f)
                    print("Оригинал удален.")
                except Exception as e:
                    print(f"[ОШИБКА] Не удалось удалить {f}: {e}")
        else:
            print(f"[ОШИБКА] Не удалось порезать {f}.")

def merge_videos():
    import shutil
    mkvmerge = get_tool_path('mkvmerge.exe')
    if not shutil.which(mkvmerge) and not os.path.exists(mkvmerge):
        print("\n[КРИТИЧЕСКАЯ ОШИБКА] Не найден файл mkvmerge.exe!")
        print("Скопируйте mkvmerge.exe в ту же папку, где находится anime_toolkit.exe.")
        return
        
    print("\n=== Склейка видео (Без потери качества) ===")
    print("Этот режим объединит все видеофайлы в папке в один большой файл.")
    print("Файлы будут склеиваться в алфавитном порядке их названий.")
    
    exts = ('*.mkv', '*.mp4', '*.hevc', '*.avi', '*.m2ts', '*.mov')
    files = []
    for e in exts: files.extend(glob.glob(e))
    
    files.sort()
    
    if not files or len(files) < 2:
        print("В папке должно быть как минимум 2 видеофайла для склейки.")
        return
        
    print("\nФайлы для склейки (по порядку):")
    for i, f in enumerate(files):
        print(f"{i+1}. {f}")
        
    ans = input("\nСклеить эти файлы в один? (y/n): ").strip().lower()
    if ans not in ('y', 'yes', 'д', 'да'):
        print("Отмена.")
        return
        
    _, target_ext = os.path.splitext(files[0])
    output_name = input("Введите название итогового файла (без расширения, по умолчанию 'merged_video'): ").strip()
    if not output_name:
        output_name = "merged_video"
        
    # Удаляем запрещенные символы для Windows и ffmpeg (например, двоеточие или слеши)
    for c in '<>:"/\\|?*':
        output_name = output_name.replace(c, '_')
        
    output_file_mkv = f"{output_name}.mkv"
    output_file_final = f"{output_name}{target_ext}"
    
    print("\nНачинаю склейку (Шаг 1: mkvmerge)...")
    cmd = [mkvmerge, "-o", output_file_mkv, files[0]]
    for f in files[1:]:
        cmd.extend(["+", f])
        
    res = subprocess.run(cmd)
    
    if res.returncode != 0:
        print("\n[ВНИМАНИЕ] mkvmerge не справился (часто бывает при HEVC MP4). Пробую через FFmpeg...")
        ffmpeg = get_tool_path('ffmpeg.exe')
        if shutil.which(ffmpeg) or os.path.exists(ffmpeg):
            with open("concat_list.txt", "w", encoding="utf-8") as txt:
                for f in files:
                    safe_f = f.replace("'", "'\\''")
                    txt.write(f"file '{safe_f}'\n")
            cmd2 = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", "concat_list.txt", "-c", "copy", output_file_final]
            res = subprocess.run(cmd2)
            try:
                os.remove("concat_list.txt")
            except:
                pass
        else:
            print("[ОШИБКА] ffmpeg.exe не найден для альтернативной склейки.")
            
    if res.returncode == 0:
        # Возвращаем родной формат, если mkvmerge отработал, но нам нужен был MP4
        if os.path.exists(output_file_mkv) and target_ext.lower() != '.mkv':
            print(f"Возвращаем формат {target_ext} (без потери качества)...")
            ffmpeg = get_tool_path('ffmpeg.exe')
            subprocess.run([ffmpeg, "-y", "-i", output_file_mkv, "-c", "copy", output_file_final], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.remove(output_file_mkv)
            
        print(f"\n[УСПЕХ] Видео успешно склеены в файл {output_file_final}!")
        ans_del = input("Удалить исходные куски? (y/n): ").strip().lower()
        if ans_del in ('y', 'yes', 'д', 'да'):
            for f in files:
                try:
                    os.remove(f)
                except:
                    pass
            print("Исходные файлы удалены.")
    else:
        print("\n[ОШИБКА] Не удалось склеить файлы ни одним из способов. Проверьте, что у них одинаковый кодек и разрешение.")
    
    input("\nНажмите Enter для возврата в меню...")

def main():
    # Fix console encoding for Windows
    if os.name == 'nt':
        os.system('chcp 65001 >nul')
        
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=============================================")
        print("          Kusaira Conventor v2.2-CBR         ")
        print("=============================================")
        print("1. Конвертация всех видео в MP4 (HEVC + AAC)")
        print("2. Safe Mode (Удалить/Извлечь/Добавить аудио)")
        print("3. Умное переименование серий")
        print("4. Разбить видео на части (Для Telegram)")
        print("5. Склеить видео в один файл")
        print("0. Выход")
        print("=============================================")
        
        choice = input("Выберите действие: ").strip()
        
        if choice == '1':
            mp4_convert()
        elif choice == '2':
            safe_mode()
        elif choice == '3':
            smart_rename()
            input("\nНажмите Enter для продолжения...")
        elif choice == '4':
            split_video()
            input("\nНажмите Enter для продолжения...")
        elif choice == '5':
            merge_videos()
            input("\nНажмите Enter для продолжения...")
        elif choice == '0':
            break
            
        input("\nНажмите Enter для продолжения...")

if __name__ == '__main__':
    main()
