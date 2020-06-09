#!/usr/bin/python

# mona_ropshell: it adds http://ropshell.com/about support to Mona.py. Used to check loaded modules (dlls) on ropshell.com, query it and extract useful gadgets
# Based on Python 2.7.17
# Date: 09/06/2020
# Author: Paolo Stagno (@Void_Sec) - https://voidsec.com

'''
Usage: mona_ropshell.py modules.txt
feed mona_ropshell with a file cointaining the results of the execution of !mona modules command
'''
import sys
import os
import argparse
import re
import requests
import hashlib
from bs4 import BeautifulSoup
from prettytable import PrettyTable


def parse(inputfile, outputfile):
    print("[-] Reading modules from input file...")
    modules=[]
    with open(inputfile) as content:
        for line in content:
            # check if line contains module
            if re.search("\(.*\)", line):
                # get module full path
                path=re.findall("\(.*\)", line)
                path=path[0]
                path=path[1:-1]
                # get module name
                name=(os.path.basename(path))
                # get module flags
                flags=re.findall("\|.*\|",line)
                #|     | Top  | Size   | Rebase  | SafeSEH | ASLR     | NXCompat | OS Dll |   |
                #| 0   | 1    | 2      | 3       | 4       | 5        | 6        | 7      | 8 |
                flags=flags[0].split("|")
                modules.append([name, path, flags[3].replace(" ", "").replace("False", "X").replace("True", "V"), flags[4].replace(" ", "").replace("False", "X").replace("True", "V"), flags[5].replace(" ", "").replace("False", "X").replace("True", "V"), flags[6].replace(" ", "").replace("False", "X").replace("True", "V"), flags[7].replace(" ", "").replace("False", "X").replace("True", "V")])
    #print(modules)
    hash_calc(modules, outputfile)
    return


def hash_calc(modules, outputfile):
    print("[-] Calculating modules hashes...")
    for item in modules:
        item.append(hashlib.md5(open(item[1],'rb').read()).hexdigest())
    ropshell_fetch(modules, outputfile)
    return
    

def ropshell_fetch(modules, outputfile):
    print("[-] Querying Ropshell")
    tbl = PrettyTable()
    tbl.field_names = ["Module Name", "Path", "Rebase", "SafeSEH", "ASLR", "NX", "OS Dll", "Hash", "Ropshell", "# Gadgets"]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:55.0) Gecko/20100101 Firefox/55.0"}
    for module in modules:
        print("\t[-] {} - {}".format(module[0], module[7]))
        result = requests.get("http://ropshell.com/ropsearch?h={}".format(module[7]), headers=headers)
        if result.status_code == 200:
            web = result.content
            soup = BeautifulSoup(web, "html.parser")
            #print(soup.prettify())
            page = soup.find_all("div", "content")
            if page:
                for tag in page:
                    content = tag.find("pre")
                    if content.contents[0].strip("\n") == "[]":
                        module.append("Not Found")
                        module.append("0")
                    else:
                        module.append("V")
                        gadgets_n=re.findall("total gadgets:.*",content.getText())
                        gadgets_n=gadgets_n[0].split(":")
                        module.append(gadgets_n[1].lstrip())
                        print("\t\t[-] Downloading gadgets...")
                        #http://ropshell.com/static/txt/226049bc657b3884e96c5b9edc908cd7.txt.gz
                        download_url = "http://ropshell.com/static/txt/{}.txt.gz".format(module[7])
                        req = requests.get(download_url, allow_redirects=True)
                        open(os.getcwd()+os.path.sep+module[0]+".gz", "wb").write(req.content)
                    tbl.add_row([module[0],module[1],module[2],module[3],module[4],module[5],module[6],module[7],module[8],module[9]])
            else:
                print("[!] Error, is the site still alive and the same?")
        else:
            print("[!] Error, something went wrong with the request")
    print("\n")
    print(tbl)
    open(outputfile,"w").write(tbl.get_string())
    print("\n[+] DONE")
    return


def main():
    parser = argparse.ArgumentParser(prog="mona_ropshell.py ",
                                     description="For all loaded modules, fetch ROP gadgets querying Ropshell DB.")
    parser.add_argument("-i", dest="inputfile", required=True, metavar="FILE", help="Modules file's list.")
    parser.add_argument("-o", dest="outputfile", required=True, metavar="FILE", help="Gadgets' recap file name.")
    args = parser.parse_args()
    print("Mona Ropshell:\n--------------------------------------")
    parse(args.inputfile, args.outputfile)
    sys.exit


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("CTRL+C, quitting...")
        sys.exit(1)
    sys.exit
