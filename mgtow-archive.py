#  ███╗   ███╗ ██████╗████████╗ ██████╗ ██╗    ██╗     █████╗ ██████╗  ██████╗██╗  ██╗██╗██╗   ██╗███████╗
#  ████╗ ████║██╔════╝╚══██╔══╝██╔═══██╗██║    ██║    ██╔══██╗██╔══██╗██╔════╝██║  ██║██║██║   ██║██╔════╝
#  ██╔████╔██║██║  ███╗  ██║   ██║   ██║██║ █╗ ██║    ███████║██████╔╝██║     ███████║██║██║   ██║█████╗
#  ██║╚██╔╝██║██║   ██║  ██║   ██║   ██║██║███╗██║    ██╔══██║██╔══██╗██║     ██╔══██║██║╚██╗ ██╔╝██╔══╝
#  ██║ ╚═╝ ██║╚██████╔╝  ██║   ╚██████╔╝╚███╔███╔╝    ██║  ██║██║  ██║╚██████╗██║  ██║██║ ╚████╔╝ ███████╗
#  ╚═╝     ╚═╝ ╚═════╝   ╚═╝    ╚═════╝  ╚══╝╚══╝     ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝
# https://github.com/PhoenixK7PB/mgtow-archive
#
# TODO: add choose option for format when downloading
# TODO: add a logger that saves every error and prints it at the end of the download FINISH IT
# TODO: add torrent options
# TODO: add options to edit, remove and download specific channels
# TODO: move all config files to a single file
# TODO: re-make README.md
# TODO: put descriptions in one folder, thumbnails in another,  subtitles in another, videos in another
# TODO: add meta-data to videos or JSON
# TODO: setup logger object, print errors at the end of downloads
# TODO: add thumbnail and metadata to the video file
# TODO: add annotation, subtitle and metadata to default on default_options
# TODO: user interface for Organizer()

import json
import threading
import signal
import sys
import os
import tty
import termios
import fnmatch

import youtube_dl
import colorama

from pathlib import Path
from time import sleep


affirmative_choice = ["y", "yes", "s", "sim", "yeah", "yah", "ya"]  # affirmative choices, used on user interaction
negative_choice = ["n", "no", "nao", "na", "nop", "nah"]    # negative choices, used on user interaction

founded_videos_dict = {}    # leave empty, used on youtube_hooker
founded_videos_limit = 10    # limit of videos that can be founded before exiting, default is 10, SHOULD BE INT

original_stdin_settings = termios.tcgetattr(sys.stdin)

sorted_folders_names = ["subtitles", "thumbnails", "descriptions", "metadata", "videos", "annotations"]


class Color:
    """
    Return text with color using colorama.
    Pretty much straight forward to read.
    Just use Color().wantedColorOrBold(textToBeColoredOrBolded).
    reset() reset the last color usage (if you use this class and after it want to
    """
    RED = colorama.Fore.RED
    YELLOW = colorama.Fore.YELLOW
    BLUE = colorama.Fore.BLUE
    BOLD = '\033[1m'
    END = '\033[0m'

    def red(self, text):
        return self.RED + text

    def yellow(self, text):
        return self.YELLOW + text

    def blue(self, text):
        return self.BLUE + text

    def bold(self, text):
        return self.BOLD + text + self.END

    def reset(self):
        return colorama.Style.RESET_ALL

class Logger(object):
    # TODO
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)

class Json:
    """
    Handle JSON requests.
    """

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

    def decode(read_filename, return_content=1):
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

            if return_content == 0:
                return json_decode


