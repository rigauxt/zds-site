# coding: utf-8

import os

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Layout, \
    Submit, Field, ButtonHolder, Hidden
from zds.member.models import Profile, listing
from zds.settings import SITE_ROOT

# Max password length for the user.
# Unlike other fields, this is not the length of DB field
MAX_PASSWORD_LENGTH = 76
# Min password length for the user.
MIN_PASSWORD_LENGTH = 6


class OldTutoForm(forms.Form):

    id = forms.ChoiceField(
        label='Ancien Tutoriel',
        required=True,
        choices=listing(),
    )

    def __init__(self, profile, *args, **kwargs):
        super(OldTutoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('zds.member.views.add_oldtuto')

        self.helper.layout = Layout(
            Field('id'),
            Hidden('profile_pk', '{{ profile.pk }}'),
            ButtonHolder(
                StrictButton('Attribuer', type='submit'),
            ),
        )


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Identifiant',
        max_length=User._meta.get_field('username').max_length,
        required=True,
        widget=forms.TextInput(
            attrs={
                'autofocus': ''
            }
        )
    )

    password = forms.CharField(
        label='Mot magique',
        max_length=MAX_PASSWORD_LENGTH,
        required=True,
        widget=forms.PasswordInput,
    )

    remember = forms.MultipleChoiceField(
        label='',
        choices=(
            ('remember', "Connexion automatique"),
        ),
        initial='remember',
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, next=None, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('zds.member.views.login_view')
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('username'),
            Field('password'),
            Field('remember'),
            HTML('{% csrf_token %}'),
            ButtonHolder(
                StrictButton('Se connecter', type='submit'),
                HTML('<a class="btn btn-cancel" href="/">Annuler</a>'),
            ),
        )


class RegisterForm(forms.Form):
    email = forms.EmailField(
        label='Adresse courriel',
        max_length=User._meta.get_field('email').max_length,
        required=True,
    )

    username = forms.CharField(
        label='Nom d\'utilisateur',
        max_length=User._meta.get_field('username').max_length,
        required=True,
    )

    password = forms.CharField(
        label='Mot de passe',
        max_length=MAX_PASSWORD_LENGTH,
        min_length=MIN_PASSWORD_LENGTH,
        required=True,
        widget=forms.PasswordInput
    )

    password_confirm = forms.CharField(
        label='Confirmation du mot de passe',
        max_length=MAX_PASSWORD_LENGTH,
        min_length=MIN_PASSWORD_LENGTH,
        required=True,
        widget=forms.PasswordInput
    )

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('username'),
            Field('password'),
            Field('password_confirm'),
            Field('email'),
            ButtonHolder(
                Submit('submit', 'Valider mon inscription'),
                HTML('<a class="btn btn-cancel" href="/">Annuler</a>'),
            ))

    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()

        # Check that the password and it's confirmation match
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if not password_confirm == password:
            msg = u'Les mots de passe sont différents'
            self._errors['password'] = self.error_class([msg])
            self._errors['password_confirm'] = self.error_class([msg])

            if 'password' in cleaned_data:
                del cleaned_data['password']

            if 'password_confirm' in cleaned_data:
                del cleaned_data['password_confirm']

        # Check that the user doesn't exist yet
        username = cleaned_data.get('username')
        
        if username is not None :
            if username.strip() == '':
                msg = u'Le nom d\'utilisateur ne peut-être vide'
                self._errors['username'] = self.error_class([msg])
            elif User.objects.filter(username=username).count() > 0:
                msg = u'Ce nom d\'utilisateur est déjà utilisé'
                self._errors['username'] = self.error_class([msg])
            # Forbid the use of comma in the username
            elif username is not None and "," in username:
                msg = u'Le nom d\'utilisateur ne peut contenir de virgules'
                self._errors['username'] = self.error_class([msg])
            elif username != username.strip():
                msg = u'Le nom d\'utilisateur ne peut commencer/finir par des espaces'
                self._errors['username'] = self.error_class([msg])

            # Check that password != username
            if password == username:
                msg = u'Le mot de passe doit être différent du pseudo'
                self._errors['password'] = self.error_class([msg])
                if 'password' in cleaned_data:
                    del cleaned_data['password']
                if 'password_confirm' in cleaned_data:
                    del cleaned_data['password_confirm']

        email = cleaned_data.get('email')
        if email:
            # Chech if email provider is authorized
            with open(os.path.join(SITE_ROOT,
                                   'forbidden_email_providers.txt'), 'r') as fh:
                for provider in fh:
                    if provider.strip() in email:
                        msg = u'Utilisez un autre fournisseur d\'adresses courriel.'
                        self._errors['email'] = self.error_class([msg])
                        break

        # Check that the email is unique
        if User.objects.filter(email=email).count() > 0:
            msg = u'Votre adresse courriel est déjà utilisée'
            self._errors['email'] = self.error_class([msg])

        return cleaned_data


