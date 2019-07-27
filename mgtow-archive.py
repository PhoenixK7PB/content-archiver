#  ███╗   ███╗ ██████╗████████╗ ██████╗ ██╗    ██╗     █████╗ ██████╗  ██████╗██╗  ██╗██╗██╗   ██╗███████╗
#  ████╗ ████║██╔════╝╚══██╔══╝██╔═══██╗██║    ██║    ██╔══██╗██╔══██╗██╔════╝██║  ██║██║██║   ██║██╔════╝
#  ██╔████╔██║██║  ███╗  ██║   ██║   ██║██║ █╗ ██║    ███████║██████╔╝██║     ███████║██║██║   ██║█████╗
#  ██║╚██╔╝██║██║   ██║  ██║   ██║   ██║██║███╗██║    ██╔══██║██╔══██╗██║     ██╔══██║██║╚██╗ ██╔╝██╔══╝
#  ██║ ╚═╝ ██║╚██████╔╝  ██║   ╚██████╔╝╚███╔███╔╝    ██║  ██║██║  ██║╚██████╗██║  ██║██║ ╚████╔╝ ███████╗
#  ╚═╝     ╚═╝ ╚═════╝   ╚═╝    ╚═════╝  ╚══╝╚══╝     ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝
# https://github.com/PhoenixK7PB/mgtow-archive
#
# TODO: add torrent options
# TODO: add options to edit, remove and download specific channels
# TODO: compressing system
# TODO: move all config files to a single file
# TODO: re-make README.md

import json
import signal
import sys
import os
import tty
import termios
import fnmatch
import tarfile
import base64

import youtube_dl
import colorama
import qbittorrentapi

from pathlib import Path
from time import sleep


affirmative_choice = ["y", "yes", "s", "sim", "yeah", "yah", "ya"]  # affirmative choices, used on user interaction
negative_choice = ["n", "no", "nao", "na", "nop", "nah"]    # negative choices, used on user interaction

original_stdin_settings = termios.tcgetattr(sys.stdin)

download_archive = True

sorted_folders_names = ["subtitles", "thumbnails", "descriptions", "metadata", "videos", "annotations"]

warnings = 0
errors = []


class Color:
    """
    Return text with color using colorama.
    Pretty much straight forward to read.
    Just use Color().wantedColorOrBold(textToBeColoredOrBolded).
    reset() reset the last color usage
    """
    RED = colorama.Fore.RED
    YELLOW = colorama.Fore.YELLOW
    BLUE = colorama.Fore.BLUE
    GREEN = colorama.Fore.GREEN
    BOLD = '\033[1m'
    END = '\033[0m'

    def red(self, text):
        return self.RED + text

    def yellow(self, text):
        return self.YELLOW + text

    def blue(self, text):
        return self.BLUE + text

    def green(self, text):
        return self.GREEN + text

    def bold(self, text):
        return self.BOLD + text + self.END

    @staticmethod
    def reset():
        return colorama.Style.RESET_ALL


class Logger(object):

    @staticmethod
    def debug(msg):
        print(msg)

    @staticmethod
    def warning(msg):
        global warnings
        warnings += 1

    @staticmethod
    def error(msg):
        global errors
        errors.append(color.red(color.bold(str(msg))))

        print(color.red(color.bold(msg)))


class Json:
    """
    Handle JSON requests.
    """

    @staticmethod
    def encode(data, write_filename):
        """
        Encode a obj (if available) to a file
        Do NOT handle exceptions or errors
        :param data: Data obj to write on the file, should be compatible with JSON
        :param write_filename: Name of the file to write
        Should have ".json" at the end.
        :return: Nothing.
        """
        with open(write_filename, "w") as write_file:
            json.dump(data, write_file)

    @staticmethod
    def decode(read_filename, return_content=False):
        """
        Read a .json file and transfer the data to a global variable
        :param read_filename: Name of the file to be read, NEED the .json at the end
        :param return_content:  1 (default) for not returning the content inside the json file
                                0 for returning the content at the end
        :return: Make a global variable called "json_decode", all content in there
        If return_content is 1, does NOT return anything
        If return_content is 0, DOES return the content
        """
        global json_decode

        with open(read_filename) as json_data:
            json_decode = json.load(json_data)

            if return_content:
                return json_decode


