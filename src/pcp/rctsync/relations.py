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

def uid_maps(site, target_path, ptype):

    logger = logging.getLogger('rctsync.uid_maps')
    mapping = {}
    contact_mapping = {}
    user_mapping = {}
    
    try:
        target = site[target_path]
    except KeyError:
         logger.error("no target folder '%s' found" % target_path)
         return None

    for content in target.contentValues():
        logger.debug(content.Title())
        if content.portal_type != ptype:
            logger.debug("Not of '%s' type: %s" % (ptype, content.Title()))
            continue
        additional = content.getAdditional()
        rct_pk = None
        rct_contact_pk = None
        rct_user_pk = None
        rct_user_inferred = None

        for item in additional:
            if item['key'] == 'rct_pk':
                rct_pk = item['value']
                message = "%s has rct_pk %s" % (content.Title(), rct_pk)
                logger.debug(message)
                break
            # special case for user mappings
            if item['key'] == 'rct_contact_pk':
                rct_contact_pk = item['value']
                message = "%s has rct_contact_pk %s" % (content.Title(), rct_contact_pk)
                logger.debug(message)
            if item['key'] == 'rct_user_pk':
                rct_user_pk = item['value']
                message = "%s has rct_user_pk %s" % (content.Title(), rct_user_pk)
                logger.debug(message)
            if item['key'] == 'rct_user_inferred':
                rct_user_inferred = item['value']
                message = "%s has rct_user_inferred %s" % (content.Title(), rct_user_inferred)
                logger.debug(message)

        if rct_pk not in [None, 'None']:
            pk = int(rct_pk)
            mapping[pk] = dict(uid=content.UID(), name=content.Title())
            message = "mapping %s to %s (%s)" % (pk, content.UID(), content.Title())
            logger.debug(message)
        else:
            logger.debug("'%s (%s)' has no corresponding 'rct_pk'" % (content.Title(), content.absolute_url()))

        if rct_contact_pk not in [None, 'None']:
            pk = int(rct_contact_pk)
            contact_mapping[pk] = dict(uid=content.UID(), name=content.Title())
            message = "contact mapping %s to %s (%s)" % (pk, content.UID(), content.Title())
            logger.debug(message)
        else:
            logger.debug("'%s (%s)' has no corresponding 'rct_contact_pk'" % (content.Title(), content.absolute_url()))    

        if rct_user_pk or rct_user_inferred:
            try:
                upk = int(rct_user_pk)
            except TypeError, ValueError:
                upk = 0
            try:
                ipk = int(rct_user_inferred)
            except TypeError, ValueError:
                ipk = 0
            pk = upk or ipk
            if pk:
                user_mapping[pk] = dict(uid=content.UID(), name=content.Title())
                message = "user mapping %s to %s (%s)" % (pk, content.UID(), content.Title())
                logger.debug(message)
        else:
            logger.debug("'%s (%s)' has no corresponding 'rct_user_pk'" % (content.Title(), content.absolute_url()))    

    if mapping:
        return mapping.copy()
    else:
        return contact_mapping.copy(), user_mapping.copy()
    
def relate_communities(site, contact_map, user_map):
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
                community.setRepresentative(contact_map[pk]['uid'])
                community.reindexObject()
                logger.info("setting '%s' (%s) as representative for '%s'", 
                            contact_map[pk]['name'],
                            pk,
                            community.Title())
            except KeyError:
                logger.error( "no person with pk '%s' found in contact_map." % pk)

        else:
            message = "'%s' has no representative set (set to %s)" % (community.Title(), 
                                                                      representative_pk)
            logger.warning(message)

        if admin_pks not in [None, 'None']:
            pks = eval(admin_pks)
            if pks == []:
                message = "'%s' has no admins set (set to [])" % community.Title()
                logger.warning(message)
                
            uids = []
            for pk in pks:
                try:
                    uids.append(user_map[pk]['uid'])
                    logger.info("Adding '%s' (%s) as admin to '%s' " % (user_map[pk]['name'],
                                                                        pk, 
                                                                        community.Title()))
                except KeyError:
                    logger.error("no person with pk '%s' found in user_map." % pk)

            community.setAdmins(uids)
            community.reindexObject()
        else:
            message = "'%s' has no admins set (set to %s)" % (community.Title(),
                                                              admin_pks)
            logger.warning(message)

def relate_projects(site, contact_map, community_map):
    logger = logging.getLogger('rctsync.relate_projects')
    for project in site.projects.contentValues():
        if project.portal_type != 'Project':
            logger.debug("Not a project: ", project.Title())
            continue
        community_pk = None
        contact_pk = None
        additional = project.getAdditional()
        
        for item in additional:
            if item['key'] == 'contact':
                contact_pk = item['value']
                logger.debug("'%s' has representative '%s'" % (project.Title(),
                                                               item['value']))
            elif item['key'] == 'community':
                community_pk = item['value']
                logger.debug("'%s' has '%s' as contact" % (project.Title(),
                                                           item['value']))
            
        if contact_pk not in [None, 'None']:
            pk = int(contact_pk)
            try:
                project.setCommunity_contact(contact_map[pk]['uid'])
                project.reindexObject()
                logger.info("setting '%s' (%s) as community contact for '%s'", 
                            contact_map[pk]['name'],
                            pk,
                            project.Title())
            except KeyError:
                logger.error( "no person with pk '%s' found." % pk)

        else:
            message = "'%s' has no 'community contact' set (set to %s)" % (project.Title(), 
                                                                           contact_pk)
            logger.warning(message)

        if community_pk not in [None, 'None']:
            pk = int(community_pk)
            try:
                project.setCommunity(community_map[pk]['uid'])
                project.reindexObject()
                logger.info("setting'%s' (%s) as community for '%s' " % (community_map[pk]['name'],
                                                                         pk, 
                                                                         project.Title()))
            except KeyError:
                logger.error("no community with pk '%s' found." % pk)
        else:
            message = "'%s' has no 'community' set (set to %s)" % (project.Title(),
                                                                   community_pk)
            logger.warning(message)


def main(app):
    argparser = utils.getArgParser()
    logger = utils.getLogger()
    args = argparser.parse_args()
    logger.info("'relations.py' called with '%s'" % args)

    site = utils.getSite(app, args.site_id, args.admin_id)
    logger.info("Got site '%s' as '%s'" % (args.site_id, args.admin_id))

    logger.info("Mapping out people")
    contact_map, user_map = uid_maps(site, 'people', 'Person')

    logger.info("Mapping out communities")
    community_map = uid_maps(site, 'communities', 'Community')

    logger.info("relating communities to people")
    relate_communities(site, contact_map, user_map)

    logger.info("relating projects to communities and people")
    relate_projects(site, contact_map, community_map)

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
