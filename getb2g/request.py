import os
import shutil

from base import valid_resources
from errors import InvalidResourceException, MultipleDeviceResourceException
from prompt import prompt
import handlers

import mozlog
log = mozlog.getLogger('GetB2G')

__all__ = ('Request', 'valid_resources')

class Request(object):
    """Represents a set of actions to be performed"""
    resources = []
    def __init__(self, metadata=None):
        self.metadata = metadata or {}

    def add_resource(self, resource):
        if resource not in valid_resources['all']:
            raise InvalidResourceException(msg="The resource '%s' is not valid! Choose from: %s" %
                                                            (resource, ", ".join(valid_resources['all'])))
        self.resources.append(resource)
        if resource in valid_resources['device']:
            if 'device' in self.metadata:
                raise MultipleDeviceResourceException(self.metadata['device'], resource)

            self.metadata['device'] = resource
            self.metadata['workdir'] = os.path.join(self.metadata['workdir'], resource)
            if os.path.isdir(self.metadata['workdir']):
                if prompt("Resource '%s' already exists in the working directory, do you want to overwrite it?" % resource) == "y":
                    log.info("removing '%s'" % self.metadata['workdir'])
                    shutil.rmtree(self.metadata['workdir'])
                else:
                    self.metadata['workdir'] = prompt("Enter the full path to a new working directory:", [])

            if not os.path.isdir(self.metadata['workdir']):
                os.makedirs(self.metadata['workdir'])

    def dispatch(self):
        """
        Request dispatches itself by calling execute_request on each of the required handlers
        """
        potential_handlers = []
        for handler in handlers.all_handlers:
            h_res = getattr(handlers, handler).handled_resources(self)
            if len(h_res) > 0:
                potential_handlers.append((handler, h_res))

        # sort the handlers based on how many resources they can handle,
        # we want to use as few as possible so resources come from the same place 
        potential_handlers.sort(key=lambda x: x[1], reverse=True)

        # the order of resources is important as resources later in the list might
        # be affected by values set by resources earlier in the list
        t_res = self.resources[:]
        for res in t_res:
            for handler, h_res in potential_handlers:
                if res in self.resources and res in h_res:
                    getattr(handlers, handler).execute_request(self)
        
        if len(self.resources) > 0:
            log.error("Sorry, unable to prepare any of these resources: %s" % ", ".join([r for r in self.resources]))
        log.info("Jobs done! Take a look in '%s' to see your files!" % self.metadata['workdir'])
