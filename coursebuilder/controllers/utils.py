# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os, logging
import webapp2, jinja2
from jinja2.exceptions import TemplateNotFound
from models.models import Student, Unit, PageCache, Email
from google.appengine.api import users, mail, taskqueue
from google.appengine.ext import db, deferred
from assessments import getAllScores


USER_EMAIL_PLACE_HOLDER = "{{ email }}"


def sendWelcomeEmail(email):
  # FIXME: To automatically send welcome emails, edit this welcome message
  # and see the welcome email FIXME in RegisterHandler
  message = mail.EmailMessage(sender="COURSE STAFF NAME <COURSE_EMAIL_ADDRESS@YOURDOMAIN>",
    subject="Welcome to COURSE NAME!")
  message.to = email
  message.body = """
    Thank you for registering for COURSE NAME.
    YOUR WELCOME MESSAGE HERE
  """
  message.html = """
    <p>Thank you for registering for COURSE NAME.</p>
    <p>YOUR WELCOME MESSAGE HERE</p>
  """
  message.send()


"""A handler that is aware of the application context."""
class ApplicationHandler(webapp2.RequestHandler):
  def __init__(self):
    super(ApplicationHandler, self).__init__()
    self.templateValue = {}

  def appendBase(self):
    """Append current course <base> to template variables."""
    slug = self.app_context.getSlug()
    if not slug.endswith('/'):
      slug = '%s/' % slug
    self.templateValue['gcb_course_base'] = slug

  def getTemplate(self, templateFile):
    """Computes the location of template files for the current namespace."""
    self.appendBase()
    template_dir = self.app_context.getTemplateHome()
    jinja_environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir))
    return jinja_environment.get_template(templateFile)

  def redirect(self, location):
    """Takes relative 'location' and adds current namespace URL prefix to it."""
    if self.app_context.getSlug() and self.app_context.getSlug() != '/':
      location = '%s%s' % (self.app_context.getSlug(), location)
    super(ApplicationHandler, self).redirect(location)


"""
Base handler
"""
class BaseHandler(ApplicationHandler):
  def getUser(self):
    """Validate user exists."""
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
    else:
      return user

  def personalizePageAndGetUser(self):
    """If the user exists, add email and logoutUrl fields to the navbar template."""
    user = self.getUser()
    if user:
      self.templateValue['email'] = user.email()
      self.templateValue['logoutUrl'] = users.create_logout_url("/")
    return user

  def render(self, templateFile):
    template = self.getTemplate(templateFile)
    self.response.out.write(template.render(self.templateValue))


"""
Student Handler
"""
class StudentHandler(ApplicationHandler):

  def getOrCreatePage(self, page_name, handler):
    def content_lambda():
      return self.delegateTo(handler)
    return PageCache.get_page(page_name, content_lambda)

  def delegateTo(self, handler):
    """"Run another handler using system identity.

    This method is called when a dynamic page template cannot be found in either
    memcache or the datastore. We now need to create this page using a handler
    passed to this method. The handler must run with the exact same request
    parameters as self, but we need to replace current user and the response."""

    # create custom function for replacing the current user
    def get_placeholder_user():
      return users.User(email = USER_EMAIL_PLACE_HOLDER)

    # create custom response.out to intercept output
    class StringWriter:
      def __init__(self):
        self.buffer = []

      def write(self, text):
        self.buffer.append(text)

      def getText(self):
        return "".join(self.buffer)

    class BufferedResponse:
      def __init__(self):
        self.out = StringWriter()

    # configure handler request and response
    handler.app_context = self.app_context
    handler.request = self.request
    handler.response = BufferedResponse()

    # substitute current user with the system account and run the handler
    get_current_user_old = users.get_current_user
    try:
      users.get_current_user = get_placeholder_user
      handler.get()
    finally:
      users.get_current_user = get_current_user_old

    return handler.response.out.getText()

  def getEnrolledStudent(self):
    user = users.get_current_user()
    if user:
      return Student.get_enrolled_student_by_email(user.email())
    else:
      self.redirect(users.create_login_url(self.request.uri))

  def serve(self, page, email, overall_score):
    # Search and substitute placeholders for current user email and
    # overall_score (if applicable) in the cached page before serving them to
    # users.
    html = page
    html = html.replace(USER_EMAIL_PLACE_HOLDER, email)
    if overall_score:
      html = html.replace('XX', overall_score)
    self.response.out.write(html)


"""
Handler for viewing course preview
"""
class CoursePreviewHandler(BaseHandler):
  def get(self):
    user = users.get_current_user()
    if not user:
      self.templateValue['loginUrl'] = users.create_login_url('/')
    else:
      self.templateValue['email'] = user.email()
      self.templateValue['logoutUrl'] = users.create_logout_url("/")

    self.templateValue['navbar'] = {'course': True}
    self.templateValue['units'] = Unit.get_units()
    if user and Student.get_enrolled_student_by_email(user.email()):
      self.redirect('/course')
    else:
      self.render('preview.html')


