import select
from threading import Thread
import socket
import os


class Conductor(Thread):

    def __init__(self, epoll_, clients):
        super(Conductor, self).__init__(daemon=True)
        self.epoll_ = epoll_
        self.clients = clients
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        self.sock.bind(('', 8080))
        self.sock.listen()

        while True:
            con, addr = self.sock.accept()
            con.setblocking(False)
            client = dict(filename='', file=None, buffer=b'', con=con)
            self.clients[con.fileno()] = client
            events = select.EPOLLIN
            self.epoll_.register(con.fileno(), events)
            print(str(addr) + ' connected as ' + str(con.fileno()))


class Server(Thread):

    def __init__(self, epoll_, clients):
        super(Server, self).__init__(daemon=True)
        self.epoll_ = epoll_
        self.clients = clients
        self.filenames = os.listdir(os.getcwd())

    def run(self):
        while True:
            events = self.epoll_.poll(0)
            for user, event in events:
                if event & select.EPOLLIN:
                    data = self.clients[user]['con'].recv(1024)
                    self.clients[user]['buffer'] += data
                    data = self.clients[user]['buffer']

                    if not data:
                        self.epoll_.modify(user, select.EPOLLOUT)
                        continue
                    if self.clients[user]['filename']:
                        self.clients[user]['file'].write(data)
                    else:
                        if b'\r\n\r\n' not in data:
                            continue
                        filename, body = data.split(b'\r\n\r\n', 1)
                        filename = filename.decode('utf-8')
                        copy = 1
                        while filename in self.filenames:
                            filename, type_ = filename.split('.')
                            filename = filename + '_copy' + str(copy) + '.' + type_
                            copy += 1
                        self.filenames += [filename]
                        self.clients[user]['filename'] = filename
                        self.clients[user]['file'] = open(filename, 'wb')
                        self.clients[user]['file'].write(body)
                    self.clients[user]['buffer'] = b''
                elif event & select.EPOLLOUT:
                    self.clients[user]['con'].send(b'Done')
                    self.epoll_.modify(user, select.EPOLLHUP)
                elif event & select.EPOLLHUP:
                    self.clients[user]['con'].close()
                    self.clients[user]['file'].close()
                    del self.clients[user]


def main():
    epoll_ = select.epoll()
    clients = {}
    Server(epoll_, clients).start()
    cond = Conductor(epoll_, clients)
    cond.start()
    cond.join()


if __name__ == '__main__':
    main()
