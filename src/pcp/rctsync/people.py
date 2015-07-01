#
# content.py
#
# script to be invoked via
#
#  cd <your-buildout-root-dir>
#  bin/instance run src/pcp.rctsync/src/pcp/rctsync/people.py
#
#  run with --help to see available options

# This is very specific as it includes the logic according
# to which the rct.contactdata and auth.user models of the
# RCT are merged.

import logging
from Products.PlonePAS.utils import cleanId
from pcp.rctsync import utils


def prepareid(values):
    logger = logging.getLogger('rctsync.people')
    fn = values['fields']['first_name'].encode('utf8')
    ln = values['fields']['last_name'].encode('utf8')
    id = "%s-%s" % (fn,ln)
    id = id.replace(' ','')
    if id == '-':
        generated = "rct-user-%s" % values['pk']
        message = "auth.user '%s' has no name set. Using '%s' instead." \
          % (values['pk'], generated)
        logger.warning(message)
        return cleanId(generated)
    logger.debug("Generating id based on '%s'" % id)
    return cleanId(id)

def prepareuserdata(values):
    logger = logging.getLogger('rctsync.prepareuserdata')
    fields = values['fields'].copy()
    
    data = {}
    name = {}
    additional = []

    name['firstnames'] = fields['first_name']
    name['lastname'] = fields['last_name']
    title = ' '.join([name['firstnames'], name['lastname']])
    if not title:
        title = "RCT User ", values['pk']
        
    additional.append({'key': 'rct_user_pk',
                       'value': str(values['pk']),
                       },
                      )    
    additional.append({'key':'rct_username',
                       'value':values['fields']['username'],
                       },
                      )
    
    data['name'] = name.copy()
    data['title'] = title
    data['email'] = fields['email']
    data['additional'] = additional
    
    return data.copy()

    
def preparedata(values, rct_users, email2userpk):
    logger = logging.getLogger('rctsync.preparedata')

    fields = values['fields'].copy()
    
    data = {}
    name = {}
    phone = []
    identifiers = []
    additional = []

    name['firstnames'] = fields['first_name']
    name['lastname'] = fields['last_name']
    title = ' '.join([name['firstnames'], name['lastname']])
    email = fields['email']

    phonenumber = fields['phone']
    if phonenumber:
        value = {}
        value['type'] = 'Office'
        value['number'] = phonenumber
        phone.append(value.copy())

    rct_uid = fields['uuid']
    identifiers = [{'type':'rct_uid',
                    'value': rct_uid},
                    ]

    additional.append({'key':'rct_user_pk',
                       'value':fields['rct_user']}
                       )
    additional.append({'key':'website',
                       'value':fields['website']}
                       )
    additional.append({'key':'address',
                       'value':fields['address']}
                       )
    additional.append({'key':'organization',
                       'value':fields['organization']}
                       )
    additional.append({'key': 'rct_contact_pk',
                       'value': str(values['pk']),
                       },
                      )
    
    userpk = fields['rct_user']
    if userpk:
        additional.append({'key':'rct_username',
                           'value':rct_users[userpk]['fields']['username'],
                           },
                          )
        rct_users[userpk]['covered'] = True
        logger.info("Updating '%s' with user data" % title)
    elif email2userpk.has_key(email):
        username = rct_users[email2userpk[email]]['fields']['username']
        additional.append({'key':'rct_username',
                           'value':username,
                           },
                          )
        rct_users[email2userpk[email]]['covered'] = True
        logger.warning("Updating '%s' with user data inferred via email match." % title)
    else:
        logger.warning("No user data found for %s" % title)
    
    data['name'] = name.copy()
    data['title'] = title
    if phone:
        data['phone'] = phone
    data['email'] = email
    data['identifiers'] = identifiers
    data['additional'] = additional
    
    return data.copy()


def main(app):
    argparser = utils.getArgParser()
    logger = utils.getLogger('var/log/rctsync_people.log')
    args = argparser.parse_args()
    logger.info("'people.py' called with '%s'" % args)

    site = utils.getSite(app, args.site_id, args.admin_id)
    logger.info("Got site '%s' as '%s'" % (args.site_id, args.admin_id))

    targetfolder = site.people
    rct_contacts = utils.getData(args.filename, 'rct.contactdata')
    rct_users = utils.getData(args.filename, 'auth.user')
    email2userpk = utils.email2userpk(rct_users)

    logger.info("Iterating over the contact data")
    for pk, values in rct_contacts.items():
        id = prepareid(values)
        if id is None:
            logger.error("Couldn't generate id for ", values)
            continue
        if id not in targetfolder.objectIds():
            targetfolder.invokeFactory('Person', id)
            logger.info("Added '%s' to the people folder" % id)
        else:
            logger.info("Found '%s' in people folder" % id)

        data = preparedata(values, rct_users, email2userpk)
        logger.debug(data)
        targetfolder[id].edit(**data)
        targetfolder[id].reindexObject()
        logger.info("Updated '%s' in the people folder" % id)

    # and now almost the same for the user data
    logger.info("Iterating over the user data.")
    for pk, values in rct_users.items():
        if rct_users[pk].has_key('covered'):
            logger.info("user '%s' already covered." % pk)
            continue
        id = prepareid(values)
        if id is None:
            logger.error("Couldn't generate id for ", values)
            continue
        if id not in targetfolder.objectIds():
            targetfolder.invokeFactory('Person', id)
            logger.info("Added '%s' to the people folder" % id)
        else:
            # this should not happen
            logger.warning("Found '%s' in people folder; skipping" % id)
            continue
        data = prepareuserdata(values)
        logger.debug(data)
        targetfolder[id].edit(**data)
        targetfolder[id].reindexObject()
        logger.info("Updated '%s' in the people folder" % id)
        

    if not args.dry:
        logger.info("committing changes to db")
        import transaction
        transaction.commit()
    else:
        logger.info("dry run; not committing anything")
            
    logger.info("Done with synchronizing people")

# As this script lives in your source tree, we need to use this trick so that
# five.grok, which scans all modules, does not try to execute the script while
# modules are being loaded on start-up
if "app" in locals():
    main(app)