class Organizer:
    def get_sort_type(self):
        try:
            global sort_type
            sort_type = Json.decode(config_dir + "sort_type.json", return_content=True)
        except FileNotFoundError:
            self.all_in_one(path)

    def sort_by_type(self, root_path):
        for channel in self.get_downloaded_channels(root_path):
            self.make_folder_sorted_directories(channel + "/")
            for file in os.listdir(channel):
                absolute_file_path = channel + "/" + file
                if os.path.isfile(absolute_file_path):
                    if fnmatch.fnmatch(file, "*.tar.gz"):
                        return
                    elif fnmatch.fnmatch(file, "*.jpg"):
                        os.rename(absolute_file_path, channel + "/thumbnails/" + file)
                    elif fnmatch.fnmatch(file, "*.description"):
                        os.rename(absolute_file_path, channel + "/descriptions/" + file)
                    elif fnmatch.fnmatch(file, "*.info.json"):
                        os.rename(absolute_file_path, channel + "/metadata/" + file)
                    elif fnmatch.fnmatch(file, "*.annotations.xml"):
                        os.rename(absolute_file_path, channel + "/annotations/" + file)
                    elif fnmatch.fnmatch(file, "*.mp4"):
                        os.rename(absolute_file_path, channel + "/videos/" + file)
                    if fnmatch.fnmatch(file, "*.vtt"):
                        os.rename(absolute_file_path, channel + "/subtitles/" + file)
                    elif fnmatch.fnmatch(file, "*.webm"):
                        os.rename(absolute_file_path, channel + "/videos/" + file)
                    elif fnmatch.fnmatch(file, "*.m4a"):
                        os.rename(absolute_file_path, channel + "/videos/" + file)
                    elif fnmatch.fnmatch(file, "*.mp3"):
                        os.rename(absolute_file_path, channel + "/videos/" + file)
                    elif fnmatch.fnmatch(file, "*.opus"):
                        os.rename(absolute_file_path, channel + "/videos/" + file)
                    elif fnmatch.fnmatch(file, "*.mkv"):
                        os.rename(absolute_file_path, channel + "/videos/" + file)
                elif os.path.isdir(absolute_file_path):
                    # handle?
                    pass
        Json.encode("sort_by_type", config_dir + "sort_type.json")
        self.get_sort_type()

    def all_in_one(self, root_path):
        for channel in self.get_downloaded_channels(root_path):
            for folder in os.listdir(channel):
                absolute_folder_path = channel + "/" + folder
                if os.path.isdir(absolute_folder_path) and folder in sorted_folders_names:
                    for file in os.listdir(absolute_folder_path):
                        os.rename(absolute_folder_path + "/" + file, channel + "/" + file)
            self.remove_folder_sorted_directories(channel + "/")
        Json.encode("all_in_one", config_dir + "sort_type.json")
        self.get_sort_type()

    @classmethod
    def remove_folder_sorted_directories(cls, channel_path):
        for folder in os.listdir(channel_path):
            absolute_folder_path = channel_path + "/" + folder
            if os.path.isdir(absolute_folder_path):
                try:
                    os.rmdir(absolute_folder_path)
                except OSError:
                    print(color.red(color.bold("\n    ERROR AT '%s':\n"
                                               "    DIRECTORY NOT EMPTY, NOT REMOVING IT!\n") % absolute_folder_path))

    @classmethod
    def make_folder_sorted_directories(cls, channel_path):
        for folder_name in sorted_folders_names:
            if not os.path.exists(channel_path + "/" + folder_name):
                os.makedirs(channel_path + "/" + folder_name)

    @classmethod
    def get_downloaded_channels(cls, root_path):
        downloaded_channels_list = []
        for directory in os.listdir(os.path.abspath(root_path)):
            if os.path.isdir(root_path + directory):
                downloaded_channels_list.append(root_path + directory)
        return downloaded_channels_list


class Compress:
    # TODO
    pass


class Format:
    def __init__(self):
        self.format_config = config_dir + "format_config.json"
        self.formats = {
            "mp4":              "mp4[height=720]/mp4[height<720]/mp4",
            "mp3":              "mp3",
            "bestaudio":        "bestaudio",
            "best":             "best",
        }

    def get_format(self, raw=False):
        if raw:
            try:
                return Json.decode(self.format_config, return_content=True)
            except FileNotFoundError:
                self.default_format()
        elif not raw:
            try:
                current_format = Json.decode(self.format_config, return_content=True)
                return list(self.formats.keys())[list(self.formats.values()).index(current_format)]
            except FileNotFoundError:
                self.default_format()

    def default_format(self):
        Json.encode("mp4[height=720]/mp4[height<720]/mp4", self.format_config)
        self.get_format()

    def mp4(self):
        Json.encode(self.formats["mp4"], self.format_config)

    def mp3(self):
        Json.encode(self.formats["mp3"], self.format_config)

    def bestaudio(self):
        Json.encode(self.formats["bestaudio"], self.format_config)

    def best(self):
        Json.encode(self.formats["best"], self.format_config)


