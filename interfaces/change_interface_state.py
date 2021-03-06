#!/bin//python

import re
try:
    import readline
except:
    pass
import urllib2
import json
import ssl
import os
import itertools
import threading
import Queue
from localutils.custom_utils import *
import interfaces.switchpreviewutil as switchpreviewutil
import logging

# Create a custom logger
# Allows logging to state detailed info such as module where code is running and 
# specifiy logging levels for file vs console.  Set default level to DEBUG to allow more
# grainular logging levels
logger = logging.getLogger('aciops.' + __name__)


def shutinterfaces(interfaces, apic, cookie):
    queue = Queue.Queue()
    interfacelist = []
    interfacelist2 =[]
    for interface in interfaces:
        t = threading.Thread(target=postshut, args=(interface,queue, apic, cookie,))
        t.start()
        interfacelist.append(t)
    for t in interfacelist:
        t.join()
        interfacelist2.append(queue.get())
    for x in sorted(interfacelist2):
        print(x)

def postshut(interface,queue, apic, cookie):
        url = 'https://{apic}/api/node/mo/uni/fabric/outofsvc.json'.format(apic=apic)
        logger.info(url)
        # data is the 'POST' data sent in the REST call to 'blacklist' (shutdown) on a normal interface
        data = """'{{"fabricRsOosPath":{{"attributes":{{"tDn":"{interface}","lc":"blacklist"}},"children":[]}}}}'""".format(interface=interface)
        logger.info(data)
        result, error =  PostandGetResponseData(url, data, cookie)
        #import pdb; pdb.set_trace()
        if result == []:
            queue.put('\x1b[1;32;40m[Complete]\x1b[0m shut ' + interface.name)
        else:
            queue.put('\x1b[1;37;41mFailure\x1b[0m -- ' + error)

def noshutinterfaces(interfaces, apic, cookie):
    queue = Queue.Queue()
    interfacelist = []
    interfacelist2 =[]
    for interface in interfaces:
        t = threading.Thread(target=postnoshut, args=(interface,queue, apic, cookie,))
        t.start()
        interfacelist.append(t)
    for t in interfacelist:
        t.join()
        interfacelist2.append(queue.get())
    for x in sorted(interfacelist2):
        print(x)

def postnoshut(interface,queue, apic, cookie):
        url = 'https://{apic}/api/node/mo/uni/fabric/outofsvc.json'.format(apic=apic)
        logger.info(url)
        # data is the 'POST' data sent in the REST call to delete object from 'blacklist' (no shut)
        data = """'{{"fabricRsOosPath":{{"attributes":{{"dn":"uni/fabric/outofsvc/rsoosPath-[{interface}]","status":"deleted"}},"children":[]}}}}'""".format(interface=interface)
        logger.info(data)
        result, error =  PostandGetResponseData(url, data, cookie)
        if result == []:
            queue.put('\x1b[1;32;40m[Complete]\x1b[0m no shut ' + interface.name)
        else:
            queue.put('\x1b[1;37;41mFailure\x1b[0m -- ' + error)

def shut_or_noshut_confirmation(interfacelist, operation = 'shut'):
    print('\nVerify ' + operation + ' for interface:\n')
    for interface in interfacelist:
        if hasattr(interface, 'leaf'):
            print("\t{} {}".format(interface.leaf,interface.name))
        else:
            print("\t{}".format(interface.name))
    print('\n')
    while True:
        ask = custom_raw_input('Confirmation [y|n=default]: ') or 'n'
        if ask != '' and ask.strip().lstrip()[0].lower() == 'n':
            return False
        elif ask != '' and ask.strip().lstrip()[0].lower() == 'y':
            return True
        else:
            print('\x1b[1;37;41mInvalid option...\x1b[0')
            continue

    

