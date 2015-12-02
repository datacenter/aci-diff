#!/bin/python
################################################################################
#                        _    ____ ___   ____ ___ _____ _____                  #
#                       / \  / ___|_ _| |  _ \_ _|  ___|  ___|                 #
#                      / _ \| |    | |  | | | | || |_  | |_                    #
#                     / ___ \ |___ | |  | |_| | ||  _| |  _|                   #
#                    /_/   \_\____|___| |____/___|_|   |_|                     #
#                                                                              #
#                     == Cisco ACI Configuration Diff tool ==                  #
################################################################################
#                                                                              #
# [+] Written by:                                                              #
#  |_ Luis Martin (lumarti2@cisco.com)                                         #
#  |_ CITT Software CoE.                                                       #
#  |_ Cisco Advanced Services, EMEAR.                                          #
#                                                                              #
################################################################################
#                                                                              #
# Copyright (c) 2015-2016 Cisco Systems                                        #
# All Rights Reserved.                                                         #
#                                                                              #
#    Unless required by applicable law or agreed to in writing, this software  #
#    is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF   #
#    ANY KIND, either express or implied.                                      #
#                                                                              #
################################################################################

from acitoolkit.acitoolkit import Session, Credentials, Tenant, EPG, AppProfile, BridgeDomain
import sys
import json
import difflib
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()


def fatal(msg):
    """
    Prints and error message and aborts program execution
    """
    sys.stderr.write(msg+"\n")
    sys.exit(1)

def split_tenant(tenant):
    """
    Takes a full Tenant object and returns a dictionary that contains info 
    about all its children. Info is indexed by class name so, for example,
    data['BridgeDomain'] will return a dict of bridge domain objects, indexed by BD name
    """
    data={'Tenant' : tenant}
    children = tenant.get_children()
    for c in children:
        if str(c.__class__.__name__) not in data:
            data[c.__class__.__name__]= { c.name : c}
        else:
            data[c.__class__.__name__][c.name] = c
    return data


def retrieve(tenant_info, data_type, data_name):
    """
    Parses a tenant_info structure (dict) produced by split_tenant() and 
    extracts the relevant piece of information (object matching the supplied
    type and name)
    @return an object of the requested type or None if it doesn't exist
    """
    for el in tenant_info[data_type]:
        if el == data_name:
            return tenant_info[data_type][el]
    return None


def retrieve_3rd(tenant_info, middle_type, middle_name, data_type, data_name):
    """
    Parses a tenant_info structure (dict) produced by split_tenant() and 
    extracts the relevant 3rd level object. This is, it first extract the 
    relevan level 2 object (the one immediatly below the tenant level) and
    then it iterates over its list of children, looking for the requested 
    object (matching the supplied data_type and data_name). This is commonly
    used for 3rd level objects like EPGs.
    @return an object of the requested type or None if it doesn't exist
    """
    # Look for the object in the middle
    for el in tenant_info[middle_type]:
        # When we find it, extract its children
        if el == middle_name:
            children = tenant_info[middle_type][el].get_children()
            # Now let's see if one them is the object we are looking for
            for c in children:
                if c.__class__.__name__ == data_type:
                    if c.name == data_name:
                        return c
    # Game over
    return None