class Torrent:
    def __init__(self):
        self.torrent_config_path = config_dir + "torrent_config.json"
        self.torrent_config_file = self.get_config()
        self.client_instance = self.get_client_instance()

    def make_default_config(self):
        default_config = {
            "ip": "localhost",
            "port": "8080",
            "username": "",
            "password": "",
        }
        Json.encode(default_config, self.torrent_config_path)
        self.get_config()

    def get_config(self):
        try:
            return Json.decode(self.torrent_config_path, return_content=True)
        except FileNotFoundError:
            self.make_default_config()

    def update_config(self, new_config_file):
        return Json.encode(new_config_file, self.torrent_config_path)

    def get_client_instance(self):
        host = self.torrent_config_file["ip"] + ":" + self.torrent_config_file["port"]
        username = self.torrent_config_file["username"]
        password = self.torrent_config_file["password"]
        return qbittorrentapi.Client(host=host, username=username, password=password)

    def client_auth_log_in(self):
        """
        Check login credentials
        :return: If login successful returns True, If login failed returns False
        """
        try:
            self.client_instance.auth_log_in(username=self.torrent_config_file["username"],
                                             password=self.torrent_config_file["password"])
            return True
        except qbittorrentapi.LoginFailed:
            return False
        except qbittorrentapi.Forbidden403Error:
            return False


    def client_version(self):
        return self.client_instance.app_version()


def clear():
    """
    check if the machine is windows or linux,
    then clear the screen
    :return: a clean screen :)
    """

    if os.name == "nt":
        os.system('cls')

    else:
        os.system('clear')


def signal_handler(signal, frame):
    """
    handler of CTRL + C, prints a blank line, then exit
    :param signal:
    :param frame:
    :return: prints a blank line and exit
    """
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_stdin_settings)
    # this line is somewhat useful if the user exit during the "press any key" thing,
    # because the "stdin" will be set to raw mode, if the user hit CTRL + C, the
    # terminal stays in raw mode, with he will be stuck, using this line, if the user
    # hit CTRL + C, the "stdin" will be restored (using the original_stdin_settings variable)
    # and he will not get stuck
    print("\n")
    sys.exit(0)


def wait_input():
    """
    this function will detect any key press, until that happens, the program will wait
    """
    print("Press " + color.yellow(color.bold("any key")) + " to continue...")
    tty.setcbreak(sys.stdin)    # set "stdin" in raw mode, no line buffering from here
    user_input = None   # used to control while loop, the user input will be None,
    # if the user input changes, the while loop should be broken
    while user_input is None:   # while the user input is None (e.i. no key press detect on "stdin"), wait...
        user_input = sys.stdin.read(1)[0]   # this will be reading "stdin" until a key is detected
        clear()     # this will only be reached when a key is detected, until that happens, this will not be reached
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_stdin_settings)    # set "stdin" to default (no raw input)


def enter_to_return():
    return color.yellow(color.bold("Enter")) + " to " + color.yellow(color.bold("return")) + "."


def exit_func():
    """
    this function should be called when exiting, first clear the screen, then exit
    :return: exits program and clear the screen
    """

    clear()
    sys.exit(0)


