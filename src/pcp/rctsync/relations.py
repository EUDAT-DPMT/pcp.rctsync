#
# relations.py
#
# script to be invoked via
#
#  cd <your-buildout-root-dir>
#  bin/instance run src/pcp.rctsync/src/pcp/rctsync/relations.py [options]
#  
#  run with --help to see available options

from Products.PlonePAS.utils import cleanId
from pcp.rctsync import utils
import logging

def map_people(site):

    logger = logging.getLogger('rctsync.map_people')
    mapping = {}

    for person in site.people.contentValues():
        logger.debug(person.Title())
        if person.portal_type != 'Person':
            logger.debug("Not a person: ", person.Title())
            continue
        additional = person.getAdditional()
        rct_pk = None

        for item in additional:
            if item['key'] == 'rct_pk':
                rct_pk = item['value']
                message = "%s has rct_pk %s" % (person.Title(), rct_pk)
                logger.debug(message)
                break

        if rct_pk is not None:
            pk = int(rct_pk)
            mapping[pk] = dict(uid=person.UID(), name=person.Title())
            message = "mapping %s to %s (%s)" % (pk, person.UID(), person.Title())
            logger.debug(message)
        else:
            logger.warning("'%s (%s)' has no corresponding 'rct_pk'" % (person.Title(), person.absolute_url()))    

    return mapping.copy()
            
def relate_communities(site, people_map):
    logger = logging.getLogger('rctsync.relate_communities')
    for community in site.communities.contentValues():
        if community.portal_type != 'Community':
            logger.debug("Not a community: ", community.Title())
            continue
        representative_pk = None
        admin_pks = None
        additional = community.getAdditional()
        
        for item in additional:
            if item['key'] == 'representative':
                representative_pk = item['value']
                logger.debug("'%s' has representative '%s'" % (community.Title(),
                                                               item['value']))
            elif item['key'] == 'admins':
                admin_pks = item['value']
                logger.debug("'%s' has admins '%s'" % (community.Title(),
                                                       item['value']))
            
        if representative_pk not in [None, 'None']:
            pk = int(representative_pk)
            try:
                community.setRepresentative(people_map[pk]['uid'])
                community.reindexObject()
                logger.info("setting '%s' (%s) as representative for '%s'", 
                            people_map[pk]['name'],
                            pk,
                            community.Title())
            except KeyError:
                logger.error( "no person with pk '%s' found." % pk)

        else:
            message = "'%s' has no representative set (set to %s)" % (community.Title(), 
                                                                      representative_pk)
            logger.warning(message)

        if admin_pks not in [None, 'None']:
            pks = eval(admin_pks)
            if pks == []:
                message = "'%s' has no admins set (set to [])", community.Title()
                logger.warning(message)
                
            uids = []
            for pk in pks:
                try:
                    uids.append(people_map[pk]['uid'])
                    logger.info("Adding '%s' (%s) as admin to '%s' " % (people_map[pk]['name'],
                                                                        pk, 
                                                                        community.Title()))
                except KeyError:
                    logger.error("no person with pk '%s' found." % pk)

            community.setAdmins(uids)
            community.reindexObject()
        else:
            message = "'%s' has no admins set (set to %s)" % (community.Title(),
                                                              admin_pks)
            logger.warning(message)


def main(app):
    argparser = utils.getArgParser()
    logger = utils.getLogger()
    args = argparser.parse_args()
    logger.info("'relations.py' called with '%s'" % args)
    site = utils.getSite(app, args.site_id, args.admin_id)
    logger.info("Got site '%s' as '%s'" % (args.site_id, args.admin_id))
    logger.info("Mapping out people")
    people_map = map_people(site)
    logger.info("relating communities to people")
    relate_communities(site, people_map)

    if not args.dry:
        logger.info("committing changes to db")
        import transaction
        transaction.commit()
    else:
        logger.info("dry run; not committing anything")

# As this script lives in your source tree, we need to use this trick so that
# five.grok, which scans all modules, does not try to execute the script while
# modules are being loaded on start-up
if "app" in locals():
    main(app)
