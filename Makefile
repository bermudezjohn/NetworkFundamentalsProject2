# Makefile
all: 4700ftp

# This rule creates an executable file '4700ftp' that runs your Python script.
# It adds the shebang line, appends your code, and makes it executable.
4700ftp: 4700ftp.py
	@echo "#!/usr/bin/env python3" > 4700ftp
	@cat 4700ftp.py >> 4700ftp
	@chmod +x 4700ftp

clean:
	rm -f 4700ftp