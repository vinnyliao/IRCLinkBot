from twisted.words.protocols import irc
from twisted.internet import reactor, protocol

import sys, re, urllib, urllib2, httplib, cookielib

class LinkBot(irc.IRCClient):
    """IRC bot that visits URLs posted in chat and responds with the page title"""
    
    urlRegex = re.compile(r"""((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?]))""")
    categoryRegex = re.compile(r"""Site Category: <font color=\'blue\'>(?P<category>[^<]*)""")
    titleRegex = re.compile(r"""<title>(?P<title>.*)</title>""")
    nickname = "linkbot"
    
    categories = [
        'Abortion',
        'Pro-Choice',
        'Pro-Life',
        #'Adult Material',
        #'Adult Content',
        'Lingerie and Swimsuit',
        #'Nudity',
        #'Sex'
        'Sex Education',
        'Advocacy Groups',
        'Bandwidth',
        'Educational Video',
        'Entertainment Video',
        'Internet Radio and TV',
        #'Internet Telephony',
        #'Peer-to-Peer File Sharing',
        'Personal Network Storage and Backup',
        'Streaming Media',
        'Surveillance',
        'Viral Video',
        'Business and Economy',
        'Financial Data and Services',
        'Hosted Business Applications',
        'Drugs',
        'Abused Drugs',
        'Marijuana',
        'Prescribed Medications',
        'Supplements and Unregulated Compounds',
        'Education',
        'Cultural Institutions',
        'Educational Institutions',
        'Educational Materials',
        'Reference Materials',
        'Entertainment',
        'MP3 and Audio Download Services',
        'Extended Protection',
        'Dynamic DNS',
        'Elevated Exposure',
        'Emerging Exploits',
        'Potentially Damaging Content',
        #'Gambling',
        'Games',
        'Government',
        'Military',
        'Political Organizations',
        'Health',
        #'Illegal or Questionable',
        'Information Technology',
        'Computer Security',
        'Hacking',
        #'Proxy Avoidance',
        'Search Engines and Portals',
        'Unauthorized Mobile Marketplaces',
        'URL Translation Sites',
        'Web and Email Spam',
        'Web Collaboration',
        'Web Hosting',
        'Internet Communication',
        'General Email',
        'Organizational Email',
        'Text and Media Messaging',
        'Job Search',
        'Militancy and Extremist',
        'Miscellaneous',
        'Content Delivery Networks',
        'Dynamic Content',
        'File Download Servers',
        'Image Servers',
        'Images (Media)',
        'Network Errors',
        'Private IP Addresses',
        'Uncategorized',
        'News and Media',
        'Alternative Journals',
        'Parked Domain',
        'Productivity',
        'Advertisements',
        'Freeware and Software Download',
        'Instant Messaging',
        'Message Boards and Forums',
        'Online Brokerage and Trading',
        #'Pay to Surf',
        #'Racism and Hate',
        'Religion',
        'Non-Traditional Religions and Occult and Folklore',
        'Traditional Religions',
        #'Security',
        #'Advanced Malware Command and Control',
        #'Advanced Malware Payloads',
        #'Bot Networks',
        #'Keyloggers',
        #'Malicious Embedded iFrame',
        #'Malicious Embedded Link',
        #'Malicious Web Sites',
        #'Mobile Malware',
        #'Phishing and Other Frauds',
        #'Potentially Unwanted Software',
        #'Spyware',
        #'Suspicious Embedded Link',
        'Shopping',
        'Internet Auctions',
        'Real Estate',
        'Social Organizations',
        'Professional and Worker Organizations',
        'Service and Philanthropic Organizations',
        'Social and Affiliation Organizations',
        'Society and Lifestyles',
        'Alcohol and Tobacco',
        'Blogs and Personal Sites',
        'Gay or Lesbian or Bisexual Interest',
        'Hobbies',
        'Personals and Dating',
        'Restaurants and Dining',
        'Social Networking',
        'Special Events',
        'Sports',
        'Sport Hunting and Gun Clubs',
        #'Tasteless',
        'Travel',
        'User-Defined',
        'Vehicles',
        #'Violence',
        'Weapons'
    ]
    whitelist = set(categories)

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)


    # callbacks for events

    def signedOn(self):
        """Called when bot has successfully signed on to server."""
        print "joining channel..."
        self.join(self.factory.channel)

    def privmsg(self, user, channel, message):
        """This will get called when the bot receives a message."""
        self.handleMessage(user, channel, message)

    def topicUpdated(self, user, channel, newTopic):
        """This will get called when the bot sees someone do an action."""
        self.handleMessage(user, channel, newTopic)

    def handleMessage(self, user, channel, message):
        print user + ": " + message

        urlMatch = self.urlRegex.search(message)
        if not urlMatch: return

        url = urlMatch.group()
        print "[URL] " + url

        if not url.startswith("http"): url = "http://" + url

        cookiejar = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
        data = {
            'url': url,
            'op': 'Test URL',
            'form_build_id': 'form-2754726509343ca336cc86a8014f6422',
            'form_id': 'r2websense_testtool_form'
        }
        data = urllib.urlencode(data)

        websenseLookupResponse = opener.open("https://toolbox.richland2.org/r2apps/r2websense", data)
        websenseLookupResults = websenseLookupResponse.read()

        categoryMatch = self.categoryRegex.search(websenseLookupResults)
        category = categoryMatch.group("category")

        if not category:
            self.msg(channel, "Could not determine Websense category")
            return

        if not category in self.whitelist:
            self.msg(channel, "Access to the Websense category " + category + " might be blocked")
            return

        try:
            response = urllib2.urlopen(url)
            page = response.read()
            titleMatch = self.titleRegex.search(page)
            title = titleMatch.group("title")
            msg = title
        except urllib2.HTTPError, e:
            msg = "HTTPError: " + str(e.code)
        except urllib2.URLError, e:
            msg = "URLError: " + str(e.reason)
        except httplib.HTTPException, e:
            msg = "Ouch! An HTTPException occurred."
        except Exception, e:
            msg = "Ouch! An Exception occurred."
        finally:
            self.msg(channel, msg)

class LinkBotFactory(protocol.ClientFactory):
    """A factory for LinkBots.

    A new protocol instance will be created each time we connect to the server.
    """

    def __init__(self, channel):
        self.channel = channel

    def buildProtocol(self, addr):
        print "creating a new linkbot..."
        p = LinkBot()
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        print "connection lost. attempting to reconnect..."
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed: ", reason
        reactor.stop()


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print "Usage: python linkbot.py <host> <port> <channel>"
    else:
        host = sys.argv[1]
        port = int(sys.argv[2])
        channel = sys.argv[3]
    
        # create factory protocol and application
        f = LinkBotFactory(channel)
    
        # connect factory to this host and port
        print "connecting to " + host + ":" + str(port) + "..."
        reactor.connectTCP(host, port, f)
    
        # run bot
        print "starting linkbot..."
        reactor.run()
