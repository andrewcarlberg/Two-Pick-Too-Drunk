import json
import os
import os.path
import re
import StringIO
import sys
import tempfile
import traceback
from types import GeneratorType
from datetime import datetime
import urllib, urllib2

import pymongo
import tornado.web

class BaseHandler(tornado.web.RequestHandler):

    def save_stream(self, actn, txt=None):
        c = ClickStream(user=self.current_user, actn=actn)
        if txt: c.txt = txt
        c.save()

    def api_write(self, data=None, status_ok=True):
        self.write(json.dumps({
            'status': 'ok' if status_ok else 'fail',
            'data': data or ''
            }))

    def prepare(self):
        super(BaseHandler, self).prepare()
        self._authed_user = None
        self._fixed = dict(
            timeago = timeago,
            pretty_amount = pretty_amount,
            nicks_to_urls = nicks_to_urls,
            DESCENDING = pymongo.DESCENDING,
            ASCENDING = pymongo.ASCENDING,
            ) # additional params to render_string

    def head(self, *a, **kwa): pass

    def clear_current_user(self):
        self._current_user = None
        self.set_secure_cookie(
            'authed_user',
            '',
            )

    def set_current_user(self, user):
        # now's as good a time as any to update the search tokens on a user
        user.last_login = datetime.now()
        user.create_search_tokens()


        # now set the secure session cookie
        self.set_secure_cookie(
            'authed_user',
            json.dumps({'user':user.nick}),
            expires_days=7,
            )

    def get_current_user(self):
        # just the user _id
        api_token = self.get_argument('apitoken','')
        api_token_login = self.get_argument('apitoken_login','')
        if api_token:
            u = User.find_one({'api_token': api_token})
            if api_token_login:
                self.set_current_user(u)
            return u
        else:
            sc = self.get_secure_cookie('authed_user')
            if sc:
                u_ = json.loads(self.get_secure_cookie('authed_user'))
                nick = u_['user']
                return User.search(nick=nick).first()
        return None

    def _handle_request_exception(self, e):
        tornado.web.RequestHandler._handle_request_exception(self,e)
        if self.application.settings.get('debug_pdb'):
            import pdb
            pdb.post_mortem()

    def render_string(self, templ, **kwa):
        if not hasattr(self, "_fixed"):
            self._fixed = {}
        self._fixed.update(kwa)
        kwa = self._fixed
        if 'message' not in kwa: kwa['message'] = []
        r_msg = self.get_argument('message', None)
        if r_msg:
            m = kwa['message']
            if isinstance(m, str): kwa['message'] = [m, r_msg]
            else: kwa['message'].append(r_msg)

        if 'error' not in kwa: kwa['error'] = []
        r_err = self.get_argument('error', None)
        if r_err:
            m = kwa['error']
            if isinstance(m, str): kwa['error'] = [m, r_err]
            else: kwa['error'].append(r_err)

        return tornado.web.RequestHandler.render_string(
            self,
            templ,
            **kwa
            )

    def get_error_html(self, status_code, **kwargs):
        if status_code == 404:
            return self.render_string('404.html')

        if not self.settings.get('debug'):
            self._log_snomelt()

        return self.render_string(
            'oops.html',
            txt="Something bad has happened. Perhaps refreshing will fix it?",
            )

    def _ignore_error(self, req=None):
        """we dont care about errors caused by some requests"""
        if not req: req = self.request
        # list of url patterns that we dont want to create snomelts for
        ignore_urls = [
                '/autodiscover/autodiscover\.xml',
                ]
        ignore_re = re.compile('|'.join(ignore_urls))
        if ignore_re.match(req.uri):
            return True
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if (req.uri == "/account/login" and
                exc_value.status_code == 403 and (
                    exc_value.log_message == (
                        "XSRF cookie does not match POST argument"
                        ) or (
                    exc_value.log_message == (
                        "'_xsrf' argument missing from POST"
                        )))):
            return True
        return False

    def _snomelt_data(self, req=None):
        if not req: req = self.request
        msg = ' '.join([
                str(self.get_status()),
                req.method,
                req.host + req.uri,
        ])
        user = self.current_user

        f = StringIO.StringIO()
        print >>f, msg
        print >>f, "{} from {} took {:.2f}ms on {}".format(
                user.nick if user else "anonymous user",
                req.remote_ip,
                1000*req.request_time(),
                datetime.strftime(datetime.now(), '%m/%d/%y %H:%M:%S'),
                )
        print >>f, str(req)
        traceback.print_exc(file=f)
        snomelt = f.getvalue()
        f.close()
        return snomelt

    def _log_snomelt(self):
        if self._ignore_error(self.request):
            return

        msg = ' '.join([
                str(self.get_status()),
                self.request.method,
                self.request.host + self.request.uri,
        ])
        user = self.current_user
        #open the snomelt file
        fid,path = tempfile.mkstemp(
                prefix = 'snomelt_',
                dir = self.settings.get('traceback_path'),
                )
        f = os.fdopen(fid,'w')
        #save debug info
        print >>f, self._snomelt_data(self.request)
        f.close()

        if self.settings.get('bkt_token'):
            bkt_url = self._snomelt_to_bucket(
                            path,
                            self.settings.get('bkt_token')
                            )
        else:
            bkt_url = ''

        #tweet
        tweet = '({}) {} {} {}'.format(
                self.settings.get('snomelt_notify', "@ksturner @nxin"),
                bkt_url,
                os.path.basename(path),
                msg
                )
        tweet_message(self.settings['twitter_error_settings'], tweet)

    def _snomelt_to_bucket(self, path, apitoken, shorten_url=True):
        """store the given file in a bucket and return a url to it"""
        snomelt = open(path).read()

        try:
            aws_host = urllib2.urlopen(
                'http://169.254.169.254/latest/meta-data/public-hostname',
                timeout=1).read()
        except (IOError, urllib2.URLError):
            from socket import gethostname
            aws_host = gethostname()

        bkt_key = os.path.basename(path)

        bkt = BucketClient(apitoken)
        bkt.put(bkt_key, {
            'doctype':'snomelt',
            'msg':snomelt,
            'host':aws_host,
            })

        url = "%s/bkt/k/%s" % (bkt.base_url, bkt_key)

        if shorten_url:
            url = self._get_blinkto_uri(url)

        return url

    def _get_blinkto_uri(self, uri):
        ' Take a url and return a blink.to shortened version. '
        import httplib
        post_data = { 'uri': uri, }
        c = httplib.HTTPConnection('blink.to')
        c.request('PUT', '/?%s' % urllib.urlencode(post_data))
        resp = c.getresponse()
        v = json.loads(resp.read())
        return v['uri']

    def oops(self, message):
        self.set_status(500)
        return self.render(
            'oops.html',
            txt=message
            )

    def show_message(self, title, text, refresh=False, refresh_secs=3):
        self.render(
            'message.html',
            message_title = title,
            message_text = text,
            refresh = refresh,
            refresh_secs = refresh_secs,
            )

