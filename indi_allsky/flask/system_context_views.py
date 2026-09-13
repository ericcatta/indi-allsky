"""Hybrid-owned system diagnostics and form context.

The optional Classic frontend reuses these views. Read adapters and their
error semantics are preserved; mutation commands are owned elsewhere.
"""
import io
import ipaddress
from pathlib import Path
import re
import socket
import time

import dbus
import ephem
import psutil
from flask import current_app as app
from flask_login import login_required

from ..version import __version__
from .base_views import TemplateView
from .forms import (IndiAllskySetDateTimeForm, IndiAllskySetTimezoneForm,
                    IndiAllskyIndiServerChangeForm, IndiAllskyLogViewerForm)


class HybridSystemInfoContextView(TemplateView):
    page_title = 'System Info'
    decorators = [login_required]

    def get_context(self):
        import sys
        import platform
        import astropy
        import flask
        import numpy
        import cv2
        import gunicorn
        import cryptography

        try:
            import pycurl
        except ImportError:
            pycurl = None

        try:
            import paho.mqtt as paho_mqtt
        except ImportError:
            paho_mqtt = None

        #try:
        #    import PyIndi
        #except ImportError:
        #    PyIndi = None

        try:
            import skyfield
        except ImportError:
            skyfield = None

        context = super(HybridSystemInfoContextView, self).get_context()

        context['release'] = str(__version__)

        context['uptime_str'] = self.getUptime()

        context['system_type'] = self.getSystemType()

        context['cpu_count'] = self.getCpuCount()
        context['cpu_usage'] = self.getCpuUsage()

        load5, load10, load15 = self.getLoadAverage()
        context['cpu_load5'] = load5
        context['cpu_load10'] = load10
        context['cpu_load15'] = load15

        mem_total, mem_usage = self.getMemoryUsage()
        context['mem_total'] = mem_total
        context['mem_usage'] = mem_usage

        swap_total, swap_usage = self.getSwapUsage()
        context['swap_total'] = swap_total
        context['swap_usage'] = swap_usage

        context['fs_data'] = self.getAllFsUsage()

        context['temp_list'] = self.getTemps()

        context['fan_list'] = self.getFans()

        context['net_list'] = self.getNetworkIps()

        context['systemd_target'] = self.getSystemdTarget()

        context['indiserver_service_activestate'], context['indiserver_service_unitstate'] = self.getSystemdUnitStatus(app.config['INDISERVER_SERVICE_NAME'])
        context['indiserver_timer_activestate'], context['indiserver_timer_unitstate'] = self.getSystemdUnitStatus(app.config['INDISERVER_TIMER_NAME'])
        context['indi_allsky_service_activestate'], context['indi_allsky_service_unitstate'] = self.getSystemdUnitStatus(app.config['ALLSKY_SERVICE_NAME'])
        context['indi_allsky_timer_activestate'], context['indi_allsky_timer_unitstate'] = self.getSystemdUnitStatus(app.config['ALLSKY_TIMER_NAME'])
        context['indiserver_next_trigger'] = self.getSystemdTimerTrigger(app.config['INDISERVER_TIMER_NAME'])
        context['indi_allsky_next_trigger'] = self.getSystemdTimerTrigger(app.config['ALLSKY_TIMER_NAME'])
        context['gunicorn_indi_allsky_service_activestate'], context['gunicorn_indi_allsky_service_unitstate'] = self.getSystemdUnitStatus(app.config['GUNICORN_SERVICE_NAME'])
        context['gunicorn_indi_allsky_socket_activestate'], context['gunicorn_indi_allsky_socket_unitstate'] = self.getSystemdUnitStatus(app.config['GUNICORN_SOCKET_NAME'])

        context['python_version'] = platform.python_version()
        context['python_platform'] = platform.machine()

        if sys.maxsize > 2147483648:
            context['cpu_bits'] = 64
        else:
            context['cpu_bits'] = 32

        context['gunicorn_version'] = str(getattr(gunicorn, '__version__', -1))
        context['cryptography_version'] = str(getattr(cryptography, '__version__', -1))
        context['cv2_version'] = str(getattr(cv2, '__version__', -1))
        context['ephem_version'] = str(getattr(ephem, '__version__', -1))
        context['numpy_version'] = str(getattr(numpy, '__version__', -1))
        context['astropy_version'] = str(getattr(astropy, '__version__', -1))
        context['flask_version'] = str(getattr(flask, '__version__', -1))
        context['dbus_version'] = str(getattr(dbus, '__version__', -1))


        if pycurl:
            context['pycurl_version'] = str(getattr(pycurl, 'version', -1))
        else:
            context['pycurl_version'] = 'Not installed'

        if paho_mqtt:
            context['pahomqtt_version'] = str(getattr(paho_mqtt, '__version__', -1))
        else:
            context['pahomqtt_version'] = 'Not installed'

        ### PyIndi no longer reports a version
        #if PyIndi:
        #    context['pyindi_version'] = '.'.join((
        #        str(getattr(PyIndi, 'INDI_VERSION_MAJOR', -1)),
        #        str(getattr(PyIndi, 'INDI_VERSION_MINOR', -1)),
        #        str(getattr(PyIndi, 'INDI_VERSION_RELEASE', -1)),
        #    ))
        #else:
        #    context['pyindi_version'] = 'Not installed'

        if skyfield:
            context['skyfield_version'] = str(getattr(skyfield, '__version__', -1))
        else:
            context['skyfield_version'] = 'Not installed'


        context['now'] = self.camera_now
        context['form_settime'] = IndiAllskySetDateTimeForm()


        timedate1_dict = self.getSystemdTimeDate()
        context['timedate1_dict'] = timedate1_dict


        timezone_data = {
            'NEW_TIMEZONE' : timedate1_dict['Timezone'],
        }
        context['form_timezone'] = IndiAllskySetTimezoneForm(data=timezone_data)


        if self.camera.driver:
            #app.logger.info('Current camera driver: %s', self.camera.driver)
            if self.camera.driver == 'rpicam-still':
                camera_driver = 'indi_simulator_ccd'
            else:
                camera_driver = self.camera.driver  # set the current camera driver as default
        else:
            camera_driver = 'indi_simulator_ccd'


        indiserver_form_data = {
            'CAMERA_SERVER_SELECT' : camera_driver,
            'GPS_SERVER_SELECT'    : '',
        }

        form_indiserver_change = IndiAllskyIndiServerChangeForm(data=indiserver_form_data)

        context['form_indiserver_change'] = form_indiserver_change


        return context


    def getUptime(self):
        uptime_s = time.time() - psutil.boot_time()

        days = int(uptime_s / 86400)
        uptime_s -= (days * 86400)

        hours = int(uptime_s / 3600)
        uptime_s -= (hours * 3600)

        minutes = int(uptime_s / 60)
        uptime_s -= (minutes * 60)

        #seconds = int(uptime_s)

        uptime_str = '{0:d} days, {1:d}:{2:d}'.format(days, hours, minutes)

        return uptime_str


    def getSystemType(self):
        # This is available for SBCs and systems using device trees
        model_p = Path('/proc/device-tree/model')

        try:
            if model_p.exists():
                with io.open(str(model_p), 'r') as f:
                    system_type = f.readline()  # only first line
            else:
                return 'Generic PC'
        except PermissionError as e:
            app.logger.error('Permission error: %s', str(e))
            return 'Unknown'


        system_type = system_type.strip()


        if not system_type:
            return 'Unknown'


        return str(system_type)


    def getCpuCount(self):
        return psutil.cpu_count()


    def getCpuUsage(self):
        c = psutil.cpu_times_percent()

        cpu_percent = {
            'user'    : c.user,
            'system'  : c.system,
            'idle'    : c.idle,
            'nice'    : c.nice,
            'iowait'  : c.iowait,
            'irq'     : c.irq,
            'softirq' : c.softirq,
        }

        return cpu_percent


    def getLoadAverage(self):
        return psutil.getloadavg()


    def getMemoryUsage(self):
        memory_info = psutil.virtual_memory()

        memory_total = memory_info.total
        #memory_free = memory_info.free

        memory_percent = {
            'user_percent'    : (memory_info.used / memory_total) * 100.0,
            'cached_percent'  : (memory_info.cached / memory_total) * 100.0,
        }

        memory_total_mb = int(memory_total / 1024.0 / 1024.0)

        #memory_percent = 100 - ((memory_free * 100) / memory_total)

        return memory_total_mb, memory_percent


    def getSwapUsage(self):
        swap_info = psutil.swap_memory()

        swap_total = int(swap_info[0] / 1024 / 1024)
        swap_usage = swap_info[3]

        return swap_total, swap_usage


    def getAllFsUsage(self):
        fs_list = psutil.disk_partitions(all=True)

        fs_data = list()
        for fs in fs_list:

            skip = False
            for p in ('/snap', '/sys', '/proc', '/run', '/dev'):
                if fs.mountpoint.startswith(p + '/'):
                    skip = True
                    break
                elif fs.mountpoint == p:
                    skip = True
                    break

            if skip:
                continue


            try:
                disk_usage = psutil.disk_usage(fs.mountpoint)
            except PermissionError as e:
                app.logger.error('PermissionError: %s', str(e))
                continue

            data = {
                'total_mb'   : disk_usage.total / 1024.0 / 1024.0,
                'mountpoint' : fs.mountpoint,
                'percent'    : disk_usage.percent,
            }

            fs_data.append(data)

        return fs_data


    def getTemps(self):
        temp_info = psutil.sensors_temperatures()

        temp_list = list()
        for t_key in sorted(temp_info):  # always return the keys in the same order
            for i, t in enumerate(temp_info[t_key]):
                temp_c = float(t.current)

                if self.indi_allsky_config.get('TEMP_DISPLAY') == 'f':
                    current_temp = (temp_c * 9.0 / 5.0) + 32
                    temp_sys = 'F'
                elif self.indi_allsky_config.get('TEMP_DISPLAY') == 'k':
                    current_temp = temp_c + 273.15
                    temp_sys = 'K'
                else:
                    current_temp = temp_c
                    temp_sys = 'C'

                # these names will match the mqtt topics
                if not t.label:
                    # use index for label name
                    label = str(i)
                else:
                    label = t.label

                topic = '{0:s}/{1:s}'.format(t_key, label)

                # no spaces, etc in topics
                topic_sub = re.sub(r'[#+\$\*\>\ ]', '_', topic)

                temp_list.append({
                    'name'   : topic_sub,
                    'temp'   : current_temp,
                    'sys'    : temp_sys,
                })

        return temp_list

    def getFans(self):
        fan_list = list()

        # 1) Standard: psutil sensors_fans()
        try:
            fan_info = psutil.sensors_fans()
        except Exception:
            fan_info = dict()

        for f_key in sorted(fan_info):  # stable ordering
            for i, f in enumerate(fan_info[f_key]):
                try:
                    rpm = float(getattr(f, 'current', 0.0) or 0.0)
                except Exception:
                    rpm = 0.0

                if not getattr(f, 'label', ''):
                    label = str(i)
                else:
                    label = f.label

                topic = '{0:s}/{1:s}'.format(f_key, label)
                topic_sub = re.sub(r'[#+\$\*\>\ ]', '_', topic)

                fan_list.append({
                    'name' : topic_sub,
                    'rpm'  : rpm,
                })

        # 2) Raspberry Pi 5 Active Cooler / fan connector fallback via sysfs
        # Typical path: /sys/devices/platform/cooling_fan/hwmon/hwmon*/fan1_input
        if not fan_list:
            try:
                base = Path('/sys/devices/platform/cooling_fan/hwmon')
                for fan_input in base.glob('hwmon*/fan1_input'):
                    try:
                        rpm = float(int(fan_input.read_text().strip()))
                        fan_list.append({
                            'name' : 'cooling_fan/fan1',
                            'rpm'  : rpm,
                        })
                    except Exception:
                        pass
                    break
            except Exception:
                pass

        return fan_list

    def getNetworkIps(self):
        net_info = psutil.net_if_addrs()

        net_list = list()
        for dev, addr_info in net_info.items():
            if dev == 'lo':
                # skip loopback
                continue


            dev_info = {
                'name'  : dev,
                'inet4' : [],
                'inet6' : [],
            }

            for addr in addr_info:
                if addr.family == socket.AF_INET:
                    cidr = ipaddress.IPv4Network('0.0.0.0/{0:s}'.format(addr.netmask)).prefixlen
                    dev_info['inet4'].append('{0:s}/{1:d}'.format(addr.address, cidr))

                elif addr.family == socket.AF_INET6:
                    dev_info['inet6'].append('{0:s}'.format(addr.address))

            net_list.append(dev_info)


        return net_list


    def getSystemdTarget(self):
        try:
            session_bus = dbus.SystemBus()
        except dbus.exceptions.DBusException:
            return 'D-Bus Unavailable'

        systemd1 = session_bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
        manager = dbus.Interface(systemd1, 'org.freedesktop.systemd1.Manager')

        try:
            default_target = manager.GetDefaultTarget()
        except dbus.exceptions.DBusException:
            return 'D-Bus Exception'

        return str(default_target)


    def getSystemdTimeDate(self):
        try:
            session_bus = dbus.SystemBus()
        except dbus.exceptions.DBusException:
            # This happens in docker
            timedate1_dict = {
                'Timezone' : 'Unknown',
                'CanNTP'   : False,
                'NTP'      : False,
                'NTPSynchronized' : False,
                'LocalRTC' : False,
                'TimeUSec' : 1,
            }
            return timedate1_dict


        timedate1 = session_bus.get_object('org.freedesktop.timedate1', '/org/freedesktop/timedate1')
        manager = dbus.Interface(timedate1, 'org.freedesktop.DBus.Properties')

        timedate1_dict = dict()
        timedate1_dict['Timezone'] = str(manager.Get('org.freedesktop.timedate1', 'Timezone'))
        timedate1_dict['CanNTP'] = bool(manager.Get('org.freedesktop.timedate1', 'CanNTP'))
        timedate1_dict['NTP'] = bool(manager.Get('org.freedesktop.timedate1', 'NTP'))
        timedate1_dict['NTPSynchronized'] = bool(manager.Get('org.freedesktop.timedate1', 'NTPSynchronized'))
        timedate1_dict['LocalRTC'] = bool(manager.Get('org.freedesktop.timedate1', 'LocalRTC'))
        timedate1_dict['TimeUSec'] = int(manager.Get('org.freedesktop.timedate1', 'TimeUSec'))

        #app.logger.info('timedate1: %s', timedate1_dict)

        return timedate1_dict


class HybridLogContextView(TemplateView):
    page_title = 'Log Viewer'
    decorators = [login_required]

    def get_context(self):
        context = super(HybridLogContextView, self).get_context()

        context['form_logviewer'] = IndiAllskyLogViewerForm()

        return context


class HybridSupportContextView(TemplateView):
    page_title = 'Support Info'
    decorators = [login_required]

    def get_context(self):
        context = super(HybridSupportContextView, self).get_context()
        return context