class Organizer:
    def sort_by_folder(self, root_path):
        for channel in self.get_downloaded_channels(root_path):
            self.make_folder_sorted_directories(channel + "/")
            for file in os.listdir(channel):
                absolute_file_path = channel + "/" + file
                if os.path.isfile(absolute_file_path):
                    if fnmatch.fnmatch(file, "*.vtt"):
                        os.rename(absolute_file_path, channel + "/subtitles/" + file)
                    elif fnmatch.fnmatch(file, "*.jpg"):
                        os.rename(absolute_file_path, channel + "/thumbnails/" + file)
                    elif fnmatch.fnmatch(file, "*.description"):
                        os.rename(absolute_file_path, channel + "/descriptions/" + file)
                    elif fnmatch.fnmatch(file, "*.info.json"):
                        os.rename(absolute_file_path, channel + "/metadata/" + file)
                    elif fnmatch.fnmatch(file, "*.webm"):
                        os.rename(absolute_file_path, channel + "/videos/" + file)
                    elif fnmatch.fnmatch(file, "*.m4a"):
                        os.rename(absolute_file_path, channel + "/videos/" + file)
                    elif fnmatch.fnmatch(file, "*.mp4"):
                        os.rename(absolute_file_path, channel + "/videos/" + file)
                    elif fnmatch.fnmatch(file, "*.mp3"):
                        os.rename(absolute_file_path, channel + "/videos/" + file)
                    elif fnmatch.fnmatch(file, "*.opus"):
                        os.rename(absolute_file_path, channel + "/videos/" + file)
                    elif fnmatch.fnmatch(file, "*.mkv"):
                        os.rename(absolute_file_path, channel + "/videos/" + file)
                    elif fnmatch.fnmatch(file, "*.annotations.xml"):
                        os.rename(absolute_file_path, channel + "/annotations/" + file)
                elif os.path.isdir(absolute_file_path):
                    # handle?
                    pass
        wait_input()

    def all_in_one(self, root_path):
        for channel in self.get_downloaded_channels(root_path):
            for folder in os.listdir(channel):
                absolute_folder_path = channel + "/" + folder
                if os.path.isdir(absolute_folder_path) and folder in sorted_folders_names:
                    for file in os.listdir(absolute_folder_path):
                        os.rename(absolute_folder_path + "/" + file, channel + "/" + file)
            self.remove_folder_sorted_directories(channel + "/")
        wait_input()

    def remove_folder_sorted_directories(self, channel_path):
        for folder in os.listdir(channel_path):
            absolute_folder_path = channel_path + "/" + folder
            if os.path.isdir(absolute_folder_path):
                try:
                    os.rmdir(absolute_folder_path)
                except OSError:
                    print(color.red(color.bold("\n    ERROR AT '%s':\n"
                                               "    DIRECTORY NOT EMPTY, NOT REMOVING IT!\n") % absolute_folder_path))

    def make_folder_sorted_directories(self, channel_path):
        for folder_name in sorted_folders_names:
            if not os.path.exists(channel_path + "/" + folder_name):
                os.makedirs(channel_path + "/" + folder_name)

    def get_downloaded_channels(self, root_path):
        downloaded_channels_list = []
        for directory in os.listdir(os.path.abspath(root_path)):
            if os.path.isdir(root_path + directory):
                downloaded_channels_list.append(root_path + directory)
        return downloaded_channels_list


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


def make_config_dir():
    """
    make the configuration center directory at ~/.config/mgtow-archive
    :return:
    """
    # if not os.path.exists(str(Path.home()) + "/.config/mgtow-archive"):  # check if config dir exists,
    os.makedirs(str(Path.home()) + "/.config/mgtow-archive/")  # if not, create it


def get_config_dir():
    global config_dir
    if not os.path.exists(str(Path.home()) + "/.config/mgtow-archive/"):  # check if config dir exists
        make_config_dir()
        config_dir = str(Path.home()) + "/.config/mgtow-archive/"
    else:
        config_dir = str(Path.home()) + "/.config/mgtow-archive/"


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
    print(color.yellow(color.bold("1") + ") Download video/playlist/channel   " +
                       color.red(color.bold("|" + "  " + color.yellow(color.bold("conf") + ") Configure yt-dl")))))
    print(color.yellow(color.bold("2") + ") Channels                          " +
                       color.red(color.bold("|" + "  " + color.yellow(color.bold("path") + ") Set download path")))))
    print(color.yellow(color.bold("0") + ") Exit"))


