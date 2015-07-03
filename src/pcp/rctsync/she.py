#
# she.py
#
# script to be invoked via
#
#  cd <your-buildout-root-dir>
#  bin/instance run src/pcp.rctsync/src/pcp/rctsync/she.py
#
#  run with --help to see available options

import logging
from Products.PlonePAS.utils import cleanId
from pcp.rctsync import utils
from pcp.rctsync import relations

def prepareid(values):
    #id = values['fields']['name'].encode('utf8')
    #id = id.replace(' ','')
    id = 'she'   # there should only be one per provider
    return cleanId(id)

def preparedata(values, site, contact_map):

    logger = logging.getLogger('rctsync.shedata')

    fields = values['fields'].copy()
    title = fields['name'].encode('utf8')
    data = {}
    additional = []
    additional.append({'key': 'contact',
                       'value': str(fields['contact']),
                       },
                      )
    additional.append({'key': 'provider',
                       'value': str(fields['provider']),
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

    data['title'] = title
    data['description'] = fields['description']
    data['account'] = fields['account']
    data['rootaccess'] = bool(fields['rootaccess']) #XXX Fix me, this is wrong
    data['setup_procedure'] = fields['setup_procedure']
    data['firewall_policy'] = fields['firewall_policy']
    data['text'] = fields['details']
    data['identifiers'] = identifiers
    data['additional'] = additional

    # XXX skipping Terms of use; they are hardly set and should become just a link
    logger.warning("Skipping terms of use for %s. Add the link manually later" % title)

    # and now the contact relation
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
    
    return data.copy()

def getTarget(site, data, provider_map):

    logger = logging.getLogger('rctsync.shetargetfinder')
    pk = None
    for entry in data['additional']:
        if entry['key'] == 'provider':
            pk = int(entry['value'])
            logger.debug("provider pk=%s for %s found" % (pk, data['title']))
            break
    if pk is None:
        logger.warning("%s has no provider set" % data['title'])
        return None
    try:
        provider = provider_map[pk]
    except KeyError:
        logger.error("No provider with pk=%s found" % pk)
        return None
    puid = provider['uid']
    logger.debug("Searching uid_catalog for %s" % puid)
    brains = site.uid_catalog(UID=puid)
    logger.debug("Found %s" % brains)
    try:
        target = brains[0].getObject()
        logger.info("Found %s as provider for %s" % (target.Title(), data['title']))
        return target
    except AttributeError, IndexError:
        logger.error("No content with uid=%s found" % puid)
        return None
    
            

def main(app):
    argparser = utils.getArgParser()
    logger = utils.getLogger('var/log/rctsync_she.log')
    args = argparser.parse_args()
    logger.info("'she.py' called with '%s'" % args)

    site = utils.getSite(app, args.site_id, args.admin_id)
    logger.info("Got site '%s' as '%s'" % (args.site_id, args.admin_id))

    targetfolder = site.providers
    rct_shes = utils.getData(args.filename, 'rct.she')

    # we assume that people are already available
    logger.info("Mapping out people")
    contact_map, user_map = relations.uid_maps(site, 'people', 'Person')
    logger.info("Mapping out providers")
    provider_map = relations.uid_maps(site, 'providers', 'Provider')

    logger.info("Iterating over the she data")
    for pk, values in rct_shes.items():
        data = preparedata(values, site, contact_map)
        target = getTarget(site, data, provider_map)
        if target is None:
            logger.error("No provider found for %s" % data['title'])
            continue
        id = prepareid(values)
        if id is None:
            logger.warning("Couldn't generate id for ", values)
            continue
        if id not in target.objectIds():
            target.invokeFactory('Environment', id)
            logger.info("Added %s to the respective provider's folder" % id)

        logger.debug(data)
        target[id].edit(**data)
        target[id].reindexObject()
        logger.info("Updated %s in the respective provider's folder" % id)

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
