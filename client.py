import sys
import socket


def main():
    filename, address, port = sys.argv[1:]
    port = int(port)
    data = filename.encode('utf-8') + b'\r\n\r\n'
    with open(filename, 'rb') as f:
        data += f.read()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((address, port))
    data = [data[i:i+1024] for i in range(0, len(data), 1024)]
    len_ = len(data)
    for i, d in enumerate(data):
        sock.send(d)
        sys.stdout.write('\r')
        sys.stdout.write("[%-20s] %d%%" % ('='*int((i/len_)*20), (i/len_)*100))
        sys.stdout.flush()
    
    sys.stdout.write('\r')
    sys.stdout.write("[%-20s] %d%%" % ('='*20, 100))
    sys.stdout.flush()
    print('\nDone')

if __name__ == '__main__':
    main()
