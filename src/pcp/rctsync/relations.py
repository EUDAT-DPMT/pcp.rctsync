#
# relations.py
#
# script to be invoked via
#
#  cd <your-buildout-root-dir>
#  bin/instance run src/pcp.rctsync/src/pcp/rctsync/relations.py
#  
#  The SITE_ID is hard coded as 'pcp'

SITE_ID = site_id = 'pcp'

from Products.PlonePAS.utils import cleanId
from pcp.rctsync import utils

def map_people(site):
    
    mapping = {}

    for person in site.people.contentValues():
        if person.portal_type != 'Person':
            print "Not a person: ", person.Title()
            continue
        additional = person.getAdditional()
        rct_pk = None

        for item in additional:
            if item['key'] == 'rct_pk':
                rct_pk = item['value']
                break

        if rct_pk is not None:
            pk = int(rct_pk)
            mapping[pk] = person.UID()

    return mapping.copy()
            
def relate_communities(site, people_map):
    for community in site.communities.contentValues():
        if community.portal_type != 'Community':
            print "Not a community: ", community.Title()
            continue
        representative_pk = None
        admin_pks = None
        additional = community.getAdditional()
        
        for item in additional:
            if item['key'] == 'representative':
                representative_pk = item['value']
            elif item['key'] == 'admins':
                admin_pks = item['value']
            
        if representative_pk not in [None, 'None']:
            pk = int(representative_pk)
            try:
                community.setRepresentative(people_map[pk])
                community.reindexObject()
                print "Setting representative for ", community.Title()
            except KeyError:
                print "### Error: no person with pk %s found." % pk

        if admin_pks not in [None, 'None']:
            pks = eval(admin_pks)
            uids = []
            for pk in pks:
                try:
                    uids.append(people_map[pk])
                except KeyError:
                    print "### Error: no person with pk %s found." % pk

            community.setAdmins(uids)
            community.reindexObject()
            print "Setting admins for ", community.Title()
                    

def main(app):
    site = utils.getSite(app, site_id)
    people_map = map_people(site)
    relate_communities(site, people_map)

    import transaction
    transaction.commit()

# As this script lives in your source tree, we need to use this trick so that
# five.grok, which scans all modules, does not try to execute the script while
# modules are being loaded on start-up
if "app" in locals():
    main(app)
