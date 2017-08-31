PACKAGE_VERSION=0.0.1
prefix=/usr
plugin=mesh

all:

clean:
	fixme

install:
	install -d -m 0755 "$(DESTDIR)/$(prefix)/lib/partner/plugins.d"
	cp -r $(plugin) "$(DESTDIR)/$(prefix)/lib/partner/plugins.d"
	find "$(DESTDIR)/$(prefix)/lib/partner/plugins.d/$(plugin)" -type f | xargs chmod 644
	find "$(DESTDIR)/$(prefix)/lib/partner/plugins.d/$(plugin)" -type d | xargs chmod 755

uninstall:
	rm -rf "$(DESTDIR)/$(prefix)/lib/partner/plugins.d/$(plugin)"

.PHONY: all clean install uninstall
