from pathlib import Path
import os.path
import shutil
import time
import yaml
import re
import exifread


# ------- Functions -------
def archive_media() -> None:
    for media in media_dir.iterdir():
        if re.match(r'^.+\.(png|jpg|jpeg)$', str(media), re.IGNORECASE):
            archive_photo(media)
        if re.match(r'^.+\.(mp4|mov)$', str(media), re.IGNORECASE):
            archive_video(media)


def archive_photo(photo_path: Path) -> None:
    """
    Archives photo
    :param photo_path: path to the photo
    """
    print('\nInfo for %s' % os.path.basename(photo_path))
    date = find_photo_date(photo_path)
    if date:
        print('Parsed date %s' % time.strftime('%Y-%m-%d - %H:%M:%S', date))
        move_to(photo_path, str(date.tm_year))
    else:
        print_debug('Could not parse any date')
        if cfg['options']['put_no_date_media_this_year']:
            now = time.gmtime(time.time())
            move_to(photo_path, str(now.tm_year))


def archive_video(video_path: Path) -> None:
    """
    Archives video
    :param video_path: path to the video
    """
    print('\nInfo for %s' % os.path.basename(video_path))
    date = get_os_file_datetime(video_path)

    extend_str = str(date.tm_year)
    if cfg['options']['video_folder']:
        extend_str = extend_str + '/video'

    move_to(video_path, extend_str)


def move_to(src_file: Path, extend_path: str) -> Path:
    """
    Builds a destination folder path out of src_file path without last element
    and extend_path and moves the source file to this folder
    :param src_file: file to move
    :param extend_path: path to extend the source path with
    :return: the new destination of the file
    """
    if src_file.is_file():
        target_dir = media_dir / extend_path
        if not cfg['options']['ignore_duplicate'] and (target_dir / os.path.basename(src_file)).exists():
            src_file = handle_duplicates_in_target(src_file, target_dir)
            create_if_not_exists(target_dir)
            shutil.move(str(src_file), str(target_dir))
            print('Moved to %s' % target_dir)
            return target_dir
        else:
            print('Duplicate Ignored!!')


def handle_duplicates_in_target(src_file: Path, target_dir: Path) -> Path:
    """
    Adds or increments a counter to the src file till it can be moved
    to target_dir without overwriting existing file
    :param src_file: file to check
    :param target_dir: target directory
    """
    path, extension = os.path.splitext(src_file)
    file_name = os.path.basename(path)
    candidate = file_name+extension

    index = 0
    format_pattern = '{}' + cfg['main']['duplicate_suffix'] + '{}{}'
    ls = set(os.listdir(str(target_dir)))
    while candidate in ls:
        print('%s already exists in %s' % (candidate, target_dir))
        candidate = format_pattern.format(file_name, index, extension)
        print('Trying %s' % candidate)
        index += 1

    renamed_src_file = media_dir / candidate
    os.rename(str(src_file), str(renamed_src_file))
    return renamed_src_file


def find_photo_date(photo_path: Path) -> time.struct_time:
    """
    Parses the date out of all possible metadata in the photo
    :param photo_path: path to the photo
    :return: parsed datetime
    """
    file = open(photo_path, 'rb')
    tags = exifread.process_file(file, details=False)

    print_debug('EXIF DateTimeOriginal: ' + str(tags.get('EXIF DateTimeOriginal')))
    if tags.get('EXIF DateTimeOriginal'):
        return parse_exif_datetime_string(str(tags.get('EXIF DateTimeOriginal')))

    print_debug('Image DateTime: ' + str(tags.get('Image DateTime')))
    if tags.get('Image DateTime'):
        return parse_exif_datetime_string(str(tags.get('Image DateTime')))

    if cfg['options']['creation_time_fallback']:
        return get_os_file_datetime(photo_path)


def parse_exif_datetime_string(tag: str) -> time.struct_time:
    """
    Parses a string with the format YYYY:MM:DD HH:MM:SS like in the exif information
    :param tag: the string to parse
    :return: parsed date
    """
    return time.strptime(tag, '%Y:%m:%d %H:%M:%S')


def get_os_file_datetime(path: Path) -> time.struct_time:
    """
    Reads last modified and creation date of the file and returns the oldest
    :param path: path to the file
    :return: datetime
    """
    print_debug('Last modified: ' + time.ctime(os.path.getmtime(path)))
    print_debug('Created: ' + time.ctime(os.path.getctime(path)))
    created = os.path.getctime(path)
    modified = os.path.getmtime(path)

    if created >= modified:
        return time.gmtime(modified)
    else:
        return time.gmtime(created)


def create_if_not_exists(folder: Path) -> None:
    """
    Creates a folder at the given path no matter if already exists or not
    Parent folder are created till given path is reachable
    :param folder: folder to create
    """
    folder.mkdir(parents=True, exist_ok=True)


def print_debug(msg: str) -> None:
    """
    Prints debug message if debugging is enabled in config
    :param msg: msg to print
    """
    if cfg['options']['print_debug']:
        print(msg)


# ------- Start point -------
with open("config.yml", 'r') as configFile:
    cfg = yaml.load(configFile)

media_dir = Path(cfg['main']['media_dir'])

if media_dir.exists() & media_dir.is_dir():
    archive_media()
else:
    print(str(media_dir) + ' neither exists or is a folder.')
