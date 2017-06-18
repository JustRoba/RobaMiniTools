from pathlib import Path
import os.path
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
    print('\nTags for ' + str(photo_path))
    date = find_date(photo_path)
    if date:
        print('Selected date %s' % time.strftime('%Y-%m-%d - %H:%M:%S', date))
    else:
        print('nothing found')


def find_date(photo_path: Path) -> time.struct_time:
    """
    Parses the date out of all possible metadata in the photo
    :param photo_path: Path
    :return: time.struct_time
    """
    file = open(photo_path, 'rb')
    tags = exifread.process_file(file, details=False)

    print_debug('Image DateTime: ' + str(tags.get('Image DateTime')))
    if tags.get('EXIF DateTimeOriginal'):
        return parse_exif_time_string(str(tags.get('EXIF DateTimeOriginal')))

    print_debug('Image DateTime: ' + str(tags.get('Image DateTime')))
    if tags.get('Image DateTime'):
        return parse_exif_time_string(str(tags.get('Image DateTime')))

    if cfg['options']['creation_time_fallback']:
        return parse_os_file_time(photo_path)


def parse_os_file_time(path: Path) -> time.struct_time:
    print_debug('Last modified: ' + time.ctime(os.path.getmtime(path)))
    print_debug('Created: ' + time.ctime(os.path.getctime(path)))
    created = os.path.getctime(path)
    modified = os.path.getmtime(path)

    if created >= modified:
        return time.gmtime(modified)
    else:
        return time.gmtime(created)


def parse_exif_time_string(tag: str) -> time.struct_time:
    return time.strptime(tag, '%Y:%m:%d %H:%M:%S')


def archive_video(video) -> None:
    pass


def print_debug(msg: str) -> None:
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