"""
Handler for course registration closed
"""
class RegisterClosedHandler(BaseHandler):
  def get(self):
    user = self.personalizePageAndGetUser()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    self.templateValue['navbar'] = {'registration': True}
    self.render('registration_close.html')


"""
Handler for course registration
"""
class RegisterHandler(BaseHandler):
  def get(self):
    user = self.personalizePageAndGetUser()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    self.templateValue['navbar'] = {'registration': True}
    # Check for existing registration -> redirect to course page
    student = Student.get_enrolled_student_by_email(user.email())
    if student:
      self.redirect('/course')
    else:
      self.render('register.html')

  def post(self):
    user = self.personalizePageAndGetUser()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    # Restrict the maximum course size to 250000 people
    # FIXME: you can change this number if you wish.
    # Uncomment the following 3 lines if you want to restrict the course size.
    # Note, though, that counting the students in this way uses a lot of database
    # calls that may cost you quota and money.

    # students = Student.all(keys_only=True)
    # if (students.count() > 249999):
    #   self.templateValue['course_status'] = 'full'

    # Create student record
    name = self.request.get('form01')

    # create new or re-enroll old student
    student = Student.get_by_email(user.email())
    if student:
      if not student.is_enrolled:
        student.is_enrolled = True
        student.name = name
    else:
      student = Student(key_name=user.email(), name=name, is_enrolled=True)
    student.put()

    # FIXME: Uncomment the following 2 lines, edit the message in the sendWelcomeEmail
    # function and create a queue.yaml file if you want to automatically send a
    # welcome email message.

    # # Send welcome email
    # deferred.defer(sendWelcomeEmail, email)

    # Render registration confirmation page
    self.templateValue['navbar'] = {'registration': True}
    self.render('confirmation.html')


"""
Handler for forum page
"""
class ForumHandler(BaseHandler):
  def get(self):
    user = self.personalizePageAndGetUser()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    self.templateValue['navbar'] = {'forum': True}
    self.render('forum.html')


"""
Handler for saving assessment answers
"""
class AnswerHandler(BaseHandler):
  def __init__(self, type):
    super(AnswerHandler, self).__init__()
    self.type = type

  def get(self):
    user = self.personalizePageAndGetUser()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    self.templateValue['navbar'] = {'course': True}
    self.templateValue['assessment'] = self.type
    self.render('test_confirmation.html')


class AddTaskHandler(ApplicationHandler):
  def get(self):
    log = ''
    emails = EmailList.all().fetch(1000)
    if emails:
      for email in emails:
        log = log + email.email + "\n"
        taskqueue.add(url='/admin/reminderemail', params={'to': email.email})
      db.delete(emails)
      self.response.out.write(log)


"""
This function handles the click to 'My Profile' link in the nav bar
"""
class StudentProfileHandler(BaseHandler):
  def get(self):
    user = self.personalizePageAndGetUser()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    self.templateValue['navbar'] = {}
    #check for existing registration -> redirect to course page
    e = user.email()
    student = Student.get_by_email(e)
    if student == None:
      self.templateValue['student'] = None
      self.templateValue['errormsg'] = 'Error: Student with email ' + e + ' can not be found on the roster.'
      self.render('register.html')
    else:
      self.templateValue['student'] = student
      self.templateValue['scores'] = getAllScores(student)
      self.render('student_profile.html')

"""
This function handles edits to student records by students
"""
class StudentEditStudentHandler(BaseHandler):
  def get(self):
    user = self.personalizePageAndGetUser()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    self.templateValue['navbar'] = {}
    e = self.request.get('email')
    # Check for existing registration -> redirect to course page
    student = Student.get_by_email(e)
    if student == None:
      self.templateValue['student'] = None
      self.templateValue['errormsg'] = 'Error: Student with email ' + e + ' can not be found on the roster.'
    else:
      self.templateValue['student'] = student
      self.templateValue['scores'] = getAllScores(student)
    self.render('student_profile.html')

  def post(self):
    user = self.personalizePageAndGetUser()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    # Update student record
    e = self.request.get('email')
    n = self.request.get('name')

    student = Student.get_by_email(e)
    if student:
      if (n != ''):
        student.name = n
      student.put()
    self.redirect('/student/editstudent?email='+e)


"""
Handler for Announcements
"""
class AnnouncementsHandler(BaseHandler):
  def get(self):
    user = self.personalizePageAndGetUser()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    self.templateValue['navbar'] = {'announcements': True}
    self.render('announcements.html')


"""
Handler for students to unenroll themselves
"""
class StudentUnenrollHandler(BaseHandler):
  def get(self):
    user = self.personalizePageAndGetUser()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    student = Student.get_enrolled_student_by_email(user.email())
    if student:
      self.templateValue['student'] = student
    self.templateValue['navbar'] = {'registration': True}
    self.render('unenroll_confirmation_check.html')

  def post(self):
    user = self.personalizePageAndGetUser()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    # Update student record
    student = Student.get_by_email(user.email())
    if student and student.is_enrolled:
      student.is_enrolled = False
      student.put()
    self.templateValue['navbar'] = {'registration': True}
    self.render('unenroll_confirmation.html')

