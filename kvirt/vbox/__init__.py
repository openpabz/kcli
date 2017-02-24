#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
interact with a local/remote libvirt daemon
"""

# from defaults import TEMPLATES
from distutils.spawn import find_executable
from iptools import IpRange
from netaddr import IPNetwork
import os
import socket
import string
import time
from virtualbox import VirtualBox


__version__ = "5.3"

KB = 1024 * 1024
MB = 1024 * KB
guestrhel532 = "rhel_5"
guestrhel564 = "rhel_5x64"
guestrhel632 = "rhel_6"
guestrhel664 = "rhel_6x64"
guestrhel764 = "rhel_7x64"
guestother = "other"
guestotherlinux = "other_linux"
guestwindowsxp = "windows_xp"
guestwindows7 = "windows_7"
guestwindows764 = "windows_7x64"
guestwindows2003 = "windows_2003"
guestwindows200364 = "windows_2003x64"
guestwindows2008 = "windows_2008"
guestwindows200864 = "windows_2008x64"
status = {'PoweredOff': 'down', 'PoweredOn': 'up', 'FirstOnline': 'up', 'Aborted': 'down', 'Saved': 'down'}


class KBox:
    def __init__(self):
        try:
            self.conn = VirtualBox()
        except Exception:
            self.conn = None

    def close(self):
        conn = self.conn
        conn.close()
        self.conn = None

    def exists(self, name):
        conn = self.conn
        for vmname in conn.machines:
            if str(vmname) == name:
                return True
        return False

#    def net_exists(self, name):
#        conn = self.conn
#        try:
#            conn.networkLookupByName(name)
#            return True
#        except:
#            return False

    def disk_exists(self, pool, name):
        conn = self.conn
        try:
            storage = conn.storagePoolLookupByName(pool)
            storage.refresh()
            for stor in sorted(storage.listVolumes()):
                if stor == name:
                    return True
        except:
            return False

    def create(self, name, virttype='kvm', title='', description='kvirt', numcpus=2, memory=512, guestid='guestrhel764', pool='default', template=None, disks=[{'size': 10}], disksize=10, diskthin=True, diskinterface='virtio', nets=['default'], iso=None, vnc=False, cloudinit=True, reserveip=False, reservedns=False, start=True, keys=None, cmds=None, ips=None, netmasks=None, gateway=None, nested=True, dns=None, domain=None, tunnel=False, files=[]):
        default_diskinterface = diskinterface
        default_diskthin = diskthin
        default_disksize = disksize
        default_pool = pool
        conn = self.conn
        try:
            default_storagepool = conn.storagePoolLookupByName(default_pool)
        except:
            return {'result': 'failure', 'reason': "Pool %s not found" % default_pool}
        default_pooltype = ''
        default_poolpath = None
        if vnc:
            display = 'vnc'
        else:
            display = 'spice'
        volumes = {}
        volumespaths = {}
        for p in conn.listStoragePools():
            poo = conn.storagePoolLookupByName(p)
            poo.refresh(0)
            for vol in poo.listAllVolumes():
                volumes[vol.name()] = {'pool': poo, 'object': vol}
                volumespaths[vol.path()] = {'pool': poo, 'object': vol}
        networks = []
        bridges = []
        for net in conn.listNetworks():
            networks.append(net)
        for net in conn.listInterfaces():
            if net != 'lo':
                bridges.append(net)
        machine = 'pc'
        sysinfo = "<smbios mode='sysinfo'/>"
        disksxml = ''
        volsxml = {}
        for index, disk in enumerate(disks):
            if disk is None:
                disksize = default_disksize
                diskthin = default_diskthin
                diskinterface = default_diskinterface
                diskpool = default_pool
                diskpooltype = default_pooltype
                diskpoolpath = default_poolpath
            elif isinstance(disk, int):
                disksize = disk
                diskthin = default_diskthin
                diskinterface = default_diskinterface
                diskpool = default_pool
                diskpooltype = default_pooltype
                diskpoolpath = default_poolpath
            elif isinstance(disk, dict):
                disksize = disk.get('size', default_disksize)
                diskthin = disk.get('thin', default_diskthin)
                diskinterface = disk.get('interface', default_diskinterface)
                diskpool = disk.get('pool', default_pool)
                diskwwn = disk.get('wwn')
                try:
                    print('x')
                except:
                    return {'result': 'failure', 'reason': "Pool %s not found" % diskpool}
                diskpooltype = ''
                diskpoolpath = None
            else:
                return {'result': 'failure', 'reason': "Invalid disk entry"}
            letter = chr(index + ord('a'))
            diskdev, diskbus = 'vd%s' % letter, 'virtio'
            if diskinterface != 'virtio':
                diskdev, diskbus = 'hd%s' % letter, 'ide'
            diskformat = 'qcow2'
            if not diskthin:
                diskformat = 'raw'
            storagename = "%s_%d.img" % (name, index + 1)
            diskpath = "%s/%s" % (diskpoolpath, storagename)
            if template is not None and index == 0:
                try:
                    default_storagepool.refresh(0)
                    if '/' in template:
                        backingvolume = volumespaths[template]['object']
                    else:
                        backingvolume = volumes[template]['object']
                    backingxml = backingvolume.XMLDesc(0)
                except:
                    return {'result': 'failure', 'reason': "Invalid template %s" % template}
                backing = backingvolume.path()
                if '/dev' in backing and diskpooltype == 'dir':
                    return {'result': 'failure', 'reason': "lvm template can not be used with a dir pool.Leaving..."}
                if '/dev' not in backing and diskpooltype == 'logical':
                    return {'result': 'failure', 'reason': "file template can not be used with a lvm pool.Leaving..."}
                backingxml = """<backingStore type='file' index='1'>
                                <format type='qcow2'/>
                                <source file='%s'/>
                                <backingStore/>
                                </backingStore>""" % backing
            else:
                backing = None
                backingxml = '<backingStore/>'
            volxml = self._xmlvolume(path=diskpath, size=disksize, pooltype=diskpooltype, backing=backing, diskformat=diskformat)
            if diskpool in volsxml:
                volsxml[diskpool].append(volxml)
            else:
                volsxml[diskpool] = [volxml]
            if diskpooltype == 'logical':
                diskformat = 'raw'
            if diskwwn is not None and diskbus == 'ide':
                diskwwn = '0x%016x' % diskwwn
                diskwwn = "<wwn>%s</wwn>" % diskwwn
            else:
                diskwwn = ''
            disksxml = """%s<disk type='file' device='disk'>
                    <driver name='qemu' type='%s'/>
                    <source file='%s'/>
                    %s
                    <target dev='%s' bus='%s'/>
                    %s
                    </disk>""" % (disksxml, diskformat, diskpath, backingxml, diskdev, diskbus, diskwwn)
        netxml = ''
        version = ''
        for index, net in enumerate(nets):
            macxml = ''
            if isinstance(net, str):
                netname = net
            elif isinstance(net, dict) and 'name' in net:
                netname = net['name']
                ip = None
                if ips and len(ips) > index and ips[index] is not None:
                    ip = ips[index]
                    nets[index]['ip'] = ip
                elif 'ip' in nets[index]:
                    ip = nets[index]['ip']
                if 'mac' in nets[index]:
                    mac = nets[index]['mac']
                    macxml = "<mac address='%s'/>" % mac
                if index == 0 and ip is not None:
                    version = "<entry name='version'>%s</entry>" % ip
            if netname in bridges:
                sourcenet = 'bridge'
            elif netname in networks:
                sourcenet = 'network'
            else:
                return {'result': 'failure', 'reason': "Invalid network %s" % netname}
            netxml = """%s
                     <interface type='%s'>
                     %s
                     <source %s='%s'/>
                     <model type='virtio'/>
                     </interface>""" % (netxml, sourcenet, macxml, sourcenet, netname)
        version = """<sysinfo type='smbios'>
                     <system>
                     %s
                     <entry name='product'>%s</entry>
                     </system>
                     </sysinfo>""" % (version, title)
        if iso is None:
            if cloudinit:
                iso = "%s/%s.iso" % (default_poolpath, name)
            else:
                iso = ''
        else:
            try:
                if os.path.isabs(iso):
                    shortiso = os.path.basename(iso)
                else:
                    shortiso = iso
                isovolume = volumes[shortiso]['object']
                iso = isovolume.path()
                # iso = "%s/%s" % (default_poolpath, iso)
                # iso = "%s/%s" % (isopath, iso)
            except:
                return {'result': 'failure', 'reason': "Invalid iso %s" % iso}
        isoxml = """<disk type='file' device='cdrom'>
                      <driver name='qemu' type='raw'/>
                      <source file='%s'/>
                      <target dev='hdc' bus='ide'/>
                      <readonly/>
                    </disk>""" % (iso)
        if tunnel:
            listen = '127.0.0.1'
        else:
            listen = '0.0.0.0'
        displayxml = """<input type='tablet' bus='usb'/>
                        <input type='mouse' bus='ps2'/>
                        <graphics type='%s' port='-1' autoport='yes' listen='%s'>
                        <listen type='address' address='%s'/>
                        </graphics>
                        <memballoon model='virtio'/>""" % (display, listen, listen)
        if nested and virttype == 'kvm':
            nestedxml = """<cpu match='exact'>
                  <model>Westmere</model>
                   <feature policy='require' name='vmx'/>
                </cpu>"""
        else:
            nestedxml = ""
        if self.host in ['localhost', '127.0.0.1']:
            serialxml = """<serial type='pty'>
                       <target port='0'/>
                       </serial>
                       <console type='pty'>
                       <target type='serial' port='0'/>
                       </console>"""
        else:
            serialxml = """ <serial type="tcp">
                     <source mode="bind" host="127.0.0.1" service="%s"/>
                     <protocol type="telnet"/>
                     <target port="0"/>
                     </serial>""" % self._get_free_port()
        vmxml = """<domain type='%s'>
                  <name>%s</name>
                  <description>%s</description>
                  %s
                  <memory unit='MiB'>%d</memory>
                  <vcpu>%d</vcpu>
                  <os>
                    <type arch='x86_64' machine='%s'>hvm</type>
                    <boot dev='hd'/>
                    <boot dev='cdrom'/>
                    <bootmenu enable='yes'/>
                    %s
                  </os>
                  <features>
                    <acpi/>
                    <apic/>
                    <pae/>
                  </features>
                  <clock offset='utc'/>
                  <on_poweroff>destroy</on_poweroff>
                  <on_reboot>restart</on_reboot>
                  <on_crash>restart</on_crash>
                  <devices>
                    %s
                    %s
                    %s
                    %s
                    %s
                  </devices>
                    %s
                    </domain>""" % (virttype, name, description, version, memory, numcpus, machine, sysinfo, disksxml, netxml, isoxml, displayxml, serialxml, nestedxml)
        for pool in volsxml:
            storagepool = conn.storagePoolLookupByName(pool)
            storagepool.refresh(0)
            for volxml in volsxml[pool]:
                storagepool.createXML(volxml, 0)
        conn.defineXML(vmxml)
        vm = conn.find_machine(name)
        vm.setAutostart(1)
        if cloudinit:
            self._cloudinit(name=name, keys=keys, cmds=cmds, nets=nets, gateway=gateway, dns=dns, domain=domain, reserveip=reserveip, files=files)
            self._uploadimage(name, pool=default_storagepool)
        if reserveip:
            vmxml = ''
            macs = []
            for element in vmxml.getiterator('interface'):
                mac = element.find('mac').get('address')
                macs.append(mac)
            self._reserve_ip(name, nets, macs)
        if start:
            vm.create()
        if reservedns:
            self._reserve_dns(name, nets, domain)
        return {'result': 'success'}

    def start(self, name):
        conn = self.conn
        try:
            vm = conn.find_machine(name)
            if status[str(vm.state)] == "up":
                return {'result': 'success'}
            else:
                vm = conn.find_machine(name)
                vm.launch_vm_process(None, 'headless', '')
                return {'result': 'success'}
        except:
            return {'result': 'failure', 'reason': "VM %s not found" % name}

    def stop(self, name):
        conn = self.conn
        vm = conn.find_machine(name)
        try:
            vm = conn.find_machine(name)
            if status[str(vm.state)] == "down":
                return {'result': 'success'}
            else:
                session = vm.create_session()
                console = session.console
                console.power_down()
                return {'result': 'success'}
        except:
            return {'result': 'failure', 'reason': "VM %s not found" % name}

    def restart(self, name):
        conn = self.conn
        vm = conn.find_machine(name)
        if status[str(vm.state)] == "down":
            return {'result': 'success'}
        else:
            self.stop(name)
            time.sleep(5)
            self.start(name)
            return {'result': 'success'}

    def report(self):
        conn = self.conn
        hostname = conn.getHostname()
        cpus = conn.getCPUMap()[0]
        memory = conn.getInfo()[1]
        print("Host:%s Cpu:%s Memory:%sMB\n" % (hostname, cpus, memory))
        for pool in conn.listStoragePools():
            poolname = pool
            pool = conn.storagePoolLookupByName(pool)
            pooltype = ''
            if pooltype == 'dir':
                poolpath = ''
            else:
                poolpath = ''
            s = pool.info()
            used = "%.2f" % (float(s[2]) / 1024 / 1024 / 1024)
            available = "%.2f" % (float(s[3]) / 1024 / 1024 / 1024)
            # Type,Status, Total space in Gb, Available space in Gb
            used = float(used)
            available = float(available)
            print("Storage:%s Type:%s Path:%s Used space:%sGB Available space:%sGB" % (poolname, pooltype, poolpath, used, available))
        print
        for interface in conn.listAllInterfaces():
            interfacename = interface.name()
            if interfacename == 'lo':
                continue
            print("Network:%s Type:bridged" % (interfacename))
        for network in conn.listAllNetworks():
            networkname = network.name()
            cidr = 'N/A'
            ip = ''
            if ip:
                attributes = ip[0].attrib
                firstip = attributes.get('address')
                netmask = attributes.get('netmask')
                if netmask is None:
                    netmask = attributes.get('prefix')
                try:
                    ip = IPNetwork('%s/%s' % (firstip, netmask))
                    cidr = ip.cidr
                except:
                    cidr = "N/A"
            dhcp = ''
            if dhcp:
                dhcp = True
            else:
                dhcp = False
            print("Network:%s Type:routed Cidr:%s Dhcp:%s" % (networkname, cidr, dhcp))

    def status(self, name):
        conn = self.conn
        try:
            vm = conn.find_machine(name)
            print dir(vm)
        except:
            return None
        return status[str(str(vm.state))]

    def list(self):
        vms = []
        # leases = {}
        conn = self.conn
        for vm in conn.machines:
            name = vm.name
            state = status[str(vm.state)]
            ip = ''
            source = ''
            description = vm.description
            title = 'N/A'
            vms.append([name, state, ip, source, description, title])
        return vms

    def console(self, name, tunnel=False):
        conn = self.conn
        vm = conn.find_machine(name)
        if not str(vm.state):
            print("VM down")
            return
        else:
            vm.launch_vm_process(None, 'gui', '')

    def serialconsole(self, name):
        conn = self.conn
        vm = conn.find_machine(name)
        if not str(vm.state):
            print("VM down")
            return
        else:
            serial = vm.get_serial_port(0)
            if not serial.enabled:
                print("No serial Console found. Leaving...")
                return
            serialport = serial.path
            os.system("nc 127.0.0.1 %s" % serialport)

    def info(self, name):
        # ips = []
        # leases = {}
        starts = {False: 'no', True: 'yes'}
        conn = self.conn
        # for network in conn.listAllNetworks():
        #    for lease in network.DHCPLeases():
        #        ip = lease['ipaddr']
        #        mac = lease['mac']
        #        leases[mac] = ip
        try:
            vm = conn.find_machine(name)
        except:
            print("VM %s not found" % name)
            return
        state = 'down'
        autostart = starts[vm.autostart_enabled]
        memory = vm.memory_size
        numcpus = vm.cpu_count
        state = status[str(vm.state)]
        print("name: %s" % name)
        print("status: %s" % state)
        print("autostart: %s" % autostart)
        description = vm.description
        print("description: %s" % description)
        title = 'N/A'
        if title is not None:
            print("profile: %s" % title)
        print("cpus: %s" % numcpus)
        print("memory: %sMB" % memory)
        for n in range(7):
            nic = vm.get_network_adapter(n)
            enabled = nic.enabled
            if not enabled:
                break
            device = "eth%s" % n
            mac = ':'.join(nic.mac_address[i: i + 2] for i in range(0, len(nic.mac_address), 2))
            network = 'default'
            networktype = 'routed'
            if nic.nat_network != '':
                networktype = 'internal'
                network = nic.internal_network
            print("net interfaces:%s mac: %s net: %s type: %s" % (device, mac, network, networktype))
        for index, dev in enumerate(['a', 'b', 'c', 'd', 'e']):
            try:
                disk = vm.get_medium('SATA', index, 0)
            except:
                break
            device = 'sd%s' % dev
            path = disk.name
            disksize = disk.logical_size / 1024 / 1024 / 1024
            drivertype = os.path.splitext(disk.name)[1].replace('.', '')
            diskformat = 'file'
            print("diskname: %s disksize: %sGB diskformat: %s type: %s path: %s" % (device, disksize, diskformat, drivertype, path))
            return

    def ip(self, name):
        return None

    def volumes(self, iso=False):
        isos = []
        templates = []
        # default_templates = [os.path.basename(t) for t in TEMPLATES.values()]
        default_templates = []
        conn = self.conn
        for storage in conn.listStoragePools():
            storage = conn.storagePoolLookupByName(storage)
            storage.refresh(0)
            root = ''
            for element in root.getiterator('path'):
                storagepath = element.text
                break
            for volume in storage.listVolumes():
                if volume.endswith('iso'):
                    isos.append("%s/%s" % (storagepath, volume))
                elif volume.endswith('qcow2') or volume in default_templates:
                    templates.append("%s/%s" % (storagepath, volume))
        if iso:
            return isos
        else:
            return templates

    def delete(self, name):
        conn = self.conn
        try:
            vm = conn.find_machine(name)
        except:
            return
        vm.remove(True)

    def clone(self, old, new, full=False, start=False):
        conn = self.conn
        tree = ''
        uuid = tree.getiterator('uuid')[0]
        tree.remove(uuid)
        for vmname in tree.getiterator('name'):
            vmname.text = new
        firstdisk = True
        for disk in tree.getiterator('disk'):
            if firstdisk or full:
                source = disk.find('source')
                oldpath = source.get('file')
                backingstore = disk.find('backingStore')
                backing = None
                for b in backingstore.getiterator():
                    backingstoresource = b.find('source')
                    if backingstoresource is not None:
                        backing = backingstoresource.get('file')
                newpath = oldpath.replace(old, new)
                source.set('file', newpath)
                oldvolume = conn.storageVolLookupByPath(oldpath)
                oldinfo = oldvolume.info()
                oldvolumesize = (float(oldinfo[1]) / 1024 / 1024 / 1024)
                newvolumexml = self._xmlvolume(newpath, oldvolumesize, backing)
                pool = oldvolume.storagePoolLookupByVolume()
                pool.createXMLFrom(newvolumexml, oldvolume, 0)
                firstdisk = False
            else:
                devices = tree.getiterator('devices')[0]
                devices.remove(disk)
        for interface in tree.getiterator('interface'):
            mac = interface.find('mac')
            interface.remove(mac)
        if self.host not in ['127.0.0.1', 'localhost']:
            for serial in tree.getiterator('serial'):
                source = serial.find('source')
                source.set('service', str(self._get_free_port()))
        vm = conn.lookupByName(new)
        if start:
            vm.setAutostart(1)
            vm.create()

    def _cloudinit(self, name, keys=None, cmds=None, nets=[], gateway=None, dns=None, domain=None, reserveip=False, files=[]):
        default_gateway = gateway
        with open('/tmp/meta-data', 'w') as metadatafile:
            if domain is not None:
                localhostname = "%s.%s" % (name, domain)
            else:
                localhostname = name
            metadatafile.write('instance-id: XXX\nlocal-hostname: %s\n' % localhostname)
            metadata = ''
            if nets:
                for index, net in enumerate(nets):
                    if isinstance(net, str):
                        if index == 0:
                            continue
                        nicname = "eth%d" % index
                        ip = None
                        netmask = None
                    elif isinstance(net, dict):
                        nicname = net.get('nic', "eth%d" % index)
                        ip = net.get('ip')
                        netmask = net.get('mask')
                    metadata += "  auto %s\n" % nicname
                    if ip is not None and netmask is not None and not reserveip:
                        metadata += "  iface %s inet static\n" % nicname
                        metadata += "  address %s\n" % ip
                        metadata += "  netmask %s\n" % netmask
                        gateway = net.get('gateway')
                        if index == 0 and default_gateway is not None:
                            metadata += "  gateway %s\n" % default_gateway
                        elif gateway is not None:
                            metadata += "  gateway %s\n" % gateway
                        dns = net.get('dns')
                        if dns is not None:
                            metadata += "  dns-nameservers %s\n" % dns
                        domain = net.get('domain')
                        if domain is not None:
                            metadatafile.write("  dns-search %s\n" % domain)
                    else:
                        metadata += "  iface %s inet dhcp\n" % nicname
                if metadata:
                    metadatafile.write("network-interfaces: |\n")
                    metadatafile.write(metadata)
                    # if dns is not None:
                    #    metadatafile.write("  dns-nameservers %s\n" % dns)
                    # if domain is not None:
                    #    metadatafile.write("  dns-search %s\n" % domain)
        with open('/tmp/user-data', 'w') as userdata:
            userdata.write('#cloud-config\nhostname: %s\n' % name)
            if domain is not None:
                userdata.write("fqdn: %s.%s\n" % (name, domain))
            if keys is not None or os.path.exists("%s/.ssh/id_rsa.pub" % os.environ['HOME']) or os.path.exists("%s/.ssh/id_dsa.pub" % os.environ['HOME']):
                userdata.write("ssh_authorized_keys:\n")
            else:
                print("neither id_rsa.pub or id_dsa public keys found in your .ssh directory, you might have trouble accessing the vm")
            if keys is not None:
                for key in keys:
                    userdata.write("- %s\n" % key)
            if os.path.exists("%s/.ssh/id_rsa.pub" % os.environ['HOME']):
                publickeyfile = "%s/.ssh/id_rsa.pub" % os.environ['HOME']
                with open(publickeyfile, 'r') as ssh:
                    key = ssh.read().rstrip()
                    userdata.write("- %s\n" % key)
            if os.path.exists("%s/.ssh/id_dsa.pub" % os.environ['HOME']):
                publickeyfile = "%s/.ssh/id_dsa.pub" % os.environ['HOME']
                with open(publickeyfile, 'r') as ssh:
                    key = ssh.read().rstrip()
                    userdata.write("- %s\n" % key)
            if cmds is not None:
                    userdata.write("runcmd:\n")
                    for cmd in cmds:
                        if cmd.startswith('#'):
                            continue
                        else:
                            userdata.write("- %s\n" % cmd)
            if files:
                userdata.write('ssh_pwauth: True\n')
                userdata.write('disable_root: false\n')
                userdata.write("write_files:\n")
                for fil in files:
                    if not isinstance(fil, dict):
                        continue
                    origin = fil.get('origin')
                    content = fil.get('content')
                    if origin is not None:
                        origin = os.path.expanduser(origin)
                        if not os.path.exists(origin):
                            print("Skipping file %s as not found" % origin)
                            continue
                        # if origin.endswith('j2'):
                        #    origin = open(origin, 'r').read()
                        #    content = Environment().from_string(origin).render(name=name, gateway=gateway, dns=dns, domain=domain)
                        # else:
                        #    content = open(origin, 'r').readlines()
                        content = open(origin, 'r').readlines()
                    elif content is None:
                        continue
                    path = fil.get('path')
                    owner = fil.get('owner', 'root')
                    permissions = fil.get('permissions', '0600')
                    userdata.write("- owner: %s:%s\n" % (owner, owner))
                    userdata.write("  path: %s\n" % path)
                    userdata.write("  permissions: '%s'\n" % (permissions))
                    userdata.write("  content: | \n")
                    for line in content.split('\n'):
                        userdata.write("     %s\n" % line.strip())
        isocmd = 'mkisofs'
        if find_executable('genisoimage') is not None:
            isocmd = 'genisoimage'
        os.system("%s --quiet -o /tmp/%s.iso --volid cidata --joliet --rock /tmp/user-data /tmp/meta-data" % (isocmd, name))

    def handler(self, stream, data, file_):
        return file_.read(data)

    def update_ip(self, name, ip):
        conn = self.conn
        vm = conn.find_machine(name)
        root = ''
        if not vm:
            print("VM %s not found" % name)
        if str(vm.state) == 1:
            print("Machine up. Change will only appear upon next reboot")
        osentry = root.getiterator('os')[0]
        smbios = osentry.find('smbios')
        if smbios is None:
            newsmbios = ''
            osentry.append(newsmbios)
        sysinfo = root.getiterator('sysinfo')
        system = root.getiterator('system')
        if not sysinfo:
            sysinfo = ''
            root.append(sysinfo)
        sysinfo = root.getiterator('sysinfo')[0]
        if not system:
            system = ''
            sysinfo.append(system)
        system = root.getiterator('system')[0]
        versionfound = False
        for entry in root.getiterator('entry'):
            attributes = entry.attrib
            if attributes['name'] == 'version':
                entry.text = ip
                versionfound = True
        if not versionfound:
            version = ''
            version.text = ip
            system.append(version)
        newxml = ''
        conn.defineXML(newxml)

    def update_memory(self, name, memory):
        conn = self.conn
        memory = str(int(memory) * 1024)
        try:
            vm = conn.find_machine(name)
            root = ''
            print vm
        except:
            print("VM %s not found" % name)
            return
        memorynode = root.getiterator('memory')[0]
        memorynode.text = memory
        currentmemory = root.getiterator('currentMemory')[0]
        currentmemory.text = memory
        newxml = ''
        conn.defineXML(newxml)

    def update_cpu(self, name, numcpus):
        conn = self.conn
        try:
            vm = conn.find_machine(name)
            print vm
            root = ''
        except:
            print("VM %s not found" % name)
            return
        cpunode = root.getiterator('vcpu')[0]
        cpunode.text = numcpus
        newxml = ''
        conn.defineXML(newxml)

    def update_start(self, name, start=True):
        conn = self.conn
        try:
            vm = conn.find_machine(name)
        except:
            print("VM %s not found" % name)
            return {'result': 'failure', 'reason': "VM %s not found" % name}
        if start:
            vm.setAutostart(1)
        else:
            vm.setAutostart(0)
        return {'result': 'success'}

    def create_disk(self, name, size, pool=None, thin=True, template=None):
        conn = self.conn
        diskformat = 'qcow2'
        if size < 1:
            print("Incorrect size.Leaving...")
            return
        if not thin:
            diskformat = 'raw'
        if pool is not None:
            pool = conn.storagePoolLookupByName(pool)
            poolroot = ''
            pooltype = poolroot.getiterator('pool')[0].get('type')
            for element in poolroot.getiterator('path'):
                poolpath = element.text
                break
        else:
            print("Pool not found. Leaving....")
            return
        if template is not None:
            volumes = {}
            for p in conn.listStoragePools():
                poo = conn.storagePoolLookupByName(p)
                for vol in poo.listAllVolumes():
                    volumes[vol.name()] = vol.path()
            if template not in volumes and template not in volumes.values():
                print("Invalid template %s.Leaving..." % template)
            if template in volumes:
                template = volumes[template]
        pool.refresh(0)
        diskpath = "%s/%s" % (poolpath, name)
        if pooltype == 'logical':
            diskformat = 'raw'
        volxml = self._xmlvolume(path=diskpath, size=size, pooltype=pooltype,
                                 diskformat=diskformat, backing=template)
        pool.createXML(volxml, 0)
        return diskpath

    def add_disk(self, name, size, pool=None, thin=True, template=None, shareable=False, existing=None):
        conn = self.conn
        diskformat = 'qcow2'
        diskbus = 'virtio'
        if size < 1:
            print("Incorrect size.Leaving...")
            return
        if not thin:
            diskformat = 'raw'
        try:
            vm = conn.find_machine(name)
            root = ''
        except:
            print("VM %s not found" % name)
            return
        currentdisk = 0
        for element in root.getiterator('disk'):
            disktype = element.get('device')
            if disktype == 'cdrom':
                continue
            currentdisk = currentdisk + 1
        diskindex = currentdisk + 1
        diskdev = "vd%s" % string.ascii_lowercase[currentdisk]
        if existing is None:
            storagename = "%s_%d.img" % (name, diskindex)
            diskpath = self.create_disk(name=storagename, size=size, pool=pool, thin=thin, template=template)
        else:
            diskpath = existing
        diskxml = self._xmldisk(diskpath=diskpath, diskdev=diskdev, diskbus=diskbus, diskformat=diskformat, shareable=shareable)
        vm.attachDevice(diskxml)
        vm = conn.find_machine(name)
        vmxml = vm.XMLDesc(0)
        conn.defineXML(vmxml)

    def delete_disk(self, name, diskname):
        conn = self.conn
        try:
            vm = conn.find_machine(name)
            root = ''
        except:
            print("VM %s not found" % name)
            return
        for element in root.getiterator('disk'):
            disktype = element.get('device')
            diskdev = element.find('target').get('dev')
            diskbus = element.find('target').get('bus')
            diskformat = element.find('driver').get('type')
            if disktype == 'cdrom':
                continue
            diskpath = element.find('source').get('file')
            volume = self.conn.storageVolLookupByPath(diskpath)
            if volume.name() == diskname or volume.path() == diskname:
                diskxml = self._xmldisk(diskpath=diskpath, diskdev=diskdev, diskbus=diskbus, diskformat=diskformat)
                vm.detachDevice(diskxml)
                volume.delete(0)
                vm = conn.find_machine(name)
                vmxml = vm.XMLDesc(0)
                conn.defineXML(vmxml)
                return
        print("Disk %s not found in %s" % (diskname, name))

    def list_disks(self):
        volumes = {}
        for p in self.conn.listStoragePools():
            poo = self.conn.storagePoolLookupByName(p)
            for volume in poo.listAllVolumes():
                volumes[volume.name()] = {'pool': poo.name(), 'path': volume.path()}
        return volumes

    def add_nic(self, name, network):
        conn = self.conn
        networks = {}
        for interface in conn.listAllInterfaces():
            networks[interface.name()] = 'bridge'
        for net in conn.listAllNetworks():
            networks[net.name()] = 'network'
        try:
            vm = conn.find_machine(name)
        except:
            print("VM %s not found" % name)
            return
        if network not in networks:
            print("Network %s not found" % network)
            return
        else:
            networktype = networks[network]
            source = "<source %s='%s'/>" % (networktype, network)
        nicxml = """<interface type='%s'>
                    %s
                    <model type='virtio'/>
                    </interface>""" % (networktype, source)
        vm.attachDevice(nicxml)
        vm = conn.find_machine(name)
        vmxml = vm.XMLDesc(0)
        conn.defineXML(vmxml)

    def delete_nic(self, name, interface):
        conn = self.conn
        networks = {}
        nicnumber = 0
        for n in conn.listAllInterfaces():
            networks[n.name()] = 'bridge'
        for n in conn.listAllNetworks():
            networks[n.name()] = 'network'
        try:
            vm = conn.find_machine(name)
            root = ''
        except:
            print("VM %s not found" % name)
            return
        for element in root.getiterator('interface'):
            device = "eth%s" % nicnumber
            if device == interface:
                mac = element.find('mac').get('address')
                networktype = element.get('type')
                if networktype == 'bridge':
                    network = element.find('source').get('bridge')
                    source = "<source %s='%s'/>" % (networktype, network)
                else:
                    network = element.find('source').get('network')
                    source = "<source %s='%s'/>" % (networktype, network)
                break
            else:
                nicnumber += 1
        nicxml = """<interface type='%s'>
                    <mac address='%s'/>
                    %s
                    <model type='virtio'/>
                    </interface>""" % (networktype, mac, source)
        print nicxml
        vm.detachDevice(nicxml)
        vm = conn.find_machine(name)
        vmxml = vm.XMLDesc(0)
        conn.defineXML(vmxml)

    def _ssh_credentials(self, name):
        ubuntus = ['utopic', 'vivid', 'wily', 'xenial', 'yakkety']
        user = 'root'
        conn = self.conn
        try:
            vm = conn.find_machine(name)
        except:
            print("VM %s not found" % name)
            return '', ''
        if str(vm.state) != 1:
            print("Machine down. Cannot ssh...")
            return '', ''
        vm = [v for v in self.list() if v[0] == name][0]
        template = vm[3]
        if template != '':
            if 'centos' in template.lower():
                user = 'centos'
            elif 'cirros' in template.lower():
                user = 'cirros'
            elif [x for x in ubuntus if x in template.lower()]:
                user = 'ubuntu'
            elif 'fedora' in template.lower():
                user = 'fedora'
            elif 'rhel' in template.lower():
                user = 'cloud-user'
            elif 'debian' in template.lower():
                user = 'debian'
            elif 'arch' in template.lower():
                user = 'arch'
        ip = vm[2]
        if ip == '':
            print("No ip found. Cannot ssh...")
        return user, ip

    def ssh(self, name, local=None, remote=None, tunnel=False):
        user, ip = self._ssh_credentials(name)
        if ip == '':
            return
        else:
            sshcommand = "%s@%s" % (user, ip)
            if self.host not in ['localhost', '127.0.0.1'] and tunnel:
                sshcommand = "-o ProxyCommand='ssh -p %s -W %%h:%%p %s@%s' %s" % (self.port, self.user, self.host, sshcommand)
            if local is not None:
                sshcommand = "-L %s %s" % (local, sshcommand)
            if remote is not None:
                sshcommand = "-R %s %s" % (remote, sshcommand)
            sshcommand = "ssh %s" % sshcommand
            os.system(sshcommand)

    def scp(self, name, source=None, destination=None, tunnel=False, download=False, recursive=False):
        user, ip = self._ssh_credentials(name)
        if ip == '':
            print("No ip found. Cannot scp...")
        else:
            if self.host not in ['localhost', '127.0.0.1'] and tunnel:
                arguments = "-o ProxyCommand='ssh -p %s -W %%h:%%p %s@%s'" % (self.port, self.user, self.host)
            else:
                arguments = ''
            scpcommand = 'scp'
            if recursive:
                scpcommand = "%s -r" % scpcommand
            if download:
                scpcommand = "%s %s %s@%s:%s %s" % (scpcommand, arguments, user, ip, source, destination)
            else:
                scpcommand = "%s %s %s %s@%s:%s" % (scpcommand, arguments, source, user, ip, destination)
            os.system(scpcommand)

    def _get_free_port(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('localhost', 0))
        addr, port = s.getsockname()
        s.close()
        return port

    def create_pool(self, name, poolpath, pooltype='dir', user='qemu'):
        conn = self.conn
        for pool in conn.listStoragePools():
            if pool == name:
                print("Pool %s already there.Leaving..." % name)
                return
        if pooltype == 'dir':
            if self.host == 'localhost' or self.host == '127.0.0.1':
                if not os.path.exists(poolpath):
                    os.makedirs(poolpath)
            elif self.protocol == 'ssh':
                cmd1 = 'ssh -p %s %s@%s "test -d %s || mkdir %s"' % (self.port, self.user, self.host, poolpath, poolpath)
                cmd2 = 'ssh %s@%s "chown %s %s"' % (self.user, self.host, user, poolpath)
                os.system(cmd1)
                os.system(cmd2)
            else:
                print("Make sur %s directory exists on hypervisor" % name)
            poolxml = """<pool type='dir'>
                         <name>%s</name>
                         <source>
                         </source>
                         <target>
                         <path>%s</path>
                         </target>
                         </pool>""" % (name, poolpath)
        elif pooltype == 'logical':
            poolxml = """<pool type='logical'>
                         <name>%s</name>
                         <source>
                         <device path='%s'/>
                         <name>%s</name>
                         <format type='lvm2'/>
                         </source>
                         <target>
                         <path>/dev/%s</path>
                         </target>
                         </pool>""" % (name, poolpath, name, name)
        else:
            print("Invalid pool type %s.Leaving..." % pooltype)
            return
        pool = conn.storagePoolDefineXML(poolxml, 0)
        pool.setAutostart(True)
        if pooltype == 'logical':
            pool.build()
        pool.create()

    def add_image(self, image, pool):
        poolname = pool
        conn = self.conn
        volumes = []
        try:
            pool = conn.storagePoolLookupByName(pool)
            for vol in pool.listAllVolumes():
                volumes.append(vol.name())
        except:
            return {'result': 'failure', 'reason': "Pool %s not found" % poolname}
        poolpath = ''
        if self.host == 'localhost' or self.host == '127.0.0.1':
            cmd = 'wget -P %s %s' % (poolpath, image)
        elif self.protocol == 'ssh':
            cmd = 'ssh -p %s %s@%s "wget -P %s %s"' % (self.port, self.user, self.host, poolpath, image)
        os.system(cmd)
        pool.refresh()
        return {'result': 'success'}

    def create_network(self, name, cidr, dhcp=True, nat=True):
        conn = self.conn
        networks = self.list_networks()
        cidrs = [network['cidr'] for network in networks.values()]
        if name in networks:
            return {'result': 'failure', 'reason': "Network %s already exists" % name}
        try:
            range = IpRange(cidr)
        except TypeError:
            return {'result': 'failure', 'reason': "Invalid Cidr %s" % cidr}
        if IPNetwork(cidr) in cidrs:
            return {'result': 'failure', 'reason': "Cidr %s already exists" % cidr}
        netmask = IPNetwork(cidr).netmask
        gateway = range[1]
        if dhcp:
            start = range[2]
            end = range[-2]
            dhcpxml = """<dhcp>
                    <range start='%s' end='%s'/>
                    </dhcp>""" % (start, end)
        else:
            dhcpxml = ''
        if nat:
            natxml = "<forward mode='nat'><nat><port start='1024' end='65535'/></nat></forward>"
        else:
            natxml = ''
        networkxml = """<network><name>%s</name>
                    %s
                    <domain name='%s'/>
                    <ip address='%s' netmask='%s'>
                    %s
                    </ip>
                    </network>""" % (name, natxml, name, gateway, netmask, dhcpxml)
        new_net = conn.networkDefineXML(networkxml)
        new_net.setAutostart(True)
        new_net.create()
        return {'result': 'success'}

    def delete_network(self, name=None):
        conn = self.conn
        try:
            network = conn.networkLookupByName(name)
        except:
            return {'result': 'failure', 'reason': "Network %s not found" % name}
        machines = self.network_ports(name)
        if machines:
            machines = ','.join(machines)
            return {'result': 'failure', 'reason': "Network %s is being used by %s" % (name, machines)}
        if network.isActive():
            network.destroy()
        network.undefine()
        return {'result': 'success'}

    def list_pools(self):
        pools = []
        conn = self.conn
        for pool in conn.listStoragePools():
            pools.append(pool)
        return pools

    def list_networks(self):
        networks = {}
        conn = self.conn
        for network in conn.listAllNetworks():
            networkname = network.name()
            cidr = 'N/A'
            root = ''
            ip = root.getiterator('ip')
            if ip:
                attributes = ip[0].attrib
                firstip = attributes.get('address')
                netmask = attributes.get('netmask')
                ip = IPNetwork('%s/%s' % (firstip, netmask))
                cidr = ip.cidr
            dhcp = root.getiterator('dhcp')
            if dhcp:
                dhcp = True
            else:
                dhcp = False
            forward = root.getiterator('forward')
            if forward:
                attributes = forward[0].attrib
                mode = attributes.get('mode')
            else:
                mode = 'isolated'
            networks[networkname] = {'cidr': cidr, 'dhcp': dhcp, 'type': 'routed', 'mode': mode}
        for interface in conn.listAllInterfaces():
            interfacename = interface.name()
            if interfacename == 'lo':
                continue
            root = ''
            ip = root.getiterator('ip')
            if ip:
                attributes = ip[0].attrib
                ip = attributes.get('address')
                prefix = attributes.get('prefix')
                ip = IPNetwork('%s/%s' % (ip, prefix))
                cidr = ip.cidr
            else:
                cidr = 'N/A'
            networks[interfacename] = {'cidr': cidr, 'dhcp': 'N/A', 'type': 'bridged', 'mode': 'N/A'}
        return networks

    def delete_pool(self, name, full=False):
        conn = self.conn
        try:
            pool = conn.storagePoolLookupByName(name)
        except:
            print("Pool %s not found. Leaving..." % name)
            return
        if full:
            for vol in pool.listAllVolumes():
                vol.delete(0)
        if pool.isActive():
            pool.destroy()
        pool.undefine()

    def bootstrap(self, pool=None, poolpath=None, pooltype='dir', nets={}, image=None):
        print "Nothing to do"