def show_menu():
    """
    function that prints the main menu options
    :return: menu banner with options
    """

    print(color.red(" ███╗   ███╗ ██████╗████████╗ ██████╗ ██╗    ██╗"))
    print(color.red(" ████╗ ████║██╔════╝╚══██╔══╝██╔═══██╗██║    ██║"))
    print(color.red(" ██╔████╔██║██║  ███╗  ██║   ██║   ██║██║ █╗ ██║"))
    print(color.red(" ██║╚██╔╝██║██║   ██║  ██║   ██║   ██║██║███╗██║"))
    print(color.red(" ██║ ╚═╝ ██║╚██████╔╝  ██║   ╚██████╔╝╚███╔███╔╝"))
    print(color.red(" ╚═╝     ╚═╝ ╚═════╝   ╚═╝    ╚═════╝  ╚══╝╚══╝  "))
    print(color.red(""))
    print(color.red("    █████╗ ██████╗  ██████╗██╗  ██╗██╗██╗   ██╗███████╗"))
    print(color.red("   ██╔══██╗██╔══██╗██╔════╝██║  ██║██║██║   ██║██╔════╝"))
    print(color.red("   ███████║██████╔╝██║     ███████║██║██║   ██║█████╗"))
    print(color.red("   ██╔══██║██╔══██╗██║     ██╔══██║██║╚██╗ ██╔╝██╔══╝"))
    print(color.red("   ██║  ██║██║  ██║╚██████╗██║  ██║██║ ╚████╔╝ ███████╗"))
    print(color.red("   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝"))
    print("                 by " + color.red(color.bold("PhoenixK7PB")))
    print(color.yellow(color.bold("1")) + ") Download video/playlist/channel  " +
                       color.red(color.bold("|")) + "  " + color.yellow(color.bold("conf")) + ") General configuration")
    print(color.yellow(color.bold("2")) + ") Channels                         " +
                       color.red(color.bold("|")) + "  ")
    print(color.yellow(color.bold("3")) + ") qBittorrent interface (v4.1+)    " +
                       color.red(color.bold("|")) + "  ")
    print(color.yellow(color.bold("0")) + ") Exit                             " +
                       color.red(color.bold("|")) + "  ")


def get_config_dir():
    global config_dir
    if not os.path.exists(str(Path.home()) + "/.config/mgtow-archive/"):  # check if config dir exists
        os.makedirs(str(Path.home()) + "/.config/mgtow-archive/")
    config_dir = str(Path.home()) + "/.config/mgtow-archive/"


def make_path():
    """
    create a JSON file on the program directory containing the path for downloaded videos,
    user can use home path
    :return: create a global variable called "path" containing the path, returns nothing
    """

    clear()
    print(color.red(color.bold("-------------------------MAKE-PATH--------------------------")))
    path_name = str(input("Type the " + color.yellow(color.bold("full path")) +
                          " for storing downloads...\n" +
                          color.yellow(color.bold("Enter")) + " to use your " +
                          color.yellow(color.bold("home path")) + "." + "\n>:"))

    if path_name == "":     # if user input is blank,
        clear()
        if not os.path.exists(str(Path.home())):    # check if user home exists,
            os.makedirs(str(Path.home()))   # if not, create it
        Json.encode(str(Path.home() + "/"), config_dir + "path.json")  # encode JSON file containing the path (home path in this case)

    else:   # if user input is not blank,
        clear()
        if not os.path.exists(path_name):   # check if user input path exists
            os.makedirs(path_name)  # if not, create it
        Json.encode(path_name + "/", config_dir + "path.json")     # encode JSON file containing the user path

    global path
    path = Json.decode(config_dir + "path.json", return_content=True)   # make a global variable containing the new path
    clear()


def get_path():
    """
    Should get a "path" for storing the downloaded content
    Uses json_handler,
    If not data could be found, calls make_path()
    :return: Make a global variable called "path",
    """
    get_config_dir()
    try:    # tries to decode path
        global path
        path = Json.decode(config_dir + "path.json", return_content=True)
        return path
    except FileNotFoundError:   # if the file is not founded, calls make_path() and makes it
        make_path()
        return path


youtube_config = {      # --------------------CHANGE-THIS!!!--------------------- #

    'logger':                   Logger(),           # Logger instance, don't change it!
    'download_archive':         get_path() + '/download_archive',   # Use download archive file, don't change it!

    'format':                   Format().get_format(raw=True),  # Video format code. See yt-dl for more info.
    'outtmpl':                  get_path() + '/%(uploader)s/%(title)s.%(ext)s',

    'restrictfilenames':        True,               # Do not allow "&" and spaces in file names
    'no_warnings':              True,               # Do not print out anything for warnings.
    'ignoreerrors':             True,               # Do not stop on download errors.
    'nooverwrites':             True,               # Prevent overwriting files.
    'writedescription':         True,               # Write the video description to a .description file
    'writeinfojson':            True,               # Write metadata to a json file
    'writethumbnail':           True,               # Write the thumbnail image to a file
    'writeautomaticsub':        True,               # Write the automatically generated subtitles to a file
    'writeannotations':         True,               # Write video annotations
    'verbose':                  False,              # Print additional info to stdout.
    'quiet':                    False,              # Do not print messages to stdout.
    'simulate':                 False,              # Do not download the video files.
    'skip_download':            False,              # Skip the actual download of the video file
    'noplaylist':               False,              # Download single video instead of a playlist if in doubt.
    'playlistrandom':           False,              # Download playlist items in random order.
    'playlistreverse':          False,              # Download playlist items in reverse order.
}