class MiniProfileForm(forms.Form):
    biography = forms.CharField(
        label='Biographie',
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Votre biographie au format Markdown.'
            }
        )
    )

    site = forms.CharField(
        label='Site internet',
        required=False,
        max_length=Profile._meta.get_field('site').max_length,
        widget=forms.TextInput(
            attrs={
                'placeholder': u'Lien vers votre site internet '
                u'personnel (ne pas oublier le http:// ou https:// devant).'
            }
        )
    )

    avatar_url = forms.CharField(
        label='Avatar',
        required=False,
        max_length=Profile._meta.get_field('avatar_url').max_length,
        widget=forms.TextInput(
            attrs={
                'placeholder': u'Lien vers un avatar externe '
                u'(laissez vide pour utiliser Gravatar).'
            }
        )
    )

    sign = forms.CharField(
        label='Signature',
        required=False,
        max_length=Profile._meta.get_field('sign').max_length,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Elle apparaitra dans les messages de forums. '
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(MiniProfileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('biography'),
            Field('site'),
            Field('avatar_url'),
            Field('sign'),
            ButtonHolder(
                StrictButton('Editer le profil', type='submit'),
                HTML('<a class="btn btn-cancel" href="/">Annuler</a>'),
            ))

# update extra information about user


class ProfileForm(MiniProfileForm):
    options = forms.MultipleChoiceField(
        label='',
        required=False,
        choices=(
            ('show_email', "Afficher mon adresse courriel publiquement"),
            ('show_sign', "Afficher les signatures"),
            ('hover_or_click', "Cochez pour dérouler les menus au survol"),
            ('email_for_answer', u'Recevez un courriel lorsque vous '
            u'recevez une réponse à un message privé'),
        ),
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        # to get initial value form checkbox show email
        initial = kwargs.get('initial', {})
        self.fields['options'].initial = ''

        if 'show_email' in initial and initial['show_email']:
            self.fields['options'].initial += 'show_email'

        if 'show_sign' in initial and initial['show_sign']:
            self.fields['options'].initial += 'show_sign'

        if 'hover_or_click' in initial and initial['hover_or_click']:
            self.fields['options'].initial += 'hover_or_click'

        if 'email_for_answer' in initial and initial['email_for_answer']:
            self.fields['options'].initial += 'email_for_answer'

        self.helper.layout = Layout(
            Field('biography'),
            Field('site'),
            Field('avatar_url'),
            HTML(u"""
                <p><a href="{% url 'zds.gallery.views.gallery_list' %}">Choisir un avatar dans une galerie</a><br/>
                   Naviguez vers l'image voulue et cliquez sur le bouton "<em>Choisir comme avatar</em>".<br/>
                   Créez une galerie et importez votre avatar si ce n'est pas déjà fait !</p>
            """),
            Field('sign'),
            Field('options'),
            ButtonHolder(
                StrictButton('Editer mon profil', type='submit'),
                HTML('<a class="btn btn-cancel" href="/">Annuler</a>'),
            ))

# to update email/username


class ChangeUserForm(forms.Form):

    username_new = forms.CharField(
        label='Nouveau pseudo',
        max_length=User._meta.get_field('username').max_length,
        min_length=1,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Ne mettez rien pour conserver l\'ancien'
            }
        )
    )

    email_new = forms.EmailField(
        label='Nouvelle adresse courriel',
        max_length=User._meta.get_field('email').max_length,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Ne mettez rien pour conserver l\'ancien'
            }
        ),
        error_messages = {'invalid': u'Veuillez entrer une adresse email valide.',}
    )

    def __init__(self, *args, **kwargs):
        super(ChangeUserForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('username_new'),
            Field('email_new'),
            ButtonHolder(
                StrictButton('Changer', type='submit'),
                HTML('<a class="btn btn-cancel" href="/">Annuler</a>'),
            ),
        )

    def clean(self):
        cleaned_data = super(ChangeUserForm, self).clean()

        # Check that the password and it's confirmation match
        username_new = cleaned_data.get('username_new')
        email_new = cleaned_data.get('email_new')

        if username_new is not None:
            if username_new != '':
                if User.objects.filter(username=username_new.strip()).count() >= 1:
                    self._errors['username_new'] = self.error_class(
                        [u'Ce nom d\'utilisateur est déjà utilisé'])
                elif username_new != username_new.strip():
                    msg = u'Le nom d\'utilisateur ne peut commencer/finir par des espaces'
                    self._errors['username_new'] = self.error_class([msg])

        if email_new is not None:
            if email_new.strip() != '':
                if User.objects.filter(email=email_new).count() >= 1:
                    self._errors['email_new'] = self.error_class(
                        [u'Votre adresse courriel est déjà utilisée'])
            # Chech if email provider is authorized
            with open(os.path.join(SITE_ROOT,
                                   'forbidden_email_providers.txt'), 'r') as fh:
                for provider in fh:
                    if provider.strip() in email_new:
                        msg = u'Utilisez un autre fournisseur d\'adresses mail.'
                        self._errors['email_new'] = self.error_class([msg])
                        break

        return cleaned_data


