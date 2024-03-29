# 2020-05-04 
# https://phyphox.org/wiki/index.php/Remote-interface_communication
# http://10.10.10.21:8080/control?cmd=start
# http://10.10.10.21:8080/control?cmd=stop
# http://10.10.10.21:8080/control?cmd=clear
# http://10.10.10.21:8080/get?pressure
# http://10.10.10.21:8080/get?pressure=201.69097|p_time&p_time=201.69097
# http://10.10.10.21:8080/get?pressure=262.40482|p_time&p_time=262.40482
 # http://10.10.10.21:8080/get?pressure=full&p_time=full

# Alle Messwerte ab secunde 35.88 (aus letzten Daten)
#  http://10.10.10.21:8080/get?pressure=full&p_time=35.88
# http://10.10.10.21:8080/get?illum
# http://10.10.10.21:8080/get?illum=57.182803|illum_time&illum_time=57.182803
import requests
import time
import zipfile
import numpy as np
import glob
import os

import pyphone.connect as connect

import aiohttp
import asyncio

import json

from pprint import pprint


#import stephane.display.graphes as graphes
def get_base_url(ip):
    return "http://"+ip+":8080"

def get_phone(ip):
    return int(ip.split('.')[-1])-100

def run_serie(iplist,T=10,folder=''):
    basefolder = connect.basefolder()+'Phyphox/'
    folder = basefolder+folder

    #PP_CHANNELS = ["accX","accY","accZ"]
    #PP_CHANNELS_COUNT = len(PP_CHANNELS)
    print(folder)

    if not os.path.exists(folder):
    	os.makedirs(folder)
   
    loop = asyncio.get_event_loop()
    funlist = [clear, run, stop, save]
    #funlist = [run]#, stop, save]

    coroutine =  execute(clear,iplist)
    loop.run_until_complete(coroutine)

    coroutine =  execute(run,iplist)
    loop.run_until_complete(coroutine)

    t1=time.time()
    t2=t1
    print('Acquisition in progress ...')

    while (t2-t1)<T:
        time.sleep(10)
        print('get data')
        coroutine =  execute(lambda x,y:save(x,y,folder=folder),iplist)
        loop.run_until_complete(coroutine)
        t2 = time.time()
    print('Acquisition done')

    coroutine =  execute(stop,iplist)
    loop.run_until_complete(coroutine)

    coroutine = execute(lambda x,y:save(x,y,folder=folder),iplist)
    loop.run_until_complete(coroutine)
#        print(fun.__name__,'Over')

def run_save(iplist,T=10,folder=''):
    basefolder = connect.basefolder()+'Phyphox/'
    folder = basefolder+folder

    #PP_CHANNELS = ["accX","accY","accZ"]
    #PP_CHANNELS_COUNT = len(PP_CHANNELS)
    print(folder)

    if not os.path.exists(folder):
    	os.makedirs(folder)
   
    loop = asyncio.get_event_loop()
    print('Save data ...')

    coroutine = execute(lambda x,y:save(x,y,folder=folder),iplist)
    loop.run_until_complete(coroutine)
#        print(fun.__name__,'Over')


def run_config(iplist):
    loop = asyncio.get_event_loop()
    coroutine = execute(lambda x,y:get_config(x,y),iplist)
    R = loop.run_until_complete(coroutine)
    return R

def run_fun(fun,iplist,**kwargs):
    loop = asyncio.get_event_loop()
    coroutine =  execute(fun,iplist)
    R = loop.run_until_complete(coroutine)
    return R

async def run_try(address,fun,session):
    #r = await fun(address,session)
    try:
        r = await fun(address,session)
        print(r)
    #fun(address,folder=folder)
    except:
        print('Cannot connect to '+address)
        r =  {'result':False}
    return r

async def execute(fun,iplist,**kwargs):
    async with aiohttp.ClientSession() as session:    
        R={}
        urls = [get_base_url(ip) for ip in iplist]
        R = await asyncio.gather(*map(lambda url:run_try(url,fun,session), urls))