def set_path():
    """
    option for changing/making new path
    :return: nothing, just changes path global variable
    """
    clear()
    get_path()
    print(color.red(color.bold("------------------------CHANGE-PATH-------------------------")))
    print("Your current path is: " + color.yellow(color.bold(path)))
    new_path = str(input("\nType your new path...\n" + enter_to_return() +
                         "\n>:"))
    if new_path == "":  # check user input, if blank, return
        clear()
        return

    else:   # else: check, encode, change global variable path and returns
        if not os.path.exists(new_path):    # checks if new path exists,
            os.makedirs(new_path)   # if not, create it,
        Json.encode(new_path + "/", config_dir + "path.json")  # then encode it
        get_path()  # change global variable path
        clear()
        return


def set_compress_type():
    clear()
    print(color.red(color.bold("----------------------COMPRESSING-TYPE----------------------")))


def set_sorting_type():
    clear()
    organizer.get_sort_type()
    print(color.red(color.bold("------------------------SORTING-TYPE------------------------")))
    print(color.red(color.bold("1) All-in-one")) +
          ": This type of sorting will result in everything\ndownloaded in just one folder, only organized by channels."
          "\n%s: PATH/channel_name/downloaded_files\n" % color.yellow(color.bold("i.e.")))
    print(color.red(color.bold("2) Sort-by-type")) +
          ": This type of sorting will result in 6 folders:\n"
          "annotations, descriptions, metadata, videos, thumbnails, subtitles."
          "\n%s: PATH/channel_name/file_type/downloaded_files\n" % color.yellow(color.bold("i.e.")))
    print("Current sorting: %s" % color.red(color.bold(sort_type)))
    print(enter_to_return())
    sorting_choice = str(input("Choose:\n>:"))
    clear()
    if sorting_choice == "":
        return
    elif sorting_choice.lower() == "1":
        organizer.all_in_one(path)
    elif sorting_choice.lower() == "2":
        organizer.sort_by_type(path)
    wait_input()


def set_format():
    while True:
        clear()
        print(color.red(color.bold("-----------------------DOWNLOAD-FORMAT----------------------")))
        current_format = download_format.get_format()

        if current_format == "mp4":
            print(color.yellow(color.bold("1)")) + "    (" + color.red(color.bold("X")) + ") MP4")
        else:
            print(color.yellow(color.bold("1)")) + "    ( ) MP4")

        if current_format == "mp3":
            print(color.yellow(color.bold("2)")) + "    (" + color.red(color.bold("X")) + ") MP3")
        else:
            print(color.yellow(color.bold("2)")) + "    ( ) MP3")

        if current_format == "bestaudio":
            print(color.yellow(color.bold("3)")) + "    (" +
                  color.red(color.bold("X")) + ") Best audio only format avaliable")
        else:
            print(color.yellow(color.bold("3)")) +
                  "    ( ) Best audio only format avaliable")

        if current_format == "best":
            print(color.yellow(color.bold("4)")) + "    (" +
                  color.red(color.bold("X")) + ") Best format avaliable")
        else:
            print(color.yellow(color.bold("4)")) +
                  "    ( ) Best format avaliable")

        print(enter_to_return())
        format_choice = str(input(">:"))

        if format_choice.lower() == "":
            break
        elif format_choice.lower() == "1":
            download_format.mp4()
            download_format.get_format()
        elif format_choice.lower() == "2":
            download_format.mp3()
            download_format.get_format()
        elif format_choice.lower() == "3":
            download_format.bestaudio()
            download_format.get_format()
        elif format_choice.lower() == "4":
            download_format.best()
            download_format.get_format()
        else:
            clear()
            wait_input()

