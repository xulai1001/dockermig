#!/usr/bin/python
import json, sys, os, pprint

container = sys.argv[1]

print "- convert container: %s" % container
if not os.path.exists("bundle"):
    os.system("mkdir -p bundle oci")
    os.system("skopeo copy docker-daemon:%s:latest oci:oci/:%s" % (container, container))
    os.system("oci-image-tool create --ref name=%s oci bundle" % container)
    print "- merge spec"
    os.system("rm -rf oci")

print "- generate config.json"
os.system("runc spec")
spec = json.load(open("config.json"))
conf = json.load(open("bundle/config.json"))
#pprint.pprint(spec)
#print "--------------"
#pprint.pprint(conf)
spec["process"].update(conf["process"])
spec["root"].update(conf["root"])
json.dump(spec, open("bundle/config.json", "w"))
os.system("rm config.json")
print "- give access to rootfs/%s" % spec["process"]["cwd"]
os.system("sudo chmod 777 bundle/rootfs/%s" % spec["process"]["cwd"])
print "- complete"
pprint.pprint(spec)

