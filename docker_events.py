# -*- coding: utf-8 -*-
import json
import docker
import logging

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)
logging.getLogger("docker").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)
    
    #
    #
    # status = data.get('status', '')
    #
    # if status == "start":
    #     container_id = data.get('id', '')
    #     if not container_id:
    #         continue
    #
    #     cfg = client.containers.get(container_id)
    #     #cfg = client.configs.get(container_id)
    #     print("---")
    #     print(cfg)
    #     print("---")

# https://github.com/jonhadfield/python-hosts
# from python_hosts.hosts import Hosts, HostsEntry
# hosts = Hosts(path='hosts_test')
# new_entry = HostsEntry(entry_type='ipv4', address='1.2.3.4', names=['www.example.com', 'example'])
# hosts.add([new_entry])
# hosts.write()


class DockerHosts(object):

    def __init__(self, containers):
        self.watch_containers = containers
        self.client = docker.from_env()
        self.containers = {}
        self._update_container_info()

    def _update_container_info(self):
        containers = self.client.containers.list()
        
        def _extract_data():
            for c in containers:
                
                if not self.is_watched_container(c.name):
                    logger.debug("Ignoring: %s (not in %s)", c.name, self.watch_containers)
                    continue
                
                logger.debug("Watched container: %s (%s)", c.id, c.name)
                yield c.id, {
                    'hostname': containers[0].attrs.get('Config', {}).get('Hostname', ''),
                    'networks': dict([
                        (network_name, network_config.get('IPAddress', None)) for network_name, network_config in c.attrs.get('NetworkSettings', {}).get('Networks', {}).items()
                    ])
                }
        self.containers = dict(_extract_data())
        logger.debug("Containers: %s", self.containers)
    
    def is_watched_container(self, container_name):
        return not self.watch_containers or container_name in self.watch_containers
    
    def run(self):
        for e in self.client.events():
            logger.debug("Event: %s", e)
        
            data = json.loads(e)
            
            status = data.get('status', '')
            cid = data.get('id', '')
            type = data.get('Type', '')
            action = data.get('Action', '')
            
            if (status == "create" or status == "die") and cid:
                self._update_container_info()
            
            # fixme: don't rely on self.client.containers.list()!!
            
            if type == 'network' and (action == 'connect' or action == 'disconnect'):
                # self._update_container_info()
                
                attributes = data.get('Actor', {}).get('Attributes', {})
                container_id = attributes.get('container', '')
                network_name = attributes.get('name', '')
                
                logger.info("EVENT: Container %s on network %s: %s", container_id, network_name, action)
                
                if container_id not in self.containers:
                    logger.info("Ignoring network event for container: %s", container_id)
                    continue
                    
                if action == 'connect':
                    self.container_connected(container_id, network_name)
                else:
                    self.container_disconnected(container_id, network_name)
    
    def container_connected(self, container_id, network_name):
        logger.info("Container %s connected to network %s", container_id, network_name)

        cfg = self.client.containers.get(container_id)
        ip_addr = cfg.attrs.get('NetworkSettings', {}).get('Networks').get(network_name, {}).get('IPAddress', None)
        
        logger.debug("Container %s: IP on network %s: %s", container_id, network_name, ip_addr)
        
        self.containers[container_id]['networks'][network_name] = ip_addr

    def container_disconnected(self, container_id, network_name):
        logger.info("Container %s disconnected from network %s", container_id, network_name)
        if network_name in self.containers[container_id]['networks']:
            del self.containers[container_id]['networks'][network_name]

DockerHosts(containers=['dummy', 'dummy2']).run()