def config_handler():
    """
    this function is used to handle pretty much all configuration process on the program,
    this is pretty much straight forward and should be easy to read (ignore color calls)
    :return:  depends i guess :p
    """
    config_maintainer = True

    while config_maintainer:
        clear()
        print(color.red(color.bold("------------------------CONFIGURATION-----------------------")))
        print(color.red(color.bold("Changes to the download config must be done on the source code.")))
        print(color.yellow(color.bold("compress")) + ") Set compress style      " + color.red(color.bold("|")) +
              "  " + color.yellow(color.bold("NONE")))

        print(color.yellow(color.bold("  format")) + ") Set download format     " + color.red(color.bold("|")) +
              "  " + color.yellow(color.bold(download_format.get_format())))

        print(color.yellow(color.bold("    path")) + ") Set download path       " + color.red(color.bold("|")) +
              "  " + color.yellow(color.bold(path)))
        print(color.yellow(color.bold("    sort")) + ") Set sorting type        " + color.red(color.bold("|")) +
              "  " + color.yellow(color.bold(sort_type)))
        print(enter_to_return())
        config_choice = str(input(">:"))  # try to convert choice(str) to choice(int),
        if config_choice == "":
            clear()
            break

        elif config_choice.lower() == "path":
            set_path()
            continue

        elif config_choice.lower() == "compress":
            set_compress_type()
            continue

        elif config_choice.lower() == "sort":
            set_sorting_type()
            continue

        elif config_choice.lower() == "format":
            set_format()
            continue

        else:
            clear()
            wait_input()


def get_channels():
    """
    decode the JSON file containing the channels, if no JSON is found, return False
    :return: make a global called channels (dict) containing all channels on the JSON file,
    the dict data is NAME : URL
    """
    try:
        global channels
        channels = Json.decode(config_dir + "channels.json", return_content=True)

    except FileNotFoundError:
        clear()
        print(color.red(color.bold("----------------------------ERROR---------------------------")))
        print("No channels founded... maybe add one?")
        wait_input()
        return False


def add_channel(channel_name, channel_url):
    """
    add a channel to a JSON file on a dict like obj
    NAME : URL
    :param channel_name: channel name
    :param channel_url: channel url
    :return:  calls get_channels()
    """
    try:
        old_channels = Json.decode(config_dir + "channels.json", return_content=True)
        old_channels[channel_name] = channel_url
        Json.encode(old_channels, config_dir + "channels.json")
        get_channels()

    except FileNotFoundError:
        new_channel = {channel_name: channel_url}
        Json.encode(new_channel, config_dir + "channels.json")
        get_channels()


def youtube_download(url):
    """
    Download a channel using the config
    :param url: url of the channel being downloaded
    :return: nothing
    """
    youtube_dl.YoutubeDL(youtube_config).download([url])


def download_choice():
    """
    user interface for downloading videos
    :return:
    """
    clear()
    print(color.red(color.bold("--------------------------DOWNLOAD--------------------------")))
    videos_lst = []
    video_url = str(input("Type the URL to download.\n" + enter_to_return() + "\n>:"))

    if video_url == "":
        clear()
        return
    else:
        videos_lst.append(video_url)
        while True:
            download_another_one = str(input("\nDownload another one? [y/N]"))
            if download_another_one not in affirmative_choice:
                break
            else:
                video_url = str(input("\nType the URL to download.\n" + enter_to_return() + "\n>:"))
                if video_url == "":
                    clear()
                    break
                else:
                    videos_lst.append(video_url)

        use_download_archive = str(input("\nUse the download archive file for not repeating downloads? [Y/n]"))
        if use_download_archive in negative_choice:
            global download_archive
            download_archive = False
            youtube_config.pop("download_archive", None)

    clear()
    print(color.yellow(color.bold("CTRL + C")) +
          " to cancel download.\n")
    sleep(0.5)

    for url in videos_lst:
        youtube_download(url)

    if sort_type == "sort_by_type":
        print(color.yellow(color.bold("\n Re-applying sorting type...")))
        organizer.sort_by_type(path)
        print(color.yellow(color.bold(" DONE!")))

    if warnings >= 1:
        print("\n   Download fished with %d warnings..." % warnings)
    if len(errors) >= 1:
        print(color.red(color.bold("\n   Download fished with %s errors..." % str(len(errors)))))
        for error in errors:
            print(color.red(color.bold(error)))
    print()
    wait_input()


