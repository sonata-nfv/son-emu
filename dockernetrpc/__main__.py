import time
import logging
import rpc

logging.basicConfig(level=logging.DEBUG)


def main():
    rpc.start_server()

if __name__ == '__main__':
    main()
