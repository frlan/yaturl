#!/bin/sh

export PYTHONPATH="include:$PYTHONPATH"

program=`pwd`"/bin/yaturl_service.py"

#~ python2.5 bin/yaturl_service.py -f
python2.5 $program -f -c /opt/projects/yaturl.conf
