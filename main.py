import cgi
import datetime
import urllib
import wsgiref.handlers
import re

from google.appengine.api import users
from google.appengine.ext import webapp

# Module for the admin interface.
import appengine_admin

from google.appengine.ext.webapp.util import run_wsgi_app

# Models is a User Defined Python File containing the Datastore Models for this application.
from models import *

from google.appengine.ext import db

from sessions import gmemsess # Session Library using google "memcached" for data storage, which is not a good option, when perfect transaction is required.

import os
from google.appengine.ext.webapp import template

class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        login_url = users.create_login_url("/")
        logout_url = users.create_logout_url("/")

        template_values = {
            'user':user,
            'login_url': login_url,
            'logout_url': logout_url,
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
        self.response.out.write(template.render(path, template_values))


# Just because I don't know how to persist GMEMSESS sessions across different views, I am not able to refactor the code 
# into separate views (I know sessions work for the same view), So you will see multiple hooks in this class.
class VotingPage(webapp.RequestHandler):
    # The handler page, where the Vote Case is selected.
    def get(self):
        user = users.get_current_user()
        login_url = users.create_login_url("/")
        logout_url = users.create_logout_url("/")

        available_vote_cases = VoteCase.all().order("title")
        #TODO: Show only those vote cases to the user, for which has not voted. vote_cases - voted_cases.

        template_values = {
            'user':user,
            'login_url': login_url,
            'vote_cases': available_vote_cases,
            'logout_url': logout_url,
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/select-vote-case.html')
        self.response.out.write(template.render(path, template_values))

    # The handler for the page, where the posted vote case is handled and list of candidates are shown for selection.
    def post(self):
        current_user = users.get_current_user()
        login_url = users.create_login_url("/")
        logout_url = users.create_logout_url("/")

        SELECTED_VOTE_CASE = self.request.get('selected-vote-case')
            
        #----Only those candidates, who have the selected vote case applicable to them, should be dispayed----#
        candidates_query = Candidate.all().order("email_id")
        all_candidates = candidates_query.fetch(20) #{CAVEAT} For now I assume not more than 20 candidates.
        # Code to filter out the the candidates that are standing for the Vote Case selected.
        candidates = []
        for candidate in all_candidates:
            if SELECTED_VOTE_CASE in candidate.vote_cases:
                candidates.append(candidate)
                
        # To check if the User is eligible to Vote for the selected Vote case, if NOT then the submit button is not shown to him    
        # on the voting page.
        user_already_voted = False
        if current_user:
            current_user_email = str(current_user.email())
            voted_users_object = VotedUser.all().filter("email_id =",current_user_email).get()
            # Short Circuit check: If voted_users_object is None, then the rest of the condition is not matched.
            if (voted_users_object and SELECTED_VOTE_CASE in voted_users_object.voted_cases):
                user_already_voted = True

        template_values = {
            'user':current_user,
            'login_url': login_url,
            'logout_url': logout_url,
            'selected_vote_case':SELECTED_VOTE_CASE,
            'candidates': candidates,
            'user_already_voted': user_already_voted,
        }

        path = os.path.join(os.path.dirname(__file__), 'templates/voting-page.html')
        self.response.out.write(template.render(path, template_values))

#TODO: Lots to be done here.
class VotingHandler(webapp.RequestHandler):
    def post(self):
        SELECTED_VOTE_CASE = self.request.get('selected_vote_case')

        current_user = users.get_current_user()
        login_url = users.create_login_url("/")
        logout_url = users.create_logout_url("/")
        user_already_voted = None
        vote_successfully_submitted = False
        valid_user_email = False

        voted_candidate_email = str(self.request.get('voted_candidate_email'))

        candidate_object = Candidate.all().filter("email_id =",voted_candidate_email).get()
        #TODO: Check whether there is NO KEY Error in any case.
        VOTE_INDEX = candidate_object.vote_cases.index(SELECTED_VOTE_CASE)
        n_of_votes = int(candidate_object.vote_count_list[VOTE_INDEX])

        # Security Check is done once again to see if the User is eligible to Vote for the selected Vote case.
        user_already_voted = False
        if current_user:
            current_user_email = str(current_user.email())
            voted_users_object = VotedUser.all().filter("email_id =",current_user_email).get()

            #<VOTEDUSER CHECK> Short Circuit check: If voted_users_object is None, then the rest of the condition is not matched.
            # VOTE_INDEX: holds the index of the selected vote case, in the voted_cases list.
            if (voted_users_object and SELECTED_VOTE_CASE in voted_users_object.voted_cases):
                user_already_voted = True

            #TODO Checking to be done as per VoteCase.re_pattern.            
            #<EMAIL ELIGIBILITY> Regex matching to check Email pattern for the vote case.         
            if (re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*\.ece[1][0]@itbhu\.ac\.in$',current_user_email) != None):
                valid_user_email = True

            #-----------Registering the Users Vote depending on the previous checks made-----------#
            if (not user_already_voted and valid_user_email):
                # (If voted_users_object exists => the User has already voted in some other case, else:) Create a new Voted User.
                if not voted_users_object:
                    voted_users_object = VotedUser()
                    voted_users_object.email_id = current_user_email
                voted_users_object.voted_cases.append(str(SELECTED_VOTE_CASE))
                candidate_object.vote_count_list[VOTE_INDEX] = str(n_of_votes + 1)
                candidate_object.put()
                voted_users_object.put()
                vote_successfully_submitted = True

        template_values = {
            'user':current_user,
            'login_url': login_url,
            'logout_url': logout_url,
            'selected_vote_case':SELECTED_VOTE_CASE,
            'user_already_voted': user_already_voted,
            'vote_successfully_submitted': vote_successfully_submitted,
        }

        path = os.path.join(os.path.dirname(__file__), 'templates/vote-submitted.html')
        self.response.out.write(template.render(path, template_values))


# Code to instantiate an application object, with a list of the mappings from the URL to the corresponding HANDLER CLASS.
application = webapp.WSGIApplication([
    ('/', MainPage),
    ('/select-vote-case', VotingPage),
    ('/voting-page', VotingPage),
    ('/vote-submitted', VotingHandler),
    # Admin pages
    (r'^(/admin)(.*)$', appengine_admin.Admin),
], debug=True)

def main():
    user = users.get_current_user()
    login_url = users.create_login_url("/")
    logout_url = users.create_logout_url("/")
    run_wsgi_app(application) # Boilerplate, Code to run the application object.

if __name__ == '__main__':
    main()
