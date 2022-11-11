#!/usr/bin/env python3

# FishNetServer.py
# D. Singletary
# 10/8/22
# Simple proxy/model for network scripting

__version__ = 'v1.0'
__desc__ = 'FishNet ' + __version__ + \
           '\nHello, and thanks for all the fish!'

import json
import time
import random
import string
from flask import Flask, redirect, url_for, request, json, jsonify, cli
# requires pip3 import flask_api
from flask_api import status

# supress the dev banner
cli.show_server_banner = lambda *_: None
app = Flask(__name__)

# generate a TOKEN
def generateToken(size=48,
                chars=string.ascii_uppercase +
                      string.ascii_lowercase + 
                      string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

# initialize the component dictionary, TOKEN, user ID and password 
def setup():
    global TOKEN
    global TOKEN_GENTIME
    global DEVICES
    global SUPPORTED_ATTRIBUTES
    global USER
    global PWORD

    TOKEN = generateToken()
    TOKEN_GENTIME = int(time.time())
    # print('TOKEN = ', TOKEN) # debug
    # print('expires: ', TOKEN_GENTIME) # debug
    USER = 'pyuser'
    PWORD = 'cis3435!'
    
    DEVICES = []
    # router 1
    DEVICES.append({'hostname':'router1',
                       'ipaddr':'192.168.2.1',
                       'macaddr':'aa:bb:cc:dd:ee:ff',
                       'nports':24})
    # switch 1
    DEVICES.append({'hostname':'switch1',
                       'ipaddr':'192.168.2.2',
                       'macaddr':'ff:ee:dd:cc:bb:aa',
                       'nports':64})

    SUPPORTED_ATTRIBUTES = [ 'ipaddr', 'macaddr', 'nports' ]

# validate token
def chkToken(checkval):
    global TOKEN
    returnVal = False

    if checkval == TOKEN:
        returnVal = True

    return returnVal

# validate device
def chkDevice(hostName):
    global DEVICES
    returnVal = False

    # check the device dictionary for the specified hostname
    for dev in DEVICES:
        chkName = dev.get('hostname')
        if chkName == hostName:
            returnVal = True
            break

    return returnVal

# validate attribute
def chkAttribute(attribute):
    returnStat = False
    if attribute in SUPPORTED_ATTRIBUTES:
        returnStat = True
    return returnStat

# validate the value based on the attribute
def chkValue(attribute, value):
    IPADDR = 'ipaddr'
    returnStat = False
    if attribute == IPADDR:
        returnStat = validateIP(value)
    return returnStat

# find device val using key
def findDev(key, val):
    # print('findDev: key=', key, ' val=', val) # debug
    for i in range(0,len(DEVICES)):
        find_val = DEVICES[i].get(key)
        if find_val == val:
            return DEVICES[i]

    return None

# function to validate IP address
def validateIP(ipaddr):
    validIP = False
    octets = ipaddr.split('.')
    for byte in octets:
        byte = int(byte)
        if byte < 0 or byte > 255:
            break
    else:
        validIP = True

    return validIP

# setValue sets the specified value for the specified host device
def setValue(host, attr, val):
    dev = findDev('hostname', host)
    # print('setValue: entry=', entry) # debug
    dev[attr] = val

# handle login and get TOKEN via GET or POST
@app.route('/login',methods = ['POST', 'GET'])
def login():

    errStr = ''
    returnStat = status.HTTP_200_OK

    if request.method == 'POST':   # POST
        user = request.form['user']
        password = request.form['password']
    else:   # GET
        user = request.args.get('user')
        password = request.args.get('password')
    # validate
    if user != USER or password != PWORD:
        errStr = 'invalid user or password'
        returnStat = status.HTTP_401_UNAUTHORIZED
    return TOKEN, returnStat

# handle GET to get inventory
@app.route('/get')
def get():

    req_args = request.args  # req_args is an ImmutableMultiDict
    #print('req_args = ', req_args, 'len = ', len(req_args)) # debug
    if len(req_args) == 0:
        return jsonify(DEVICES), status.HTTP_200_OK
        #return jsonify(DEVICES)
    else:
        try_key = 'hostname'
        req_val = request.args.get(try_key, default=None, type=None)
        if (req_val == None):
            #return jsonify('invalid key')
            return 'invalid key', status.HTTP_404_NOT_FOUND
        else:
            comp = findDev(try_key, req_val)
            if comp == None:
                #return jsonify('invalid hostname')
                return 'invalid hostname', status.HTTP_404_NOT_FOUND
            else:
                return comp, status.HTTP_200_OK

# handle POST to set an attribute
@app.route('/set',methods = ['POST'])
def set():
    errStr = 'success!'
    returnStat = errStr, status.HTTP_200_OK

    if request.method == 'GET': # HTTP GET is not supported for set
        errStr = 'HTTP GET is not supported for set'
        print(errStr)
        returnStat = errStr, status.HTTP_403_FORBIDDEN

    # validate the token
    elif request.method == 'POST':
        passedToken = request.form['token']
        if chkToken(passedToken) != True:
            errStr = 'invalid TOKEN: ' + passedToken
            print(errStr)
            returnStat = errStr, status.HTTP_401_UNAUTHORIZED
        else:
            # print('set: token accepted') # debug
            host = request.form['hostname']
            attr = request.form['attribute']
            val = request.form['value']
            #print('\thostname = ', host) #debug
            #print('\tattribute = ', attr)
            #print('\tvalue = ', val)
            if chkDevice(host) != True:
                errStr = 'no such device: ' + host
                print(errStr)
                returnStat = errStr, status.HTTP_404_NOT_FOUND
            elif chkAttribute(attr) != True:
                errStr = 'no such attribute: ' + attr
                print(errStr)
                returnStat = errStr, status.HTTP_404_NOT_FOUND
            elif chkValue(attr, val) != True:
                errStr = 'invalid value: ' + val
                print(errStr)
                returnStat = errStr, status.HTTP_404_NOT_FOUND
            else:
                # attribute and value have been validated, safe to set
                # debug
                # print('host:', host, ', setting', attr, ', value', val)
                setValue(host, attr, val)
                
    return returnStat

def main():
    print(__desc__)
    setup()
    #print(DEVICES) # debug
    app.run()

if __name__ == '__main__':
    main()

# TODO
# set netmask
# enable pw
# set IF name
# set hostname
# activate IF (noshut)