def youtube_hooker(video):
    """
    log and check how much videos have been founded on the machine, this is used by every thread/daemon
    :param video: video being downloaded
    :return: if more than "X" videos have been founded on the machine, exit the current thread/download
    """

    if threading.current_thread() not in founded_videos_dict:
        # check if the current thread have already been logged on the dict,
        # if not, create a key using the current thread name and gives to it a value 0
        founded_videos_dict[threading.current_thread()] = 0

    if len(video) <= 4:
        # check if the video dict properties has more than 4 keys, this happens because when a video is founded, yt-dl
        # creates only 4 keys to it on the hooker dict
        founded_videos_dict[threading.current_thread()] += 1

    if founded_videos_dict[threading.current_thread()] >= founded_videos_limit:
        # if more than or equal than founded_videos_limit, exit the thread
        # this happens because threads/daemons consumes machine resources and time
        # if you want to download a full channel but you already have some videos, dont use the channels tab
        print("\n     " + color.yellow(color.bold("LIMIT OF VIDEOS FOUNDED FOR CURRENT CHANNEL,")) +
              "\n     " + color.red(color.bold("EXITING DAEMON: %s \n" % threading.current_thread())))
        sys.exit(0)


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
    path = Json.decode(config_dir + "path.json", return_content=0)   # make a global variable containing the new path
    clear()


def get_path():
    """
    Should get a "path" for storing the downloaded content
    Uses json_handler,
    If not data could be found, calls make_path()
    :return: Make a global variable called "path",
    """

    try:    # tries to decode path
        global path
        get_config_dir()
        path = Json.decode(config_dir + "path.json", return_content=0)
        return path

    except FileNotFoundError:   # if the file is not founded, calls make_path() and makes it
        make_path()
        return path


def change_path():
    """
    option for changing/making new path
    :return: nothing, just changes path global variable
    """

    clear()
    print(color.red(color.bold("------------------------CHANGE-PATH-------------------------")))
    get_path()
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


youtube_config = {      # --------------------CHANGE-THIS!!!--------------------- #

    'format':                   'bestaudio/best',   # Video format code. See options.py for more information.
    'outtmpl':                  get_path() + '/%(uploader)s/%(title)s.%(ext)s',
    'restrictfilenames':        True,               # Do not allow "&" and spaces in file names
    'no_warnings':              True,               # Do not print out anything for warnings.
    'ignoreerrors':             True,               # Do not stop on download errors.
    'nooverwrites':             True,               # Prevent overwriting files.
    'writedescription':         True,              # Write the video description to a .description file
    'writeinfojson':            True,
    'writethumbnail':           True,              # Write the thumbnail image to a file
    'writeautomaticsub':        True,              # Write the automatically generated subtitles to a file
    'writeannotations':         True,
    'verbose':                  False,              # Print additional info to stdout.
    'quiet':                    False,              # Do not print messages to stdout.
    'simulate':                 False,              # Do not download the video files.
    'skip_download':            False,              # Skip the actual download of the video file
    'noplaylist':               False,              # Download single video instead of a playlist if in doubt.
    'playlistrandom':           False,              # Download playlist items in random order.
    'playlistreverse':          False,              # Download playlist items in reverse order.
    'forceurl':                 False,              # Force printing final URL.
    'forcetitle':               False,              # Force printing title.
    'forceid':                  False,              # Force printing ID.
    'forcethumbnail':           False,              # Force printing thumbnail URL.
    'forcedescription':         False,              # Force printing description.
    'forcefilename':            False,              # Force printing final filename.
    'forceduration':            False,              # Force printing duration.
    'forcejson':                False,              # Force printing info_dict as JSON.
}

yt_list_of_channels_config = {      # --------------------CHANGE-THIS!!!--------------------- #

    'progress_hooks': [youtube_hooker],     # DONT CHANGE

    'format':                   'bestaudio/best',   # Video format code. See options.py for more information.
    'outtmpl':                  get_path() + '/%(uploader)s/%(title)s.%(ext)s',
    'restrictfilenames':        True,               # Do not allow "&" and spaces in file names
    'no_warnings':              True,               # Do not print out anything for warnings.
    'ignoreerrors':             False,               # Do not stop on download errors.
    'nooverwrites':             True,               # Prevent overwriting files.
    'writedescription':         True,              # Write the video description to a .description file
    'writethumbnail':           True,              # Write the thumbnail image to a file
    'writeautomaticsub':        False,              # Write the automatically generated subtitles to a file
    'verbose':                  False,              # Print additional info to stdout.
    'quiet':                    False,              # Do not print messages to stdout.
    'simulate':                 False,              # Do not download the video files.
    'skip_download':            False,              # Skip the actual download of the video file
    'noplaylist':               False,              # Download single video instead of a playlist if in doubt.
    'playlistrandom':           False,              # Download playlist items in random order.
    'playlistreverse':          False,              # Download playlist items in reverse order.
    'forceurl':                 False,              # Force printing final URL.
    'forcetitle':               False,              # Force printing title.
    'forceid':                  False,              # Force printing ID.
    'forcethumbnail':           False,              # Force printing thumbnail URL.
    'forcedescription':         False,              # Force printing description.
    'forcefilename':            False,              # Force printing final filename.
    'forceduration':            False,              # Force printing duration.
    'forcejson':                False,              # Force printing info_dict as JSON.
}

