class RegisterForm(FlaskForm):
  username = StringField(validators=[InputRequired(),
                                     Length(min=4, max=20)],
                         render_kw={"placeholder": "Username"})

  email = EmailField(validators=[InputRequired(),
                                 Length(min=4, max=20)],
                     render_kw={"placeholder": "Email"})

  phonenumber = StringField(
    validators=[InputRequired(), Length(min=4, max=20)],
    render_kw={"placeholder": "phonenumber"})

  password = PasswordField(validators=[InputRequired(),
                                       Length(min=8, max=20)],
                           render_kw={"placeholder": "Password"})

  submit = SubmitField('Register')

  def validate_username(self, username):
    existing_user_username = User.query.filter_by(
      username=username.data).first()
    if existing_user_username:
      raise ValidationError(
        'That username already exists. Please choose a different one.')

  def validate_username(self, email):
    existing_user_email = User.query.filter_by(email=email.data).first()
    if existing_user_email:
      raise ValidationError(
        'That email already exists. Please choose a different one.')


class LoginForm(FlaskForm):
  # username = StringField(validators=[InputRequired(),
  #                                    Length(min=4, max=20)],
  #                        render_kw={"placeholder": "Username"})

  email = EmailField(validators=[InputRequired(),
                                 Length(min=4, max=20)],
                     render_kw={"placeholder": "Email"})
  password = PasswordField(validators=[InputRequired(),
                                       Length(min=8, max=20)],
                           render_kw={"placeholder": "Password"})

  submit = SubmitField('Login')




# def load_users_from_db():
#   with engine.connect() as conn:
#     result = conn.execution_options(stream_results=True).execute(
#       text("select * from users"))
#     result_all = result.all()
#     column_names = result.keys()
#     users = []
#     for idx, r in enumerate(result_all):
#       users.append(dict(zip(column_names, r)))
#   return users