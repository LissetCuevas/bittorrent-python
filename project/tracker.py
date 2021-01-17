import json
import random
import threading
from project.utils import *
from collections import defaultdict
from project.node import Node
from project import modes
from project.messages.tracker_to_node import TrackerToNode

DEBUG_MODE = True


class Tracker:
    def __init__(self):
        self.nodes = []
        self.open_ports = (1024, 49151)  # available user ports
        self.tracker_s = create_socket(TRACKER_PORT)
        self.uploader_list = defaultdict(list)

    def add_node(self, node: Node):
        self.nodes.append(node)

    def give_port(self) -> int:
        rand_port = random.randint(self.open_ports[0], self.open_ports[1])
        return rand_port

    def handle_node(self, data, addr):
        packet = json.loads(data.decode())
        packet_mode = packet['mode']
        if packet_mode == modes.HAVE:
            self.add_uploader(packet, addr)
        elif packet_mode == modes.NEED:
            self.search_file(packet, addr)

    def listen(self):
        while True:
            data, addr = self.tracker_s.recvfrom(1024)
            t = threading.Thread(target=self.handle_node(data, addr))
            t.start()

    def start(self):
        t = threading.Thread(target=self.listen())
        t.daemon = True
        t.start()
        t.join()

    def add_uploader(self, packet, addr):
        node_name = packet['name']
        filename = packet['message']
        item = {
            'name': node_name,
            'ip': addr[0],
            'port': addr[1]
        }
        self.uploader_list[filename].append(json.dumps(item))
        self.uploader_list[filename] = list(set(self.uploader_list[filename]))
        if DEBUG_MODE:
            print("Current uploader list :", self.uploader_list)

    def search_file(self, packet, addr):
        node_name = packet['name']
        filename = packet['message']
        search_result = []
        for item_json in self.uploader_list[filename]:
            item = json.loads(item_json)
            search_result.append((item['ip'], item['port']))
        response = TrackerToNode(node_name, search_result, filename)
        s = create_socket(self.give_port())
        s.sendto(str.encode(response.get()), (addr[0], addr[1]))
        s.close()


def main():
    t = Tracker()
    t.start()


if __name__ == '__main__':
    main()
