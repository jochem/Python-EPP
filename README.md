Python-EPP
==========

EPP client written in Python. Development is still in an early phase, but most of this should actually work. Tested against the Dutch SIDN DRS5 interface.

Usage
-----

    from EPP import EPP, Contact, Domain, Nameserver

    config = {
        'host': '%s.domain-registry.nl' % ('testdrs' if args['test'] else 'drs'),
        'port': 700,
        'user': <user>,
        'pass': <pass>,
    }
    contacts = {
        'registrant': 'NEX001077-NEXTG',
        'admin': 'FJF000131-NEXTG',
        'tech': 'JOO011933-NEXTG',
    }
    ns = ['ns.nextgear.nl', 'ns2.nextgear.nl']

    """ This wil automatically handle the greeting and login """
    epp = EPP(**config)

    """ Get the token for a given domain """
    domain = Domain(epp, 'nextgear.nl')
    print domain.token()

    """ Lookup the IP for a given nameserver """
    ns = Nameserver(epp, ns[0])
    print ns.get_ip()

    """ Get contact information for a given handle """
    contact = Contact(epp, 'JOO011933-NEXTG')
    print contact.info()