def main(import_apic, import_cookie):
    while True:
        cookie = import_cookie
        apic = import_apic
        allepglist = get_All_EGPs_names(apic,cookie)
        allpclist = get_All_PCs(apic,cookie)
        allvpclist = get_All_vPCs(apic,cookie)
        all_leaflist = get_All_leafs(apic,cookie)
        clear_screen()
        location_banner('Shut and No Shut interfaces')
        selection = interface_menu()
    
        if selection == '1':
            chosenleafs = physical_leaf_selection(all_leaflist, apic, cookie)
            switchpreviewutil.main(apic,cookie,chosenleafs)
            returnedlist = physical_interface_selection(apic, cookie, chosenleafs, provideleaf=False)
            print('\r')
            while True:
                option = custom_raw_input(
                    ("Would you like to do?\n\
                        \n1.) shut\
                        \n2.) no shut\
                        \n3.) bounce \n\
                        \nSelect a number: "))
                if option == '1':
                    print('\n')
                    confirmed = shut_or_noshut_confirmation(returnedlist, operation = '"shut"')
                    if confirmed:
                        print('\n')
                        shutinterfaces(returnedlist, apic, cookie)
                    else:
                        print('\nCancelled\n')
                    break
                elif option == '2':
                    print('\n')
                    confirmed = shut_or_noshut_confirmation(returnedlist, operation = '"no shut"')
                    if confirmed:
                        print('\n')
                        noshutinterfaces(returnedlist, apic, cookie)
                    else:
                        print('\nCancelled\n')
                    break
                elif option == '3':
                    print('\n')
                    confirmed = shut_or_noshut_confirmation(returnedlist, operation = '"bounce"')
                    if confirmed:
                        print('\n')
                        shutinterfaces(returnedlist, apic, cookie)
                        noshutinterfaces(returnedlist, apic, cookie)
                    else:
                        print('\nCancelled\n')
                    break
                else:
                    print('\n\x1b[1;31;40mInvalid option, please try again...\x1b[0m\n')
                    continue
            custom_raw_input('\n#Press Enter to continue...')
        elif selection == '2':
            returnedlist = port_channel_selection(allpclist)
            print('\r')
            while True:
                option = custom_raw_input(
                        ("Would you like to do?\n\
                            \n1.) shut\
                            \n2.) no shut\
                            \n3.) bounce \n\
                            \nSelect a number: "))
                if option == '1':
                    print('\n')
                    confirmed = shut_or_noshut_confirmation(returnedlist, operation = '"shut"')
                    if confirmed:
                        print('\n')
                        shutinterfaces(returnedlist, apic, cookie)
                    else:
                        print('\nCancelled\n')
                    break
                elif option == '2':
                    print('\n')
                    confirmed = shut_or_noshut_confirmation(returnedlist, operation = '"no shut"')
                    if confirmed:
                        print('\n')
                        noshutinterfaces(returnedlist, apic, cookie)
                    else:
                        print('\nCancelled\n')
                    break
                elif option == '3':
                    print('\n')
                    confirmed = shut_or_noshut_confirmation(returnedlist, operation = '"bounce"')
                    if confirmed:
                        print('\n')
                        shutinterfaces(returnedlist, apic, cookie)
                        noshutinterfaces(returnedlist, apic, cookie)
                    else:
                        print('\nCancelled\n')
                    break
                else:
                    print('\n\x1b[1;31;40mInvalid option, please try again...\x1b[0m\n')
                    continue
    
            custom_raw_input('\n#Press Enter to continue...')

        elif selection == '3':
            returnedlist = port_channel_selection(allvpclist)
            print('\r')
            while True:
                option = custom_raw_input(
                        ("Would you like to do?\n\
                            \n1.) shut\
                            \n2.) no shut\
                            \n3.) bounce \n\
                            \nSelect a number: "))
                if option == '1':
                    print('\n')
                    confirmed = shut_or_noshut_confirmation(returnedlist, operation = '"shut"')
                    if confirmed:
                        print('\n')
                        shutinterfaces(returnedlist, apic, cookie)
                    else:
                        print('\nCancelled\n')
                    break
                elif option == '2':
                    print('\n')
                    confirmed = shut_or_noshut_confirmation(returnedlist, operation = '"no shut"')
                    if confirmed:
                        print('\n')
                        noshutinterfaces(returnedlist, apic, cookie)
                    else:
                        print('\nCancelled\n')
                    break
                elif option == '3':
                    print('\n')
                    confirmed = shut_or_noshut_confirmation(returnedlist, operation = '"bounce"')
                    if confirmed:
                        print('\n')
                        shutinterfaces(returnedlist, apic, cookie)
                        noshutinterfaces(returnedlist, apic, cookie)
                    else:
                        print('\nCancelled\n')
                    break
                else:
                    print('\n\x1b[1;31;40mInvalid option, please try again...\x1b[0m\n')
                    continue
            custom_raw_input('\n#Press Enter to continue...')