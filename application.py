#!/usr/bin/python
import sys
from chalicepoints import app as application

if __name__ == "__main__":
    port = application.config['PORT']
    if len(sys.argv) == 2:
        port = int(sys.argv[1])

    application.run(
        host=application.config['HOST'],
        port=port,
        debug=application.config['DEBUG'],
    )