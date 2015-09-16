import os
import inspect

def EnsimeInitPath():
    path = os.path.abspath(inspect.getfile(inspect.currentframe()))
    if path.endswith('/rplugin/python/ensime.py'): # nvim rplugin
        sys.path.append(os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(path)))))
    elif path.endswith('/autoload/ensime.vim.py'): # vim plugin
        sys.path.append(os.path.join(
            os.path.dirname(os.path.dirname(path))))

EnsimeInitPath()

import vim
import json
import subprocess
import re
import logging
import time
import datetime
import thread
import inspect
from ensime_launcher import EnsimeLauncher
from websocket import create_connection
import Queue

class EnsimeClient(object):
    def log(self, what):
        log_dir = "/tmp/"
        if os.path.isdir(self.ensime_cache):
            log_dir = self.ensime_cache
        f = open(log_dir + "ensime-vim.log", "a")
        f.write("{}: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), what))
        f.close()
    def unqueue_poll(self):
        while True:
            if self.ws != None:
                result = self.ws.recv()
                self.queue.put(result)
            time.sleep(1)
    def __init__(self, vim, config_path):
        self.config_path = os.path.abspath(config_path)

        project_root = os.path.dirname(self.config_path)

        self.ensime_cache = os.path.join(project_root, ".ensime_cache")
        self.log("__init__: in")
        self.log("config_path: {}".format(self.config_path))
        self.callId = 0
        self.browse = False
        self.vim = vim
        self.matches = []
        self.is_setup = False
        self.suggests = None
        self.ensime = None
        self.no_teardown = False
        self.open_definition = False
        self.ws = None
        self.queue = Queue.Queue()
        thread.start_new_thread(self.unqueue_poll, ())
    def ensime_bridge(self, action):
        binary = os.environ.get("ENSIME_BRIDGE")
        if binary == None: binary = "ensime_bridge"
        binary = (binary + " " + action)
        self.log("ensime_bridge: lanching " + binary) 
        subprocess.Popen(binary.split())
    def start_ensime_launcher(self):
        if self.ensime == None:
            self.ensime = EnsimeLauncher(self.config_path, self.vim)
        if self.ensime.classpath != None:
            self.log("starting up ensime")
            self.message("ensime startup")
            self.ensime.run()
            return True
        else:
           self.log("launching EnsimeLauncher.setup()")
           self.ensime.setup()
           self.log("done launching EnsimeLauncher.setup()")
        return False
    def stop_ensime_launcher(self):
        self.ensime.stop()
        f = open(self.ensime_cache + "server.pid")
        pid = f.read()
        f.close()
        self.vim.command("!kill {}".format(pid))
    # @neovim.autocmd('VimLeave', pattern='*.scala', eval='expand("<afile>")', sync=True)
    def teardown(self, filename):
        self.log("teardown: in")
        if os.path.exists(self.config_path) and not self.no_teardown:
            self.stop_ensime_launcher()
            #self.ensime_bridge("stop")
    def setup(self):
        self.log("setup: in")
        if os.path.exists(self.config_path) and not self.is_setup:
            if self.start_ensime_launcher():
                self.vim.command("set completefunc=EnCompleteFunc")
                self.is_setup = True
        if self.ensime_is_ready() and self.ws == None:
            self.ws = create_connection("ws://127.0.0.1:{}/jerky".format(
                self.get_cache_port("http")))
    def get_cache_port(self, where):
        self.log("get_cache_port: in")
        f = open(self.ensime_cache + where)
        port = f.read()
        f.close()
        return port.replace("\n", "")
    def send(self, what):
        self.log("send: in")
        if self.ws == None:
            self.message("still initializing")
        else:
            self.log("send: {}".format(what))
            self.ws.send(what + "\n")
    def cursor(self):
        self.log("cursor: in")
        return self.vim.current.window.cursor
    def path(self):
        self.log("path: in")
        return self.vim.current.buffer.name
    def path_start_size(self, what, where = "range"):
        self.log("path_start_size: in")
        self.vim.command("normal e")
        e = self.cursor()[1]
        self.vim.command("normal b")
        b = self.cursor()[1]
        s = e - b
        self.send_at_point(what, self.path(), self.cursor()[0], b + 1, s, where)
    def get_position(self, row, col):
        result = col -1
        f = open(self.path())
        result += sum([len(f.readline()) for i in range(row - 1)])
        f.close()
        return result
    def complete(self):
        self.log("complete: in")
        content = self.vim.eval('join(getline(1, "$"), "\n")')
        pos = self.get_position(self.cursor()[0], self.cursor()[1] + 1)
        self.send_request({"point": pos, "maxResults":100,
            "typehint":"CompletionsReq",
            "caseSens":True,
            "fileInfo": {"file": self.path(), "contents": content},
            "reload":False})
    def send_at_point(self, what, path, row, col, size, where = "range"):
        i = self.get_position(row, col)
        self.send_request({"typehint" : what + "AtPointReq",
            "file" : path,
            where : {"from": i,"to": i + size}})
    # @neovim.command('EnNoTeardown', range='', nargs='*', sync=True)
    def do_no_teardown(self, args, range = None):
        self.log("do_no_teardown: in")
        self.no_teardown = True
    # @neovim.command('EnTypeCheck', range='', nargs='*', sync=True)
    def type_check_cmd(self, args, range = None):
        self.log("type_check_cmd: in")
        self.type_check("")
    # @neovim.command('EnType', range='', nargs='*', sync=True)
    def type(self, args, range = None):
        self.log("type: in")
        self.path_start_size("Type")
    def ensime_is_ready(self):
        self.log("ready: in")
        return os.path.exists(self.ensime_cache + "http")
    def symbol_at_point_req(self, open_definition):
        self.open_definition = open_definition
        pos = self.get_position(self.cursor()[0], self.cursor()[1] + 1)
        self.send_request({
            "point": pos, "typehint":"SymbolAtPointReq", "file":self.path()})
    # @neovim.command('EnDeclaration', range='', nargs='*', sync=True)
    def open_declaration(self, args, range = None):
        self.log("open_declaration: in")
        self.symbol_at_point_req(True)
    # @neovim.command('EnSymbol', range='', nargs='*', sync=True)
    def symbol(self, args, range = None):
        self.log("symbol: in")
        self.symbol_at_point_req(True)
    # @neovim.command('EnDocUri', range='', nargs='*', sync=True)
    def doc_uri(self, args, range = None):
        self.log("doc_uri: in")
        self.path_start_size("DocUri", "point")
    # @neovim.command('EnDocBrowse', range='', nargs='*', sync=True)
    def doc_browse(self, args, range = None) :
        self.log("browse: in")
        self.browse = True
        self.doc_uri(args, range = None)
    def read_line(self, s):
        self.log("read_line: in")
        ret = ''
        while True:
            c = s.recv(1)
            if c == '\n' or c == '':
                break
            else:
                ret += c
        return ret
    def message(self, m):
        self.log("message: in")
        self.vim.command("echo '{}'".format(m))
    def handle_new_scala_notes_event(self, notes):
        for note in notes:
            l = note["line"]
            c = note["col"] - 1
            e = note["col"] + (note["end"] - note["beg"])
            self.matches.append(self.vim.eval(
                "matchadd('EnError', '\\%{}l\\%>{}c\\%<{}c')".format(l, c, e)))
            self.message(note["msg"])
    def handle_string_response(self, payload):
        url = "http://127.0.0.1:{}/{}".format(self.get_cache_port("http"),
                payload["text"])
        if self.browse:
            subprocess.Popen([os.environ.get("BROWSER"), url])
            self.browse = False
        self.message(url)
    def handle_completion_info_list(self, completions):
        self.suggests = [completion["name"] for completion in completions]
    def handle_payload(self, payload):
        self.log("handle_payload: in")
        typehint = payload["typehint"]
        if typehint == "SymbolInfo":
            self.message(payload["declPos"]["file"])
            if self.open_definition:
                self.vim.command(":vsplit {}".format(
                    payload["declPos"]["file"]))
        elif typehint == "IndexerReadyEvent":
            self.message("ensime indexer ready")
        elif typehint == "AnalyzerReadyEvent":
            self.message("ensime analyzer ready")
        elif typehint == "NewScalaNotesEvent":
            self.handle_new_scala_notes_event(payload["notes"])
        elif typehint == "BasicTypeInfo":
            self.message(payload["fullName"])
        elif typehint == "StringResponse":
            self.handle_string_response(payload)
        elif typehint == "CompletionInfoList":
            self.handle_completion_info_list(payload["completions"])
    def send_request(self, request):
        self.log("send_request: in")
        self.send(json.dumps({"callId" : self.callId,"req" : request}))
        self.callId += 1
    # @neovim.autocmd('BufWritePost', pattern='*.scala', eval='expand("<afile>")', sync=True)
    def type_check(self, filename):
        self.log("type_check: in")
        self.send_request({"typehint": "TypecheckFilesReq",
            "files" : [self.path()]})
        for i in self.matches:
            self.vim.eval("matchdelete({})".format(i))
        self.matches = []
    # @neovim.autocmd('CursorHold', pattern='*.scala', eval='expand("<afile>")', sync=True)
    def on_cursor_hold(self, filename):
        self.log("on_cursor_hold: in")
        self.unqueue(filename)
        self.vim.command('call feedkeys("f\e")')
    # @neovim.autocmd('CursorMoved', pattern='*.scala', eval='expand("<afile>")', sync=True)
    def unqueue(self, filename):
        self.log("unqueue: in")
        self.setup()
        if self.ws == None: return
        while True:
            if self.queue.empty():
                break
            result = self.queue.get(False)
            self.log("unqueue: result received {}".format(str(result)))
            if result == None or result == "nil":
                self.log("unqueue: nil or None received")
                break
            _json = json.loads(result)
            if _json["payload"] != None:
                self.handle_payload(_json["payload"])
        self.log("unqueue: before close")
        self.log("unqueue: after close")
    def autocmd_handler(self, filename):
        self._increment_calls()
        self.vim.current.line = (
            'Autocmd: Called %s times, file: %s' % (self.calls, filename))
    # @neovim.function('EnCompleteFunc', sync=True)
    def complete_func(self, args):
        if args[0] == '1':
            self.complete()
            line = self.vim.eval("getline('.')")
            start = self.cursor()[1] - 1
            pattern = re.compile('\a')
            while start > 0 and pattern.match(line[start - 1]):
                start -= 1
            return start
        else:
            while True:
                if self.suggests != None:
                    break
                self.unqueue("")
            result = []
            pattern = re.compile('^' + args[1])
            for m in self.suggests:
                if pattern.match(m):
                    result.append(m)
            self.suggests = None
            return result

class Ensime(object):
    def __init__(self, vim):
        self.vim = vim
        self.no_teardown = False
        self.clients = {} # .ensime path => ensime server process

    def __message__(self, m):
        # TODO: escape m
        self.vim.command("echo '{}'".format(m))

    def teardown_all(self):
        for c in self.clients.values():
            c.teardown()

    def current_client(self):
        config_path = self.find_config_path(vim.eval("expand('%:p')"))
        if config_path == None:
            return None
        else:
            return self.client_for(config_path)

    def client_for(self, config_path):
        abs_path = os.path.abspath(config_path)
        if abs_path in self.clients:
            return self.clients[abs_path]
        else:
            self.clients[abs_path] = EnsimeClient(vim, config_path)
            return self.clients[abs_path]

    def find_config_path(self, path):
        abs_path = os.path.abspath(path)
        config_path = os.path.join(abs_path, '.ensime')

        if abs_path == os.path.abspath('/'):
            return None
        elif os.path.isfile(config_path):
            return config_path
        else:
            return self.find_config_path(os.path.dirname(abs_path))

    def with_current_client(self, proc):
        c = self.current_client()
        if c == None:
            self.__message__("Ensime server not loaded for this project.")
        else:
            return proc(c)

    def current_offset_range(self):
        return ['', 0, 0]

    def update(self):
        for c in self.clients.values():
            c.update()

    def command_en_no_teardown(self, _):
        self.no_teardown = True

    def command_en_type_check(self, _):
        self.with_current_client(lambda c: c.type_check())

    def command_en_type(self, _):
        self.with_current_client(lambda c:
                c.type_at_point(self.current_offset_range()))

    def command_en_declaration(self, _):
        self.with_current_client(lambda c:
                c.symbol_at_point(self.current_offset_range()))

    def command_en_symbol(self, _):
        self.command_en_declaration()

    def command_en_doc_uri(self, _):
        # todo
        None

    def command_en_doc_browse(self, _):
        # todo
        None

    def autocmd_vim_leave(self, _):
        if not self.no_teardown:
            self.teardown_all()

    def autocmd_buf_write_post(self, _):
        self.command_en_type_check()

    def autocmd_cursor_hold(self, _):
        self.update()

    def autocmd_cursor_moved(self, _):
        self.update()

    def function_en_complete_func(self, args):
        self.with_current_client(lambda c: c.complete_func(args))

ensime_plugin = Ensime(vim)