youtube_default_config = {      # -----------------DO-NOT-CHANGE-THIS!!!----------------- #

    'format':                   'bestaudio/best',   # Video format code. See options.py for more information.
    'outtmpl':                  get_path() + '/%(uploader)s/%(title)s.%(ext)s',
    'restrictfilenames':        True,               # Do not allow "&" and spaces in file names
    'no_warnings':              True,               # Do not print out anything for warnings.
    'ignoreerrors':             True,               # Do not stop on download errors.
    'nooverwrites':             True,               # Prevent overwriting files.
    'writedescription':         True,              # Write the video description to a .description file
    'writethumbnail':           True,              # Write the thumbnail image to a file
    'writeautomaticsub':        False,              # Write the automatically generated subtitles to a file
    'verbose':                  False,              # Print additional info to stdout.
    'quiet':                    False,              # Do not print messages to stdout.
    'simulate':                 False,              # Do not download the video files.
    'skip_download':            False,              # Skip the actual download of the video file
    'noplaylist':               False,              # Download single video instead of a playlist if in doubt.
    'playlistrandom':           False,              # Download playlist items in random order.
    'playlistreverse':          False,              # Download playlist items in reverse order.
    'forceurl':                 False,              # Force printing final URL.
    'forcetitle':               False,              # Force printing title.
    'forceid':                  False,              # Force printing ID.
    'forcethumbnail':           False,              # Force printing thumbnail URL.
    'forcedescription':         False,              # Force printing description.
    'forcefilename':            False,              # Force printing final filename.
    'forceduration':            False,              # Force printing duration.
    'forcejson':                False,              # Force printing info_dict as JSON.
}


def make_default_config():
    """
    function to reset the yt-dl config JSON
    changes yt_config variable, makes a new yt_config.json file
    :return: nothing
    """
    Json.encode(youtube_default_config, config_dir + "yt_config.json")
    global yt_config
    yt_config = Json.decode(config_dir + "yt_config.json", return_content=0)


def apply_config():
    """
    used to write-down new changes to the yt config
    :return: nothing
    """
    Json.encode(youtube_config, config_dir + "yt_config.json")
    global yt_config
    yt_config = Json.decode(config_dir + "yt_config.json", return_content=0)


def get_config():
    """
    access the json configuration file and make a global variable called yt_config
    :return: nothing
    """
    try:    # tries to decode the yt_config.json file
        global yt_config
        yt_config = Json.decode(config_dir + "yt_config.json", return_content=0)
    except FileNotFoundError:   # if the file doesnt exists, make a default one
        make_default_config()


