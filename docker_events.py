# -*- coding: utf-8 -*-
import json

import daiquiri
import docker
import logging

daiquiri.setup(level=logging.DEBUG)
logging.getLogger("docker").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)

logger = logging.getLogger(__name__)
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

    def __init__(self, container_filter=None, network_filter=None):
        self.container_filter = [lambda name: name == x for x in container_filter] if container_filter else [lambda name: True]
        self.network_filter = [lambda name: name == x for x in network_filter] if network_filter else [lambda name: True]
        
        self.client = docker.from_env()
        self.containers = {}
        self._update_container_info()

    def _update_container_info(self):# todo: remove me
        containers = self.client.containers.list()
        
        def _extract_data():
            for c in containers:
                
                if not self.is_watched_container(c.name):
                    logger.debug("Ignoring: %s", c.name)
                    continue
                
                logger.debug("Watched container: %s (%s)", c.id, c.name)
                yield c.id, {
                    'name': c.name,
                    'hostname': containers[0].attrs.get('Config', {}).get('Hostname', ''),
                    'networks': dict([
                        (network_name, network_config.get('IPAddress', None)) for network_name, network_config in c.attrs.get('NetworkSettings', {}).get('Networks', {}).items()
                    ])
                }
        self.containers = dict(_extract_data())
        logger.debug("Containers: %s", self.containers)
    
    def update_container_info(self, container_id=None):
        
        query_filters = {'id': container_id} if container_id else None
        
        for c in self.client.containers.list(query_filters):
        
            if not self.is_watched_container(c.name):
                logger.debug("Ignoring: %s", c.name)
                continue
        
            logger.debug("Watched container: %s (%s)", c.id, c.name)
            self.containers[c.id] = {
                'name': c.name,
                'hostname': c.attrs.get('Config', {}).get('Hostname', ''),
                'networks': dict([
                    (network_name, network_config.get('IPAddress', None)) for network_name, network_config in
                    c.attrs.get('NetworkSettings', {}).get('Networks', {}).items()
                ])
            }
            
        logger.info("Containers:")
        for cid, vars in self.containers.items():
            logger.info("%s: %s", cid, vars)
    
    def is_watched_container(self, container_name):
        return any([f(container_name) for f in self.container_filter])
    
    def is_watched_network(self, network_name):
        return any([f(network_name) for f in self.network_filter])
    
    def register_container(self, container_id, container_name):
        if container_id not in self.containers:
            logger.info("Registring new container: %s (%s)", container_name, container_id)
            self.containers[container_id] = {
                'name': container_name
            }
    
    def deregister_container(self, container_id):
        if container_id in self.containers:
            logger.info("De-registring container: %s", container_id)
            del self.containers[container_id]
    
    def dump_container_infos(self, log_mark):
        logger.warning("------ (%s)", log_mark)
        for c in self.client.containers.list():
            logger.warning("%s -> %s", c.id, {
                'name': c.name,
                'hostname': c.attrs.get('Config', {}).get('Hostname', ''),
                'networks': dict([
                    (network_name, network_config.get('IPAddress', None)) for network_name, network_config in
                    c.attrs.get('NetworkSettings', {}).get('Networks', {}).items()
                ])
            })
    
    def run(self):
        for e in self.client.events():
            data = json.loads(e)
            logger.debug("Event: %s", data)

            status = data.get('status', '')
            cid = data.get('id', '')
            type = data.get('Type', '')
            action = data.get('Action', '')
            
            actor = data.get('Actor', {})
            actor_attributes = actor.get('Attributes', {})
            actor_container_name = actor_attributes.get('name', '')

            if not cid or not self.is_watched_container(actor_container_name):
                continue
            
            if status == "create":
                self.register_container(cid, actor_container_name)
            if status == "die":
                self.deregister_container(cid)
            if status == "start" and cid in self.containers:
                self.update_container_info(cid)
            
            # fixme: don't rely on self.client.containers.list()!!

            container_id = actor_attributes.get('container', '')
            network_name = actor_attributes.get('name', '')
            if type == "network" and not self.is_watched_network(network_name):
                logger.warning("Ignoring (unwatched network): %s", data)
                continue
            
            if action == 'connect' or action == 'disconnect':
                #logger.info("EVENT: Container %s on network %s: %s", container_id, network_name, action)
                
                if container_id in self.containers:
                    logger.warning("Network event on WATCHED CONTAINER: %s (%s): %s", container_id, action, self.containers.get(container_id))
                    self.dump_container_infos("network connect/disconnect")
                    
                
                
            #     # self._update_container_info()
            #
            #     attributes = data.get('Actor', {}).get('Attributes', {})
            #     container_id = attributes.get('container', '')
            #     network_name = attributes.get('name', '')
            #
            #     logger.info("EVENT: Container %s on network %s: %s", container_id, network_name, action)
            #
            #     if container_id not in self.containers:
            #         logger.info("Ignoring network event for container: %s", container_id)
            #         continue
            #
            #     if action == 'connect':
            #         self.container_connected(container_id, network_name)
            #     else:
            #         self.container_disconnected(container_id, network_name)
    
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

DockerHosts(container_filter=['dummy', 'dummy2'], network_filter=['bridge', 'test']).run()
