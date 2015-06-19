import json
from collections import defaultdict

from AccessControl.SecurityManagement import newSecurityManager
from Testing import makerequest

from zope.component.hooks import setSite


def getSite(app, site_id, admin_id='admin'):
    app = makerequest.makerequest(app)
    admin = app.acl_users.getUser(admin_id)  # RR: should we have a dedicated sync admin?
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
