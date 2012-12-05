import re
import tornado.web
from tornado.escape import json_encode, json_decode
from viewlib import route, BaseHandler, async_yield
import utils
from passlib.hash import sha256_crypt




@route("/account/login")
class LoginHandler(BaseHandler):

  def get(self):
    self.render("account/login.html", next=self.get_argument("next","/"), message=self.get_argument("error","") )

  def post(self):
    email = self.get_argument("email", "")
    password = self.get_argument("password", "")
    db = utils.connect_db('Two_Pick_Too_Drunk')

    user = db['users'].find_one( { 'user': email } )

    if user and user['password'] and sha256_crypt.verify(password,user['password']):
      self.set_current_user(email)
      self.redirect("hello")
    else:
      error_msg = u"?error=" + tornado.escape.url_escape("Login incorrect.")
      self.redirect(u"/login" + error_msg)
    
    self.render("account/home.html")


  def set_current_user(self, user):
    print "setting "+user
    if user:
      self.set_secure_cookie("user", tornado.escape.json_encode(user))
    else:
      self.clear_cookie("user")

@route("/account/register")
class RegisterHandler(LoginHandler):

  def get(self):
    error = self.get_argument("error", "")    
    self.render(  "account/register.html", next=self.get_argument("next","/"), error=error)

  def post(self):
    email = self.get_argument("email", "")
    
    db = utils.connect_db('Two_Pick_Too_Drunk')
    collection = db['users']
    already_taken = collection.find_one( { 'user': email } )
    if already_taken:
      error_msg = u"?error=" + tornado.escape.url_escape("Login name already taken")
      self.redirect(u"account/register" + error_msg, error = True)


    password = self.get_argument("password", "")
    hashed_pass = sha256_crypt.encrypt(password)

    user = {}
    user['user'] = email
    user['password'] = hashed_pass

    collection.save(user)
    self.set_current_user(email)

    self.redirect("account/home.html")
