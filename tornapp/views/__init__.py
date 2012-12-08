from viewlib import route, BaseHandler, async_yield
import tornado.web

# build our views here.
import account
import search


# this MUST COME LAST
@route('/(.*)')
class FourOhFour(BaseHandler):

    def get(self, maybe_nick=None):
        self.set_status(404)
        self.render('404.html')

    def post(self):
        self.render('404.html')

# must be done after all Handlers are defined and imported
routes = route.get_routes()