def channels_choice():
    """
    user interface for channels stuff
    :return:
    """
    channel_maintainer = True

    while channel_maintainer:
        clear()
        print(color.red(color.bold("--------------------------CHANNELS--------------------------")))
        print(color.yellow(color.bold("1")) + ") Search for new videos in every channel")
        print(color.yellow(color.bold("2")) + ") View channels")
        print(color.yellow(color.bold("3")) + ") Add a channel")
        print(enter_to_return())
        channel_choice = input(">:")

        try:
            channel_choice = int(channel_choice)

        except ValueError:
            if channel_choice.lower() == "":
                break
            else:
                clear()
                wait_input()

        if channel_choice == 1:
            clear()
            print(color.red(color.bold("----------------------DOWNLOAD-CHANNELS---------------------")))
            if get_channels() is False:
                continue

            print(color.yellow(color.bold("Found ")) +
                  color.red(color.bold(str(len(channels)) + " channels")) +
                  color.yellow(color.bold("...\n")))
            download_channels_choice = str(input(color.red(color.bold("All videos")) +
                                                 color.yellow(color.bold(" from ")) +
                                                 color.red(color.bold("all channels")) +
                                                 color.yellow(color.bold(" will be downloaded.")) +
                                                 color.yellow(color.bold("\nProceed? [y/N]")) +
                                                 "\n>:"))

            if download_channels_choice not in affirmative_choice:
                clear()
                continue

            clear()
            print(color.yellow(color.bold("CTRL + C")) +
                  " to cancel download.\n")
            sleep(0.5)

            channel_count = 0
            for channel in channels:
                channel_count += 1
                print()
                print("     Channel %d of %d" % (channel_count, len(channels)))
                print("     Channel: %s" % channel)
                print("     URL: %s" % channels[channel])
                print()
                sleep(0.25)
                youtube_download(channels[channel])

            if sort_type == "sort_by_type":
                print(color.yellow(color.bold("\nApplying sorting type...")))
                organizer.sort_by_type(path)
                print(color.yellow(color.bold(" DONE!")))

            if warnings >= 1:
                print("\n   Download fished with %d warnings..." % warnings)
            if len(errors) >= 1:
                print(color.red(color.bold("\n   Download fished with %s errors..." % str(len(errors)))))
                for error in errors:
                    print(color.red(color.bold(error)))
            print()
            wait_input()

        elif channel_choice == 2:
            clear()
            if get_channels() is False:
                continue

            print(color.red(color.bold("------------------------VIEW-CHANNELS-----------------------")))
            print("Found %s channels...\n" % color.yellow(color.bold(str(len(channels)))))
            count = 0

            for channel in channels:
                count += 1
                print("      %s) Name: %s\n"
                      "         URL:  %s" % (color.yellow(color.bold(str(count))), channel, channels[channel]))
                print()
            wait_input()

        elif channel_choice == 3:
            add_channel_maintainer = True

            while add_channel_maintainer:
                clear()
                print(color.red(color.bold("-------------------------ADD-CHANNEL------------------------")))
                print(color.yellow(color.bold("Leave everything blank to cancel.\n")))
                channel_name = str(input(color.yellow(color.bold("Name")) + " of the channel?\n>:"))
                channel_url = str(input(color.yellow(color.bold("\nLink")) + " of the channel?\n>:"))
                if channel_name and channel_url != "":
                    add_channel(channel_name, channel_url)
                else:
                    clear()
                    break

                add_another_channel_choice = str(input("\nAdd another channel? [y/N]\n>:"))
                if add_another_channel_choice not in affirmative_choice:
                    clear()
                    break