def config_handler():
    """
    this function is used to handle pretty much all configuration process on the program,
    this is pretty much straight forward and should be easy to read (ignore color calls)
    :return:  depends i guess :p
    """
    config_maintainer = True

    while config_maintainer:
        clear()
        get_config()
        print(color.red(color.bold("-----------------------CONFIGURE-YT-DL----------------------")))
        print("Youtube-dl version: " + color.yellow(color.bold(youtube_dl.update.__version__)))
        print("\n" + color.yellow(color.bold("apply") + ") Apply changes (from code) using "'youtube_config.'))

        print(color.yellow(color.bold("reset") + ") Reset the config to default."))

        print(color.yellow(color.bold("see") + ") See current configuration options."))
        print(enter_to_return())
        config_choice = str(input(">:"))

        if config_choice == "":
            return

        elif config_choice.lower() == 'apply':
            clear()
            apply_config()
            print(color.red(color.bold("--------------------CONFIGURATION-APPLIED-------------------")))
            wait_input()
            return

        elif config_choice.lower() == 'reset':
            clear()
            print(color.red(color.bold("---------------------RESET-CONFIGURATION--------------------")))
            sure = str(input(color.yellow(color.bold("Current modifications will be ")) +
                             color.red(color.bold("lost")) + color.yellow(color.bold(".\n")) +
                             color.yellow(color.bold("Proceed? [y/N]")) + "\n>:"))
            if sure in affirmative_choice:
                make_default_config()
                continue
            else:
                continue

        elif config_choice.lower() == 'see':
            clear()
            get_config()
            print(color.red(color.bold("--------------------CONFIGURATION-OPTIONS-------------------")))
            print("Found " + color.yellow(color.bold(str(len(yt_config)))) +
                  " options...\n")
            for config in yt_config:
                print(color.yellow(color.bold(str(config)) + color.bold(": ") +
                                   color.red(color.bold(str(yt_config[config])))))
            print()
            wait_input()


def get_channels():
    """
    decode the JSON file containing the channels, if no JSON is found, return False
    :return: make a global called channels (dict) containing all channels on the JSON file,
    the dict data is NAME : URL
    """
    try:
        global channels
        channels = Json.decode(config_dir + "channels.json", return_content=0)

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
        old_channels = Json.decode(config_dir + "channels.json", return_content=0)
        old_channels[channel_name] = channel_url
        Json.encode(old_channels, config_dir + "channels.json")
        get_channels()

    except FileNotFoundError:
        new_channel = {channel_name: channel_url}
        Json.encode(new_channel, config_dir + "channels.json")
        get_channels()


def youtube_download(url):
    """
    Download a channel using the normal config
    :param url: url of the channel being downloaded
    :return: nothing
    """
    youtube_dl.YoutubeDL(yt_config).download([url])


def youtube_channel_download(url):
    """
    Download a channel using the config for channels (calls a progress hooker)
    :param url: url of the channel being downloaded
    :return: nothing
    """
    youtube_dl.YoutubeDL(yt_list_of_channels_config).download([url])


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
            download_another_one = input(str("Download another one? [y/N]"))
            if download_another_one not in affirmative_choice:
                break
            else:
                video_url = str(input("Type the URL to download.\n>:"))
                videos_lst.append(video_url)
    videos_threads = []
    for url in videos_lst:
        video_thread = threading.Thread(target=youtube_download, args=(url,),
                                        daemon=True)
        videos_threads.append(video_thread)
    if len(videos_lst) >= 2:
        print(color.red(color.bold("\nStarting threads...\n")))
    else:
        print(color.red(color.bold("\nStarting thread...\n")))
    sleep(1)
    for video_thread in videos_threads:
        video_thread.start()
    for video_thread in videos_threads:
        while video_thread.is_alive():
            pass
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
                  " to cancel download.\n" +
                  color.yellow(color.bold("ENTER")) +
                  " to resume program after the download is finished.")
            sleep(2)
            channel_count = 0
            videos_threads = []
            for channel in channels:
                channel_count += 1
                print()
                print("     Channel %d of %d" % (channel_count, len(channels)))
                print("     Channel: %s" % channel)
                print("     URL: %s" % channels[channel])
                print()
                sleep(0.25)
                video_thread = threading.Thread(target=youtube_channel_download, args=(channels[channel],),
                                                daemon=True)
                videos_threads.append(video_thread)

            print(color.red(color.bold("\nStarting threads...\n")))
            sleep(1)
            for video_thread in videos_threads:
                video_thread.start()
            for video_thread in videos_threads:
                while video_thread.is_alive():
                    pass
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


if __name__ == "__main__":
    colorama.init(autoreset=True)
    signal.signal(signal.SIGINT, signal_handler)
    color = Color()
    get_config_dir()
    get_config()
    get_path()
    Organizer().all_in_one(path)

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
            if choice.lower() == "path":
                change_path()
                continue

            elif choice.lower() == "conf":
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
            pass
            # TODO start torrent stuff?
        elif choice == 0:
            exit_func()
        else:
            clear()
            wait_input()