# to update a password
class ChangePasswordForm(forms.Form):
    password_new = forms.CharField(
        label='Nouveau mot de passe',
        max_length=MAX_PASSWORD_LENGTH,
        widget=forms.PasswordInput
    )

    password_old = forms.CharField(
        label='Mot de passe actuel',
        max_length=MAX_PASSWORD_LENGTH,
        widget=forms.PasswordInput
    )

    password_confirm = forms.CharField(
        label='Confirmer le nouveau mot de passe',
        max_length=MAX_PASSWORD_LENGTH,
        widget=forms.PasswordInput
    )

    def __init__(self, user, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.user = user

        self.helper.layout = Layout(
            Field('password_old'),
            Field('password_new'),
            Field('password_confirm'),
            ButtonHolder(
                StrictButton('Changer', type='submit'),
                HTML('<a class="btn btn-cancel" href="/">Annuler</a>'),
            )
        )

    def clean(self):
        cleaned_data = super(ChangePasswordForm, self).clean()

        password_old = cleaned_data.get('password_old')
        password_new = cleaned_data.get('password_new')
        password_confirm = cleaned_data.get('password_confirm')

        # Check if the actual password is not empty
        if password_old:
            user_exist = authenticate(
                username=self.user.username, password=password_old
            )
            # Check if the user exist with old informations.
            if not user_exist and password_old != "":
                self._errors['password_old'] = self.error_class(
                    [u'Mot de passe incorrect.'])
                if 'password_old' in cleaned_data:
                    del cleaned_data['password_old']

        # Check that the password and it's confirmation match
        if not password_confirm == password_new:
            msg = u'Les mots de passe sont différents.'
            self._errors['password_new'] = self.error_class([msg])
            self._errors['password_confirm'] = self.error_class([msg])

            if 'password_new' in cleaned_data:
                del cleaned_data['password_new']

            if 'password_confirm' in cleaned_data:
                del cleaned_data['password_confirm']

        # Check that the password is at least MIN_PASSWORD_LENGTH
        if len(password_new) < MIN_PASSWORD_LENGTH:
            msg = u'Le mot de passe doit faire au moins {0} caractères'.format(MIN_PASSWORD_LENGTH)
            self._errors['password_new'] = self.error_class([msg])
            if 'password_new' in cleaned_data:
                del cleaned_data['password_new']

            if 'password_confirm' in cleaned_data:
                del cleaned_data['password_confirm']

        # Check that password != username
        if password_new == self.user.username:
            msg = u'Le mot de passe doit être différent de votre pseudo'
            self._errors['password_new'] = self.error_class([msg])
            if 'password_new' in cleaned_data:
                del cleaned_data['password_new']

            if 'password_confirm' in cleaned_data:
                del cleaned_data['password_confirm']

        return cleaned_data

# Reset the password


class ForgotPasswordForm(forms.Form):
    username = forms.CharField(
        label='Nom d\'utilisateur',
        max_length=User._meta.get_field('username').max_length,
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(ForgotPasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('username'),
            ButtonHolder(
                StrictButton('Envoyer', type='submit'),
                HTML('<a class="btn btn-cancel" href="/">Annuler</a>'),
            )
        )

    def clean(self):
        cleaned_data = super(ForgotPasswordForm, self).clean()

        # Check that the password and it's confirmation match
        username = cleaned_data.get('username')

        if User.objects.filter(username=username).count() == 0:
            self._errors['username'] = self.error_class(
                [u'Ce nom d\'utilisateur n\'existe pas'])

        return cleaned_data


class NewPasswordForm(forms.Form):
    password = forms.CharField(
        label='Mot de passe',
        max_length=MAX_PASSWORD_LENGTH,
        widget=forms.PasswordInput
    )
    password_confirm = forms.CharField(
        label='Confirmation',
        max_length=MAX_PASSWORD_LENGTH,
        widget=forms.PasswordInput
    )

    def __init__(self, identifier, *args, **kwargs):
        super(NewPasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'
        self.username = identifier

        self.helper.layout = Layout(
            Field('password'),
            Field('password_confirm'),
            ButtonHolder(
                StrictButton('Envoyer', type='submit'),
                HTML('<a class="btn btn-cancel" href="/">Annuler</a>'),
            )
        )

    def clean(self):
        cleaned_data = super(NewPasswordForm, self).clean()

        # Check that the password and it's confirmation match
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if not password_confirm == password:
            msg = u'Les mots de passe sont différents'
            self._errors['password'] = self.error_class([''])
            self._errors['password_confirm'] = self.error_class([msg])

            if 'password' in cleaned_data:
                del cleaned_data['password']

            if 'password_confirm' in cleaned_data:
                del cleaned_data['password_confirm']

        # Check that the password is at least MIN_PASSWORD_LENGTH
        if len(password) < MIN_PASSWORD_LENGTH:
            msg = u'Le mot de passe doit faire au moins {0} caractères'.format(MIN_PASSWORD_LENGTH)
            self._errors['password'] = self.error_class([msg])
            if 'password' in cleaned_data:
                del cleaned_data['password']

            if 'password_confirm' in cleaned_data:
                del cleaned_data['password_confirm']

        # Check that password != username
        if password == self.username:
            msg = u'Le mot de passe doit être différent de votre pseudo'
            self._errors['password'] = self.error_class([msg])
            if 'password' in cleaned_data:
                del cleaned_data['password']

            if 'password_confirm' in cleaned_data:
                del cleaned_data['password_confirm']

        return cleaned_data
