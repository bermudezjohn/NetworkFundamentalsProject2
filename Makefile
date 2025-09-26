# Makefile
all: 4700ftp

4700ftp: 4700ftp.py
	@echo "#!/usr/bin/env python3" > 4700ftp
	@cat 4700ftp.py >> 4700ftp
	@chmod +x 4700ftp

clean:
	rm -f 4700ftp