# -*- coding: utf-8 -*-
import json
import logging

import daiquiri
import docker
from python_hosts import Hosts, HostsEntry

daiquiri.setup(level=logging.WARNING)
logging.getLogger("docker").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class DockerHosts(object):

    def __init__(self, container_filter=None, network_filter=None, hosts_file=None, pattern=None):
        self.pattern = pattern
        self.hosts_file = hosts_file
        self.container_filter = lambda name: name in container_filter if container_filter else lambda name: True
        self.network_filter = lambda name: name in network_filter if network_filter else lambda name: True
        
        self.client = docker.from_env()
        self.containers = {}
        self.update_container_info()

    def update_container_info(self, container_id=None):
        previous_config = self.containers if container_id is None else self.containers.get(container_id)

        for c in self.client.containers.list({'id': container_id} if container_id else None):
            if not self.is_watched_container(c.name):
                continue
    
            logger.debug('Watched container: %s (%s)', c.id, c.name)
            container_hostname = c.attrs.get('Config', {}).get('Hostname', '')
            if c.id[:len(container_hostname)] == container_hostname:
                container_hostname = c.attrs.get('Name', '').lstrip('/')
            
            self.containers[c.id] = {
                'name': c.name,
                'hostname': container_hostname,
                'networks': dict([
                    (network_name, network_config.get('IPAddress', None)) for network_name, network_config in
                    c.attrs.get('NetworkSettings', {}).get('Networks', {}).items()
                ])
            }
            
        logger.info('Containers:')
        for cid, vars in self.containers.items():
            logger.info("%s: %s", cid, vars)
        
        self.write_hosts_entries(container_id, previous_config)

    def write_hosts_entries(self, container_id, previous_config):
        """
        :param container_id: May be None (= all containers)
        :param previous_config: Either None (no information available), a dict from self.containers or the value of self.containers. If
        it is a dict of a single container, container_id must be set. If it is the previous value of self.containers, container_id MUST NOT be set
        """
        if container_id:
            self.write_file_entry(self.containers.get(container_id, None), previous_config)
        else:
            for cid in set(list(self.containers.keys()) + list(previous_config.keys())):
                self.write_file_entry(self.containers.get(cid, None), previous_config.get(container_id, None))

    def write_file_entry(self, current_config=None, previous_config=None):
        f = Hosts(self.hosts_file)

        def _fmt(**kwargs):
            return self.pattern.format(**kwargs)

        def _gen_entries():
            for network_name, network_address in current_config.get('networks', {}).items():
                name = _fmt(name=current_config['name'], hostname=current_config['hostname'], network=network_name)
                if network_address and network_name:
                    logger.debug("Adding host entry %s <> %s", network_address, name)
                    yield HostsEntry(entry_type='ipv4', address=network_address, names=[name])

        for cfg in current_config, previous_config:
            if cfg is None:
                continue
                
            for _, addr in cfg.get('networks', {}).items():
                if addr:
                    logger.debug("Removing entries matching address: %s", addr)
                    f.remove_all_matching(address=addr)

            for network, _ in cfg.get('networks', {}).items():
                name = _fmt(name=cfg['name'], hostname=cfg['hostname'], network=network)
                logger.debug("Removing entries matching name: %s", name)
                f.remove_all_matching(name=name)

        if current_config:
            f.add(list(_gen_entries()))

        f.write()

    def is_watched_container(self, container_name):
        return self.container_filter(container_name)
    
    def is_watched_network(self, network_name):
        return self.network_filter(network_name)
    
    def register_container(self, container_id, container_name):
        # logger.debug('register_container(%s, %s)', container_id, container_name)
        if container_id not in self.containers:
            logger.debug("Registring new container: %s (%s)", container_name, container_id)
            self.containers[container_id] = {
                'name': container_name
            }
    
    def deregister_container(self, container_id):
        if container_id in self.containers:
            logger.info("De-registring container: %s", container_id)
            previous_config = self.containers.get(container_id, None)
            del self.containers[container_id]
            self.write_hosts_entries(container_id, previous_config)
       
    def run(self):
        for e in self.client.events():
            data = json.loads(e)
            
            type = data.get('Type', '')
            action = data.get('Action', '')
            event_object_id = data.get('id', '')

            actor = data.get('Actor', {})
            actor_attributes = actor.get('Attributes', {})
            actor_name = actor_attributes.get('name', '')
            actor_container_id = actor_attributes.get('container', '')

            if type not in ('container', 'network'):
                logger.info('IGNORING EVENT for %s', type)
                continue
            
            if type == 'container' and not self.is_watched_container(data.get('id')):
                logger.info('Ignoring (unwatched) event %s/%s', type, action)
                continue
            
            if type == 'network' and not self.is_watched_network(actor_name):
                logger.info('Ignoring (unwatched) event %s/%s', type, action)
                continue
            
            if type == 'container':
                if action in ('attach', 'start'):
                    self.register_container(event_object_id, actor_name)
                elif action in ('kill', 'die', 'stop'):
                    self.deregister_container(event_object_id)
                else:
                    continue
            
            if type == 'network':
                if action not in ('connect', 'disconnect'):
                    logger.debug('Ignore network event: %s/%s', type, action)
                    continue
            
            self.update_container_info(actor_container_id or event_object_id)
            

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
