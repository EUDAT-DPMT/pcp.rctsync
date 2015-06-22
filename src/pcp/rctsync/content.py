#
# content.py
#
# script to be invoked via
#
#  cd <your-buildout-root-dir>
#  bin/instance run src/pcp.rctsync/src/pcp/rctsync/content.py
#
#  run with --help to see available options

from Products.PlonePAS.utils import cleanId
from pcp.rctsync import utils

def prepareid(values):
    id = values['fields']['name'].encode('utf8')
    id = id.replace(' ','')
    return cleanId(id)

def preparedata(values):

    fields = values['fields'].copy()
    
    data = {}
    additional = []
    additional.append({'key': 'contact',
                       'value': str(fields['contact']),
                       },
                      )
    additional.append({'key': 'community',
                       'value': str(fields['community']),
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

    data['title'] = fields['name']
    data['description'] = fields['description']
    data['website'] = fields['website']
    data['identifiers'] = identifiers
    data['additional'] = additional
    
    return data.copy()

def main(app):
    argparser = utils.getArgParser()
    args = argparser.parse_args()
    site = utils.getSite(app, args.site_id, args.admin_id)
    targetfolder = site.projects
    rct_projects = utils.getData(args.filename, 'rct.project')

    for pk, values in rct_projects.items():
        id = prepareid(values)
        if id is None:
            print "Couldn't generate id for ", line
            continue
        if id not in targetfolder.objectIds():
            targetfolder.invokeFactory('Project', id)
            print "Added %s to the projects folder" % id

        data = preparedata(values)
        print data
        targetfolder[id].edit(**data)
        targetfolder[id].reindexObject()
        print "Updated %s in the projects folder" % id

    if not args.dry:
        import transaction
        transaction.commit()
    else:
        print "dry run; not committing anything"
            
    print "Done"

# As this script lives in your source tree, we need to use this trick so that
# five.grok, which scans all modules, does not try to execute the script while
# modules are being loaded on start-up
if "app" in locals():
    main(app)