def torrent_handler():
    torrent_maintainer = True
    while torrent_maintainer:
        clear()
        print(color.red(color.bold("----------------------TORRENT-INTERFACE---------------------")))
        if torrent.client_auth_log_in():
            print("Login status: %s"
                  % color.green(color.bold("Successful")))
        else:
            print("Login status: %s  |  Enable bypass for clientes on the localhost."
                  % color.red(color.bold("Failed")))
        print()
        print(color.yellow(color.bold("1")) + ") Change login                     " +
              color.red(color.bold("|")) + "  %s:%s"
              % (torrent.get_config()["ip"], torrent.get_config()["port"]))
        print(enter_to_return())
        torrent_choice = str(input(">:"))

        if torrent_choice == "1":
            clear()
            print(color.red(color.bold("BE CAREFUL WHEN CHANGING THE LOGIN IP AND PORT!"
                                       "\nANY MISLEADING CHANGES COULD BE CATASTROPHIC!"
                                       "\nRemove the file '~/.config/mgtow-archive/torrent_config.json' "
                                       "if any errors occur.")))
            wait_input()
            while True:
                clear()
                print(color.red(color.bold("------------------------CHANGE-LOGIN------------------------")))
                if torrent.client_auth_log_in():
                    print("Login status: %s" % color.green(color.bold("Successful")))
                else:
                    print("Login status: %s" % color.red(color.bold("Failed")))
                print()
                print(color.yellow(color.bold("1")) + ") IP:        %s" % torrent.get_config()["ip"])
                print(color.yellow(color.bold("2")) + ") Port:      %s" % torrent.get_config()["port"])
                print(color.yellow(color.bold("3")) + ") Username:  %s" % torrent.get_config()["username"])
                print(color.yellow(color.bold("4")) + ") Password:  %s" % torrent.get_config()["password"])
                print(color.yellow(color.bold("0")) + ") Reset login to default")
                print(enter_to_return())
                change_login_choice = str(input(">:"))

                if change_login_choice == "1":
                    clear()
                    print(color.red(color.bold("--------------------------CHANGE-IP-------------------------")))
                    print(color.yellow(color.bold("Leave everything blank to cancel.\n")))
                    print("Current IP: %s" % torrent.get_config()["ip"])
                    print("\nEnter the new IP to the used.")
                    new_ip = str(input(">:"))
                    if new_ip == "":
                        return
                    else:
                        new_config = torrent.get_config()
                        new_config["ip"] = new_ip
                        torrent.update_config(new_config)

                elif change_login_choice == "2":
                    clear()
                    print(color.red(color.bold("-------------------------CHANGE-PORT------------------------")))
                    print(color.yellow(color.bold("Leave everything blank to cancel.\n")))
                    print("Current port: %s" % torrent.get_config()["port"])
                    print("\nEnter the new port to the used.")
                    new_port = str(input(">:"))
                    if new_port == "":
                        return
                    else:
                        new_config = torrent.get_config()
                        new_config["port"] = new_port
                        torrent.update_config(new_config)

                elif change_login_choice == "3":
                    clear()
                    print(color.red(color.bold("-----------------------CHANGE-USERNAME----------------------")))
                    print(color.yellow(color.bold("Leave everything blank to cancel.\n")))
                    print("Current username: %s" % torrent.get_config()["username"])
                    print("\nEnter the new username to the used.")
                    new_username = str(input(">:"))
                    if new_username == "":
                        return
                    else:
                        new_config = torrent.get_config()
                        new_config["username"] = new_username
                        torrent.update_config(new_config)

                elif change_login_choice == "4":
                    clear()
                    print(color.red(color.bold("-----------------------CHANGE-PASSWORD----------------------")))
                    print(color.yellow(color.bold("Leave everything blank to cancel.\n")))
                    print("Current password: %s" % torrent.get_config()["password"])
                    print("\nEnter the new password to the used.")
                    new_password = str(input(">:"))
                    if new_password == "":
                        return
                    else:
                        new_config = torrent.get_config()
                        new_config["password"] = new_password
                        torrent.update_config(new_config)

                elif change_login_choice == "0":
                    clear()
                    print(color.red(color.bold("--------------------RESET-TORRENT-CONFIG--------------------")))
                    torrent_reset_config_choice = str(input("This will undo all changes to the torrent configuration. "
                                                            "Proceed? [y/N]"))
                    if torrent_reset_config_choice in affirmative_choice:
                        torrent.make_default_config()
                    else:
                        return

                elif change_login_choice == "":
                    break
                else:
                    clear()
                    wait_input()

        elif torrent_choice == "":
            break
        else:
            clear()
            wait_input()


if __name__ == "__main__":
    colorama.init(autoreset=True)
    signal.signal(signal.SIGINT, signal_handler)

    # init instances
    color = Color()
    organizer = Organizer()
    download_format = Format()
    torrent = Torrent()
    compress = Compress()

    get_config_dir()
    get_path()
    organizer.get_sort_type()

    maintainer = True
    while maintainer:
        clear()
        show_menu()  # show menu
        choice = input(">:")  # wait for user input

        if choice == "":
            clear()
            continue

        try:
            choice = int(choice)  # try to convert choice(str) to choice(int),
            # this is needed because the normal input is a str

        except ValueError:  # if the int() parser cant convert, raises a ValueError, this take care if it
            if choice.lower() == "conf":
                config_handler()
                continue

            else:   # if user type something that is not an option, ignore and wait for another input
                clear()
                wait_input()
                continue

        if choice == 1:
            download_choice()

        elif choice == 2:
            channels_choice()

        elif choice == 3:
            torrent_handler()

        elif choice == 0:
            exit_func()
        else:
            clear()
            wait_input()
