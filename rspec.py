"""One mos servers on c240g5 (EMULAB) v0.1"""

#
# NOTE: This code was machine converted. An actual human would not
#       write code like this!
#

# Import the Portal object.
import geni.portal as portal
# Import the ProtoGENI library.
import geni.rspec.pg as pg
# Import the Emulab specific extensions.
import geni.rspec.emulab as emulab

# Create a portal object,
pc = portal.Context()

# Create a Request object to start building the RSpec.
request = pc.makeRequestRSpec()

# Node node-0
node_0 = request.RawPC('node-0')
node_0.hardware_type = 'c240g5'
node_0.disk_image = 'urn:publicid:IDN+wisc.cloudlab.us+image+videorendering-PG0:STSerial1'

# Print the generated rspec
pc.printRequestRSpec(request)