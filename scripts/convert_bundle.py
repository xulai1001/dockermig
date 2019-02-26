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
for it in spec["process"]["capabilities"].keys():
    spec["process"]["capabilities"][it] += [
        "CAP_CHOWN", "CAP_DAC_OVERRIDE", "CAP_FSETID", "CAP_FOWNER",
        "CAP_SETGID", "CAP_SETUID", "CAP_SETFCAP", "CAP_MKNOD",
        "CAP_NET_RAW", "CAP_SETPCAP", "CAP_SYS_CHROOT"
        ]
spec["linux"]["namespaces"].remove({"type": "network"}) # use host network
spec["root"]["readonly"] = False

json.dump(spec, open("bundle/config.json", "w"))
os.system("rm config.json")
print "- give access to rootfs/%s" % spec["process"]["cwd"]
os.system("sudo chmod 777 bundle/rootfs/%s" % spec["process"]["cwd"])
print "- complete"
pprint.pprint(spec)