#            R[get_phone(ip_s)] = r#["result"]
        print(R)

        out = {}
        for i,ip in enumerate(iplist):
            phone = get_phone(ip)
            out[phone]={}
            for key in R[i].keys():
                out[phone][key]=R[i][key]
    return out

async def get_config(address,session):
#    adress=get_base_url(ip)
    url = address+"/config"
    return await request_json(url,session)

async def request_json(url,session):
    print(url)
    async with session.get(url,timeout=20) as resp:
        r = await resp.json()#.text()
    return r  

def run_get(iplist,name):
    loop = asyncio.get_event_loop()
    #coroutine = execute(get,iplist,name=name)
    coroutine = execute(lambda x,y:get(x,y,name=name),iplist)

    R = loop.run_until_complete(coroutine)
    return R

async def get(address,session,name=''):
    #name=kwargs.get('name')
#    adress=get_base_url(ip)
    print(name)
#    name='all'
    if name=='location':
        s = "locLat&&locLon"
        url = address+"/get?"+s
        return await request_json(url,session)
    if name=='all':
        #rlist = await get_config(address,session)
        s= "accX&&accY&&accZ&&locLat&&locLon"
        #for r in rlist['buffers'][1:4]:
        #s=s+r['name']+"&&"
        #s=s[:-2]
        print(s)
        url = address+"/get?"+s
        return await request_json(url,session)
    else:
        print('not defined')
        s=""
        return None

async def request(url,session):
    print(url)
    async with session.get(url,timeout=600) as resp:
        r = await resp.read()#.text()
    return r

async def clear(address,session,folder=''):
    url = address + "/control?cmd=clear"
    return await request_json(url,session)
    
async def run(address,session,folder=''):
    url = address + "/control?cmd=start"
    return await request_json(url,session)

async def stop(address,session,folder=''):
    url = address + "/control?cmd=stop"
    return await request_json(url,session)

async def save(address,session,folder,name='test'):
    ip_s = address.split(':')[1][2:]
    print('Save data for '+ip_s)
    url = address + '/export?format=1'

    out = await request(url,session)#requests.get(url=url)    
    print(ip_s)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    name = folder+'/'+name+'_'+ip_s.replace('.','_')
    with open(name+".zip", "wb") as file:
        file.write(out)
    print('Done')

    return {'result':True}


async def get_buffer(address,session,buffername):
    url = adress+"/get?"+buffername
    return await request(url,session)

def get_buffer():
    pass
def load(folder):
    filelist = glob.glob(folder+'*.zip')
    print(filelist)

    data = {}
    for filename in filelist:
        with zipfile.ZipFile(filename,"r") as zip_ref:
            foldersave = filename.split('.')[0]
            zip_ref.extractall(foldersave)
        datafile = foldersave+'/Raw Data.csv'
        d = np.loadtxt(datafile, delimiter=',',skiprows=1)
        data[filename] = d
    return data

def showdata(data):
    import pylab as plt
    n = len(data.keys())

    colors = ['g','b','y']
    coords = ['x','y','z']

    fig,axs = plt.subplots(nrows=3,ncols=n,figsize=(10,8))
    for j,key in enumerate(data.keys()):
        d = data[key]
        for i,(ax,color,coord) in enumerate(zip(axs[:,j],colors,coords)):
            ax.plot(d[:,0],d[:,i+1],color)
        #    if j==0:
        #        graphes.legende('','$a_'+coord+'$ (m/s$^2$)','',ax=ax)
        #graphes.legende('Times (s)','$a_'+coord+'$ (m/s$^2$)','',ax=ax)

    plt.show()


if __name__=='__main__':
    basefolder = connect.basefolder()
    date = '121223_'+str(time.time())
    folder = basefolder+'Phyphox/'+'date'
    # [1,2,3,4,5,6,7,8,9,10,11,12,13,14,16,17,18,19,20,21,22,23,24,25]#
    tel_numbers =np.arange(1,64,dtype=int)
    print(tel_numbers)
    base = connect_phone.ipbase()
    print(base)
    iplist = [base + str(100+tel) for tel in tel_numbers]
    run_serie(iplist,T=600,folder=date)
    #data = load(date+'/')
    #showdata(data)

    
