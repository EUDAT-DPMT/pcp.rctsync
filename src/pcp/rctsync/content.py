#
# content.py
#
# script to be invoked via
#
#  cd <your-buildout-root-dir>
#  bin/instance run src/pcp.rctsync/src/pcp/rctsync/content.py
#
#  reads source information from data/rct_dump_20150609.json
#  
#  The SITE_ID is hard coded as 'pcp'

FILE_NAME = 'data/rct_dump_20150609.json'
SITE_ID = site_id = 'pcp'

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
    site = utils.getSite(app, site_id)
    targetfolder = site.projects
    rct_projects = utils.getData(FILE_NAME, 'rct.project')

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

    import transaction
    transaction.commit()

    print "Done"

# As this script lives in your source tree, then we need to use this trick so that
# five.grok, which scans all modules, does not try to execute the script while
# modules are being loaded on the start-up
if "app" in locals():
    main(app)
