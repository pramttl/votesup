from google.appengine.ext import db
import appengine_admin

class EmailPattern(db.Model):
    title = db.StringProperty()
    re_pattern = db.StringProperty()

    def __unicode__(self):
        return self.title

class VoteCase(db.Model):
    """The model for the candidates for the voting competition"""
    title = db.StringProperty()
    description = db.StringProperty()
    pattern_filter = db.ReferenceProperty(EmailPattern)  # To know which Regex Pattern filter to apply to each VoteCase.

    def __unicode__(self):
        return self.email_id

class Candidate(db.Model):
    """The model for the candidates for the voting competition"""
    first_name = db.StringProperty()
    last_name = db.StringProperty()
    email_id = db.EmailProperty()
    vote_cases = db.StringListProperty(default = ['testCase']) # ['gen-secy','sports-secy']
    vote_count_list = db.StringListProperty(default=['0']) # [2,7] {This means gen-secy => 2 votes}
    date = db.DateTimeProperty(auto_now_add=True)

    def __unicode__(self):
        return self.email_id

class VotedUser(db.Model):
    """The model for the candidates for the voting competition"""
    email_id = db.EmailProperty()
    voted_cases = db.StringListProperty()

    def __unicode__(self):
        return self.user_email


## Admin views ##
class AdminVoteCase(appengine_admin.ModelAdmin):
    model = VoteCase
    listFields = ('title','description',)
    editFields = ('title','description',)

class AdminCandidate(appengine_admin.ModelAdmin):
    model = Candidate
    listFields = ('first_name','last_name','email_id','vote_cases', 'vote_count_list',)
    editFields = ('first_name','last_name','email_id','vote_cases','vote_count_list')

class AdminVotedUser(appengine_admin.ModelAdmin):
    model = VotedUser
    listFields = ('email_id','voted_cases')
    editFields = ('email_id','voted_cases')

class AdminEmailPattern(appengine_admin.ModelAdmin):
    model = VotedUser
    listFields = ('title','re_pattern')
    editFields = ('email_id','voted_cases')

# Register the models to the ADMIN sub-application.
appengine_admin.register(AdminVoteCase,AdminCandidate,AdminVotedUser,)
