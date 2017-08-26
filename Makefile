PACKAGE_VERSION=0.0.1
prefix=/usr
plugin=mesh

all:

clean:
	fixme

install:
	install -d -m 0755 "$(DESTDIR)/$(prefix)/lib/partner/plugins"
	cp -r $(plugin) "$(DESTDIR)/$(prefix)/lib/partner/plugins"
	find "$(DESTDIR)/$(prefix)/lib/partner/plugins/$(plugin)" -type f | xargs chmod 644
	find "$(DESTDIR)/$(prefix)/lib/partner/plugins/$(plugin)" -type d | xargs chmod 755

uninstall:
	rm -rf "$(DESTDIR)/$(prefix)/lib/partner/plugins/$(plugin)"

.PHONY: all clean install uninstall
