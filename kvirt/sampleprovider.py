#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Base Kvirt serving as interface for the virtualisation providers
"""

# general notes
# most functions should either return
# return {'result': 'success'}
# or
# return {'result': 'failure', 'reason': reason}
# for instance
# return {'result': 'failure', 'reason': "VM %s not found" % name}


# your base class __init__ needs to define conn attribute and set it to None
# when backend cannot be reached
# it should also set debug from the debug variable passed in kcli client
class Kbase(object):
    """

    """
    def __init__(self, host='127.0.0.1', port=None, user='root', debug=False):
        return

# should cleanly close your connection, if needed
    def close(self):
        """

        :return:
        """
        print("not implemented")
        return

    def exists(self, name):
        """

        :param name:
        :return:
        """
        return

    def net_exists(self, name):
        """

        :param name:
        :return:
        """
        print("not implemented")
        return

    def disk_exists(self, pool, name):
        """

        :param pool:
        :param name:
        """
        print("not implemented")

    def create(self, name, virttype='kvm', profile='', flavor=None, plan='kvirt',
               cpumodel='Westmere', cpuflags=[], numcpus=2, memory=512,
               guestid='guestrhel764', pool='default', template=None,
               disks=[{'size': 10}], disksize=10, diskthin=True,
               diskinterface='virtio', nets=['default'], iso=None, vnc=False,
               cloudinit=True, reserveip=False, reservedns=False,
               reservehost=False, start=True, keys=None, cmds=[], ips=None,
               netmasks=None, gateway=None, nested=True, dns=None, domain=None,
               tunnel=False, files=[], enableroot=True, alias=[], overrides={},
               tags=None):
        """

        :param name:
        :param virttype:
        :param profile:
        :param flavor:
        :param plan:
        :param cpumodel:
        :param cpuflags:
        :param numcpus:
        :param memory:
        :param guestid:
        :param pool:
        :param template:
        :param disks:
        :param disksize:
        :param diskthin:
        :param diskinterface:
        :param nets:
        :param iso:
        :param vnc:
        :param cloudinit:
        :param reserveip:
        :param reservedns:
        :param reservehost:
        :param start:
        :param keys:
        :param cmds:
        :param ips:
        :param netmasks:
        :param gateway:
        :param nested:
        :param dns:
        :param domain:
        :param tunnel:
        :param files:
        :param enableroot:
        :param alias:
        :param overrides:
        :param tags:
        :return:
        """
        print("not implemented")
        return {'result': 'success'}

    def start(self, name):
        """

        :param name:
        :return:
        """
        print("not implemented")
        return {'result': 'success'}

    def stop(self, name):
        """

        :param name:
        :return:
        """
        print("not implemented")
        return {'result': 'success'}

    def snapshot(self, name, base, revert=False, delete=False, listing=False):
        """

        :param name:
        :param base:
        :param revert:
        :param delete:
        :param listing:
        :return:
        """
        print("not implemented")
        return

    def restart(self, name):
        """

        :param name:
        :return:
        """
        print("not implemented")
        return {'result': 'success'}

    def report(self):
        """

        :return:
        """
        print("not implemented")
        return

    def status(self, name):
        """

        :param name:
        :return:
        """
        print("not implemented")
        return

# should return a sorted list of name, state, ip, source, plan, profile, report
    def list(self):
        """

        :return:
        """
        print("not implemented")
        return

    def console(self, name, tunnel=False):
        """

        :param name:
        :param tunnel:
        :return:
        """
        print("not implemented")
        return

    def serialconsole(self, name):
        """

        :param name:
        :return:
        """
        print("not implemented")
        return

# should generate info in a dict and then pass it to
# print_info(yamlinfo, output=output, fields=fields, values=values)
# from kvirt.common where:
# yamlinfo is the dict
# with the following keys (you can omit the ones you want)
# name
# autostart
# plan
# profile
# template
# ip
# memory
# cpus
# creationdate
# nets list  of
# {'device': device, 'mac': mac, 'net': network, 'type': network_type}
# disks list of
# {'device': device, 'size': disksize, 'format': diskformat,
# 'type': drivertype, 'path': path}
# snapshots list of {'snapshot': snapshot, current: current}
# fields should be split with fields.split(',')
    def info(self, name, output='plain', fields=None, values=False):
        """

        :param name:
        :param output:
        :param fields:
        :param values:
        :return:
        """
        print("not implemented")
        return {'result': 'success'}

# should return ip string
    def ip(self, name):
        """

        :param name:
        :return:
        """
        print("not implemented")
        return None

# should return a list of available templates, or isos ( if iso is set to True
    def volumes(self, iso=False):
        """

        :param iso:
        :return:
        """
        print("not implemented")
        return

    def delete(self, name, snapshots=False):
        """

        :param name:
        :param snapshots:
        :return:
        """
        print("not implemented")
        return {'result': 'success'}

    def clone(self, old, new, full=False, start=False):
        """

        :param old:
        :param new:
        :param full:
        :param start:
        :return:
        """
        print("not implemented")
        return

    def update_metadata(self, name, metatype, metavalue):
        """

        :param name:
        :param metatype:
        :param metavalue:
        :return:
        """
        print("not implemented")
        return

    def update_memory(self, name, memory):
        """

        :param name:
        :param memory:
        :return:
        """
        print("not implemented")
        return

    def update_cpu(self, name, numcpus):
        """

        :param name:
        :param numcpus:
        :return:
        """
        print("not implemented")
        return

    def update_start(self, name, start=True):
        """

        :param name:
        :param start:
        :return:
        """
        print("not implemented")
        return

    def update_information(self, name, information):
        """

        :param name:
        :param information:
        :return:
        """
        print("not implemented")
        return

    def update_iso(self, name, iso):
        """

        :param name:
        :param iso:
        :return:
        """
        print("not implemented")
        return

    def create_disk(self, name, size, pool=None, thin=True, template=None):
        """

        :param name:
        :param size:
        :param pool:
        :param thin:
        :param template:
        :return:
        """
        print("not implemented")
        return

    def add_disk(self, name, size, pool=None, thin=True, template=None,
                 shareable=False, existing=None):
        """

        :param name:
        :param size:
        :param pool:
        :param thin:
        :param template:
        :param shareable:
        :param existing:
        :return:
        """
        print("not implemented")
        return

    def delete_disk(self, name, diskname, pool=None):
        """

        :param name:
        :param diskname:
        :param pool:
        :return:
        """
        print("not implemented")
        return

# should return a dict of {'pool': poolname, 'path': name}
    def list_disks(self):
        """

        :return:
        """
        print("not implemented")
        return

    def add_nic(self, name, network):
        """

        :param name:
        :param network:
        :return:
        """
        print("not implemented")
        return

    def delete_nic(self, name, interface):
        """

        :param name:
        :param interface:
        :return:
        """
        print("not implemented")
        return

# should return (user, ip)
    def _ssh_credentials(self, name):
        print("not implemented")
        return

# should leverage if possible
# should return a sshcommand string
# u, ip = self._ssh_credentials(name)
# sshcommand = common.ssh(name, ip=ip, host=self.host, port=self.port,
# hostuser=self.user, user=u, local=local,
# remote=remote, tunnel=tunnel, insecure=insecure, cmd=cmd, X=X,
# debug=self.debug)
    def ssh(self, name, user=None, local=None, remote=None, tunnel=False,
            insecure=False, cmd=None, X=False, Y=False, D=None):
        """

        :param name:
        :param user:
        :param local:
        :param remote:
        :param tunnel:
        :param insecure:
        :param cmd:
        :param X:
        :param Y:
        :param D:
        :return:
        """
        print("not implemented")
        return

# should leverage if possible
# should return a scpcommand string
# u, ip = self._ssh_credentials(name)
# scpcommand = common.scp(name, ip='', host=self.host, port=self.port,
# hostuser=self.user, user=user,
# source=source, destination=destination, recursive=recursive, tunnel=tunnel,
# debug=self.debug, download=False)
    def scp(self, name, user=None, source=None, destination=None, tunnel=False,
            download=False, recursive=False):
        """

        :param name:
        :param user:
        :param source:
        :param destination:
        :param tunnel:
        :param download:
        :param recursive:
        :return:
        """
        print("not implemented")
        return

    def create_pool(self, name, poolpath, pooltype='dir', user='qemu', thinpool=None):
        """

        :param name:
        :param poolpath:
        :param pooltype:
        :param user:
        :param thinpool:
        :return:
        """
        print("not implemented")
        return

    def add_image(self, image, pool, short=None, cmd=None, name=None, size=1):
        """

        :param image:
        :param pool:
        :param short:
        :param cmd:
        :param name:
        :param size:
        :return:
        """
        print("not implemented")
        return {'result': 'success'}

    def create_network(self, name, cidr=None, dhcp=True, nat=True, domain=None,
                       plan='kvirt', pxe=None, vlan=None):
        """

        :param name:
        :param cidr:
        :param dhcp:
        :param nat:
        :param domain:
        :param plan:
        :param pxe:
        :param vlan:
        :return:
        """
        print("not implemented")
        return

    def delete_network(self, name=None):
        """

        :param name:
        :return:
        """
        print("not implemented")
        return

# should return a dict of pool strings
    def list_pools(self):
        """

        :return:
        """
        print("not implemented")
        return

    def list_networks(self):
        """

        :return:
        """
        print("not implemented")
        return {}

    def list_subnets(self):
        """

        :return:
        """
        print("not implemented")
        return {}

    def delete_pool(self, name, full=False):
        """

        :param name:
        :param full:
        :return:
        """
        print("not implemented")
        return

    def network_ports(self, name):
        """

        :param name:
        :return:
        """
        print("not implemented")
        return

    def vm_ports(self, name):
        """

        :param name:
        :return:
        """
        print("not implemented")
        return ['default']

# returns the path of the pool, if it makes sense. used by kcli list --pools
    def get_pool_path(self, pool):
        """

        :param pool:
        :return:
        """
        print("not implemented")
        return

# return a list of [name, numcpus, memory] for each flavor, if the platform has this concept
    def flavors(self):
        """

        :return:
        """
        return []

# export the primary disk of the corresponding instance so it's available as a template
    def export(name, template=None):
        """

        :param template:
        :return:
        """
        return
