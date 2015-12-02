
                        _    ____ ___   ____ ___ _____ _____
                       / \  / ___|_ _| |  _ \_ _|  ___|  ___|
                      / _ \| |    | |  | | | | || |_  | |
                     / ___ \ |___ | |  | |_| | ||  _| |  _|
                    /_/   \_\____|___| |____/___|_|   |_|

                     == Cisco ACI Configuration Diff tool ==


Introduction
=============
ACI Diff is a simple tool to compare different objects on an ACI fabric. 
It currently allows comparing the following types of objects:

- Tenant
- BridgeDomain
- Context
- AppProfile
- EPG

Requirements
=============
- Python 2.7 or Python3.3 or above.
- The "acitoolkit" library
  - Download it from the following URL and install it using "python2.7 setup.py install"
    - https://github.com/datacenter/acitoolkit

Usage
=====

    $ acidiff.py --left <OBJ_PATH> --right <OBJ_PATH> --type <OBJ_TYPE>

The application also takes the regular parameters for APIC address, userna and 
password, as well as parses any existing *credentials.py* file stored in the
same directory. In that case, the content of the *credentials.py* file must 
follow this format:

    URL="https://192.168.0.90"
    LOGIN="admin"
    PASSWORD="Ap1cPass123"

If the *credentials.py* does not exist and the credentials are not supplied from
the command line, the application will ask for them interactively.

Usage Examples
==============

    $ ./acidiff.py -L "POD1/My_Expenses" -R "POD2/TTA" -t AP -l admin -p "Ap1cPass123" -u "https://192.168.0.90"
    $ ./acidiff.py -L "POD1/My_Expenses" -R "POD2/TTA" -t AP
    $ ./acidiff.py -L "POD2/TTA/Web" -R "POD3/POD3_ESX_AP/POD3_L2_EXT" -t EPG


Output Examples
===============

    $ ./acidiff.py -L POD2/TTA/Web -R POD3/POD3_ESX_AP/POD3_L2_EXT -t EPG
    --- POD2/TTA/Web.json
    
    +++ POD3/POD3_ESX_AP/POD3_L2_EXT.json
    
    @@ -1,13 +1,20 @@
    
     {
         "fvAEPg": {
             "attributes": {
    -            "name": "Web"
    +            "name": "POD3_L2_EXT"
             },
             "children": [
                 {
    +                "fvRsProv": {
    +                    "attributes": {
    +                        "tnVzBrCPName": "export_ICMP"
    +                    }
    +                }
    +            },
    +            {
                     "fvRsBd": {
                         "attributes": {
    -                        "tnFvBDName": "Web"
    +                        "tnFvBDName": "bd-300"
                         }
                     }
                 }
    
    
    
    $ ./acidiff.py -L POD2/TTA -R POD3/POD3_ESX_AP -t AppProfile
    --- POD2/TTA.json
    
    +++ POD3/POD3_ESX_AP.json
    
    @@ -1,19 +1,26 @@
    
     {
         "fvAp": {
             "attributes": {
    -            "name": "TTA"
    +            "name": "POD3_ESX_AP"
             },
             "children": [
                 {
                     "fvAEPg": {
                         "attributes": {
    -                        "name": "Web"
    +                        "name": "POD3_L2_EXT"
                         },
                         "children": [
                             {
    +                            "fvRsProv": {
    +                                "attributes": {
    +                                    "tnVzBrCPName": "export_ICMP"
    +                                }
    +                            }
    +                        },
    +                        {
                                 "fvRsBd": {
                                     "attributes": {
    -                                    "tnFvBDName": "Web"
    +                                    "tnFvBDName": "bd-300"
                                     }
                                 }
                             }

    
    
    
