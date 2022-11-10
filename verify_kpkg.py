#!/router/bin/python
#-------------------------------------------------------------------------
#
# Script to verify Key Package.
# This copyright has to be modified when publishing this script to github.
#
# Sep 2021, Sameer Pasha
#
# Copyright (c) 2022 by cisco Systems, Inc.
# All rights reserved.
#-------------------------------------------------------------------------

import argparse
import json
from kpkg_cmn import *

def unTar(fname):
    cmd = UNTAR+tmp+" -xvf "+tmp+fname
    kdbg("Cmd: "+cmd)
    status, log = getstatusoutput(cmd)
    if (status != 0):
        print("Failed to Untar file:"+log)
        kcleanup_exit()


def cleanTemp():
    global tmp
    tmp = TEMPDIR
    cmd = MKDIRCMD+tmp
    kdbg("Cmd: "+cmd)
    status, log = getstatusoutput(cmd)
    if (status != 0):
        print("Failed to create temp directory:"+log)
        kcleanup_exit()
    cmd = RMCMD+tmp+"*"
    kdbg("Cmd: "+cmd)
    status, log = getstatusoutput(cmd)
    if (status != 0):
        print("Failed to cleanup temp directory:"+log)
        kcleanup_exit()
    kdbg("Temp directory set to: "+tmp)

def copyPkg(pkgf, ns):
    global tmp
    dest = ""
    if ns:
        dest = TARFILE
    cmd = "cp "+pkgf+" "+tmp+dest
    kdbg("Cmd: "+cmd)
    status, log = getstatusoutput(cmd)
    if (status != 0):
        print("Failed to copy file:"+log)
        kcleanup_exit()

def verifyPkg(pkgf, pubkey):
    global tmp
    head, pfile = os.path.split(pkgf)
    ssl_cmd = "openssl smime -inform DER -verify -CAfile "
    ssl_cmd += pubkey+" -partial_chain -in "+tmp+pfile+" -out "+tmp+TARFILE
    kdbg("Cmd: "+ssl_cmd)
    status, log = getstatusoutput(ssl_cmd)
    if (status != 0) or ("Verification successful" not in log):
        print("Failed to verify file:"+log)
        kcleanup_exit()

def ValidateVersionTwo(jobj):
    for key in jobj:
        if key not in sacret_str:
            print("Invalid line found in JSON file:"+key)
            kcleanup_exit()
        else:
            if key == sacret_str[1]:
                sanitizeOperation(jobj[key])
                continue
            if key == sacret_str[2]:
                sanitizeTarget(jobj[key])
                continue
            if key == sacret_str[3]:
                sanitizeUsage(jobj[key])
                continue
            if key == sacret_str[4]:
                sanitizeAdditional(jobj[key])
                continue
            if key == sacret_str[5]:
                sanitizeTimestamp(jobj[key])
                continue
            if key == sacret_str[6]:
                sanitizeKeyType(jobj[key])
                continue

def VerifyBlist(fname, nosign, pubkey):
    if not nosign:
        # Verify Key package
        verifyPkg(fname, pubkey)
    else:
        # Untar file
        unTar(os.path.basename(fname))

        # Sanitize config.txt
        sanitizeConfigFile(nosign, pubkey)
    kdbg(fname+" : Verification complete")

def ValidateVersionTwoConfig(jobj, nosign, pubkey):
    if sacret_str[7] in jobj:
        kdbg("Key Package Bundle found.")
        flist = jobj["PACKAGE_LIST"]
        alist = flist[trgt[0]]
        rlist = flist[trgt[1]]
        kdbg("Allowed List and Revoked List in bundle:")
        kdbg(alist)
        kdbg(rlist)
        for x in alist:
            VerifyBlist(x, nosign, pubkey)
        for x in rlist:
            VerifyBlist(x, nosign, pubkey)
        kdbg("Bundle verification complete")
    else:
        ValidateVersionTwo(jobj)

def sanitizeConfigFile(nosign, pubkey):
    global tmp
    global CONFIG

    with open(tmp+CONFIG, 'r') as f:
        jobj = json.load(f)

        # Check version
        if jobj[sacret_str[0]] == 1:
            print("Invalid version 1 found in key package")
            kcleanup_exit()
        
        if jobj[sacret_str[0]] == 2:
            kdbg("Key package Version 2")
            ValidateVersionTwoConfig(jobj, nosign, pubkey)
        else:
            print("Invalid version found in key package")
            kcleanup_exit()


def ValidateKeyPackage(kpkg, nosign, pubkey):
    cleanTemp()
    # Misc
    copyPkg(kpkg, nosign)

    if not nosign:
        # Verify Key package
        verifyPkg(kpkg, pubkey)

    # Untar file
    unTar(TARFILE)

    # Sanitize config.txt
    sanitizeConfigFile(nosign, pubkey)


def main():

    parser = argparse.ArgumentParser(description="Verify a Signed or Unsigned Key Package or Key Package Bundle")
    parser.add_argument('-p', '--pubkey', required=False, help="Verification public key")
    parser.add_argument('-f', '--keypackage', required=True, type=str,
                        help="Key package to be verified")
    parser.add_argument('-n', '--nosign', required=False, action='store_true',
                        help="Unsigned Key Package to be verified.")
    parser.add_argument('-x', '--tempdir', required=False, help="Temporary directory to be used")
    parser.add_argument('-v', '--verbose', required=False, action='store_true',
                        help="Verbose information")

    args = parser.parse_args()

    # Set debug
    if args.verbose:
        setDbg(1)

    if not args.nosign:
        if not args.pubkey:
            print("Valid public key is needed for verifying signed packages")
            kcleanup_exit()

    # Set TEMP directory
    global TEMPDIR
    if args.tempdir:
        TEMPDIR = args.tempdir+"/"
    else:
        TEMPDIR = "/tmp/KPKG_TMPDIR/"
    cleanTemp()

    ValidateKeyPackage(args.keypackage, args.nosign, args.pubkey)

    print("Key package is valid")

if __name__ == "__main__":
    main()

