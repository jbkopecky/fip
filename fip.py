import socket
import random
import json
import datetime
import subprocess
import sys
from collections import defaultdict


USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.85 Safari/537.36",
        "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
        ]


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def netcat(hostname, port, content):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((hostname, port))
    s.sendall(content.encode('utf-8'))
    s.shutdown(socket.SHUT_WR)
    out = []
    while True:
        data = s.recv(1024)
        if len(data) == 0:
            break
        out.append(data.decode('utf-8'))
    s.close()
    return "".join(out)


class Song(object):
    def __init__(self, data):
        self.title = data['title']
        self.youtube_link = data['lienYoutube']
        self.visual = data['visual']
        self.performers = data['performers']
        self.authors = data['authors']
        self.label = data['label']
        self.album_title = data['titreAlbum']
        self.year = data['anneeEditionMusique']
        self.start = datetime.datetime.fromtimestamp(data['start'])
        self.end = datetime.datetime.fromtimestamp(data['end'])

    def __str__(self):
        youtube_link = " - [" + self.youtube_link + "]" if self.youtube_link is not None else ""
        start = "%02i:%02i" % (self.start.hour, self.start.minute)
        end = "%02i:%02i" % (self.end.hour, self.end.minute)
        name = "%s - %s" % (self.title, self.performers)
        return start +  " - " + end + " | " + name + youtube_link

    def download(self, path="~/Music"):
        if self.youtube_link is None:
            print(" ** Sorry, no youtube link provided by FIP...")
        else:
            print(" ** Downloading song %s ..." % (self.title))
            command = ["youtube-dl"]
            command += ["--extract-audio", "--audio-format", "mp3"]
            command += ["--add-metadata"]
            command += ["-o", path + "/%(title)s.%(ext)s"]
            command += [self.youtube_link]
            print(" ".join(command))
            try:
                subprocess.call(command)
                print(" ** Done !")
            except OSError as e:
                if e.errno == os.errno.ENOENT:
                    print(" ** Please Install Youtube-dl")
                else:
                    print(" ** Error Downloading song...")


class FipDownloader(object):
    def __init__(self):
        self.host = "www.fipradio.fr"
        self.base_url = "/livemeta"
        self.port = 80
        self.http_version = "1.1"
        self.current_songs = []
        self.download_time = None

    def build_content(self, url):
        user_agent = random.choice(USER_AGENTS)
        content =  "GET %s HTTP/%s\r\n" % (url, self.http_version)
        content += "Host: %s\r\n" % self.host
        content += "User-Agent: %s\r\n" % user_agent
        content += "Accept: */*\r\n"
        content += "Connection: close\r\n\r\n"
        return content

    def build_url(self):
        url = self.base_url
        return url

    def get_metadata(self):
        url = self.build_url()
        content = self.build_content(url)
        response = netcat(self.host, self.port, content)
        data = response.split("\r\n")[-1]
        data = json.loads(data)
        return data

    def get_songs(self):
        data = self.get_metadata()
        self.download_time = datetime.datetime.now()
        ids = data['levels'][0]['items']
        cur_id = ids[data['levels'][0]['position']]
        for i in ids:
            _data = defaultdict(lambda: None, data['steps'][i])
            song = Song(_data)
            self.current_songs.append(song)

    def print_current_songs(self):
        now = datetime.datetime.now()
        for i,s in enumerate(self.current_songs):
            if s.start <= now < s.end:
                pre = " -> "
            else:
                pre = "    "
            print(pre+str(s))

    def current_song(self):
        now = datetime.datetime.now()
        out = self.current_songs[-2]
        for i,s in enumerate(self.current_songs):
            if s.start <= now < s.end:
                out = s
        return out


if __name__ == "__main__":
    fipdl = FipDownloader()
    fipdl.get_songs()
    fipdl.print_current_songs()
    current_song = fipdl.current_song()
    where = "~/Music"
    download = query_yes_no(" ** Do you want to download current song %s in %s ?" % (current_song.title, where))
    if download:
        current_song.download(path=where)
