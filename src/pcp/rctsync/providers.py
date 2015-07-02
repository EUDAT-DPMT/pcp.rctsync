#
# providers.py
#
# script to be invoked via
#
#  cd <your-buildout-root-dir>
#  bin/instance run src/pcp.rctsync/src/pcp/rctsync/providers.py
#
#  run with --help to see available options

import logging
from Products.PlonePAS.utils import cleanId
from pcp.rctsync import utils
from pcp.rctsync import relations

def prepareid(values):
    id = values['fields']['name'].encode('utf8')
    id = id.replace(' ','')
    return cleanId(id)

def preparedata(values, site, contact_map, user_map, community_map):

    logger = logging.getLogger('rctsync.providerdata')

    fields = values['fields'].copy()
    title = fields['name'].encode('utf8')
    data = {}
    additional = []
    additional.append({'key': 'contact',
                       'value': str(fields['contact']),
                       },
                      )
    additional.append({'key': 'admins',
                       'value': str(fields['admins']),
                       },
                      )
    additional.append({'key': 'communities_primary',
                       'value': str(fields['communities_primary']),
                       },
                      )
    additional.append({'key': 'communities_secondary',
                       'value': str(fields['communities_secondary']),
                       },
                      )
    additional.append({'key': 'rct_pk',
                       'value': str(values['pk']),
                       },
                      )

    rct_uid = fields['uuid']
    identifiers = [{'type':'rct_uid',
                    'value': rct_uid},
                    ]

    admin_uids = []
    for pk in fields['admins']:
        try:
            user = user_map[pk]
        except KeyError:
            logger.error("No user with pk=%s found (admin for %s)"%(pk,title))
            continue
        message = "Linking '%s' to '%s' as admin" % (user['name'], title)
        logger.debug(message)
        admin_uids.append(user['uid'])
    cp_uids = []
    for pk in fields['communities_primary']:
        message = "Linking '%s' to '%s' as primary community" % (community_map[pk]['name'], title)
        logger.debug(message)        
        cp_uids.append(community_map[pk]['uid'])
    cs_uids = []
    for pk in fields['communities_secondary']:
        message = "Linking '%s' to '%s' as secondary community" % (community_map[pk]['name'], title)
        logger.debug(message)
        cs_uids.append(community_map[pk]['uid'])

    osvocab = utils.getOspk2name()
    sos = [osvocab[index] for index in fields['supported_os']]
    data['supported_os'] = tuple(sos)  

    data['title'] = title
    data['description'] = fields['description']
    data['url'] = fields['website']
    data['address'] = {"country":fields['country']}
    data['getaccount'] = fields['getaccount']
    data['committed_cores'] = fields['committed_cores']
    data['committed_disk'] = fields['committed_disk']
    data['committed_tape'] = fields['committed_tape']
    data['used_disk'] = fields['used_disk']
    data['used_tape'] = fields['used_tape']
    
    data['identifiers'] = identifiers
    data['additional'] = additional

    # and now the relations
    cpk = fields['contact']
    try:
        contact = contact_map[cpk]
        message = "Linking '%s' as contact for '%s'" % (contact['name'], title)
        logger.debug(message)
        data['contact'] = contact['uid']
    except KeyError:
        if cpk == 21:  # Alberto Michelini has two contact data entries on RCT: 21 and 29
            contact = contact_map[29]
            message = "Linking '%s' (but as 29 not 21) as contact for '%s'" % (contact['name'], title)
            logger.warning(message)
            data['contact'] = contact['uid']
        else:
            logger.error("No user with pk=%s found (contact for %s)"%(cpk,title))
    data['admins'] = admin_uids
    data['communities_primary'] = cp_uids
    data['communities_secondary'] = cs_uids
    
    return data.copy()

def main(app):
    argparser = utils.getArgParser()
    logger = utils.getLogger('var/log/rctsync_providers.log')
    args = argparser.parse_args()
    logger.info("'providers.py' called with '%s'" % args)

    site = utils.getSite(app, args.site_id, args.admin_id)
    logger.info("Got site '%s' as '%s'" % (args.site_id, args.admin_id))

    targetfolder = site.providers
    rct_providers = utils.getData(args.filename, 'rct.provider')

    # we assume that people and communities are already available
    logger.info("Mapping out people")
    contact_map, user_map = relations.uid_maps(site, 'people', 'Person')

    logger.info("Mapping out communities")
    community_map = relations.uid_maps(site, 'communities', 'Community')
        
    logger.info("Iterating over the provider data")
    for pk, values in rct_providers.items():
        id = prepareid(values)
        if id is None:
            logger.warning("Couldn't generate id for ", values)
            continue
        if id not in targetfolder.objectIds():
            targetfolder.invokeFactory('Provider', id)
            logger.info("Added %s to the providers folder" % id)

        data = preparedata(values, site, contact_map, user_map, community_map)
        logger.debug(data)
        targetfolder[id].edit(**data)
        targetfolder[id].reindexObject()
        logger.info("Updated %s in the providers folder" % id)

    if not args.dry:
        logger.info("Committing changes to database")
        import transaction
        transaction.commit()
    else:
        logger.info("dry run; not committing anything")
            
    logger.info("Done")

# As this script lives in your source tree, we need to use this trick so that
# five.grok, which scans all modules, does not try to execute the script while
# modules are being loaded on start-up
if "app" in locals():
    main(app)