# Start of the execution
if __name__ == "__main__":
    
    items={ 'left'  : {},
            'right' : {}
          }

    # Argument parsing. We use the ACI toolkit logic here, which tries to
    # retrieve credentials from the following places:
    # 1. Command line options
    # 2. Configuration file called credentials.py
    # 3. Environment variables
    # 4. Interactively querying the user
    # At the end, we should have an object args with all the necessary info.
    description = 'APIC credentials'
    creds = Credentials('apic', description)
    creds.add_argument('-L', "--left", default=None, help='Object on the left')
    creds.add_argument('-R', "--right", default=None, help='Object on the right')
    creds.add_argument('-t', "--type", default=None, help='Object type')
    args = creds.get()
    
    # Arg validation
    if args.right is None:
        fatal("[E] Right object missing. Please pass it using --right <obj_name>")
    if args.left is None: 
        fatal("[E] Left object missing. Please pass it using --left <obj_name>")
    if args.type is None: 
        sys.stderr.write("[W] WARNING: No type supplied. Defaulting to 'Tenant'\n")
        args.type='Tenant'

    # Process the supplied left and right data, according to the supplied type
    
    # 1. Tenant object
    if args.type.lower() in [None, "tenant", "tn"]:
        args.type='Tenant'
        items['left']['Tenant']=args.left
        items['right']['Tenant']=args.right
    
    # 2. Objects right below the Tenant Level (AppProfile, BridgeDomain, Context)
    elif args.type.lower() in ["ap", "appprofile", "bd", "bridgedomain", "ctx", "context"]:
        # Normalize the type, based on user provided data
        if args.type.lower() in ["ap", "appprofile"]:
            args.type='AppProfile'
        elif args.type.lower() in ["bd", "bridgedomain"]:
            args.type="BridgeDomain"
        elif args.type.lower() in [ "ctx", "context"]:
            args.type="Context"
        # Extract the two members from Tenant/Whatever
        try:
            tenant_left, type_left = args.left.split("/")
            tenant_right, type_right= args.right.split("/")
            assert(tenant_left is not None and type_left is not None)
            assert(tenant_right is not None and type_right is not None)
            assert(len(tenant_left)>0 and len(type_left)>0)
            assert(len(tenant_right)>0 and len(type_right)>0)
            items['left']['Tenant']=tenant_left
            items['right']['Tenant']=tenant_right
            items['left'][args.type]=type_left
            items['right'][args.type]=type_right
        except:
            fatal("[E] Incorrect object format for the %s type." % args.type)
    
    # 3. Objects on the third level (EPG)
    elif args.type.lower() in ["epg", "endpoint"]:
        # Normalize the type, based on user provided data
        if args.type.lower() in ["epg", "endpoint"]:
            args.type='EPG'
        # Extract the three members from Tenant/AppProfile/EPG
        try:
            tenant_left, middle_left, type_left = args.left.split("/")
            tenant_right, middle_right, type_right= args.right.split("/")
            assert(tenant_left is not None and middle_left is not None and type_left is not None)
            assert(tenant_right is not None and middle_right is not None and type_right is not None)
            assert(len(tenant_left)>0 and len(middle_left)>0 and len(type_left)>0)
            assert(len(tenant_right)>0 and len(middle_right)>0 and len(type_right)>0)
            items['left']['Tenant']=tenant_left
            items['right']['Tenant']=tenant_right
            items['left'][args.type]=type_left
            items['right'][args.type]=type_right
            if args.type=="EPG":
                items['left']['AppProfile']=middle_left
                items['right']['AppProfile']=middle_right
        except:
            fatal("[E] Incorrect object format for the %s type." % args.type)
    
    # Now, we log into the APIC
    session = Session(args.url, args.login, args.password)
    response = session.login()
    if response.ok is False:
        print(response.content)
        sys.exit(1)
        
    # Retrieve Tenant data and split it into smaller components. Note that we
    # will keep reusing the "left" and "right" variables all the time until
    # we get to the object we need
    try:
        left  = Tenant.get_deep(session, [items['left']['Tenant']])[0]
        left  = split_tenant(left)
        right = Tenant.get_deep(session, [items['right']['Tenant']])[0]
        right = split_tenant(right)
    except:
        print("[E] Error, couldn't retrieve data from fabric")
        sys.exit(2)

    # Get the JSON output for the required left and right objects.
    # Level 1 objects
    if args.type == 'Tenant':
        left = left['Tenant']
        right = right['Tenant']
    
    # Level 2 objects
    elif args.type in ["AppProfile", "BridgeDomain", "Context"]:
        left = retrieve(left, args.type, items['left'][args.type])
        right = retrieve(right, args.type, items['right'][args.type])
    
    # Level 3 objects
    elif args.type in ["EPG"]:
        if args.type=="EPG":
            middle_type = "AppProfile"
        left = retrieve_3rd(left, middle_type, items['left'][middle_type], args.type, items['left'][args.type])
        right = retrieve_3rd(right, middle_type, items['right'][middle_type], args.type, items['right'][args.type])

    # Convert the raw JSON into printable output with proper indentation
    left  = json.dumps(left.get_json(), sort_keys=True, indent=4, separators=(',', ': ')).split("\n")
    right = json.dumps(right.get_json(), sort_keys=True, indent=4, separators=(',', ': ')).split("\n")
    
    # Finally, do the unified diff magic, using the stardard lib
    for line in difflib.unified_diff(left, right, fromfile='%s.json' % args.left, tofile='%s.json' % args.right):
        print(line)

    sys.exit(0)
    
