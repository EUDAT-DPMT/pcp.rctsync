import json
import argparse
from collections import defaultdict

from AccessControl.SecurityManagement import newSecurityManager
from Testing import makerequest

from zope.component.hooks import setSite


def getArgParser():
    parser = argparse.ArgumentParser(description='The rctsync package provides scripts to '\
                                     'transfer data from the resource coordination tool to '\
                                     'the data project coordination portal.')
    parser.add_argument("-s", "--site_id", default="pcp", 
                        help="internal id of the Plone site object (default: 'pcp')")
    parser.add_argument("-f", "--filename", default="data/rct_dump_20150609.json", 
                        help="relative path to the input data file "\
                        "(default: 'data/rct_dump_20150609.json')")
    parser.add_argument("-a", "--admin_id", default="admin", 
                        help="all changes and additions will be shown as from this user"\
                        " (default: 'admin')")
    parser.add_argument("-d", "--dry", action='store_true',
                        help="dry run aka nothing is saved to the database")
    parser.add_argument("-c", "--command", 
                        help="name of the script invoked. Set automatically. It is here"\
                        "to keep the 'argparse' module happy")
    return parser
    

def getSite(app, site_id, admin_id):
    app = makerequest.makerequest(app)
    admin = app.acl_users.getUser(admin_id)
    admin = admin.__of__(app.acl_users)
    newSecurityManager(None, admin)

    site = app.get(site_id, None)

    if site is None:
        print "'%s' not found (maybe a typo?)." % site_id
        print "To create a site call 'import_structure' first."
        raise ValueError

    setSite(site)  # enable lookup of local components

    return site
    

def getData(path, model=None):
    source = open(path,'r')
    raw = json.load(source)
    rct_data = defaultdict(dict)

    # cast the raw data into some nested structure for easy access later
    for item in raw:
        rct_data[item['model']][item['pk']] = item.copy()
    if not model:
        return rct_data.copy()
    else:
        return rct_data[model].copy()
